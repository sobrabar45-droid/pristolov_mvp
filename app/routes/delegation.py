import random
import secrets

from fastapi import APIRouter, Body, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
import segno
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.house_catalog import HOUSE_CATALOG, get_taken_house_keys, score_available_houses
from app.models.game import Game
from app.models.game_house_tower import GameHouseTower
from app.models.house import House
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.player import Player
from app.models.role import Role
from app.services.house_service import set_house_ready_logic
from app.utils.player_tokens import issue_player_token
from sqlalchemy import text

router = APIRouter(tags=["delegation"])

templates = Jinja2Templates(directory="app/templates")


def generate_invite_code():
    return secrets.token_hex(3).upper()


@router.get("/dev/reset-delegations/{room_code}", response_class=HTMLResponse)
def dev_reset_delegations(room_code: str):
    db: Session = SessionLocal()

    try:
        clean_room_code = room_code.strip().upper()

        game = db.query(Game).filter(Game.room_code == clean_room_code).first()
        if not game:
            return HTMLResponse(
                content=f"<h1>Ошибка</h1><p>Игра с кодом {clean_room_code} не найдена</p>",
                status_code=404,
            )

        houses = db.query(House).filter(House.game_id == game.id).all()
        house_ids = [house.id for house in houses]

        deleted_players = 0
        deleted_houses = 0

        if house_ids:
            (
                db.query(HouseGoldTransaction)
                .filter(HouseGoldTransaction.game_id == game.id)
                .delete(synchronize_session=False)
            )

            deleted_players = (
                db.query(Player)
                .filter(Player.house_id.in_(house_ids))
                .delete(synchronize_session=False)
            )

            (
                db.query(GameHouseTower)
                .filter(GameHouseTower.game_id == game.id)
                .delete(synchronize_session=False)
            )

            deleted_houses = (
                db.query(House)
                .filter(House.game_id == game.id)
                .delete(synchronize_session=False)
            )

            db.commit()

        return HTMLResponse(
            content=(
                f"<h1>Сброс выполнен</h1>"
                f"<p>Игра: {clean_room_code}</p>"
                f"<p>Удалено игроков: {deleted_players}</p>"
                f"<p>Удалено домов: {deleted_houses}</p>"
                f'<p><a href="/delegation/start">Вернуться к созданию делегации</a></p>'
            )
        )

    finally:
        db.close()


@router.get("/delegation/start", response_class=HTMLResponse)
def delegation_start_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="delegation_start.html",
        context={"error": None},
    )


