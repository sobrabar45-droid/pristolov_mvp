import json

from sqlalchemy.orm import Session
from copy import deepcopy

from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.game_phase import GamePhase
from app.models.game_deal import GameDeal
from app.models.game_assignment import GameAssignment
from app.models.game_host_round import GameHostRound
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.game_duel import GameDuel
from app.models.game_expedition import GameExpedition
from app.models.game_map_visit import GameMapVisit
from app.models.game_house_tower import GameHouseTower
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate
from app.services.scenario_service import get_scenario_director_logic
from app.services.court_service import (
    build_court_runtime_view_logic,
    get_court_runtime_logic,
)


def _text_quality_score(text):
    if not isinstance(text, str):
        return 0
    cyrillic_count = sum(1 for ch in text if "\u0400" <= ch <= "\u04FF")
    mojibake_markers = (
        text.count("Р")
        + text.count("С")
        + text.count("Ñ")
        + text.count("Ð")
        + text.count("Г‘")
        + text.count("Гѓ")
        + text.count("Г‚")
        + text.count("пїЅ")
    )
    return cyrillic_count - (mojibake_markers * 4)


def fix_encoding(text):
    if not isinstance(text, str) or not text:
        return text

    candidates = [text]
    for encoding in ("latin1", "cp1251"):
        try:
            candidates.append(text.encode(encoding).decode("utf-8"))
        except Exception:
            pass
    return max(candidates, key=_text_quality_score)


def _get_tower_class(score: int) -> str:
    if score is None:
        score = 0
    if score <= 2:
        return "none"
    if score <= 5:
        return "minor"
    if score <= 8:
        return "strong"
    return "dominant"


def _build_master_prompt(*, active_host_round, current_question, duels_block, expeditions_block, active_phases, court_runtime=None):
    if current_question and current_question.get("status") == "active":
        return {
            "title": "Вопрос в работе",
            "body": "Жди ответы или закрой вопрос вручную",
            "severity": "high",
        }

    if isinstance(court_runtime, dict):
        court_status = str(court_runtime.get("status") or "").strip().lower()
        court_pair = court_runtime.get("current_pair")
        if (
            court_status == "bracket_ready"
            and not isinstance(court_pair, dict)
            and bool(court_runtime.get("can_start_next_pair"))
        ):
            return {
                "title": "Суд готов",
                "body": "Сетка Суда готова. Следующий безопасный шаг — начать первую пару.",
                "severity": "high",
            }

    if active_host_round and active_host_round.get("status") == "active" and not current_question:
        current_no = int(active_host_round.get("current_question_no") or 0)
        questions_total = int(active_host_round.get("questions_total") or 0)
        if questions_total > 0:
            next_no = min(current_no + 1, questions_total)
            body = f"Раунд активен. Следующий безопасный шаг — открыть вопрос {next_no}/{questions_total}."
        else:
            body = "Раунд активен, но вопрос ещё не открыт. Подготовь зал и открой следующий вопрос."
        return {
            "title": "Раунд активен",
            "body": body,
            "severity": "medium",
        }

    if active_host_round and active_host_round.get("status") == "completed_waiting_host":
        return {
            "title": "Раунд ждёт ведущего",
            "body": "Подтверди завершение раунда",
            "severity": "high",
        }

    challenged_duels = (duels_block or {}).get("challenged", [])
    if challenged_duels:
        return {
            "title": "Есть вызов на дуэль",
            "body": "Озвучь вызов и зафиксируй принятие или отказ",
            "severity": "high",
        }

    ready_live_duels = [
        duel for duel in (duels_block or {}).get("active_or_pending", [])
        if duel.get("status") == "accepted" and duel.get("live_bonus_label")
    ]
    if ready_live_duels:
        return {
            "title": "Дуэль готова к сцене",
            "body": "Озвучь бонус дуэли и запускай состязание",
            "severity": "medium",
        }

    planned_without_approval = [
        expedition for expedition in (expeditions_block or {}).get("planned", [])
        if not expedition.get("approved_by_player_id")
    ]
    if planned_without_approval:
        return {
            "title": "Экспедиция ждёт решения",
            "body": "Лорд должен утвердить экспедицию",
            "severity": "medium",
        }

    active_phase_types = [phase.phase_type for phase in (active_phases or [])]
    if "last_whisper" in active_phase_types:
        return {
            "title": "Последний Шёпот открыт",
            "body": "Дай Домам короткое окно на интриги и затем переводи игру к финалу.",
            "severity": "medium",
        }
    phase_text = ", ".join(active_phase_types) if active_phase_types else "нет активной фазы"
    return {
        "title": "Окно перехода",
        "body": f"Можно переводить игру дальше. Сейчас активны: {phase_text}.",
        "severity": "low",
    }


STAGE_BRIEFING_COPY = {
    "opening": {
        "title": "Открытие игры",
        "instruction": "Соберите Дом, проверьте роли и готовьтесь к первому раунду.",
        "roles": "Весь Дом",
        "movement": "Не расходимся.",
    },
    "warmup": {
        "title": "Быстрый раунд",
        "instruction": "Слушайте ведущего. Отвечайте быстро, время ограничено.",
        "roles": "Весь Дом",
        "movement": "Не расходимся.",
    },
    "map": {
        "title": "Экспедиция",
        "instruction": "Лорд / Леди назначает участников. Назначенные игроки выбирают направление.",
        "roles": "Лорд / Леди и участники экспедиции",
        "movement": "Назначенные игроки остаются на связи.",
    },
    "diplomacy": {
        "title": "Дипломатия",
        "instruction": "Дипломаты выходят на переговоры. Дома могут заключать союзы.",
        "roles": "Дипломаты, Лорд / Леди",
        "movement": "Дипломатам можно перемещаться.",
    },
    "free_play": {
        "title": "Свободная игра",
        "instruction": "Дома используют доступные действия: переговоры, золото, экспедиции и решения роли.",
        "roles": "Все активные роли",
        "movement": "Можно двигаться, но следите за объявлениями.",
    },
    "duel": {
        "title": "Дуэли Домов",
        "instruction": "Лорд / Леди следит за вызовами. Участники дуэли подходят к месту игры.",
        "roles": "Лорд / Леди, участники дуэли",
        "movement": "Не уходите далеко.",
    },
    "court": {
        "title": "Суд Домов",
        "instruction": "Дома готовятся к парам. Ведущий объявит порядок выступлений.",
        "roles": "Представители Домов",
        "movement": "Не расходимся.",
    },
    "last_whisper": {
        "title": "Последний Шёпот",
        "instruction": "Мастер над шёпотом делает тайный ход перед финалом.",
        "roles": "Мастер над шёпотом",
        "movement": "Следите за экраном.",
    },
    "final": {
        "title": "Финал",
        "instruction": "Один Дом выходит к финальному испытанию против игротехника.",
        "roles": "Финалисты и весь зал",
        "movement": "Не расходимся.",
    },
}


def _stage_briefing_key_from_code(raw_code: str | None) -> str | None:
    code = str(raw_code or "").strip().lower()
    if not code:
        return None

    exact = {
        "opening": "opening",
        "intro": "opening",
        "stage_opening": "opening",
        "host_round": "warmup",
        "truth_false": "warmup",
        "stage_truth_false": "warmup",
        "stage_warmup": "warmup",
        "stage_light_questions": "warmup",
        "stage_map_entry": "map",
        "map": "map",
        "expedition": "map",
        "stage_diplomacy_1": "diplomacy",
        "diplomacy": "diplomacy",
        "stage_free_play": "free_play",
        "free_play": "free_play",
        "stage_duels": "duel",
        "duel": "duel",
        "stage_court": "court",
        "stage_court_battle": "court",
        "court": "court",
        "stage_last_whisper": "last_whisper",
        "last_whisper": "last_whisper",
        "stage_final": "final",
        "stage_final_show": "final",
        "final": "final",
    }
    if code in exact:
        return exact[code]

    if "diplom" in code:
        return "diplomacy"
    if "whisper" in code:
        return "last_whisper"
    if "court" in code:
        return "court"
    if "duel" in code:
        return "duel"
    if "map" in code or "expedition" in code:
        return "map"
    if "free" in code:
        return "free_play"
    if "final" in code:
        return "final"
    if "truth" in code or "warmup" in code or "question" in code or "round" in code:
        return "warmup"
    if "open" in code or "intro" in code:
        return "opening"
    return None


