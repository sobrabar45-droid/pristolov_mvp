from __future__ import annotations

from copy import deepcopy
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.game_phase import GamePhase
from app.models.game_host_round import GameHostRound
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.round_question_template import RoundQuestionTemplate
from app.models.round_template import RoundTemplate
from app.services.host_round_service import (
    force_close_current_question_by_host as _force_close_current_question_by_host,
    open_next_question_for_host_round as _open_next_question_for_host_round,
)


COURT_PHASE_TYPE = "court"
COURT_SOURCE = "court_mvp"
COURT_ROUND_CODE = "stage_court"
COURT_QUESTION_ROUND_CODE = "stage_court_battle"
COURT_QUESTION_SOURCE_ROUND_CODES = (
    "stage_court_battle",
    "court_battle_01",
    "season1_opening_questions",
    "imported_warmup_test",
    "imported_media_test",
)
COURT_MAX_QUESTIONS = 7
COURT_TEAM_SIZE = 4
PAIR_FINISHED_STATUSES = {"pair_result", "finished"}


def _game_payload(game: Game) -> dict[str, Any]:
    return {
        "id": game.id,
        "room_code": game.room_code,
        "title": game.title,
    }


def _default_court_payload() -> dict[str, Any]:
    return {
        "source": COURT_SOURCE,
        "round_code": COURT_ROUND_CODE,
        "status": "active",
        "bracket": [],
        "current_pair_index": None,
        "current_pair": None,
        "history": [],
    }


def _normalize_court_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}

    normalized = deepcopy(payload)
    defaults = _default_court_payload()
    for key, value in defaults.items():
        if key not in normalized:
            normalized[key] = deepcopy(value)

    if not isinstance(normalized.get("bracket"), list):
        normalized["bracket"] = []
    if not isinstance(normalized.get("history"), list):
        normalized["history"] = []
    if normalized.get("current_pair") is not None and not isinstance(normalized.get("current_pair"), dict):
        normalized["current_pair"] = None

    normalized["source"] = COURT_SOURCE
    normalized["round_code"] = normalized.get("round_code") or COURT_ROUND_CODE
    normalized["status"] = normalized.get("status") or "active"
    return normalized


def _get_game_by_room_code(db: Session, room_code: str) -> Game | None:
    normalized = str(room_code or "").strip()
    if not normalized:
        return None
    return db.query(Game).filter(Game.room_code == normalized).first()


def _get_active_court_phase(db: Session, game: Game) -> GamePhase | None:
    return (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == COURT_PHASE_TYPE,
            GamePhase.status == "active",
        )
        .order_by(GamePhase.id.desc())
        .first()
    )


def _get_or_create_court_phase(db: Session, game: Game) -> GamePhase:
    phase = _get_active_court_phase(db, game)
    if phase:
        phase.payload = _normalize_court_payload(phase.payload)
        db.add(phase)
        db.flush()
        return phase

    phase = GamePhase(
        game_id=game.id,
        phase_type=COURT_PHASE_TYPE,
        status="active",
        payload=_default_court_payload(),
    )
    db.add(phase)
    db.flush()
    return phase


def _build_ranked_houses(game: Game) -> list[dict[str, Any]]:
    houses = sorted(
        list(game.houses or []),
        key=lambda house: (
            -(house.resource_influence or 0),
            -(house.resource_gold or 0),
            house.id or 0,
        ),
    )

    ranked = []
    for seed, house in enumerate(houses, start=1):
        ranked.append(
            {
                "seed": seed,
                "house_id": house.id,
                "house_name": house.name,
                "house_key": house.house_key,
                "influence": house.resource_influence or 0,
                "gold": house.resource_gold or 0,
            }
        )
    return ranked


