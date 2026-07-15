from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.game_deal import GameDeal
from app.models.game_duel import GameDuel
from app.models.house import House
from app.services.gold_service import resolve_pvp_gold
from app.services.phase_service import has_active_phase
from app.services.resource_service import apply_house_effect
from app.services.serialization_utils import dump_json, load_json_text
from app.services.tower_service import get_or_create_house_tower, recalculate_tower_score


DUEL_PHASE_TYPE = "duel"
DUEL_STAKE_GOLD = 3
BRAAVOS_BANK_PROTECTION_GOLD_THRESHOLD = 4
DUEL_REFUSE_INFLUENCE_TRANSFER = 1
DUEL_RESOLVE_INFLUENCE_TRANSFER = 1
DUEL_WINNER_INFLUENCE_BONUS = 1
DUEL_TOWER_BONUS_INFLUENCE = 1
DUEL_ALLOWED_STATUSES = {"challenged", "accepted", "refused", "resolved", "canceled", "needs_replay"}


def _normalize_duel_stake_gold(payload: dict | None) -> int:
    raw_value = payload.get("stake_gold") if isinstance(payload, dict) else None
    if raw_value in (None, ""):
        return DUEL_STAKE_GOLD

    try:
        stake_gold = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid stake_gold") from exc

    if stake_gold <= 0:
        raise ValueError("invalid stake_gold")

    return stake_gold


