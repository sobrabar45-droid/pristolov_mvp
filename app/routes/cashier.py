from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.game_deal import GameDeal
from app.models.game import Game
from app.models.house import House
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/cashier", tags=["cashier"])
templates = Jinja2Templates(directory="app/templates")


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
                if isinstance(deal.offer, dict)
                and str(deal.offer.get("type") or "").strip().lower() == "treasurer_shop_request"
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
                        "status": deal.status,
                    }
                    for deal in pending_shop_requests
                ],
            },
        )

    finally:
        db.close()