def _build_stage_briefing_payload(*, scenario_director_payload=None, active_host_round=None, active_phases=None):
    candidate_codes = []
    if isinstance(active_host_round, dict):
        candidate_codes.append(active_host_round.get("round_code"))
        candidate_codes.append(active_host_round.get("phase_code"))

    director = scenario_director_payload if isinstance(scenario_director_payload, dict) else {}
    for key in ("current_round", "active_host_round", "next_round"):
        round_payload = director.get(key)
        if isinstance(round_payload, dict):
            candidate_codes.append(round_payload.get("round_code"))
            candidate_codes.append(round_payload.get("phase_code"))

    active_stage = director.get("active_system_stage_phase")
    if isinstance(active_stage, dict):
        candidate_codes.append(active_stage.get("phase_type"))
        payload = active_stage.get("payload")
        if isinstance(payload, dict):
            candidate_codes.append(payload.get("round_code"))

    for phase in active_phases or []:
        candidate_codes.append(getattr(phase, "phase_type", None))

    stage_key = None
    source_code = None
    for code in candidate_codes:
        stage_key = _stage_briefing_key_from_code(code)
        if stage_key:
            source_code = str(code or "").strip()
            break

    if not stage_key:
        return {
            "active": False,
            "stage_key": "waiting",
            "source_code": None,
            "title": "Ожидание этапа",
            "instruction": "Ведущий скоро объявит следующий шаг.",
            "roles": "Весь Дом",
            "movement": "Оставайтесь на связи с экраном.",
            "sound_cue": False,
        }

    briefing = STAGE_BRIEFING_COPY[stage_key]
    return {
        "active": True,
        "stage_key": stage_key,
        "source_code": source_code,
        "title": briefing["title"],
        "instruction": briefing["instruction"],
        "roles": briefing["roles"],
        "movement": briefing["movement"],
        "sound_cue": True,
    }


def _get_last_whisper_phase(active_phases):
    for phase in active_phases or []:
        if getattr(phase, "phase_type", None) == "last_whisper" and getattr(phase, "status", None) == "active":
            return phase
    return None


def _serialize_last_whisper_event(raw_event: dict) -> dict:
    house_name = fix_encoding(str(raw_event.get("house_name") or "").strip())
    action_label = fix_encoding(str(raw_event.get("action_label") or "").strip())
    tv_text = fix_encoding(str(raw_event.get("tv_text") or "").strip())
    player_name = fix_encoding(str(raw_event.get("player_name") or "").strip())
    target_house_name = fix_encoding(str(raw_event.get("target_house_name") or "").strip())
    return {
        "order_no": raw_event.get("order_no"),
        "created_at": raw_event.get("created_at"),
        "house_id": raw_event.get("house_id"),
        "house_name": house_name or None,
        "target_house_id": raw_event.get("target_house_id"),
        "target_house_name": target_house_name or None,
        "player_id": raw_event.get("player_id"),
        "player_name": player_name or None,
        "action_code": str(raw_event.get("action_code") or "").strip().lower() or None,
        "action_label": action_label or None,
        "tv_text": tv_text or None,
        "resources_changed": raw_event.get("resources_changed") if isinstance(raw_event.get("resources_changed"), dict) else {},
    }


def _build_last_whisper_payload(active_phases):
    phase = _get_last_whisper_phase(active_phases)
    if not phase:
        return None

    payload = phase.payload if isinstance(phase.payload, dict) else {}
    raw_events = payload.get("whisper_actions")
    events = []
    if isinstance(raw_events, list):
        events = [
            _serialize_last_whisper_event(item)
            for item in raw_events
            if isinstance(item, dict)
        ]

    return {
        "active": True,
        "phase_id": phase.id,
        "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
        "events": events,
        "latest_event": events[-1] if events else None,
        "events_count": len(events),
    }


def _build_treasurer_shop_events(db: Session, *, game_id: int, limit: int = 5) -> list[dict]:
    if not game_id:
        return []

    rows = (
        db.query(HouseGoldTransaction)
        .filter(
            HouseGoldTransaction.game_id == game_id,
            HouseGoldTransaction.source_type == "treasurer_shop",
        )
        .order_by(HouseGoldTransaction.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": row.id,
            "type": "treasurer_shop",
            "title": "Покупка Мастера золота",
            "text": row.reason,
            "house_id": row.house_id,
            "gold_delta": row.amount,
            "gold_before": row.balance_before,
            "gold_after": row.balance_after,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]


def _build_recent_events_payload(
    *,
    last_whisper_payload=None,
    broken_alliances_recent=None,
    duels_block=None,
    recent_closed_deals=None,
    treasurer_shop_events=None,
    event_feed=None,
    limit: int = 10,
):
    events = []

    def add_event(
        *,
        event_type: str,
        title: str,
        text: str | None,
        created_at=None,
        source: str,
        severity: str = "info",
        sort_key=None,
    ):
        clean_text = fix_encoding(str(text or "").strip())
        if not clean_text:
            return
        clean_title = fix_encoding(str(title or event_type or "event").strip())
        effective_sort_key = sort_key or created_at or ""
        events.append(
            {
                "type": event_type,
                "title": clean_title or event_type,
                "text": clean_text,
                "created_at": created_at,
                "sort_key": effective_sort_key,
                "source": source,
                "severity": severity,
            }
        )

    latest_whisper = None
    if isinstance(last_whisper_payload, dict):
        candidate = last_whisper_payload.get("latest_event")
        if isinstance(candidate, dict):
            latest_whisper = candidate
    if latest_whisper:
        add_event(
            event_type="last_whisper",
            title=latest_whisper.get("action_label") or "Последний Шёпот",
            text=latest_whisper.get("tv_text"),
            created_at=latest_whisper.get("created_at"),
            source="last_whisper.latest_event",
            severity="high",
            sort_key=latest_whisper.get("created_at") or latest_whisper.get("order_no"),
        )

    for item in broken_alliances_recent or []:
        if not isinstance(item, dict):
            continue
        house_a = item.get("house_a") or {}
        house_b = item.get("house_b") or {}
        fallback_text = None
        if isinstance(house_a, dict) and isinstance(house_b, dict):
            house_a_name = house_a.get("name") or "Дом"
            house_b_name = house_b.get("name") or "Дом"
            fallback_text = f"{house_a_name} и {house_b_name} больше не связаны союзом."
        add_event(
            event_type="alliance_broken",
            title="Союз разрушен",
            text=item.get("break_text") or fallback_text,
            created_at=item.get("broken_at"),
            source="broken_alliances_recent",
            severity="high",
            sort_key=item.get("broken_at") or item.get("id"),
        )

    for duel in (duels_block or {}).get("recent", [])[:3]:
        if not isinstance(duel, dict):
            continue
        status = str(duel.get("status") or "").strip()
        challenger = (duel.get("challenger_house") or {}).get("name") if isinstance(duel.get("challenger_house"), dict) else None
        target = (duel.get("target_house") or {}).get("name") if isinstance(duel.get("target_house"), dict) else None
        challenger = challenger or duel.get("challenger_house_name") or "Дом"
        target = target or duel.get("target_house_name") or "Дом"
        winner = (duel.get("winner_house") or {}).get("name") if isinstance(duel.get("winner_house"), dict) else None
        if status == "resolved" and winner:
            text = f"Победа в дуэли: {winner}"
            severity = "ok"
        elif status == "refused":
            text = f"{target} отказался от дуэли с {challenger}"
            severity = "warn"
        elif status == "canceled":
            text = f"Дуэль {challenger} и {target} отменена"
            severity = "warn"
        else:
            text = f"Дуэль {challenger} и {target}: {status}"
            severity = "info"
        add_event(
            event_type="duel",
            title="Дуэль Домов",
            text=text,
            created_at=duel.get("resolved_at") or duel.get("created_at"),
            source="duels.recent",
            severity=severity,
            sort_key=duel.get("resolved_at") or duel.get("created_at") or duel.get("id"),
        )

    for deal in recent_closed_deals or []:
        if not isinstance(deal, dict):
            continue
        from_house = deal.get("from_house") or {}
        to_house = deal.get("to_house") or {}
        from_name = from_house.get("name") if isinstance(from_house, dict) else None
        to_name = to_house.get("name") if isinstance(to_house, dict) else None
        status = str(deal.get("status") or "").strip()
        route_text = f"{from_name or 'Дом'} → {to_name or 'Дом'}"
        offer_text = deal.get("offer_text") or deal.get("note")
        if offer_text:
            route_text = f"{route_text}: {offer_text}"
        add_event(
            event_type="deal",
            title="Дипломатическая сделка",
            text=route_text,
            created_at=deal.get("responded_at") or deal.get("created_at"),
            source="deals.recent_closed",
            severity="ok" if status in {"accepted", "completed"} else "info",
            sort_key=deal.get("responded_at") or deal.get("created_at") or deal.get("id"),
        )

    for item in treasurer_shop_events or []:
        if not isinstance(item, dict):
            continue
        add_event(
            event_type="treasurer_shop",
            title=item.get("title") or "Покупка Мастера золота",
            text=item.get("text"),
            created_at=item.get("created_at"),
            source="treasurer_shop.purchase",
            severity="ok",
            sort_key=item.get("created_at") or item.get("id"),
        )

    for item in event_feed or []:
        if not isinstance(item, dict):
            continue
        add_event(
            event_type=item.get("type") or "event",
            title=item.get("title") or "Событие",
            text=item.get("text"),
            created_at=item.get("created_at"),
            source="event_feed",
            severity=item.get("severity") or "info",
            sort_key=item.get("created_at"),
        )

    def event_sort_key(item):
        key = item.get("sort_key")
        if key is None:
            return ""
        return str(key)

    return sorted(events, key=event_sort_key, reverse=True)[:limit]


def _build_runtime_question_payload(runtime_question):
    if not runtime_question:
        return None

    question_template = runtime_question.question_template
    question_content = {}
    if question_template and question_template.content_json:
        try:
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
        "time_limit_sec": getattr(question_template, "time_limit_sec", None) if question_template else None,
        "timer": getattr(question_template, "timer", None) if question_template else None,
        "duration_sec": getattr(question_template, "duration_sec", None) if question_template else None,
        "content": question_content,
        "media_type": question_content.get("media_type"),
        "media_ref": question_content.get("media_ref"),
        "is_media_question": bool(question_content.get("is_media_question")),
    }
    if payload["time_limit_sec"] is None:
        payload["time_limit_sec"] = question_content.get("time_limit_sec")
    if payload["timer"] is None:
        payload["timer"] = question_content.get("timer")
    if payload["duration_sec"] is None:
        payload["duration_sec"] = question_content.get("duration_sec")
    return payload


