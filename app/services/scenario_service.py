import json
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.game_template import GameTemplate
from app.models.game_scenario_template import GameScenarioTemplate
from app.models.game_host_round import GameHostRound
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.game_phase import GamePhase
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate
from app.services.phase_service import close_game_phase_logic, has_active_phase, open_game_phase_logic


SYSTEM_STAGE_PHASE_MAP = {
    "stage_map_entry": "map",
    "stage_diplomacy_1": "diplomacy",
    "stage_crest": "crest",
    "stage_free_play": "free_play",
    "stage_upgrade": "upgrade",
    "stage_duels": "duel",
    "stage_intrigue": "intrigue",
    "stage_court": "court",
    "stage_last_whisper": "last_whisper",
}


def _normalize_scenario_lookup_value(value):
    if value is None:
        return ""
    return str(value).strip()


def _find_scenario_by_lookup(db: Session, scenario_code: str):
    normalized_code = _normalize_scenario_lookup_value(scenario_code)
    if not normalized_code:
        return None

    scenario = (
        db.query(GameScenarioTemplate)
        .filter(GameScenarioTemplate.code == normalized_code)
        .first()
    )
    if scenario:
        return scenario

    scenario = (
        db.query(GameScenarioTemplate)
        .join(GameTemplate, GameTemplate.id == GameScenarioTemplate.template_id)
        .filter(GameTemplate.template_code == normalized_code)
        .first()
    )
    if scenario:
        return scenario

    return (
        db.query(GameScenarioTemplate)
        .join(GameTemplate, GameTemplate.id == GameScenarioTemplate.template_id)
        .filter(GameTemplate.name == normalized_code)
        .first()
    )


