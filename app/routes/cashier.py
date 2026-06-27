from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.game_deal import GameDeal
from app.models.game import Game
from app.models.house import House
from app.services.gold_service import (
    GoldError,
    GoldInsufficientFundsError,
    spend_gold_for_action,
)
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/cashier", tags=["cashier"])
templates = Jinja2Templates(directory="app/templates")

TREASURER_SHOP_REQUEST_TYPE = "treasurer_shop_request"
TREASURER_SHOP_REQUEST_ACTIONS = {
    "author_tea",
    "premium_champagne_premier",
    "tincture_set",
    "beer_giraffe_shihan",
    "lemonade_02",
    "sobranie_pizza",
    "beer_set_any",
    "anna_pavlova",
    "tapas_set",
}


def _is_treasurer_shop_request(deal: GameDeal) -> bool:
    return (
        isinstance(deal.offer, dict)
        and str(deal.offer.get("type") or "").strip().lower() == TREASURER_SHOP_REQUEST_TYPE
    )


def _shop_offer_value(offer: dict, key: str) -> str:
    return str(offer.get(key) or "").strip()


@router.get("/gold-desk/{room_code}", response_class=HTMLResponse)
async def cashier_gold_desk_page(request: Request, room_code: str):
    db = SessionLocal()

    try:
        normalized_room_code = room_code.strip().upper()
        game = (
            db.query(Game)
            .filter(Game.room_code == normalized_room_code)
            .first()
        )

        houses = []
        pending_shop_requests = []
        if game:
            houses = (
                db.query(House)
                .filter(House.game_id == game.id)
                .order_by(House.name.asc(), House.id.asc())
                .all()
            )
            candidate_requests = (
                db.query(GameDeal)
                .options(joinedload(GameDeal.from_house))
                .filter(
                    GameDeal.game_id == game.id,
                    GameDeal.status == "pending",
                )
                .order_by(GameDeal.id.desc())
                .all()
            )
            pending_shop_requests = [
                deal
                for deal in candidate_requests
                if _is_treasurer_shop_request(deal)
            ]

        return templates.TemplateResponse(
            request,
            "cashier_gold_desk.html",
            {
                "room_code": normalized_room_code,
                "game_found": bool(game),
                "houses": [
                    {
                        "id": house.id,
                        "name": house.name,
                        "house_key": house.house_key,
                        "gold": house.resource_gold,
                    }
                    for house in houses
                ],
                "pending_shop_requests": [
                    {
                        "id": deal.id,
                        "house_name": deal.from_house.name if deal.from_house else None,
                        "house_key": deal.from_house.house_key if deal.from_house else None,
                        "item_label": deal.offer.get("item_label") if isinstance(deal.offer, dict) else None,
                        "cost_gold": deal.offer.get("cost_gold") if isinstance(deal.offer, dict) else None,
                        "is_18_plus": bool(deal.offer.get("is_18_plus")) if isinstance(deal.offer, dict) else False,
                        "status": deal.status,
                    }
                    for deal in pending_shop_requests
                ],
            },
        )

    finally:
        db.close()


@router.post("/treasurer-shop/requests/{request_id}/confirm")
def confirm_treasurer_shop_request(request_id: int):
    db = SessionLocal()

    try:
        deal = (
            db.query(GameDeal)
            .options(joinedload(GameDeal.from_house))
            .filter(GameDeal.id == request_id)
            .first()
        )
        if not deal:
            return {
                "ok": False,
                "message": "Заявка не найдена",
            }
        if not _is_treasurer_shop_request(deal):
            return {
                "ok": False,
                "message": "Это не заявка Харчевни",
                "request_status": deal.status,
            }
        if deal.status != "pending":
            return {
                "ok": False,
                "message": "Заявка уже обработана",
                "request_status": deal.status,
            }
        if not deal.from_house:
            return {
                "ok": False,
                "message": "У заявки не найден Дом",
                "request_status": deal.status,
            }

        offer = dict(deal.offer) if isinstance(deal.offer, dict) else {}
        action_code = _shop_offer_value(offer, "action_code")
        item_label = _shop_offer_value(offer, "item_label")
        player_id = offer.get("player_id")

        try:
            cost_gold = int(offer.get("cost_gold") or 0)
        except (TypeError, ValueError):
            cost_gold = 0

        if action_code not in TREASURER_SHOP_REQUEST_ACTIONS:
            return {
                "ok": False,
                "message": "В заявке указан неизвестный товар Харчевни",
                "request_status": deal.status,
            }
        if cost_gold <= 0:
            return {
                "ok": False,
                "message": "В заявке указана некорректная стоимость",
                "request_status": deal.status,
            }
        if not item_label:
            item_label = action_code
        if not isinstance(player_id, int):
            player_id = None

        reason = f"Дом {deal.from_house.name or deal.from_house.house_key} заказал {item_label} за {cost_gold} золота. Заказ принят кассиром."

        try:
            result = spend_gold_for_action(
                db,
                house=deal.from_house,
                amount=cost_gold,
                reason=reason,
                source_type="treasurer_shop",
                source_id=deal.id,
                performed_by_player_id=player_id,
            )
        except GoldInsufficientFundsError as exc:
            db.rollback()
            return {
                "ok": False,
                "message": str(exc),
                "request_status": deal.status,
                "gold_before": int(deal.from_house.resource_gold or 0),
                "gold_after": int(deal.from_house.resource_gold or 0),
            }

        now = datetime.utcnow()
        offer["confirmed_at"] = now.isoformat()
        offer["confirmed_transaction_id"] = result.transaction_id
        deal.offer = offer
        deal.status = "completed"
        deal.responded_at = now
        db.add(deal)
        db.commit()
        db.refresh(deal)

        return {
            "ok": True,
            "message": "Заказ принят",
            "request_id": deal.id,
            "request_status": deal.status,
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "transaction_id": result.transaction_id,
        }
    except GoldError as exc:
        db.rollback()
        return {
            "ok": False,
            "message": str(exc),
        }
    finally:
        db.close()
