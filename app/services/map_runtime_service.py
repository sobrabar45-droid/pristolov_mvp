from __future__ import annotations

from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.role import Role
from app.models.game_map_state import GameMapState
from app.models.game_map_visit import GameMapVisit
from app.services.map_service import (
    load_locations_catalog,
    choose_active_locations,
    explore_location_for_house,
)
from app.services.expedition_service import get_expedition_runtime_context
from app.services.serialization_utils import dump_json, load_json_text
from app.models.game_expedition import GameExpedition, GameExpeditionMember

DEFAULT_MOVES_TOTAL = 2
DEFAULT_OPEN_LOCATIONS_COUNT = 4

def apply_expedition_role_modifiers(
    *,
    role_codes: list[str],
    session_modifiers: dict[str, Any],
    members_count: int = 0,
    approved_by_lord: bool = False,
) -> dict[str, Any]:
    base_modifiers = dict(session_modifiers or {})
    modifiers = dict(base_modifiers)

    role_set = set(role_codes or [])
    applied_synergies: list[str] = []

    if "diplomat" in role_set:
        modifiers["reward_bonus"] = modifiers.get("reward_bonus", 0) + 1

    if "maester" in role_set:
        modifiers["risk_reduction"] = modifiers.get("risk_reduction", 0) + 1

    if "whisper_master" in role_set:
        modifiers["hidden_bonus"] = modifiers.get("hidden_bonus", 0) + 1

    if "treasurer" in role_set:
        modifiers["resource_bonus"] = modifiers.get("resource_bonus", 0) + 1

    if "house_sworn" in role_set:
        modifiers["penalty_reduction"] = modifiers.get("penalty_reduction", 0) + 1
        modifiers["risk_reduction"] = modifiers.get("risk_reduction", 0) + 1

    if "lord_lady" in role_set:
        modifiers["command_bonus"] = modifiers.get("command_bonus", 0) + 1

    if approved_by_lord:
        modifiers["command_bonus"] = modifiers.get("command_bonus", 0) + 1
        applied_synergies.append("lord_approval")

    size_profile = "standard"
    if members_count <= 1:
        modifiers["risk_bonus"] = modifiers.get("risk_bonus", 0) + 1
        size_profile = "solo"
        applied_synergies.append("size:solo")
    elif members_count >= 3:
        modifiers["reward_bonus"] = modifiers.get("reward_bonus", 0) + 1
        modifiers["risk_bonus"] = modifiers.get("risk_bonus", 0) + 1
        size_profile = "group"
        applied_synergies.append("size:group")

    if "diplomat" in role_set and "whisper_master" in role_set:
        modifiers["hidden_bonus"] = modifiers.get("hidden_bonus", 0) + 2
        applied_synergies.append("diplomat+whisper_master")

    if "maester" in role_set and "treasurer" in role_set:
        modifiers["resource_bonus"] = modifiers.get("resource_bonus", 0) + 2
        modifiers["reward_bonus"] = modifiers.get("reward_bonus", 0) + 1
        applied_synergies.append("maester+treasurer")

    if "lord_lady" in role_set and "house_sworn" in role_set:
        modifiers["penalty_reduction"] = modifiers.get("penalty_reduction", 0) + 2
        modifiers["risk_reduction"] = modifiers.get("risk_reduction", 0) + 1
        applied_synergies.append("lord_lady+house_sworn")

    if "lord_lady" in role_set and "diplomat" in role_set:
        modifiers["reward_bonus"] = modifiers.get("reward_bonus", 0) + 1
        modifiers["command_bonus"] = modifiers.get("command_bonus", 0) + 1
        applied_synergies.append("lord_lady+diplomat")

    if "maester" in role_set and "whisper_master" in role_set:
        modifiers["hidden_bonus"] = modifiers.get("hidden_bonus", 0) + 1
        modifiers["risk_reduction"] = modifiers.get("risk_reduction", 0) + 1
        applied_synergies.append("maester+whisper_master")

    modifiers_delta = {}

    all_modifier_keys = sorted(set(base_modifiers.keys()) | set(modifiers.keys()))
    for key in all_modifier_keys:
        before_value = base_modifiers.get(key, 0)
        after_value = modifiers.get(key, 0)

        if before_value != after_value:
            modifiers_delta[key] = {
                "before": before_value,
                "after": after_value,
                "delta": after_value - before_value,
            }

    return {
        "base_modifiers": base_modifiers,
        "final_modifiers": modifiers,
        "modifiers_delta": modifiers_delta,
        "applied_synergies": applied_synergies,
        "members_count": members_count,
        "size_profile": size_profile,
        "approved_by_lord": approved_by_lord,
    }
