#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: F401 - register SQLAlchemy model relationships
from app.database import SessionLocal
from app.models.game import Game
from app.models.game_scenario_template import GameScenarioTemplate
from app.models.house import House
from app.models.player import Player
from app.services.scenario_service import apply_scenario_to_game_logic, import_scenario_logic
from app.services.serialization_utils import dump_json


DEFAULT_SCENARIO = "season1_mvp_live_v2"
DEFAULT_PUBLIC_BASE_URL = "https://pristolov.ru"
ROOM_CODE_PATTERN = re.compile(r"^[A-Z0-9_]+$")
SCENARIOS_DIR = PROJECT_ROOT / "app" / "game_templates" / "scenarios"


class SetupError(Exception):
    pass


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def _normalize_room_code(value: str) -> str:
    return (value or "").strip().upper()


def _validate_room_code(room_code: str, *, allow_live01: bool) -> None:
    if not room_code:
        raise SetupError("room_code is required")
    if not ROOM_CODE_PATTERN.match(room_code):
        raise SetupError("room_code must use only uppercase Latin letters, numbers, and underscores")
    if room_code == "LIVE01" and not allow_live01:
        raise SetupError("Refusing LIVE01 without --allow-live01")


def _scenario_file_path(scenario_code: str) -> Path:
    return SCENARIOS_DIR / f"{scenario_code}.json"