def _safe_json_dict(value):
    if isinstance(value, dict):
        return value
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except Exception:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _build_final_outcome_payload(
    db: Session,
    *,
    game,
    leaders,
    scenario_director_payload,
    active_host_round,
    current_question_payload,
):
    director = scenario_director_payload or {}
    current_round = director.get("current_round") if isinstance(director, dict) else None
    last_completed_round = director.get("last_completed_round") if isinstance(director, dict) else None
    active_round_code = str((active_host_round or {}).get("round_code") or "").strip().lower()
    current_round_code = str((current_round or {}).get("round_code") or "").strip().lower()
    last_completed_round_code = str((last_completed_round or {}).get("round_code") or "").strip().lower()

    is_final_context = any(
        code == "stage_final_show"
        for code in (active_round_code, current_round_code, last_completed_round_code)
    ) or bool((director or {}).get("scenario_finished"))

    if not is_final_context:
        return None

    by_influence = (leaders or {}).get("by_influence") or []
    by_gold = (leaders or {}).get("by_gold") or []
    winner = by_influence[0] if by_influence else (by_gold[0] if by_gold else None)
    winner_house_id = winner.get("id") if isinstance(winner, dict) else None
    winner_house_name = winner.get("name") if isinstance(winner, dict) else "Дом вечера"
    influence_value = winner.get("resources", {}).get("influence") if isinstance(winner, dict) else None
    gold_value = winner.get("resources", {}).get("gold") if isinstance(winner, dict) else None

    config = {}
    if isinstance(current_question_payload, dict):
        config = _safe_json_dict(current_question_payload.get("content"))

    if not config:
        final_round_template = (
            db.query(RoundTemplate)
            .filter(
                RoundTemplate.scenario_id == game.scenario_id,
                RoundTemplate.round_code == "stage_final_show",
            )
            .order_by(RoundTemplate.id.desc())
            .first()
        )
        if final_round_template:
            final_question_template = (
                db.query(RoundQuestionTemplate)
                .filter(RoundQuestionTemplate.round_template_id == final_round_template.id)
                .order_by(RoundQuestionTemplate.sequence_no.asc(), RoundQuestionTemplate.id.asc())
                .first()
            )
            if final_question_template:
                config = _safe_json_dict(final_question_template.content_json)

    jackpot_amount = config.get("jackpot_amount")
    jackpot_currency = str(config.get("jackpot_currency") or "₽").strip() or "₽"
    jackpot_amount_label = str(config.get("jackpot_amount_label") or "").strip()
    if not jackpot_amount_label:
        if isinstance(jackpot_amount, (int, float)) and jackpot_amount > 0:
            jackpot_amount_label = f"{int(jackpot_amount)} {jackpot_currency}"
        elif isinstance(jackpot_amount, str) and jackpot_amount.strip():
            jackpot_amount_label = jackpot_amount.strip()
        else:
            jackpot_amount_label = "сумма уточняется ведущим"

    outcome_type = str(config.get("jackpot_outcome") or "").strip().lower()
    carry_over = config.get("carry_over")
    if outcome_type not in {"won", "carry_over"}:
        if carry_over is True:
            outcome_type = "carry_over"
        elif carry_over is False:
            outcome_type = "won"
        else:
            outcome_type = "pending"

    configured = outcome_type in {"won", "carry_over"} or bool(config.get("jackpot_amount")) or bool(config.get("jackpot_amount_label"))

    if outcome_type == "won":
        outcome_title = "Счёт Дома покрыт"
        outcome_text = f"{winner_house_name} выигрывает джекпот игры."
        operator_text = "Подтверди со сцены, что счёт Дома покрыт."
    elif outcome_type == "carry_over":
        outcome_title = "Джекпот переходит дальше"
        outcome_text = "Дом вечера определён, но джекпот переносится на следующую игру."
        operator_text = "Подтверди со сцены перенос джекпота на следующую игру."
    else:
        outcome_title = "Исход джекпота объявляет ведущий"
        outcome_text = "Победитель вечера определён, но приз не зафиксирован в runtime."
        operator_text = "Озвучь вручную: счёт Дома покрыт или джекпот переносится."

    return {
        "winner_house_id": winner_house_id,
        "winner_house_name": winner_house_name,
        "winner_by": "influence" if by_influence else "gold",
        "winner_influence": influence_value,
        "winner_gold": gold_value,
        "jackpot_amount": jackpot_amount,
        "jackpot_currency": jackpot_currency,
        "jackpot_amount_label": jackpot_amount_label,
        "outcome_type": outcome_type,
        "configured": configured,
        "carry_over": outcome_type == "carry_over",
        "covers_bill": outcome_type == "won",
        "outcome_title": outcome_title,
        "outcome_text": outcome_text,
        "operator_text": operator_text,
    }


def _enrich_court_runtime_payload(db: Session, room_code: str, court_runtime_payload):
    if not isinstance(court_runtime_payload, dict):
        return None

    # GET state must be read-only; court sync must happen only from explicit POST actions.
    return deepcopy(build_court_runtime_view_logic(db, room_code, court_runtime_payload))


def _is_court_runtime_allowed(court_runtime_payload, scenario_director_payload):
    if not isinstance(court_runtime_payload, dict):
        return False

    if str(court_runtime_payload.get("source") or "").strip().lower() != "court_mvp":
        return True

    director_current_round = ((scenario_director_payload or {}).get("current_round") or {})
    current_round_code = str(director_current_round.get("round_code") or "").strip().lower()
    if current_round_code == "stage_court":
        return True

    active_system_stage_phase = ((scenario_director_payload or {}).get("active_system_stage_phase") or {})
    active_phase_type = str(active_system_stage_phase.get("phase_type") or "").strip().lower()
    active_phase_payload = active_system_stage_phase.get("payload") or {}
    active_phase_round_code = str(active_phase_payload.get("round_code") or "").strip().lower()
    return active_phase_type == "court" or active_phase_round_code == "stage_court"


def _suppress_stale_court_host_round(court_runtime_payload, active_host_round, current_question_payload, *, court_runtime_allowed=True):
    if not isinstance(court_runtime_payload, dict):
        if (
            not court_runtime_allowed
            and isinstance(active_host_round, dict)
            and str(active_host_round.get("round_code") or "").strip().lower() == "stage_court_battle"
        ):
            return None, None
        return active_host_round, current_question_payload

    if str(court_runtime_payload.get("source") or "").strip().lower() != "court_mvp":
        return active_host_round, current_question_payload

    if not court_runtime_allowed:
        if (
            isinstance(active_host_round, dict)
            and str(active_host_round.get("round_code") or "").strip().lower() == "stage_court_battle"
        ):
            return None, None
        return active_host_round, current_question_payload

    if not isinstance(active_host_round, dict):
        return active_host_round, current_question_payload

    if str(active_host_round.get("round_code") or "").strip().lower() != "stage_court_battle":
        return active_host_round, current_question_payload

    court_finished = bool(court_runtime_payload.get("is_finished")) or str(court_runtime_payload.get("status") or "").strip().lower() == "court_finished"
    court_has_pair = isinstance(court_runtime_payload.get("current_pair"), dict)
    court_has_question = isinstance(court_runtime_payload.get("current_question"), dict)

    if not court_has_question:
        current_question_payload = None

    if court_finished or (not court_has_pair and not court_has_question):
        return None, None

    return active_host_round, current_question_payload


