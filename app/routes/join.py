from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.role import Role

router = APIRouter(tags=["join"])

templates = Jinja2Templates(directory="app/templates")


@router.get("/join", response_class=HTMLResponse)
def join_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="join.html",
        context={"error": None},
    )


@router.post("/join", response_class=HTMLResponse)
def join_submit(request: Request, room_code: str = Form(...)):
    db: Session = SessionLocal()

    try:
        clean_code = room_code.strip().upper()

        game = db.query(Game).filter(Game.room_code == clean_code).first()

        if not game:
            return templates.TemplateResponse(
                request=request,
                name="join.html",
                context={"error": f"Игра с кодом {clean_code} не найдена"},
            )

        return RedirectResponse(url=f"/game/{clean_code}", status_code=303)

    finally:
        db.close()


@router.get("/game/{room_code}", response_class=HTMLResponse)
def game_page(request: Request, room_code: str):
    db: Session = SessionLocal()

    try:
        clean_code = room_code.strip().upper()

        game = db.query(Game).filter(Game.room_code == clean_code).first()

        if not game:
            return templates.TemplateResponse(
                request=request,
                name="join.html",
                context={"error": f"Игра с кодом {clean_code} не найдена"},
            )

        houses = db.query(House).filter(House.game_id == game.id).all()

        return templates.TemplateResponse(
            request=request,
            name="game.html",
            context={
                "game": game,
                "houses": houses,
                "error": None,
            },
        )

    finally:
        db.close()


@router.post("/game/{room_code}/join-house", response_class=HTMLResponse)
def join_house(
    request: Request,
    room_code: str,
    nickname: str = Form(...),
    house_id: int = Form(...),
):
    db: Session = SessionLocal()

    try:
        clean_code = room_code.strip().upper()
        clean_nickname = nickname.strip()

        game = db.query(Game).filter(Game.room_code == clean_code).first()

        if not game:
            return templates.TemplateResponse(
                request=request,
                name="join.html",
                context={"error": f"Игра с кодом {clean_code} не найдена"},
            )

        houses = db.query(House).filter(House.game_id == game.id).all()

        if not clean_nickname:
            return templates.TemplateResponse(
                request=request,
                name="game.html",
                context={
                    "game": game,
                    "houses": houses,
                    "error": "Введите имя игрока",
                },
            )

        selected_house = (
            db.query(House)
            .filter(House.id == house_id, House.game_id == game.id)
            .first()
        )

        if not selected_house:
            return templates.TemplateResponse(
                request=request,
                name="game.html",
                context={
                    "game": game,
                    "houses": houses,
                    "error": "Выбранный дом не найден",
                },
            )

        player = Player(
            game_id=game.id,
            house_id=selected_house.id,
            nickname=clean_nickname,
        )
        db.add(player)
        db.commit()
        db.refresh(player)

        return RedirectResponse(
            url=f"/player/{player.id}/role-select",
            status_code=303,
        )

    finally:
        db.close()


@router.get("/player/{player_id}/role-select", response_class=HTMLResponse)
def role_select_page(request: Request, player_id: int):
    db: Session = SessionLocal()

    try:
        player = db.query(Player).filter(Player.id == player_id).first()

        if not player:
            return HTMLResponse(content="Игрок не найден", status_code=404)

        game = db.query(Game).filter(Game.id == player.game_id).first()
        house = db.query(House).filter(House.id == player.house_id).first()
        roles = db.query(Role).order_by(Role.id.asc()).all()

        return templates.TemplateResponse(
            request=request,
            name="role_select.html",
            context={
                "player": player,
                "game": game,
                "house": house,
                "roles": roles,
                "error": None,
            },
        )

    finally:
        db.close()


@router.post("/player/{player_id}/role-select", response_class=HTMLResponse)
def role_select_submit(
    request: Request,
    player_id: int,
    role_id: int = Form(...),
):
    db: Session = SessionLocal()

    try:
        player = db.query(Player).filter(Player.id == player_id).first()

        if not player:
            return HTMLResponse(content="Игрок не найден", status_code=404)

        game = db.query(Game).filter(Game.id == player.game_id).first()
        house = db.query(House).filter(House.id == player.house_id).first()
        roles = db.query(Role).order_by(Role.id.asc()).all()

        selected_role = db.query(Role).filter(Role.id == role_id).first()

        if not selected_role:
            return templates.TemplateResponse(
                request=request,
                name="role_select.html",
                context={
                    "player": player,
                    "game": game,
                    "house": house,
                    "roles": roles,
                    "error": "Выбранная роль не найдена",
                },
            )

        existing_player_with_role = (
            db.query(Player)
            .filter(
                Player.house_id == player.house_id,
                Player.role_id == selected_role.id,
                Player.id != player.id,
            )
            .first()
        )

        if existing_player_with_role:
            return templates.TemplateResponse(
                request=request,
                name="role_select.html",
                context={
                    "player": player,
                    "game": game,
                    "house": house,
                    "roles": roles,
                    "error": f'Роль "{selected_role.name}" в доме "{house.name}" уже занята',
                },
            )

        player.role_id = selected_role.id
        db.commit()
        db.refresh(player)

        return templates.TemplateResponse(
            request=request,
            name="player_joined.html",
            context={
                "player": player,
                "game": game,
                "house": house,
                "role": selected_role,
            },
        )

    finally:
        db.close()
@router.get("/game/{room_code}/roster", response_class=HTMLResponse)
def game_roster_page(request: Request, room_code: str):
    db: Session = SessionLocal()

    try:
        clean_code = room_code.strip().upper()

        game = db.query(Game).filter(Game.room_code == clean_code).first()

        if not game:
            return templates.TemplateResponse(
                request=request,
                name="join.html",
                context={"error": f"Игра с кодом {clean_code} не найдена"},
            )

        houses = db.query(House).filter(House.game_id == game.id).order_by(House.id.asc()).all()
        roles = db.query(Role).order_by(Role.id.asc()).all()

        roster_data = []

        for house in houses:
            players = (
                db.query(Player)
                .filter(Player.house_id == house.id)
                .order_by(Player.id.asc())
                .all()
            )

            used_role_ids = {player.role_id for player in players if player.role_id is not None}

            free_roles = [role for role in roles if role.id not in used_role_ids]

            roster_data.append(
                {
                    "house": house,
                    "players": players,
                    "free_roles": free_roles,
                }
            )

        return templates.TemplateResponse(
            request=request,
            name="roster.html",
            context={
                "game": game,
                "roster_data": roster_data,
            },
        )

    finally:
        db.close()