def get_expedition_role_codes(
    db: Session,
    expedition: GameExpedition,
) -> list[str]:
    members = (
        db.query(GameExpeditionMember)
        .filter(GameExpeditionMember.expedition_id == expedition.id)
        .all()
    )

    role_codes: list[str] = []

    for m in members:
        player = db.query(Player).filter(Player.id == m.player_id).first()
        if player and player.role and player.role.code:
            role_codes.append(player.role.code)

    return list(set(role_codes))

def get_or_create_map_state_for_house(
    db: Session,
    *,
    game_id: int,
    house_id: int,
    locations_file_path: Path,
    open_codes: list[str] | None = None,
    base_open_count: int = DEFAULT_OPEN_LOCATIONS_COUNT,
    moves_total: int = DEFAULT_MOVES_TOTAL,
    seed: int | None = None,
) -> GameMapState:
    existing = (
        db.query(GameMapState)
        .filter(
            GameMapState.game_id == game_id,
            GameMapState.house_id == house_id,
        )
        .first()
    )

    if existing:
        return existing

    catalog = load_locations_catalog(locations_file_path)
    active_locations = choose_active_locations(
        catalog,
        open_codes=open_codes,
        base_open_count=base_open_count,
        seed=seed,
    )

    active_codes = []

    for item in active_locations:
        code = item.get("code")
        if not code:
            continue

        location = catalog.get(code, {})
        required_tags = location.get("requires_any_tag", [])

        if isinstance(required_tags, list) and required_tags:
            continue

        active_codes.append(code)

    state = GameMapState(
        game_id=game_id,
        house_id=house_id,
        current_location_code=None,
        moves_total=moves_total,
        moves_used=0,
        active_location_codes=dump_json(active_codes),
        opened_tags=dump_json([]),
        session_modifiers=dump_json({}),
    )

    db.add(state)
    db.flush()
    return state


def get_house_role_codes_for_map(
    db: Session,
    *,
    game_id: int,
    house_id: int,
) -> list[str]:
    """
    Для карты считаем, что Дом действует через набор ролей игроков,
    находящихся внутри этого дома в этой игре.
    """
    players = (
        db.query(Player)
        .filter(
            Player.game_id == game_id,
            Player.house_id == house_id,
        )
        .all()
    )

    role_codes: list[str] = []

    for player in players:
        if player.role and player.role.code:
            role_codes.append(player.role.code)

    # unique preserving order
    unique_codes: list[str] = []
    seen = set()
    for code in role_codes:
        if code not in seen:
            unique_codes.append(code)
            seen.add(code)

    return unique_codes


def get_player_role_codes_for_map(player: Player) -> list[str]:
    if player.role and player.role.code:
        return [player.role.code]
    return []


def get_visit_count_for_house_and_location(
    db: Session,
    *,
    game_id: int,
    house_id: int,
    location_code: str,
) -> int:
    visits_count = (
        db.query(GameMapVisit)
        .filter(
            GameMapVisit.game_id == game_id,
            GameMapVisit.house_id == house_id,
            GameMapVisit.location_code == location_code,
        )
        .count()
    )
    return visits_count


def parse_opened_tags(state: GameMapState) -> list[str]:
    raw = load_json_text(state.opened_tags)
    if isinstance(raw, list):
        return raw
    return []


def parse_active_location_codes(state: GameMapState) -> list[str]:
    raw = load_json_text(state.active_location_codes)
    if isinstance(raw, list):
        return raw
    return []


def parse_session_modifiers(state: GameMapState) -> dict[str, Any]:
    raw = load_json_text(state.session_modifiers)
    if isinstance(raw, dict):
        return raw
    return {}


