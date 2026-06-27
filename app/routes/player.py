from datetime import datetime, timezone
from secrets import token_urlsafe
import random
import json
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import SessionLocal
from app.models.player import Player
from app.models.house import House
from app.models.game import Game
from app.models.game_phase import GamePhase
from app.models.game_assignment import GameAssignment
from app.models.game_host_round import GameHostRound
from app.models.game_expedition import GameExpedition
from app.models.game_map_visit import GameMapVisit
from app.models.game_deal import GameDeal
from app.models.game_duel import GameDuel
from app.services.serialization_utils import dump_json as _dump_json, load_json_text as _load_json_text
from app.services.map_service import load_locations_catalog
from app.services.expedition_service import create_expedition as _create_expedition
from app.services.duel_service import (
    create_duel_challenge as _create_duel_challenge,
    accept_duel as _accept_duel,
    refuse_duel as _refuse_duel,
    serialize_duel as _serialize_duel,
)
from app.services.gold_service import (
    GoldError,
    GoldInsufficientFundsError,
    spend_gold_for_action,
)

# Временный мост: используем уже существующую игровую логику ответов
from app.services.resource_service import apply_house_effect as _apply_house_effect, build_house_resources_snapshot as _build_house_resources_snapshot
from app.services.assignment_service import process_assignment_answer as _process_assignment_answer
from app.services.host_round_service import open_next_question_for_host_round as _open_next_question_for_host_round

router = APIRouter(prefix="/player", tags=["player"])

BASE_DIR = Path(__file__).resolve().parent.parent
MAP_LOCATIONS_FILE = BASE_DIR / "game_templates" / "season1_core_v1" / "locations.yaml"

EXPEDITION_LOCATION_OPTIONS = {
    "old_market": "Старый рынок",
    "craft_yard": "Ремесленный двор",
    "archive": "Архив",
    "guard_barracks": "Казармы стражи",
    "alleys": "Переулки",
    "guest_court": "Гостевой двор",
}

EXPEDITION_LOCATION_FALLBACKS = {
    "craft_yard": {
        "code": "craft_yard",
        "name": "Ремесленный двор",
        "risk_level": 22,
        "preferred_roles": ["treasurer", "house_sworn"],
        "outcomes": [
            {"weight": 45, "type": "reward", "reward": {"wood": 1, "stone": 1}, "text": "Ремесленники помогли с материалами для Дома."},
            {"weight": 35, "type": "reward", "reward": {"gold": 1}, "text": "Удачный подряд принёс дополнительное золото."},
            {"weight": 20, "type": "penalty", "penalty": {"gold": -1}, "text": "Срыв работы стоил Дому лишних трат."},
        ],
    },
    "guard_barracks": {
        "code": "guard_barracks",
        "name": "Казармы стражи",
        "risk_level": 30,
        "preferred_roles": ["lord_lady", "house_sworn"],
        "outcomes": [
            {"weight": 40, "type": "reward", "reward": {"influence": 1}, "text": "Стража признала силу вашего Дома."},
            {"weight": 35, "type": "reward", "reward": {"iron": 1}, "text": "Удалось получить доступ к военным запасам."},
            {"weight": 25, "type": "penalty", "penalty": {"influence": -1}, "text": "Разговор с гарнизоном обернулся потерей веса."},
        ],
    },
    "guest_court": {
        "code": "guest_court",
        "name": "Гостевой двор",
        "risk_level": 18,
        "preferred_roles": ["diplomat", "whisper_master"],
        "outcomes": [
            {"weight": 45, "type": "reward", "reward": {"influence": 1, "gold": 1}, "text": "Гостевой двор открыл выгодную договорённость."},
            {"weight": 30, "type": "reward", "reward": {"key": 1}, "text": "Через гостей удалось добыть важный ключ."},
            {"weight": 25, "type": "empty", "text": "Вежливые разговоры не принесли заметной выгоды."},
        ],
    },
}

EXPEDITION_ROLE_OPTIONS = {
    "lord_lady": "Лорд / Леди",
    "maester": "Мейстер",
    "diplomat": "Дипломат",
    "treasurer": "Мастер над золотом",
    "whisper_master": "Мастер шёпота",
    "house_sworn": "Соратник Дома",
}

DEAL_ACTIVE_SUBMIT_BLOCKING_STATUSES = {
    "pending",
    "processing",
    "countered",
    "accepted_waiting_treasurer",
    "accepted",
    "alliance_active",
}

DEAL_PROMISE_BLOCKING_STATUSES = {
    "pending",
    "processing",
    "countered",
    "accepted_waiting_treasurer",
    "accepted",
    "alliance_active",
    "completed",
}

DEAL_ACTIONABLE_RESPONSE_STATUSES = {
    "pending",
    "countered",
}

V1_DIPLOMACY_RESOURCE_TYPES = {
    "gold",
    "influence",
}

LAST_WHISPER_ACTIONS = {
    "quiet_support": {
        "code": "quiet_support",
        "label": "Тихая поддержка",
        "tv_text": "{house_name} пустил тихую поддержку перед финалом.",
    },
    "break_alliance": {
        "code": "break_alliance",
        "label": "Разрыв союза",
        "tv_text": "{house_name} вмешался в союзные договорённости.",
    },
    "crown_tax": {
        "code": "crown_tax",
        "label": "Налог на корону",
        "tv_text": "{house_name} потребовал налог на корону.",
    },
}

TREASURER_SHOP_ACTIONS = {
    "set_bar": {
        "code": "set_bar",
        "label": "Сет у стойки",
        "cost": 5,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "operator",
        "event_text": "Дом {actor} заказал сет у стойки за 5 золота. За столом стало громче.",
    },
    "giraffe": {
        "code": "giraffe",
        "label": "Жираф",
        "cost": 10,
        "requires_ally": False,
        "is_18_plus": True,
        "category": "alcohol",
        "event_text": "Дом {actor} заказал жирафа за 10 золота. Пир набирает силу.",
    },
    "author_tea": {
        "code": "author_tea",
        "label": "Авторский чай",
        "cost": 3,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "drink",
        "event_text": "Дом {actor} заказал авторский чай за 3 золота. За столом стало теплее.",
    },
    "premium_champagne_premier": {
        "code": "premium_champagne_premier",
        "label": "Шампанское Премиум премьер",
        "cost": 7,
        "requires_ally": False,
        "is_18_plus": True,
        "category": "alcohol",
        "event_text": "Дом {actor} заказал шампанское Премиум премьер за 7 золота. Выдача подтверждена баром.",
    },
    "tincture_set": {
        "code": "tincture_set",
        "label": "Сет настоек",
        "cost": 7,
        "requires_ally": False,
        "is_18_plus": True,
        "category": "alcohol",
        "event_text": "Дом {actor} заказал сет настоек за 7 золота. Выдача подтверждена баром.",
    },
    "beer_giraffe_shihan": {
        "code": "beer_giraffe_shihan",
        "label": "Жираф пива Шихан",
        "cost": 10,
        "requires_ally": False,
        "is_18_plus": True,
        "category": "alcohol",
        "event_text": "Дом {actor} заказал жираф пива Шихан за 10 золота. Выдача подтверждена баром.",
    },
    "lemonade_02": {
        "code": "lemonade_02",
        "label": "Лимонад 0.2 л",
        "cost": 2,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "drink",
        "event_text": "Дом {actor} заказал лимонад 0.2 л за 2 золота. Пир получил лёгкую передышку.",
    },
    "sobranie_pizza": {
        "code": "sobranie_pizza",
        "label": "Пицца Собрание",
        "cost": 6,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "food",
        "event_text": "Дом {actor} заказал пиццу Собрание за 6 золота. Совет Дома подкрепился.",
    },
    "beer_set_any": {
        "code": "beer_set_any",
        "label": "любой пивной сет (1, 2, 3, 4)",
        "cost": 10,
        "requires_ally": False,
        "is_18_plus": True,
        "category": "alcohol",
        "event_text": "Дом {actor} заказал пивной сет за 10 золота. Конкретный сет согласован вручную с баром.",
    },
    "anna_pavlova": {
        "code": "anna_pavlova",
        "label": "Анна Павлова",
        "cost": 2,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "dessert",
        "event_text": "Дом {actor} заказал Анну Павлову за 2 золота. В зале стало чуть торжественнее.",
    },
    "tapas_set": {
        "code": "tapas_set",
        "label": "Сет тапасов",
        "cost": 7,
        "requires_ally": False,
        "is_18_plus": False,
        "category": "food",
        "event_text": "Дом {actor} заказал сет тапасов за 7 золота. За столом стало сытнее.",
    },
    "gift_to_ally": {
        "code": "gift_to_ally",
        "label": "Подарок союзнику",
        "cost": 15,
        "requires_ally": True,
        "is_18_plus": False,
        "category": "game_effect",
        "event_text": "Дом {actor} угостил союзников из Дома {ally}. Оба Дома получают +1 влияние.",
    },
}

TREASURER_SHOP_DIRECT_PURCHASE_ACTIONS = {
    "set_bar",
    "giraffe",
    "author_tea",
    "lemonade_02",
    "sobranie_pizza",
    "anna_pavlova",
    "gift_to_ally",
}

TREASURER_SHOP_REQUEST_ACTIONS = {
    code: TREASURER_SHOP_ACTIONS[code]
    for code in (
        "author_tea",
        "premium_champagne_premier",
        "tincture_set",
        "beer_giraffe_shihan",
        "lemonade_02",
        "sobranie_pizza",
        "beer_set_any",
        "anna_pavlova",
        "tapas_set",
    )
}


def _issue_player_token() -> str:
    return token_urlsafe(24)


def _resolve_player_by_token(db: Session, player_token: str):
    if not player_token or not isinstance(player_token, str):
        return None

    player = (
        db.query(Player)
        .options(
            joinedload(Player.house),
            joinedload(Player.role),
            joinedload(Player.game),
        )
        .filter(Player.player_token == player_token)
        .first()
    )
    return player


def _ensure_player_token(db: Session, player: Player) -> str:
    if player.player_token:
        return player.player_token

    while True:
        new_token = _issue_player_token()
        exists = db.query(Player).filter(Player.player_token == new_token).first()
        if not exists:
            player.player_token = new_token
            db.flush()
            return new_token


def _normalize_deal_text_value(value) -> str:
    if value is None:
        return ""
    normalized = fix_encoding(str(value)).strip().lower()
    return " ".join(normalized.split())


def _normalize_deal_offer_payload(offer_payload) -> dict:
    if not isinstance(offer_payload, dict):
        return {}
    resource_amount = offer_payload.get("resource_amount")
    if not isinstance(resource_amount, int):
        resource_amount = None
    return {
        "type": str(offer_payload.get("type") or "").strip().lower(),
        "resource_type": str(offer_payload.get("resource_type") or "").strip().lower() or None,
        "resource_amount": resource_amount,
        "crest_piece": _normalize_deal_text_value(offer_payload.get("crest_piece")) or None,
        "text": _normalize_deal_text_value(offer_payload.get("text")) or None,
    }


def _offers_are_equivalent(left_offer, right_offer) -> bool:
    return _normalize_deal_offer_payload(left_offer) == _normalize_deal_offer_payload(right_offer)


def _find_duplicate_outgoing_deal(
    db: Session,
    *,
    game_id: int,
    from_house_id: int,
    to_house_id: int,
    offer_payload: dict,
):
    candidate_deals = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.from_house_id == from_house_id,
            GameDeal.to_house_id == to_house_id,
            GameDeal.status.in_(list(DEAL_ACTIVE_SUBMIT_BLOCKING_STATUSES)),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )
    for deal in candidate_deals:
        if _offers_are_equivalent(deal.offer, offer_payload):
            return deal
    return None


def _find_promised_crest_piece_conflict(
    db: Session,
    *,
    game_id: int,
    from_house_id: int,
    crest_piece: str,
):
    normalized_piece = _normalize_deal_text_value(crest_piece)
    if not normalized_piece:
        return None
    candidate_deals = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.from_house_id == from_house_id,
            GameDeal.status.in_(list(DEAL_PROMISE_BLOCKING_STATUSES)),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )
    for deal in candidate_deals:
        offer = _normalize_deal_offer_payload(deal.offer)
        if offer.get("type") != "crest_piece":
            continue
        if offer.get("crest_piece") == normalized_piece:
            return deal
    return None


def _find_promised_resource_conflict(
    db: Session,
    *,
    game_id: int,
    from_house_id: int,
    to_house_id: int,
    resource_type: str,
    resource_amount: int | None,
):
    normalized_type = str(resource_type or "").strip().lower()
    if not normalized_type or not isinstance(resource_amount, int) or resource_amount <= 0:
        return None
    candidate_deals = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.from_house_id == from_house_id,
            GameDeal.to_house_id == to_house_id,
            GameDeal.status.in_(list(DEAL_ACTIVE_SUBMIT_BLOCKING_STATUSES)),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )
    for deal in candidate_deals:
        offer = _normalize_deal_offer_payload(deal.offer)
        if offer.get("type") != "resource":
            continue
        if offer.get("resource_type") == normalized_type and offer.get("resource_amount") == resource_amount:
            return deal
    return None