def ensure_duel_schema(engine):
    statements = [
        """
        CREATE TABLE IF NOT EXISTS game_duels (
            id SERIAL PRIMARY KEY,
            game_id INTEGER NOT NULL,
            challenger_house_id INTEGER NOT NULL,
            target_house_id INTEGER NOT NULL,
            status VARCHAR NOT NULL DEFAULT 'challenged',
            stake_gold INTEGER NOT NULL DEFAULT 3,
            winner_house_id INTEGER NULL,
            refused_at TIMESTAMPTZ NULL,
            resolved_at TIMESTAMPTZ NULL,
            notes_json TEXT NULL,
            challenger_tower_bonus VARCHAR NULL,
            target_tower_bonus VARCHAR NULL,
            duel_advantage_side VARCHAR NULL,
            duel_advantage_class VARCHAR NULL,
            duel_advantage_payload_json TEXT NULL,
            duel_format VARCHAR NULL,
            live_bonus_side VARCHAR NULL,
            live_bonus_code VARCHAR NULL,
            live_bonus_label VARCHAR NULL,
            live_bonus_host_text TEXT NULL,
            live_bonus_tv_text TEXT NULL,
            live_bonus_payload_json TEXT NULL,
            influence_transfer_amount INTEGER NOT NULL DEFAULT 0,
            bonus_payload_json TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS status VARCHAR NOT NULL DEFAULT 'challenged'",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS stake_gold INTEGER NOT NULL DEFAULT 3",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS winner_house_id INTEGER NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS refused_at TIMESTAMPTZ NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS notes_json TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS challenger_tower_bonus VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS target_tower_bonus VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS duel_advantage_side VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS duel_advantage_class VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS duel_advantage_payload_json TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS duel_format VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_side VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_code VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_label VARCHAR NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_host_text TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_tv_text TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS live_bonus_payload_json TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS influence_transfer_amount INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS bonus_payload_json TEXT NULL",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "ALTER TABLE game_duels ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()",
        "CREATE INDEX IF NOT EXISTS ix_game_duels_game_id ON game_duels(game_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_duels_challenger_house_id ON game_duels(challenger_house_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_duels_target_house_id ON game_duels(target_house_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_duels_winner_house_id ON game_duels(winner_house_id)",
        "CREATE INDEX IF NOT EXISTS ix_game_duels_status ON game_duels(status)",
    ]

    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def _touch_duel(duel: GameDuel):
    duel.updated_at = datetime.now(timezone.utc)


def _append_note(duel: GameDuel, key: str, value):
    notes = load_json_text(duel.notes_json)
    if not isinstance(notes, dict):
        notes = {}
    notes[key] = value
    duel.notes_json = dump_json(notes)


def _ensure_duel_phase_active(db: Session, game_id: int):
    if has_active_phase(db, game_id, DUEL_PHASE_TYPE):
        return {
            "ok": True,
        }

    return {
        "ok": False,
        "message": 'Фаза "duel" не активна',
        "phase_type": DUEL_PHASE_TYPE,
    }


def serialize_duel(duel: GameDuel) -> dict:
    notes = load_json_text(duel.notes_json)
    if not isinstance(notes, dict):
        notes = {}

    resolve_debug = notes.get("resolve_debug")
    tower_advantage_debug = resolve_debug.get("tower_advantage") if isinstance(resolve_debug, dict) else None

    return {
        "id": duel.id,
        "game_id": duel.game_id,
        "challenger_house_id": duel.challenger_house_id,
        "target_house_id": duel.target_house_id,
        "status": duel.status,
        "stake_gold": duel.stake_gold,
        "winner_house_id": duel.winner_house_id,
        "refused_at": duel.refused_at.isoformat() if duel.refused_at else None,
        "resolved_at": duel.resolved_at.isoformat() if duel.resolved_at else None,
        "notes": load_json_text(duel.notes_json),
        "challenger_tower_bonus": duel.challenger_tower_bonus,
        "target_tower_bonus": duel.target_tower_bonus,
        "duel_advantage_side": duel.duel_advantage_side,
        "duel_advantage_class": duel.duel_advantage_class,
        "duel_advantage_payload": load_json_text(duel.duel_advantage_payload_json),
        "duel_format": duel.duel_format,
        "live_bonus_side": duel.live_bonus_side,
        "live_bonus_code": duel.live_bonus_code,
        "live_bonus_label": duel.live_bonus_label,
        "live_bonus_host_text": duel.live_bonus_host_text,
        "live_bonus_tv_text": duel.live_bonus_tv_text,
        "live_bonus_payload": load_json_text(duel.live_bonus_payload_json),
        "influence_transfer_amount": duel.influence_transfer_amount,
        "bonus_payload": load_json_text(duel.bonus_payload_json),
        "tower_bonus_applied": bool(
            isinstance(tower_advantage_debug, dict) and tower_advantage_debug.get("extra_influence_applied", 0) > 0
        ),
        "tower_bonus_effect_debug": tower_advantage_debug,
        "created_at": duel.created_at.isoformat() if duel.created_at else None,
        "updated_at": duel.updated_at.isoformat() if duel.updated_at else None,
        "challenger_house": {
            "id": duel.challenger_house.id,
            "house_key": duel.challenger_house.house_key,
            "name": duel.challenger_house.name,
            "gold": duel.challenger_house.resource_gold,
            "influence": duel.challenger_house.resource_influence,
        } if duel.challenger_house else None,
        "target_house": {
            "id": duel.target_house.id,
            "house_key": duel.target_house.house_key,
            "name": duel.target_house.name,
            "gold": duel.target_house.resource_gold,
            "influence": duel.target_house.resource_influence,
        } if duel.target_house else None,
        "winner_house": {
            "id": duel.winner_house.id,
            "house_key": duel.winner_house.house_key,
            "name": duel.winner_house.name,
        } if duel.winner_house else None,
    }


def get_house_duel_protection_status(db: Session, house_id: int) -> dict:
    house = (
        db.query(House)
        .filter(House.id == house_id)
        .first()
    )

    if not house:
        return {
            "ok": False,
            "message": "Дом не найден",
            "house_id": house_id,
        }

    gold = int(house.resource_gold or 0)
    protected = gold < BRAAVOS_BANK_PROTECTION_GOLD_THRESHOLD

    return {
        "ok": True,
        "house_id": house.id,
        "gold": gold,
        "threshold": BRAAVOS_BANK_PROTECTION_GOLD_THRESHOLD,
        "protected_by_braavos_bank": protected,
        "message": "Дом под защитой Железного банка Бравоса" if protected else "Защита Банка Бравоса не активна",
    }


def are_houses_official_allies(db: Session, house_a_id: int, house_b_id: int) -> bool:
    if not house_a_id or not house_b_id:
        return False

    deal = (
        db.query(GameDeal.id)
        .filter(
            GameDeal.status == "alliance_active",
            (
                ((GameDeal.from_house_id == house_a_id) & (GameDeal.to_house_id == house_b_id))
                | ((GameDeal.from_house_id == house_b_id) & (GameDeal.to_house_id == house_a_id))
            ),
        )
        .first()
    )
    return bool(deal)


def get_house_tower_bonus_class(db: Session, game_id: int, house_id: int) -> str:
    tower = get_or_create_house_tower(db, game_id, house_id)
    score = recalculate_tower_score(tower)

    if score <= 2:
        return "none"
    if score <= 5:
        return "minor"
    if score <= 8:
        return "strong"
    return "dominant"


def get_tower_bonus_rank(bonus_class: str) -> int:
    ranks = {
        "none": 0,
        "minor": 1,
        "strong": 2,
        "dominant": 3,
    }
    return ranks.get(str(bonus_class or "").strip(), 0)


def calculate_duel_advantage(challenger_bonus: str, target_bonus: str) -> dict:
    challenger_rank = get_tower_bonus_rank(challenger_bonus)
    target_rank = get_tower_bonus_rank(target_bonus)
    diff = challenger_rank - target_rank

    if diff == 0:
        advantage_side = None
        advantage_class = "no_advantage"
    else:
        advantage_side = "challenger" if diff > 0 else "target"
        abs_diff = abs(diff)
        if abs_diff == 1:
            advantage_class = "minor_advantage"
        elif abs_diff == 2:
            advantage_class = "strong_advantage"
        else:
            advantage_class = "dominant_advantage"

    return {
        "side": advantage_side,
        "class": advantage_class,
        "payload": {
            "challenger_tower_bonus": challenger_bonus,
            "target_tower_bonus": target_bonus,
            "diff": diff,
        },
    }


def apply_duel_advantage_bonus(db: Session, duel: GameDuel, winner_house_id: int) -> dict:
    advantage_side = duel.duel_advantage_side
    advantage_class = duel.duel_advantage_class or "no_advantage"
    winner_matched_advantage = (
        (advantage_side == "challenger" and winner_house_id == duel.challenger_house_id)
        or (advantage_side == "target" and winner_house_id == duel.target_house_id)
    )

    extra_influence_applied = 0
    right_to_error = False
    tower_bonus_applied = False
    winner_effect = None

    if winner_matched_advantage and advantage_class in {"strong_advantage", "dominant_advantage"}:
        winner_house = duel.challenger_house if winner_house_id == duel.challenger_house_id else duel.target_house
        winner_effect = apply_house_effect(
            db=db,
            house=winner_house,
            effect_data={"influence": DUEL_TOWER_BONUS_INFLUENCE},
        )
        extra_influence_applied = DUEL_TOWER_BONUS_INFLUENCE
        tower_bonus_applied = True

        if advantage_class == "dominant_advantage":
            right_to_error = True

    return {
        "advantage_side": advantage_side,
        "advantage_class": advantage_class,
        "winner_matched_advantage": winner_matched_advantage,
        "extra_influence_applied": extra_influence_applied,
        "right_to_error": right_to_error,
        "tower_bonus_applied": tower_bonus_applied,
        "winner_effect": winner_effect,
    }


def get_default_duel_format() -> str:
    return "tic_tac_toe"


def normalize_duel_format(duel_format: str) -> str:
    normalized = str(duel_format or "").strip().lower()
    if normalized in {"tic_tac_toe", "drunken_checkers"}:
        return normalized
    return get_default_duel_format()


def build_live_duel_bonus(
    duel_format,
    duel_advantage_side,
    duel_advantage_class,
    challenger_house_name,
    target_house_name,
) -> dict:
    normalized_format = normalize_duel_format(duel_format)
    if duel_advantage_class == "no_advantage" or not duel_advantage_side:
        return {
            "live_bonus_side": None,
            "live_bonus_code": None,
            "live_bonus_label": None,
            "live_bonus_host_text": None,
            "live_bonus_tv_text": None,
            "live_bonus_payload": {
                "duel_format": normalized_format,
                "duel_advantage_class": duel_advantage_class,
                "mapped_from": "no_advantage",
                "house_name": None,
            },
        }

    house_name = challenger_house_name if duel_advantage_side == "challenger" else target_house_name

    mapping = {
        "tic_tac_toe": {
            "minor_advantage": {
                "code": "first_move",
                "label": "Первый ход",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Они делают первый ход.",
                "tv_text": "Преимущество Башни: первый ход",
            },
            "strong_advantage": {
                "code": "first_move_plus_one_correction",
                "label": "Первый ход и 1 коррекция",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Они ходят первыми и один раз за дуэль могут сразу скорректировать свой ход.",
                "tv_text": "Преимущество Башни: первый ход + 1 коррекция",
            },
            "dominant_advantage": {
                "code": "first_move_plus_right_to_error",
                "label": "Первый ход и право на ошибку",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Они ходят первыми и один раз за дуэль имеют право отменить неудачный ход.",
                "tv_text": "Преимущество Башни: первый ход + право на ошибку",
            },
        },
        "drunken_checkers": {
            "minor_advantage": {
                "code": "first_move",
                "label": "Первый ход",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Они открывают дуэль первым ходом.",
                "tv_text": "Преимущество Башни: первый ход",
            },
            "strong_advantage": {
                "code": "enhanced_piece",
                "label": "1 усиленная фигура",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Одна их фигура считается усиленной.",
                "tv_text": "Преимущество Башни: 1 усиленная фигура",
            },
            "dominant_advantage": {
                "code": "enhanced_piece_plus_right_to_error",
                "label": "Усиленная фигура и право на ошибку",
                "host_text": "Преимущество Башни у {HOUSE_NAME}. Одна их фигура усилена, и один раз за дуэль они могут отменить ошибочное действие.",
                "tv_text": "Преимущество Башни: усиленная фигура + право на ошибку",
            },
        },
    }

    item = mapping.get(normalized_format, {}).get(duel_advantage_class)
    if not item:
        return {
            "live_bonus_side": None,
            "live_bonus_code": None,
            "live_bonus_label": None,
            "live_bonus_host_text": None,
            "live_bonus_tv_text": None,
            "live_bonus_payload": {
                "duel_format": normalized_format,
                "duel_advantage_class": duel_advantage_class,
                "mapped_from": "unsupported_mapping",
                "house_name": house_name,
            },
        }

    return {
        "live_bonus_side": duel_advantage_side,
        "live_bonus_code": item["code"],
        "live_bonus_label": item["label"],
        "live_bonus_host_text": item["host_text"].replace("{HOUSE_NAME}", house_name),
        "live_bonus_tv_text": item["tv_text"],
        "live_bonus_payload": {
            "duel_format": normalized_format,
            "duel_advantage_class": duel_advantage_class,
            "mapped_from": duel_advantage_class,
            "house_name": house_name,
        },
    }


def create_duel_challenge(db: Session, game_id: int, challenger_house_id: int, target_house_id: int, payload: dict) -> dict:
    phase_guard = _ensure_duel_phase_active(db, game_id)
    if not phase_guard.get("ok"):
        return phase_guard

    if challenger_house_id == target_house_id:
        return {
            "ok": False,
            "message": "Нельзя бросить вызов своему Дому",
        }

    challenger_house = (
        db.query(House)
        .filter(
            House.id == challenger_house_id,
            House.game_id == game_id,
        )
        .first()
    )
    target_house = (
        db.query(House)
        .filter(
            House.id == target_house_id,
            House.game_id == game_id,
        )
        .first()
    )

    if not challenger_house or not target_house:
        return {
            "ok": False,
            "message": "Один или оба Дома не найдены в этой игре",
            "challenger_house_id": challenger_house_id,
            "target_house_id": target_house_id,
        }

    if are_houses_official_allies(db, challenger_house.id, target_house.id):
        return {
            "ok": False,
            "message": "Нельзя вызвать союзный Дом",
        }

    existing_active_duel = (
        db.query(GameDuel)
        .filter(
            GameDuel.game_id == game_id,
            GameDuel.status.in_(["challenged", "accepted", "needs_replay"]),
            (
                (
                    (GameDuel.challenger_house_id == challenger_house.id)
                    & (GameDuel.target_house_id == target_house.id)
                )
                | (
                    (GameDuel.challenger_house_id == target_house.id)
                    & (GameDuel.target_house_id == challenger_house.id)
                )
            ),
        )
        .order_by(GameDuel.id.desc())
        .first()
    )
    if existing_active_duel:
        return {
            "ok": False,
            "message": "Между этими Домами уже есть активная дуэль",
            "duel": serialize_duel(existing_active_duel),
        }

    try:
        stake_gold = _normalize_duel_stake_gold(payload)
    except ValueError:
        return {
            "ok": False,
            "message": "Ставка дуэли должна быть целым положительным числом",
            "stake_gold": payload.get("stake_gold") if isinstance(payload, dict) else None,
        }

    target_protection = get_house_duel_protection_status(db, target_house.id)
    if target_protection.get("protected_by_braavos_bank"):
        return {
            "ok": False,
            "message": "Дом под защитой Железного банка Бравоса",
            "protection": target_protection,
        }

    if int(challenger_house.resource_gold or 0) < stake_gold:
        return {
            "ok": False,
            "message": "У вызывающего Дома недостаточно золота для ставки",
            "required_gold": stake_gold,
            "current_gold": challenger_house.resource_gold,
        }

    if int(target_house.resource_gold or 0) < stake_gold:
        return {
            "ok": False,
            "message": "У Дома-цели недостаточно золота для ставки",
            "required_gold": stake_gold,
            "current_gold": target_house.resource_gold,
        }

    challenger_tower_bonus = get_house_tower_bonus_class(db, game_id, challenger_house.id)
    target_tower_bonus = get_house_tower_bonus_class(db, game_id, target_house.id)
    duel_advantage = calculate_duel_advantage(
        challenger_bonus=challenger_tower_bonus,
        target_bonus=target_tower_bonus,
    )
    duel_format = normalize_duel_format(payload.get("duel_format") if isinstance(payload, dict) else None)
    live_bonus = build_live_duel_bonus(
        duel_format=duel_format,
        duel_advantage_side=duel_advantage["side"],
        duel_advantage_class=duel_advantage["class"],
        challenger_house_name=challenger_house.name,
        target_house_name=target_house.name,
    )

    duel = GameDuel(
        game_id=game_id,
        challenger_house_id=challenger_house.id,
        target_house_id=target_house.id,
        status="challenged",
        stake_gold=stake_gold,
        challenger_tower_bonus=challenger_tower_bonus,
        target_tower_bonus=target_tower_bonus,
        duel_advantage_side=duel_advantage["side"],
        duel_advantage_class=duel_advantage["class"],
        duel_advantage_payload_json=dump_json(duel_advantage["payload"]),
        duel_format=duel_format,
        live_bonus_side=live_bonus["live_bonus_side"],
        live_bonus_code=live_bonus["live_bonus_code"],
        live_bonus_label=live_bonus["live_bonus_label"],
        live_bonus_host_text=live_bonus["live_bonus_host_text"],
        live_bonus_tv_text=live_bonus["live_bonus_tv_text"],
        live_bonus_payload_json=dump_json(live_bonus["live_bonus_payload"]),
        notes_json=dump_json({
            "challenge_note": payload.get("note") if isinstance(payload, dict) else None,
            "tower_advantage": {
                "advantage_side": duel_advantage["side"],
                "advantage_class": duel_advantage["class"],
                "payload": duel_advantage["payload"],
            },
            "live_bonus": {
                "side": live_bonus["live_bonus_side"],
                "code": live_bonus["live_bonus_code"],
                "label": live_bonus["live_bonus_label"],
                "host_text": live_bonus["live_bonus_host_text"],
                "tv_text": live_bonus["live_bonus_tv_text"],
                "payload": live_bonus["live_bonus_payload"],
            },
        }),
    )
    db.add(duel)
    db.flush()

    return {
        "ok": True,
        "message": "Вызов на дуэль зарегистрирован",
        "duel": serialize_duel(duel),
        "tower_bonus_applied": False,
        "tower_bonus_effect_debug": {
            "advantage_side": duel.duel_advantage_side,
            "advantage_class": duel.duel_advantage_class,
            "winner_matched_advantage": False,
            "extra_influence_applied": 0,
            "right_to_error": False,
        },
    }


def accept_duel(db: Session, duel: GameDuel, payload: dict) -> dict:
    phase_guard = _ensure_duel_phase_active(db, duel.game_id)
    if not phase_guard.get("ok"):
        return phase_guard

    if duel.status != "challenged":
        return {
            "ok": False,
            "message": f'Дуэль нельзя принять в статусе "{duel.status}"',
            "duel": serialize_duel(duel),
        }

    duel.status = "accepted"
    _append_note(duel, "accept_note", payload.get("note") if isinstance(payload, dict) else None)
    _touch_duel(duel)
    db.flush()

    return {
        "ok": True,
        "message": "Вызов на дуэль принят",
        "duel": serialize_duel(duel),
    }


def refuse_duel(db: Session, duel: GameDuel, payload: dict) -> dict:
    phase_guard = _ensure_duel_phase_active(db, duel.game_id)
    if not phase_guard.get("ok"):
        return phase_guard

    if duel.status != "challenged":
        return {
            "ok": False,
            "message": f'Отказ невозможен для дуэли в статусе "{duel.status}"',
            "duel": serialize_duel(duel),
        }

    target_house = duel.target_house
    challenger_house = duel.challenger_house

    target_effect = apply_house_effect(
        db=db,
        house=target_house,
        effect_data={"influence": -DUEL_REFUSE_INFLUENCE_TRANSFER},
    )
    challenger_effect = apply_house_effect(
        db=db,
        house=challenger_house,
        effect_data={"influence": DUEL_REFUSE_INFLUENCE_TRANSFER},
    )

    duel.status = "refused"
    duel.refused_at = datetime.now(timezone.utc)
    duel.influence_transfer_amount = DUEL_REFUSE_INFLUENCE_TRANSFER
    _append_note(
        duel,
        "refuse_debug",
        {
            "note": payload.get("note") if isinstance(payload, dict) else None,
            "target_effect": target_effect,
            "challenger_effect": challenger_effect,
        },
    )
    _touch_duel(duel)
    db.flush()

    return {
        "ok": True,
        "message": "Вызов на дуэль отклонён",
        "duel": serialize_duel(duel),
        "refuse_debug": {
            "influence_transfer_amount": DUEL_REFUSE_INFLUENCE_TRANSFER,
            "target_effect": target_effect,
            "challenger_effect": challenger_effect,
        },
    }


def mark_duel_needs_replay(db: Session, duel: GameDuel, payload: dict) -> dict:
    phase_guard = _ensure_duel_phase_active(db, duel.game_id)
    if not phase_guard.get("ok"):
        return phase_guard

    if duel.status not in {"challenged", "accepted"}:
        return {
            "ok": False,
            "message": f'Ничью нельзя отметить для дуэли в статусе "{duel.status}"',
            "duel": serialize_duel(duel),
        }

    duel.status = "needs_replay"
    duel.winner_house_id = None
    _append_note(
        duel,
        "draw_debug",
        {
            "note": payload.get("note") if isinstance(payload, dict) else None,
            "marked_at": datetime.now(timezone.utc).isoformat(),
            "reward_applied": False,
            "requires": "replay_or_host_tiebreak",
        },
    )
    _touch_duel(duel)
    db.flush()

    return {
        "ok": True,
        "message": "Дуэль завершилась ничьей. Нужна переигровка или решение ведущего.",
        "duel": serialize_duel(duel),
        "reward_applied": False,
    }


def resolve_duel(db: Session, duel: GameDuel, payload: dict) -> dict:
    if duel.status != "needs_replay":
        phase_guard = _ensure_duel_phase_active(db, duel.game_id)
        if not phase_guard.get("ok"):
            return phase_guard

    if duel.status not in {"challenged", "accepted", "needs_replay"}:
        return {
            "ok": False,
            "message": f'Разрешение невозможно для дуэли в статусе "{duel.status}"',
            "duel": serialize_duel(duel),
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    winner_house_id = payload.get("winner_house_id")
    if winner_house_id not in {duel.challenger_house_id, duel.target_house_id}:
        return {
            "ok": False,
            "message": "Победитель дуэли должен быть одной из двух сторон",
            "winner_house_id": winner_house_id,
        }

    winner_house = duel.challenger_house if duel.challenger_house_id == winner_house_id else duel.target_house
    loser_house = duel.target_house if winner_house.id == duel.challenger_house_id else duel.challenger_house
    stake_gold = int(duel.stake_gold or DUEL_STAKE_GOLD)

    if int(duel.challenger_house.resource_gold or 0) < stake_gold:
        return {
            "ok": False,
            "message": "У вызывающего Дома недостаточно золота для финальной ставки",
            "required_gold": stake_gold,
            "current_gold": duel.challenger_house.resource_gold,
            "duel": serialize_duel(duel),
        }

    if int(duel.target_house.resource_gold or 0) < stake_gold:
        return {
            "ok": False,
            "message": "У Дома-соперника недостаточно золота для финальной ставки",
            "required_gold": stake_gold,
            "current_gold": duel.target_house.resource_gold,
            "duel": serialize_duel(duel),
        }

    gold_result = resolve_pvp_gold(
        db=db,
        house_a=duel.challenger_house,
        house_b=duel.target_house,
        winner_house=winner_house,
        duel_id=duel.id,
        stake_gold=stake_gold,
    )

    loser_effect = apply_house_effect(
        db=db,
        house=loser_house,
        effect_data={"influence": -DUEL_RESOLVE_INFLUENCE_TRANSFER},
    )
    winner_transfer_effect = apply_house_effect(
        db=db,
        house=winner_house,
        effect_data={"influence": DUEL_RESOLVE_INFLUENCE_TRANSFER},
    )
    winner_bonus_effect = apply_house_effect(
        db=db,
        house=winner_house,
        effect_data={"influence": DUEL_WINNER_INFLUENCE_BONUS},
    )
    tower_advantage_effect = apply_duel_advantage_bonus(
        db=db,
        duel=duel,
        winner_house_id=winner_house.id,
    )

    duel.status = "resolved"
    duel.resolved_at = datetime.now(timezone.utc)
    duel.winner_house_id = winner_house.id
    duel.influence_transfer_amount = DUEL_RESOLVE_INFLUENCE_TRANSFER
    duel.bonus_payload_json = dump_json({
        "influence_bonus": DUEL_WINNER_INFLUENCE_BONUS,
        "tower_advantage_class": duel.duel_advantage_class or "no_advantage",
        "tower_bonus_applied": tower_advantage_effect["tower_bonus_applied"],
        "tower_extra_influence_bonus": tower_advantage_effect["extra_influence_applied"],
        "right_to_error": tower_advantage_effect["right_to_error"],
    })
    _append_note(
        duel,
        "resolve_debug",
        {
            "note": payload.get("note"),
            "gold_result": gold_result,
            "loser_effect": loser_effect,
            "winner_transfer_effect": winner_transfer_effect,
            "winner_bonus_effect": winner_bonus_effect,
            "tower_advantage": {
                "advantage_side": duel.duel_advantage_side,
                "advantage_class": duel.duel_advantage_class,
                "winner_matched_advantage": tower_advantage_effect["winner_matched_advantage"],
                "extra_influence_applied": tower_advantage_effect["extra_influence_applied"],
                "right_to_error": tower_advantage_effect["right_to_error"],
            },
            "tower_bonus_effect_debug": tower_advantage_effect,
        },
    )
    _touch_duel(duel)
    db.flush()

    return {
        "ok": True,
        "message": "Дуэль разрешена",
        "duel": serialize_duel(duel),
        "gold_result": gold_result,
        "live_bonus": {
            "duel_format": duel.duel_format,
            "live_bonus_side": duel.live_bonus_side,
            "live_bonus_code": duel.live_bonus_code,
            "live_bonus_label": duel.live_bonus_label,
            "live_bonus_host_text": duel.live_bonus_host_text,
            "live_bonus_tv_text": duel.live_bonus_tv_text,
            "live_bonus_payload": load_json_text(duel.live_bonus_payload_json),
        },
        "tower_bonus_applied": tower_advantage_effect["tower_bonus_applied"],
        "tower_bonus_effect_debug": tower_advantage_effect,
        "influence_debug": {
            "transfer_amount": DUEL_RESOLVE_INFLUENCE_TRANSFER,
            "bonus_payload": load_json_text(duel.bonus_payload_json),
            "loser_effect": loser_effect,
            "winner_transfer_effect": winner_transfer_effect,
            "winner_bonus_effect": winner_bonus_effect,
            "tower_advantage": {
                "advantage_side": duel.duel_advantage_side,
                "advantage_class": duel.duel_advantage_class,
                "winner_matched_advantage": tower_advantage_effect["winner_matched_advantage"],
                "extra_influence_applied": tower_advantage_effect["extra_influence_applied"],
                "right_to_error": tower_advantage_effect["right_to_error"],
            },
            "tower_bonus_effect_debug": tower_advantage_effect,
        },
    }


def list_duels_for_game(db: Session, game_id: int) -> list[GameDuel]:
    return (
        db.query(GameDuel)
        .filter(GameDuel.game_id == game_id)
        .order_by(GameDuel.id.asc())
        .all()
    )