def get_game_master_state_logic(
    db: Session,
    room_code: str,
    *,
    public_deal_status_fn,
    load_json_text_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    phases = (
        db.query(GamePhase)
        .filter(GamePhase.game_id == game.id)
        .order_by(GamePhase.id.asc())
        .all()
    )

    active_phases = [phase for phase in phases if phase.status == "active"]

    houses = (
        db.query(House)
        .filter(House.game_id == game.id)
        .order_by(House.id.asc())
        .all()
    )

    houses_payload = []
    for house in houses:
        houses_payload.append(
            {
                "id": house.id,
                "house_key": house.house_key,
                "name": house.name,
                "invite_code": house.invite_code,
                "is_ready": bool(getattr(house, "is_ready", False)),
                "resources": {
                    "gold": house.resource_gold,
                    "influence": house.resource_influence,
                    "stone": house.resource_stone,
                    "wood": house.resource_wood,
                    "iron": house.resource_iron,
                    "scroll": house.resource_scroll,
                    "key": house.resource_key,
                    "fire": house.resource_fire,
                },
            }
        )

    players = (
        db.query(Player)
        .filter(Player.game_id == game.id)
        .order_by(Player.id.asc())
        .all()
    )

    players_payload = []
    for player in players:
        players_payload.append(
            {
                "id": player.id,
                "nickname": player.nickname,
                "house_id": player.house_id,
                "house_name": player.house.name if player.house else None,
                "role_code": player.role.code if player.role else None,
                "role_name": player.role.name if player.role else None,
            }
        )

    host_rounds = (
        db.query(GameHostRound)
        .filter(GameHostRound.game_id == game.id)
        .order_by(GameHostRound.id.asc())
        .all()
    )

    runtime_questions = (
        db.query(GameHostRoundQuestion)
        .join(GameHostRound, GameHostRoundQuestion.host_round_id == GameHostRound.id)
        .filter(GameHostRound.game_id == game.id)
        .order_by(GameHostRoundQuestion.id.asc())
        .all()
    )

    host_rounds_payload = []
    for host_round in host_rounds:
        round_questions = [rq for rq in runtime_questions if rq.host_round_id == host_round.id]

        host_rounds_payload.append(
            {
                "id": host_round.id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "act_number": host_round.act_number,
                "round_kind": host_round.round_kind,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
                "runtime_questions_count": len(round_questions),
                "runtime_questions": [
                    {
                        "id": rq.id,
                        "sequence_no": rq.sequence_no,
                        "status": rq.status,
                        "answers_open": rq.answers_open,
                        "check_mode": rq.check_mode,
                    }
                    for rq in round_questions
                ],
            }
        )

    active_host_round = next(
        (
            round_item
            for round_item in reversed(host_rounds_payload)
            if round_item["status"] in {"active", "completed_waiting_host"}
        ),
        None,
    )

    current_runtime_question = None
    current_question_payload = None
    if active_host_round:
        current_runtime_question = next(
            (
                question
                for question in active_host_round.get("runtime_questions", [])
                if question.get("status") == "active"
            ),
            None,
        )
        current_runtime_question_entity = next(
            (
                question
                for question in runtime_questions
                if question.host_round_id == active_host_round["id"] and question.status == "active"
            ),
            None,
        )
        current_question_payload = _build_runtime_question_payload(current_runtime_question_entity)

    deals = (
        db.query(GameDeal)
        .filter(GameDeal.game_id == game.id)
        .order_by(GameDeal.id.asc())
        .all()
    )

    houses_by_id = {house.id: house for house in houses}

    child_map = {}
    for deal in deals:
        if deal.parent_deal_id:
            child_map.setdefault(deal.parent_deal_id, []).append(deal.id)

    deals_payload = []
    for deal in deals:
        public_status = public_deal_status_fn(deal.status)

        deals_payload.append(
            {
                "id": deal.id,
                "parent_deal_id": deal.parent_deal_id,
                "child_deal_ids": child_map.get(deal.id, []),
                "status": public_status,
                "from_house": {
                    "id": deal.from_house_id,
                    "house_key": houses_by_id.get(deal.from_house_id).house_key
                    if houses_by_id.get(deal.from_house_id)
                    else None,
                    "name": houses_by_id.get(deal.from_house_id).name
                    if houses_by_id.get(deal.from_house_id)
                    else None,
                },
                "to_house": {
                    "id": deal.to_house_id,
                    "house_key": houses_by_id.get(deal.to_house_id).house_key
                    if houses_by_id.get(deal.to_house_id)
                    else None,
                    "name": houses_by_id.get(deal.to_house_id).name
                    if houses_by_id.get(deal.to_house_id)
                    else None,
                },
                "offer": load_json_text_fn(deal.offer) if deal.offer else {},
                "note": deal.note,
                "created_at": deal.created_at.isoformat() if deal.created_at else None,
                "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
                "is_active": public_status in {"pending", "countered"},
            }
        )

    active_deals = [deal for deal in deals_payload if deal["status"] == "pending"]
    countered_deals = [deal for deal in deals_payload if deal["status"] == "countered"]
    recent_closed_deals = [
        deal
        for deal in reversed(deals_payload)
        if deal["status"] in {"accepted", "rejected", "cancelled", "completed"}
    ][:5]
    alliances_payload = [
        {
            "id": deal.id,
            "house_a": {
                "id": deal.from_house_id,
                "house_key": houses_by_id.get(deal.from_house_id).house_key
                if houses_by_id.get(deal.from_house_id)
                else None,
                "name": houses_by_id.get(deal.from_house_id).name
                if houses_by_id.get(deal.from_house_id)
                else None,
            },
            "house_b": {
                "id": deal.to_house_id,
                "house_key": houses_by_id.get(deal.to_house_id).house_key
                if houses_by_id.get(deal.to_house_id)
                else None,
                "name": houses_by_id.get(deal.to_house_id).name
                if houses_by_id.get(deal.to_house_id)
                else None,
            },
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "activated_at": offer_data.get("activated_at") if isinstance(offer_data, dict) else None,
            "alliance_bonus": (offer_data.get("alliance_bonus") if isinstance(offer_data, dict) else None) or {"influence": 1},
            "bonus_text": (
                offer_data.get("bonus_text")
                if isinstance(offer_data, dict) and offer_data.get("bonus_text")
                else "+1 влияние обоим Домам"
            ),
        }
        for deal in deals
        for offer_data in [load_json_text_fn(deal.offer) if deal.offer else {}]
        if deal.status == "alliance_active"
        and isinstance(offer_data, dict)
        and offer_data.get("type") == "alliance"
    ]
    broken_alliances_recent = [
        {
            "id": deal.id,
            "status": deal.status,
            "house_a": {
                "id": deal.from_house_id,
                "house_key": houses_by_id.get(deal.from_house_id).house_key
                if houses_by_id.get(deal.from_house_id)
                else None,
                "name": houses_by_id.get(deal.from_house_id).name
                if houses_by_id.get(deal.from_house_id)
                else None,
            },
            "house_b": {
                "id": deal.to_house_id,
                "house_key": houses_by_id.get(deal.to_house_id).house_key
                if houses_by_id.get(deal.to_house_id)
                else None,
                "name": houses_by_id.get(deal.to_house_id).name
                if houses_by_id.get(deal.to_house_id)
                else None,
            },
            "broken_by_house": {
                "id": offer_data.get("broken_by_house_id") if isinstance(offer_data, dict) else None,
                "house_key": houses_by_id.get(offer_data.get("broken_by_house_id")).house_key
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("broken_by_house_id"))
                else None,
                "name": houses_by_id.get(offer_data.get("broken_by_house_id")).name
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("broken_by_house_id"))
                else None,
            },
            "other_house": {
                "id": offer_data.get("other_house_id") if isinstance(offer_data, dict) else None,
                "house_key": houses_by_id.get(offer_data.get("other_house_id")).house_key
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("other_house_id"))
                else None,
                "name": houses_by_id.get(offer_data.get("other_house_id")).name
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("other_house_id"))
                else None,
            },
            "break_mode": offer_data.get("break_mode") if isinstance(offer_data, dict) else None,
            "break_text": offer_data.get("break_text") if isinstance(offer_data, dict) else None,
            "betrayal_effect": offer_data.get("betrayal_effect") if isinstance(offer_data, dict) else None,
            "broken_at": offer_data.get("broken_at") if isinstance(offer_data, dict) else None,
        }
        for deal in reversed(deals)
        for offer_data in [load_json_text_fn(deal.offer) if deal.offer else {}]
        if deal.status in {"alliance_broken", "alliance_betrayed"}
        and isinstance(offer_data, dict)
        and offer_data.get("type") == "alliance"
    ][:3]

    towers = (
        db.query(GameHouseTower)
        .filter(GameHouseTower.game_id == game.id)
        .order_by(GameHouseTower.house_id.asc())
        .all()
    )
    towers_by_house_id = {tower.house_id: tower for tower in towers}
    towers_quick = []
    for house in houses:
        tower = towers_by_house_id.get(house.id)
        tower_score = tower.tower_score if tower else 0
        towers_quick.append(
            {
                "house_id": house.id,
                "house_name": house.name,
                "tower_score": tower_score,
                "tower_class": _get_tower_class(tower_score),
            }
        )

    ready_houses = [house for house in houses_payload if house.get("is_ready")]
    not_ready_houses = [house for house in houses_payload if not house.get("is_ready")]

    duels = (
        db.query(GameDuel)
        .filter(GameDuel.game_id == game.id)
        .order_by(GameDuel.id.asc())
        .all()
    )
    duels_payload = []
    for duel in duels:
        duels_payload.append(
            {
                "id": duel.id,
                "challenger_house": {
                    "id": duel.challenger_house.id,
                    "name": duel.challenger_house.name,
                    "house_key": duel.challenger_house.house_key,
                } if duel.challenger_house else None,
                "target_house": {
                    "id": duel.target_house.id,
                    "name": duel.target_house.name,
                    "house_key": duel.target_house.house_key,
                } if duel.target_house else None,
                "status": duel.status,
                "duel_format": duel.duel_format,
                "live_bonus_label": duel.live_bonus_label,
                "live_bonus_host_text": duel.live_bonus_host_text,
                "live_bonus_tv_text": duel.live_bonus_tv_text,
                "duel_advantage_class": duel.duel_advantage_class,
                "tower_bonus_applied": bool(load_json_text_fn(duel.bonus_payload_json) and load_json_text_fn(duel.bonus_payload_json).get("tower_bonus_applied")),
                "winner_house": {
                    "id": duel.winner_house.id,
                    "name": duel.winner_house.name,
                    "house_key": duel.winner_house.house_key,
                } if duel.winner_house else None,
                "created_at": duel.created_at.isoformat() if duel.created_at else None,
                "resolved_at": duel.resolved_at.isoformat() if duel.resolved_at else None,
            }
        )

    challenged_duels = [duel for duel in duels_payload if duel["status"] == "challenged"]
    accepted_duels = [duel for duel in duels_payload if duel["status"] == "accepted"]
    recent_duels = [duel for duel in reversed(duels_payload) if duel["status"] in {"refused", "resolved", "canceled"}][:5]
    duels_block = {
        "active_or_pending": [duel for duel in duels_payload if duel["status"] in {"challenged", "accepted"}],
        "challenged": challenged_duels,
        "accepted": accepted_duels,
        "recent": recent_duels,
    }

    expeditions = (
        db.query(GameExpedition)
        .filter(GameExpedition.game_id == game.id)
        .order_by(GameExpedition.id.asc())
        .all()
    )
    expeditions_payload = []
    for expedition in expeditions:
        role_codes = []
        member_ids = []
        for member in expedition.members or []:
            member_ids.append(member.player_id)
            if member.player and member.player.role and member.player.role.code:
                role_codes.append(member.player.role.code)

        expeditions_payload.append(
            {
                "id": expedition.id,
                "house": {
                    "id": expedition.house.id,
                    "name": expedition.house.name,
                    "house_key": expedition.house.house_key,
                } if expedition.house else None,
                "status": expedition.status,
                "leader_player_id": expedition.leader_player_id,
                "approved_by_player_id": expedition.approved_by_player_id,
                "member_ids": member_ids,
                "members_count": len(member_ids),
                "role_codes": role_codes,
                "target_location_code": expedition.target_location_code,
                "approved_at": expedition.approved_at.isoformat() if expedition.approved_at else None,
            }
        )

    expeditions_block = {
        "planned": [expedition for expedition in expeditions_payload if expedition["status"] == "planned"],
        "approved": [expedition for expedition in expeditions_payload if expedition["status"] == "approved"],
        "recently_resolved": [expedition for expedition in reversed(expeditions_payload) if expedition["status"] == "resolved"][:5],
    }

    def sort_houses_by_resource(resource_key: str):
        return sorted(
            houses_payload,
            key=lambda x: x["resources"].get(resource_key, 0),
            reverse=True,
        )

    leaders = {
        "by_gold": sort_houses_by_resource("gold")[:3],
        "by_influence": sort_houses_by_resource("influence")[:3],
        "by_scroll": sort_houses_by_resource("scroll")[:3],
    }

    total_houses_base = 10

    summary = {
        "houses_count": len(houses_payload),
        "houses_active": len(houses_payload),
        "houses_total": total_houses_base,
        "houses_ready_count": len(ready_houses),
        "houses_not_ready_count": len(not_ready_houses),
        "players_count": len(players_payload),
        "phases_count": len(phases),
        "active_phases_count": len(active_phases),
        "host_rounds_count": len(host_rounds_payload),
        "deals_count": len(deals_payload),
        "pending_deals_count": len(active_deals),
        "countered_deals_count": len(countered_deals),
        "duels_count": len(duels_payload),
        "active_duels_count": len(duels_block["active_or_pending"]),
        "planned_expeditions_count": len(expeditions_block["planned"]),
        "approved_expeditions_count": len(expeditions_block["approved"]),
    }

    event_feed = []
    for duel in reversed(duels_payload):
        if duel["status"] == "challenged":
            event_feed.append(
                {
                    "type": "duel",
                    "title": "Вызов на дуэль",
                    "text": f'{duel["challenger_house"]["name"]} вызвал {duel["target_house"]["name"]} на дуэль',
                    "created_at": duel.get("created_at"),
                    "severity": "warn",
                }
            )
        elif duel["status"] == "refused":
            event_feed.append(
                {
                    "type": "duel",
                    "title": "Отказ от дуэли",
                    "text": f'{duel["target_house"]["name"]} отказался от дуэли',
                    "created_at": duel.get("resolved_at") or duel.get("created_at"),
                    "severity": "warn",
                }
            )
        elif duel["status"] == "resolved" and duel.get("winner_house"):
            event_feed.append(
                {
                    "type": "duel",
                    "title": "Дуэль разрешена",
                    "text": f'Победа в дуэли: {duel["winner_house"]["name"]}',
                    "created_at": duel.get("resolved_at") or duel.get("created_at"),
                    "severity": "ok",
                }
            )
        if duel.get("live_bonus_label"):
            event_feed.append(
                {
                    "type": "duel_bonus",
                    "title": "Преимущество Башни",
                    "text": duel.get("live_bonus_tv_text") or duel.get("live_bonus_host_text"),
                    "created_at": duel.get("created_at"),
                    "severity": "info",
                }
            )

    for expedition in reversed(expeditions_payload):
        if expedition["status"] == "approved":
            event_feed.append(
                {
                    "type": "expedition",
                    "title": "Экспедиция утверждена",
                    "text": f'Экспедиция {expedition["house"]["name"]} утверждена',
                    "created_at": expedition.get("approved_at"),
                    "severity": "ok",
                }
            )
        elif expedition["status"] == "planned":
            event_feed.append(
                {
                    "type": "expedition",
                    "title": "Экспедиция ждёт решения",
                    "text": f'Экспедиция {expedition["house"]["name"]} ждёт утверждения',
                    "created_at": expedition.get("approved_at"),
                    "severity": "info",
                }
            )
        elif expedition["status"] == "resolved":
            event_feed.append(
                {
                    "type": "expedition",
                    "title": "Экспедиция завершена",
                    "text": f'Экспедиция {expedition["house"]["name"]} завершена',
                    "created_at": expedition.get("approved_at"),
                    "severity": "ok",
                }
            )

    for deal in reversed(deals_payload):
        if deal["status"] in {"pending", "countered"}:
            event_feed.append(
                {
                    "type": "deal",
                    "title": "Дипломатическая сделка",
                    "text": f'{deal["from_house"]["name"]} → {deal["to_house"]["name"]}',
                    "created_at": deal.get("created_at"),
                    "severity": "info",
                }
            )

    if active_host_round and current_runtime_question:
        event_feed.append(
            {
                "type": "host_round",
                "title": "Активный вопрос",
                "text": f'Идёт вопрос #{current_runtime_question["sequence_no"]} в раунде {active_host_round.get("title") or active_host_round.get("round_code") or "—"}',
                "created_at": None,
                "severity": "high",
            }
        )
    elif active_host_round and active_host_round.get("status") == "completed_waiting_host":
        event_feed.append(
            {
                "type": "host_round",
                "title": "Раунд ждёт подтверждения",
                "text": "Подтверди завершение текущего раунда",
                "created_at": None,
                "severity": "warn",
            }
        )

    event_feed = event_feed[:15]

    scenario_director_payload = None
    scenario_director_state = get_scenario_director_logic(db, room_code=room_code)
    if isinstance(scenario_director_state, dict) and scenario_director_state.get("ok"):
        scenario_director_payload = {
            "current_round": scenario_director_state.get("current_round"),
            "current_round_status": scenario_director_state.get("current_round_status"),
            "current_round_completed": scenario_director_state.get("current_round_completed"),
            "next_round": scenario_director_state.get("next_round"),
            "last_completed_round": scenario_director_state.get("last_completed_round"),
            "has_active_host_round": scenario_director_state.get("has_active_host_round"),
            "active_host_round": scenario_director_state.get("active_host_round"),
            "active_system_stage_phase": scenario_director_state.get("active_system_stage_phase"),
            "can_start_next": scenario_director_state.get("can_start_next"),
            "can_advance": scenario_director_state.get("can_advance"),
            "can_advance_and_start": scenario_director_state.get("can_advance_and_start"),
            "scenario_finished": scenario_director_state.get("scenario_finished"),
            "progress": scenario_director_state.get("progress"),
        }

    court_runtime_result = get_court_runtime_logic(db, room_code)
    court_runtime_payload = (
        court_runtime_result.get("court")
        if isinstance(court_runtime_result, dict) and court_runtime_result.get("ok")
        else None
    )
    court_runtime_payload = _enrich_court_runtime_payload(db, room_code, court_runtime_payload)
    court_runtime_allowed = _is_court_runtime_allowed(court_runtime_payload, scenario_director_payload)
    if not court_runtime_allowed:
        court_runtime_payload = None
        active_phases = [phase for phase in active_phases if phase.phase_type != "court"]
        summary["active_phases_count"] = len(active_phases)
    active_host_round, current_question_payload = _suppress_stale_court_host_round(
        court_runtime_payload,
        active_host_round,
        current_question_payload,
        court_runtime_allowed=court_runtime_allowed,
    )
    master_prompt = _build_master_prompt(
        active_host_round=active_host_round,
        current_question=current_runtime_question,
        duels_block=duels_block,
        expeditions_block=expeditions_block,
        active_phases=active_phases,
        court_runtime=court_runtime_payload,
    )
    stage_briefing = _build_stage_briefing_payload(
        scenario_director_payload=scenario_director_payload,
        active_host_round=active_host_round,
        active_phases=active_phases,
    )
    final_outcome_payload = _build_final_outcome_payload(
        db,
        game=game,
        leaders=leaders,
        scenario_director_payload=scenario_director_payload,
        active_host_round=active_host_round,
        current_question_payload=current_question_payload,
    )
    last_whisper_payload = _build_last_whisper_payload(active_phases)
    treasurer_shop_events = _build_treasurer_shop_events(db, game_id=game.id)
    recent_events = _build_recent_events_payload(
        last_whisper_payload=last_whisper_payload,
        broken_alliances_recent=broken_alliances_recent,
        duels_block=duels_block,
        recent_closed_deals=recent_closed_deals,
        treasurer_shop_events=treasurer_shop_events,
        event_feed=event_feed,
    )

    readiness_payload = {
        "ready_count": len(ready_houses),
        "not_ready_count": len(not_ready_houses),
        "total_count": len(houses_payload),
        "ready_houses": [
            {
                "id": house.get("id"),
                "name": house.get("name"),
                "house_key": house.get("house_key"),
            }
            for house in ready_houses
        ],
        "not_ready_houses": [
            {
                "id": house.get("id"),
                "name": house.get("name"),
                "house_key": house.get("house_key"),
            }
            for house in not_ready_houses
        ],
    }

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "summary": summary,
        "active_phases": [
            {
                "id": phase.id,
                "phase_type": phase.phase_type,
                "status": phase.status,
                "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
                "closed_at": phase.closed_at.isoformat() if phase.closed_at else None,
            }
            for phase in active_phases
        ],
        "all_phases": [
            {
                "id": phase.id,
                "phase_type": phase.phase_type,
                "status": phase.status,
                "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
                "closed_at": phase.closed_at.isoformat() if phase.closed_at else None,
            }
            for phase in phases
        ],
        "active_host_round": active_host_round,
        "current_question": current_question_payload,
        "host_rounds": host_rounds_payload,
        "houses": houses_payload,
        "players": players_payload,
        "deals": deals_payload,
        "alliances": alliances_payload,
        "broken_alliances_recent": broken_alliances_recent,
        "leaders": leaders,
        "readiness": readiness_payload,
        "duels": duels_block,
        "expeditions": expeditions_block,
        "last_whisper": last_whisper_payload,
        "treasurer_shop_events": treasurer_shop_events,
        "towers_quick": towers_quick,
        "court_runtime": court_runtime_payload,
        "final_outcome": final_outcome_payload,
        "scenario_director": scenario_director_payload,
        "master_prompt": master_prompt,
        "stage_briefing": stage_briefing,
        "event_feed": event_feed,
        "recent_events": recent_events,
    }