def _get_blocked_crest_pieces_for_house(
    db: Session,
    *,
    game_id: int,
    from_house_id: int,
) -> list[str]:
    candidate_deals = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.from_house_id == from_house_id,
            GameDeal.status.in_(list(DEAL_PROMISE_BLOCKING_STATUSES)),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )
    blocked_by_key: dict[str, str] = {}
    for deal in candidate_deals:
        offer = _normalize_deal_offer_payload(deal.offer)
        if offer.get("type") != "crest_piece":
            continue
        normalized_piece = offer.get("crest_piece")
        if not normalized_piece or normalized_piece in blocked_by_key:
            continue
        raw_piece = ""
        if isinstance(deal.offer, dict):
            raw_piece = fix_encoding(str(deal.offer.get("crest_piece") or "").strip())
        blocked_by_key[normalized_piece] = raw_piece or normalized_piece
    return sorted(blocked_by_key.values(), key=lambda item: _normalize_deal_text_value(item))


LAST_SEEN_TOUCH_INTERVAL_SECONDS = 60


def _touch_last_seen(player: Player, *, min_interval_seconds: int = LAST_SEEN_TOUCH_INTERVAL_SECONDS) -> bool:
    now = datetime.now(timezone.utc)
    last_seen_at = player.last_seen_at
    if last_seen_at and last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
    if last_seen_at and (now - last_seen_at).total_seconds() < min_interval_seconds:
        return False
    player.last_seen_at = now
    return True


def _get_phase_label(phase_type: str | None) -> str | None:
    phase_labels = {
        "host_round": "Раунд ведущего",
        "map": "Карта",
        "diplomacy": "Дипломатия",
        "crest": "Герб",
        "upgrade": "Усиление",
        "duel": "Дуэли",
        "intrigue": "Интриги",
        "free_play": "Свободная игра",
        "intermission": "Перерыв",
        "court": "Суд Домов",
        "final": "Финал",
        "last_whisper": "Последний Шёпот",
    }
    return phase_labels.get(phase_type, phase_type)


def _get_active_last_whisper_phase(db: Session, game_id: int) -> GamePhase | None:
    return (
        db.query(GamePhase)
        .filter(
            GamePhase.game_id == game_id,
            GamePhase.phase_type == "last_whisper",
            GamePhase.status == "active",
        )
        .order_by(GamePhase.id.desc())
        .first()
    )


def _get_last_whisper_actions_from_phase(phase: GamePhase | None) -> list[dict]:
    if not phase:
        return []
    payload = phase.payload if isinstance(phase.payload, dict) else {}
    actions = payload.get("whisper_actions")
    if not isinstance(actions, list):
        return []
    return [item for item in actions if isinstance(item, dict)]


def _serialize_last_whisper_action(raw_action: dict) -> dict:
    house_name = fix_encoding(str(raw_action.get("house_name") or "").strip())
    action_code = str(raw_action.get("action_code") or "").strip().lower()
    action_label = fix_encoding(str(raw_action.get("action_label") or "").strip())
    tv_text = fix_encoding(str(raw_action.get("tv_text") or "").strip())
    target_house_name = fix_encoding(str(raw_action.get("target_house_name") or "").strip())
    target_label = fix_encoding(str(raw_action.get("target_label") or "").strip())
    return {
        "order_no": raw_action.get("order_no"),
        "created_at": raw_action.get("created_at"),
        "house_id": raw_action.get("house_id"),
        "house_name": house_name or None,
        "target_deal_id": raw_action.get("target_deal_id"),
        "target_house_id": raw_action.get("target_house_id"),
        "target_house_name": target_house_name or None,
        "target_label": target_label or None,
        "player_id": raw_action.get("player_id"),
        "player_name": fix_encoding(str(raw_action.get("player_name") or "").strip()) or None,
        "action_code": action_code or None,
        "action_label": action_label or None,
        "tv_text": tv_text or None,
        "resources_changed": raw_action.get("resources_changed") if isinstance(raw_action.get("resources_changed"), dict) else {},
    }


def _build_last_whisper_state_for_player(db: Session, player: Player) -> dict | None:
    phase = _get_active_last_whisper_phase(db, player.game_id)
    if not phase:
        return None

    events = [_serialize_last_whisper_action(item) for item in _get_last_whisper_actions_from_phase(phase)]
    viewer_event = None
    for item in events:
        if item.get("house_id") == player.house_id:
            viewer_event = item
            break

    available_target_houses = []
    if player.house_id:
        other_houses = (
            db.query(House)
            .filter(
                House.game_id == player.game_id,
                House.id != player.house_id,
            )
            .order_by(House.id.asc())
            .all()
        )
        available_target_houses = [
            {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            }
            for house in other_houses
        ]

    available_alliances = [
        {
            "deal_id": deal.id,
            "house_a": {
                "id": deal.from_house.id,
                "name": deal.from_house.name,
                "house_key": deal.from_house.house_key,
            } if deal.from_house else None,
            "house_b": {
                "id": deal.to_house.id,
                "name": deal.to_house.name,
                "house_key": deal.to_house.house_key,
            } if deal.to_house else None,
            "label": fix_encoding(
                f"{deal.from_house.name if deal.from_house else 'Дом'} ↔ {deal.to_house.name if deal.to_house else 'Дом'}"
            ),
        }
        for deal in _get_active_alliance_deals(db, game_id=player.game_id)
    ]

    return {
        "active": True,
        "phase_id": phase.id,
        "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
        "viewer_can_act": bool(player.role and player.role.code == "whisper_master" and player.house_id),
        "viewer_has_acted": viewer_event is not None,
        "viewer_action": viewer_event,
        "available_actions": [
            {
                "code": item["code"],
                "label": item["label"],
                "requires_target_house": item["code"] == "quiet_support",
                "requires_alliance_deal": item["code"] == "break_alliance",
            }
            for item in LAST_WHISPER_ACTIONS.values()
        ],
        "available_target_houses": available_target_houses,
        "available_alliances": available_alliances,
        "events": events,
        "latest_event": events[-1] if events else None,
    }



def _get_single_influence_leader(db: Session, game_id: int) -> House | None:
    houses = (
        db.query(House)
        .filter(House.game_id == game_id)
        .order_by(House.id.asc())
        .all()
    )
    if not houses:
        return None

    leaders = sorted(
        houses,
        key=lambda house: int(getattr(house, "resource_influence", 0) or 0),
        reverse=True,
    )
    top_value = int(getattr(leaders[0], "resource_influence", 0) or 0)
    top_houses = [
        house
        for house in leaders
        if int(getattr(house, "resource_influence", 0) or 0) == top_value
    ]
    if len(top_houses) != 1:
        return None
    return top_houses[0]

def _load_expedition_locations_catalog() -> dict[str, dict]:
    catalog = {}
    try:
        catalog = load_locations_catalog(MAP_LOCATIONS_FILE)
    except Exception:
        catalog = {}

    merged = dict(catalog)
    for code, payload in EXPEDITION_LOCATION_FALLBACKS.items():
        if code not in merged:
            merged[code] = payload

    for code, name in EXPEDITION_LOCATION_OPTIONS.items():
        if code not in merged:
            merged[code] = {
                "code": code,
                "name": name,
                "risk_level": 20,
                "preferred_roles": [],
                "outcomes": [
                    {"weight": 100, "type": "empty", "text": "Экспедиция не нашла заметного преимущества."}
                ],
            }

    return merged


def _location_name_by_code(location_code: str | None) -> str | None:
    if not location_code:
        return None
    catalog = _load_expedition_locations_catalog()
    location = catalog.get(location_code, {})
    raw_name = location.get("name") or EXPEDITION_LOCATION_OPTIONS.get(location_code) or location_code
    return fix_encoding(raw_name)


def _normalize_expedition_location_code(location_code) -> str:
    if not isinstance(location_code, str):
        return ""
    return location_code.strip().lower()


def _get_catalog_expedition_location(location_code) -> dict | None:
    normalized_code = _normalize_expedition_location_code(location_code)
    if not normalized_code:
        return None
    return _load_expedition_locations_catalog().get(normalized_code)


def _weighted_pick_outcome(outcomes: list[dict]) -> dict:
    weighted_pool = []
    total_weight = 0

    for outcome in outcomes or []:
        weight = outcome.get("weight", 0)
        if not isinstance(weight, int) or weight <= 0:
            continue
        total_weight += weight
        weighted_pool.append((total_weight, outcome))

    if not weighted_pool:
        return {"type": "empty", "text": "Экспедиция не принесла заметного результата."}

    roll = random.randint(1, total_weight)
    for threshold, outcome in weighted_pool:
        if roll <= threshold:
            return outcome

    return weighted_pool[-1][1]


def _normalize_resource_delta_map(raw: dict | None) -> dict[str, int]:
    resource_keys = ["gold", "influence", "scroll", "key", "wood", "stone", "iron", "fire"]
    normalized = {}
    raw = raw or {}

    for key in resource_keys:
        value = raw.get(key, 0)
        if isinstance(value, int) and value != 0:
            normalized[key] = value

    return normalized


def _apply_house_resource_deltas(house: House, delta_map: dict[str, int]) -> dict[str, int]:
    field_map = {
        "gold": "resource_gold",
        "influence": "resource_influence",
        "scroll": "resource_scroll",
        "key": "resource_key",
        "wood": "resource_wood",
        "stone": "resource_stone",
        "iron": "resource_iron",
        "fire": "resource_fire",
    }

    applied = {}
    for key, delta in (delta_map or {}).items():
        field_name = field_map.get(key)
        if not field_name or not isinstance(delta, int):
            continue

        old_value = getattr(house, field_name, 0) or 0
        new_value = old_value + delta
        if new_value < 0:
            new_value = 0
        setattr(house, field_name, new_value)
        applied[key] = new_value - old_value

    return applied


def _house_resources_snapshot(house: House) -> dict[str, int]:
    return {
        "gold": house.resource_gold or 0,
        "influence": house.resource_influence or 0,
        "scroll": house.resource_scroll or 0,
        "key": house.resource_key or 0,
        "wood": house.resource_wood or 0,
        "stone": house.resource_stone or 0,
        "iron": house.resource_iron or 0,
        "fire": house.resource_fire or 0,
    }


def _has_active_phase_types(db: Session, game_id: int, phase_types: set[str]) -> bool:
    return db.query(GamePhase.id).filter(
        GamePhase.game_id == game_id,
        GamePhase.status == "active",
        GamePhase.phase_type.in_(list(phase_types)),
    ).first() is not None


def _rebalance_expedition_outcome(
    location: dict,
    reward: dict[str, int],
    penalty: dict[str, int],
) -> tuple[dict[str, int], dict[str, int]]:
    reward = dict(reward or {})
    penalty = dict(penalty or {})

    positive_reward_keys = [key for key, value in reward.items() if isinstance(value, int) and value > 0]
    gold_reward = reward.get("gold", 0)
    risk_level = location.get("risk_level", 0)

    if isinstance(gold_reward, int) and gold_reward > 1:
        allow_strong_gold = bool(
            len(positive_reward_keys) == 1
            and risk_level >= 28
        )
        reward["gold"] = 2 if allow_strong_gold else 1

    if isinstance(reward.get("influence"), int) and reward["influence"] > 1:
        reward["influence"] = 1
    if isinstance(reward.get("scroll"), int) and reward["scroll"] > 1:
        reward["scroll"] = 1

    if isinstance(penalty.get("gold"), int) and penalty["gold"] < -1:
        penalty["gold"] = -1
    if isinstance(penalty.get("influence"), int) and penalty["influence"] < -1:
        penalty["influence"] = -1

    return reward, penalty


def _apply_location_pressure(
    db: Session,
    *,
    game_id: int,
    location_code: str,
    reward: dict[str, int],
    outcome_text: str | None,
) -> tuple[dict[str, int], str | None]:
    prior_resolved_count = (
        db.query(GameExpedition)
        .filter(
            GameExpedition.game_id == game_id,
            GameExpedition.status == "resolved",
            GameExpedition.target_location_code == location_code,
        )
        .count()
    )

    reward = dict(reward or {})
    outcome_text = outcome_text or ""

    if prior_resolved_count == 1 and isinstance(reward.get("gold"), int):
        reward["gold"] = min(reward["gold"], 1)
    elif prior_resolved_count >= 2:
        if isinstance(reward.get("gold"), int):
            reward["gold"] = 0
        if reward.get("gold") == 0:
            reward.pop("gold", None)
        if outcome_text:
            outcome_text = fix_encoding(f"{outcome_text} Точка заметно истощена.")
        else:
            outcome_text = fix_encoding("Точка заметно истощена.")

    return reward, outcome_text