def _build_bracket_from_ranked_houses(
    ranked_houses: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    history_events: list[dict[str, Any]] = []
    ranked_for_pairs = list(ranked_houses)

    if len(ranked_for_pairs) % 2 == 1 and ranked_for_pairs:
        bye_house = ranked_for_pairs[0]
        ranked_for_pairs = ranked_for_pairs[1:]
        history_events.append(
            {
                "type": "bye",
                "house_id": bye_house["house_id"],
                "house_name": bye_house["house_name"],
                "seed": bye_house["seed"],
            }
        )

    bracket: list[dict[str, Any]] = []
    left = len(ranked_for_pairs) // 2 - 1
    right = len(ranked_for_pairs) // 2
    pair_no = 1

    while left >= 0 and right < len(ranked_for_pairs):
        house_a = ranked_for_pairs[left]
        house_b = ranked_for_pairs[right]
        bracket.append(
            {
                "pair_no": pair_no,
                "house_a_id": house_a["house_id"],
                "house_b_id": house_b["house_id"],
                "house_a_name": house_a["house_name"],
                "house_b_name": house_b["house_name"],
                "seed_a": house_a["seed"],
                "seed_b": house_b["seed"],
                "status": "pending",
                "winner_house_id": None,
            }
        )
        pair_no += 1
        left -= 1
        right += 1

    return bracket, history_events


def _find_bracket_pair(
    payload: dict[str, Any],
    *,
    pair_no: int | None = None,
) -> tuple[int | None, dict[str, Any] | None]:
    bracket = payload.get("bracket") or []
    if pair_no is not None:
        for index, item in enumerate(bracket):
            if int(item.get("pair_no") or 0) == int(pair_no):
                return index, item
        return None, None

    for index, item in enumerate(bracket):
        if item.get("status") == "pending":
            return index, item
    return None, None


def _sync_bracket_pair(payload: dict[str, Any], current_pair: dict[str, Any]) -> None:
    bracket = payload.get("bracket") or []
    for item in bracket:
        if int(item.get("pair_no") or 0) == int(current_pair.get("pair_no") or 0):
            item["winner_house_id"] = current_pair.get("winner_house_id")
            if current_pair.get("status") in PAIR_FINISHED_STATUSES:
                item["status"] = "finished"
            elif current_pair.get("status") == "pair_active":
                item["status"] = "active"
            elif item.get("status") == "pending":
                item["status"] = "active"
            return


def _append_history(payload: dict[str, Any], event: dict[str, Any]) -> None:
    history = payload.setdefault("history", [])
    history.append(event)
    payload["last_event"] = event


def _is_pair_winner_confirmed(payload: dict[str, Any], pair_no: int | None) -> bool:
    if not pair_no:
        return False
    history = payload.get("history") or []
    for item in history:
        if item.get("type") == "pair_winner_confirmed" and int(item.get("pair_no") or 0) == int(pair_no):
            return True
    return False


def _save_court_phase(db: Session, phase: GamePhase, payload: dict[str, Any]) -> None:
    phase.payload = _normalize_court_payload(payload)
    db.add(phase)
    db.commit()
    db.refresh(phase)


def _build_court_question_state(*, host_round_id: int | None = None, question_no: int = 0) -> dict[str, Any]:
    return {
        "question_host_round_id": host_round_id,
        "question_active": False,
        "question_no": int(question_no or 0),
        "question_status": "closed",
    }


def _apply_court_question_state(
    current_pair: dict[str, Any],
    *,
    host_round_id: int | None = None,
    question_active: bool | None = None,
    question_no: int | None = None,
    question_status: str | None = None,
) -> None:
    current_pair.update(
        {
            "question_host_round_id": host_round_id if host_round_id is not None else current_pair.get("question_host_round_id"),
            "question_active": bool(question_active) if question_active is not None else bool(current_pair.get("question_active")),
            "question_no": int(question_no) if question_no is not None else int(current_pair.get("question_no") or 0),
            "question_status": question_status or current_pair.get("question_status") or "closed",
        }
    )


def _ensure_host_round_phase_active(db: Session, game: Game) -> None:
    phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == "host_round",
            GamePhase.status == "active",
        )
        .order_by(GamePhase.id.desc())
        .first()
    )
    if phase:
        return

    phase = GamePhase(
        game_id=game.id,
        phase_type="host_round",
        status="active",
        payload=None,
    )
    db.add(phase)
    db.flush()


def _find_round_template_by_code(db: Session, round_code: str) -> RoundTemplate | None:
    normalized_code = str(round_code or "").strip()
    if not normalized_code:
        return None
    return (
        db.query(RoundTemplate)
        .filter(RoundTemplate.round_code == normalized_code)
        .order_by(RoundTemplate.id.desc())
        .first()
    )


