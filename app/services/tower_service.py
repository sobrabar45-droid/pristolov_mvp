from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.game_house_tower import GameHouseTower
from app.services.serialization_utils import dump_json, load_json_text


def ensure_tower_schema(engine):
    statements = [
        """
        CREATE TABLE IF NOT EXISTS game_house_towers (
            id SERIAL PRIMARY KEY,
            game_id INTEGER NOT NULL,
            house_id INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'draft',
            levels_count INTEGER NOT NULL DEFAULT 0,
            has_foundation BOOLEAN NOT NULL DEFAULT FALSE,
            unique_element_count INTEGER NOT NULL DEFAULT 0,
            blueprint_code VARCHAR NULL,
            blueprint_applied BOOLEAN NOT NULL DEFAULT FALSE,
            tower_score INTEGER NOT NULL DEFAULT 0,
            parts_json TEXT NULL,
            notes_json TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'draft'",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS levels_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS has_foundation BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS unique_element_count INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS blueprint_code VARCHAR NULL",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS blueprint_applied BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS tower_score INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS parts_json TEXT NULL",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS notes_json TEXT NULL",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE game_house_towers ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "CREATE INDEX IF NOT EXISTS ix_game_house_towers_game_id ON game_house_towers(game_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_house_towers_house_id ON game_house_towers(house_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_game_house_towers_game_house ON game_house_towers(game_id, house_id)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def get_or_create_house_tower(db: Session, game_id: int, house_id: int) -> GameHouseTower:
    tower = (
        db.query(GameHouseTower)
        .filter(
            GameHouseTower.game_id == game_id,
            GameHouseTower.house_id == house_id,
        )
        .first()
    )

    if tower:
        return tower

    tower = GameHouseTower(
        game_id=game_id,
        house_id=house_id,
        status="draft",
        levels_count=0,
        has_foundation=False,
        unique_element_count=0,
        blueprint_applied=False,
        tower_score=0,
        parts_json=dump_json([]),
        notes_json=dump_json({}),
    )
    db.add(tower)
    db.flush()
    return tower


def serialize_house_tower(tower: GameHouseTower) -> dict:
    return {
        "id": tower.id,
        "game_id": tower.game_id,
        "house_id": tower.house_id,
        "status": tower.status,
        "levels_count": tower.levels_count,
        "has_foundation": tower.has_foundation,
        "unique_element_count": tower.unique_element_count,
        "blueprint_code": tower.blueprint_code,
        "blueprint_applied": tower.blueprint_applied,
        "tower_score": tower.tower_score,
        "parts": load_json_text(tower.parts_json),
        "notes": load_json_text(tower.notes_json),
        "created_at": tower.created_at.isoformat() if tower.created_at else None,
        "updated_at": tower.updated_at.isoformat() if tower.updated_at else None,
    }


def recalculate_tower_score(tower: GameHouseTower) -> int:
    score = 0
    score += min(max(tower.levels_count or 0, 0), 5)

    if tower.has_foundation:
        score += 2

    if tower.blueprint_applied and tower.blueprint_code:
        score += 2

    if (tower.unique_element_count or 0) > 0:
        score += 1

    if score < 0:
        score = 0
    if score > 10:
        score = 10

    tower.tower_score = score
    tower.updated_at = datetime.now(timezone.utc)
    return score


def _append_part_note(tower: GameHouseTower, note: dict):
    parts = load_json_text(tower.parts_json)
    if not isinstance(parts, list):
        parts = []

    parts.append(note)
    tower.parts_json = dump_json(parts)


def add_tower_part(db: Session, game_id: int, house_id: int, payload: dict) -> dict:
    tower = get_or_create_house_tower(db, game_id, house_id)

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    part_type = payload.get("part_type")
    quantity = payload.get("quantity", 1)

    if part_type not in {"level", "foundation", "unique"}:
        return {
            "ok": False,
            "message": 'Поле "part_type" должно быть одним из: "level", "foundation", "unique"',
            "received_part_type": part_type,
        }

    if not isinstance(quantity, int) or quantity <= 0:
        return {
            "ok": False,
            "message": 'Поле "quantity" должно быть положительным целым числом',
            "received_quantity": quantity,
        }

    change_debug = {
        "part_type": part_type,
        "requested_quantity": quantity,
        "applied_quantity": 0,
        "before": {
            "levels_count": tower.levels_count,
            "has_foundation": tower.has_foundation,
            "unique_element_count": tower.unique_element_count,
            "tower_score": tower.tower_score,
        },
    }

    if part_type == "level":
        before = tower.levels_count or 0
        target = min(before + quantity, 5)
        applied_quantity = max(0, target - before)
        tower.levels_count = target
        change_debug["applied_quantity"] = applied_quantity
    elif part_type == "foundation":
        already_had_foundation = bool(tower.has_foundation)
        tower.has_foundation = True
        change_debug["applied_quantity"] = 0 if already_had_foundation else 1
    elif part_type == "unique":
        tower.unique_element_count = (tower.unique_element_count or 0) + quantity
        change_debug["applied_quantity"] = quantity

    tower.status = "building"
    _append_part_note(
        tower,
        {
            "action": "add_part",
            "part_type": part_type,
            "quantity": change_debug["applied_quantity"],
            "requested_quantity": quantity,
        },
    )
    recalculate_tower_score(tower)

    change_debug["after"] = {
        "levels_count": tower.levels_count,
        "has_foundation": tower.has_foundation,
        "unique_element_count": tower.unique_element_count,
        "tower_score": tower.tower_score,
    }

    db.flush()

    return {
        "ok": True,
        "message": "Часть башни добавлена",
        "tower": serialize_house_tower(tower),
        "applied_change": change_debug,
    }


def apply_tower_blueprint(db: Session, game_id: int, house_id: int, payload: dict) -> dict:
    tower = get_or_create_house_tower(db, game_id, house_id)

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    blueprint_code = payload.get("blueprint_code")
    apply_flag = payload.get("apply", True)

    if not isinstance(blueprint_code, str) or not blueprint_code.strip():
        return {
            "ok": False,
            "message": 'Поле "blueprint_code" должно быть непустой строкой',
            "received_blueprint_code": blueprint_code,
        }

    tower.blueprint_code = blueprint_code.strip()
    tower.blueprint_applied = bool(apply_flag and tower.blueprint_code)
    tower.status = "building"

    notes = load_json_text(tower.notes_json)
    if not isinstance(notes, dict):
        notes = {}
    notes["last_blueprint"] = tower.blueprint_code
    notes["blueprint_applied"] = tower.blueprint_applied
    tower.notes_json = dump_json(notes)

    recalculate_tower_score(tower)
    db.flush()

    return {
        "ok": True,
        "message": "Чертёж башни применён",
        "tower": serialize_house_tower(tower),
        "blueprint_debug": {
            "blueprint_code": tower.blueprint_code,
            "blueprint_applied": tower.blueprint_applied,
            "score_after": tower.tower_score,
        },
    }


def get_house_tower_payload(db: Session, game_id: int, house_id: int) -> dict:
    tower = get_or_create_house_tower(db, game_id, house_id)
    recalculate_tower_score(tower)
    db.flush()
    return {
        "ok": True,
        "tower": serialize_house_tower(tower),
    }
