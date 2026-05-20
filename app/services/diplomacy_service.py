from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.game_deal import GameDeal
from app.services.resource_service import (
    apply_transfer_between_houses,
    validate_offer_against_house_balance,
    build_house_resources_snapshot,
)


def resolve_player_for_game(db: Session, game_id: int, player_id: int):
    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.game_id == game_id,
        )
        .first()
    )
    return player


def can_player_propose_diplomacy(player: Player, from_house_id: int) -> bool:
    if not player:
        return False

    if player.house_id != from_house_id:
        return False

    if not player.role:
        return False

    return player.role.code == "diplomat"


def can_player_propose_gold_deal(player: Player, from_house_id: int) -> bool:
    if not player:
        return False

    if player.house_id != from_house_id:
        return False

    if not player.role:
        return False

    return player.role.code == "treasurer"


def can_player_respond_diplomacy(player: Player, to_house_id: int) -> bool:
    if not player:
        return False

    if player.house_id != to_house_id:
        return False

    if not player.role:
        return False

    return player.role.code in {"diplomat", "lord_lady"}


def can_player_respond_gold_diplomacy(player: Player, to_house_id: int) -> bool:
    if not player:
        return False

    if player.house_id != to_house_id:
        return False

    if not player.role:
        return False

    return player.role.code in {"treasurer", "lord_lady"}


def can_player_cancel_diplomacy(player: Player, from_house_id: int) -> bool:
    if not player:
        return False

    if player.house_id != from_house_id:
        return False

    if not player.role:
        return False

    return player.role.code in {"diplomat", "lord_lady"}


def claim_pending_deal_for_processing(db: Session, game_id: int, deal_id: int):
    rows_updated = (
        db.query(GameDeal)
        .filter(
            GameDeal.id == deal_id,
            GameDeal.game_id == game_id,
            GameDeal.status == "pending",
        )
        .update(
            {
                GameDeal.status: "processing",
            },
            synchronize_session=False,
        )
    )

    db.flush()

    if rows_updated == 0:
        return {
            "ok": False,
            "message": "Сделка уже обрабатывается или больше не находится в статусе pending",
            "deal_id": deal_id,
        }

    claimed_deal = (
        db.query(GameDeal)
        .filter(
            GameDeal.id == deal_id,
            GameDeal.game_id == game_id,
        )
        .first()
    )

    return {
        "ok": True,
        "deal": claimed_deal,
    }


def public_deal_status(status: str) -> str:
    if status == "processing":
        return "pending"
    return status


def propose_diplomacy_deal_logic(
    db: Session,
    room_code: str,
    payload: dict,
    has_active_phase_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    if not has_active_phase_fn(db, game.id, "diplomacy"):
        return {
            "ok": False,
            "message": "Фаза diplomacy не активна. Сделки сейчас запрещены.",
            "room_code": room_code,
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    player_id = payload.get("player_id")
    from_house_id = payload.get("from_house_id")
    to_house_id = payload.get("to_house_id")
    offer = payload.get("offer")
    note = payload.get("note")

    if not player_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "player_id"',
        }

    if not from_house_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "from_house_id"',
        }

    if not to_house_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "to_house_id"',
        }

    if from_house_id == to_house_id:
        return {
            "ok": False,
            "message": "Нельзя отправить сделку самому себе",
        }

    from_house = (
        db.query(House)
        .filter(
            House.id == from_house_id,
            House.game_id == game.id,
        )
        .first()
    )

    to_house = (
        db.query(House)
        .filter(
            House.id == to_house_id,
            House.game_id == game.id,
        )
        .first()
    )

    if not from_house:
        return {
            "ok": False,
            "message": "Дом-отправитель не найден в этой игре",
            "from_house_id": from_house_id,
        }

    if not to_house:
        return {
            "ok": False,
            "message": "Дом-получатель не найден в этой игре",
            "to_house_id": to_house_id,
        }

    player = resolve_player_for_game(db, game.id, player_id)

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден в этой игре",
            "player_id": player_id,
        }

    if not isinstance(offer, dict):
        return {
            "ok": False,
            "message": 'Поле "offer" должно быть объектом',
        }

    gold_in_offer = offer.get("gold", 0)
    is_gold_deal = isinstance(gold_in_offer, int) and gold_in_offer > 0

    if is_gold_deal:
        if not can_player_propose_gold_deal(player, from_house_id):
            return {
                "ok": False,
                "message": "Казной Дома распоряжается только Мастер над золотом.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_role": "treasurer",
                "offer_type": "gold_deal",
            }
    else:
        if not can_player_propose_diplomacy(player, from_house_id):
            return {
                "ok": False,
                "message": "У вас нет права вести переговоры от имени этого Дома.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_role": "diplomat",
                "offer_type": "standard_deal",
            }

    offer_validation = validate_offer_against_house_balance(db, from_house, offer)

    if not offer_validation.get("ok"):
        return {
            "ok": False,
            "message": "Сделка не может быть создана",
            "offer_error": offer_validation,
        }

    offer = offer_validation["validated_offer"]

    deal = GameDeal(
        game_id=game.id,
        from_house_id=from_house.id,
        to_house_id=to_house.id,
        status="pending",
        offer=offer,
        note=note,
    )

    db.add(deal)
    db.flush()

    return {
        "ok": True,
        "message": "Дипломатическое предложение зарегистрировано",
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "from_house": {
                "id": from_house.id,
                "house_key": from_house.house_key,
                "name": from_house.name,
            },
            "to_house": {
                "id": to_house.id,
                "house_key": to_house.house_key,
                "name": to_house.name,
            },
            "offer": deal.offer,
            "note": deal.note,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "phase_required": "diplomacy",
        },
    }