def _ensure_court_question_round_template(db: Session, game: Game) -> RoundTemplate | None:
    existing = _find_round_template_by_code(db, COURT_QUESTION_ROUND_CODE)
    if existing and len(existing.questions or []) > 0:
        return existing

    source_round = None
    for candidate_code in COURT_QUESTION_SOURCE_ROUND_CODES:
        candidate = _find_round_template_by_code(db, candidate_code)
        if candidate and len(candidate.questions or []) > 0:
            source_round = candidate
            break

    if source_round is None:
        source_round = (
            db.query(RoundTemplate)
            .join(RoundQuestionTemplate, RoundQuestionTemplate.round_template_id == RoundTemplate.id)
            .filter(
                RoundTemplate.round_code != COURT_ROUND_CODE,
                RoundTemplate.round_code != COURT_QUESTION_ROUND_CODE,
            )
            .group_by(RoundTemplate.id)
            .order_by(func.count(RoundQuestionTemplate.id).desc(), RoundTemplate.id.desc())
            .first()
        )

    if source_round is None:
        return None

    if existing is None:
        existing = RoundTemplate(
            template_id=source_round.template_id,
            scenario_id=source_round.scenario_id,
            round_code=COURT_QUESTION_ROUND_CODE,
            import_key=f"{COURT_QUESTION_ROUND_CODE}_auto",
            title="Вопросы Суда Домов",
            order_no=source_round.order_no,
            act_number=source_round.act_number or 1,
            round_type=source_round.round_type or "host_round_series",
            round_kind=source_round.round_kind or "host_round_series",
            check_mode=source_round.check_mode or "auto",
            questions_total=0,
            time_limit_sec=source_round.time_limit_sec,
            is_host_led=source_round.is_host_led,
            is_optional=True,
            bar_window_opens=False,
            scoring_mode=source_round.scoring_mode,
            question_transition_mode=source_round.question_transition_mode,
            round_transition_mode=source_round.round_transition_mode,
            intro_text="Вопросы для Суда Домов",
            outro_text=source_round.outro_text,
        )
        db.add(existing)
        db.flush()
    else:
        existing.template_id = source_round.template_id
        existing.scenario_id = source_round.scenario_id
        existing.title = existing.title or "Вопросы Суда Домов"

    if len(existing.questions or []) == 0:
        cloned_count = 0
        source_questions = sorted(list(source_round.questions or []), key=lambda item: (item.sequence_no or 0, item.id or 0))
        for index, source_question in enumerate(source_questions, start=1):
            cloned = RoundQuestionTemplate(
                round_template_id=existing.id,
                question_code=f"court_{source_question.question_code or index}",
                sequence_no=index,
                role_code="court_mvp",
                title=source_question.title,
                prompt=source_question.prompt,
                ui_template=source_question.ui_template,
                answer_mode=source_question.answer_mode,
                auto_check=source_question.auto_check,
                manual_check_allowed=source_question.manual_check_allowed,
                allowed_house_keys=None,
                content_json=source_question.content_json,
                reward_json=source_question.reward_json,
                fail_effect_json=source_question.fail_effect_json,
            )
            db.add(cloned)
            cloned_count += 1
        existing.questions_total = cloned_count
        db.flush()
        db.refresh(existing)

    return existing


def _get_court_question_host_round(
    db: Session,
    *,
    game: Game,
    host_round_id: int | None = None,
) -> GameHostRound | None:
    if host_round_id:
        host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.id == int(host_round_id),
                GameHostRound.game_id == game.id,
            )
            .first()
        )
        if host_round:
            return host_round

    return (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game.id,
            GameHostRound.round_code == COURT_QUESTION_ROUND_CODE,
            GameHostRound.status.in_(["active", "completed_waiting_host"]),
        )
        .order_by(GameHostRound.id.desc())
        .first()
    )


def _build_question_payload(runtime_question: GameHostRoundQuestion | None) -> dict[str, Any] | None:
    if runtime_question is None:
        return None

    question_template = runtime_question.question_template
    question_content = {}
    if question_template and question_template.content_json:
        try:
            import json

            question_content = json.loads(question_template.content_json)
        except Exception:
            question_content = {}
    if not isinstance(question_content, dict):
        question_content = {}

    payload = {
        "id": runtime_question.id,
        "sequence_no": runtime_question.sequence_no,
        "status": runtime_question.status,
        "answers_open": runtime_question.answers_open,
        "title": question_template.title if question_template else f"Вопрос #{runtime_question.sequence_no}",
        "prompt": question_template.prompt if question_template else None,
        "question_code": question_template.question_code if question_template else None,
        "ui_template": question_template.ui_template if question_template else None,
        "role_code": question_template.role_code if question_template else None,
        "time_limit_sec": question_content.get("time_limit_sec"),
        "timer": question_content.get("timer"),
        "duration_sec": question_content.get("duration_sec"),
        "content": question_content,
        "media_type": question_content.get("media_type"),
        "media_ref": question_content.get("media_ref"),
        "is_media_question": bool(question_content.get("is_media_question")),
    }
    return payload


def sync_court_question_runtime_logic(
    db: Session,
    room_code: str,
    *,
    host_round_id: int | None = None,
) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_active_court_phase(db, game)
    if not phase:
        return {"ok": True, "game": _game_payload(game), "court": None}

    payload = _normalize_court_payload(phase.payload)
    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        payload["current_question"] = None
        phase.payload = payload
        db.add(phase)
        db.flush()
        return {"ok": True, "game": _game_payload(game), "court": payload}

    host_round = _get_court_question_host_round(
        db,
        game=game,
        host_round_id=host_round_id if host_round_id is not None else current_pair.get("question_host_round_id"),
    )
    if host_round is None:
        _apply_court_question_state(
            current_pair,
            host_round_id=None,
            question_active=False,
            question_status="closed",
        )
        payload["current_pair"] = current_pair
        payload["current_question"] = None
        phase.payload = payload
        db.add(phase)
        db.flush()
        return {"ok": True, "game": _game_payload(game), "court": payload}

    runtime_question = (
        db.query(GameHostRoundQuestion)
        .filter(GameHostRoundQuestion.host_round_id == host_round.id)
        .order_by(GameHostRoundQuestion.sequence_no.desc(), GameHostRoundQuestion.id.desc())
        .first()
    )

    question_payload = _build_question_payload(runtime_question)
    if runtime_question is None:
        question_status = "closed"
        question_active = False
    elif runtime_question.status == "active" and runtime_question.answers_open:
        question_status = "active"
        question_active = True
        if current_pair.get("status") not in PAIR_FINISHED_STATUSES:
            current_pair["status"] = "question_active"
    elif runtime_question.status in {"resolved", "closed"} or runtime_question.answers_open is False:
        question_status = "reveal"
        question_active = False
        if current_pair.get("status") not in PAIR_FINISHED_STATUSES and current_pair.get("status") not in {"needs_extra_question", "sudden_death"}:
            current_pair["status"] = "question_reveal"
    else:
        question_status = runtime_question.status or "closed"
        question_active = False

    _apply_court_question_state(
        current_pair,
        host_round_id=host_round.id,
        question_active=question_active,
        question_no=host_round.current_question_no or current_pair.get("question_no") or 0,
        question_status=question_status,
    )
    payload["current_pair"] = current_pair
    payload["current_question"] = question_payload
    phase.payload = payload
    db.add(phase)
    db.flush()
    return {"ok": True, "game": _game_payload(game), "court": payload}


