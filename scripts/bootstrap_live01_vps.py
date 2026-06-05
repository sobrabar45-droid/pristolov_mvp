#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Game, Role
from app.models.game_scenario_template import GameScenarioTemplate
from app.services.duel_service import ensure_duel_schema
from app.services.expedition_service import ensure_expedition_schema
from app.services.house_service import ensure_house_schema
from app.services.scenario_service import (
    apply_scenario_to_game_logic,
    ensure_scenario_schema,
    import_scenario_logic,
)
from app.services.serialization_utils import dump_json, load_yaml_file
from app.services.template_service import (
    import_template_core_real_logic,
    import_template_map_real_logic,
    import_template_rounds_real_logic,
    import_template_task_pools_real_logic,
)
from app.services.tower_service import ensure_tower_schema


ROOM_CODE = "LIVE01"
GAME_TITLE = "Железный Стол"
TEMPLATE_CODE = "season1_core_v1"
SCENARIO_CODE = "season1_mvp_live_v2"
GAME_TEMPLATES_DIR = PROJECT_ROOT / "app" / "game_templates"
SCENARIO_PATH = GAME_TEMPLATES_DIR / "scenarios" / f"{SCENARIO_CODE}.json"

REQUIRED_ROLES = [
    {
        "code": "lord_lady",
        "name": "Лорд / Леди",
        "description": "Глава Дома: стратегические решения, дуэли и финальные выборы.",
    },
    {
        "code": "diplomat",
        "name": "Дипломат",
        "description": "Переговоры, сделки и союзные договорённости Дома.",
    },
    {
        "code": "maester",
        "name": "Мейстер",
        "description": "Знания, вопросы и аналитические задания Дома.",
    },
    {
        "code": "whisper_master",
        "name": "Мастер шепота",
        "description": "Тайные политические действия перед финалом.",
    },
    {
        "code": "treasurer",
        "name": "Мастер над золотом",
        "description": "Золото, сделки и подтверждение ресурсных переводов.",
    },
    {
        "code": "house_sworn",
        "name": "Соратник Дома",
        "description": "Участник Дома без отдельной v1 управляющей роли.",
    },
]


class BootstrapFailure(Exception):
    pass


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _redacted_db_target() -> str:
    try:
        url = make_url(settings.DATABASE_URL)
        host = url.host or "local"
        database = url.database or ""
        return f"{url.drivername}://{host}/{database}"
    except Exception:
        return "<configured DATABASE_URL>"


def _ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_scenario_schema(engine)
    ensure_expedition_schema(engine)
    ensure_house_schema(engine)
    ensure_tower_schema(engine)
    ensure_duel_schema(engine)


def _ensure_roles(db) -> dict:
    created = []
    existing = []
    updated = []

    for role_data in REQUIRED_ROLES:
        role = db.query(Role).filter(Role.code == role_data["code"]).first()
        if not role:
            role = Role(
                code=role_data["code"],
                name=role_data["name"],
                description=role_data["description"],
            )
            db.add(role)
            created.append(role_data["code"])
            continue

        existing.append(role_data["code"])
        if not role.name:
            role.name = role_data["name"]
            updated.append(role_data["code"])
        if not role.description:
            role.description = role_data["description"]
            if role_data["code"] not in updated:
                updated.append(role_data["code"])

    db.commit()
    return {
        "created": created,
        "existing": existing,
        "updated": updated,
        "total_required": len(REQUIRED_ROLES),
    }


def _insert_game_with_schema_columns(db, room_code: str) -> Game:
    columns = {column["name"] for column in inspect(engine).get_columns("games")}
    insert_values = {
        "room_code": room_code,
        "title": GAME_TITLE,
        "template_code": None,
        "scenario_id": None,
        "scenario_code": SCENARIO_CODE,
    }
    insert_columns = [column for column in insert_values if column in columns]

    if "status" in columns:
        insert_columns.append("status")
        insert_values["status"] = "active"

    if "room_code" not in insert_columns or "title" not in insert_columns:
        raise BootstrapFailure("games table does not expose required room_code/title columns")

    placeholders = ", ".join(f":{column}" for column in insert_columns)
    db.execute(
        text(f"INSERT INTO games ({', '.join(insert_columns)}) VALUES ({placeholders})"),
        {column: insert_values[column] for column in insert_columns},
    )
    db.flush()
    return db.query(Game).filter(Game.room_code == room_code).first()