@router.post("/delegation/start", response_class=HTMLResponse)
def delegation_start_submit(
    request: Request,
    game_code: str = Form(...),
    leader_nickname: str = Form(...),
    team_size_declared: int = Form(...),
    entry_mode: str = Form(...),
    answer_priority: str = Form(None),
    answer_conflict: str = Form(None),
    answer_style: str = Form(None),
):
    db: Session = SessionLocal()

    try:
        clean_game_code = game_code.strip().upper()
        clean_leader = leader_nickname.strip()
        clean_entry_mode = entry_mode.strip().lower()

        game = db.query(Game).filter(Game.room_code == clean_game_code).first()
        if not game:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": f"Игра с кодом {clean_game_code} не найдена"},
            )

        if not clean_leader:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "Введите имя главы делегации"},
            )

        if team_size_declared < 2 or team_size_declared > 10:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "Размер делегации должен быть от 2 до 10 человек"},
            )

        if clean_entry_mode not in ("quiz", "random"):
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "Некорректный режим входа в игру"},
            )

        existing_houses = db.query(House).filter(House.game_id == game.id).all()
        taken_keys = get_taken_house_keys(existing_houses)
        available_houses = [house for house in HOUSE_CATALOG if house["key"] not in taken_keys]

        if not available_houses:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "В этой игре больше нет свободных Домов"},
            )

        best_match_overall = None
        chosen_house = None

        if clean_entry_mode == "random":
            chosen_house = random.choice(available_houses)

        elif clean_entry_mode == "quiz":
            valid_priority_values = {"power", "diplomacy", "wealth", "knowledge", "shadow", "risk"}
            valid_conflict_values = {"direct", "negotiate", "calculate", "secret"}
            valid_style_values = {"dominance", "alliances", "knowledge", "risk"}

            if answer_priority not in valid_priority_values:
                return templates.TemplateResponse(
                    request=request,
                    name="delegation_start.html",
                    context={"error": "Некорректный ответ на вопрос о приоритете делегации"},
                )

            if answer_conflict not in valid_conflict_values:
                return templates.TemplateResponse(
                    request=request,
                    name="delegation_start.html",
                    context={"error": "Некорректный ответ на вопрос о конфликте"},
                )

            if answer_style not in valid_style_values:
                return templates.TemplateResponse(
                    request=request,
                    name="delegation_start.html",
                    context={"error": "Некорректный ответ на вопрос о пути Дома"},
                )

            answers = {
                "power": 0,
                "diplomacy": 0,
                "wealth": 0,
                "knowledge": 0,
                "shadow": 0,
                "risk": 0,
            }

            priority_map = {
                "power": {"power": 3},
                "diplomacy": {"diplomacy": 3},
                "wealth": {"wealth": 3},
                "knowledge": {"knowledge": 3},
                "shadow": {"shadow": 3},
                "risk": {"risk": 3},
            }

            conflict_map = {
                "direct": {"power": 2, "risk": 1},
                "negotiate": {"diplomacy": 2, "knowledge": 1},
                "calculate": {"wealth": 2, "knowledge": 1},
                "secret": {"shadow": 2, "knowledge": 1},
            }

            style_map = {
                "dominance": {"power": 2, "diplomacy": 1},
                "alliances": {"diplomacy": 2, "wealth": 1},
                "knowledge": {"knowledge": 2, "shadow": 1},
                "risk": {"risk": 2, "power": 1},
            }

            for axis, value in priority_map[answer_priority].items():
                answers[axis] += value

            for axis, value in conflict_map[answer_conflict].items():
                answers[axis] += value

            for axis, value in style_map[answer_style].items():
                answers[axis] += value

            overall_scored = score_available_houses(HOUSE_CATALOG, answers)
            available_scored = score_available_houses(available_houses, answers)

            best_match_overall = overall_scored[0]["house"] if overall_scored else None
            chosen_house = available_scored[0]["house"] if available_scored else None

        if not chosen_house:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "Не удалось определить Дом для делегации"},
            )

        lord_role = db.query(Role).filter(Role.code == "lord_lady").first()
        if not lord_role:
            return templates.TemplateResponse(
                request=request,
                name="delegation_start.html",
                context={"error": "Сначала выполните /seed-roles"},
            )

        invite_code = generate_invite_code()

        house = House(
            game_id=game.id,
            house_key=chosen_house["key"],
            name=chosen_house["name"],
            motto=chosen_house["motto"],
            color=chosen_house["color"],
            team_size_declared=team_size_declared,
            invite_code=invite_code,
            entry_mode=clean_entry_mode,
            resource_gold=11 if clean_entry_mode == "quiz" else 10,
            resource_influence=0,
            resource_stone=0,
            resource_wood=0,
            resource_iron=0,
            resource_scroll=0,
            resource_key=0,
            resource_fire=0,
            fate_bias=1 if clean_entry_mode == "random" else 0,
        )
        db.add(house)
        db.commit()
        db.refresh(house)

        leader = Player(
            game_id=game.id,
            house_id=house.id,
            nickname=clean_leader,
            role_id=lord_role.id,
            player_token=issue_player_token(),
        )
        db.add(leader)
        db.commit()
        db.refresh(leader)

        house.leader_player_id = leader.id
        db.commit()
        db.refresh(house)

        return templates.TemplateResponse(
            request=request,
            name="delegation_result.html",
            context={
                "game": game,
                "house": house,
                "leader": leader,
                "best_match_overall": best_match_overall,
                "chosen_house": chosen_house,
            },
        )

    finally:
        db.close()


@router.get("/delegation/join", response_class=HTMLResponse)
def delegation_join_page(request: Request, game_code: str = "", invite_code: str = ""):
    return templates.TemplateResponse(
        request=request,
        name="delegation_join.html",
        context={
            "error": None,
            "default_game_code": (game_code or "").strip().upper(),
            "default_invite_code": (invite_code or "").strip().upper(),
        },
    )