def build_court_runtime_view_logic(
    db: Session,
    room_code: str,
    court_runtime_payload: dict[str, Any] | None,
    *,
    host_round_id: int | None = None,
) -> dict[str, Any] | None:
    if not isinstance(court_runtime_payload, dict):
        return None

    game = _get_game_by_room_code(db, room_code)
    payload = _decorate_court_payload(court_runtime_payload)
    if not game:
        return payload

    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        payload["current_question"] = None
        return _decorate_court_payload(payload)

    host_round = _get_court_question_host_round(
        db,
        game=game,
        host_round_id=host_round_id if host_round_id is not None else current_pair.get("question_host_round_id"),
    )
    if host_round is None:
        _apply_court_question_state(
            current_pair,
            host_round_id=None,
            question_active=False,
            question_status="closed",
        )
        payload["current_pair"] = current_pair
        payload["current_question"] = None
        return _decorate_court_payload(payload)

    runtime_question = (
        db.query(GameHostRoundQuestion)
        .filter(GameHostRoundQuestion.host_round_id == host_round.id)
        .order_by(GameHostRoundQuestion.sequence_no.desc(), GameHostRoundQuestion.id.desc())
        .first()
    )

    question_payload = _build_question_payload(runtime_question)
    if runtime_question is None:
        question_status = "closed"
        question_active = False
    elif runtime_question.status == "active" and runtime_question.answers_open:
        question_status = "active"
        question_active = True
        if current_pair.get("status") not in PAIR_FINISHED_STATUSES:
            current_pair["status"] = "question_active"
    elif runtime_question.status in {"resolved", "closed"} or runtime_question.answers_open is False:
        question_status = "reveal"
        question_active = False
        if current_pair.get("status") not in PAIR_FINISHED_STATUSES and current_pair.get("status") not in {"needs_extra_question", "sudden_death"}:
            current_pair["status"] = "question_reveal"
    else:
        question_status = runtime_question.status or "closed"
        question_active = False

    _apply_court_question_state(
        current_pair,
        host_round_id=host_round.id,
        question_active=question_active,
        question_no=host_round.current_question_no or current_pair.get("question_no") or 0,
        question_status=question_status,
    )
    payload["current_pair"] = current_pair
    payload["current_question"] = question_payload
    return _decorate_court_payload(payload)


def get_court_runtime_logic(db: Session, room_code: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
        }

    phase = _get_active_court_phase(db, game)
    return {
        "ok": True,
        "court": _decorate_court_payload(phase.payload) if phase else None,
    }


def get_court_state_logic(db: Session, room_code: str) -> dict[str, Any]:
    runtime_result = get_court_runtime_logic(db, room_code)
    if not runtime_result.get("ok"):
        return runtime_result

    game = _get_game_by_room_code(db, room_code)
    court_payload = build_court_runtime_view_logic(
        db,
        room_code,
        runtime_result.get("court"),
    )
    return {
        "ok": True,
        "game": _game_payload(game),
        "court": court_payload,
    }


def _ensure_winner_entry(
    payload: dict[str, Any],
    *,
    winner_house_id: int,
    winner_house_name: str,
    pair_no: int | None,
    source: str,
) -> None:
    winners = payload.setdefault("winners", [])
    for item in winners:
        if int(item.get("house_id") or 0) == int(winner_house_id):
            item["pair_no"] = pair_no
            item["source"] = source
            item["house_name"] = winner_house_name
            return
    winners.append(
        {
            "house_id": int(winner_house_id),
            "house_name": winner_house_name,
            "pair_no": pair_no,
            "source": source,
        }
    )


def _append_warning(payload: dict[str, Any], warning_code: str) -> None:
    warnings = payload.setdefault("warnings", [])
    if warning_code not in warnings:
        warnings.append(warning_code)


