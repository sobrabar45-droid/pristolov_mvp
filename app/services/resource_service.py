from sqlalchemy.orm import Session

from app.models.house import House
from app.models.game_deal import GameDeal
from app.services.gold_service import (
    apply_expedition_gold_outcome,
    transfer_gold_between_houses,
)


def apply_house_effect(db: Session, house: House, effect_data):
    if not isinstance(effect_data, dict):
        return {
            "applied": False,
            "reason": "effect_data is not dict",
            "resources_changed": {},
        }

    resource_map = {
        "influence": "resource_influence",
        "stone": "resource_stone",
        "wood": "resource_wood",
        "iron": "resource_iron",
        "scroll": "resource_scroll",
        "key": "resource_key",
        "fire": "resource_fire",
    }

    resources_changed = {}

    gold_delta = effect_data.get("gold")

    if isinstance(gold_delta, int) and gold_delta != 0:
        result = apply_expedition_gold_outcome(
            db=db,
            house=house,
            gold_delta=gold_delta,
            reason="Результат экспедиции",
        )

        gold_before = getattr(result, "gold_before", None)
        if gold_before is None:
            gold_before = getattr(result, "balance_before", None)

        gold_after = getattr(result, "gold_after", None)
        if gold_after is None:
            gold_after = getattr(result, "balance_after", None)

        resources_changed["gold"] = {
            "old": gold_before,
            "delta": gold_delta,
            "new": gold_after,
        }

    for public_key, model_field in resource_map.items():
        delta = effect_data.get(public_key)

        if delta is None:
            continue

        if not isinstance(delta, int):
            continue

        old_value = getattr(house, model_field, 0)
        raw_new_value = old_value + delta

        if raw_new_value < 0:
            new_value = 0
        else:
            new_value = raw_new_value

        actual_delta = new_value - old_value

        setattr(house, model_field, new_value)

        resources_changed[public_key] = {
            "old": old_value,
            "delta": actual_delta,
            "requested_delta": delta,
            "new": new_value,
            "clamped_to_zero": raw_new_value < 0,
        }

    return {
        "applied": len(resources_changed) > 0,
        "reason": None if len(resources_changed) > 0 else "no resource deltas applied",
        "resources_changed": resources_changed,
    }


def apply_transfer_between_houses(
    db: Session,
    from_house: House,
    to_house: House,
    offer_data,
    source_type: str = "deal",
    source_id: int | None = None,
    reason: str = "Перенос ресурсов между домами",
    performed_by_player_id: int | None = None,
):
    if not isinstance(offer_data, dict):
        return {
            "ok": False,
            "message": "offer_data должен быть объектом",
            "transferred": {},
        }

    resource_map = {
        "influence": "resource_influence",
        "stone": "resource_stone",
        "wood": "resource_wood",
        "iron": "resource_iron",
        "scroll": "resource_scroll",
        "key": "resource_key",
        "fire": "resource_fire",
    }

    transferred = {}

    gold_delta = offer_data.get("gold")

    if gold_delta is not None:
        if not isinstance(gold_delta, int):
            return {
                "ok": False,
                "message": 'Количество ресурса "gold" должно быть целым числом',
                "transferred": transferred,
            }

        if gold_delta < 0:
            return {
                "ok": False,
                "message": 'В offer недопустимо отрицательное значение для "gold"',
                "transferred": transferred,
            }

        if gold_delta > 0:
            from_old = getattr(from_house, "resource_gold", 0)
            to_old = getattr(to_house, "resource_gold", 0)

            if from_old < gold_delta:
                return {
                    "ok": False,
                    "message": f'У дома "{from_house.name}" недостаточно ресурса "gold"',
                    "transferred": transferred,
                }

            try:
                gold_transfer_result = transfer_gold_between_houses(
                    db=db,
                    from_house=from_house,
                    to_house=to_house,
                    amount=gold_delta,
                    source_type=source_type,
                    source_id=source_id,
                    reason=reason,
                    performed_by_player_id=performed_by_player_id,
                )
            except Exception as e:
                return {
                    "ok": False,
                    "message": f'Не удалось перенести gold: {str(e)}',
                    "transferred": transferred,
                }

            transferred["gold"] = {
                "from_old": from_old,
                "from_new": gold_transfer_result["from_house"].balance_after,
                "to_old": to_old,
                "to_new": gold_transfer_result["to_house"].balance_after,
                "delta": gold_delta,
                "source_type": source_type,
                "source_id": source_id,
            }

    for public_key, field_name in resource_map.items():
        delta = offer_data.get(public_key)

        if delta is None:
            continue

        if not isinstance(delta, int):
            return {
                "ok": False,
                "message": f'Количество ресурса "{public_key}" должно быть целым числом',
                "transferred": transferred,
            }

        if delta < 0:
            return {
                "ok": False,
                "message": f'В offer недопустимо отрицательное значение для "{public_key}"',
                "transferred": transferred,
            }

        from_old = getattr(from_house, field_name, 0)
        to_old = getattr(to_house, field_name, 0)

        if from_old < delta:
            return {
                "ok": False,
                "message": f'У дома "{from_house.name}" недостаточно ресурса "{public_key}"',
                "transferred": transferred,
            }

        setattr(from_house, field_name, from_old - delta)
        setattr(to_house, field_name, to_old + delta)

        transferred[public_key] = {
            "from_old": from_old,
            "from_new": from_old - delta,
            "to_old": to_old,
            "to_new": to_old + delta,
            "delta": delta,
            "source_type": source_type,
            "source_id": source_id,
        }

    return {
        "ok": True,
        "message": "Перенос ресурсов выполнен",
        "transferred": transferred,
    }