@router.post("/delegation/join", response_class=HTMLResponse)
def delegation_join_submit(
    request: Request,
    game_code: str = Form(...),
    invite_code: str = Form(...),
    nickname: str = Form(...),
):
    db: Session = SessionLocal()

    try:
        clean_game_code = game_code.strip().upper()
        clean_invite_code = invite_code.strip().upper()
        clean_nickname = nickname.strip()

        game = db.query(Game).filter(Game.room_code == clean_game_code).first()
        if not game:
            return templates.TemplateResponse(
                request=request,
                name="delegation_join.html",
                context={"error": f"Игра с кодом {clean_game_code} не найдена"},
            )

        house = (
            db.query(House)
            .filter(House.game_id == game.id, House.invite_code == clean_invite_code)
            .first()
        )

        if not house:
            return templates.TemplateResponse(
                request=request,
                name="delegation_join.html",
                context={"error": "Верительная грамота не найдена"},
            )

        if not clean_nickname:
            return templates.TemplateResponse(
                request=request,
                name="delegation_join.html",
                context={"error": "Введите имя участника"},
            )

        current_players_count = db.query(Player).filter(Player.house_id == house.id).count()

        if current_players_count >= house.team_size_declared:
            existing_players = (
                db.query(Player)
                .filter(Player.house_id == house.id)
                .all()
            )

            normalized_nickname = clean_nickname.casefold()

            for existing_player in existing_players:
                if existing_player.nickname and existing_player.nickname.strip().casefold() == normalized_nickname:
                    if house.leader_player_id == existing_player.id:
                        return templates.TemplateResponse(
                            request=request,
                            name="lord_dashboard.html",
                            context=_build_house_lobby_context(db, house.invite_code, base_url=str(request.base_url).rstrip("/")),
                        )

                    return templates.TemplateResponse(
                        request=request,
                        name="player_room.html",
                        context=_build_player_room_context(db, house.invite_code, existing_player.id),
                    )

            return templates.TemplateResponse(
                request=request,
                name="delegation_join.html",
                context={"error": f'Дом "{house.name}" уже набрал заявленный состав'},
            )

        existing_players = db.query(Player).filter(Player.house_id == house.id).all()
        normalized_nickname = clean_nickname.casefold()

        for existing_player in existing_players:
            if existing_player.nickname and existing_player.nickname.strip().casefold() == normalized_nickname:
                if house.leader_player_id == existing_player.id:
                    return templates.TemplateResponse(
                        request=request,
                        name="lord_dashboard.html",
                        context=_build_house_lobby_context(db, house.invite_code, base_url=str(request.base_url).rstrip("/")),
                    )

                return templates.TemplateResponse(
                    request=request,
                    name="player_room.html",
                    context=_build_player_room_context(db, house.invite_code, existing_player.id),
                )

        player = Player(
            game_id=game.id,
            house_id=house.id,
            nickname=clean_nickname,
            role_id=None,
            player_token=issue_player_token(),
        )
        db.add(player)
        db.commit()
        db.refresh(player)

        return templates.TemplateResponse(
            request=request,
            name="player_room.html",
            context=_build_player_room_context(db, house.invite_code, player.id),
        )

    finally:
        db.close()


@router.get("/house/{invite_code}", response_class=HTMLResponse)
def house_lobby_page(request: Request, invite_code: str):
    db: Session = SessionLocal()

    try:
        return templates.TemplateResponse(
            request=request,
            name="lord_dashboard.html",
            context=_build_house_lobby_context(db, invite_code.strip().upper(), base_url=str(request.base_url).rstrip("/")),
        )

    finally:
        db.close()


@router.get("/house/{invite_code}/player/{player_id}", response_class=HTMLResponse)
def player_room_page(request: Request, invite_code: str, player_id: int):
    db: Session = SessionLocal()

    try:
        return templates.TemplateResponse(
            request=request,
            name="player_room.html",
            context=_build_player_room_context(db, invite_code.strip().upper(), player_id),
        )

    finally:
        db.close()