def _finish_active_court_host_rounds(db: Session, game_id: int) -> None:
    court_host_rounds = (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game_id,
            GameHostRound.round_code == COURT_QUESTION_ROUND_CODE,
            GameHostRound.status.in_(["active", "completed_waiting_host"]),
        )
        .all()
    )
    for host_round in court_host_rounds:
        host_round.answers_open = False
        host_round.status = "finished"
        db.add(host_round)


def _decorate_court_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = _normalize_court_payload(payload)
    history = normalized.get("history") or []
    bracket = normalized.get("bracket") or []
    current_pair = normalized.get("current_pair")
    winners = normalized.setdefault("winners", [])
    normalized.setdefault("used_questions", [])
    normalized.setdefault("warnings", [])

    bye_houses = [
        {
            "house_id": item.get("house_id"),
            "house_name": item.get("house_name"),
            "seed": item.get("seed"),
        }
        for item in history
        if item.get("type") == "bye"
    ]
    normalized["bye_houses"] = bye_houses
    for item in bye_houses:
        if item.get("house_id") is not None:
            _ensure_winner_entry(
                normalized,
                winner_house_id=int(item["house_id"]),
                winner_house_name=item.get("house_name") or f'Дом #{item["house_id"]}',
                pair_no=None,
                source="bye",
            )

    eliminated_houses = []
    for pair in bracket:
        winner_id = pair.get("winner_house_id")
        if winner_id is None:
            continue
        if int(winner_id) == int(pair.get("house_a_id") or 0):
            eliminated_houses.append(
                {
                    "pair_no": pair.get("pair_no"),
                    "house_id": pair.get("house_b_id"),
                    "house_name": pair.get("house_b_name"),
                }
            )
        else:
            eliminated_houses.append(
                {
                    "pair_no": pair.get("pair_no"),
                    "house_id": pair.get("house_a_id"),
                    "house_name": pair.get("house_a_name"),
                }
            )
    normalized["eliminated_houses"] = eliminated_houses

    pending_pairs = [pair for pair in bracket if pair.get("status") == "pending"]
    winner_confirmed = bool(current_pair and _is_pair_winner_confirmed(normalized, current_pair.get("pair_no")))
    pair_finished = bool(current_pair and current_pair.get("status") in PAIR_FINISHED_STATUSES)

    normalized["pending_pairs_count"] = len(pending_pairs)
    normalized["remaining_pairs"] = len(pending_pairs)
    normalized["winner_confirmed"] = winner_confirmed
    normalized["can_start_next_pair"] = bool(not current_pair and pending_pairs)
    normalized["can_finish_pair"] = bool(pair_finished and winner_confirmed and not pending_pairs)
    normalized["can_advance_pair"] = bool(pair_finished and winner_confirmed and pending_pairs)
    normalized["is_finished"] = pick_status = str(normalized.get("status") or "").strip().lower() == "court_finished"
    if pick_status:
        normalized["current_pair"] = None
        normalized["current_pair_index"] = None
        normalized["current_question"] = None
        normalized["can_start_next_pair"] = False

    return normalized


def _create_court_host_round(db: Session, game: Game, round_template: RoundTemplate, *, current_question_no: int = 0) -> GameHostRound:
    host_round = GameHostRound(
        game_id=game.id,
        template_pool_id=None,
        template_task_id=None,
        round_template_id=round_template.id,
        round_code=round_template.round_code,
        act_number=round_template.act_number,
        round_kind=round_template.round_kind,
        role_code=round_template.questions[0].role_code if round_template.questions else "court_mvp",
        title=round_template.title,
        prompt=round_template.intro_text,
        ui_template=None,
        questions_total=round_template.questions_total,
        current_question_no=current_question_no,
        answers_open=False,
        intro_shown=False,
        outro_shown=False,
        status="active",
    )
    db.add(host_round)
    db.flush()
    return host_round


