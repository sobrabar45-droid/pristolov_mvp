from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database import SessionLocal
from app.models.game import Game
from app.models.house import House

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
        if game:
            houses = (
                db.query(House)
                .filter(House.game_id == game.id)
                .order_by(House.name.asc(), House.id.asc())
                .all()
            )

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
            },
        )

    finally:
        db.close()