def _load_meta_json(raw_value):
    if not raw_value:
        return {}

    if isinstance(raw_value, dict):
        return raw_value

    try:
        parsed = json.loads(raw_value)
    except Exception:
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _text_quality_score(text: str) -> int:
    if not isinstance(text, str):
        return -10_000

    cyrillic_count = sum(1 for ch in text if ("А" <= ch <= "я") or ch in "Ёё")
    mojibake_markers = (
        text.count("РЎ")
        + text.count("Рђ")
        + text.count("СЃ")
        + text.count("Ð")
        + text.count("Ñ")
        + text.count("Ã")
        + text.count("Â")
        + text.count("�")
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


def _fix_text_map(value):
    if isinstance(value, dict):
        return {key: _fix_text_map(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_fix_text_map(item) for item in value]
    if isinstance(value, str):
        return fix_encoding(value)
    return value


def _house_resources_dict(house: House | None):
    if not house:
        return None

    return {
        "gold": house.resource_gold,
        "influence": house.resource_influence,
        "stone": house.resource_stone,
        "wood": house.resource_wood,
        "iron": house.resource_iron,
        "scroll": house.resource_scroll,
        "key": house.resource_key,
        "fire": house.resource_fire,
    }


def _build_whisper_feed(db: Session, player: Player):
    role_code = player.role.code if player and player.role else None
    if role_code != "whisper_master":
        return []

    house_name = player.house.name if player and player.house else "ваш Дом"
    feed = [
        {
            "title": "Слух с карты",
            "text": f"Разведчики шепчут, что один из маршрутов рядом с {house_name} может скрывать редкую возможность.",
            "kind": "map_secret",
        },
        {
            "title": "Тень за переговорами",
            "text": "Не все события выходят на общий экран. Следите за тем, кто слишком рано меняет тон переговоров.",
            "kind": "soft_warning",
        },
    ]

    if player and player.house_id and player.game_id:
        active_expedition = _get_active_house_expedition(db, player.game_id, player.house_id)
        if active_expedition:
            vote_visits = _get_expedition_vote_visits(db, active_expedition)
            chosen_locations = [visit.location_code for visit in vote_visits if visit.location_code]
            unique_locations_count = len(set(chosen_locations))

            if unique_locations_count > 1:
                feed.append(
                    {
                        "title": "Слухи экспедиции",
                        "text": "В вашем Доме нет согласия по маршруту",
                        "kind": "map_secret",
                    }
                )
            elif chosen_locations and unique_locations_count == 1:
                feed.append(
                    {
                        "title": "Слухи экспедиции",
                        "text": "Большинство склоняется к одному направлению",
                        "kind": "map_secret",
                    }
                )

    return feed


def _get_active_house_expedition(db: Session, game_id: int, house_id: int):
    return (
        db.query(GameExpedition)
        .filter(
            GameExpedition.game_id == game_id,
            GameExpedition.house_id == house_id,
            GameExpedition.status.in_(["planned", "approved"]),
        )
        .order_by(GameExpedition.id.desc())
        .first()
    )


def _get_expedition_vote_visits(db: Session, expedition: GameExpedition):
    raw_visits = (
        db.query(GameMapVisit)
        .filter(
            GameMapVisit.game_id == expedition.game_id,
            GameMapVisit.house_id == expedition.house_id,
            GameMapVisit.outcome_type == "expedition_vote",
        )
        .order_by(GameMapVisit.id.asc())
        .all()
    )

    matched = []
    for visit in raw_visits:
        meta = _load_meta_json(getattr(visit, "meta_json", None))
        if meta.get("expedition_id") == expedition.id:
            matched.append(visit)

    return matched


def _get_expedition_plan_visit(db: Session, expedition: GameExpedition):
    raw_visits = (
        db.query(GameMapVisit)
        .filter(
            GameMapVisit.game_id == expedition.game_id,
            GameMapVisit.house_id == expedition.house_id,
            GameMapVisit.outcome_type == "expedition_plan",
        )
        .order_by(GameMapVisit.id.desc())
        .all()
    )

    for visit in raw_visits:
        meta = _load_meta_json(getattr(visit, "meta_json", None))
        if meta.get("expedition_id") == expedition.id:
            return visit

    return None


def _get_expedition_plan_meta(db: Session, expedition: GameExpedition) -> dict:
    plan_visit = _get_expedition_plan_visit(db, expedition)
    if not plan_visit:
        return {"members_count": 0, "role_codes": []}

    meta = _load_meta_json(getattr(plan_visit, "meta_json", None))
    role_codes = meta.get("role_codes")
    if not isinstance(role_codes, list):
        role_codes = []

    members_count = meta.get("members_count")
    if not isinstance(members_count, int):
        members_count = len(role_codes) if role_codes else 0

    return {
        "members_count": members_count,
        "role_codes": [code for code in role_codes if code in EXPEDITION_ROLE_OPTIONS],
    }


def _normalize_expedition_role_codes(role_codes) -> list[str]:
    if not isinstance(role_codes, list):
        return []

    normalized = []
    for code in role_codes:
        if not isinstance(code, str):
            continue
        if code not in EXPEDITION_ROLE_OPTIONS:
            continue
        if code in normalized:
            continue
        normalized.append(code)
    return normalized


def _validate_expedition_party_request(db: Session, *, house_id: int, members_count: int, raw_role_codes) -> dict:
    house_players = (
        db.query(Player)
        .options(joinedload(Player.role))
        .filter(Player.house_id == house_id)
        .all()
    )
    real_players_count = len(house_players)

    if members_count > real_players_count:
        return {
            "ok": False,
            "message": f"В Доме только {real_players_count} реальных игроков. Нельзя назначить экспедицию на {members_count} участников.",
        }

    if not isinstance(raw_role_codes, list):
        return {
            "ok": True,
            "role_codes": [],
            "real_players_count": real_players_count,
        }

    requested_role_codes: list[str] = []
    seen_role_codes = set()

    for raw_code in raw_role_codes:
        if not isinstance(raw_code, str):
            return {
                "ok": False,
                "message": "Состав экспедиции содержит некорректную роль участника.",
            }

        code = raw_code.strip().lower()
        if code not in EXPEDITION_ROLE_OPTIONS:
            return {
                "ok": False,
                "message": "Состав экспедиции содержит неизвестную роль.",
            }

        if code in seen_role_codes:
            return {
                "ok": False,
                "message": "Роли участников экспедиции не должны повторяться.",
            }

        seen_role_codes.add(code)
        requested_role_codes.append(code)

    occupied_role_codes = {
        str(player.role.code).strip().lower()
        for player in house_players
        if player.role and player.role.code
    }
    missing_role_codes = [
        code for code in requested_role_codes
        if code not in occupied_role_codes
    ]
    if missing_role_codes:
        return {
            "ok": False,
            "message": "В составе экспедиции есть роль, которая не принадлежит реальному игроку этого Дома.",
        }

    return {
        "ok": True,
        "role_codes": requested_role_codes,
        "real_players_count": real_players_count,
    }


def _build_active_house_expedition_payload(db: Session, expedition: GameExpedition | None, *, player_id: int | None = None):
    if not expedition:
        return None

    plan_meta = _get_expedition_plan_meta(db, expedition)
    visits = _get_expedition_vote_visits(db, expedition)
    chosen_locations = [visit.location_code for visit in visits if visit.location_code]
    unique_locations = sorted(set(chosen_locations))
    player_vote = next((visit for visit in reversed(visits) if visit.triggered_by_player_id == player_id), None)

    return {
        "id": expedition.id,
        "status": expedition.status,
        "house_id": expedition.house_id,
        "target_location_code": expedition.target_location_code,
        "members_count": plan_meta["members_count"],
        "role_codes": plan_meta["role_codes"],
        "choices_count": len(visits),
        "unique_locations_count": len(unique_locations),
        "chosen_locations": unique_locations,
        "player_vote_location": player_vote.location_code if player_vote else None,
        "player_vote_location_name": _location_name_by_code(player_vote.location_code) if player_vote and player_vote.location_code else None,
    }


def _sanitize_assignment_question_content(content, *, runtime_question):
    safe_content = dict(content or {}) if isinstance(content, dict) else {}
    if not runtime_question:
        return safe_content

    is_reveal = str(getattr(runtime_question, "status", "") or "").lower() != "active"
    answers_open = bool(getattr(runtime_question, "answers_open", False))
    if is_reveal:
        return safe_content

    for key in ("correct_answer", "answer", "explanation"):
        safe_content.pop(key, None)

    if not answers_open:
        for key in ("options", "statements", "choices", "variants", "items"):
            safe_content.pop(key, None)

    return safe_content


def _sanitize_assignment_result_payload(result_payload, *, runtime_question):
    parsed = _load_json_text(result_payload)
    if not isinstance(parsed, dict) or not runtime_question:
        return result_payload

    is_reveal = str(getattr(runtime_question, "status", "") or "").lower() != "active"
    if is_reveal:
        return result_payload

    parsed.pop("correct_answer", None)
    return _dump_json(parsed)


def _sanitize_assignment_result_payload_object(result_payload, *, runtime_question):
    safe_payload = dict(result_payload or {}) if isinstance(result_payload, dict) else {}
    if not runtime_question:
        return safe_payload

    is_reveal = str(getattr(runtime_question, "status", "") or "").lower() != "active"
    if not is_reveal:
        safe_payload.pop("correct_answer", None)

    return safe_payload


def _serialize_assignment(assignment: GameAssignment):
    template_task = getattr(assignment, "template_task", None)
    host_round = getattr(assignment, "host_round", None)
    runtime_question = getattr(assignment, "host_round_question", None)

    task_content = None
    if template_task and getattr(template_task, "content_json", None):
        task_content = template_task.content_json

    question_content = None
    if runtime_question and getattr(runtime_question, "question_template", None):
        tpl = runtime_question.question_template
        question_content = {
            "id": tpl.id,
            "question_code": tpl.question_code,
            "title": tpl.title,
            "prompt": tpl.prompt,
            "ui_template": tpl.ui_template,
            "answer_mode": tpl.answer_mode,
            "role_code": tpl.role_code,
            "content": _sanitize_assignment_question_content(
                _load_json_text(tpl.content_json),
                runtime_question=runtime_question,
            ),
            "reward": _load_json_text(tpl.reward_json),
            "fail_effect": _load_json_text(tpl.fail_effect_json),
        }

    result_payload = _sanitize_assignment_result_payload(assignment.result_payload, runtime_question=runtime_question)
    answer_payload = assignment.answer_payload

    return {
        "id": assignment.id,
        "status": assignment.status,
        "delivery_mode": assignment.delivery_mode,
        "role_code": assignment.role_code,
        "answer_mode": assignment.answer_mode,
        "auto_check": assignment.auto_check,
        "is_correct": assignment.is_correct,
        "result_applied": assignment.result_applied,
        "triggered_by_host": assignment.triggered_by_host,
        "created_at": assignment.created_at.isoformat() if assignment.created_at else None,
        "template_task": {
            "id": template_task.id,
            "task_code": template_task.task_code,
            "title": template_task.title,
            "prompt": template_task.prompt,
            "ui_template": template_task.ui_template,
            "difficulty": template_task.difficulty,
            "content_json": task_content,
        } if template_task else None,
        "host_round": {
            "id": host_round.id,
            "round_code": host_round.round_code,
            "title": host_round.title,
            "status": host_round.status,
            "current_question_no": host_round.current_question_no,
            "questions_total": host_round.questions_total,
        } if host_round else None,
        "host_round_question": {
            "id": runtime_question.id,
            "sequence_no": runtime_question.sequence_no,
            "status": runtime_question.status,
            "answers_open": runtime_question.answers_open,
            "reveal_stage": "reveal" if str(runtime_question.status or "").lower() != "active" else ("options" if runtime_question.answers_open else "question"),
            "started_at": runtime_question.started_at.isoformat() if runtime_question.started_at else None,
            "template": question_content,
        } if runtime_question else None,
        "answer_payload": answer_payload,
        "result_payload": result_payload,
    }


def _format_deal_offer_text(offer, note: str | None = None) -> str:
    if isinstance(offer, dict):
        offer_type = str(offer.get("type") or "").strip()
        resource_type = str(offer.get("resource_type") or "").strip()
        resource_amount = offer.get("resource_amount")
        crest_piece = str(offer.get("crest_piece") or "").strip()
        text_value = offer.get("text")
        text_value = fix_encoding(text_value.strip()) if isinstance(text_value, str) and text_value.strip() else ""

        resource_labels = {
            "gold": "золото",
            "influence": "влияние",
            "stone": "камень",
            "wood": "дерево",
            "iron": "железо",
            "scroll": "свиток",
            "key": "ключ",
            "fire": "огонь",
        }

        if offer_type == "resource" and resource_type and isinstance(resource_amount, int) and resource_amount > 0:
            base = f"Передача ресурса: {resource_labels.get(resource_type, resource_type)} × {resource_amount}"
            return fix_encoding(f"{base}. Комментарий: {text_value}") if text_value else fix_encoding(base)

        if offer_type == "crest_piece" and crest_piece:
            base = f"Кусок герба: {crest_piece}"
            return fix_encoding(f"{base}. Комментарий: {text_value}") if text_value else fix_encoding(base)

        if offer_type == "open_agreement" and text_value:
            return fix_encoding(f"Открытая договорённость: {text_value}")

        if offer_type == "alliance":
            return fix_encoding(text_value or "Союз домов")

        if text_value:
            return text_value
    if isinstance(note, str) and note.strip():
        return fix_encoding(note.strip())
    return ""


def _serialize_player_deal(deal: GameDeal) -> dict:
    offer_data = deal.offer if isinstance(deal.offer, dict) else {}
    alliance_bonus_applied_to = offer_data.get("alliance_bonus_applied_to") if isinstance(offer_data, dict) else []
    if not isinstance(alliance_bonus_applied_to, list):
        alliance_bonus_applied_to = []
    if str(offer_data.get("type") or "").strip() == "alliance":
        if len(alliance_bonus_applied_to) >= 2:
            bonus_text = "+1 влияние обоим Домам"
        elif len(alliance_bonus_applied_to) == 1:
            bonus_text = "+1 влияние одному из Домов"
        else:
            bonus_text = "Бонус союза уже был использован"
    else:
        bonus_text = ""
    return _fix_text_map({
        "id": deal.id,
        "from_house_id": deal.from_house_id,
        "to_house_id": deal.to_house_id,
        "status": deal.status,
        "offer": offer_data,
        "offer_text": _format_deal_offer_text(offer_data, deal.note),
        "offer_type_label": {
            "resource": "Передача ресурса",
            "crest_piece": "Кусок герба",
            "open_agreement": "Открытая договорённость",
            "alliance": "Союз",
        }.get(str(offer_data.get("type") or "").strip(), ""),
        "from_house": {
            "id": deal.from_house.id,
            "name": deal.from_house.name,
            "house_key": deal.from_house.house_key,
        } if deal.from_house else None,
        "to_house": {
            "id": deal.to_house.id,
            "name": deal.to_house.name,
            "house_key": deal.to_house.house_key,
        } if deal.to_house else None,
        "created_at": deal.created_at.isoformat() if deal.created_at else None,
        "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
        "alliance_bonus": offer_data.get("alliance_bonus") if isinstance(offer_data, dict) else None,
        "bonus_text": bonus_text,
    })


def _serialize_active_alliance(deal: GameDeal, viewer_house_id: int | None = None) -> dict:
    offer_data = deal.offer if isinstance(deal.offer, dict) else {}
    house_a = {
        "id": deal.from_house.id,
        "name": deal.from_house.name,
        "house_key": deal.from_house.house_key,
    } if deal.from_house else None
    house_b = {
        "id": deal.to_house.id,
        "name": deal.to_house.name,
        "house_key": deal.to_house.house_key,
    } if deal.to_house else None
    ally_house = None
    if viewer_house_id:
        if deal.from_house_id == viewer_house_id:
            ally_house = house_b
        elif deal.to_house_id == viewer_house_id:
            ally_house = house_a

    return _fix_text_map({
        "id": deal.id,
        "status": deal.status,
        "house_a": house_a,
        "house_b": house_b,
        "ally_house": ally_house,
        "bonus_text": _serialize_player_deal(deal).get("bonus_text"),
        "activated_at": offer_data.get("activated_at") if isinstance(offer_data, dict) else None,
    })


def _serialize_player_duel(duel: GameDuel) -> dict:
    return _fix_text_map(_serialize_duel(duel))


def _get_active_alliances_for_house(db: Session, *, game_id: int, house_id: int) -> list[GameDeal]:
    if not game_id or not house_id:
        return []
    return (
        db.query(GameDeal)
        .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.status == "alliance_active",
            (
                (GameDeal.from_house_id == house_id)
                | (GameDeal.to_house_id == house_id)
            ),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )


def _get_active_alliance_deals(db: Session, *, game_id: int) -> list[GameDeal]:
    if not game_id:
        return []

    deals = (
        db.query(GameDeal)
        .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.status == "alliance_active",
        )
        .order_by(GameDeal.id.desc())
        .all()
    )

    result = []
    for deal in deals:
        offer = deal.offer if isinstance(deal.offer, dict) else {}
        if str(offer.get("type") or "").strip() == "alliance":
            result.append(deal)
    return result


def _get_treasurer_pending_deals(db: Session, player: Player) -> list[GameDeal]:
    if not player or not player.house_id or not player.game_id:
        return []

    deals = (
        db.query(GameDeal)
        .options(
            joinedload(GameDeal.from_house),
            joinedload(GameDeal.to_house),
        )
        .filter(
            GameDeal.game_id == player.game_id,
            GameDeal.from_house_id == player.house_id,
            GameDeal.status == "accepted_waiting_treasurer",
        )
        .order_by(GameDeal.id.desc())
        .all()
    )

    return [
        deal for deal in deals
        if isinstance(deal.offer, dict) and str(deal.offer.get("type") or "").strip() == "resource"
    ]


def _get_house_duels(
    db: Session,
    *,
    game_id: int,
    house_id: int,
    statuses: set[str] | None = None,
) -> list[GameDuel]:
    if not game_id or not house_id:
        return []

    query = (
        db.query(GameDuel)
        .options(
            joinedload(GameDuel.challenger_house),
            joinedload(GameDuel.target_house),
            joinedload(GameDuel.winner_house),
        )
        .filter(
            GameDuel.game_id == game_id,
            (
                (GameDuel.challenger_house_id == house_id)
                | (GameDuel.target_house_id == house_id)
            ),
        )
        .order_by(GameDuel.id.desc())
    )

    if statuses:
        query = query.filter(GameDuel.status.in_(list(statuses)))

    return query.all()


def _find_alliance_conflict(
    db: Session,
    *,
    game_id: int,
    house_ids: list[int],
    statuses: set[str],
    exclude_deal_id: int | None = None,
):
    if not game_id or not house_ids or not statuses:
        return None

    query = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.status.in_(list(statuses)),
            (
                GameDeal.from_house_id.in_(house_ids)
                | GameDeal.to_house_id.in_(house_ids)
            ),
        )
        .order_by(GameDeal.id.desc())
    )
    if exclude_deal_id:
        query = query.filter(GameDeal.id != exclude_deal_id)

    for deal in query.all():
        offer = deal.offer if isinstance(deal.offer, dict) else {}
        if str(offer.get("type") or "").strip() == "alliance":
            return deal
    return None