def generate_court_bracket_logic(db: Session, room_code: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    ranked_houses = _build_ranked_houses(game)
    if len(ranked_houses) < 2:
        return {"ok": False, "message": "Для суда нужно минимум два Дома"}

    phase = _get_or_create_court_phase(db, game)
    bracket, history_events = _build_bracket_from_ranked_houses(ranked_houses)

    payload = _normalize_court_payload(phase.payload)
    payload["bracket"] = bracket
    payload["current_pair_index"] = None
    payload["current_pair"] = None
    payload["current_question"] = None
    payload["history"] = list(history_events)
    payload["status"] = "bracket_ready"
    payload["winners"] = []
    payload["used_questions"] = []
    payload["warnings"] = []
    if history_events:
        payload["last_event"] = history_events[-1]
    payload.pop("next_pair", None)

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def start_court_pair_logic(db: Session, room_code: str, *, pair_no: int | None = None) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)

    existing_pair = payload.get("current_pair")
    if isinstance(existing_pair, dict) and existing_pair.get("status") not in PAIR_FINISHED_STATUSES:
        return {"ok": False, "message": "Текущая пара ещё не завершена"}

    index, bracket_pair = _find_bracket_pair(payload, pair_no=pair_no)
    if bracket_pair is None:
        payload["status"] = "court_finished"
        payload["current_pair"] = None
        payload["current_pair_index"] = None
        payload["current_question"] = None
        _finish_active_court_host_rounds(db, game.id)
        _append_history(payload, {"type": "court_finished", "next_pair_no": None})
        payload = _decorate_court_payload(payload)
        _save_court_phase(db, phase, payload)
        return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}

    if bracket_pair.get("status") != "pending":
        return {"ok": False, "message": "Эту пару уже нельзя запустить"}

    bracket_pair["status"] = "active"
    current_pair = {
        "pair_no": bracket_pair["pair_no"],
        "house_a_id": bracket_pair["house_a_id"],
        "house_b_id": bracket_pair["house_b_id"],
        "house_a_name": bracket_pair["house_a_name"],
        "house_b_name": bracket_pair["house_b_name"],
        "seed_a": bracket_pair["seed_a"],
        "seed_b": bracket_pair["seed_b"],
        "house_a_alive": COURT_TEAM_SIZE,
        "house_b_alive": COURT_TEAM_SIZE,
        "house_a_eliminated": 0,
        "house_b_eliminated": 0,
        "questions_used": 0,
        "max_questions": COURT_MAX_QUESTIONS,
        "status": "pair_intro",
        "sudden_death": False,
        "winner_house_id": None,
        **_build_court_question_state(),
    }

    payload["current_pair_index"] = index
    payload["current_pair"] = current_pair
    payload["status"] = "pair_active"
    payload["current_question"] = None
    payload.pop("next_pair", None)
    _append_history(
        payload,
        {
            "type": "pair_started",
            "pair_no": current_pair["pair_no"],
            "house_a_id": current_pair["house_a_id"],
            "house_b_id": current_pair["house_b_id"],
            "house_a_name": current_pair["house_a_name"],
            "house_b_name": current_pair["house_b_name"],
        },
    )

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def mark_court_result_logic(db: Session, room_code: str, *, side: str, result: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)
    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        return {"ok": False, "message": "Сейчас нет активной пары"}

    if not bool(current_pair.get("question_active")):
        if str(current_pair.get("question_status") or "").strip().lower() == "reveal":
            return {
                "ok": False,
                "already_applied": True,
                "message": "Результат по текущему вопросу суда уже применён",
            }
        return {"ok": False, "message": "Сейчас нет активного вопроса суда"}

    normalized_side = str(side or "").strip().lower()
    normalized_result = str(result or "").strip().lower()
    if normalized_side not in {"a", "b"}:
        return {"ok": False, "message": "Сторона должна быть 'a' или 'b'"}
    if normalized_result not in {"correct", "wrong"}:
        return {"ok": False, "message": "Результат должен быть 'correct' или 'wrong'"}
    if current_pair.get("status") in PAIR_FINISHED_STATUSES:
        return {"ok": False, "message": "Текущая пара уже завершена"}

    host_round = _get_court_question_host_round(
        db,
        game=game,
        host_round_id=current_pair.get("question_host_round_id"),
    )
    if host_round is None:
        return {"ok": False, "message": "Сейчас нет активного вопроса суда"}

    active_runtime_question = (
        db.query(GameHostRoundQuestion)
        .filter(
            GameHostRoundQuestion.host_round_id == host_round.id,
            GameHostRoundQuestion.status == "active",
        )
        .order_by(GameHostRoundQuestion.sequence_no.desc(), GameHostRoundQuestion.id.desc())
        .first()
    )
    if active_runtime_question is None or active_runtime_question.answers_open is False:
        return {
            "ok": False,
            "already_applied": True,
            "message": "Результат по текущему вопросу суда уже применён",
        }

    loser_side = "b" if (normalized_side == "a" and normalized_result == "correct") else "a" if (normalized_side == "b" and normalized_result == "correct") else normalized_side
    loser_house_id = current_pair.get("house_b_id") if loser_side == "b" else current_pair.get("house_a_id")
    loser_house_name = current_pair.get("house_b_name") if loser_side == "b" else current_pair.get("house_a_name")

    if loser_side == "a":
        current_pair["house_a_alive"] = max(0, int(current_pair.get("house_a_alive") or 0) - 1)
        current_pair["house_a_eliminated"] = int(current_pair.get("house_a_eliminated") or 0) + 1
    else:
        current_pair["house_b_alive"] = max(0, int(current_pair.get("house_b_alive") or 0) - 1)
        current_pair["house_b_eliminated"] = int(current_pair.get("house_b_eliminated") or 0) + 1

    current_pair["questions_used"] = int(current_pair.get("questions_used") or 0) + 1
    current_pair["question_active"] = False
    current_pair["question_status"] = "reveal"
    close_result = _force_close_current_question_by_host(db, host_round)
    if not close_result.get("ok"):
        db.rollback()
        return close_result

    _append_history(
        payload,
        {
            "type": "court_answer_result",
            "pair_no": current_pair.get("pair_no"),
            "side": normalized_side,
            "result": normalized_result,
            "loser_side": loser_side,
            "loser_house_id": loser_house_id,
            "loser_house_name": loser_house_name,
            "house_a_alive": current_pair.get("house_a_alive"),
            "house_b_alive": current_pair.get("house_b_alive"),
        },
    )

    winner_house_id = None
    if int(current_pair.get("house_a_alive") or 0) <= 0:
        winner_house_id = current_pair.get("house_b_id")
    elif int(current_pair.get("house_b_alive") or 0) <= 0:
        winner_house_id = current_pair.get("house_a_id")

    if winner_house_id is not None:
        current_pair["winner_house_id"] = winner_house_id
        current_pair["status"] = "pair_result"
    elif int(current_pair.get("questions_used") or 0) >= int(current_pair.get("max_questions") or COURT_MAX_QUESTIONS):
        current_pair["status"] = "needs_extra_question"
        current_pair["sudden_death"] = True
    else:
        current_pair["status"] = "question_reveal"

    _sync_bracket_pair(payload, current_pair)
    payload["current_pair"] = current_pair
    payload["status"] = "pair_active"

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def court_extra_question_logic(db: Session, room_code: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)
    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        return {"ok": False, "message": "Сейчас нет активной пары"}

    current_pair["sudden_death"] = True
    current_pair["status"] = "sudden_death"
    current_pair["max_questions"] = int(current_pair.get("max_questions") or COURT_MAX_QUESTIONS) + 1
    payload["current_pair"] = current_pair
    payload["status"] = "pair_active"
    _append_history(
        payload,
        {
            "type": "extra_question",
            "pair_no": current_pair.get("pair_no"),
            "max_questions": current_pair.get("max_questions"),
        },
    )

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def confirm_court_pair_winner_logic(db: Session, room_code: str, *, winner_house_id: int) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)
    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        return {"ok": False, "message": "Сейчас нет активной пары"}

    valid_house_ids = {current_pair.get("house_a_id"), current_pair.get("house_b_id")}
    if int(winner_house_id) not in {int(item) for item in valid_house_ids if item is not None}:
        return {"ok": False, "message": "Победитель не участвует в текущей паре"}

    current_pair["winner_house_id"] = int(winner_house_id)
    current_pair["status"] = "pair_result"
    payload["current_pair"] = current_pair
    payload["status"] = "pair_active"
    _sync_bracket_pair(payload, current_pair)
    winner_name = (
        current_pair.get("house_a_name")
        if int(winner_house_id) == int(current_pair.get("house_a_id") or 0)
        else current_pair.get("house_b_name")
    ) or f"Дом #{winner_house_id}"
    _ensure_winner_entry(
        payload,
        winner_house_id=int(winner_house_id),
        winner_house_name=winner_name,
        pair_no=current_pair.get("pair_no"),
        source="pair",
    )
    _append_history(
        payload,
        {
            "type": "pair_winner_confirmed",
            "pair_no": current_pair.get("pair_no"),
            "winner_house_id": int(winner_house_id),
            "winner_house_name": winner_name,
        },
    )

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def next_court_pair_logic(db: Session, room_code: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)
    current_pair = payload.get("current_pair")

    if isinstance(current_pair, dict) and current_pair.get("status") not in PAIR_FINISHED_STATUSES:
        return {"ok": False, "message": "Текущая пара ещё не завершена"}
    if isinstance(current_pair, dict) and current_pair.get("winner_house_id") and not _is_pair_winner_confirmed(payload, current_pair.get("pair_no")):
        return {"ok": False, "message": "Сначала подтвердите победителя пары"}

    payload["current_pair"] = None
    payload["current_pair_index"] = None
    payload["current_question"] = None

    _, next_pair = _find_bracket_pair(payload)
    if next_pair is None:
        payload["status"] = "court_finished"
        payload.pop("next_pair", None)
        _finish_active_court_host_rounds(db, game.id)
    else:
        payload["status"] = "bracket_ready"
        payload["next_pair"] = {
            "pair_no": next_pair.get("pair_no"),
            "house_a_id": next_pair.get("house_a_id"),
            "house_b_id": next_pair.get("house_b_id"),
            "house_a_name": next_pair.get("house_a_name"),
            "house_b_name": next_pair.get("house_b_name"),
            "seed_a": next_pair.get("seed_a"),
            "seed_b": next_pair.get("seed_b"),
        }

    _append_history(
        payload,
        {
            "type": "next_pair_ready" if next_pair is not None else "court_finished",
            "next_pair_no": next_pair.get("pair_no") if next_pair is not None else None,
        },
    )

    payload = _decorate_court_payload(payload)
    _save_court_phase(db, phase, payload)
    return {"ok": True, "game": _game_payload(game), "court": _decorate_court_payload(phase.payload)}