def _ensure_game(db) -> dict:
    game = db.query(Game).filter(Game.room_code == ROOM_CODE).first()
    created = False
    updated_fields = []

    if not game:
        game = _insert_game_with_schema_columns(db, ROOM_CODE)
        created = True

    if not game:
        raise BootstrapFailure(f"Failed to ensure game {ROOM_CODE}")

    if game.title != GAME_TITLE:
        game.title = GAME_TITLE
        updated_fields.append("title")

    db.commit()
    db.refresh(game)
    return {
        "created": created,
        "updated_fields": updated_fields,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
            "template_code": game.template_code,
            "scenario_code": getattr(game, "scenario_code", None),
            "scenario_id": getattr(game, "scenario_id", None),
        },
    }


def _require_ok(step: str, result: dict) -> dict:
    if not isinstance(result, dict) or not result.get("ok"):
        raise BootstrapFailure(f"{step} failed: {json.dumps(result, ensure_ascii=False, default=str)}")
    return result


def _import_template_bundle(db) -> dict:
    steps = [
        ("template_core", import_template_core_real_logic),
        ("template_map", import_template_map_real_logic),
        ("template_task_pools", import_template_task_pools_real_logic),
        ("template_rounds", import_template_rounds_real_logic),
    ]

    summary = {}
    for step_name, import_fn in steps:
        result = import_fn(
            db,
            template_code=TEMPLATE_CODE,
            game_templates_dir=GAME_TEMPLATES_DIR,
            load_yaml_file_fn=load_yaml_file,
            dump_json_fn=dump_json,
        )
        _require_ok(step_name, result)
        summary[step_name] = {
            "ok": True,
            "counts": result.get("imported_counts"),
            "nodes": result.get("imported_nodes_count"),
            "warnings_count": len(result.get("validation_warnings") or []),
        }

    return summary


def _import_scenario(db) -> dict:
    if not SCENARIO_PATH.exists():
        raise BootstrapFailure(f"Scenario file not found: {SCENARIO_PATH}")

    payload = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    payload["import_mode"] = "merge"
    result = import_scenario_logic(db, payload=payload, dump_json_fn=dump_json)
    _require_ok("scenario_import", result)

    scenario = result.get("scenario") or {}
    return {
        "ok": True,
        "code": scenario.get("code"),
        "rounds_count": scenario.get("rounds_count"),
        "questions_count": scenario.get("questions_count"),
        "imported_rounds": len(result.get("imported_round_codes") or []),
        "imported_questions": len(result.get("imported_question_codes") or []),
        "import_mode": result.get("import_mode"),
    }


def _apply_scenario(db) -> dict:
    result = apply_scenario_to_game_logic(
        db,
        room_code=ROOM_CODE,
        payload={
            "scenario_code": SCENARIO_CODE,
            "apply_mode": "merge",
        },
    )
    _require_ok("scenario_apply", result)

    game = result.get("game") or {}
    scenario = result.get("scenario") or {}
    return {
        "ok": True,
        "already_applied": result.get("already_applied"),
        "game": {
            "id": game.get("id"),
            "room_code": game.get("room_code"),
            "title": game.get("title"),
            "template_code": game.get("template_code"),
            "scenario_code": game.get("scenario_code"),
            "scenario_id": game.get("scenario_id"),
        },
        "scenario": {
            "code": scenario.get("code"),
            "rounds_count": scenario.get("rounds_count"),
            "questions_count": scenario.get("questions_count"),
        },
    }


def _verify_live01_ready(db) -> dict:
    game = db.query(Game).filter(Game.room_code == ROOM_CODE).first()
    scenario = db.query(GameScenarioTemplate).filter(GameScenarioTemplate.code == SCENARIO_CODE).first()

    if not game:
        raise BootstrapFailure(f"{ROOM_CODE} was not found after bootstrap")
    if not scenario:
        raise BootstrapFailure(f"{SCENARIO_CODE} was not found after bootstrap")
    if getattr(game, "scenario_code", None) != SCENARIO_CODE:
        raise BootstrapFailure(
            f"{ROOM_CODE} scenario_code is {getattr(game, 'scenario_code', None)!r}, expected {SCENARIO_CODE!r}"
        )

    return {
        "ok": True,
        "room_code": game.room_code,
        "scenario_code": game.scenario_code,
        "scenario_id": game.scenario_id,
        "scenario_template_id": scenario.id,
    }


def run_bootstrap() -> dict:
    _ensure_schema()

    db = SessionLocal()
    try:
        return {
            "ok": True,
            "database": _redacted_db_target(),
            "roles": _ensure_roles(db),
            "game": _ensure_game(db),
            "template": _import_template_bundle(db),
            "scenario": _import_scenario(db),
            "live01_link": _apply_scenario(db),
            "verification": _verify_live01_ready(db),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def main() -> int:
    _configure_stdio()
    try:
        summary = run_bootstrap()
    except Exception as exc:
        print("LIVE01 VPS BOOTSTRAP: FAIL")
        print(str(exc))
        return 1

    print("LIVE01 VPS BOOTSTRAP: PASS")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