def _load_scenario_payload(scenario_code: str) -> dict:
    path = _scenario_file_path(scenario_code)
    if not path.exists():
        raise SetupError(f"Scenario JSON not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SetupError(f"Scenario JSON must be an object: {path}")
    payload["import_mode"] = "merge"
    return payload


def _build_urls(room_code: str, *, base_url: str, registration_mode: str) -> dict:
    base = base_url.rstrip("/")
    return {
        "one_qr_registration": f"{base}/delegation/start?game_code={room_code}&entry_mode={registration_mode}",
        "master": f"{base}/dev/master-screen/{room_code}",
        "game_master": f"{base}/dev/game-master/{room_code}",
        "tv": f"{base}/dev/tv-mode/{room_code}",
        "cashier": f"{base}/cashier/gold-desk/{room_code}",
        "dev_gold": f"{base}/dev/gold-desk/{room_code}",
        "treasurer_shop": f"{base}/dev/treasurer-shop/{room_code}",
        "player_registration": f"{base}/game/{room_code}",
    }


def _game_summary(db, game: Game | None) -> dict | None:
    if not game:
        return None
    houses_count = db.query(House).filter(House.game_id == game.id).count()
    players_count = db.query(Player).filter(Player.game_id == game.id).count()
    return {
        "id": game.id,
        "room_code": game.room_code,
        "title": game.title,
        "template_code": game.template_code,
        "scenario_code": getattr(game, "scenario_code", None),
        "scenario_id": getattr(game, "scenario_id", None),
        "houses_count": houses_count,
        "players_count": players_count,
    }


def _ensure_scenario_template(db, *, scenario_code: str, dry_run: bool) -> dict:
    scenario = db.query(GameScenarioTemplate).filter(GameScenarioTemplate.code == scenario_code).first()
    if scenario:
        return {
            "status": "exists",
            "code": scenario.code,
            "id": scenario.id,
            "rounds_count": len(scenario.rounds or []),
        }

    path = _scenario_file_path(scenario_code)
    if dry_run:
        return {
            "status": "would_import" if path.exists() else "missing",
            "code": scenario_code,
            "path": str(path),
        }

    payload = _load_scenario_payload(scenario_code)
    result = import_scenario_logic(db, payload=payload, dump_json_fn=dump_json)
    if not result.get("ok"):
        raise SetupError(f"Scenario import failed: {result.get('message') or result}")

    scenario_data = result.get("scenario") or {}
    return {
        "status": "imported",
        "code": scenario_data.get("code"),
        "id": scenario_data.get("id"),
        "rounds_count": scenario_data.get("rounds_count"),
        "questions_count": scenario_data.get("questions_count"),
    }


def _create_game(db, *, room_code: str, title: str, scenario_code: str, dry_run: bool) -> tuple[Game | None, dict]:
    if dry_run:
        return None, {
            "status": "would_create",
            "room_code": room_code,
            "title": title,
            "scenario_code": scenario_code,
        }

    game = Game(
        room_code=room_code,
        title=title,
        template_code=None,
        scenario_code=None,
        scenario_id=None,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return game, {
        "status": "created",
        "id": game.id,
        "room_code": game.room_code,
        "title": game.title,
    }


def _apply_scenario(db, *, game: Game, scenario_code: str, dry_run: bool) -> dict:
    current_scenario = getattr(game, "scenario_code", None)
    if current_scenario == scenario_code:
        return {
            "status": "already_applied",
            "scenario_code": scenario_code,
        }
    if current_scenario and current_scenario != scenario_code:
        raise SetupError(
            f"Room already has scenario {current_scenario!r}; refusing to replace it in MVP helper"
        )
    if dry_run:
        return {
            "status": "would_apply",
            "scenario_code": scenario_code,
        }

    result = apply_scenario_to_game_logic(
        db,
        room_code=game.room_code,
        payload={
            "scenario_code": scenario_code,
            "apply_mode": "merge",
        },
    )
    if not result.get("ok"):
        raise SetupError(f"Scenario apply failed: {result.get('message') or result}")

    applied_game = result.get("game") or {}
    return {
        "status": "applied",
        "scenario_code": applied_game.get("scenario_code") or scenario_code,
        "scenario_id": applied_game.get("scenario_id"),
        "already_applied": result.get("already_applied"),
    }


def setup_room(args: argparse.Namespace) -> dict:
    room_code = _normalize_room_code(args.room_code)
    _validate_room_code(room_code, allow_live01=args.allow_live01)

    scenario_code = (args.scenario or DEFAULT_SCENARIO).strip()
    title = args.title or f"PRISTOLOV {room_code}"
    urls = _build_urls(room_code, base_url=args.public_base_url, registration_mode=args.registration_mode)

    db = SessionLocal()
    try:
        existing_game = db.query(Game).filter(Game.room_code == room_code).first()
        existing_summary = _game_summary(db, existing_game)

        if existing_game and not args.force:
            return {
                "ok": True,
                "status": "exists_no_changes",
                "message": "Room already exists. Re-run with --force to complete missing safe setup steps.",
                "room": existing_summary,
                "scenario": {"requested": scenario_code},
                "urls": urls if args.print_urls else {},
                "next_manual_step": "Review room summary before making changes.",
            }

        scenario_summary = _ensure_scenario_template(db, scenario_code=scenario_code, dry_run=args.dry_run)

        created_game = None
        create_summary = {"status": "exists", "room": existing_summary}
        if not existing_game:
            created_game, create_summary = _create_game(
                db,
                room_code=room_code,
                title=title,
                scenario_code=scenario_code,
                dry_run=args.dry_run,
            )
            game = created_game
        else:
            game = existing_game

        apply_summary = {"status": "skipped_dry_run_no_game"}
        if args.dry_run and not game:
            apply_summary = {"status": "would_apply", "scenario_code": scenario_code}
        elif game:
            apply_summary = _apply_scenario(db, game=game, scenario_code=scenario_code, dry_run=args.dry_run)
            if not args.dry_run:
                db.refresh(game)

        final_game = game if game else existing_game
        final_summary = _game_summary(db, final_game) if final_game else None

        return {
            "ok": True,
            "status": "dry_run" if args.dry_run else "ready",
            "room_code": room_code,
            "room": final_summary or create_summary,
            "scenario": scenario_summary,
            "scenario_apply": apply_summary,
            "registration": {
                "mode": args.registration_mode,
                "starting_gold_policy": args.starting_gold_policy,
                "current_policy_summary": "manual=10, random=11",
            },
            "smoke": {
                "room_exists": bool(final_summary) if not args.dry_run else "would_create",
                "scenario_applied": (
                    bool(final_summary and final_summary.get("scenario_code") == scenario_code)
                    if not args.dry_run
                    else "would_apply"
                ),
                "players_count": final_summary.get("players_count") if final_summary else 0,
                "houses_count": final_summary.get("houses_count") if final_summary else 0,
                "urls_generated": True,
            },
            "urls": urls if args.print_urls else {},
            "next_manual_step": "Open One QR registration only after operator confirms room_code and URLs.",
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or safely complete a PRISTOLOV room setup without players or destructive reset."
    )
    parser.add_argument("--room-code", required=True, help="Room code, uppercase Latin/numbers/underscore, e.g. KURGAN02")
    parser.add_argument("--title", default=None, help="Room title. Defaults to PRISTOLOV {room_code}.")
    parser.add_argument("--scenario", default=DEFAULT_SCENARIO, help=f"Scenario code. Default: {DEFAULT_SCENARIO}.")
    parser.add_argument("--registration-mode", choices=["random", "quiz"], default="random")
    parser.add_argument("--starting-gold-policy", default="current", help="Label only for MVP summary. Default: current.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned actions without writing DB changes.")
    parser.add_argument("--force", action="store_true", help="For existing rooms, complete safe missing setup only.")
    parser.add_argument("--allow-live01", action="store_true", help="Allow LIVE01. Refused by default.")
    parser.add_argument("--public-base-url", default=DEFAULT_PUBLIC_BASE_URL, help="Base URL used for printed links.")
    parser.add_argument("--no-print-urls", action="store_false", dest="print_urls", help="Do not include URLs in output.")
    parser.set_defaults(print_urls=True)
    return parser


def main() -> int:
    _configure_stdio()
    parser = build_parser()
    args = parser.parse_args()

    try:
        result = setup_room(args)
    except SetupError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    except Exception as exc:
        print(json.dumps({"ok": False, "error": f"Unexpected failure: {exc}"}, ensure_ascii=False, indent=2))
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