def open_court_question_logic(db: Session, room_code: str) -> dict[str, Any]:
    game = _get_game_by_room_code(db, room_code)
    if not game:
        return {"ok": False, "message": "Игра не найдена"}

    phase = _get_or_create_court_phase(db, game)
    payload = _decorate_court_payload(phase.payload)
    current_pair = payload.get("current_pair")
    if not isinstance(current_pair, dict):
        return {"ok": False, "message": "Сейчас нет активной пары"}
    if current_pair.get("status") in PAIR_FINISHED_STATUSES:
        return {"ok": False, "message": "Текущая пара уже завершена"}
    if current_pair.get("question_active"):
        return {"ok": False, "message": "Вопрос суда уже активен"}

    round_template = _ensure_court_question_round_template(db, game)
    if round_template is None or len(round_template.questions or []) == 0:
        db.rollback()
        return {"ok": False, "message": "Не найден шаблон court-вопросов"}

    question_templates = sorted(list(round_template.questions or []), key=lambda item: (item.sequence_no or 0, item.id or 0))
    used_questions = payload.setdefault("used_questions", [])
    selected_question = next((item for item in question_templates if item.question_code not in used_questions), None)
    if selected_question is None and question_templates:
        selected_question = question_templates[0]
        _append_warning(payload, "court_question_bank_exhausted")

    if selected_question is None:
        db.rollback()
        return {"ok": False, "message": "Банк court-вопросов пуст"}

    _ensure_host_round_phase_active(db, game)
    db.flush()

    selected_sequence_no = int(selected_question.sequence_no or 1)
    host_round = _get_court_question_host_round(
        db,
        game=game,
        host_round_id=current_pair.get("question_host_round_id"),
    )

    if host_round is None or host_round.status != "active":
        host_round = _create_court_host_round(
            db,
            game,
            round_template,
            current_question_no=max(0, selected_sequence_no - 1),
        )
    else:
        host_round.status = "active"
        host_round.answers_open = False
        host_round.current_question_no = max(0, selected_sequence_no - 1)
        db.add(host_round)
        db.flush()

    result = _open_next_question_for_host_round(
        db=db,
        host_round=host_round,
        house_key_allowed_fn=lambda _allowed, _key: True,
    )

    if not result.get("ok") and "все вопросы" in str(result.get("message") or "").lower():
        host_round = _create_court_host_round(
            db,
            game,
            round_template,
            current_question_no=max(0, selected_sequence_no - 1),
        )
        result = _open_next_question_for_host_round(
            db=db,
            host_round=host_round,
            house_key_allowed_fn=lambda _allowed, _key: True,
        )

    if not result.get("ok"):
        db.rollback()
        return result

    runtime_question = result["runtime_question"]
    question_template = result["question_template"]
    if question_template and question_template.question_code not in used_questions:
        used_questions.append(question_template.question_code)

    current_pair["status"] = "question_active"
    _apply_court_question_state(
        current_pair,
        host_round_id=host_round.id,
        question_active=True,
        question_no=runtime_question.sequence_no,
        question_status="active",
    )
    current_pair["last_question_code"] = question_template.question_code if question_template else None
    payload["current_pair"] = current_pair
    payload["status"] = "pair_active"
    _append_history(
        payload,
        {
            "type": "court_question_opened",
            "pair_no": current_pair.get("pair_no"),
            "question_no": runtime_question.sequence_no,
            "host_round_id": host_round.id,
            "question_code": question_template.question_code if question_template else None,
        },
    )
    phase.payload = _normalize_court_payload(payload)
    db.add(phase)
    db.flush()

    sync_result = sync_court_question_runtime_logic(db, room_code, host_round_id=host_round.id)
    db.commit()
    db.refresh(host_round)
    db.refresh(phase)

    return {
        "ok": True,
        "message": "Вопрос суда открыт",
        "warning": "court_question_bank_exhausted" if "court_question_bank_exhausted" in payload.get("warnings", []) else None,
        "game": _game_payload(game),
        "court": _decorate_court_payload(sync_result.get("court") if isinstance(sync_result, dict) and sync_result.get("ok") else _normalize_court_payload(phase.payload)),
        "host_round": {
            "id": host_round.id,
            "round_code": host_round.round_code,
            "title": host_round.title,
            "status": host_round.status,
            "questions_total": host_round.questions_total,
            "current_question_no": host_round.current_question_no,
            "answers_open": host_round.answers_open,
        },
        "runtime_question": {
            "id": runtime_question.id,
            "sequence_no": runtime_question.sequence_no,
            "status": runtime_question.status,
            "answers_open": runtime_question.answers_open,
        },
        "question_template": _build_question_payload(runtime_question),
        "created_assignments_count": len(result.get("created_assignment_ids") or []),
        "created_assignment_ids": result.get("created_assignment_ids") or [],
    }