def _get_houses_with_alliance_bonus_history(
    db: Session,
    *,
    game_id: int,
    house_ids: list[int],
    exclude_deal_id: int | None = None,
) -> set[int]:
    if not game_id or not house_ids:
        return set()

    query = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.status == "alliance_active",
            (
                GameDeal.from_house_id.in_(house_ids)
                | GameDeal.to_house_id.in_(house_ids)
            ),
        )
        .order_by(GameDeal.id.desc())
    )
    if exclude_deal_id:
        query = query.filter(GameDeal.id != exclude_deal_id)

    used_house_ids: set[int] = set()
    for deal in query.all():
        offer = deal.offer if isinstance(deal.offer, dict) else {}
        if str(offer.get("type") or "").strip() != "alliance":
            continue
        applied_to = offer.get("alliance_bonus_applied_to")
        if isinstance(applied_to, list):
            used_house_ids.update(int(house_id) for house_id in applied_to if isinstance(house_id, int))
            continue
        if offer.get("alliance_bonus_applied") is True:
            if deal.from_house_id in house_ids:
                used_house_ids.add(deal.from_house_id)
            if deal.to_house_id in house_ids:
                used_house_ids.add(deal.to_house_id)
    return used_house_ids


def _find_active_alliance_between_houses(
    db: Session,
    *,
    game_id: int,
    house_a_id: int,
    house_b_id: int,
) -> GameDeal | None:
    if not game_id or not house_a_id or not house_b_id or house_a_id == house_b_id:
        return None

    deals = (
        db.query(GameDeal)
        .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.status == "alliance_active",
            (
                (
                    (GameDeal.from_house_id == house_a_id)
                    & (GameDeal.to_house_id == house_b_id)
                )
                | (
                    (GameDeal.from_house_id == house_b_id)
                    & (GameDeal.to_house_id == house_a_id)
                )
            ),
        )
        .order_by(GameDeal.id.desc())
        .all()
    )

    for deal in deals:
        offer = deal.offer if isinstance(deal.offer, dict) else {}
        if str(offer.get("type") or "").strip() == "alliance":
            return deal
    return None


def _is_treasurer_shop_request_deal(deal: GameDeal) -> bool:
    offer = deal.offer if isinstance(deal.offer, dict) else {}
    return str(offer.get("type") or "").strip().lower() == "treasurer_shop_request"


@router.get("/me/{player_token}")
def get_player_me(player_token: str):
    db: Session = SessionLocal()

    try:
        player = _resolve_player_by_token(db, player_token)

        if not player:
            return {
                "ok": False,
                "message": "Игрок по токену не найден",
            }

        if _touch_last_seen(player):
            db.commit()
            db.refresh(player)

        active_phases = (
            db.query(GamePhase)
            .filter(
                GamePhase.game_id == player.game_id,
                GamePhase.status == "active",
            )
            .order_by(GamePhase.id.asc())
            .all()
        )
        active_phase_types = {
            str(phase.phase_type or "").strip().lower()
            for phase in active_phases
            if phase.phase_type
        }
        role_code = player.role.code if player.role else None
        is_lord = role_code == "lord_lady"
        is_diplomat = role_code == "diplomat"
        is_treasurer = role_code == "treasurer"
        is_whisper_master = role_code == "whisper_master"
        can_show_deals = is_diplomat and bool(active_phase_types & {"diplomacy", "free_play"})
        can_show_duels = is_lord and "duel" in active_phase_types
        can_show_expedition = bool(role_code) and bool(active_phase_types & {"map", "free_play"})
        can_show_last_whisper = "last_whisper" in active_phase_types

        active_host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == player.game_id,
                GameHostRound.status.in_(["active", "completed_waiting_host"]),
            )
            .order_by(GameHostRound.id.desc())
            .first()
        )

        active_assignments_count = (
            db.query(GameAssignment)
            .filter(
                GameAssignment.player_id == player.id,
                GameAssignment.status == "issued",
            )
            .count()
        )
        active_house_expedition = None
        if can_show_expedition and player.house_id:
            active_house_expedition = _build_active_house_expedition_payload(
                db,
                _get_active_house_expedition(db, player.game_id, player.house_id),
                player_id=player.id,
            )

        incoming_deals = []
        if can_show_deals and player.house_id:
            incoming_deals = [
                deal for deal in (
                db.query(GameDeal)
                .options(
                    joinedload(GameDeal.from_house),
                    joinedload(GameDeal.to_house),
                )
                .filter(
                    GameDeal.game_id == player.game_id,
                    GameDeal.to_house_id == player.house_id,
                    GameDeal.status.in_(["pending", "countered"]),
                )
                .order_by(GameDeal.id.desc())
                .all()
                )
                if not _is_treasurer_shop_request_deal(deal)
            ]

        available_deal_houses = []
        available_duel_houses = []
        if player.house_id and (can_show_deals or can_show_duels):
            other_houses = (
                db.query(House)
                .filter(
                    House.game_id == player.game_id,
                    House.id != player.house_id,
                )
                .order_by(House.id.asc())
                .all()
            )
            available_deal_houses = [
                {
                    "id": house.id,
                    "name": house.name,
                    "house_key": house.house_key,
                }
                for house in other_houses
            ]
            if can_show_duels:
                available_duel_houses = list(available_deal_houses)
            if not can_show_deals:
                available_deal_houses = []

        treasurer_pending_deals = []
        if is_treasurer:
            treasurer_pending_deals = _get_treasurer_pending_deals(db, player)

        active_alliances = []
        if is_lord and player.house_id:
            active_alliances = [
                _serialize_active_alliance(deal, viewer_house_id=player.house_id)
                for deal in _get_active_alliances_for_house(
                    db,
                    game_id=player.game_id,
                    house_id=player.house_id,
                )
            ]

        blocked_crest_pieces = []
        if can_show_deals and player.house_id:
            blocked_crest_pieces = _get_blocked_crest_pieces_for_house(
                db,
                game_id=player.game_id,
                from_house_id=player.house_id,
            )

        active_house_duels = []
        incoming_house_duels = []
        if can_show_duels and player.house_id:
            active_house_duels = _get_house_duels(
                db,
                game_id=player.game_id,
                house_id=player.house_id,
                statuses={"challenged", "accepted", "needs_replay"},
            )
            incoming_house_duels = [
                duel
                for duel in active_house_duels
                if duel.target_house_id == player.house_id and duel.status == "challenged"
            ]

        last_whisper_state = _build_last_whisper_state_for_player(db, player) if can_show_last_whisper else None

        return {
            "ok": True,
            "player": {
                "id": player.id,
                "nickname": player.nickname,
                "player_token": player.player_token,
                "created_at": player.created_at.isoformat() if player.created_at else None,
                "last_seen_at": player.last_seen_at.isoformat() if player.last_seen_at else None,
            },
            "game": {
                "id": player.game.id if player.game else None,
                "room_code": player.game.room_code if player.game else None,
                "title": player.game.title if player.game else None,
            },
            "house": {
                "id": player.house.id,
                "house_key": player.house.house_key,
                "name": player.house.name,
                "motto": player.house.motto,
                "invite_code": player.house.invite_code,
                "resources": _house_resources_dict(player.house),
            } if player.house else None,
            "role": {
                "id": player.role.id,
                "code": player.role.code,
                "name": player.role.name,
            } if player.role else None,
            "active_phases": [
                {
                    "id": phase.id,
                    "phase_type": phase.phase_type,
                    "phase_label": _get_phase_label(phase.phase_type),
                    "status": phase.status,
                    "opened_at": phase.opened_at.isoformat() if phase.opened_at else None,
                }
                for phase in active_phases
            ],
            "active_host_round": {
                "id": active_host_round.id,
                "round_code": active_host_round.round_code,
                "title": active_host_round.title,
                "status": active_host_round.status,
                "current_question_no": active_host_round.current_question_no,
                "questions_total": active_host_round.questions_total,
                "answers_open": active_host_round.answers_open,
            } if active_host_round else None,
            "active_assignments_count": active_assignments_count,
            "active_house_expedition": active_house_expedition,
            "available_deal_houses": available_deal_houses,
            "available_duel_houses": available_duel_houses,
            "incoming_deals": [_serialize_player_deal(deal) for deal in incoming_deals],
            "treasurer_pending_deals": [_serialize_player_deal(deal) for deal in treasurer_pending_deals],
            "active_alliances": active_alliances,
            "blocked_crest_pieces": blocked_crest_pieces,
            "active_house_duels": [_serialize_player_duel(duel) for duel in active_house_duels],
            "incoming_house_duels": [_serialize_player_duel(duel) for duel in incoming_house_duels],
            "whisper_feed": _build_whisper_feed(db, player),
            "last_whisper": last_whisper_state,
        }

    finally:
        db.close()