def append_opened_tags_from_meta(
    state: GameMapState,
    *,
    meta: dict[str, Any] | None = None,
) -> list[str]:
    meta = meta or {}
    reward_meta = meta.get("reward_meta", {})
    opened_tags = parse_opened_tags(state)

    if not isinstance(reward_meta, dict):
        reward_meta = {}

    candidate_tags: list[str] = []

    access_tag = reward_meta.get("access_tag")
    if isinstance(access_tag, str):
        candidate_tags.append(access_tag)

    for key, value in reward_meta.items():
        if isinstance(value, int) and value > 0:
            if key in {
                "contraband_access",
                "foreign_contact",
                "official_pass",
                "hidden_signal",
                "fear_tag",
                "house_secret",
                "deal_advantage",
                "exchange_offer",
            }:
                candidate_tags.append(key)

    merged = list(opened_tags)
    for tag in candidate_tags:
        if tag not in merged:
            merged.append(tag)

    state.opened_tags = dump_json(merged)
    return merged

def unlock_locations_by_opened_tags(
    state: GameMapState,
    *,
    catalog: dict[str, dict[str, Any]],
    opened_tags: list[str],
) -> list[str]:
    active_codes = parse_active_location_codes(state)
    updated_codes = list(active_codes)

    for code, location in catalog.items():
        if code in updated_codes:
            continue

        required_tags = location.get("requires_any_tag", [])
        if not isinstance(required_tags, list) or not required_tags:
            continue

        if any(tag in opened_tags for tag in required_tags):
            updated_codes.append(code)

    state.active_location_codes = dump_json(updated_codes)
    return updated_codes


def get_map_state_payload(
    db: Session,
    *,
    room_code: str,
    locations_file_path: Path,
) -> dict[str, Any]:
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    houses = (
        db.query(House)
        .filter(House.game_id == game.id)
        .order_by(House.id.asc())
        .all()
    )

    catalog = load_locations_catalog(locations_file_path)

    houses_payload = []

    for house in houses:
        state = get_or_create_map_state_for_house(
            db=db,
            game_id=game.id,
            house_id=house.id,
            locations_file_path=locations_file_path,
        )

        active_codes_raw = parse_active_location_codes(state)
        opened_tags = parse_opened_tags(state)
        role_codes = get_house_role_codes_for_map(
            db,
            game_id=game.id,
            house_id=house.id,
        )

        active_codes = []

        for code in active_codes_raw:
            location = catalog.get(code)
            if not location:
                continue

            required_tags = location.get("requires_any_tag", [])
            if isinstance(required_tags, list) and required_tags:
                if not any(tag in opened_tags for tag in required_tags):
                    continue

            active_codes.append(code)

        active_locations_payload = []

        for code in active_codes:
            location = catalog.get(code)
            if not location:
                continue

            visit_count = get_visit_count_for_house_and_location(
                db=db,
                game_id=game.id,
                house_id=house.id,
                location_code=code,
            )

            active_locations_payload.append(
                {
                    "code": location.get("code"),
                    "name": location.get("name"),
                    "type": location.get("type"),
                    "difficulty": location.get("difficulty"),
                    "risk_level": location.get("risk_level"),
                    "preferred_roles": location.get("preferred_roles", []),
                    "requires_any_tag": location.get("requires_any_tag", []),
                    "summary": location.get("summary"),
                    "visit_count": visit_count,
                }
            )

        houses_payload.append(
            {
                "house": {
                    "id": house.id,
                    "house_key": house.house_key,
                    "name": house.name,
                },
                "map_state": {
                    "id": state.id,
                    "current_location_code": state.current_location_code,
                    "moves_total": state.moves_total,
                    "moves_used": state.moves_used,
                    "moves_left": max(0, (state.moves_total or 0) - (state.moves_used or 0)),
                    "opened_tags": opened_tags,
                    "role_codes": role_codes,
                },
                "active_locations": active_locations_payload,
            }
        )

    db.flush()

    return {
        "ok": True,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "houses_count": len(houses_payload),
        "houses": houses_payload,
    }