def build_house_resources_snapshot(house: House):
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


def get_reserved_resources_for_house(db: Session, game_id: int, house_id: int) -> dict:
    deals = (
        db.query(GameDeal)
        .filter(
            GameDeal.game_id == game_id,
            GameDeal.from_house_id == house_id,
            GameDeal.status.in_(["pending", "countered", "processing"]),
        )
        .all()
    )

    reserved = {
        "gold": 0,
        "influence": 0,
        "stone": 0,
        "wood": 0,
        "iron": 0,
        "scroll": 0,
        "key": 0,
        "fire": 0,
    }

    for deal in deals:
        offer_data = deal.offer if isinstance(deal.offer, dict) else {}

        if not isinstance(offer_data, dict):
            continue

        for resource_key in reserved.keys():
            value = offer_data.get(resource_key, 0)
            if isinstance(value, int) and value > 0:
                reserved[resource_key] += value

    return reserved


def get_available_resources_for_house(db: Session, house: House) -> dict:
    reserved = get_reserved_resources_for_house(
        db=db,
        game_id=house.game_id,
        house_id=house.id,
    )

    current_resources = {
        "gold": getattr(house, "resource_gold", 0) or 0,
        "influence": getattr(house, "resource_influence", 0) or 0,
        "stone": getattr(house, "resource_stone", 0) or 0,
        "wood": getattr(house, "resource_wood", 0) or 0,
        "iron": getattr(house, "resource_iron", 0) or 0,
        "scroll": getattr(house, "resource_scroll", 0) or 0,
        "key": getattr(house, "resource_key", 0) or 0,
        "fire": getattr(house, "resource_fire", 0) or 0,
    }

    available = {}

    for resource_key, current_value in current_resources.items():
        available_value = current_value - reserved.get(resource_key, 0)
        if available_value < 0:
            available_value = 0
        available[resource_key] = available_value

    return {
        "current": current_resources,
        "reserved": reserved,
        "available": available,
    }


def validate_offer_against_house_balance(db: Session, house: House, offer: dict):
    if not isinstance(offer, dict):
        return {
            "ok": False,
            "message": 'Поле "offer" должно быть объектом',
        }

    validated_offer = {}

    resource_map = {
        "gold": "resource_gold",
        "influence": "resource_influence",
        "stone": "resource_stone",
        "wood": "resource_wood",
        "iron": "resource_iron",
        "scroll": "resource_scroll",
        "key": "resource_key",
        "fire": "resource_fire",
    }

    resource_state = get_available_resources_for_house(db=db, house=house)
    current_resources = resource_state["current"]
    reserved_resources = resource_state["reserved"]
    available_resources = resource_state["available"]

    for resource_key in resource_map.keys():
        value = offer.get(resource_key)

        if value is None:
            continue

        if not isinstance(value, int):
            return {
                "ok": False,
                "message": f'Значение ресурса "{resource_key}" должно быть целым числом',
                "resource": resource_key,
                "received_value": value,
            }

        if value < 0:
            return {
                "ok": False,
                "message": f'Значение ресурса "{resource_key}" не может быть отрицательным',
                "resource": resource_key,
                "received_value": value,
            }

        if value == 0:
            continue

        if resource_key == "influence":
            return {
                "ok": False,
                "message": "Влияние нельзя передавать через обычные сделки. Для этого позже будет отдельная механика союзов и временной поддержки.",
                "resource": "influence",
                "requested": value,
            }

        available_value = available_resources.get(resource_key, 0)

        if value > available_value:
            return {
                "ok": False,
                "message": f'Дом не может предложить больше ресурса "{resource_key}", чем доступно с учётом уже открытых сделок',
                "resource": resource_key,
                "requested": value,
                "available": available_value,
                "current": current_resources.get(resource_key, 0),
                "reserved": reserved_resources.get(resource_key, 0),
            }

        validated_offer[resource_key] = value

    if not validated_offer:
        return {
            "ok": False,
            "message": "Предложение не содержит положительных ресурсов",
        }

    return {
        "ok": True,
        "validated_offer": validated_offer,
        "resource_state": resource_state,
    }