@router.get("/me/{player_token}/assignments")
def get_player_assignments(player_token: str):
    db: Session = SessionLocal()

    try:
        player = _resolve_player_by_token(db, player_token)

        if not player:
            return {
                "ok": False,
                "message": "Игрок по токену не найден",
            }

        assignments = (
            db.query(GameAssignment)
            .options(
                joinedload(GameAssignment.template_task),
                joinedload(GameAssignment.host_round),
                joinedload(GameAssignment.host_round_question),
            )
            .filter(GameAssignment.player_id == player.id)
            .order_by(GameAssignment.id.desc())
            .all()
        )

        issued = [a for a in assignments if a.status == "issued"]
        answered = [a for a in assignments if a.status in ["answered", "resolved", "applied"]]
        expired = [a for a in assignments if a.status == "expired"]

        return {
            "ok": True,
            "player": {
                "id": player.id,
                "nickname": player.nickname,
                "role_code": player.role.code if player.role else None,
                "role_name": player.role.name if player.role else None,
            },
            "counts": {
                "all": len(assignments),
                "issued": len(issued),
                "answered": len(answered),
                "expired": len(expired),
            },
            "assignments": {
                "issued": [_serialize_assignment(a) for a in issued],
                "answered": [_serialize_assignment(a) for a in answered],
                "expired": [_serialize_assignment(a) for a in expired],
            },
        }

    finally:
        db.close()


@router.post("/me/{player_token}/ensure-token")
def ensure_token_for_player(player_token: str):
    db: Session = SessionLocal()

    try:
        player = _resolve_player_by_token(db, player_token)

        if not player:
            return {
                "ok": False,
                "message": "Игрок по токену не найден",
            }

        token_value = _ensure_player_token(db, player)
        _touch_last_seen(player)

        db.commit()
        db.refresh(player)

        return {
            "ok": True,
            "player_id": player.id,
            "player_token": token_value,
        }

    finally:
        db.close()


@router.post("/explore/{player_id}")
def explore_map(player_id: int):
    db: Session = SessionLocal()

    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        if not player.house:
            raise HTTPException(status_code=400, detail="У игрока не найден Дом")

        existing_resolved = (
            db.query(GameExpedition)
            .filter(
                GameExpedition.game_id == player.game_id,
                GameExpedition.house_id == player.house_id,
                GameExpedition.status == "resolved",
            )
            .order_by(GameExpedition.id.desc())
            .first()
        )

        if existing_resolved:
            return {
                "ok": False,
                "message": "Ваш Дом уже отправил экспедицию в этой фазе",
            }

        expedition = GameExpedition(
            game_id=player.game_id,
            house_id=player.house_id,
            status="planned",
            target_location_code="test_location",
        )
        setattr(expedition, "target_location_name", "Тестовая точка")

        events_pool = [
            {"text": "нашли золото", "effect": "gold", "value": 2},
            {"text": "попали в засаду", "effect": "influence", "value": -1},
            {"text": "нашли древний свиток", "effect": "scroll", "value": 1},
            {"text": "ничего не нашли", "effect": "none", "value": 0},
        ]
        event = random.choice(events_pool)

        if event["effect"] == "gold":
            player.house.resource_gold += event["value"]
        elif event["effect"] == "influence":
            player.house.resource_influence = max(0, player.house.resource_influence + event["value"])
        elif event["effect"] == "scroll":
            player.house.resource_scroll += event["value"]

        setattr(expedition, "result_text", event["text"])

        db.add(expedition)
        db.flush()

        map_visit = GameMapVisit(
            game_id=player.game_id,
            house_id=player.house_id,
            triggered_by_player_id=player.id,
            location_code="test_location",
            visit_no_for_house=(
                db.query(GameMapVisit)
                .filter(
                    GameMapVisit.game_id == player.game_id,
                    GameMapVisit.house_id == player.house_id,
                )
                .count()
            ) + 1,
            outcome_type=event["effect"],
            outcome_text=event["text"],
        )
        db.add(map_visit)
        db.commit()
        db.refresh(expedition)

        return {
            "ok": True,
            "message": "Экспедиция отправлена",
            "expedition_id": expedition.id,
            "status": expedition.status,
            "house_id": expedition.house_id,
            "event": event["text"],
        }
    finally:
        db.close()


@router.post("/expedition/create/{player_id}")
def create_expedition(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Тело запроса должно быть JSON-объектом")

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        if not player.house:
            raise HTTPException(status_code=400, detail="У игрока не найден Дом")
        if not player.role or player.role.code != "lord_lady":
            raise HTTPException(status_code=403, detail="Только Лорд / Леди может назначить экспедицию")

        members_count = payload.get("members_count")
        if not isinstance(members_count, int):
            members_count = 0

        validation = _validate_expedition_party_request(
            db,
            house_id=player.house_id,
            members_count=members_count,
            raw_role_codes=payload.get("role_codes"),
        )
        if not validation.get("ok"):
            return validation

        role_codes = validation.get("role_codes") or []

        if role_codes and members_count != len(role_codes):
            return {
                "ok": False,
                "message": "Количество участников должно совпадать с числом выбранных ролей",
            }

        if members_count not in {2, 3, 4, 5, 6}:
            return {
                "ok": False,
                "message": "Выберите состав экспедиции от 2 до 6 участников",
            }

        expedition = _create_expedition(
            db,
            game_id=player.game_id,
            house_id=player.house_id,
        )
        if isinstance(expedition, dict) and not expedition.get("ok", True):
            existing_plan = {"members_count": members_count, "role_codes": role_codes}
            if expedition.get("expedition_id"):
                existing = (
                    db.query(GameExpedition)
                    .filter(GameExpedition.id == expedition["expedition_id"])
                    .first()
                )
                if existing:
                    existing_plan = _get_expedition_plan_meta(db, existing)
            expedition["members_count"] = existing_plan["members_count"]
            expedition["role_codes"] = existing_plan["role_codes"]
            return _fix_text_map(expedition)

        expedition.target_location_code = None
        expedition.leader_player_id = player.id
        db.flush()

        plan_visit_no = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == player.game_id,
                GameMapVisit.house_id == player.house_id,
            )
            .count()
        ) + 1

        db.add(
            GameMapVisit(
                game_id=player.game_id,
                house_id=player.house_id,
                triggered_by_player_id=player.id,
                location_code="expedition_plan",
                visit_no_for_house=plan_visit_no,
                outcome_type="expedition_plan",
                outcome_text="Состав экспедиции назначен",
                meta_json=json.dumps(
                    {
                        "expedition_id": expedition.id,
                        "members_count": members_count,
                        "role_codes": role_codes,
                    },
                    ensure_ascii=False,
                ),
            )
        )
        db.commit()
        db.refresh(expedition)

        return _fix_text_map({
            "ok": True,
            "message": "Экспедиция назначена",
            "expedition_id": expedition.id,
            "members_count": members_count,
            "role_codes": role_codes,
        })
    finally:
        db.close()