def explore_location_by_player(
    db: Session,
    *,
    room_code: str,
    player_id: int,
    location_code: str,
    locations_file_path: Path,
    expedition_id: int | None = None,
) -> dict[str, Any]:
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.game_id == game.id,
        )
        .first()
    )

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден в этой игре",
            "player_id": player_id,
        }

    if not player.house_id:
        return {
            "ok": False,
            "message": "Игрок не привязан к Дому",
            "player_id": player_id,
        }

    house = (
        db.query(House)
        .filter(
            House.id == player.house_id,
            House.game_id == game.id,
        )
        .first()
    )

    if not house:
        return {
            "ok": False,
            "message": "Дом игрока не найден",
            "player_id": player_id,
            "house_id": player.house_id,
        }

    state = get_or_create_map_state_for_house(
        db=db,
        game_id=game.id,
        house_id=house.id,
        locations_file_path=locations_file_path,
    )

    moves_total = state.moves_total or 0
    moves_used = state.moves_used or 0
    moves_left = max(0, moves_total - moves_used)

    if moves_left <= 0:
        return {
            "ok": False,
            "message": "У Дома не осталось ходов по карте",
            "house": {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            },
            "moves_total": moves_total,
            "moves_used": moves_used,
            "moves_left": 0,
        }

    active_codes = parse_active_location_codes(state)
    if location_code not in active_codes:
        return {
            "ok": False,
            "message": "Эта локация сейчас не активна для Дома",
            "location_code": location_code,
            "active_location_codes": active_codes,
        }

    catalog = load_locations_catalog(locations_file_path)

    role_codes = get_player_role_codes_for_map(player)

    expedition = None
    expedition_context = None

    if expedition_id:
        expedition = (
            db.query(GameExpedition)
            .filter(GameExpedition.id == expedition_id)
            .first()
        )

        if expedition:
            expedition_context = get_expedition_runtime_context(db, expedition)
            role_codes = expedition_context["role_codes"]
    
    opened_tags = parse_opened_tags(state)

    base_session_modifiers = parse_session_modifiers(state)

    if expedition:
        expedition_modifier_result = apply_expedition_role_modifiers(
            role_codes=role_codes,
            session_modifiers=base_session_modifiers,
            members_count=expedition_context["members_count"] if expedition_context else 0,
            approved_by_lord=bool(expedition_context and expedition_context["approved"]),
        )
        session_modifiers = dict(expedition_modifier_result["final_modifiers"])
        session_modifiers["is_expedition"] = True
    else:
        expedition_modifier_result = {
            "base_modifiers": base_session_modifiers,
            "final_modifiers": base_session_modifiers,
            "modifiers_delta": {},
            "applied_synergies": [],
        }
        session_modifiers = dict(base_session_modifiers)
        session_modifiers["is_expedition"] = False

    visit_count = get_visit_count_for_house_and_location(
        db=db,
        game_id=game.id,
        house_id=house.id,
        location_code=location_code,
    )

    explore_result = explore_location_for_house(
        db=db,
        catalog=catalog,
        house=house,
        location_code=location_code,
        roles=role_codes,
        visit_count=visit_count,
        house_tags=opened_tags,
        session_modifiers=session_modifiers,
    )

    if not explore_result.get("ok"):
        return explore_result

    rolled_outcome = explore_result.get("rolled_outcome", {})
    effect_data = explore_result.get("effect_data", {})
    outcome_effect_data = explore_result.get("outcome_effect_data", {})
    risk_effect_data = explore_result.get("risk_effect_data", {})
    risk_event = explore_result.get("risk_event", {})
    meta = explore_result.get("meta", {})
    outcome_debug = explore_result.get("outcome_debug", {})
    expedition_risk_debug = explore_result.get("expedition_risk_debug", {})
    risk_event_debug = explore_result.get("risk_event_debug", {})
    expedition_failure_debug = explore_result.get("expedition_failure_debug", {})

    visit_no_for_house = visit_count + 1

    visit = GameMapVisit(
        game_id=game.id,
        house_id=house.id,
        triggered_by_player_id=player.id,
        location_code=location_code,
        visit_no_for_house=visit_no_for_house,
        outcome_type=rolled_outcome.get("type"),
        outcome_text=rolled_outcome.get("text"),
        rolled_outcome_json=dump_json(rolled_outcome),
        effect_data_json=dump_json(effect_data),
        meta_json=dump_json(meta),
    )
    db.add(visit)

    state.current_location_code = location_code
    state.moves_used = moves_used + 1

    opened_tags_after = append_opened_tags_from_meta(
        state,
        meta=meta,
    )

    active_location_codes_after = unlock_locations_by_opened_tags(
        state,
        catalog=catalog,
        opened_tags=opened_tags_after,
    )

    if expedition:
        expedition.status = "resolved"

    db.flush()

    return {
        "ok": True,
        "message": "Ход по карте выполнен",
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "player": {
            "id": player.id,
            "nickname": player.nickname,
            "role_code": player.role.code if player.role else None,
            "role_name": player.role.name if player.role else None,
        },
        "house": {
            "id": house.id,
            "house_key": house.house_key,
            "name": house.name,
        },
        "map_state": {
            "id": state.id,
            "current_location_code": state.current_location_code,
            "moves_total": state.moves_total,
            "moves_used": state.moves_used,
            "moves_left": max(0, (state.moves_total or 0) - (state.moves_used or 0)),
            "opened_tags": opened_tags_after,
            "active_location_codes": active_location_codes_after,
        },
        "visit": {
            "id": visit.id,
            "location_code": visit.location_code,
            "visit_no_for_house": visit.visit_no_for_house,
            "outcome_type": visit.outcome_type,
            "outcome_text": visit.outcome_text,
        },
        "location": explore_result.get("location"),
        "rolled_outcome": rolled_outcome,
        "effect_data": effect_data,
        "outcome_effect_data": outcome_effect_data,
        "risk_effect_data": risk_effect_data,
        "risk_event": risk_event,
        "meta": meta,
        "effect_result": explore_result.get("effect_result"),
        "outcome_debug": outcome_debug,
        "expedition_risk_debug": expedition_risk_debug,
        "risk_event_debug": risk_event_debug,
        "expedition_failure_debug": expedition_failure_debug,
        "expedition_debug": {
            "is_expedition": expedition is not None,
            "expedition_id": expedition.id if expedition else None,
            "role_codes": role_codes,
            "members_count": expedition_context["members_count"] if expedition_context else 1,
            "approved": bool(expedition_context and expedition_context["approved"]),
            "approved_by_player_id": expedition_context["approved_by_player_id"] if expedition_context else None,
            "leader_player_id": expedition_context["leader_player_id"] if expedition_context else None,
            "visit_count_before": visit_count,
            "modifiers": {
                "base": expedition_modifier_result.get("base_modifiers", {}),
                "final": expedition_modifier_result.get("final_modifiers", {}),
                "delta": expedition_modifier_result.get("modifiers_delta", {}),
            },
            "applied_synergies": expedition_modifier_result.get("applied_synergies", []),
            "size_profile": expedition_modifier_result.get("size_profile"),
            "approval_required": bool(expedition_context and expedition_context["requires_lord_approval"]),
            "fallback_without_lord": bool(expedition_context and expedition_context["fallback_without_lord"]),
        },
    }