def get_game_master_tv_state_logic(
    db: Session,
    room_code: str,
    *,
    public_deal_status_fn,
    load_json_text_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    phases = (
        db.query(GamePhase)
        .filter(GamePhase.game_id == game.id)
        .order_by(GamePhase.id.asc())
        .all()
    )

    active_phases = [phase for phase in phases if phase.status == "active"]

    houses = (
        db.query(House)
        .filter(House.game_id == game.id)
        .order_by(House.id.asc())
        .all()
    )

    houses_payload = []
    for house in houses:
        houses_payload.append(
            {
                "id": house.id,
                "house_key": house.house_key,
                "name": house.name,
                "invite_code": house.invite_code,
                "is_ready": bool(getattr(house, "is_ready", False)),
                "resources": {
                    "gold": house.resource_gold,
                    "influence": house.resource_influence,
                    "stone": house.resource_stone,
                    "wood": house.resource_wood,
                    "iron": house.resource_iron,
                    "scroll": house.resource_scroll,
                    "key": house.resource_key,
                    "fire": house.resource_fire,
                },
            }
        )

    ready_houses = [house for house in houses_payload if house.get("is_ready")]
    not_ready_houses = [house for house in houses_payload if not house.get("is_ready")]

    houses_by_id = {house.id: house for house in houses}

    host_rounds = (
        db.query(GameHostRound)
        .filter(GameHostRound.game_id == game.id)
        .order_by(GameHostRound.id.asc())
        .all()
    )

    runtime_questions = (
        db.query(GameHostRoundQuestion)
        .join(GameHostRound, GameHostRoundQuestion.host_round_id == GameHostRound.id)
        .filter(GameHostRound.game_id == game.id)
        .order_by(GameHostRoundQuestion.id.asc())
        .all()
    )

    host_rounds_payload = []
    for host_round in host_rounds:
        round_questions = [rq for rq in runtime_questions if rq.host_round_id == host_round.id]

        host_rounds_payload.append(
            {
                "id": host_round.id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "act_number": host_round.act_number,
                "round_kind": host_round.round_kind,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
                "runtime_questions_count": len(round_questions),
                "runtime_questions": [
                    {
                        "id": rq.id,
                        "sequence_no": rq.sequence_no,
                        "status": rq.status,
                        "answers_open": rq.answers_open,
                        "check_mode": rq.check_mode,
                    }
                    for rq in round_questions
                ],
            }
        )

    active_host_round = next(
        (
            round_item
            for round_item in reversed(host_rounds_payload)
            if round_item["status"] in {"active", "completed_waiting_host"}
        ),
        None,
    )

    current_question_payload = None
    if active_host_round:
        current_runtime_question = next(
            (
                question
                for question in runtime_questions
                if question.host_round_id == active_host_round["id"] and question.status == "active"
            ),
            None,
        )
        current_question_payload = _build_runtime_question_payload(current_runtime_question)

    deals = (
        db.query(GameDeal)
        .filter(GameDeal.game_id == game.id)
        .order_by(GameDeal.id.asc())
        .all()
    )

    child_map = {}
    for deal in deals:
        if deal.parent_deal_id:
            child_map.setdefault(deal.parent_deal_id, []).append(deal.id)

    def format_offer_text(offer: dict):
        if not offer:
            return ""

        text_value = offer.get("text") if isinstance(offer, dict) else None
        if isinstance(text_value, str) and text_value.strip():
            return text_value.strip()

        parts = []
        names = {
            "gold": "золота",
            "wood": "дерева",
            "stone": "камня",
            "iron": "железа",
            "scroll": "свитков",
            "key": "ключей",
            "fire": "огня",
            "influence": "влияния",
        }

        for key, value in offer.items():
            if isinstance(value, int) and value > 0:
                parts.append(f"{value} {names.get(key, key)}")

        return ", ".join(parts)

    deals_payload = []
    for deal in deals:
        offer_data = load_json_text_fn(deal.offer) if deal.offer else {}
        public_status = public_deal_status_fn(deal.status)

        deals_payload.append(
            {
                "id": deal.id,
                "parent_deal_id": deal.parent_deal_id,
                "child_deal_ids": child_map.get(deal.id, []),
                "status": public_status,
                "from_house": {
                    "id": deal.from_house_id,
                    "house_key": houses_by_id.get(deal.from_house_id).house_key
                    if houses_by_id.get(deal.from_house_id)
                    else None,
                    "name": houses_by_id.get(deal.from_house_id).name
                    if houses_by_id.get(deal.from_house_id)
                    else None,
                },
                "to_house": {
                    "id": deal.to_house_id,
                    "house_key": houses_by_id.get(deal.to_house_id).house_key
                    if houses_by_id.get(deal.to_house_id)
                    else None,
                    "name": houses_by_id.get(deal.to_house_id).name
                    if houses_by_id.get(deal.to_house_id)
                    else None,
                },
                "offer": offer_data,
                "offer_text": format_offer_text(offer_data),
                "note": deal.note,
                "created_at": deal.created_at.isoformat() if deal.created_at else None,
                "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
                "is_active": public_status in {"pending", "countered"},
            }
        )

    pending_deals = [deal for deal in deals_payload if deal["status"] == "pending"]
    countered_deals = [deal for deal in deals_payload if deal["status"] == "countered"]
    alliances_payload = [
        {
            "id": deal.id,
            "house_a": {
                "id": deal.from_house_id,
                "house_key": houses_by_id.get(deal.from_house_id).house_key
                if houses_by_id.get(deal.from_house_id)
                else None,
                "name": houses_by_id.get(deal.from_house_id).name
                if houses_by_id.get(deal.from_house_id)
                else None,
            },
            "house_b": {
                "id": deal.to_house_id,
                "house_key": houses_by_id.get(deal.to_house_id).house_key
                if houses_by_id.get(deal.to_house_id)
                else None,
                "name": houses_by_id.get(deal.to_house_id).name
                if houses_by_id.get(deal.to_house_id)
                else None,
            },
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "activated_at": offer_data.get("activated_at") if isinstance(offer_data, dict) else None,
            "alliance_bonus": (offer_data.get("alliance_bonus") if isinstance(offer_data, dict) else None) or {"influence": 1},
            "bonus_text": (
                offer_data.get("bonus_text")
                if isinstance(offer_data, dict) and offer_data.get("bonus_text")
                else "+1 влияние обоим Домам"
            ),
        }
        for deal in deals
        for offer_data in [load_json_text_fn(deal.offer) if deal.offer else {}]
        if deal.status == "alliance_active"
        and isinstance(offer_data, dict)
        and offer_data.get("type") == "alliance"
    ]
    broken_alliances_recent = [
        {
            "id": deal.id,
            "status": deal.status,
            "house_a": {
                "id": deal.from_house_id,
                "house_key": houses_by_id.get(deal.from_house_id).house_key
                if houses_by_id.get(deal.from_house_id)
                else None,
                "name": houses_by_id.get(deal.from_house_id).name
                if houses_by_id.get(deal.from_house_id)
                else None,
            },
            "house_b": {
                "id": deal.to_house_id,
                "house_key": houses_by_id.get(deal.to_house_id).house_key
                if houses_by_id.get(deal.to_house_id)
                else None,
                "name": houses_by_id.get(deal.to_house_id).name
                if houses_by_id.get(deal.to_house_id)
                else None,
            },
            "broken_by_house": {
                "id": offer_data.get("broken_by_house_id") if isinstance(offer_data, dict) else None,
                "house_key": houses_by_id.get(offer_data.get("broken_by_house_id")).house_key
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("broken_by_house_id"))
                else None,
                "name": houses_by_id.get(offer_data.get("broken_by_house_id")).name
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("broken_by_house_id"))
                else None,
            },
            "other_house": {
                "id": offer_data.get("other_house_id") if isinstance(offer_data, dict) else None,
                "house_key": houses_by_id.get(offer_data.get("other_house_id")).house_key
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("other_house_id"))
                else None,
                "name": houses_by_id.get(offer_data.get("other_house_id")).name
                if isinstance(offer_data, dict) and houses_by_id.get(offer_data.get("other_house_id"))
                else None,
            },
            "break_mode": offer_data.get("break_mode") if isinstance(offer_data, dict) else None,
            "break_text": offer_data.get("break_text") if isinstance(offer_data, dict) else None,
            "betrayal_effect": offer_data.get("betrayal_effect") if isinstance(offer_data, dict) else None,
            "broken_at": offer_data.get("broken_at") if isinstance(offer_data, dict) else None,
        }
        for deal in reversed(deals)
        for offer_data in [load_json_text_fn(deal.offer) if deal.offer else {}]
        if deal.status in {"alliance_broken", "alliance_betrayed"}
        and isinstance(offer_data, dict)
        and offer_data.get("type") == "alliance"
    ][:3]

    recent_closed_deals = [
        deal for deal in reversed(deals_payload) if deal["status"] in {"accepted", "rejected", "cancelled"}
    ][:5]

    def sort_houses_by_resource(resource_key: str):
        return sorted(
            houses_payload,
            key=lambda x: x["resources"].get(resource_key, 0),
            reverse=True,
        )

    leaders = {
        "by_gold": sort_houses_by_resource("gold")[:3],
        "by_influence": sort_houses_by_resource("influence")[:3],
        "by_scroll": sort_houses_by_resource("scroll")[:3],
    }

    duels_payload = []
    try:
        duels = (
            db.query(GameDuel)
            .filter(GameDuel.game_id == game.id)
            .order_by(GameDuel.id.asc())
            .all()
        )

        for duel in duels:
            duels_payload.append(
                {
                    "id": duel.id,
                    "status": duel.status,
                    "challenger_house_id": duel.challenger_house.id if duel.challenger_house else None,
                    "challenger_house_name": duel.challenger_house.name if duel.challenger_house else None,
                    "target_house_id": duel.target_house.id if duel.target_house else None,
                    "target_house_name": duel.target_house.name if duel.target_house else None,
                    "stake_gold": getattr(duel, "stake_gold", None),
                    "duel_format": getattr(duel, "duel_format", None),
                    "live_bonus_label": getattr(duel, "live_bonus_label", None),
                    "created_at": duel.created_at.isoformat() if duel.created_at else None,
                }
            )
    except Exception:
        duels_payload = []

    duels_block = {
        "active_or_pending": [duel for duel in duels_payload if duel["status"] in {"challenged", "accepted"}][:5],
        "challenged": [duel for duel in duels_payload if duel["status"] == "challenged"][:5],
        "accepted": [duel for duel in duels_payload if duel["status"] == "accepted"][:5],
        "recent": [duel for duel in reversed(duels_payload) if duel["status"] in {"refused", "resolved", "canceled"}][:5],
    }

    expeditions_payload = []
    try:
        expedition_plan_visits = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == game.id,
                GameMapVisit.outcome_type == "expedition_plan",
            )
            .order_by(GameMapVisit.id.asc())
            .all()
        )
        plan_meta_by_expedition_id = {}
        for visit in expedition_plan_visits:
            try:
                meta = json.loads(visit.meta_json) if visit.meta_json else {}
            except Exception:
                meta = {}

            expedition_id = meta.get("expedition_id")
            if not expedition_id:
                continue

            role_codes = meta.get("role_codes")
            if not isinstance(role_codes, list):
                role_codes = []

            members_count = meta.get("members_count")
            if not isinstance(members_count, int):
                members_count = len(role_codes) if role_codes else 0

            plan_meta_by_expedition_id[expedition_id] = {
                "members_count": members_count,
                "role_codes": role_codes,
            }

        expedition_vote_visits = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == game.id,
                GameMapVisit.outcome_type == "expedition_vote",
            )
            .order_by(GameMapVisit.id.asc())
            .all()
        )
        votes_summary_by_expedition_id = {}
        for visit in expedition_vote_visits:
            meta = {}
            try:
                meta = json.loads(visit.meta_json) if visit.meta_json else {}
            except Exception:
                meta = {}

            expedition_id = meta.get("expedition_id")
            if not expedition_id:
                continue

            bucket = votes_summary_by_expedition_id.setdefault(
                expedition_id,
                {"choices_count": 0, "locations": set()},
            )
            bucket["choices_count"] += 1
            if visit.location_code:
                bucket["locations"].add(visit.location_code)

        expedition_result_visits = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == game.id,
                GameMapVisit.outcome_type.in_(["map_success", "map_fail"]),
            )
            .order_by(GameMapVisit.id.asc())
            .all()
        )
        result_meta_by_expedition_id = {}
        for visit in expedition_result_visits:
            try:
                meta = json.loads(visit.meta_json) if visit.meta_json else {}
            except Exception:
                meta = {}

            expedition_id = meta.get("expedition_id")
            if not expedition_id:
                continue

            result_meta_by_expedition_id[expedition_id] = {
                "location_name": meta.get("location_name"),
                "reward": meta.get("reward") or {},
                "penalty": meta.get("penalty") or {},
                "outcome_text": visit.outcome_text,
                "success": meta.get("success"),
                "role_bonus": meta.get("role_bonus"),
                "vote_counts": meta.get("vote_counts_display") or [],
                "resolved_at": visit.created_at.isoformat() if getattr(visit, "created_at", None) else None,
            }

        expeditions = (
            db.query(GameExpedition)
            .filter(GameExpedition.game_id == game.id)
            .order_by(GameExpedition.id.asc())
            .all()
        )

        for expedition in expeditions:
            vote_summary = votes_summary_by_expedition_id.get(
                expedition.id,
                {"choices_count": 0, "locations": set()},
            )
            plan_meta = plan_meta_by_expedition_id.get(
                expedition.id,
                {"members_count": 0, "role_codes": []},
            )
            result_meta = result_meta_by_expedition_id.get(expedition.id, {})
            expeditions_payload.append(
                {
                    "id": expedition.id,
                    "status": expedition.status,
                    "house_id": expedition.house.id if expedition.house else None,
                    "house_name": expedition.house.name if expedition.house else None,
                    "target_location_code": getattr(expedition, "target_location_code", None),
                    "target_location_name": result_meta.get("location_name"),
                    "location_code": getattr(expedition, "target_location_code", None),
                    "location_name": result_meta.get("location_name"),
                    "reward": result_meta.get("reward") or {},
                    "penalty": result_meta.get("penalty") or {},
                    "outcome_text": result_meta.get("outcome_text"),
                    "result_text": result_meta.get("outcome_text"),
                    "success": result_meta.get("success"),
                    "role_bonus": result_meta.get("role_bonus"),
                    "vote_counts": result_meta.get("vote_counts") or [],
                    "created_at": expedition.created_at.isoformat() if getattr(expedition, "created_at", None) else None,
                    "approved_at": expedition.approved_at.isoformat() if expedition.approved_at else None,
                    "resolved_at": result_meta.get("resolved_at"),
                    "members_count": plan_meta["members_count"],
                    "role_codes": plan_meta["role_codes"],
                    "choices_count": vote_summary["choices_count"],
                    "unique_locations_count": len(vote_summary["locations"]),
                }
            )
    except Exception:
        expeditions_payload = []

    expeditions_block = {
        "planned": [expedition for expedition in expeditions_payload if expedition["status"] == "planned"][:5],
        "approved": [expedition for expedition in expeditions_payload if expedition["status"] == "approved"][:5],
        "recently_resolved": [expedition for expedition in reversed(expeditions_payload) if expedition["status"] == "resolved"][:5],
    }

    try:
        recent_visits = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == game.id,
                GameMapVisit.outcome_type.in_(["map_success", "map_fail"]),
            )
            .order_by(GameMapVisit.id.desc())
            .all()
        )

        map_events_payload = []
        for visit in recent_visits[:5]:
            if not visit.outcome_text:
                continue

            try:
                meta = json.loads(visit.meta_json) if visit.meta_json else {}
            except Exception:
                meta = {}

            map_events_payload.append(
                {
                    "house_name": visit.house.name if visit.house else None,
                    "text": visit.outcome_text,
                    "outcome_text": visit.outcome_text,
                    "location_name": meta.get("location_name"),
                    "location_code": meta.get("location_code") or visit.location_code,
                    "result_text": visit.outcome_text,
                    "success": meta.get("success"),
                    "role_bonus": meta.get("role_bonus"),
                    "members_count": meta.get("members_count"),
                    "role_codes": meta.get("role_codes") or [],
                    "preferred_roles": meta.get("preferred_roles") or [],
                    "reward": meta.get("reward") or {},
                    "penalty": meta.get("penalty") or {},
                    "vote_counts": meta.get("vote_counts_display") or [],
                    "created_at": visit.created_at.isoformat() if getattr(visit, "created_at", None) else None,
                }
            )
    except Exception:
        map_events_payload = []

    tv_summary = {
        "active_phase_types": [phase.phase_type for phase in active_phases],
        "pending_deals_count": len(pending_deals),
        "countered_deals_count": len(countered_deals),
        "houses_count": len(houses_payload),
        "houses_ready_count": len(ready_houses),
        "houses_not_ready_count": len(not_ready_houses),
    }

    readiness_payload = {
        "ready_count": len(ready_houses),
        "not_ready_count": len(not_ready_houses),
        "total_count": len(houses_payload),
        "ready_houses": [
            {
                "id": house.get("id"),
                "name": house.get("name"),
                "house_key": house.get("house_key"),
            }
            for house in ready_houses
        ],
        "not_ready_houses": [
            {
                "id": house.get("id"),
                "name": house.get("name"),
                "house_key": house.get("house_key"),
            }
            for house in not_ready_houses
        ],
    }

    scenario_director_payload = None
    scenario_director_state = get_scenario_director_logic(db, room_code=room_code)
    if isinstance(scenario_director_state, dict) and scenario_director_state.get("ok"):
        scenario_director_payload = {
            "current_round": scenario_director_state.get("current_round"),
            "current_round_status": scenario_director_state.get("current_round_status"),
            "current_round_completed": scenario_director_state.get("current_round_completed"),
            "next_round": scenario_director_state.get("next_round"),
            "last_completed_round": scenario_director_state.get("last_completed_round"),
            "has_active_host_round": scenario_director_state.get("has_active_host_round"),
            "active_host_round": scenario_director_state.get("active_host_round"),
            "active_system_stage_phase": scenario_director_state.get("active_system_stage_phase"),
            "can_start_next": scenario_director_state.get("can_start_next"),
            "can_advance": scenario_director_state.get("can_advance"),
            "can_advance_and_start": scenario_director_state.get("can_advance_and_start"),
            "scenario_finished": scenario_director_state.get("scenario_finished"),
            "progress": scenario_director_state.get("progress"),
        }

    court_runtime_result = get_court_runtime_logic(db, room_code)
    court_runtime_payload = (
        court_runtime_result.get("court")
        if isinstance(court_runtime_result, dict) and court_runtime_result.get("ok")
        else None
    )
    court_runtime_payload = _enrich_court_runtime_payload(db, room_code, court_runtime_payload)
    court_runtime_allowed = _is_court_runtime_allowed(court_runtime_payload, scenario_director_payload)
    if not court_runtime_allowed:
        court_runtime_payload = None
        active_phases = [phase for phase in active_phases if phase.phase_type != "court"]
        tv_summary["active_phase_types"] = [phase.phase_type for phase in active_phases]
    active_host_round, current_question_payload = _suppress_stale_court_host_round(
        court_runtime_payload,
        active_host_round,
        current_question_payload,
        court_runtime_allowed=court_runtime_allowed,
    )
    stage_briefing = _build_stage_briefing_payload(
        scenario_director_payload=scenario_director_payload,
        active_host_round=active_host_round,
        active_phases=active_phases,
    )
    final_outcome_payload = _build_final_outcome_payload(
        db,
        game=game,
        leaders=leaders,
        scenario_director_payload=scenario_director_payload,
        active_host_round=active_host_round,
        current_question_payload=current_question_payload,
    )
    last_whisper_payload = _build_last_whisper_payload(active_phases)
    treasurer_shop_events = _build_treasurer_shop_events(db, game_id=game.id)
    recent_events = _build_recent_events_payload(
        last_whisper_payload=last_whisper_payload,
        broken_alliances_recent=broken_alliances_recent,
        duels_block=duels_block,
        recent_closed_deals=recent_closed_deals,
        treasurer_shop_events=treasurer_shop_events,
    )

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "tv_summary": tv_summary,
        "active_phases": [
            {
                "id": phase.id,
                "phase_type": phase.phase_type,
                "status": phase.status,
                "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
            }
            for phase in active_phases
        ],
        "active_host_round": active_host_round,
        "current_question": current_question_payload,
        "houses": houses_payload,
        "deals": {
            "pending": pending_deals,
            "countered": countered_deals,
            "recent_closed": recent_closed_deals,
        },
        "alliances": alliances_payload,
        "broken_alliances_recent": broken_alliances_recent,
        "readiness": readiness_payload,
        "duels": duels_block,
        "expeditions": expeditions_block,
        "map_events": {
            "public_recent": map_events_payload,
        },
        "leaders": leaders,
        "last_whisper": last_whisper_payload,
        "treasurer_shop_events": treasurer_shop_events,
        "recent_events": recent_events,
        "court_runtime": court_runtime_payload,
        "final_outcome": final_outcome_payload,
        "scenario_director": scenario_director_payload,
        "stage_briefing": stage_briefing,
    }