@router.post("/expedition/{expedition_id}/choose-location/{player_id}")
def choose_expedition_location(expedition_id: int, player_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Тело запроса должно быть JSON-объектом")

        location_code = _normalize_expedition_location_code(payload.get("location_code"))
        location = _get_catalog_expedition_location(location_code)
        if not location:
            raise HTTPException(status_code=400, detail="Недопустимое направление экспедиции")

        player = (
            db.query(Player)
            .options(joinedload(Player.house), joinedload(Player.role))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")

        expedition = (
            db.query(GameExpedition)
            .filter(GameExpedition.id == expedition_id)
            .first()
        )
        if not expedition:
            raise HTTPException(status_code=404, detail="Экспедиция не найдена")
        if expedition.house_id != player.house_id or expedition.game_id != player.game_id:
            raise HTTPException(status_code=403, detail="Игрок не относится к этой экспедиции")
        if expedition.status not in {"planned", "approved"}:
            raise HTTPException(status_code=400, detail="Экспедиция уже закрыта")

        plan_meta = _get_expedition_plan_meta(db, expedition)
        role_codes = plan_meta.get("role_codes") or []
        if role_codes and (not player.role or player.role.code not in role_codes):
            raise HTTPException(status_code=403, detail="Игрок не входит в состав экспедиции")

        existing_vote = next(
            (
                visit
                for visit in reversed(_get_expedition_vote_visits(db, expedition))
                if visit.triggered_by_player_id == player.id
            ),
            None,
        )

        location_name = fix_encoding(location.get("name") or location_code)

        vote_meta = json.dumps(
            {
                "expedition_id": expedition.id,
                "location_name": location_name,
            },
            ensure_ascii=False,
        )

        if existing_vote:
            existing_vote.location_code = location_code
            existing_vote.outcome_text = "Выбор направления"
            existing_vote.meta_json = vote_meta
        else:
            house_vote_no = (
                db.query(GameMapVisit)
                .filter(
                    GameMapVisit.game_id == player.game_id,
                    GameMapVisit.house_id == player.house_id,
                )
                .count()
            ) + 1

            db.add(
                GameMapVisit(
                    game_id=player.game_id,
                    house_id=player.house_id,
                    triggered_by_player_id=player.id,
                    location_code=location_code,
                    visit_no_for_house=house_vote_no,
                    outcome_type="expedition_vote",
                    outcome_text="Выбор направления",
                    meta_json=vote_meta,
                )
            )

        db.commit()
        db.refresh(expedition)

        summary = _build_active_house_expedition_payload(db, expedition, player_id=player.id)
        return _fix_text_map({
            "ok": True,
            "message": "Выбор направления сохранён",
            "expedition_id": expedition.id,
            "location_code": location_code,
            "location_name": location_name,
            "choices_count": summary["choices_count"] if summary else 0,
            "unique_locations_count": summary["unique_locations_count"] if summary else 0,
        })
    finally:
        db.close()


@router.post("/expedition/{expedition_id}/resolve/{player_id}")
def resolve_expedition(expedition_id: int, player_id: int):
    db: Session = SessionLocal()

    try:
        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            raise HTTPException(status_code=404, detail="Игрок не найден")
        if not player.role or player.role.code != "lord_lady":
            raise HTTPException(status_code=403, detail="Только Лорд / Леди может завершить экспедицию")

        expedition = (
            db.query(GameExpedition)
            .options(joinedload(GameExpedition.house))
            .filter(GameExpedition.id == expedition_id)
            .first()
        )
        if not expedition:
            raise HTTPException(status_code=404, detail="Экспедиция не найдена")
        if expedition.house_id != player.house_id or expedition.game_id != player.game_id:
            raise HTTPException(status_code=403, detail="Это не экспедиция вашего Дома")
        if expedition.status not in {"planned", "approved"}:
            raise HTTPException(status_code=400, detail="Экспедиция уже завершена")

        vote_visits = _get_expedition_vote_visits(db, expedition)
        plan_meta = _get_expedition_plan_meta(db, expedition)
        members_count = plan_meta.get("members_count") or 0
        role_codes = plan_meta.get("role_codes") or []
        lord_vote = next(
            (
                visit
                for visit in reversed(vote_visits)
                if visit.triggered_by_player_id == player.id and visit.location_code
            ),
            None,
        )

        if "lord_lady" in role_codes and not lord_vote:
            return _fix_text_map({
                "ok": False,
                "message": "Сначала Лорд должен выбрать маршрут экспедиции",
            })

        if members_count > 0 and len(vote_visits) < members_count:
            return _fix_text_map({
                "ok": False,
                "message": "Экспедиция ещё не собрала назначенный состав",
            })

        vote_counts = {}
        location_names = {}
        for visit in vote_visits:
            if not visit.location_code:
                continue
            meta = _load_meta_json(getattr(visit, "meta_json", None))
            vote_counts[visit.location_code] = vote_counts.get(visit.location_code, 0) + 1
            location_names[visit.location_code] = meta.get("location_name") or _location_name_by_code(visit.location_code) or visit.location_code

        chosen_locations = list(vote_counts.keys())
        unique_locations_count = len(chosen_locations)
        vote_counts_display = [
            {
                "location_code": location_code,
                "location_name": location_names.get(location_code) or location_code,
                "count": count,
            }
            for location_code, count in sorted(vote_counts.items(), key=lambda item: (-item[1], item[0]))
        ]

        success = bool(vote_counts_display) and unique_locations_count == 1
        reward = {}
        penalty = {}
        resources_after = _house_resources_snapshot(expedition.house) if expedition.house else {}
        location_name = None
        outcome_text = None
        role_bonus = False
        preferred_roles = []

        if success:
            chosen_location_code = vote_counts_display[0]["location_code"]
            location_name = vote_counts_display[0]["location_name"]
            catalog = _load_expedition_locations_catalog()
            location = catalog.get(chosen_location_code)
            if not location:
                raise HTTPException(status_code=400, detail="Локация экспедиции не найдена в каталоге")

            outcome = _weighted_pick_outcome(location.get("outcomes", []))
            outcome_text = fix_encoding(outcome.get("text") or "Экспедиция достигла цели.")
            reward = _normalize_resource_delta_map(outcome.get("reward"))
            penalty = _normalize_resource_delta_map(outcome.get("penalty"))
            reward, penalty = _rebalance_expedition_outcome(location, reward, penalty)
            preferred_roles = list(location.get("preferred_roles") or [])
            preferred_roles_set = set(preferred_roles)

            if preferred_roles_set and set(role_codes).intersection(preferred_roles_set):
                if reward:
                    if "gold" in reward:
                        reward["gold"] += 1
                    elif "influence" in reward:
                        reward["influence"] += 1
                    elif "scroll" in reward:
                        reward["scroll"] += 1
                    else:
                        reward["gold"] = 1
                else:
                    reward["gold"] = 1

                if "gold" in penalty and penalty["gold"] < 0:
                    penalty["gold"] = min(0, penalty["gold"] + 1)
                    if penalty["gold"] == 0:
                        penalty.pop("gold", None)
                if "influence" in penalty and penalty["influence"] < 0:
                    penalty["influence"] = min(0, penalty["influence"] + 1)
                    if penalty["influence"] == 0:
                        penalty.pop("influence", None)

                role_bonus = True

            reward, penalty = _rebalance_expedition_outcome(location, reward, penalty)

            reward, outcome_text = _apply_location_pressure(
                db,
                game_id=expedition.game_id,
                location_code=chosen_location_code,
                reward=reward,
                outcome_text=outcome_text,
            )

            applied_reward = _apply_house_resource_deltas(expedition.house, reward) if expedition.house else {}
            applied_penalty = _apply_house_resource_deltas(expedition.house, penalty) if expedition.house else {}
            reward = {key: value for key, value in applied_reward.items() if value > 0}
            penalty = {key: value for key, value in applied_penalty.items() if value < 0}
            resources_after = _house_resources_snapshot(expedition.house) if expedition.house else {}

            expedition.status = "resolved"
            expedition.target_location_code = chosen_location_code
            result_message = fix_encoding(f"Дом дошёл до точки: {location_name}")
            result_type = "map_success"
        else:
            expedition.status = "resolved"
            expedition.target_location_code = None
            if expedition.house:
                resources_after = _house_resources_snapshot(expedition.house)
            result_message = fix_encoding("Экспедиция разошлась по разным дорогам и не достигла цели")
            outcome_text = result_message
            result_type = "map_fail"

        result_visit_no = (
            db.query(GameMapVisit)
            .filter(
                GameMapVisit.game_id == expedition.game_id,
                GameMapVisit.house_id == expedition.house_id,
            )
            .count()
        ) + 1

        db.add(
            GameMapVisit(
                game_id=expedition.game_id,
                house_id=expedition.house_id,
                triggered_by_player_id=player.id,
                location_code=expedition.target_location_code or "mixed_route",
                visit_no_for_house=result_visit_no,
                outcome_type=result_type,
                outcome_text=outcome_text or result_message,
                meta_json=json.dumps(
                    {
                        "expedition_id": expedition.id,
                        "members_count": members_count,
                        "role_codes": role_codes,
                        "preferred_roles": preferred_roles,
                        "chosen_locations": chosen_locations,
                        "vote_counts_display": vote_counts_display,
                        "success": success,
                        "location_code": expedition.target_location_code,
                        "location_name": location_name,
                        "outcome_type": result_type,
                        "role_bonus": role_bonus,
                        "reward": reward,
                        "penalty": penalty,
                    },
                    ensure_ascii=False,
                ),
            )
        )

        db.commit()

        return _fix_text_map({
            "ok": True,
            "success": success,
            "message": result_message,
            "location_name": location_name,
            "outcome_text": outcome_text,
            "members_count": members_count,
            "role_codes": role_codes,
            "preferred_roles": preferred_roles,
            "reward": reward,
            "penalty": penalty,
            "role_bonus": role_bonus,
            "vote_counts": vote_counts_display,
            "chosen_locations": chosen_locations,
            "resources_after": resources_after,
        })
    finally:
        db.close()


@router.post("/duels/challenge/{player_id}")
def create_player_duel_challenge(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.house:
            return {"ok": False, "message": "У игрока не найден Дом"}
        if not player.role or player.role.code != "lord_lady":
            return {"ok": False, "message": "Только Лорд/Леди может бросать и принимать вызовы."}

        target_house_id = payload.get("target_house_id")
        if not isinstance(target_house_id, int):
            return {"ok": False, "message": "Выберите Дом, которому хотите бросить вызов"}

        result = _create_duel_challenge(
            db=db,
            game_id=player.game_id,
            challenger_house_id=player.house_id,
            target_house_id=target_house_id,
            payload=payload,
        )
        if not result.get("ok"):
            db.rollback()
            return _fix_text_map(result)

        db.commit()
        return _fix_text_map(result)
    finally:
        db.close()


@router.post("/duels/accept/{player_id}/{duel_id}")
def accept_player_duel(player_id: int, duel_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None or not isinstance(payload, dict):
            payload = {}

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.house:
            return {"ok": False, "message": "У игрока не найден Дом"}
        if not player.role or player.role.code != "lord_lady":
            return {"ok": False, "message": "Только Лорд/Леди может бросать и принимать вызовы."}

        duel = (
            db.query(GameDuel)
            .options(
                joinedload(GameDuel.challenger_house),
                joinedload(GameDuel.target_house),
                joinedload(GameDuel.winner_house),
            )
            .filter(
                GameDuel.id == duel_id,
                GameDuel.game_id == player.game_id,
            )
            .first()
        )
        if not duel:
            return {"ok": False, "message": "Дуэль не найдена"}
        if duel.target_house_id != player.house_id:
            return {"ok": False, "message": "Принять или отклонить вызов может только Лорд/Леди Дома-цели."}

        result = _accept_duel(db=db, duel=duel, payload=payload)
        if not result.get("ok"):
            db.rollback()
            return _fix_text_map(result)

        db.commit()
        return _fix_text_map(result)
    finally:
        db.close()


@router.post("/duels/refuse/{player_id}/{duel_id}")
def refuse_player_duel(player_id: int, duel_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None or not isinstance(payload, dict):
            payload = {}

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.house:
            return {"ok": False, "message": "У игрока не найден Дом"}
        if not player.role or player.role.code != "lord_lady":
            return {"ok": False, "message": "Только Лорд/Леди может бросать и принимать вызовы."}

        duel = (
            db.query(GameDuel)
            .options(
                joinedload(GameDuel.challenger_house),
                joinedload(GameDuel.target_house),
                joinedload(GameDuel.winner_house),
            )
            .filter(
                GameDuel.id == duel_id,
                GameDuel.game_id == player.game_id,
            )
            .first()
        )
        if not duel:
            return {"ok": False, "message": "Дуэль не найдена"}
        if duel.target_house_id != player.house_id:
            return {"ok": False, "message": "Принять или отклонить вызов может только Лорд/Леди Дома-цели."}

        result = _refuse_duel(db=db, duel=duel, payload=payload)
        if not result.get("ok"):
            db.rollback()
            return _fix_text_map(result)

        db.commit()
        return _fix_text_map(result)
    finally:
        db.close()


@router.post("/treasurer-shop/{player_id}/purchase")
def purchase_treasurer_shop_item(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.game:
            return {"ok": False, "message": "Игра не найдена"}
        if not player.house:
            return {"ok": False, "message": "У игрока не найден Дом"}
        if not player.role or player.role.code != "treasurer":
            return {
                "ok": False,
                "message": "Только Мастер золота может совершать покупки.",
            }

        action_code = str(payload.get("action_code") or "").strip().lower()
        action_meta = TREASURER_SHOP_ACTIONS.get(action_code)
        if not action_meta or action_code not in TREASURER_SHOP_DIRECT_PURCHASE_ACTIONS:
            return {
                "ok": False,
                "message": "Выберите доступную покупку Мастера золота.",
            }

        target_house = None
        alliance_granted = False
        resources_changed = {}

        if action_meta.get("requires_ally"):
            target_house_id = payload.get("target_house_id")
            if not isinstance(target_house_id, int):
                return {
                    "ok": False,
                    "message": "Выберите союзный Дом для подарка.",
                }
            if target_house_id == player.house_id:
                return {
                    "ok": False,
                    "message": "Подарок союзнику нельзя отправить своему Дому.",
                }
            target_house = (
                db.query(House)
                .filter(
                    House.id == target_house_id,
                    House.game_id == player.game_id,
                )
                .first()
            )
            if not target_house:
                return {
                    "ok": False,
                    "message": "Союзный Дом не найден в этой игре.",
                }
            active_alliance = _find_active_alliance_between_houses(
                db,
                game_id=player.game_id,
                house_a_id=player.house_id,
                house_b_id=target_house.id,
            )
            if not active_alliance:
                return {
                    "ok": False,
                    "message": "Подарок можно отправить только активному союзнику.",
                }

        cost = int(action_meta["cost"])
        actor_name = player.house.name or "Дом"
        ally_name = target_house.name if target_house else ""
        event_text = action_meta["event_text"].format(actor=actor_name, ally=ally_name)

        try:
            spend_result = spend_gold_for_action(
                db,
                house=player.house,
                amount=cost,
                reason=event_text,
                source_type="treasurer_shop",
                performed_by_player_id=player.id,
            )
        except GoldInsufficientFundsError as exc:
            db.rollback()
            return {
                "ok": False,
                "message": "Недостаточно золота для этой покупки.",
                "detail": str(exc),
            }
        except GoldError as exc:
            db.rollback()
            return {
                "ok": False,
                "message": str(exc),
            }

        if action_code == "gift_to_ally" and target_house:
            actor_effect = _apply_house_effect(db, player.house, {"influence": 1})
            ally_effect = _apply_house_effect(db, target_house, {"influence": 1})
            resources_changed = {
                "actor": actor_effect.get("resources_changed") if isinstance(actor_effect, dict) else {},
                "ally": ally_effect.get("resources_changed") if isinstance(ally_effect, dict) else {},
            }
            alliance_granted = True

        db.commit()
        db.refresh(player.house)
        if target_house:
            db.refresh(target_house)

        return _fix_text_map({
            "ok": True,
            "action_code": action_code,
            "house_id": player.house_id,
            "house_name": player.house.name,
            "target_house_id": target_house.id if target_house else None,
            "target_house_name": target_house.name if target_house else None,
            "gold_before": spend_result.balance_before,
            "gold_after": spend_result.balance_after,
            "delta": -cost,
            "event_text": event_text,
            "alliance_granted": alliance_granted,
            "resources_changed": resources_changed,
            "transaction_id": spend_result.transaction_id,
        })
    finally:
        db.close()


@router.post("/treasurer-shop/request/{player_id}")
def create_treasurer_shop_request(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.game:
            return {"ok": False, "message": "Игра не найдена"}
        if not player.house:
            return {"ok": False, "message": "У игрока не найден Дом"}
        if not player.role or player.role.code != "treasurer":
            return {
                "ok": False,
                "message": "Заявку в Харчевню может отправить только Мастер золота.",
            }

        action_code = str(payload.get("action_code") or "").strip().lower()
        action_meta = TREASURER_SHOP_REQUEST_ACTIONS.get(action_code)
        if not action_meta:
            return {
                "ok": False,
                "message": "Выберите доступную позицию Харчевни.",
            }

        deal = GameDeal(
            game_id=player.game_id,
            from_house_id=player.house_id,
            to_house_id=player.house_id,
            status="pending",
            offer={
                "type": "treasurer_shop_request",
                "action_code": action_code,
                "item_label": action_meta["label"],
                "cost_gold": int(action_meta["cost"]),
                "player_id": player.id,
                "is_18_plus": bool(action_meta.get("is_18_plus")),
                "category": str(action_meta.get("category") or ""),
                "requires_bar_confirmation": True,
                "replacement_policy": "manual_only",
            },
            note="Treasurer Shop request: pending cashier review",
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return _fix_text_map({
            "ok": True,
            "request_id": deal.id,
            "status": deal.status,
            "action_code": action_code,
            "item_label": action_meta["label"],
            "cost_gold": int(action_meta["cost"]),
            "house_id": player.house_id,
            "house_name": player.house.name,
            "message": "Заявка отправлена кассиру. Золото пока не списано.",
        })
    finally:
        db.close()


@router.post("/last-whisper/action/{player_id}")
def apply_last_whisper_action(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "РўРµР»Рѕ Р·Р°РїСЂРѕСЃР° РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ JSON-РѕР±СЉРµРєС‚РѕРј",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "РРіСЂРѕРє РЅРµ РЅР°Р№РґРµРЅ"}
        if not player.house:
            return {"ok": False, "message": "РЈ РёРіСЂРѕРєР° РЅРµ РЅР°Р№РґРµРЅ Р”РѕРј"}
        if not player.role or player.role.code != "whisper_master":
            return {"ok": False, "message": "Только Мастер шепота может действовать в этот момент."}

        phase = _get_active_last_whisper_phase(db, player.game_id)
        if not phase:
            return {"ok": False, "message": "Окно Последнего Шёпота сейчас недоступно."}

        action_code = str(payload.get("action_code") or "").strip().lower()
        action_meta = LAST_WHISPER_ACTIONS.get(action_code)
        if not action_meta:
            return {"ok": False, "message": "Выберите одно из доступных действий Мастера шепота."}

        phase_payload = phase.payload if isinstance(phase.payload, dict) else {}
        raw_actions = _get_last_whisper_actions_from_phase(phase)
        for item in raw_actions:
            if item.get("house_id") == player.house_id:
                return {"ok": False, "message": "Мастер шепота уже сделал ход."}

        target_house = None
        target_house_id = payload.get("target_house_id")
        target_deal = None
        target_deal_id = payload.get("target_deal_id")
        target_label = None
        resources_changed = {}

        if action_code == "quiet_support":
            if not isinstance(target_house_id, int):
                return {"ok": False, "message": "Выберите Дом, который получит тайную поддержку."}
            if target_house_id == player.house_id:
                return {"ok": False, "message": "Нельзя направить тайную поддержку своему Дому."}
            target_house = (
                db.query(House)
                .filter(
                    House.id == target_house_id,
                    House.game_id == player.game_id,
                )
                .first()
            )
            if not target_house:
                return {"ok": False, "message": "Целевой Дом не найден в этой игре."}
            effect_result = _apply_house_effect(db, target_house, {"influence": 1})
            resources_changed = effect_result.get("resources_changed") if isinstance(effect_result, dict) else {}
            tv_text = f"{target_house.name} получил +1 влияние благодаря тайной поддержке"
        elif action_code == "crown_tax":
            target_house = _get_single_influence_leader(db, player.game_id)
            if target_house is None:
                tv_text = "Корона не нашла единственного носителя. Влияние не изменилось."
            else:
                effect_result = _apply_house_effect(db, target_house, {"influence": -1})
                resources_changed = effect_result.get("resources_changed") if isinstance(effect_result, dict) else {}
                influence_change = resources_changed.get("influence") if isinstance(resources_changed, dict) else {}
                actual_delta = 0
                if isinstance(influence_change, dict):
                    actual_delta = int(influence_change.get("delta") or 0)
                if actual_delta == -1:
                    tv_text = f"Корона стала тяжелее. {target_house.name} потерял 1 влияние."
                else:
                    zero_target_name = f"Дома {target_house.name[4:]}" if isinstance(target_house.name, str) and target_house.name.startswith("Дом ") else f"Дома {target_house.name}"
                    tv_text = f"Корона стала тяжелее, но влияние {zero_target_name} уже не может быть уменьшено."
        elif action_code == "break_alliance":
            active_alliances = _get_active_alliance_deals(db, game_id=player.game_id)
            if not active_alliances:
                return {"ok": False, "message": "Нет активных союзов для разрыва."}
            if not isinstance(target_deal_id, int):
                return {"ok": False, "message": "Выберите активный союз для разрыва."}
            target_deal = (
                db.query(GameDeal)
                .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
                .filter(
                    GameDeal.id == target_deal_id,
                    GameDeal.game_id == player.game_id,
                )
                .first()
            )
            if not target_deal:
                return {"ok": False, "message": "Выбранный союз не найден в этой игре."}
            target_offer = dict(target_deal.offer) if isinstance(target_deal.offer, dict) else {}
            if target_deal.status != "alliance_active" or str(target_offer.get("type") or "").strip() != "alliance":
                return {"ok": False, "message": "Выбранный союз уже недоступен для разрыва."}
            house_a_name = target_deal.from_house.name if target_deal.from_house else "Дом"
            house_b_name = target_deal.to_house.name if target_deal.to_house else "Дом"
            target_label = fix_encoding(f"{house_a_name} ↔ {house_b_name}")
            target_offer["break_mode"] = "whisper_break"
            target_offer["broken_at"] = datetime.utcnow().isoformat()
            target_offer["broken_by_house_id"] = player.house_id
            target_offer["break_text"] = f"Последний шёпот разрушил союз: {house_a_name} и {house_b_name} больше не связаны договором."
            target_deal.status = "alliance_broken"
            target_deal.offer = target_offer
            target_deal.responded_at = datetime.utcnow()
            db.add(target_deal)
            tv_text = target_offer["break_text"]
        else:
            tv_text = action_meta["tv_text"].format(house_name=player.house.name if player.house else "Дом")

        action_meta = {
            **action_meta,
            "tv_text": tv_text,
        }

        event_payload = {
            "order_no": len(raw_actions) + 1,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "house_id": player.house_id,
            "house_name": player.house.name if player.house else None,
            "target_deal_id": target_deal.id if target_deal else None,
            "target_house_id": target_house.id if target_house else None,
            "target_house_name": target_house.name if target_house else None,
            "target_label": target_label,
            "player_id": player.id,
            "player_name": player.nickname,
            "action_code": action_meta["code"],
            "action_label": action_meta["label"],
            "tv_text": action_meta["tv_text"].format(house_name=player.house.name if player.house else "Дом"),
            "resources_changed": resources_changed,
        }

        phase.payload = {
            **phase_payload,
            "whisper_actions": [*raw_actions, event_payload],
        }
        db.add(phase)
        db.commit()

        return _fix_text_map({
            "ok": True,
            "message": "Ход Мастера шепота зафиксирован.",
            "event": _serialize_last_whisper_action(event_payload),
            "resources_changed": resources_changed,
        })
    finally:
        db.close()


@router.post("/deals/create/{player_id}")
def create_player_deal(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.role), joinedload(Player.house), joinedload(Player.game))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {
                "ok": False,
                "message": "Игрок не найден",
            }
        if not player.house:
            return {
                "ok": False,
                "message": "У игрока не найден Дом",
            }
        if not player.role or player.role.code != "diplomat":
            return {
                "ok": False,
                "message": "Фиксировать договорённости может только Дипломат",
            }
        if not _has_active_phase_types(db, player.game_id, {"diplomacy", "free_play"}):
            return {
                "ok": False,
                "message": "Договорённости можно фиксировать только на этапе дипломатии",
            }

        target_house_id = payload.get("target_house_id")
        deal_type = str(payload.get("deal_type") or "").strip()
        resource_type = str(payload.get("resource_type") or "").strip().lower()
        crest_piece = fix_encoding(str(payload.get("crest_piece") or "").strip())
        offer_text = fix_encoding(str(payload.get("offer_text") or "").strip())
        resource_amount_raw = payload.get("resource_amount")

        try:
            resource_amount = int(resource_amount_raw) if resource_amount_raw not in (None, "") else None
        except Exception:
            resource_amount = None

        if not isinstance(target_house_id, int):
            return {
                "ok": False,
                "message": "Выберите Дом для договорённости",
            }
        if not deal_type:
            return {
                "ok": False,
                "message": "Выберите тип договорённости",
            }
        if deal_type == "resource":
            if not resource_type:
                return {
                    "ok": False,
                    "message": "Выберите ресурс",
                }
            if resource_type not in V1_DIPLOMACY_RESOURCE_TYPES:
                return _fix_text_map({
                    "ok": False,
                    "message": "В этой версии для договорённостей доступны только золото и влияние.",
                    "allowed_resource_types": sorted(V1_DIPLOMACY_RESOURCE_TYPES),
                })
            if resource_amount is None or resource_amount <= 0:
                return {
                    "ok": False,
                    "message": "Укажите количество ресурса",
                }
        elif deal_type == "crest_piece":
            if not crest_piece:
                return {
                    "ok": False,
                    "message": "Опишите кусок герба",
                }
        elif deal_type == "open_agreement":
            if not offer_text:
                return {
                    "ok": False,
                    "message": "Опишите суть договорённости",
                }
        elif deal_type == "alliance":
            offer_text = offer_text or "Союз домов"
        else:
            return {
                "ok": False,
                "message": "Неизвестный тип договорённости",
            }
        if target_house_id == player.house_id:
            return {
                "ok": False,
                "message": "Нельзя заключить сделку с собственным Домом",
            }

        target_house = (
            db.query(House)
            .filter(
                House.game_id == player.game_id,
                House.id == target_house_id,
            )
            .first()
        )
        if not target_house:
            return {
                "ok": False,
                "message": "Дом для договорённости не найден",
            }

        if deal_type == "alliance":
            house_ids = [player.house_id, target_house_id]
            active_alliance = _find_alliance_conflict(
                db,
                game_id=player.game_id,
                house_ids=house_ids,
                statuses={"alliance_active"},
            )
            if active_alliance:
                return {
                    "ok": False,
                    "message": "Один Дом может иметь только один активный союз",
                }

            pending_or_active_alliance = _find_alliance_conflict(
                db,
                game_id=player.game_id,
                house_ids=house_ids,
                statuses={"pending", "alliance_active"},
            )
            if pending_or_active_alliance:
                return {
                    "ok": False,
                    "message": "У одного из Домов уже есть активный или ожидающий союз",
                }

        offer_payload = {
            "type": deal_type,
            "resource_type": resource_type or None,
            "resource_amount": resource_amount,
            "crest_piece": crest_piece or None,
            "text": offer_text,
        }
        duplicate_deal = _find_duplicate_outgoing_deal(
            db,
            game_id=player.game_id,
            from_house_id=player.house_id,
            to_house_id=target_house_id,
            offer_payload=offer_payload,
        )
        if duplicate_deal:
            return _fix_text_map({
                "ok": False,
                "message": "Такая договорённость уже зафиксирована и ещё не закрыта.",
                "duplicate_deal_id": duplicate_deal.id,
            })

        if deal_type == "crest_piece":
            crest_conflict = _find_promised_crest_piece_conflict(
                db,
                game_id=player.game_id,
                from_house_id=player.house_id,
                crest_piece=crest_piece,
            )
            if crest_conflict:
                return _fix_text_map({
                    "ok": False,
                    "message": "Этот кусок герба уже обещан в другой договорённости.",
                    "duplicate_deal_id": crest_conflict.id,
                })

        if deal_type == "resource":
            resource_conflict = _find_promised_resource_conflict(
                db,
                game_id=player.game_id,
                from_house_id=player.house_id,
                to_house_id=target_house_id,
                resource_type=resource_type,
                resource_amount=resource_amount,
            )
            if resource_conflict:
                return _fix_text_map({
                    "ok": False,
                    "message": "Такой ресурс уже обещан в незакрытой договорённости.",
                    "duplicate_deal_id": resource_conflict.id,
                })
        human_offer_text = _format_deal_offer_text(offer_payload, None)

        deal = GameDeal(
            game_id=player.game_id,
            from_house_id=player.house_id,
            to_house_id=target_house_id,
            status="pending",
            offer=offer_payload,
            note=human_offer_text,
        )
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return _fix_text_map({
            "ok": True,
            "message": "Договорённость зафиксирована",
            "deal": _serialize_player_deal(deal),
        })
    finally:
        db.close()


@router.post("/deals/respond/{player_id}")
def respond_player_deal(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.house), joinedload(Player.role))
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "ok": False,
                "message": "Игрок не найден",
            }

        if not player.house_id:
            return {
                "ok": False,
                "message": "У игрока не найден Дом",
            }

        deal_id = payload.get("deal_id")
        action = str(payload.get("action") or "").strip().lower()

        if not deal_id:
            return {
                "ok": False,
                "message": "Не указана сделка",
            }

        if action not in {"accept", "reject"}:
            return {
                "ok": False,
                "message": "Нужно выбрать действие по сделке",
            }

        deal = (
            db.query(GameDeal)
            .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
            .filter(
                GameDeal.id == deal_id,
                GameDeal.game_id == player.game_id,
            )
            .first()
        )

        if not deal:
            return {
                "ok": False,
                "message": "Сделка не найдена",
            }

        if deal.to_house_id != player.house_id:
            return {
                "ok": False,
                "message": "Вы не можете отвечать на эту договорённость",
            }

        if deal.status not in DEAL_ACTIONABLE_RESPONSE_STATUSES:
            return _fix_text_map({
                "ok": False,
                "message": "Эта договорённость уже обработана и не принимает повторный ответ.",
                "deal_status": deal.status,
            })

        offer_type = ""
        if isinstance(deal.offer, dict):
            offer_type = str(deal.offer.get("type") or "").strip()

        if action == "accept":
            if offer_type == "resource":
                deal.status = "accepted_waiting_treasurer"
                message = "Сделка принята. Ожидает подтверждения Мастера над золотом"
            elif offer_type == "alliance":
                house_ids = [deal.from_house_id, deal.to_house_id]
                active_alliance = _find_alliance_conflict(
                    db,
                    game_id=player.game_id,
                    house_ids=house_ids,
                    statuses={"alliance_active"},
                    exclude_deal_id=deal.id,
                )
                if active_alliance:
                    return _fix_text_map({
                        "ok": False,
                        "message": "Один Дом может иметь только один активный союз",
                    })

                deal.status = "alliance_active"
                offer = dict(deal.offer) if isinstance(deal.offer, dict) else {}
                existing_applied_to = offer.get("alliance_bonus_applied_to")
                applied_to: list[int] = (
                    [house_id for house_id in existing_applied_to if isinstance(house_id, int)]
                    if isinstance(existing_applied_to, list)
                    else []
                )
                if offer.get("alliance_bonus_applied") and not applied_to:
                    applied_to = [house_id for house_id in house_ids if isinstance(house_id, int)]
                if not offer.get("alliance_bonus_applied"):
                    prior_bonus_houses = _get_houses_with_alliance_bonus_history(
                        db,
                        game_id=player.game_id,
                        house_ids=house_ids,
                        exclude_deal_id=deal.id,
                    )
                    if deal.from_house and deal.from_house_id not in prior_bonus_houses:
                        _apply_house_resource_deltas(deal.from_house, {"influence": 1})
                        applied_to.append(deal.from_house_id)
                    if deal.to_house and deal.to_house_id not in prior_bonus_houses:
                        _apply_house_resource_deltas(deal.to_house, {"influence": 1})
                        applied_to.append(deal.to_house_id)
                    offer["alliance_bonus_applied"] = True
                offer["alliance_bonus_applied_to"] = applied_to
                offer["activated_at"] = datetime.utcnow().isoformat()
                offer["alliance_bonus"] = {"influence": 1}
                if len(applied_to) >= 2:
                    offer["bonus_text"] = "+1 влияние обоим Домам"
                elif len(applied_to) == 1:
                    offer["bonus_text"] = "+1 влияние одному из Домов"
                else:
                    offer["bonus_text"] = "Бонус союза уже был использован"
                deal.offer = offer
                message = "Союз заключён"
            else:
                deal.status = "accepted"
                message = "Ответ по договорённости сохранён"
        else:
            deal.status = "rejected"
            message = "Ответ по договорённости сохранён"
        deal.responded_at = datetime.utcnow()
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return _fix_text_map({
            "ok": True,
            "message": message,
            "deal": _serialize_player_deal(deal),
        })
    finally:
        db.close()


@router.post("/alliances/break/{player_id}")
def break_alliance(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.house), joinedload(Player.role))
            .filter(Player.id == player_id)
            .first()
        )
        if not player:
            return {"ok": False, "message": "Игрок не найден"}
        if not player.role or player.role.code != "lord_lady":
            return {"ok": False, "message": "Разорвать союз может только Лорд / Леди"}
        if not player.house_id:
            return {"ok": False, "message": "У игрока не найден Дом"}

        deal_id = payload.get("deal_id")
        mode = str(payload.get("mode") or "").strip()
        if mode not in {"peaceful_break", "betrayal"}:
            return {"ok": False, "message": "Выберите способ разрыва союза"}

        deal = (
            db.query(GameDeal)
            .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
            .filter(GameDeal.id == deal_id, GameDeal.game_id == player.game_id)
            .first()
        )
        if not deal:
            return {"ok": False, "message": "Сделка не найдена"}
        if deal.status != "alliance_active":
            return {"ok": False, "message": "Этот союз уже не активен"}
        if player.house_id not in {deal.from_house_id, deal.to_house_id}:
            return {"ok": False, "message": "Вы не можете разорвать чужой союз"}

        breaker_house = deal.from_house if deal.from_house_id == player.house_id else deal.to_house
        other_house = deal.to_house if deal.from_house_id == player.house_id else deal.from_house
        offer = dict(deal.offer) if isinstance(deal.offer, dict) else {}
        offer["break_mode"] = mode
        offer["broken_at"] = datetime.utcnow().isoformat()
        offer["broken_by_house_id"] = breaker_house.id if breaker_house else player.house_id
        offer["other_house_id"] = other_house.id if other_house else None

        if mode == "peaceful_break":
            deal.status = "alliance_broken"
            offer["break_text"] = "Союз разорван по решению Дома"
            message = offer["break_text"]
        else:
            deal.status = "alliance_betrayed"
            if breaker_house:
                _apply_house_resource_deltas(breaker_house, {"gold": 1, "influence": -1})
            if other_house:
                _apply_house_resource_deltas(other_house, {"influence": 1})
            offer["betrayal_effect"] = {
                "breaker": {"gold": 1, "influence": -1},
                "other": {"influence": 1},
            }
            offer["break_text"] = "Союз предан. Предатель получает золото, но теряет влияние. Второй Дом получает влияние."
            message = offer["break_text"]

        deal.offer = offer
        deal.responded_at = datetime.utcnow()
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return _fix_text_map({
            "ok": True,
            "message": message,
            "deal": _serialize_player_deal(deal),
            "active_alliances": [
                _serialize_active_alliance(item, viewer_house_id=player.house_id)
                for item in _get_active_alliances_for_house(
                    db,
                    game_id=player.game_id,
                    house_id=player.house_id,
                )
            ],
            "breaker_house_resources": _house_resources_snapshot(breaker_house) if breaker_house else {},
            "other_house_resources": _house_resources_snapshot(other_house) if other_house else {},
        })
    finally:
        db.close()


@router.post("/deals/treasurer-confirm/{player_id}")
def treasurer_confirm_deal(player_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player = (
            db.query(Player)
            .options(joinedload(Player.house), joinedload(Player.role))
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "ok": False,
                "message": "Игрок не найден",
            }
        if not player.house:
            return {
                "ok": False,
                "message": "У игрока не найден Дом",
            }
        if not player.role or player.role.code != "treasurer":
            return {
                "ok": False,
                "message": "Подтверждать сделку может только Мастер над золотом",
            }

        deal_id = payload.get("deal_id")
        action = str(payload.get("action") or "").strip().lower()

        if not deal_id:
            return {
                "ok": False,
                "message": "Не указана сделка",
            }
        if action not in {"confirm", "reject"}:
            return {
                "ok": False,
                "message": "Нужно выбрать действие по сделке",
            }

        deal = (
            db.query(GameDeal)
            .options(joinedload(GameDeal.from_house), joinedload(GameDeal.to_house))
            .filter(
                GameDeal.id == deal_id,
                GameDeal.game_id == player.game_id,
            )
            .first()
        )

        if not deal:
            return {
                "ok": False,
                "message": "Сделка не найдена",
            }
        if deal.from_house_id != player.house_id:
            return {
                "ok": False,
                "message": "Вы не можете подтверждать эту сделку",
            }
        if deal.status != "accepted_waiting_treasurer":
            return {
                "ok": False,
                "message": "Сделка не ожидает подтверждения Мастера над золотом",
            }

        offer = deal.offer if isinstance(deal.offer, dict) else {}
        if str(offer.get("type") or "").strip() != "resource":
            return {
                "ok": False,
                "message": "Подтверждение требуется только для ресурсной сделки",
            }

        if action == "reject":
            deal.status = "treasurer_rejected"
            deal.responded_at = datetime.utcnow()
            db.add(deal)
            db.commit()
            db.refresh(deal)
            return _fix_text_map({
                "ok": True,
                "message": "Мастер над золотом отклонил сделку",
                "deal": _serialize_player_deal(deal),
            })

        resource_type = str(offer.get("resource_type") or "").strip()
        resource_amount = offer.get("resource_amount")
        if resource_type not in {"gold", "influence", "stone", "wood", "iron", "scroll", "key", "fire"}:
            return {
                "ok": False,
                "message": "В сделке указан некорректный ресурс",
            }
        if not isinstance(resource_amount, int) or resource_amount <= 0:
            return {
                "ok": False,
                "message": "В сделке указано некорректное количество ресурса",
            }
        if not deal.from_house or not deal.to_house:
            return {
                "ok": False,
                "message": "У сделки не найден Дом-отправитель или Дом-получатель",
            }

        from_before = _house_resources_snapshot(deal.from_house)
        if (from_before.get(resource_type) or 0) < resource_amount:
            return {
                "ok": False,
                "message": "Недостаточно ресурса для подтверждения сделки",
            }

        from_delta = _apply_house_resource_deltas(deal.from_house, {resource_type: -resource_amount})
        to_delta = _apply_house_resource_deltas(deal.to_house, {resource_type: resource_amount})

        deal.status = "completed"
        deal.responded_at = datetime.utcnow()
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return _fix_text_map({
            "ok": True,
            "message": "Сделка подтверждена и исполнена",
            "deal": _serialize_player_deal(deal),
            "from_house_resources": _house_resources_snapshot(deal.from_house),
            "to_house_resources": _house_resources_snapshot(deal.to_house),
            "transferred": {
                "resource_type": resource_type,
                "resource_amount": resource_amount,
                "from_delta": from_delta,
                "to_delta": to_delta,
            },
        })
    finally:
        db.close()


@router.post("/assignments/{assignment_id}/answer")
def answer_assignment(
    assignment_id: int,
    payload: dict = Body(...),
):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player_token = payload.get("player_token")
        answer_payload = payload.get("answer_payload")

        if not player_token:
            return {
                "ok": False,
                "message": 'Поле "player_token" обязательно',
            }

        if answer_payload is None:
            return {
                "ok": False,
                "message": 'Поле "answer_payload" обязательно',
            }

        player = _resolve_player_by_token(db, player_token)

        if not player:
            return {
                "ok": False,
                "message": "Игрок по токену не найден",
            }

        assignment = (
            db.query(GameAssignment)
            .options(
                joinedload(GameAssignment.player),
                joinedload(GameAssignment.template_task),
                joinedload(GameAssignment.host_round),
                joinedload(GameAssignment.host_round_question),
            )
            .filter(GameAssignment.id == assignment_id)
            .first()
        )

        if not assignment:
            return {
                "ok": False,
                "message": "Assignment не найден",
                "assignment_id": assignment_id,
            }

        if assignment.player_id != player.id:
            return {
                "ok": False,
                "message": "Этот assignment выдан другому игроку",
                "assignment_id": assignment_id,
                "player_id": player.id,
            }

        result = _process_assignment_answer(
            db=db,
            assignment=assignment,
            payload=answer_payload,
            load_json_text_fn=_load_json_text,
            dump_json_fn=_dump_json,
            apply_house_effect_fn=_apply_house_effect,
            build_house_resources_snapshot_fn=_build_house_resources_snapshot,
            open_next_question_for_host_round_fn=_open_next_question_for_host_round,
        )
        _touch_last_seen(player)

        db.commit()
        db.refresh(assignment)

        return {
            "ok": True,
            "message": "Ответ игрока принят",
            "player": {
                "id": player.id,
                "nickname": player.nickname,
            },
            "assignment": _serialize_assignment(result["assignment"]),
            "result_payload": _sanitize_assignment_result_payload_object(
                result["result_payload"],
                runtime_question=getattr(result["assignment"], "host_round_question", None),
            ),
            "house_resources_after": result["house_resources_after"],
        }

    except ValueError as e:
        db.rollback()
        return {
            "ok": False,
            "message": str(e),
            "assignment_id": assignment_id,
        }
    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Ошибка при обработке ответа игрока",
            "details": str(e),
            "assignment_id": assignment_id,
        }
    finally:
        db.close()