def reset_map_moves_for_house(
    db: Session,
    *,
    house_id: int,
    moves_total: int | None = None,
) -> dict[str, Any]:
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

    state = (
        db.query(GameMapState)
        .filter(
            GameMapState.game_id == house.game_id,
            GameMapState.house_id == house.id,
        )
        .first()
    )

    if not state:
        return {
            "ok": False,
            "message": "Для дома ещё не создано map_state",
            "house_id": house_id,
        }

    old_moves_total = state.moves_total or 0
    old_moves_used = state.moves_used or 0

    state.moves_used = 0

    if isinstance(moves_total, int) and moves_total >= 0:
        state.moves_total = moves_total

    db.flush()

    return {
        "ok": True,
        "message": "Ходы карты для дома сброшены",
        "house": {
            "id": house.id,
            "house_key": house.house_key,
            "name": house.name,
            "game_id": house.game_id,
        },
        "map_state": {
            "id": state.id,
            "current_location_code": state.current_location_code,
            "moves_total_old": old_moves_total,
            "moves_total_new": state.moves_total,
            "moves_used_old": old_moves_used,
            "moves_used_new": state.moves_used,
            "moves_left": max(0, (state.moves_total or 0) - (state.moves_used or 0)),
            "opened_tags": parse_opened_tags(state),
            "active_location_codes": parse_active_location_codes(state),
        },
    }