@router.get("/house/{invite_code}/assign-role/{player_id}/{role_code}", response_class=HTMLResponse)
def assign_house_role(request: Request, invite_code: str, player_id: int, role_code: str):
    db: Session = SessionLocal()

    try:
        clean_invite_code = invite_code.strip().upper()
        clean_role_code = role_code.strip().lower()

        house = db.query(House).filter(House.invite_code == clean_invite_code).first()
        if not house:
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context={
                    "error": "Дом по этой грамоте не найден",
                    "house": None,
                    "game": None,
                    "leader": None,
                    "players": [],
                    "remaining_slots": 0,
                    "occupied_slots": 0,
                    "house_roles_status": [],
                    "taken_unique_role_codes": set(),
                    "available_role_links_by_player_id": {},
                    "current_role_by_player_id": {},
                },
            )

        player = db.query(Player).filter(Player.id == player_id).first()
        if not player or player.house_id != house.id:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "Игрок не найден в составе этого Дома"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        if house.leader_player_id == player.id:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "Главе Дома нельзя менять роль через это действие"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        allowed_role_codes = {
            "diplomat",
            "treasurer",
            "maester",
            "whisper_master",
            "house_sworn",
        }

        if clean_role_code not in allowed_role_codes:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "Эту роль нельзя назначить через лобби"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        role = db.query(Role).filter(Role.code == clean_role_code).first()
        if not role:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "Роль не найдена в базе. Выполните /seed-roles"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        # роли, которые могут быть только у одного игрока
        unique_role_codes = {
            "diplomat",
            "treasurer",
            "maester",
            "whisper_master",
        }

        # если роль уникальная — проверяем, не занята ли
        if clean_role_code in unique_role_codes:
            existing = (
                db.query(Player)
                .join(Role, Player.role_id == Role.id)
                .filter(
                    Player.house_id == house.id,
                    Role.code == clean_role_code,
                    Player.id != player.id,
                )
                .first()
            )

            if existing:
                context = _build_house_lobby_context(db, clean_invite_code)
                context["error"] = f'Роль "{role.name}" уже занята игроком {existing.nickname}'
                return templates.TemplateResponse(
                    request=request,
                    name="lord_dashboard.html",
                    context=context,
                )

        player.role_id = role.id
        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="lord_dashboard.html",
            context=_build_house_lobby_context(db, clean_invite_code, base_url=str(request.base_url).rstrip("/")),
        )

    finally:
        db.close()


@router.get("/house/{invite_code}/clear-role/{player_id}", response_class=HTMLResponse)
def clear_house_role(request: Request, invite_code: str, player_id: int):
    db: Session = SessionLocal()

    try:
        clean_invite_code = invite_code.strip().upper()

        house = db.query(House).filter(House.invite_code == clean_invite_code).first()
        if not house:
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context={
                    "error": "Дом по этой грамоте не найден",
                    "house": None,
                    "game": None,
                    "leader": None,
                    "players": [],
                    "remaining_slots": 0,
                    "occupied_slots": 0,
                    "house_roles_status": [],
                    "taken_unique_role_codes": set(),
                    "available_role_links_by_player_id": {},
                    "current_role_by_player_id": {},
                },
            )

        player = db.query(Player).filter(Player.id == player_id).first()
        if not player or player.house_id != house.id:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "Игрок не найден в составе этого Дома"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        if house.leader_player_id == player.id:
            context = _build_house_lobby_context(db, clean_invite_code)
            context["error"] = "У главы Дома нельзя снять базовую роль"
            return templates.TemplateResponse(
                request=request,
                name="lord_dashboard.html",
                context=context,
            )

        player.role_id = None
        db.commit()

        return templates.TemplateResponse(
            request=request,
            name="lord_dashboard.html",
            context=_build_house_lobby_context(db, clean_invite_code, base_url=str(request.base_url).rstrip("/")),
        )

    finally:
        db.close()