def respond_diplomacy_deal_logic(
    db: Session,
    room_code: str,
    deal_id: int,
    payload: dict,
    has_active_phase_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    if not has_active_phase_fn(db, game.id, "diplomacy"):
        return {
            "ok": False,
            "message": "Фаза diplomacy не активна. Ответ на сделки сейчас запрещён.",
            "room_code": room_code,
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    player_id = payload.get("player_id")
    decision = payload.get("decision")

    if not player_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "player_id"',
        }

    if decision not in {"accepted", "rejected"}:
        return {
            "ok": False,
            "message": 'Поле "decision" должно быть "accepted" или "rejected"',
        }

    deal = (
        db.query(GameDeal)
        .filter(
            GameDeal.id == deal_id,
            GameDeal.game_id == game.id,
        )
        .first()
    )

    if not deal:
        return {
            "ok": False,
            "message": "Сделка не найдена в этой игре",
            "deal_id": deal_id,
        }

    claim_result = claim_pending_deal_for_processing(db, game.id, deal_id)
    if not claim_result.get("ok"):
        return claim_result

    deal = claim_result["deal"]
    player = resolve_player_for_game(db, game.id, player_id)

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден в этой игре",
            "player_id": player_id,
        }

    offer_data = deal.offer if isinstance(deal.offer, dict) else {}
    if not isinstance(offer_data, dict):
        offer_data = {}

    gold_in_offer = offer_data.get("gold", 0)
    is_gold_deal = isinstance(gold_in_offer, int) and gold_in_offer > 0

    if is_gold_deal:
        if not can_player_respond_gold_diplomacy(player, deal.to_house_id):
            return {
                "ok": False,
                "message": "Решения по золоту принимает только Мастер над золотом или Лорд / Леди Дома.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_roles": ["treasurer", "lord_lady"],
                "offer_type": "gold_deal",
            }
    else:
        if not can_player_respond_diplomacy(player, deal.to_house_id):
            return {
                "ok": False,
                "message": "У вас нет права говорить от имени этого Дома в переговорах.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_roles": ["diplomat", "lord_lady"],
                "offer_type": "standard_deal",
            }

    from_house = (
        db.query(House)
        .filter(House.id == deal.from_house_id)
        .first()
    )

    to_house = (
        db.query(House)
        .filter(House.id == deal.to_house_id)
        .first()
    )

    if not from_house or not to_house:
        return {
            "ok": False,
            "message": "Один из домов сделки не найден",
            "deal_id": deal_id,
        }

    transfer_result = None

    if decision == "accepted":
        transfer_result = apply_transfer_between_houses(
            db=db,
            from_house=from_house,
            to_house=to_house,
            offer_data=deal.offer,
            source_type="deal",
            source_id=deal.id,
            reason=f'Дипломатическая сделка #{deal.id}',
            performed_by_player_id=player.id,
        )

        if not transfer_result.get("ok"):
            db.rollback()
            deal_reset = (
                db.query(GameDeal)
                .filter(
                    GameDeal.id == deal_id,
                    GameDeal.game_id == game.id,
                )
                .first()
            )
            if deal_reset and deal_reset.status == "processing":
                deal_reset.status = "pending"
                db.flush()

            return {
                "ok": False,
                "message": "Сделка не может быть принята",
                "deal_id": deal_id,
                "transfer_error": transfer_result,
            }

    deal.status = decision
    deal.responded_at = datetime.now(timezone.utc)

    if decision == "accepted":
        message = f"{from_house.name} и {to_house.name} достигли соглашения."
    else:
        message = f"{to_house.name} отверг предложение {from_house.name}."

    return {
        "ok": True,
        "message": message,
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "from_house": {
                "id": from_house.id,
                "house_key": from_house.house_key,
                "name": from_house.name,
            } if from_house else None,
            "to_house": {
                "id": to_house.id,
                "house_key": to_house.house_key,
                "name": to_house.name,
            } if to_house else None,
            "offer": deal.offer,
            "note": deal.note,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
        },
        "transfer_result": transfer_result,
        "from_house_resources_after": build_house_resources_snapshot(from_house) if from_house else None,
        "to_house_resources_after": build_house_resources_snapshot(to_house) if to_house else None,
    }


