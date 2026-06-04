#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import inspect, text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal, engine
from app.models import Game, GamePhase, House, Player, GameHostRound, GameAssignment
from app.services.phase_service import open_game_phase_logic


ROOM_A = "LIVE01"
ROOM_B = "LIVE02"
PROBE_PHASE_TYPE = "multi_room_smoke_probe"


class SmokeFailure(Exception):
    pass


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def ensure_game(db, room_code: str) -> Game:
    game = db.query(Game).filter(Game.room_code == room_code).first()
    if game:
        return game

    columns = {column["name"] for column in inspect(engine).get_columns("games")}
    insert_columns = ["room_code", "title", "template_code", "scenario_id", "scenario_code"]
    insert_values = {
        "room_code": room_code,
        "title": f"{room_code} Multi-room smoke",
        "template_code": None,
        "scenario_id": None,
        "scenario_code": None,
    }

    if "status" in columns:
        insert_columns.append("status")
        insert_values["status"] = "active"

    placeholders = ", ".join(f":{column}" for column in insert_columns)
    db.execute(
        text(f"INSERT INTO games ({', '.join(insert_columns)}) VALUES ({placeholders})"),
        insert_values,
    )
    db.flush()
    return db.query(Game).filter(Game.room_code == room_code).first()


def room_snapshot(db, game: Game) -> dict:
    active_phases = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.status == "active",
        )
        .order_by(GamePhase.id.asc())
        .all()
    )
    probe_phases = (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == PROBE_PHASE_TYPE,
        )
        .order_by(GamePhase.id.asc())
        .all()
    )
    return {
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
            "template_code": game.template_code,
            "scenario_code": game.scenario_code,
            "scenario_id": game.scenario_id,
        },
        "counts": {
            "houses": db.query(House).filter(House.game_id == game.id).count(),
            "players": db.query(Player).filter(Player.game_id == game.id).count(),
            "host_rounds": db.query(GameHostRound).filter(GameHostRound.game_id == game.id).count(),
            "assignments": db.query(GameAssignment).filter(GameAssignment.game_id == game.id).count(),
            "phases_total": db.query(GamePhase).filter(GamePhase.game_id == game.id).count(),
            "probe_phases_total": len(probe_phases),
        },
        "active_phases": [
            {
                "id": phase.id,
                "phase_type": phase.phase_type,
                "status": phase.status,
                "payload": phase.payload,
            }
            for phase in active_phases
        ],
        "latest_probe_phase": (
            {
                "id": probe_phases[-1].id,
                "status": probe_phases[-1].status,
                "opened_at": probe_phases[-1].opened_at.isoformat() if probe_phases[-1].opened_at else None,
                "closed_at": probe_phases[-1].closed_at.isoformat() if probe_phases[-1].closed_at else None,
            }
            if probe_phases
            else None
        ),
    }


def comparable_live02_snapshot(snapshot: dict) -> dict:
    return {
        "game": snapshot["game"],
        "counts": snapshot["counts"],
        "active_phases": snapshot["active_phases"],
        "latest_probe_phase": snapshot["latest_probe_phase"],
    }


def close_probe_phase(db, phase_id: int) -> None:
    phase = db.query(GamePhase).filter(GamePhase.id == phase_id).first()
    if not phase:
        return
    phase.status = "closed"
    phase.closed_at = datetime.now(timezone.utc)
    db.flush()


def main() -> int:
    summary = {
        "rooms": [ROOM_A, ROOM_B],
        "mutation": {
            "room_code": ROOM_A,
            "service": "open_game_phase_logic",
            "phase_type": PROBE_PHASE_TYPE,
        },
        "checks": [],
    }

    db = SessionLocal()
    created_probe_phase_id = None

    try:
        live01 = ensure_game(db, ROOM_A)
        live02 = ensure_game(db, ROOM_B)
        db.commit()
        db.refresh(live01)
        db.refresh(live02)
        summary["checks"].append("LIVE01 and LIVE02 exist")

        before_live01 = room_snapshot(db, live01)
        before_live02 = room_snapshot(db, live02)
        summary["before"] = {
            ROOM_A: before_live01,
            ROOM_B: before_live02,
        }

        active_probe = (
            db.query(GamePhase)
            .filter(
                GamePhase.game_id == live01.id,
                GamePhase.phase_type == PROBE_PHASE_TYPE,
                GamePhase.status == "active",
            )
            .first()
        )
        expect(active_probe is None, f"{ROOM_A} already has active {PROBE_PHASE_TYPE}; close it before rerun")

        open_result = open_game_phase_logic(db, ROOM_A, PROBE_PHASE_TYPE)
        expect(open_result.get("ok") is True, f"probe phase open failed: {open_result}")
        created_probe_phase_id = int((open_result.get("phase") or {}).get("id") or 0)
        expect(created_probe_phase_id > 0, f"probe phase id missing: {open_result}")
        db.commit()
        summary["checks"].append("LIVE01 probe phase opened")

        db.refresh(live01)
        db.refresh(live02)
        after_mutation_live01 = room_snapshot(db, live01)
        after_mutation_live02 = room_snapshot(db, live02)

        expect(
            after_mutation_live01["counts"]["probe_phases_total"] == before_live01["counts"]["probe_phases_total"] + 1,
            "LIVE01 probe phase count did not increase by exactly 1",
        )
        expect(
            any(phase["id"] == created_probe_phase_id for phase in after_mutation_live01["active_phases"]),
            "LIVE01 active phases do not include created probe phase",
        )
        expect(
            comparable_live02_snapshot(after_mutation_live02) == comparable_live02_snapshot(before_live02),
            "LIVE02 changed after LIVE01-only mutation",
        )
        summary["checks"].append("LIVE01 changed and LIVE02 stayed unchanged")

        close_probe_phase(db, created_probe_phase_id)
        db.commit()
        summary["checks"].append("LIVE01 probe phase closed")

        final_live01 = room_snapshot(db, live01)
        final_live02 = room_snapshot(db, live02)
        expect(
            final_live01["latest_probe_phase"]["status"] == "closed",
            "created LIVE01 probe phase was not closed",
        )
        expect(
            comparable_live02_snapshot(final_live02) == comparable_live02_snapshot(before_live02),
            "LIVE02 changed after probe cleanup",
        )
        summary["checks"].append("LIVE02 remained unchanged after cleanup")

        summary["after"] = {
            ROOM_A: final_live01,
            ROOM_B: final_live02,
        }
        print("MULTI ROOM ISOLATION SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    except Exception as exc:
        db.rollback()
        if created_probe_phase_id:
            try:
                close_probe_phase(db, created_probe_phase_id)
                db.commit()
            except Exception:
                db.rollback()
        print("MULTI ROOM ISOLATION SMOKE: FAIL")
        print(str(exc))
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