@router.post("/house/{invite_code}/ready")
def set_house_ready(invite_code: str, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        return set_house_ready_logic(
            db,
            invite_code=invite_code,
            is_ready=bool((payload or {}).get("is_ready")),
        )
    finally:
        db.close()


@router.get("/house/{invite_code}/join-qr.svg")
def house_join_qr_svg(request: Request, invite_code: str):
    db: Session = SessionLocal()

    try:
        clean_invite_code = invite_code.strip().upper()
        house = db.query(House).filter(House.invite_code == clean_invite_code).first()
        if not house:
            return Response(status_code=404, content="Дом не найден")

        game = db.query(Game).filter(Game.id == house.game_id).first()
        if not game:
            return Response(status_code=404, content="Игра не найдена")

        base_url = str(request.base_url).rstrip("/")
        join_url = f"{base_url}/delegation/join?game_code={game.room_code}&invite_code={house.invite_code}"
        qr = segno.make(join_url, error="M", micro=False)
        svg_text = qr.svg_inline(scale=8, border=2, dark="#111111", light="#ffffff")
        return Response(content=svg_text, media_type="image/svg+xml")
    finally:
        db.close()


def _build_house_lobby_context(db: Session, invite_code: str, base_url: str | None = None):
    house = db.query(House).filter(House.invite_code == invite_code).first()
    if not house:
        return {
            "error": "Дом по этой грамоте не найден",
            "house": None,
            "game": None,
            "leader": None,
            "players": [],
            "remaining_slots": 0,
            "occupied_slots": 0,
            "house_roles_status": [],
            "taken_unique_role_codes": set(),
            "available_role_links_by_player_id": {},
            "current_role_by_player_id": {},
        }

    game = db.query(Game).filter(Game.id == house.game_id).first()
    leader = db.query(Player).filter(Player.id == house.leader_player_id).first()
    players = db.query(Player).filter(Player.house_id == house.id).order_by(Player.id.asc()).all()

    occupied_slots = len(players)
    remaining_slots = house.team_size_declared - occupied_slots
    if remaining_slots < 0:
        remaining_slots = 0

    all_roles = db.query(Role).order_by(Role.id.asc()).all()

    priority_role_codes = [
        "lord_lady",
        "diplomat",
        "treasurer",
        "maester",
        "whisper_master",
    ]

    priority_role_names = {
        "lord_lady": "Лорд / Леди",
        "diplomat": "Дипломат",
        "treasurer": "Мастер над золотом",
        "maester": "Мейстер",
        "whisper_master": "Мастер шепота",
    }

    assignable_role_codes = [
        "diplomat",
        "maester",
        "treasurer",
        "whisper_master",
        "house_sworn",
    ]

    assignable_role_names = {
        "diplomat": "Дипломат",
        "maester": "Мейстер",
        "treasurer": "Мастер над золотом",
        "whisper_master": "Мастер шепота",
        "house_sworn": "Соратник Дома",
    }

    roles_by_code = {role.code: role for role in all_roles}
    roles_by_id = {role.id: role for role in all_roles}

    house_roles_status = []

    for role_code in priority_role_codes:
        role = roles_by_code.get(role_code)

        assigned_player = None
        if role:
            assigned_player = (
                db.query(Player)
                .filter(Player.house_id == house.id, Player.role_id == role.id)
                .first()
            )

        house_roles_status.append(
            {
                "code": role_code,
                "name": priority_role_names.get(role_code, role_code),
                "is_seeded": role is not None,
                "assigned_player": assigned_player,
                "is_vacant": role is not None and assigned_player is None,
            }
        )

    unique_role_codes = {"diplomat", "treasurer", "maester", "whisper_master"}

    taken_unique_role_codes = {
        role.code
        for role in db.query(Role)
        .join(Player, Player.role_id == Role.id)
        .filter(
            Player.house_id == house.id,
            Role.code.in_(unique_role_codes),
        )
        .all()
    }

    available_role_links_by_player_id = {}
    current_role_by_player_id = {}

    for player in players:
        if player.role_id and player.role_id in roles_by_id:
            current_role_by_player_id[player.id] = roles_by_id[player.role_id]
        else:
            current_role_by_player_id[player.id] = None

        if leader and player.id == leader.id:
            available_role_links_by_player_id[player.id] = []
            continue

        player_links = []

        for role_code in assignable_role_codes:
            role = roles_by_code.get(role_code)
            if not role:
                continue

            if player.role_id == role.id:
                continue

            if role_code in unique_role_codes and role_code in taken_unique_role_codes:
                continue

            player_links.append(
                {
                    "role_code": role_code,
                    "role_name": assignable_role_names.get(role_code, role_code),
                }
            )

        available_role_links_by_player_id[player.id] = player_links

    active_phase = (
        db.execute(
            text("""
                SELECT phase_type, status
                FROM game_phases
                WHERE game_id = :game_id AND status = 'active'
                ORDER BY id DESC
                LIMIT 1
            """),
            {"game_id": game.id}
        )
        .mappings()
        .first()
    )

    phase_name_map = {
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
    }

    active_host_round = (
        db.execute(
            text("""
                SELECT id, round_code, title, status, current_question_no, questions_total, answers_open
                FROM game_host_rounds
                WHERE game_id = :game_id AND status IN ('active', 'completed_waiting_host')
                ORDER BY id DESC
                LIMIT 1
            """),
            {"game_id": game.id}
        )
        .mappings()
        .first()
    )

    active_phase_type = active_phase["phase_type"] if active_phase else None
    active_phase_label = phase_name_map.get(active_phase_type, active_phase_type) if active_phase_type else None
    join_url = f"/delegation/join?game_code={game.room_code}&invite_code={house.invite_code}" if game else None
    join_url_absolute = f"{base_url}{join_url}" if base_url and join_url else join_url
    join_url_qr_src = f"/house/{house.invite_code}/join-qr.svg" if join_url_absolute else None

    return {
        "error": None,
        "house": house,
        "game": game,
        "leader": leader,
        "players": players,
        "remaining_slots": remaining_slots,
        "occupied_slots": occupied_slots,
        "house_roles_status": house_roles_status,
        "taken_unique_role_codes": taken_unique_role_codes,
        "available_role_links_by_player_id": available_role_links_by_player_id,
        "current_role_by_player_id": current_role_by_player_id,
        "house_ready": bool(house.is_ready),
        "leader_token": leader.player_token if leader else None,
        "leader_player_url": f"/house/{house.invite_code}/player/{leader.id}" if leader else None,
        "join_url": join_url,
        "join_url_absolute": join_url_absolute,
        "join_url_qr_src": join_url_qr_src,
        "active_phase_type": active_phase_type,
        "active_phase_label": active_phase_label,
        "active_host_round": active_host_round,
        "current_stage_title": (
            active_host_round["title"]
            if active_host_round
            else active_phase_label
            if active_phase_label
            else "Ожидание старта"
        ),
        "current_stage_subtitle": (
            "Раунд ведущего"
            if active_host_round
            else "Системная фаза"
            if active_phase_label
            else "Игра ещё не запущена"
        ),
        "can_use_diplomacy": active_phase_type == "diplomacy",
        "can_use_expedition": active_phase_type in {"map", "free_play"},
        "can_use_duel": active_phase_type == "duel",
        "can_use_alliance": active_phase_type == "diplomacy",
    }

def _build_player_room_context(db: Session, invite_code: str, player_id: int):
    house = db.query(House).filter(House.invite_code == invite_code).first()
    if not house:
        return {
            "error": "Дом по этой грамоте не найден",
            "house": None,
            "game": None,
            "leader": None,
            "player": None,
            "role": None,
            "players_count": 0,
            "is_leader": False,
            "active_host_round": None,
            "active_phase_label": None,
            "active_assignments_count": 0,
        }

    game = db.query(Game).filter(Game.id == house.game_id).first()
    leader = db.query(Player).filter(Player.id == house.leader_player_id).first()
    player = db.query(Player).filter(Player.id == player_id, Player.house_id == house.id).first()

    if not player:
        return {
            "error": "Участник не найден в этом Доме",
            "house": None,
            "game": None,
            "leader": None,
            "player": None,
            "role": None,
            "players_count": 0,
            "is_leader": False,
            "active_host_round": None,
            "active_phase_label": None,
            "active_assignments_count": 0,
        }

    players_count = db.query(Player).filter(Player.house_id == house.id).count()

    role = None
    if player.role_id:
        role = db.query(Role).filter(Role.id == player.role_id).first()

    active_phase = (
        db.execute(
            text("""
                SELECT phase_type, status
                FROM game_phases
                WHERE game_id = :game_id AND status = 'active'
                ORDER BY id DESC
                LIMIT 1
            """),
            {"game_id": game.id}
        )
        .mappings()
        .first()
    )

    phase_name_map = {
        "intermission": "Перерыв",
        "diplomacy": "Дипломатия",
        "market": "Рынок",
        "game_phase": "Игровая фаза",
        "court": "Суд Домов",
        "voting": "Голосование",
    }

    active_phase_label = None
    if active_phase:
        active_phase_label = phase_name_map.get(active_phase["phase_type"], active_phase["phase_type"])

    active_host_round = (
        db.execute(
            text("""
                SELECT id, round_code, title, status, current_question_no, questions_total, answers_open
                FROM game_host_rounds
                WHERE game_id = :game_id AND status IN ('active', 'completed_waiting_host')
                ORDER BY id DESC
                LIMIT 1
            """),
            {"game_id": game.id}
        )
        .mappings()
        .first()
    )

    active_assignments_count = (
        db.execute(
            text("""
                SELECT COUNT(*) AS cnt
                FROM game_assignments
                WHERE player_id = :player_id AND status = 'issued'
            """),
            {"player_id": player.id}
        )
        .mappings()
        .first()
    )

    return {
        "error": None,
        "house": house,
        "game": game,
        "leader": leader,
        "player": player,
        "role": role,
        "players_count": players_count,
        "is_leader": house.leader_player_id == player.id,
        "active_host_round": active_host_round,
        "active_phase_label": active_phase_label,
        "active_assignments_count": active_assignments_count["cnt"] if active_assignments_count else 0,
    }