def counter_diplomacy_deal_logic(
    db: Session,
    room_code: str,
    deal_id: int,
    payload: dict,
    has_active_phase_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    if not has_active_phase_fn(db, game.id, "diplomacy"):
        return {
            "ok": False,
            "message": "Фаза diplomacy не активна. Встречные сделки сейчас запрещены.",
            "room_code": room_code,
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    player_id = payload.get("player_id")
    offer = payload.get("offer")
    note = payload.get("note")

    if not player_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "player_id"',
        }

    original_deal = (
        db.query(GameDeal)
        .filter(
            GameDeal.id == deal_id,
            GameDeal.game_id == game.id,
        )
        .first()
    )

    if not original_deal:
        return {
            "ok": False,
            "message": "Исходная сделка не найдена",
            "deal_id": deal_id,
        }

    claim_result = claim_pending_deal_for_processing(db, game.id, deal_id)
    if not claim_result.get("ok"):
        return claim_result

    original_deal = claim_result["deal"]

    player = resolve_player_for_game(db, game.id, player_id)

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден в этой игре",
            "player_id": player_id,
        }

    if not isinstance(offer, dict):
        return {
            "ok": False,
            "message": 'Поле "offer" должно быть объектом',
        }

    gold_in_offer = offer.get("gold", 0)
    is_gold_deal = isinstance(gold_in_offer, int) and gold_in_offer > 0

    if is_gold_deal:
        if not can_player_propose_gold_deal(player, original_deal.to_house_id):
            return {
                "ok": False,
                "message": "Казной Дома распоряжается только Мастер над золотом.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_role": "treasurer",
                "offer_type": "gold_deal",
            }
    else:
        if not can_player_respond_diplomacy(player, original_deal.to_house_id):
            return {
                "ok": False,
                "message": "У вас нет права вести переговоры от имени этого Дома.",
                "player_id": player.id,
                "player_house_id": player.house_id,
                "player_role_code": player.role.code if player.role else None,
                "required_roles": ["diplomat", "lord_lady"],
                "offer_type": "standard_deal",
            }

    counter_from_house = (
        db.query(House)
        .filter(House.id == original_deal.to_house_id)
        .first()
    )

    counter_to_house = (
        db.query(House)
        .filter(House.id == original_deal.from_house_id)
        .first()
    )

    if not counter_from_house or not counter_to_house:
        return {
            "ok": False,
            "message": "Не удалось определить дома для встречной сделки",
            "deal_id": deal_id,
        }

    offer_validation = validate_offer_against_house_balance(db, counter_from_house, offer)

    if not offer_validation.get("ok"):
        return {
            "ok": False,
            "message": "Встречная сделка не может быть создана",
            "offer_error": offer_validation,
        }

    offer = offer_validation["validated_offer"]

    original_deal.status = "countered"
    original_deal.responded_at = datetime.now(timezone.utc)

    counter_deal = GameDeal(
        game_id=game.id,
        from_house_id=counter_from_house.id,
        to_house_id=counter_to_house.id,
        parent_deal_id=original_deal.id,
        status="pending",
        offer=offer,
        note=note,
    )

    db.add(counter_deal)
    db.flush()

    return {
        "ok": True,
        "message": "Встречное предложение зарегистрировано",
        "original_deal": {
            "id": original_deal.id,
            "status": original_deal.status,
            "responded_at": original_deal.responded_at.isoformat() if original_deal.responded_at else None,
        },
        "counter_deal": {
            "id": counter_deal.id,
            "parent_deal_id": counter_deal.parent_deal_id,
            "status": counter_deal.status,
            "from_house": {
                "id": counter_from_house.id,
                "house_key": counter_from_house.house_key,
                "name": counter_from_house.name,
            },
            "to_house": {
                "id": counter_to_house.id,
                "house_key": counter_to_house.house_key,
                "name": counter_to_house.name,
            },
            "offer": counter_deal.offer,
            "note": counter_deal.note,
            "created_at": counter_deal.created_at.isoformat() if counter_deal.created_at else None,
        },
    }