def host_round_debug_logic(db: Session, host_round_id: int):
    host_round = (
        db.query(GameHostRound)
        .filter(GameHostRound.id == host_round_id)
        .first()
    )

    if not host_round:
        return {
            "ok": False,
            "message": "host_round not found",
            "host_round_id": host_round_id,
        }

    current_question = (
        db.query(GameHostRoundQuestion)
        .filter(
            GameHostRoundQuestion.host_round_id == host_round.id,
            GameHostRoundQuestion.status == "active",
        )
        .first()
    )

    assignments = []
    stats = {
        "total": 0,
        "answered": 0,
        "correct": 0,
        "wrong": 0,
        "pending": 0,
        "expired": 0,
    }

    question_payload = None

    if current_question:
        question_template = current_question.question_template
        question_content = {}
        if question_template and question_template.content_json:
            try:
                question_content = json.loads(question_template.content_json)
            except Exception:
                question_content = {}
        if not isinstance(question_content, dict):
            question_content = {}

        question_payload = {
            "id": current_question.id,
            "sequence_no": current_question.sequence_no,
            "status": current_question.status,
            "answers_open": current_question.answers_open,
            "title": question_template.title if question_template else f"Вопрос #{current_question.sequence_no}",
            "prompt": question_template.prompt if question_template else None,
            "question_code": question_template.question_code if question_template else None,
            "ui_template": question_template.ui_template if question_template else None,
            "role_code": question_template.role_code if question_template else None,
            "time_limit_sec": getattr(question_template, "time_limit_sec", None) if question_template else None,
            "timer": getattr(question_template, "timer", None) if question_template else None,
            "duration_sec": getattr(question_template, "duration_sec", None) if question_template else None,
            "content": question_content,
            "media_type": question_content.get("media_type"),
            "media_ref": question_content.get("media_ref"),
            "is_media_question": bool(question_content.get("is_media_question")),
        }

        if question_payload["time_limit_sec"] is None:
            question_payload["time_limit_sec"] = question_content.get("time_limit_sec")
        if question_payload["timer"] is None:
            question_payload["timer"] = question_content.get("timer")
        if question_payload["duration_sec"] is None:
            question_payload["duration_sec"] = question_content.get("duration_sec")

        raw_assignments = (
            db.query(GameAssignment)
            .filter(GameAssignment.host_round_question_id == current_question.id)
            .order_by(GameAssignment.id.asc())
            .all()
        )

        stats["total"] = len(raw_assignments)

        for assignment in raw_assignments:
            house = db.query(House).filter(House.id == assignment.house_id).first()

            item = {
                "assignment_id": assignment.id,
                "house_id": assignment.house_id,
                "house_name": house.name if house else f"house#{assignment.house_id}",
                "player_id": assignment.player_id,
                "status": assignment.status,
                "is_correct": assignment.is_correct,
                "delivery_mode": assignment.delivery_mode,
                "answer_mode": assignment.answer_mode,
                "result_applied": assignment.result_applied,
            }

            if assignment.status in {"answered", "resolved"}:
                stats["answered"] += 1

                if assignment.is_correct is True:
                    stats["correct"] += 1
                elif assignment.is_correct is False:
                    stats["wrong"] += 1
            elif assignment.status == "expired":
                stats["expired"] += 1
            else:
                stats["pending"] += 1

            assignments.append(item)

    return {
        "ok": True,
        "host_round": {
            "id": host_round.id,
            "title": host_round.title,
            "status": host_round.status,
            "round_code": host_round.round_code,
            "questions_total": host_round.questions_total,
            "current_question_no": host_round.current_question_no,
            "answers_open": host_round.answers_open,
        },
        "current_question": question_payload,
        "stats": stats,
        "assignments": assignments,
    }