def ensure_scenario_schema(engine):
    statements = [
        """
        CREATE TABLE IF NOT EXISTS game_scenario_templates (
            id SERIAL PRIMARY KEY,
            template_id INTEGER NULL,
            code VARCHAR NOT NULL UNIQUE,
            name VARCHAR NOT NULL,
            description TEXT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            status VARCHAR NOT NULL DEFAULT 'draft',
            recommended_houses TEXT NULL,
            metadata_json TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_game_scenario_templates_code ON game_scenario_templates(code)",
        "CREATE INDEX IF NOT EXISTS ix_game_scenario_templates_template_id ON game_scenario_templates(template_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_scenario_templates_status ON game_scenario_templates(status)",
        "ALTER TABLE round_templates ADD COLUMN IF NOT EXISTS scenario_id INTEGER",
        "ALTER TABLE round_templates ADD COLUMN IF NOT EXISTS import_key VARCHAR",
        "ALTER TABLE round_templates ADD COLUMN IF NOT EXISTS order_no INTEGER",
        "ALTER TABLE round_templates ADD COLUMN IF NOT EXISTS round_type VARCHAR",
        "ALTER TABLE round_templates ADD COLUMN IF NOT EXISTS is_optional BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS scenario_id INTEGER",
        "ALTER TABLE games ADD COLUMN IF NOT EXISTS scenario_code VARCHAR",
        "CREATE INDEX IF NOT EXISTS ix_games_scenario_id ON games(scenario_id)",
        "CREATE INDEX IF NOT EXISTS ix_games_scenario_code ON games(scenario_code)",
        "CREATE INDEX IF NOT EXISTS ix_round_templates_scenario_id ON round_templates(scenario_id)",
        "CREATE INDEX IF NOT EXISTS ix_round_templates_import_key ON round_templates(import_key)",
        "CREATE INDEX IF NOT EXISTS ix_round_templates_order_no ON round_templates(order_no)",
        "CREATE INDEX IF NOT EXISTS ix_round_templates_round_type ON round_templates(round_type)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _parse_json_text(value):
    if value is None:
        return None
    if isinstance(value, (dict, list, int, float, bool)):
        return value
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def _json_text(value, dump_json_fn):
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            return value
    return dump_json_fn(value)


def _ensure_backing_template(db: Session, scenario_data: dict):
    backing_template_code = _normalize_scenario_lookup_value(
        scenario_data.get("backing_template_code")
    )
    if backing_template_code:
        template = (
            db.query(GameTemplate)
            .filter(GameTemplate.template_code == backing_template_code)
            .first()
        )
        if not template:
            raise ValueError(
                f'Backing game template "{backing_template_code}" not found'
            )
        return template

    template = (
        db.query(GameTemplate)
        .filter(GameTemplate.template_code == scenario_data["code"])
        .first()
    )

    if not template:
        template = GameTemplate(template_code=scenario_data["code"])
        db.add(template)

    template.name = scenario_data.get("name") or scenario_data["code"]
    template.version = int(scenario_data.get("version") or 1)
    template.description = scenario_data.get("description")

    recommended_houses = scenario_data.get("recommended_houses")
    template.recommended_houses = recommended_houses if isinstance(recommended_houses, int) else None

    return template


def _resolve_scenario_backing_template(db: Session, scenario: GameScenarioTemplate):
    template = (
        db.query(GameTemplate)
        .filter(GameTemplate.id == scenario.template_id)
        .first()
    )
    if not template or not _normalize_scenario_lookup_value(template.template_code):
        raise ValueError(
            f'Backing game template for scenario "{scenario.code}" not found'
        )
    return template


def _upsert_scenario(db: Session, scenario_data: dict, import_mode: str, dump_json_fn):
    existing = (
        db.query(GameScenarioTemplate)
        .filter(GameScenarioTemplate.code == scenario_data["code"])
        .first()
    )

    if import_mode == "create" and existing:
        raise ValueError(f'Сценарий "{scenario_data["code"]}" уже существует')

    template = _ensure_backing_template(db, scenario_data)
    db.flush()

    scenario = existing
    if not scenario:
        scenario = GameScenarioTemplate(code=scenario_data["code"])
        db.add(scenario)

    scenario.template_id = template.id
    scenario.name = scenario_data.get("name") or scenario_data["code"]
    scenario.description = scenario_data.get("description")
    scenario.version = int(scenario_data.get("version") or 1)
    scenario.status = scenario_data.get("status") or "draft"
    scenario.recommended_houses = _json_text(scenario_data.get("recommended_houses"), dump_json_fn)
    scenario.metadata_json = _json_text(scenario_data.get("metadata_json") or scenario_data.get("metadata") or {}, dump_json_fn)

    db.flush()
    return scenario


def _delete_round_questions_for_round(db: Session, round_template_id: int):
    (
        db.query(RoundQuestionTemplate)
        .filter(RoundQuestionTemplate.round_template_id == round_template_id)
        .delete(synchronize_session=False)
    )


def _replace_scenario_rounds(db: Session, scenario_id: int):
    scenario_rounds = (
        db.query(RoundTemplate)
        .filter(RoundTemplate.scenario_id == scenario_id)
        .all()
    )

    for round_item in scenario_rounds:
        _delete_round_questions_for_round(db, round_item.id)

    (
        db.query(RoundTemplate)
        .filter(RoundTemplate.scenario_id == scenario_id)
        .delete(synchronize_session=False)
    )


def _normalize_question_content(question_item: dict):
    content = question_item.get("content") or {}
    if not isinstance(content, dict):
        content = {}

    if question_item.get("time_limit_sec") is not None and content.get("time_limit_sec") is None:
        content["time_limit_sec"] = question_item.get("time_limit_sec")

    return content


def _upsert_round(
    db: Session,
    *,
    scenario: GameScenarioTemplate,
    round_item: dict,
    import_mode: str,
    order_fallback: int,
    dump_json_fn,
):
    round_code = round_item.get("round_code")
    if not round_code:
        raise ValueError("У раунда отсутствует round_code")

    questions = round_item.get("questions") or []
    if not isinstance(questions, list):
        raise ValueError(f'У раунда "{round_code}" поле "questions" должно быть списком')

    existing_round = (
        db.query(RoundTemplate)
        .filter(
            RoundTemplate.scenario_id == scenario.id,
            RoundTemplate.round_code == round_code,
        )
        .first()
    )

    reusable_round = None
    if not existing_round:
        reusable_round = (
            db.query(RoundTemplate)
            .filter(
                RoundTemplate.template_id == scenario.template_id,
                RoundTemplate.scenario_id.is_(None),
                RoundTemplate.round_code == round_code,
            )
            .first()
        )

    if import_mode == "create" and existing_round:
        raise ValueError(f'Раунд "{round_code}" уже существует в сценарии "{scenario.code}"')

    if existing_round and import_mode == "replace":
        _delete_round_questions_for_round(db, existing_round.id)

    round_template = existing_round or reusable_round
    if not round_template:
        round_template = RoundTemplate(
            template_id=scenario.template_id,
            scenario_id=scenario.id,
            round_code=round_code,
        )
        db.add(round_template)

    order_no = round_item.get("order_no")
    act_number = round_item.get("act_number")
    round_type = round_item.get("round_type") or round_item.get("round_kind") or "series"

    round_template.template_id = scenario.template_id
    round_template.scenario_id = scenario.id
    round_template.import_key = round_item.get("import_key") or round_code
    round_template.title = round_item.get("title") or round_code
    round_template.order_no = order_no if order_no is not None else order_fallback
    round_template.act_number = act_number if act_number is not None else (round_template.order_no or order_fallback)
    round_template.round_type = round_type
    round_template.round_kind = round_item.get("round_kind") or round_type
    round_template.check_mode = round_item.get("check_mode") or "auto"
    round_template.questions_total = round_item.get("questions_total") or len(questions) or 1
    round_template.time_limit_sec = round_item.get("time_limit_sec")
    round_template.is_host_led = bool(round_item.get("is_host_led", True))
    round_template.is_optional = bool(round_item.get("is_optional", False))
    round_template.bar_window_opens = bool(round_item.get("bar_window_opens", False))
    round_template.scoring_mode = round_item.get("scoring_mode")
    round_template.question_transition_mode = round_item.get("question_transition_mode") or "manual"
    round_template.round_transition_mode = round_item.get("round_transition_mode") or "manual"
    round_template.intro_text = round_item.get("intro_text")
    round_template.outro_text = round_item.get("outro_text")

    db.flush()

    for idx, question_item in enumerate(questions, start=1):
        question_code = question_item.get("question_code")
        if not question_code:
            raise ValueError(f'У вопроса раунда "{round_code}" отсутствует question_code')

        existing_question = (
            db.query(RoundQuestionTemplate)
            .filter(
                RoundQuestionTemplate.round_template_id == round_template.id,
                RoundQuestionTemplate.question_code == question_code,
            )
            .first()
        )

        if import_mode == "create" and existing_question:
            raise ValueError(f'Вопрос "{question_code}" уже существует в раунде "{round_code}"')

        question_template = existing_question
        if not question_template:
            question_template = RoundQuestionTemplate(
                round_template_id=round_template.id,
                question_code=question_code,
            )
            db.add(question_template)

        question_template.sequence_no = question_item.get("sequence_no") or idx
        question_template.role_code = question_item.get("role_code")
        question_template.title = question_item.get("title")
        question_template.prompt = question_item.get("prompt") or ""
        question_template.ui_template = question_item.get("ui_template") or "text"
        question_template.answer_mode = question_item.get("answer_mode") or "text"
        question_template.auto_check = bool(question_item.get("auto_check", True))
        question_template.manual_check_allowed = bool(question_item.get("manual_check_allowed", False))
        question_template.allowed_house_keys = _json_text(question_item.get("allowed_house_keys", []), dump_json_fn)
        question_template.content_json = _json_text(_normalize_question_content(question_item), dump_json_fn)
        question_template.reward_json = _json_text(question_item.get("reward") or {}, dump_json_fn)
        question_template.fail_effect_json = _json_text(question_item.get("fail_effect") or {}, dump_json_fn)

    round_template.questions_total = len(questions) or round_template.questions_total
    db.flush()
    return round_template


def import_scenario_logic(db: Session, *, payload: dict, dump_json_fn):
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    import_mode = payload.get("import_mode") or "create"
    if import_mode not in {"create", "replace", "merge"}:
        return {
            "ok": False,
            "message": 'import_mode должен быть одним из: "create", "replace", "merge"',
        }

    scenario_data = payload.get("scenario") or {}
    rounds = payload.get("rounds") or []

    if not isinstance(scenario_data, dict) or not scenario_data.get("code"):
        return {
            "ok": False,
            "message": 'В поле "scenario" должен быть объект с непустым code',
        }

    if not isinstance(rounds, list):
        return {
            "ok": False,
            "message": 'Поле "rounds" должно быть списком',
        }

    try:
        scenario = _upsert_scenario(db, scenario_data, import_mode, dump_json_fn)

        if import_mode == "replace":
            _replace_scenario_rounds(db, scenario.id)

        imported_round_codes = []
        imported_question_codes = []

        for idx, round_item in enumerate(rounds, start=1):
            round_template = _upsert_round(
                db,
                scenario=scenario,
                round_item=round_item,
                import_mode="merge" if import_mode == "merge" else "replace" if import_mode == "replace" else "create",
                order_fallback=idx,
                dump_json_fn=dump_json_fn,
            )
            imported_round_codes.append(round_template.round_code)
            for question in round_item.get("questions") or []:
                if question.get("question_code"):
                    imported_question_codes.append(question["question_code"])

        db.commit()
        db.refresh(scenario)

        return {
            "ok": True,
            "message": "Сценарий импортирован",
            "scenario": build_scenario_detail_payload(db, scenario),
            "import_mode": import_mode,
            "imported_round_codes": imported_round_codes,
            "imported_question_codes": imported_question_codes,
        }
    except ValueError as e:
        db.rollback()
        return {
            "ok": False,
            "message": str(e),
        }


def import_scenario_round_logic(db: Session, *, scenario_code: str, payload: dict, dump_json_fn):
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    import_mode = payload.get("import_mode") or "create"
    if import_mode not in {"create", "replace", "merge"}:
        return {
            "ok": False,
            "message": 'import_mode должен быть одним из: "create", "replace", "merge"',
        }

    scenario = (
        db.query(GameScenarioTemplate)
        .filter(GameScenarioTemplate.code == scenario_code)
        .first()
    )

    if not scenario:
        return {
            "ok": False,
            "message": f'Сценарий "{scenario_code}" не найден',
        }

    try:
        round_template = _upsert_round(
            db,
            scenario=scenario,
            round_item=payload,
            import_mode=import_mode,
            order_fallback=payload.get("order_no") or 1,
            dump_json_fn=dump_json_fn,
        )
        db.commit()
        db.refresh(scenario)

        return {
            "ok": True,
            "message": "Раунд импортирован в сценарий",
            "import_mode": import_mode,
            "scenario": build_scenario_detail_payload(db, scenario),
            "round": {
                "id": round_template.id,
                "round_code": round_template.round_code,
                "title": round_template.title,
                "order_no": round_template.order_no,
                "questions_total": round_template.questions_total,
            },
        }
    except ValueError as e:
        db.rollback()
        return {
            "ok": False,
            "message": str(e),
        }


def build_scenario_detail_payload(db: Session, scenario: GameScenarioTemplate):
    rounds = (
        db.query(RoundTemplate)
        .filter(RoundTemplate.scenario_id == scenario.id)
        .order_by(RoundTemplate.order_no.asc().nullslast(), RoundTemplate.id.asc())
        .all()
    )

    rounds_payload = []
    questions_total = 0
    for round_item in rounds:
        questions_count = (
            db.query(RoundQuestionTemplate)
            .filter(RoundQuestionTemplate.round_template_id == round_item.id)
            .count()
        )
        questions_total += questions_count
        rounds_payload.append(
            {
                "id": round_item.id,
                "round_code": round_item.round_code,
                "title": round_item.title,
                "order_no": round_item.order_no,
                "act_number": round_item.act_number,
                "round_type": round_item.round_type,
                "round_kind": round_item.round_kind,
                "is_optional": round_item.is_optional,
                "import_key": round_item.import_key,
                "questions_count": questions_count,
            }
        )

    return {
        "id": scenario.id,
        "code": scenario.code,
        "name": scenario.name,
        "description": scenario.description,
        "version": scenario.version,
        "status": scenario.status,
        "recommended_houses": _parse_json_text(scenario.recommended_houses),
        "metadata": _parse_json_text(scenario.metadata_json),
        "template_id": scenario.template_id,
        "rounds_count": len(rounds_payload),
        "questions_count": questions_total,
        "rounds": rounds_payload,
    }


def list_scenarios_logic(db: Session):
    scenarios = (
        db.query(GameScenarioTemplate)
        .order_by(GameScenarioTemplate.id.asc())
        .all()
    )

    payload = []
    for scenario in scenarios:
        detail = build_scenario_detail_payload(db, scenario)
        payload.append(
            {
                "id": detail["id"],
                "code": detail["code"],
                "name": detail["name"],
                "version": detail["version"],
                "status": detail["status"],
                "rounds_count": detail["rounds_count"],
                "questions_count": detail["questions_count"],
            }
        )

    return {
        "ok": True,
        "scenarios_count": len(payload),
        "scenarios": payload,
    }


def get_scenario_logic(db: Session, *, scenario_code: str):
    scenario = (
        db.query(GameScenarioTemplate)
        .filter(GameScenarioTemplate.code == scenario_code)
        .first()
    )

    if not scenario:
        return {
            "ok": False,
            "message": f'Сценарий "{scenario_code}" не найден',
            "scenario_code": scenario_code,
        }

    return {
        "ok": True,
        "scenario": build_scenario_detail_payload(db, scenario),
    }


def _build_game_scenario_payload(db: Session, game: Game):
    scenario = None

    if getattr(game, "scenario_code", None):
        scenario = (
            db.query(GameScenarioTemplate)
            .filter(GameScenarioTemplate.code == game.scenario_code)
            .first()
        )

    if not scenario and getattr(game, "scenario_id", None):
        scenario = (
            db.query(GameScenarioTemplate)
            .filter(GameScenarioTemplate.id == game.scenario_id)
            .first()
        )

    applied_rounds_count = 0
    if scenario:
        applied_rounds_count = (
            db.query(RoundTemplate)
            .filter(RoundTemplate.scenario_id == scenario.id)
            .count()
        )

    return {
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
            "template_code": game.template_code,
            "scenario_code": getattr(game, "scenario_code", None),
            "scenario_id": getattr(game, "scenario_id", None),
        },
        "scenario": build_scenario_detail_payload(db, scenario) if scenario else None,
        "applied_rounds_count": applied_rounds_count,
    }


def get_game_scenario_logic(db: Session, *, room_code: str):
    game = (
        db.query(Game)
        .filter(Game.room_code == room_code)
        .first()
    )

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    payload = _build_game_scenario_payload(db, game)

    return {
        "ok": True,
        "linked": payload["scenario"] is not None,
        **payload,
    }


def apply_scenario_to_game_logic(db: Session, *, room_code: str, payload: dict):
    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
            "room_code": room_code,
        }

    scenario_code = _normalize_scenario_lookup_value(
        payload.get("scenario_code") or payload.get("code") or payload.get("template_code")
    )
    apply_mode = payload.get("apply_mode") or payload.get("import_mode") or "replace"

    if apply_mode not in {"create", "replace", "merge"}:
        return {
            "ok": False,
            "message": 'apply_mode должен быть одним из: "create", "replace", "merge"',
            "room_code": room_code,
        }

    if not scenario_code:
        return {
            "ok": False,
            "message": 'Поле "scenario_code" обязательно',
            "room_code": room_code,
        }

    game = (
        db.query(Game)
        .filter(Game.room_code == room_code)
        .first()
    )

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    scenario = _find_scenario_by_lookup(db, scenario_code)

    if not scenario:
        return {
            "ok": False,
            "message": f'Сценарий "{scenario_code}" не найден',
            "room_code": room_code,
        }

    current_scenario_code = getattr(game, "scenario_code", None)
    already_applied = current_scenario_code == scenario.code

    if current_scenario_code and current_scenario_code != scenario.code and apply_mode == "create":
        return {
            "ok": False,
            "message": f'У игры уже привязан сценарий "{current_scenario_code}"',
            "room_code": room_code,
            "current_scenario_code": current_scenario_code,
        }

    game.scenario_id = scenario.id
    game.scenario_code = scenario.code
    backing_template = _resolve_scenario_backing_template(db, scenario)
    game.template_code = backing_template.template_code

    _cleanup_stale_court_runtime(db, game)
    db.flush()
    db.commit()
    db.refresh(game)

    payload_data = _build_game_scenario_payload(db, game)

    return {
        "ok": True,
        "message": "Сценарий применён к игре",
        "apply_mode": apply_mode,
        "already_applied": already_applied,
        **payload_data,
    }


def _serialize_round_brief(round_item: RoundTemplate | None):
    if not round_item:
        return None

    return {
        "id": round_item.id,
        "round_code": round_item.round_code,
        "title": round_item.title,
        "order_no": round_item.order_no,
        "act_number": round_item.act_number,
        "round_type": round_item.round_type,
        "round_kind": round_item.round_kind,
        "questions_total": round_item.questions_total,
    }


def _serialize_host_round_brief(host_round: GameHostRound | None):
    if not host_round:
        return None

    return {
        "id": host_round.id,
        "status": host_round.status,
        "round_code": host_round.round_code,
        "round_template_id": host_round.round_template_id,
        "title": host_round.title,
    }


def _get_linked_scenario(db: Session, game: Game):
    scenario = None

    if getattr(game, "scenario_id", None):
        scenario = (
            db.query(GameScenarioTemplate)
            .filter(GameScenarioTemplate.id == game.scenario_id)
            .first()
        )

    if not scenario and getattr(game, "scenario_code", None):
        scenario = (
            db.query(GameScenarioTemplate)
            .filter(GameScenarioTemplate.code == game.scenario_code)
            .first()
        )

    return scenario


SCENARIO_AUXILIARY_ROUND_KINDS = {"question_bank"}


def _is_scenario_director_round(round_item: RoundTemplate | None) -> bool:
    if round_item is None:
        return False
    round_kind = str(getattr(round_item, "round_kind", "") or "").strip().lower()
    return round_kind not in SCENARIO_AUXILIARY_ROUND_KINDS


def _get_scenario_rounds(db: Session, scenario_id: int):
    rounds = (
        db.query(RoundTemplate)
        .filter(RoundTemplate.scenario_id == scenario_id)
        .order_by(RoundTemplate.order_no.asc().nullslast(), RoundTemplate.id.asc())
        .all()
    )
    return [round_item for round_item in rounds if _is_scenario_director_round(round_item)]


def _get_scenario_host_rounds(db: Session, game_id: int, scenario_round_ids: list[int]):
    if not scenario_round_ids:
        return []

    return (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game_id,
            GameHostRound.round_template_id.in_(scenario_round_ids),
        )
        .order_by(GameHostRound.id.asc())
        .all()
    )


def _is_system_stage_round(round_item: RoundTemplate | None) -> bool:
    if not round_item:
        return False
    if getattr(round_item, "round_code", None) in SYSTEM_STAGE_PHASE_MAP:
        return True
    round_type = getattr(round_item, "round_type", None) or getattr(round_item, "round_kind", None)
    return round_type == "system_stage"


def _get_system_stage_phase_type(round_item: RoundTemplate | None):
    if not round_item:
        return None
    return SYSTEM_STAGE_PHASE_MAP.get(round_item.round_code)


def _build_system_stage_phase_payload(game: Game, scenario: GameScenarioTemplate, round_item: RoundTemplate):
    return {
        "source": "scenario_system_stage",
        "scenario_id": scenario.id,
        "scenario_code": scenario.code,
        "round_template_id": round_item.id,
        "round_code": round_item.round_code,
        "round_type": round_item.round_type,
    }


def _cleanup_stale_court_runtime(db: Session, game: Game) -> bool:
    changed = False
    now = datetime.utcnow()

    active_court_phases = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == "court",
            GamePhase.status == "active",
        )
        .all()
    )

    for phase in active_court_phases:
        phase.status = "closed"
        phase.closed_at = now
        db.add(phase)
        changed = True

    court_host_rounds = (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game.id,
            GameHostRound.round_code == "stage_court_battle",
            GameHostRound.status.in_(["active", "completed_waiting_host"]),
        )
        .all()
    )

    for host_round in court_host_rounds:
        active_questions = (
            db.query(GameHostRoundQuestion)
            .filter(
                GameHostRoundQuestion.host_round_id == host_round.id,
                GameHostRoundQuestion.status == "active",
            )
            .all()
        )
        for runtime_question in active_questions:
            runtime_question.status = "resolved"
            runtime_question.answers_open = False
            runtime_question.resolved_at = now
            db.add(runtime_question)

        host_round.answers_open = False
        host_round.status = "finished"
        db.add(host_round)
        changed = True

    if changed:
        remaining_active_host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == game.id,
                GameHostRound.status.in_(["active", "completed_waiting_host"]),
            )
            .first()
        )
        if not remaining_active_host_round:
            active_host_round_phases = (
                db.query(GamePhase)
                .filter(
                    GamePhase.game_id == game.id,
                    GamePhase.phase_type == "host_round",
                    GamePhase.status == "active",
                )
                .all()
            )
            for phase in active_host_round_phases:
                phase.status = "closed"
                phase.closed_at = now
                db.add(phase)

        db.flush()

    return changed


def _get_scenario_game_phases(db: Session, game_id: int, scenario: GameScenarioTemplate):
    phases = (
        db.query(GamePhase)
        .filter(GamePhase.game_id == game_id)
        .order_by(GamePhase.id.asc())
        .all()
    )

    filtered = []
    for phase in phases:
        payload = phase.payload if isinstance(phase.payload, dict) else {}
        if payload.get("scenario_id") != scenario.id and payload.get("scenario_code") != scenario.code:
            continue
        if not payload.get("round_template_id"):
            continue
        filtered.append(phase)

    return filtered


def _open_system_stage_for_round(db: Session, game: Game, scenario: GameScenarioTemplate, round_item: RoundTemplate):
    phase_type = _get_system_stage_phase_type(round_item)
    if not phase_type:
        return {
            "ok": False,
            "message": f'Для system_stage "{round_item.round_code}" не найден phase_type mapping',
            "round_code": round_item.round_code,
        }

    existing_phase = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == phase_type,
            GamePhase.status == "active",
        )
        .order_by(GamePhase.id.desc())
        .first()
    )

    if phase_type == "court" and existing_phase:
        payload = existing_phase.payload if isinstance(existing_phase.payload, dict) else {}
        if (
            payload.get("source") != "scenario_system_stage"
            or payload.get("round_template_id") != round_item.id
            or payload.get("scenario_id") != scenario.id
        ):
            _cleanup_stale_court_runtime(db, game)
            db.commit()
            existing_phase = None

    if existing_phase:
        payload = existing_phase.payload if isinstance(existing_phase.payload, dict) else {}
        desired_payload = _build_system_stage_phase_payload(game, scenario, round_item)
        if (
            payload.get("source") != "scenario_system_stage"
            or payload.get("round_template_id") != round_item.id
            or payload.get("scenario_id") != scenario.id
        ):
            existing_phase.payload = {
                **payload,
                **desired_payload,
            }
            db.add(existing_phase)
            db.commit()
            db.refresh(existing_phase)
        return {
            "ok": True,
            "message": f'Фаза "{phase_type}" уже активна',
            "phase": {
                "id": existing_phase.id,
                "phase_type": existing_phase.phase_type,
                "status": existing_phase.status,
                "payload": existing_phase.payload,
            },
            "round_template": _serialize_round_brief(round_item),
        }

    phase = GamePhase(
        game_id=game.id,
        phase_type=phase_type,
        status="active",
        payload=_build_system_stage_phase_payload(game, scenario, round_item),
    )
    db.add(phase)
    db.commit()
    db.refresh(phase)

    return {
        "ok": True,
        "message": f'Сценарный этап "{round_item.round_code}" активирован через фазу "{phase_type}"',
        "phase": {
            "id": phase.id,
            "phase_type": phase.phase_type,
            "status": phase.status,
            "payload": phase.payload,
        },
        "round_template": _serialize_round_brief(round_item),
    }


def _close_system_stage_for_round(db: Session, game: Game, scenario: GameScenarioTemplate, round_item: RoundTemplate):
    phase_type = _get_system_stage_phase_type(round_item)
    if not phase_type:
        return {
            "ok": False,
            "message": f'Для system_stage "{round_item.round_code}" не найден phase_type mapping',
            "round_code": round_item.round_code,
        }

    phase = None
    for item in reversed(_get_scenario_game_phases(db, game.id, scenario)):
        payload = item.payload if isinstance(item.payload, dict) else {}
        if (
            item.status == "active"
            and item.phase_type == phase_type
            and payload.get("round_template_id") == round_item.id
        ):
            phase = item
            break

    if not phase:
        return {
            "ok": True,
            "message": "Активная системная фаза уже закрыта или не была открыта",
            "round_template": _serialize_round_brief(round_item),
        }

    if round_item.round_code == "stage_court":
        court_host_rounds = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == game.id,
                GameHostRound.round_code == "stage_court_battle",
                GameHostRound.status.in_(["active", "completed_waiting_host"]),
            )
            .all()
        )

        for host_round in court_host_rounds:
            active_questions = (
                db.query(GameHostRoundQuestion)
                .filter(
                    GameHostRoundQuestion.host_round_id == host_round.id,
                    GameHostRoundQuestion.status == "active",
                )
                .all()
            )
            for runtime_question in active_questions:
                runtime_question.status = "resolved"
                runtime_question.answers_open = False
                runtime_question.resolved_at = datetime.utcnow()
                db.add(runtime_question)

            host_round.answers_open = False
            host_round.status = "finished"
            db.add(host_round)

    phase.status = "closed"
    phase.closed_at = datetime.utcnow()
    db.add(phase)
    db.commit()
    db.refresh(phase)

    if round_item.round_code == "stage_court" and has_active_phase(db, game.id, "host_round"):
        remaining_active_host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == game.id,
                GameHostRound.status.in_(["active", "completed_waiting_host"]),
            )
            .first()
        )
        if not remaining_active_host_round:
            close_game_phase_logic(db, game.room_code, "host_round")
            db.flush()
            db.commit()

    return {
        "ok": True,
        "message": f'Сценарный этап "{round_item.round_code}" завершён',
        "phase": {
            "id": phase.id,
            "phase_type": phase.phase_type,
            "status": phase.status,
            "payload": phase.payload,
        },
        "round_template": _serialize_round_brief(round_item),
    }


def _build_director_state(db: Session, game: Game, scenario: GameScenarioTemplate):
    rounds = _get_scenario_rounds(db, scenario.id)
    round_ids = [item.id for item in rounds]
    host_rounds = _get_scenario_host_rounds(db, game.id, round_ids)
    system_stage_phases = _get_scenario_game_phases(db, game.id, scenario)

    rounds_by_id = {item.id: item for item in rounds}
    order_by_round_id = {item.id: idx + 1 for idx, item in enumerate(rounds)}

    active_host_round = next(
        (
            item
            for item in reversed(host_rounds)
            if item.status in {"active", "completed_waiting_host"}
        ),
        None,
    )

    last_completed_host_round = next(
        (
            item
            for item in reversed(host_rounds)
            if item.status == "finished"
        ),
        None,
    )

    active_system_stage_round = None
    active_system_stage_phase = None
    completed_system_stage_ids = set()

    for phase in system_stage_phases:
        payload = phase.payload if isinstance(phase.payload, dict) else {}
        round_template_id = payload.get("round_template_id")
        if not round_template_id:
            continue

        round_item = rounds_by_id.get(round_template_id)
        if not round_item:
            continue

        if phase.status == "active":
            active_system_stage_round = round_item
            active_system_stage_phase = phase
        elif phase.status in {"closed", "finished", "completed"}:
            completed_system_stage_ids.add(round_template_id)

    current_round = None
    current_round_status = "pending"
    active_host_round_payload = None

    if active_host_round:
        current_round = rounds_by_id.get(active_host_round.round_template_id)
        current_round_status = active_host_round.status
        active_host_round_payload = _serialize_host_round_brief(active_host_round)
    elif active_system_stage_round:
        current_round = active_system_stage_round
        current_round_status = active_system_stage_phase.status if active_system_stage_phase else "active"

    completed_host_round_ids = {
        item.round_template_id
        for item in host_rounds
        if item.status == "finished"
    }
    completed_ids = completed_host_round_ids | completed_system_stage_ids

    last_completed_round = None
    for round_item in reversed(rounds):
        if round_item.id in completed_ids:
            last_completed_round = round_item
            break

    if current_round:
        current_index = order_by_round_id.get(current_round.id, 0)
        next_round = rounds[current_index] if current_index < len(rounds) else None
    elif last_completed_round:
        last_index = order_by_round_id.get(last_completed_round.id, 0)
        current_index = last_index
        next_round = rounds[last_index] if last_index < len(rounds) else None
    else:
        current_index = 0
        next_round = rounds[0] if rounds else None

    has_active_system_stage = active_system_stage_round is not None
    scenario_finished = bool(rounds) and next_round is None and active_host_round is None and not has_active_system_stage
    if not current_round and last_completed_round:
        current_round_status = "finished"
    current_round_completed = current_round is None and last_completed_round is not None
    can_start_next = active_host_round is None and not has_active_system_stage and next_round is not None
    can_advance = (
        (active_host_round is not None and active_host_round.status == "completed_waiting_host")
        or has_active_system_stage
    )
    can_advance_and_start = can_advance and next_round is not None

    rounds_overview = []
    active_round_id = current_round.id if current_round else None

    for idx, round_item in enumerate(rounds, start=1):
        status = "pending"
        if round_item.id == active_round_id:
            status = current_round_status if current_round_status else "active"
        elif round_item.id in completed_ids:
            status = "finished"
        elif next_round and round_item.id == next_round.id:
            status = "next"

        rounds_overview.append(
            {
                "round_code": round_item.round_code,
                "title": round_item.title,
                "order_no": round_item.order_no,
                "index": idx,
                "status": status,
            }
        )

    return {
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
            "scenario_code": getattr(game, "scenario_code", None),
            "scenario_id": getattr(game, "scenario_id", None),
            "template_code": game.template_code,
        },
        "linked_scenario": {
            "id": scenario.id,
            "code": scenario.code,
            "name": scenario.name,
            "version": scenario.version,
            "status": scenario.status,
            "rounds_total": len(rounds),
        },
        "current_round": _serialize_round_brief(current_round),
        "current_round_status": current_round_status,
        "current_round_completed": current_round_completed,
        "next_round": _serialize_round_brief(next_round),
        "last_completed_round": _serialize_round_brief(last_completed_round),
        "has_active_host_round": active_host_round is not None,
        "active_host_round": active_host_round_payload,
        "active_system_stage_phase": {
            "id": active_system_stage_phase.id,
            "phase_type": active_system_stage_phase.phase_type,
            "status": active_system_stage_phase.status,
            "payload": active_system_stage_phase.payload,
        } if active_system_stage_phase else None,
        "can_start_next": can_start_next,
        "can_advance": can_advance,
        "can_advance_and_start": can_advance_and_start,
        "scenario_finished": scenario_finished,
        "progress": {
            "current_index": current_index,
            "total": len(rounds),
            "completed_count": len(completed_ids),
        },
        "rounds_overview": rounds_overview,
    }


def get_scenario_director_logic(db: Session, *, room_code: str):
    game = (
        db.query(Game)
        .filter(Game.room_code == room_code)
        .first()
    )

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    scenario = _get_linked_scenario(db, game)
    if not scenario:
        return {
            "ok": False,
            "message": "К игре не привязан сценарий",
            "room_code": room_code,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
        }

    return {
        "ok": True,
        **_build_director_state(db, game, scenario),
    }


def _classify_scenario_round_start_conflict(host_rounds, round_template: RoundTemplate):
    exact_matches = [
        item
        for item in host_rounds
        if item.round_template_id == round_template.id
    ]
    if exact_matches:
        return {
            "type": "duplicate_round_template",
            "host_round": exact_matches[-1],
        }

    wrong_template_matches = [
        item
        for item in host_rounds
        if item.round_code == round_template.round_code
    ]
    if wrong_template_matches:
        return {
            "type": "round_code_template_mismatch",
            "host_round": wrong_template_matches[-1],
        }

    return None


def start_next_scenario_round_logic(
    db: Session,
    *,
    room_code: str,
    start_series_round_fn,
):
    game = (
        db.query(Game)
        .filter(Game.room_code == room_code)
        .with_for_update()
        .first()
    )

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    scenario = _get_linked_scenario(db, game)
    if not scenario:
        return {
            "ok": False,
            "message": "К игре не привязан сценарий",
            "room_code": room_code,
        }

    director = _build_director_state(db, game, scenario)
    active_host_round = director.get("active_host_round")

    if active_host_round and active_host_round.get("status") in {"active", "waiting_host", "completed_waiting_host"}:
        return {
            "ok": False,
            "message": "Сначала завершите текущий раунд сценария",
            "active_host_round": active_host_round,
            "linked_scenario": director.get("linked_scenario"),
            "current_round": director.get("current_round"),
            "next_round_preview": director.get("next_round"),
            "scenario_finished": director.get("scenario_finished"),
        }

    if director.get("active_system_stage_phase"):
        return {
            "ok": False,
            "message": "Сначала завершите текущий этап сценария",
            "active_system_stage_phase": director.get("active_system_stage_phase"),
            "linked_scenario": director.get("linked_scenario"),
            "current_round": director.get("current_round"),
            "next_round_preview": director.get("next_round"),
            "scenario_finished": director.get("scenario_finished"),
        }

    next_round = director.get("next_round")
    total = director.get("progress", {}).get("total", 0)

    if not next_round:
        return {
            "ok": False,
            "message": "Следующего раунда в сценарии нет",
            "linked_scenario": director.get("linked_scenario"),
            "scenario_finished": True,
        }

    round_template = (
        db.query(RoundTemplate)
        .filter(RoundTemplate.id == next_round["id"])
        .first()
    )

    if not round_template:
        return {
            "ok": False,
            "message": "Шаблон следующего раунда не найден",
            "linked_scenario": director.get("linked_scenario"),
            "next_round": next_round,
        }

    existing_same_code_rounds = (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game.id,
            GameHostRound.round_code == round_template.round_code,
        )
        .order_by(GameHostRound.id.asc())
        .all()
    )
    start_conflict = _classify_scenario_round_start_conflict(
        existing_same_code_rounds,
        round_template,
    )
    if start_conflict:
        existing_host_round = start_conflict["host_round"]
        return {
            "ok": False,
            "message": "Scenario round start blocked because this round code already has runtime history",
            "duplicate_start_blocked": True,
            "conflict_type": start_conflict["type"],
            "target_round_template_id": round_template.id,
            "target_scenario_id": scenario.id,
            "existing_host_round": _serialize_host_round_brief(existing_host_round),
        }

    if round_template.round_code != "stage_court":
        _cleanup_stale_court_runtime(db, game)

    if _is_system_stage_round(round_template):
        start_result = _open_system_stage_for_round(db, game, scenario, round_template)
    else:
        if not has_active_phase(db, game.id, "host_round"):
            phase_open_result = open_game_phase_logic(db, game.room_code, "host_round")
            if not phase_open_result.get("ok"):
                return phase_open_result
        start_result = start_series_round_fn(
            db,
            game,
            next_round["round_code"],
            round_template_id=round_template.id,
            scenario_id=scenario.id,
        )

    if not start_result.get("ok"):
        return start_result

    current_index = 0
    for idx, item in enumerate(director.get("rounds_overview", []), start=1):
        if item.get("round_code") == next_round["round_code"]:
            current_index = idx
            break

    next_round_preview = None
    if current_index < total:
        overview = director.get("rounds_overview", [])
        if current_index < len(overview):
            next_code = overview[current_index]["round_code"]
            for round_item in _get_scenario_rounds(db, scenario.id):
                if round_item.round_code == next_code:
                    next_round_preview = _serialize_round_brief(round_item)
                    break

    return {
        "ok": True,
        "message": "Следующий раунд сценария запущен",
        "linked_scenario": director.get("linked_scenario"),
        "started_round": start_result.get("round_template"),
        "host_round": start_result.get("host_round"),
        "current_index": current_index,
        "total": total,
        "next_round_preview": next_round_preview,
        "scenario_finished": next_round_preview is None and current_index == total,
    }


def advance_scenario_logic(
    db: Session,
    *,
    room_code: str,
    payload: dict,
    finalize_host_round_fn,
    start_series_round_fn,
):
    if not isinstance(payload, dict):
        payload = {}

    def _is_truthy(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return False

    auto_start_next = bool(payload.get("auto_start_next", False))
    force_advance = _is_truthy(payload.get("force"))

    game = (
        db.query(Game)
        .filter(Game.room_code == room_code)
        .first()
    )

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    scenario = _get_linked_scenario(db, game)
    if not scenario:
        return {
            "ok": False,
            "message": "К игре не привязан сценарий",
            "room_code": room_code,
        }

    director = _build_director_state(db, game, scenario)
    active_host_round_payload = director.get("active_host_round")
    current_round_payload = director.get("current_round")
    current_round = None
    if current_round_payload:
        current_round = (
            db.query(RoundTemplate)
            .filter(RoundTemplate.id == current_round_payload["id"])
            .first()
        )

    target_host_round = None
    if active_host_round_payload:
        target_host_round = (
            db.query(GameHostRound)
            .filter(GameHostRound.id == active_host_round_payload["id"])
            .first()
        )
    elif current_round and _is_system_stage_round(current_round) and director.get("active_system_stage_phase"):
        if current_round.round_code == "stage_court" and not force_advance:
            active_phase_payload = director.get("active_system_stage_phase", {}).get("payload") or {}
            if (
                isinstance(active_phase_payload, dict)
                and active_phase_payload.get("source") == "court_mvp"
                and active_phase_payload.get("status") != "court_finished"
            ):
                return {
                    "ok": False,
                    "needs_confirmation": True,
                    "message": "Суд Домов ещё не завершён. Завершить принудительно?",
                    "court_status": active_phase_payload.get("status"),
                    "hint": "Передайте force=true для принудительного завершения",
                    "current_round": current_round_payload,
                    "next_round": director.get("next_round"),
                }

        close_result = _close_system_stage_for_round(db, game, scenario, current_round)
        if not close_result.get("ok"):
            return close_result

        refreshed_director = _build_director_state(db, game, scenario)
        completed_round = current_round_payload
        next_round = refreshed_director.get("next_round")
        auto_started = False
        started_round = None

        if auto_start_next and next_round:
            start_result = start_next_scenario_round_logic(
                db,
                room_code=room_code,
                start_series_round_fn=start_series_round_fn,
            )
            if start_result.get("ok"):
                auto_started = True
                started_round = start_result.get("started_round")
                next_round = start_result.get("next_round_preview")
            else:
                return {
                    "ok": False,
                    "message": "Системный этап завершён, но следующий автоматически запустить не удалось",
                    "completed_round": completed_round,
                    "next_round": next_round,
                    "auto_started": False,
                    "start_next_error": start_result,
                    "scenario_finished": refreshed_director.get("scenario_finished"),
                }

        return {
            "ok": True,
            "message": "Системный этап сценария завершён",
            "completed_round": completed_round,
            "next_round": next_round,
            "auto_started": auto_started,
            "started_round": started_round,
            "scenario_finished": refreshed_director.get("scenario_finished") and not auto_started,
        }
    elif director.get("last_completed_round"):
        target_host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == game.id,
                GameHostRound.round_template_id == director["last_completed_round"]["id"],
                GameHostRound.status == "finished",
            )
            .order_by(GameHostRound.id.desc())
            .first()
        )

    if not target_host_round:
        return {
            "ok": False,
            "message": "Для сценария ещё нет раунда, который можно подтвердить",
            "linked_scenario": director.get("linked_scenario"),
        }

    if target_host_round.status == "completed_waiting_host":
        target_host_round.status = "finished"
        target_host_round.answers_open = False
        db.add(target_host_round)
        db.flush()
        db.commit()
        db.refresh(target_host_round)
    elif target_host_round.status != "finished":
        return {
            "ok": False,
            "message": f'Нельзя подтвердить завершение раунда со статусом "{target_host_round.status}"',
            "active_host_round": director.get("active_host_round"),
        }

    remaining_active_host_round = (
        db.query(GameHostRound)
        .filter(
            GameHostRound.game_id == game.id,
            GameHostRound.status.in_(["active", "completed_waiting_host"]),
        )
        .first()
    )

    if not remaining_active_host_round and has_active_phase(db, game.id, "host_round"):
        phase_close_result = close_game_phase_logic(db, game.room_code, "host_round")
        if not phase_close_result.get("ok"):
            return phase_close_result
        db.flush()
        db.commit()

    refreshed_director = _build_director_state(db, game, scenario)
    completed_round = refreshed_director.get("last_completed_round")
    next_round = refreshed_director.get("next_round")
    auto_started = False
    started_round = None

    if auto_start_next and next_round:
        start_result = start_next_scenario_round_logic(
            db,
            room_code=room_code,
            start_series_round_fn=start_series_round_fn,
        )
        if start_result.get("ok"):
            auto_started = True
            started_round = start_result.get("started_round")
            next_round = start_result.get("next_round_preview")
        else:
            return {
                "ok": False,
                "message": "Раунд завершён, но следующий автоматически запустить не удалось",
                "completed_round": completed_round,
                "next_round": next_round,
                "auto_started": False,
                "start_next_error": start_result,
                "scenario_finished": refreshed_director.get("scenario_finished"),
            }

    return {
        "ok": True,
        "message": "Завершение раунда сценария подтверждено",
        "completed_round": completed_round,
        "next_round": next_round,
        "auto_started": auto_started,
        "started_round": started_round,
        "scenario_finished": refreshed_director.get("scenario_finished") and not auto_started,
    }