def cancel_diplomacy_deal_logic(
    db: Session,
    room_code: str,
    deal_id: int,
    payload: dict,
    has_active_phase_fn,
):
    game = db.query(Game).filter(Game.room_code == room_code).first()

    if not game:
        return {
            "ok": False,
            "message": "Игра не найдена",
            "room_code": room_code,
        }

    if not has_active_phase_fn(db, game.id, "diplomacy"):
        return {
            "ok": False,
            "message": "Фаза diplomacy не активна. Отмена сделок сейчас запрещена.",
            "room_code": room_code,
        }

    if not isinstance(payload, dict):
        return {
            "ok": False,
            "message": "Тело запроса должно быть JSON-объектом",
        }

    player_id = payload.get("player_id")

    if not player_id:
        return {
            "ok": False,
            "message": 'Отсутствует обязательное поле "player_id"',
        }

    deal = (
        db.query(GameDeal)
        .filter(
            GameDeal.id == deal_id,
            GameDeal.game_id == game.id,
        )
        .first()
    )

    if not deal:
        return {
            "ok": False,
            "message": "Сделка не найдена в этой игре",
            "deal_id": deal_id,
        }

    claim_result = claim_pending_deal_for_processing(db, game.id, deal_id)
    if not claim_result.get("ok"):
        return claim_result

    deal = claim_result["deal"]

    player = resolve_player_for_game(db, game.id, player_id)

    if not player:
        return {
            "ok": False,
            "message": "Игрок не найден в этой игре",
            "player_id": player_id,
        }

    if not can_player_cancel_diplomacy(player, deal.from_house_id):
        return {
            "ok": False,
            "message": "Игрок не может отменить эту дипломатическую сделку",
            "player_id": player.id,
            "player_house_id": player.house_id,
            "player_role_code": player.role.code if player.role else None,
            "required_roles": ["diplomat", "lord_lady"],
        }

    deal.status = "cancelled"
    deal.responded_at = datetime.now(timezone.utc)

    from_house = (
        db.query(House)
        .filter(House.id == deal.from_house_id)
        .first()
    )

    to_house = (
        db.query(House)
        .filter(House.id == deal.to_house_id)
        .first()
    )

    return {
        "ok": True,
        "message": f'Сделка #{deal.id} отменена',
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "deal": {
            "id": deal.id,
            "status": deal.status,
            "from_house": {
                "id": from_house.id,
                "house_key": from_house.house_key,
                "name": from_house.name,
            } if from_house else None,
            "to_house": {
                "id": to_house.id,
                "house_key": to_house.house_key,
                "name": to_house.name,
            } if to_house else None,
            "offer": deal.offer,
            "note": deal.note,
            "created_at": deal.created_at.isoformat() if deal.created_at else None,
            "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
        },
    }