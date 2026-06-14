from pathlib import Path
import json

from sqlalchemy.orm import Session
from sqlalchemy import func
import yaml

from app.database import SessionLocal
from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.role import Role
from app.models.game_template import GameTemplate
from app.models.game_template_house import GameTemplateHouse
from app.models.game_template_role import GameTemplateRole
from app.models.game_template_act import GameTemplateAct
from app.models.game_template_map_node import GameTemplateMapNode
from app.models.game_template_task_pool import GameTemplateTaskPool
from app.models.game_template_task import GameTemplateTask
from app.models.game_assignment import GameAssignment
from app.models.game_host_round import GameHostRound
from app.models.game_scenario_template import GameScenarioTemplate
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.game_expedition import GameExpedition, GameExpeditionMember
from app.models.game_map_state import GameMapState
from app.models.game_map_visit import GameMapVisit
from datetime import datetime, timezone
from secrets import token_urlsafe
from app.models.game_phase import GamePhase
from app.models.game_deal import GameDeal
from app.models.game_duel import GameDuel
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import APIRouter, Request, Body, UploadFile, File, Form
import tempfile
from app.services.phase_service import is_phase_active
from app.services.gold_service import apply_admin_gold_adjustment
from app.services.resource_service import (
    apply_house_effect as _apply_house_effect,
    apply_transfer_between_houses as _apply_transfer_between_houses,
    validate_offer_against_house_balance as _validate_offer_against_house_balance,
    build_house_resources_snapshot as _build_house_resources_snapshot,
)
from app.services.diplomacy_service import (
    public_deal_status as _public_deal_status,
    propose_diplomacy_deal_logic as _propose_diplomacy_deal_logic,
    respond_diplomacy_deal_logic as _respond_diplomacy_deal_logic,
    counter_diplomacy_deal_logic as _counter_diplomacy_deal_logic,
    cancel_diplomacy_deal_logic as _cancel_diplomacy_deal_logic,
)

from app.services.assignment_service import (
    process_assignment_answer as _process_assignment_answer,
)

from app.services.host_round_service import (
    open_next_question_for_host_round as _open_next_question_for_host_round,
    finalize_host_round_by_host as _finalize_host_round_by_host,
    force_close_current_question_by_host as _force_close_current_question_by_host,
    pick_runtime_task_for_player as _pick_runtime_task_for_player,
)
from app.services.template_service import (
    load_template_bundle as _load_template_bundle,
    run_deep_validation_from_loaded as _run_deep_validation_from_loaded,
    validate_template_logic as _validate_template_logic,
    import_template_core_preview_logic as _import_template_core_preview_logic,
    import_template_core_real_logic as _import_template_core_real_logic,
    import_template_map_real_logic as _import_template_map_real_logic,
    import_template_task_pools_real_logic as _import_template_task_pools_real_logic,
    import_template_rounds_real_logic as _import_template_rounds_real_logic,
)

from app.services.phase_service import (
    has_active_phase as _has_active_phase,
    has_any_active_phase as _has_any_active_phase,
    open_game_phase_logic as _open_game_phase_logic,
    close_game_phase_logic as _close_game_phase_logic,
    get_game_phases_logic as _get_game_phases_logic,
    can_use_diplomacy_logic as _can_use_diplomacy_logic,
    can_use_map_logic as _can_use_map_logic,
)

from app.services.master_state_service import (
    get_game_master_state_logic as _get_game_master_state_logic,
    get_game_master_tv_state_logic as _get_game_master_tv_state_logic,
    host_round_debug_logic as _host_round_debug_logic,
)
from app.services.question_import_service import (
    build_questions_import_preview as _build_questions_import_preview,
    select_questions_by_limits as _select_questions_by_limits,
)
from app.services.media_prepare_service import (
    prepare_media_files as _prepare_media_files,
    slugify_media_ref as _slugify_media_ref,
)
from app.services.scenario_service import (
    import_scenario_logic as _import_scenario_logic,
    import_scenario_round_logic as _import_scenario_round_logic,
    list_scenarios_logic as _list_scenarios_logic,
    get_scenario_logic as _get_scenario_logic,
    get_game_scenario_logic as _get_game_scenario_logic,
    apply_scenario_to_game_logic as _apply_scenario_to_game_logic,
    get_scenario_director_logic as _get_scenario_director_logic,
    start_next_scenario_round_logic as _start_next_scenario_round_logic,
    advance_scenario_logic as _advance_scenario_logic,
)

from app.services.serialization_utils import (
    load_yaml_file as _load_yaml_file,
    safe_list_length as _safe_list_length,
    dump_json as _dump_json,
    load_json_text as _load_json_text,
    house_key_allowed as _house_key_allowed,
)

from app.services.game_context_service import (
    resolve_template_for_game as _resolve_template_for_game,
    resolve_round_template_for_game as _resolve_round_template_for_game,
)

from app.services.map_runtime_service import (
    get_map_state_payload as _get_map_state_payload,
    explore_location_by_player as _explore_location_by_player,
    reset_map_moves_for_house as _reset_map_moves_for_house,
)

from app.services.expedition_service import (
    create_expedition as _create_expedition,
    add_member as _add_member,
    get_expedition_roles as _get_expedition_roles,
    get_expedition_runtime_context as _get_expedition_runtime_context,
    approve_expedition as _approve_expedition,
)
from app.services.tower_service import (
    get_house_tower_payload as _get_house_tower_payload,
    add_tower_part as _add_tower_part,
    apply_tower_blueprint as _apply_tower_blueprint,
)
from app.services.duel_service import (
    create_duel_challenge as _create_duel_challenge,
    accept_duel as _accept_duel,
    refuse_duel as _refuse_duel,
    resolve_duel as _resolve_duel,
    serialize_duel as _serialize_duel,
    list_duels_for_game as _list_duels_for_game,
)
from app.services.court_service import (
    get_court_state_logic as _get_court_state_logic,
    generate_court_bracket_logic as _generate_court_bracket_logic,
    start_court_pair_logic as _start_court_pair_logic,
    open_court_question_logic as _open_court_question_logic,
    mark_court_result_logic as _mark_court_result_logic,
    court_extra_question_logic as _court_extra_question_logic,
    confirm_court_pair_winner_logic as _confirm_court_pair_winner_logic,
    next_court_pair_logic as _next_court_pair_logic,
    sync_court_question_runtime_logic as _sync_court_question_runtime_logic,
)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

BASE_DIR = Path(__file__).resolve().parent.parent
GAME_TEMPLATES_DIR = BASE_DIR / "game_templates"
MAP_LOCATIONS_FILE = GAME_TEMPLATES_DIR / "season1_core_v1" / "locations.yaml"


def _resolve_questions_import_template(db: Session):
    games_with_template = [
        game
        for game in db.query(Game).order_by(Game.id.asc()).all()
        if getattr(game, "template_code", None)
    ]

    if len(games_with_template) == 1:
        template_code = games_with_template[0].template_code
        template = (
            db.query(GameTemplate)
            .filter(GameTemplate.template_code == template_code)
            .first()
        )
        if template:
            return template

    templates = db.query(GameTemplate).order_by(GameTemplate.id.asc()).all()
    if len(templates) == 1:
        return templates[0]

    iron_game = next((game for game in games_with_template if game.room_code == "IRON01"), None)
    if iron_game and iron_game.template_code:
        template = (
            db.query(GameTemplate)
            .filter(GameTemplate.template_code == iron_game.template_code)
            .first()
        )
        if template:
            return template

    return None

print("BASE_DIR =", BASE_DIR)
print("GAME_TEMPLATES_DIR =", GAME_TEMPLATES_DIR)
print("MAP_LOCATIONS_FILE =", MAP_LOCATIONS_FILE)


def _issue_dev_player_token() -> str:
    return token_urlsafe(24)


def _ensure_dev_player_token(db: Session, player: Player) -> str:
    if player.player_token:
        return player.player_token

    while True:
        new_token = _issue_dev_player_token()
        exists = db.query(Player).filter(Player.player_token == new_token).first()
        if not exists:
            player.player_token = new_token
            db.flush()
            return new_token


def _generate_dev_invite_code(db: Session, room_code: str, suffix: str) -> str:
    base = f"{room_code.strip().upper()[:4]}{suffix.strip().upper()[:4]}"
    candidate = base[:8]

    if not db.query(House).filter(House.invite_code == candidate).first():
        return candidate

    counter = 2
    while True:
        alt_candidate = f"{base[:6]}{counter:02d}"[:8]
        if not db.query(House).filter(House.invite_code == alt_candidate).first():
            return alt_candidate
        counter += 1


@router.get("/scenario-admin", response_class=HTMLResponse)
async def scenario_admin_page(request: Request):
    return templates.TemplateResponse(
        request,
        "scenario_admin.html",
        {},
    )

ANSWER_MODE_BY_UI_TEMPLATE = {
    "truth_lie": "single_choice",
    "timeline": "ordered_list",
    "group_assignment": "group_assignment",
    "negotiation_offer": "single_choice",
    "resource_choice": "single_choice",
    "strategic_choice": "single_choice",
}

@router.get("/players/{room_code}")
def get_players_by_room_code(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        players = (
            db.query(Player)
            .filter(Player.game_id == game.id)
            .order_by(Player.id.asc())
            .all()
        )

        houses_by_id = {
            house.id: house
            for house in db.query(House).filter(House.game_id == game.id).all()
        }

        template_resolution = _resolve_template_for_game(db, game)
        resolved_template_code = None
        template_warning = None

        if template_resolution.get("ok"):
            resolved_template_code = template_resolution["template"].template_code
            if template_resolution.get("fallback_used"):
                template_warning = "Для игры используется fallback-шаблон, потому что у Game нет template_code."
        else:
            template_warning = template_resolution.get("message")

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
                "template_code": resolved_template_code,
            },
            "template_warning": template_warning,
            "players_count": len(players),
            "players": [
                {
                    "player_id": player.id,
                    "nickname": player.nickname,
                    "house_id": player.house_id,
                    "house_name": houses_by_id.get(player.house_id).name if houses_by_id.get(player.house_id) else None,
                    "role_id": player.role_id,
                    "role_code": player.role.code if player.role else None,
                    "role_name": player.role.name if player.role else None,
                }
                for player in players
            ],
        }

    finally:
        db.close()


@router.get("/houses/{room_code}")
def get_houses_by_room_code(room_code: str):
    db: Session = SessionLocal()

    try:
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

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "houses_count": len(houses),
            "houses": [
                {
                    "id": house.id,
                    "house_key": house.house_key,
                    "name": house.name,
                    "invite_code": house.invite_code,
                    "leader_player_id": house.leader_player_id,
                }
                for house in houses
            ],
        }

    finally:
        db.close()


@router.get("/games/{room_code}/tower/{house_id}")
def get_house_tower(room_code: str, house_id: int):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        house = (
            db.query(House)
            .filter(
                House.id == house_id,
                House.game_id == game.id,
            )
            .first()
        )

        if not house:
            return {
                "ok": False,
                "message": "Дом не найден в этой игре",
                "room_code": room_code,
                "house_id": house_id,
            }

        result = _get_house_tower_payload(
            db=db,
            game_id=game.id,
            house_id=house.id,
        )

        db.commit()

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "house": {
                "id": house.id,
                "house_key": house.house_key,
                "name": house.name,
            },
            "tower": result["tower"],
        }

    finally:
        db.close()


@router.post("/games/{room_code}/tower/{house_id}/add-part")
def add_house_tower_part(room_code: str, house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        house = (
            db.query(House)
            .filter(
                House.id == house_id,
                House.game_id == game.id,
            )
            .first()
        )

        if not house:
            return {
                "ok": False,
                "message": "Дом не найден в этой игре",
                "room_code": room_code,
                "house_id": house_id,
            }

        result = _add_tower_part(
            db=db,
            game_id=game.id,
            house_id=house.id,
            payload=payload,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()

        return {
            "ok": True,
            "message": result["message"],
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "house": {
                "id": house.id,
                "house_key": house.house_key,
                "name": house.name,
            },
            "tower": result["tower"],
            "applied_change": result["applied_change"],
        }

    finally:
        db.close()


@router.post("/games/{room_code}/tower/{house_id}/apply-blueprint")
def apply_house_tower_blueprint(room_code: str, house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        house = (
            db.query(House)
            .filter(
                House.id == house_id,
                House.game_id == game.id,
            )
            .first()
        )

        if not house:
            return {
                "ok": False,
                "message": "Дом не найден в этой игре",
                "room_code": room_code,
                "house_id": house_id,
            }

        result = _apply_tower_blueprint(
            db=db,
            game_id=game.id,
            house_id=house.id,
            payload=payload,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()

        return {
            "ok": True,
            "message": result["message"],
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "house": {
                "id": house.id,
                "house_key": house.house_key,
                "name": house.name,
            },
            "tower": result["tower"],
            "blueprint_debug": result["blueprint_debug"],
        }

    finally:
        db.close()


@router.get("/issue-role-task-by-player/{player_id}")
def issue_role_task_by_player(player_id: int):
    db: Session = SessionLocal()

    try:
        player = (
            db.query(Player)
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "ok": False,
                "message": "Игрок не найден",
                "player_id": player_id,
            }

        if not player.house:
            return {
                "ok": False,
                "message": "У игрока не найден дом",
                "player_id": player_id,
            }

        if not player.game:
            return {
                "ok": False,
                "message": "У игрока не найдена игра",
                "player_id": player_id,
            }

        runtime_pick = _pick_runtime_task_for_player(
            db=db,
            player=player,
            resolve_template_for_game_fn=_resolve_template_for_game,
            house_key_allowed_fn=_house_key_allowed,
        )

        if not runtime_pick.get("ok"):
            return runtime_pick

        selected_task = runtime_pick["task"]
        selected_pool = runtime_pick["pool"]

        existing_assignment = (
            db.query(GameAssignment)
            .filter(
                GameAssignment.game_id == player.game_id,
                GameAssignment.house_id == player.house_id,
                GameAssignment.player_id == player.id,
                GameAssignment.template_task_id == selected_task.id,
                GameAssignment.delivery_mode == "personal",
            )
            .first()
        )

        created_now = False

        if not existing_assignment:
            existing_assignment = GameAssignment(
                game_id=player.game_id,
                house_id=player.house_id,
                player_id=player.id,
                template_task_id=selected_task.id,
                template_pool_id=selected_pool.id if selected_pool else None,
                role_code=player.role.code if player.role else None,
                delivery_mode="personal",
                answer_mode=ANSWER_MODE_BY_UI_TEMPLATE.get(selected_task.ui_template, "text"),
                auto_check=True,
                status="issued",
                is_correct=None,
                result_applied=False,
                triggered_by_host=False,
                answered_by_player_id=None,
                answer_payload=None,
                result_payload=None,
            )
            db.add(existing_assignment)
            db.commit()
            db.refresh(existing_assignment)
            created_now = True

        return {
            "ok": True,
            "message": "Задание для игрока определено",
            "assignment_created_now": created_now,
            "player": {
                "id": player.id,
                "nickname": player.nickname,
                "role_code": player.role.code if player.role else None,
                "role_name": player.role.name if player.role else None,
            },
            "game": {
                "id": player.game.id,
                "room_code": player.game.room_code,
                "title": player.game.title,
                "template_code": runtime_pick["template"].template_code if runtime_pick.get("template") else None,
            },
            "house": {
                "id": player.house.id,
                "house_key": player.house.house_key,
                "name": player.house.name,
            },
            "pool": {
                "id": selected_pool.id if selected_pool else None,
                "pool_code": selected_pool.pool_code if selected_pool else None,
                "role_code": selected_pool.role_code if selected_pool else None,
                "assignment_type": selected_pool.assignment_type if selected_pool else None,
            },
            "task": {
                "id": selected_task.id,
                "task_code": selected_task.task_code,
                "title": selected_task.title,
                "prompt": selected_task.prompt,
                "ui_template": selected_task.ui_template,
                "difficulty": selected_task.difficulty,
                "act_min": selected_task.act_min,
                "act_max": selected_task.act_max,
                "allowed_house_keys": _load_json_text(selected_task.allowed_house_keys),
                "content": _load_json_text(selected_task.content_json),
                "reward": _load_json_text(selected_task.reward_json),
                "fail_effect": _load_json_text(selected_task.fail_effect_json),
            },
            "assignment": {
                "id": existing_assignment.id,
                "status": existing_assignment.status,
                "delivery_mode": existing_assignment.delivery_mode,
                "answer_mode": existing_assignment.answer_mode,
            },
        }

    finally:
        db.close()

@router.get("/game-assignments/{room_code}")
def get_game_assignments(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        assignments = (
            db.query(GameAssignment)
            .filter(GameAssignment.game_id == game.id)
            .order_by(GameAssignment.id.asc())
            .all()
        )

        task_ids = [a.template_task_id for a in assignments if a.template_task_id]
        tasks_by_id = {}

        if task_ids:
            tasks = (
                db.query(GameTemplateTask)
                .filter(GameTemplateTask.id.in_(task_ids))
                .all()
            )
            tasks_by_id = {task.id: task for task in tasks}

        players_by_id = {p.id: p for p in game.players}
        houses_by_id = {h.id: h for h in db.query(House).filter(House.game_id == game.id).all()}

        template_resolution = _resolve_template_for_game(db, game)

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
                "template_code": template_resolution.get("template").template_code
                if template_resolution.get("ok")
                else None,
            },
            "assignments_count": len(assignments),
            "assignments": [
                {
                    "id": assignment.id,
                    "host_round_id": assignment.host_round_id,
                    "player_id": assignment.player_id,
                    "player_nickname": players_by_id.get(assignment.player_id).nickname
                    if players_by_id.get(assignment.player_id)
                    else None,
                    "house_id": assignment.house_id,
                    "house_name": houses_by_id.get(assignment.house_id).name
                    if houses_by_id.get(assignment.house_id)
                    else None,
                    "role_code": assignment.role_code,
                    "delivery_mode": assignment.delivery_mode,
                    "answer_mode": assignment.answer_mode,
                    "status": assignment.status,
                    "is_correct": assignment.is_correct,
                    "result_applied": assignment.result_applied,
                    "template_pool_id": assignment.template_pool_id,
                    "template_task_id": assignment.template_task_id,
                    "task_code": tasks_by_id.get(assignment.template_task_id).task_code
                    if tasks_by_id.get(assignment.template_task_id)
                    else None,
                    "task_title": tasks_by_id.get(assignment.template_task_id).title
                    if tasks_by_id.get(assignment.template_task_id)
                    else None,
                }
                for assignment in assignments
            ],
        }

    finally:
        db.close()


@router.get("/host-led-start-for-role/{room_code}/{role_code}/{task_code}")
def host_led_start_for_role(room_code: str, role_code: str, task_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        template_resolution = _resolve_template_for_game(db, game)
        if not template_resolution.get("ok"):
            return template_resolution

        template = template_resolution["template"]

        template_task = (
            db.query(GameTemplateTask)
            .filter(
                GameTemplateTask.template_id == template.id,
                GameTemplateTask.task_code == task_code,
                GameTemplateTask.role_code == role_code,
            )
            .first()
        )

        if not template_task:
            return {
                "ok": False,
                "message": "Шаблонная задача не найдена для этой роли",
                "task_code": task_code,
                "role_code": role_code,
            }

        template_pool = (
            db.query(GameTemplateTaskPool)
            .filter(GameTemplateTaskPool.id == template_task.pool_id)
            .first()
        )

        if not template_pool:
            return {
                "ok": False,
                "message": "Не найден пул задачи",
                "task_code": task_code,
            }
        
        if not is_phase_active(db, game.id, "host_round"):
            return {
                "ok": False,
                "message": "Фаза host_round не активна",
            }

        host_round = GameHostRound(
            game_id=game.id,
            template_pool_id=template_pool.id,
            template_task_id=template_task.id,
            role_code=role_code,
            title=template_task.title,
            prompt=template_task.prompt,
            ui_template=template_task.ui_template,
            status="active",
        )
        db.add(host_round)
        db.commit()
        db.refresh(host_round)

        eligible_players = (
            db.query(Player)
            .filter(Player.game_id == game.id)
            .all()
        )

        created_assignments = []

        for player in eligible_players:
            if not player.role:
                continue

            if player.role.code != role_code:
                continue

            if not player.house:
                continue

            if not _house_key_allowed(template_task.allowed_house_keys, player.house.house_key):
                continue

            existing_assignment = (
                db.query(GameAssignment)
                .filter(
                    GameAssignment.host_round_id == host_round.id,
                    GameAssignment.player_id == player.id,
                    GameAssignment.template_task_id == template_task.id,
                )
                .first()
            )

            if existing_assignment:
                created_assignments.append(existing_assignment.id)
                continue

            assignment = GameAssignment(
                game_id=game.id,
                house_id=player.house_id,
                player_id=player.id,
                host_round_id=host_round.id,
                template_pool_id=template_pool.id,
                template_task_id=template_task.id,
                role_code=role_code,
                delivery_mode="host_led_broadcast",
                answer_mode=ANSWER_MODE_BY_UI_TEMPLATE.get(template_task.ui_template, "text"),
                auto_check=True,
                status="issued",
                is_correct=None,
                result_applied=False,
                triggered_by_host=True,
                answered_by_player_id=None,
                answer_payload=None,
                result_payload=None,
            )
            db.add(assignment)
            db.commit()
            db.refresh(assignment)

            created_assignments.append(assignment.id)

        return {
            "ok": True,
            "message": "Общий раунд ведущего запущен",
            "host_round": {
                "id": host_round.id,
                "game_id": host_round.game_id,
                "role_code": host_round.role_code,
                "title": host_round.title,
                "prompt": host_round.prompt,
                "ui_template": host_round.ui_template,
                "status": host_round.status,
            },
            "template": {
                "template_code": template.template_code,
                "name": template.name,
            },
            "task": {
                "task_code": template_task.task_code,
                "title": template_task.title,
                "role_code": template_task.role_code,
                "ui_template": template_task.ui_template,
                "allowed_house_keys": _load_json_text(template_task.allowed_house_keys),
            },
            "created_assignments_count": len(created_assignments),
            "created_assignment_ids": created_assignments,
        }

    finally:
        db.close()


@router.get("/game-host-rounds/{room_code}")
def get_game_host_rounds(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        rounds = (
            db.query(GameHostRound)
            .filter(GameHostRound.game_id == game.id)
            .order_by(GameHostRound.id.asc())
            .all()
        )

        assignments = (
            db.query(GameAssignment)
            .filter(GameAssignment.game_id == game.id)
            .filter(GameAssignment.host_round_id.isnot(None))
            .order_by(GameAssignment.id.asc())
            .all()
        )

        players_by_id = {p.id: p for p in db.query(Player).filter(Player.game_id == game.id).all()}
        houses_by_id = {h.id: h for h in db.query(House).filter(House.game_id == game.id).all()}

        rounds_payload = []

        for round_item in rounds:
            round_assignments = [a for a in assignments if a.host_round_id == round_item.id]

            rounds_payload.append(
                {
                    "host_round_id": round_item.id,
                    "role_code": round_item.role_code,
                    "title": round_item.title,
                    "prompt": round_item.prompt,
                    "ui_template": round_item.ui_template,
                    "status": round_item.status,
                    "assignments_count": len(round_assignments),
                    "assignments": [
                        {
                            "assignment_id": assignment.id,
                            "player_id": assignment.player_id,
                            "player_nickname": players_by_id.get(assignment.player_id).nickname
                            if players_by_id.get(assignment.player_id)
                            else None,
                            "house_id": assignment.house_id,
                            "house_name": houses_by_id.get(assignment.house_id).name
                            if houses_by_id.get(assignment.house_id)
                            else None,
                            "status": assignment.status,
                            "delivery_mode": assignment.delivery_mode,
                            "is_correct": assignment.is_correct,
                            "result_applied": assignment.result_applied,
                        }
                        for assignment in round_assignments
                    ],
                }
            )

        template_resolution = _resolve_template_for_game(db, game)

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
                "template_code": template_resolution.get("template").template_code
                if template_resolution.get("ok")
                else None,
            },
            "host_rounds_count": len(rounds),
            "host_rounds": rounds_payload,
        }

    finally:
        db.close()

@router.get("/scenarios")
def get_scenarios():
    db: Session = SessionLocal()

    try:
        return _list_scenarios_logic(db)

    finally:
        db.close()


@router.get("/scenarios/{scenario_code}")
def get_scenario(scenario_code: str):
    db: Session = SessionLocal()

    try:
        return _get_scenario_logic(db, scenario_code=scenario_code)

    finally:
        db.close()


@router.post("/scenarios/import")
def import_scenario(payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        return _import_scenario_logic(
            db,
            payload=payload,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()


@router.post("/scenarios/{scenario_code}/import-round")
def import_scenario_round(scenario_code: str, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        return _import_scenario_round_logic(
            db,
            scenario_code=scenario_code,
            payload=payload,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()


@router.get("/games/{room_code}/scenario")
def get_game_scenario(room_code: str):
    db: Session = SessionLocal()

    try:
        return _get_game_scenario_logic(db, room_code=room_code)

    finally:
        db.close()


@router.post("/games/{room_code}/scenario/apply")
def apply_game_scenario(room_code: str, scenario_code: str | None = None, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        request_payload = dict(payload) if isinstance(payload, dict) else {}
        if scenario_code is not None and "scenario_code" not in request_payload:
            request_payload["scenario_code"] = scenario_code
        return _apply_scenario_to_game_logic(db, room_code=room_code, payload=request_payload)

    finally:
        db.close()


@router.post("/games/{room_code}/reset-runtime")
def reset_game_runtime(room_code: str):
    db: Session = SessionLocal()

    try:
        if room_code not in {"IRON01", "LIVE01"}:
            return {
                "ok": False,
                "message": "Reset runtime разрешён только для тестовой комнаты IRON01",
                "room_code": room_code,
            }

        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        deleted = {}

        query = db.query(GameAssignment).filter(GameAssignment.game_id == game.id)
        deleted["assignments"] = query.count()
        query.delete(synchronize_session=False)

        host_round_question_ids = [
            row.id
            for row in db.query(GameHostRoundQuestion.id)
            .join(
                GameHostRound,
                GameHostRound.id == GameHostRoundQuestion.host_round_id,
            )
            .filter(GameHostRound.game_id == game.id)
            .all()
        ]

        deleted["host_round_questions"] = len(host_round_question_ids)

        if host_round_question_ids:
            db.query(GameHostRoundQuestion).filter(
                GameHostRoundQuestion.id.in_(host_round_question_ids)
            ).delete(synchronize_session=False)

        expedition_member_ids = [
            row.id
            for row in db.query(GameExpeditionMember.id)
            .join(
                GameExpedition,
                GameExpedition.id == GameExpeditionMember.expedition_id,
            )
            .filter(GameExpedition.game_id == game.id)
            .all()
        ]

        deleted["expedition_members"] = len(expedition_member_ids)

        if expedition_member_ids:
            db.query(GameExpeditionMember).filter(
                GameExpeditionMember.id.in_(expedition_member_ids)
            ).delete(synchronize_session=False)

        query = db.query(GameExpedition).filter(GameExpedition.game_id == game.id)
        deleted["expeditions"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GameDeal).filter(GameDeal.game_id == game.id)
        deleted["deals"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GameDuel).filter(GameDuel.game_id == game.id)
        deleted["duels"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GameHostRound).filter(GameHostRound.game_id == game.id)
        deleted["host_rounds"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GamePhase).filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type == "court",
        )
        deleted["court_phases"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GamePhase).filter(
            GamePhase.game_id == game.id,
            GamePhase.phase_type != "court",
        )
        deleted["phases"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GameMapVisit).filter(GameMapVisit.game_id == game.id)
        deleted["map_visits"] = query.count()
        query.delete(synchronize_session=False)

        query = db.query(GameMapState).filter(GameMapState.game_id == game.id)
        deleted["map_states"] = query.count()
        query.delete(synchronize_session=False)

        db.commit()

        return {
            "ok": True,
            "room_code": room_code,
            "deleted": deleted,
        }
    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось очистить runtime-данные игры",
            "room_code": room_code,
            "error": str(e),
        }
    finally:
        db.close()


@router.post("/games/{room_code}/seed-technical-run")
def seed_technical_run(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        required_role_codes = [
            "lord_lady",
            "maester",
            "diplomat",
            "treasurer",
            "whisper_master",
            "house_sworn",
        ]

        roles = (
            db.query(Role)
            .filter(Role.code.in_(required_role_codes))
            .all()
        )
        roles_by_code = {role.code: role for role in roles}
        missing_role_codes = [code for code in required_role_codes if code not in roles_by_code]

        if missing_role_codes:
            return {
                "ok": False,
                "message": "Не найдены обязательные роли для технического прогона",
                "missing_role_codes": missing_role_codes,
                "hint": "Проверьте seed ролей перед вызовом endpoint",
            }

        multi_role_supported = False
        multi_role_note = "multi-role не найден, роли Волка проверяются как одиночные"

        def ensure_house(*, house_name: str, house_key: str, team_size_declared: int, invite_suffix: str):
            house = (
                db.query(House)
                .filter(
                    House.game_id == game.id,
                    House.name == house_name,
                )
                .order_by(House.id.asc())
                .first()
            )

            if house:
                if not house.invite_code:
                    house.invite_code = _generate_dev_invite_code(db, game.room_code, invite_suffix)
                house.team_size_declared = team_size_declared
                if not house.house_key:
                    house.house_key = house_key
                db.flush()
                return house

            house = House(
                game_id=game.id,
                house_key=house_key,
                name=house_name,
                motto=None,
                color=None,
                team_size_declared=team_size_declared,
                invite_code=_generate_dev_invite_code(db, game.room_code, invite_suffix),
                entry_mode="technical_run",
                leader_player_id=None,
                resource_gold=0,
                resource_influence=0,
                resource_stone=0,
                resource_wood=0,
                resource_iron=0,
                resource_scroll=0,
                resource_key=0,
                resource_fire=0,
                fate_bias=0,
            )
            db.add(house)
            db.flush()
            return house

        def ensure_player(*, house: House, nickname: str, primary_role_code: str):
            player = (
                db.query(Player)
                .filter(
                    Player.game_id == game.id,
                    Player.house_id == house.id,
                    Player.nickname == nickname,
                )
                .order_by(Player.id.asc())
                .first()
            )

            role = roles_by_code[primary_role_code]

            if not player:
                player = Player(
                    game_id=game.id,
                    house_id=house.id,
                    nickname=nickname,
                    role_id=role.id,
                    player_token=None,
                )
                db.add(player)
                db.flush()
            else:
                player.role_id = role.id
                if player.house_id != house.id:
                    player.house_id = house.id
                if player.game_id != game.id:
                    player.game_id = game.id
                db.flush()

            _ensure_dev_player_token(db, player)
            db.flush()
            db.refresh(player)
            return player

        fire_house = ensure_house(
            house_name="Дом Огня",
            house_key="tech_fire",
            team_size_declared=6,
            invite_suffix="FIRE",
        )
        wolf_house = ensure_house(
            house_name="Дом Волка",
            house_key="tech_wolf",
            team_size_declared=4,
            invite_suffix="WOLF",
        )

        house_specs = [
            {
                "house": fire_house,
                "house_name": "Дом Огня",
                "players": [
                    {"nickname": "Огонь / Лорд", "role_code": "lord_lady", "extra_roles": []},
                    {"nickname": "Огонь / Мейстер", "role_code": "maester", "extra_roles": []},
                    {"nickname": "Огонь / Дипломат", "role_code": "diplomat", "extra_roles": []},
                    {"nickname": "Огонь / Казначей", "role_code": "treasurer", "extra_roles": []},
                    {"nickname": "Огонь / Шёпот", "role_code": "whisper_master", "extra_roles": []},
                    {"nickname": "Огонь / Соратник", "role_code": "house_sworn", "extra_roles": []},
                ],
                "leader_nickname": "Огонь / Лорд",
            },
            {
                "house": wolf_house,
                "house_name": "Дом Волка",
                "players": [
                    {"nickname": "Волк / Лорд", "role_code": "lord_lady", "extra_roles": ["treasurer"]},
                    {"nickname": "Волк / Мейстер", "role_code": "maester", "extra_roles": []},
                    {"nickname": "Волк / Дипломат", "role_code": "diplomat", "extra_roles": []},
                    {"nickname": "Волк / Шёпот", "role_code": "whisper_master", "extra_roles": ["house_sworn"]},
                ],
                "leader_nickname": "Волк / Лорд",
            },
        ]

        houses_payload = []

        for spec in house_specs:
            house = spec["house"]
            players_payload = []
            leader_player_id = house.leader_player_id

            for player_spec in spec["players"]:
                player = ensure_player(
                    house=house,
                    nickname=player_spec["nickname"],
                    primary_role_code=player_spec["role_code"],
                )

                if player.nickname == spec["leader_nickname"]:
                    leader_player_id = player.id

                role = roles_by_code[player_spec["role_code"]]
                players_payload.append(
                    {
                        "nickname": player.nickname,
                        "role_code": role.code,
                        "role_name": role.name,
                        "extra_roles": player_spec["extra_roles"] if multi_role_supported else [],
                        "player_token": player.player_token,
                        "player_url": f"http://127.0.0.1:8000/house/{house.invite_code}/player/{player.id}",
                    }
                )

            house.leader_player_id = leader_player_id
            db.flush()

            houses_payload.append(
                {
                    "house_name": spec["house_name"],
                    "players_count": len(players_payload),
                    "players": players_payload,
                }
            )

        db.commit()

        response = {
            "ok": True,
            "room_code": game.room_code,
            "houses": houses_payload,
            "multi_role_supported": multi_role_supported,
        }

        if not multi_role_supported:
            response["multi_role_note"] = multi_role_note

        return response

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось подготовить технический прогон игры",
            "room_code": room_code,
            "error": str(e),
        }
    finally:
        db.close()


@router.get("/games/{room_code}/scenario/director")
def get_scenario_director(room_code: str):
    db: Session = SessionLocal()

    try:
        return _get_scenario_director_logic(db, room_code=room_code)

    finally:
        db.close()


@router.post("/games/{room_code}/scenario/start-next-round")
def start_next_scenario_round(room_code: str):
    db: Session = SessionLocal()

    try:
        return _start_next_scenario_round_logic(
            db,
            room_code=room_code,
            start_series_round_fn=lambda db_obj, game_obj, round_code: _start_series_host_round_logic(
                db_obj,
                game_obj,
                round_code,
            ),
        )

    finally:
        db.close()


@router.post("/games/{room_code}/scenario/advance")
def advance_scenario(room_code: str, force: bool | None = None, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        request_payload = payload or {}
        if force is not None:
            request_payload = {
                **request_payload,
                "force": force,
            }
        return _advance_scenario_logic(
            db,
            room_code=room_code,
            payload=request_payload,
            finalize_host_round_fn=_finalize_host_round_by_host,
            start_series_round_fn=lambda db_obj, game_obj, round_code: _start_series_host_round_logic(
                db_obj,
                game_obj,
                round_code,
            ),
        )

    finally:
        db.close()

@router.get("/host-rounds/available/{room_code}")
def get_available_series_rounds(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        template_resolution = _resolve_template_for_game(db, game)
        if not template_resolution.get("ok"):
            return template_resolution

        template = template_resolution["template"]

        rounds = (
            db.query(RoundTemplate)
            .filter(RoundTemplate.template_id == template.id)
            .order_by(RoundTemplate.act_number.asc(), RoundTemplate.id.asc())
            .all()
        )

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "template": {
                "id": template.id,
                "template_code": template.template_code,
                "name": template.name,
            },
            "rounds_count": len(rounds),
            "rounds": [
                {
                    "id": round_item.id,
                    "round_code": round_item.round_code,
                    "title": round_item.title,
                    "act_number": round_item.act_number,
                    "round_kind": round_item.round_kind,
                    "questions_total": round_item.questions_total,
                }
                for round_item in rounds
            ],
        }

    finally:
        db.close()

def _start_series_host_round_logic(db: Session, game: Game, round_code: str):
    round_resolution = _resolve_round_template_for_game(db, game, round_code)
    if not round_resolution.get("ok"):
        return round_resolution

    round_template = round_resolution["round_template"]

    if not is_phase_active(db, game.id, "host_round"):
        return {
            "ok": False,
            "message": "Фаза host_round не активна",
        }

    host_round = GameHostRound(
        game_id=game.id,
        template_pool_id=None,
        template_task_id=None,
        round_template_id=round_template.id,
        round_code=round_template.round_code,
        act_number=round_template.act_number,
        round_kind=round_template.round_kind,
        role_code=round_template.questions[0].role_code if round_template.questions else "mixed",
        title=round_template.title,
        prompt=round_template.intro_text,
        ui_template=None,
        questions_total=round_template.questions_total,
        current_question_no=0,
        answers_open=False,
        intro_shown=False,
        outro_shown=False,
        status="active",
    )
    db.add(host_round)
    db.commit()
    db.refresh(host_round)

    return {
        "ok": True,
        "message": "???????????????? ?????????? ???????????????? ??????????????",
        "game": {
            "id": game.id,
            "room_code": game.room_code,
            "title": game.title,
        },
        "host_round": {
            "id": host_round.id,
            "round_code": host_round.round_code,
            "title": host_round.title,
            "act_number": host_round.act_number,
            "round_kind": host_round.round_kind,
            "questions_total": host_round.questions_total,
            "current_question_no": host_round.current_question_no,
            "status": host_round.status,
            "answers_open": host_round.answers_open,
        },
        "round_template": {
            "id": round_template.id,
            "round_code": round_template.round_code,
            "title": round_template.title,
            "check_mode": round_template.check_mode,
            "questions_total": round_template.questions_total,
        },
    }

@router.post("/host-rounds/start-series/{room_code}/{round_code}")
def start_series_host_round(room_code: str, round_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "???????? ???? ??????????????",
                "room_code": room_code,
            }

        return _start_series_host_round_logic(db, game, round_code)

    finally:
        db.close()
@router.post("/host-rounds/{host_round_id}/open-next-question")
def open_next_question_for_host_round(host_round_id: int):
    db: Session = SessionLocal()

    try:
        host_round = (
            db.query(GameHostRound)
            .filter(GameHostRound.id == host_round_id)
            .first()
        )

        if not host_round:
            return {
                "ok": False,
                "message": "Host round не найден",
                "host_round_id": host_round_id,
            }
        
        if not is_phase_active(db, host_round.game_id, "host_round"):
            return {
                "ok": False,
                "message": "Фаза host_round не активна",
            }

        result = _open_next_question_for_host_round(
            db=db,
            host_round=host_round,
            house_key_allowed_fn=_house_key_allowed,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        db.refresh(host_round)

        runtime_question = result["runtime_question"]
        question_template = result["question_template"]
        content = _load_json_text(question_template.content_json) or {}
        court_payload = None
        if host_round.round_code == "stage_court_battle":
            sync_result = _sync_court_question_runtime_logic(
                db,
                host_round.game.room_code,
                host_round_id=host_round.id,
            )
            if sync_result.get("ok"):
                db.commit()
                court_payload = sync_result.get("court")

        return {
            "ok": True,
            "message": "Следующий вопрос серии открыт",
            "host_round": {
                "id": host_round.id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
            },
            "runtime_question": {
                "id": runtime_question.id,
                "sequence_no": runtime_question.sequence_no,
                "status": runtime_question.status,
                "answers_open": runtime_question.answers_open,
            },
            "question_template": {
                "id": question_template.id,
                "question_code": question_template.question_code,
                "title": question_template.title,
                "prompt": question_template.prompt,
                "ui_template": question_template.ui_template,
                "answer_mode": question_template.answer_mode,
                "role_code": question_template.role_code,
                "time_limit_sec": content.get("time_limit_sec"),
                "timer": content.get("timer"),
                "duration_sec": content.get("duration_sec"),
                "content": content,
                "reward": _load_json_text(question_template.reward_json),
                "fail_effect": _load_json_text(question_template.fail_effect_json),
            },
            "created_assignments_count": len(result["created_assignment_ids"]),
            "created_assignment_ids": result["created_assignment_ids"],
            "court": court_payload,
        }

    finally:
        db.close()

@router.get("/host-rounds/{host_round_id}")
def get_series_host_round(host_round_id: int):
    db: Session = SessionLocal()

    try:
        host_round = (
            db.query(GameHostRound)
            .filter(GameHostRound.id == host_round_id)
            .first()
        )

        if not host_round:
            return {
                "ok": False,
                "message": "Host round не найден",
                "host_round_id": host_round_id,
            }

        runtime_questions = (
            db.query(GameHostRoundQuestion)
            .filter(GameHostRoundQuestion.host_round_id == host_round.id)
            .order_by(GameHostRoundQuestion.sequence_no.asc())
            .all()
        )

        assignments = (
            db.query(GameAssignment)
            .filter(GameAssignment.host_round_id == host_round.id)
            .order_by(GameAssignment.id.asc())
            .all()
        )

        players_by_id = {
            p.id: p
            for p in db.query(Player).filter(Player.game_id == host_round.game_id).all()
        }

        houses_by_id = {
            h.id: h
            for h in db.query(House).filter(House.game_id == host_round.game_id).all()
        }

        return {
            "ok": True,
            "host_round": {
                "id": host_round.id,
                "game_id": host_round.game_id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "act_number": host_round.act_number,
                "round_kind": host_round.round_kind,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
            },
            "runtime_questions_count": len(runtime_questions),
            "runtime_questions": [
                {
                    "id": rq.id,
                    "sequence_no": rq.sequence_no,
                    "status": rq.status,
                    "answers_open": rq.answers_open,
                    "check_mode": rq.check_mode,
                }
                for rq in runtime_questions
            ],
            "assignments_count": len(assignments),
            "assignments": [
                {
                    "assignment_id": assignment.id,
                    "host_round_question_id": assignment.host_round_question_id,
                    "player_id": assignment.player_id,
                    "player_nickname": players_by_id.get(assignment.player_id).nickname
                    if players_by_id.get(assignment.player_id)
                    else None,
                    "house_id": assignment.house_id,
                    "house_name": houses_by_id.get(assignment.house_id).name
                    if houses_by_id.get(assignment.house_id)
                    else None,
                    "delivery_mode": assignment.delivery_mode,
                    "answer_mode": assignment.answer_mode,
                    "status": assignment.status,
                    "is_correct": assignment.is_correct,
                    "result_applied": assignment.result_applied,
                }
                for assignment in assignments
            ],
        }

    finally:
        db.close()

@router.post("/host-rounds/{host_round_id}/host-continue")
def host_continue_after_completed_round(host_round_id: int):
    db: Session = SessionLocal()

    try:
        host_round = (
            db.query(GameHostRound)
            .filter(GameHostRound.id == host_round_id)
            .first()
        )

        if not is_phase_active(db, host_round.game_id, "host_round"):
            return {
                "ok": False,
                "message": "Фаза host_round не активна",
            }

        if not host_round:
            return {
                "ok": False,
                "message": "Host round не найден",
                "host_round_id": host_round_id,
            }

        result = _finalize_host_round_by_host(
            db=db,
            host_round=host_round,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        db.refresh(host_round)
        court_payload = None
        if host_round.round_code == "stage_court_battle":
            sync_result = _sync_court_question_runtime_logic(
                db,
                host_round.game.room_code,
                host_round_id=host_round.id,
            )
            if sync_result.get("ok"):
                db.commit()
                court_payload = sync_result.get("court")

        remaining_active_host_round = (
            db.query(GameHostRound)
            .filter(
                GameHostRound.game_id == host_round.game_id,
                GameHostRound.status.in_(["active", "completed_waiting_host"]),
            )
            .first()
        )
        if not remaining_active_host_round and is_phase_active(db, host_round.game_id, "host_round"):
            phase_close_result = _close_game_phase_logic(db, host_round.game.room_code, "host_round")
            if not phase_close_result.get("ok"):
                db.rollback()
                return phase_close_result
            db.commit()

        return {
            "ok": True,
            "message": "Раунд подтверждён ведущим и завершён",
            "host_round": {
                "id": host_round.id,
                "game_id": host_round.game_id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
            },
            "court": court_payload,
        }

    finally:
        db.close()
        
@router.post("/host-rounds/{host_round_id}/force-close-question")
def force_close_question_for_host_round(host_round_id: int):
    db: Session = SessionLocal()

    try:
        host_round = (
            db.query(GameHostRound)
            .filter(GameHostRound.id == host_round_id)
            .first()
        )
        if not is_phase_active(db, host_round.game_id, "host_round"):
            return {
                "ok": False,
                "message": "Фаза host_round не активна",
            }
        if not host_round:
            return {
                "ok": False,
                "message": "Host round не найден",
                "host_round_id": host_round_id,
            }

        result = _force_close_current_question_by_host(
            db=db,
            host_round=host_round,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        db.refresh(host_round)

        runtime_question = result["runtime_question"]
        court_payload = None
        if host_round.round_code == "stage_court_battle":
            sync_result = _sync_court_question_runtime_logic(
                db,
                host_round.game.room_code,
                host_round_id=host_round.id,
            )
            if sync_result.get("ok"):
                db.commit()
                court_payload = sync_result.get("court")

        return {
            "ok": True,
            "message": result["message"],
            "host_round": {
                "id": host_round.id,
                "round_code": host_round.round_code,
                "title": host_round.title,
                "status": host_round.status,
                "questions_total": host_round.questions_total,
                "current_question_no": host_round.current_question_no,
                "answers_open": host_round.answers_open,
            },
            "runtime_question": {
                "id": runtime_question.id,
                "sequence_no": runtime_question.sequence_no,
                "status": runtime_question.status,
                "answers_open": runtime_question.answers_open,
            },
            "expired_assignment_ids": result["expired_assignment_ids"],
            "completed_waiting_host": result["completed_waiting_host"],
            "court": court_payload,
        }

    finally:
        db.close()

@router.get("/validate-template/{template_code}")
def validate_template(template_code: str):
    return _validate_template_logic(
        template_code=template_code,
        game_templates_dir=GAME_TEMPLATES_DIR,
        load_yaml_file_fn=_load_yaml_file,
        safe_list_length_fn=_safe_list_length,
    )


@router.get("/template/{template_code}")
def get_template_core(template_code: str):
    db: Session = SessionLocal()

    try:
        template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()

        if not template:
            return {
                "ok": False,
                "message": "Шаблон не найден в БД",
                "template_code": template_code,
            }

        houses = (
            db.query(GameTemplateHouse)
            .filter(GameTemplateHouse.template_id == template.id)
            .order_by(GameTemplateHouse.id.asc())
            .all()
        )

        roles = (
            db.query(GameTemplateRole)
            .filter(GameTemplateRole.template_id == template.id)
            .order_by(GameTemplateRole.id.asc())
            .all()
        )

        acts = (
            db.query(GameTemplateAct)
            .filter(GameTemplateAct.template_id == template.id)
            .order_by(GameTemplateAct.act_number.asc())
            .all()
        )

        return {
            "ok": True,
            "template": {
                "id": template.id,
                "template_code": template.template_code,
                "name": template.name,
                "version": template.version,
                "description": template.description,
                "default_team_size_min": template.default_team_size_min,
                "default_team_size_max": template.default_team_size_max,
                "acts_total": template.acts_total,
                "supported_houses_min": template.supported_houses_min,
                "supported_houses_max": template.supported_houses_max,
                "recommended_houses": template.recommended_houses,
                "simultaneous_houses_supported": template.simultaneous_houses_supported,
                "allow_role_overlap_in_small_team": template.allow_role_overlap_in_small_team,
            },
            "houses": [
                {
                    "id": house.id,
                    "house_key": house.house_key,
                    "name": house.name,
                    "theme_tags": house.theme_tags,
                }
                for house in houses
            ],
            "roles": [
                {
                    "id": role.id,
                    "code": role.code,
                    "name": role.name,
                    "ui_track": role.ui_track,
                    "assignment_types": role.assignment_types,
                }
                for role in roles
            ],
            "acts": [
                {
                    "id": act.id,
                    "act_number": act.act_number,
                    "name": act.name,
                    "enabled_assignment_types": act.enabled_assignment_types,
                    "event_tags": act.event_tags,
                }
                for act in acts
            ],
        }

    finally:
        db.close()


@router.get("/template-map/{template_code}")
def get_template_map(template_code: str):
    db: Session = SessionLocal()

    try:
        template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()

        if not template:
            return {
                "ok": False,
                "message": "Шаблон не найден в БД",
                "template_code": template_code,
            }

        map_nodes = (
            db.query(GameTemplateMapNode)
            .filter(GameTemplateMapNode.template_id == template.id)
            .order_by(GameTemplateMapNode.id.asc())
            .all()
        )

        return {
            "ok": True,
            "template": {
                "id": template.id,
                "template_code": template.template_code,
                "name": template.name,
            },
            "map_nodes_count": len(map_nodes),
            "map_nodes": [
                {
                    "id": node.id,
                    "node_code": node.node_code,
                    "name": node.name,
                    "node_type": node.node_type,
                    "visible_for_roles": node.visible_for_roles,
                    "visible_for_houses": node.visible_for_houses,
                    "act_min": node.act_min,
                    "act_max": node.act_max,
                    "move_cost": node.move_cost,
                    "result_mode": node.result_mode,
                    "payload": node.payload,
                }
                for node in map_nodes
            ],
        }

    finally:
        db.close()


@router.get("/template-task-pools/{template_code}")
def get_template_task_pools(template_code: str):
    db: Session = SessionLocal()

    try:
        template = db.query(GameTemplate).filter(GameTemplate.template_code == template_code).first()

        if not template:
            return {
                "ok": False,
                "message": "Шаблон не найден в БД",
                "template_code": template_code,
            }

        pools = (
            db.query(GameTemplateTaskPool)
            .filter(GameTemplateTaskPool.template_id == template.id)
            .order_by(GameTemplateTaskPool.id.asc())
            .all()
        )

        tasks = (
            db.query(GameTemplateTask)
            .filter(GameTemplateTask.template_id == template.id)
            .order_by(GameTemplateTask.id.asc())
            .all()
        )

        return {
            "ok": True,
            "template": {
                "id": template.id,
                "template_code": template.template_code,
                "name": template.name,
            },
            "pools_count": len(pools),
            "tasks_count": len(tasks),
            "pools": [
                {
                    "id": pool.id,
                    "pool_code": pool.pool_code,
                    "role_code": pool.role_code,
                    "assignment_type": pool.assignment_type,
                    "selection_policy": pool.selection_policy,
                }
                for pool in pools
            ],
            "tasks": [
                {
                    "id": task.id,
                    "task_code": task.task_code,
                    "pool_id": task.pool_id,
                    "role_code": task.role_code,
                    "assignment_type": task.assignment_type,
                    "title": task.title,
                    "ui_template": task.ui_template,
                    "difficulty": task.difficulty,
                    "act_min": task.act_min,
                    "act_max": task.act_max,
                    "allowed_house_keys": task.allowed_house_keys,
                }
                for task in tasks
            ],
        }

    finally:
        db.close()


@router.get("/import-template-core/{template_code}")
def import_template_core(template_code: str):
    return _import_template_core_preview_logic(
        template_code=template_code,
        game_templates_dir=GAME_TEMPLATES_DIR,
        load_yaml_file_fn=_load_yaml_file,
    )


@router.get("/import-template-core-real/{template_code}")
def import_template_core_real(template_code: str):
    db: Session = SessionLocal()

    try:
        return _import_template_core_real_logic(
            db=db,
            template_code=template_code,
            game_templates_dir=GAME_TEMPLATES_DIR,
            load_yaml_file_fn=_load_yaml_file,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()


@router.get("/import-template-map-real/{template_code}")
def import_template_map_real(template_code: str):
    db: Session = SessionLocal()

    try:
        return _import_template_map_real_logic(
            db=db,
            template_code=template_code,
            game_templates_dir=GAME_TEMPLATES_DIR,
            load_yaml_file_fn=_load_yaml_file,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()


@router.get("/import-template-task-pools-real/{template_code}")
def import_template_task_pools_real(template_code: str):
    db: Session = SessionLocal()

    try:
        return _import_template_task_pools_real_logic(
            db=db,
            template_code=template_code,
            game_templates_dir=GAME_TEMPLATES_DIR,
            load_yaml_file_fn=_load_yaml_file,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()

@router.get("/import-template-rounds-real/{template_code}")
def import_template_rounds_real(template_code: str):
    db: Session = SessionLocal()

    try:
        return _import_template_rounds_real_logic(
            db=db,
            template_code=template_code,
            game_templates_dir=GAME_TEMPLATES_DIR,
            load_yaml_file_fn=_load_yaml_file,
            dump_json_fn=_dump_json,
        )

    finally:
        db.close()

@router.get("/validate-template-deep/{template_code}")
def validate_template_deep(template_code: str):
    bundle = _load_template_bundle(
        template_code=template_code,
        game_templates_dir=GAME_TEMPLATES_DIR,
        load_yaml_file_fn=_load_yaml_file,
    )

    if not bundle.get("ok"):
        return bundle

    return _run_deep_validation_from_loaded(
        template_code=bundle["template_code"],
        template_dir=bundle["template_dir"],
        loaded_files=bundle["loaded_files"],
    )

@router.post("/answer-assignment/{assignment_id}")
def answer_assignment(assignment_id: int, payload: dict):
    db: Session = SessionLocal()

    try:
        assignment = (
            db.query(GameAssignment)
            .filter(GameAssignment.id == assignment_id)
            .first()
        )

        if not assignment:
            return {
                "ok": False,
                "message": "Assignment не найден",
                "assignment_id": assignment_id,
            }

        result = _process_assignment_answer(
            db=db,
            assignment=assignment,
            payload=payload,
            load_json_text_fn=_load_json_text,
            dump_json_fn=_dump_json,
            apply_house_effect_fn=_apply_house_effect,
            build_house_resources_snapshot_fn=_build_house_resources_snapshot,
            open_next_question_for_host_round_fn=_open_next_question_for_host_round,
        )

        db.commit()
        db.refresh(assignment)

        template_task = result.get("template_task")
        round_question_template = result.get("round_question_template")
        result_payload = result["result_payload"]

        task_payload = None

        if template_task is not None:
            task_payload = {
                "source_type": "template_task",
                "id": template_task.id,
                "task_code": template_task.task_code,
                "title": template_task.title,
                "ui_template": template_task.ui_template,
            }
        elif round_question_template is not None:
            task_payload = {
                "source_type": "round_question_template",
                "id": round_question_template.id,
                "question_code": round_question_template.question_code,
                "title": round_question_template.title,
                "ui_template": round_question_template.ui_template,
            }

        return {
            "ok": True,
            "message": "Ответ на assignment обработан",
            "assignment": {
                "id": assignment.id,
                "game_id": assignment.game_id,
                "house_id": assignment.house_id,
                "player_id": assignment.player_id,
                "host_round_id": assignment.host_round_id,
                "host_round_question_id": assignment.host_round_question_id,
                "delivery_mode": assignment.delivery_mode,
                "answer_mode": assignment.answer_mode,
                "status": assignment.status,
                "is_correct": assignment.is_correct,
                "result_applied": assignment.result_applied,
                "answered_by_player_id": assignment.answered_by_player_id,
                "answered_at": assignment.answered_at.isoformat() if assignment.answered_at else None,
            },
            "task": task_payload,
            "result": result_payload,
            "house_resources_after": result["house_resources_after"],
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось обработать ответ на assignment",
            "error": str(e),
            "assignment_id": assignment_id,
        }

    finally:
        db.close()


@router.post("/games/{room_code}/open-phase/{phase_type}")
def open_game_phase(room_code: str, phase_type: str):
    db: Session = SessionLocal()

    try:
        result = _open_game_phase_logic(
            db=db,
            room_code=room_code,
            phase_type=phase_type,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    finally:
        db.close()


@router.post("/games/{room_code}/close-phase/{phase_type}")
def close_game_phase(room_code: str, phase_type: str):
    db: Session = SessionLocal()

    try:
        result = _close_game_phase_logic(
            db=db,
            room_code=room_code,
            phase_type=phase_type,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    finally:
        db.close()


@router.get("/games/{room_code}/phases")
def get_game_phases(room_code: str):
    db: Session = SessionLocal()

    try:
        return _get_game_phases_logic(
            db=db,
            room_code=room_code,
        )

    finally:
        db.close()


@router.get("/games/{room_code}/can-use-diplomacy")
def can_use_diplomacy(room_code: str):
    db: Session = SessionLocal()

    try:
        return _can_use_diplomacy_logic(
            db=db,
            room_code=room_code,
        )

    finally:
        db.close()


@router.get("/games/{room_code}/can-use-map")
def can_use_map(room_code: str):
    db: Session = SessionLocal()

    try:
        return _can_use_map_logic(
            db=db,
            room_code=room_code,
        )

    finally:
        db.close()
def can_use_diplomacy(room_code: str):
    db: Session = SessionLocal()

    try:
        return _can_use_diplomacy_logic(
            db=db,
            room_code=room_code,
        )

    finally:
        db.close()

@router.post("/games/{room_code}/diplomacy/propose-deal")
def propose_diplomacy_deal(room_code: str, payload: dict):
    db: Session = SessionLocal()

    try:
        result = _propose_diplomacy_deal_logic(
            db=db,
            room_code=room_code,
            payload=payload,
            has_active_phase_fn=_has_active_phase,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось создать дипломатическую сделку",
            "error": str(e),
            "room_code": room_code,
        }

    finally:
        db.close()

@router.post("/games/{room_code}/diplomacy/respond-deal/{deal_id}")
def respond_diplomacy_deal(room_code: str, deal_id: int, payload: dict):
    db: Session = SessionLocal()

    try:
        result = _respond_diplomacy_deal_logic(
            db=db,
            room_code=room_code,
            deal_id=deal_id,
            payload=payload,
            has_active_phase_fn=_has_active_phase,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось ответить на дипломатическую сделку",
            "error": str(e),
            "room_code": room_code,
            "deal_id": deal_id,
        }

    finally:
        db.close()

@router.post("/games/{room_code}/diplomacy/counter-deal/{deal_id}")
def counter_diplomacy_deal(room_code: str, deal_id: int, payload: dict):
    db: Session = SessionLocal()

    try:
        result = _counter_diplomacy_deal_logic(
            db=db,
            room_code=room_code,
            deal_id=deal_id,
            payload=payload,
            has_active_phase_fn=_has_active_phase,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось создать встречную дипломатическую сделку",
            "error": str(e),
            "room_code": room_code,
            "deal_id": deal_id,
        }

    finally:
        db.close()

@router.post("/games/{room_code}/diplomacy/cancel-deal/{deal_id}")
def cancel_diplomacy_deal(room_code: str, deal_id: int, payload: dict):
    db: Session = SessionLocal()

    try:
        result = _cancel_diplomacy_deal_logic(
            db=db,
            room_code=room_code,
            deal_id=deal_id,
            payload=payload,
            has_active_phase_fn=_has_active_phase,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось отменить дипломатическую сделку",
            "error": str(e),
            "room_code": room_code,
            "deal_id": deal_id,
        }

    finally:
        db.close()

@router.get("/games/{room_code}/deals")
def get_game_deals(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        deals = (
            db.query(GameDeal)
            .filter(GameDeal.game_id == game.id)
            .order_by(GameDeal.id.asc())
            .all()
        )

        houses = (
            db.query(House)
            .filter(House.game_id == game.id)
            .all()
        )
        houses_by_id = {house.id: house for house in houses}

        child_map = {}
        for deal in deals:
            if deal.parent_deal_id:
                child_map.setdefault(deal.parent_deal_id, []).append(deal.id)

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "deals_count": len(deals),
            "deals": [
                {
                    "id": deal.id,
                    "parent_deal_id": deal.parent_deal_id,
                    "child_deal_ids": child_map.get(deal.id, []),
                    "status": _public_deal_status(deal.status),
                    "from_house": {
                        "id": deal.from_house_id,
                        "house_key": houses_by_id.get(deal.from_house_id).house_key if houses_by_id.get(deal.from_house_id) else None,
                        "name": houses_by_id.get(deal.from_house_id).name if houses_by_id.get(deal.from_house_id) else None,
                    },
                    "to_house": {
                        "id": deal.to_house_id,
                        "house_key": houses_by_id.get(deal.to_house_id).house_key if houses_by_id.get(deal.to_house_id) else None,
                        "name": houses_by_id.get(deal.to_house_id).name if houses_by_id.get(deal.to_house_id) else None,
                    },
                    "offer": deal.offer,
                    "note": deal.note,
                    "created_at": deal.created_at.isoformat() if deal.created_at else None,
                    "responded_at": deal.responded_at.isoformat() if deal.responded_at else None,
                }
                for deal in deals
            ],
        }

    finally:
        db.close()


@router.post("/games/{room_code}/duels/challenge")
def create_game_duel_challenge(room_code: str, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        result = _create_duel_challenge(
            db=db,
            game_id=game.id,
            challenger_house_id=payload.get("challenger_house_id"),
            target_house_id=payload.get("target_house_id"),
            payload=payload,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось создать вызов на дуэль",
            "error": str(e),
            "room_code": room_code,
        }

    finally:
        db.close()


@router.post("/games/{room_code}/duels/{duel_id}/accept")
def accept_game_duel(room_code: str, duel_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        duel = (
            db.query(GameDuel)
            .filter(
                GameDuel.id == duel_id,
                GameDuel.game_id == game.id,
            )
            .first()
        )

        if not duel:
            return {
                "ok": False,
                "message": "Дуэль не найдена",
                "duel_id": duel_id,
                "room_code": room_code,
            }

        result = _accept_duel(
            db=db,
            duel=duel,
            payload=payload if isinstance(payload, dict) else {},
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось принять дуэль",
            "error": str(e),
            "room_code": room_code,
            "duel_id": duel_id,
        }

    finally:
        db.close()


@router.post("/games/{room_code}/duels/{duel_id}/refuse")
def refuse_game_duel(room_code: str, duel_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        duel = (
            db.query(GameDuel)
            .filter(
                GameDuel.id == duel_id,
                GameDuel.game_id == game.id,
            )
            .first()
        )

        if not duel:
            return {
                "ok": False,
                "message": "Дуэль не найдена",
                "duel_id": duel_id,
                "room_code": room_code,
            }

        result = _refuse_duel(
            db=db,
            duel=duel,
            payload=payload if isinstance(payload, dict) else {},
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось отклонить дуэль",
            "error": str(e),
            "room_code": room_code,
            "duel_id": duel_id,
        }

    finally:
        db.close()


@router.post("/games/{room_code}/duels/{duel_id}/resolve")
def resolve_game_duel(room_code: str, duel_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        duel = (
            db.query(GameDuel)
            .filter(
                GameDuel.id == duel_id,
                GameDuel.game_id == game.id,
            )
            .first()
        )

        if not duel:
            return {
                "ok": False,
                "message": "Дуэль не найдена",
                "duel_id": duel_id,
                "room_code": room_code,
            }

        result = _resolve_duel(
            db=db,
            duel=duel,
            payload=payload if isinstance(payload, dict) else {},
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось разрешить дуэль",
            "error": str(e),
            "room_code": room_code,
            "duel_id": duel_id,
        }

    finally:
        db.close()


@router.get("/games/{room_code}/duels")
def get_game_duels(room_code: str):
    db: Session = SessionLocal()

    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        duels = _list_duels_for_game(
            db=db,
            game_id=game.id,
        )

        return {
            "ok": True,
            "game": {
                "id": game.id,
                "room_code": game.room_code,
                "title": game.title,
            },
            "duels_count": len(duels),
            "duels": [
                _serialize_duel(duel)
                for duel in duels
            ],
        }

    finally:
        db.close()


@router.get("/games/{room_code}/map")
def get_game_map(room_code: str):
    db: Session = SessionLocal()

    try:
        result = _get_map_state_payload(
            db=db,
            room_code=room_code,
            locations_file_path=MAP_LOCATIONS_FILE,
        )

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось получить состояние карты",
            "error": str(e),
            "room_code": room_code,
        }

    finally:
        db.close()


@router.post("/games/{room_code}/map/explore")
def explore_game_map_location(room_code: str, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        if not _has_any_active_phase(db, game.id, ["map", "free_play"]):
            return {
                "ok": False,
                "message": "Карта сейчас недоступна",
                "reason": "Фазы map/free_play не активны",
                "room_code": room_code,
                "allowed_phase_types": ["map", "free_play"],
            }

        player_id = payload.get("player_id")
        location_code = payload.get("location_code")

        if not isinstance(player_id, int):
            return {
                "ok": False,
                "message": 'Поле "player_id" должно быть целым числом',
                "received_player_id": player_id,
            }

        if not isinstance(location_code, str) or not location_code.strip():
            return {
                "ok": False,
                "message": 'Поле "location_code" должно быть непустой строкой',
                "received_location_code": location_code,
            }

        result = _explore_location_by_player(
            db=db,
            room_code=room_code,
            player_id=player_id,
            location_code=location_code.strip(),
            locations_file_path=MAP_LOCATIONS_FILE,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось выполнить ход по карте",
            "error": str(e),
            "room_code": room_code,
        }

    finally:
        db.close()

@router.post("/houses/{house_id}/expeditions")
def create_house_expedition(house_id: int):
    db = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()

        if not house:
            return {"ok": False, "message": "Дом не найден"}

        expedition = _create_expedition(
            db,
            game_id=house.game_id,
            house_id=house.id,
        )

        if isinstance(expedition, dict) and not expedition.get("ok", True):
            db.rollback()
            return expedition

        db.commit()

        return {
            "ok": True,
            "expedition": {
                "id": expedition.id,
                "house_id": expedition.house_id,
                "status": expedition.status,
            },
        }

    finally:
        db.close()

@router.post("/expeditions/{expedition_id}/members")
def add_expedition_member(expedition_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player_id = payload.get("player_id")

        if not isinstance(player_id, int):
            return {
                "ok": False,
                "message": 'Поле "player_id" должно быть целым числом',
                "received_player_id": player_id,
            }

        expedition = (
            db.query(GameExpedition)
            .filter(GameExpedition.id == expedition_id)
            .first()
        )

        if not expedition:
            return {
                "ok": False,
                "message": "Экспедиция не найдена",
                "expedition_id": expedition_id,
            }

        player = (
            db.query(Player)
            .filter(Player.id == player_id)
            .first()
        )

        if not player:
            return {
                "ok": False,
                "message": "Игрок не найден",
                "player_id": player_id,
            }

        if player.game_id != expedition.game_id:
            return {
                "ok": False,
                "message": "Игрок не принадлежит игре этой экспедиции",
                "player_id": player_id,
                "player_game_id": player.game_id,
                "expedition_game_id": expedition.game_id,
            }

        if player.house_id != expedition.house_id:
            return {
                "ok": False,
                "message": "Игрок не принадлежит дому этой экспедиции",
                "player_id": player_id,
                "player_house_id": player.house_id,
                "expedition_house_id": expedition.house_id,
            }

        member = _add_member(
            db=db,
            expedition_id=expedition_id,
            player_id=player_id,
        )

        db.commit()

        return {
            "ok": True,
            "message": "Игрок добавлен в экспедицию",
            "expedition": {
                "id": expedition.id,
                "game_id": expedition.game_id,
                "house_id": expedition.house_id,
                "status": expedition.status,
            },
            "member": {
                "id": member.id,
                "player_id": member.player_id,
            },
            "player": {
                "id": player.id,
                "nickname": player.nickname,
                "role_code": player.role.code if player.role else None,
                "role_name": player.role.name if player.role else None,
            },
        }

    finally:
        db.close()


@router.post("/expeditions/{expedition_id}/approve")
def approve_house_expedition(expedition_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        player_id = payload.get("player_id")

        if not isinstance(player_id, int):
            return {
                "ok": False,
                "message": 'Поле "player_id" должно быть целым числом',
                "received_player_id": player_id,
            }

        expedition = (
            db.query(GameExpedition)
            .filter(GameExpedition.id == expedition_id)
            .first()
        )

        if not expedition:
            return {
                "ok": False,
                "message": "Экспедиция не найдена",
                "expedition_id": expedition_id,
            }

        result = _approve_expedition(
            db=db,
            expedition=expedition,
            player_id=player_id,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        db.refresh(expedition)

        approved_by = result["approved_by"]

        return {
            "ok": True,
            "message": result["message"],
            "expedition": {
                "id": expedition.id,
                "game_id": expedition.game_id,
                "house_id": expedition.house_id,
                "status": expedition.status,
                "leader_player_id": expedition.leader_player_id,
                "approved_by_player_id": expedition.approved_by_player_id,
                "approved_at": expedition.approved_at.isoformat() if expedition.approved_at else None,
            },
            "approved_by": {
                "id": approved_by.id,
                "nickname": approved_by.nickname,
                "role_code": approved_by.role.code if approved_by.role else None,
                "role_name": approved_by.role.name if approved_by.role else None,
            },
            "expedition_debug": result["expedition_debug"],
        }

    finally:
        db.close()


@router.post("/games/{room_code}/map/explore-expedition")
def explore_game_map_expedition(room_code: str, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        game = db.query(Game).filter(Game.room_code == room_code).first()

        if not game:
            return {
                "ok": False,
                "message": "Игра не найдена",
                "room_code": room_code,
            }

        if not _has_any_active_phase(db, game.id, ["map", "free_play"]):
            return {
                "ok": False,
                "message": "Карта сейчас недоступна для экспедиции",
                "reason": "Фазы map/free_play не активны",
                "room_code": room_code,
                "allowed_phase_types": ["map", "free_play"],
            }

        expedition_id = payload.get("expedition_id")
        location_code = payload.get("location_code")

        if not isinstance(expedition_id, int):
            return {
                "ok": False,
                "message": 'Поле "expedition_id" должно быть целым числом',
                "received_expedition_id": expedition_id,
            }

        if not isinstance(location_code, str) or not location_code.strip():
            return {
                "ok": False,
                "message": 'Поле "location_code" должно быть непустой строкой',
                "received_location_code": location_code,
            }

        expedition = (
            db.query(GameExpedition)
            .filter(GameExpedition.id == expedition_id)
            .first()
        )

        if not expedition:
            return {
                "ok": False,
                "message": "Экспедиция не найдена",
                "expedition_id": expedition_id,
            }

        if expedition.game_id != game.id:
            return {
                "ok": False,
                "message": "Экспедиция не принадлежит этой игре",
                "expedition_id": expedition_id,
                "room_code_game_id": game.id,
            }

        members = (
            db.query(GameExpeditionMember)
            .filter(GameExpeditionMember.expedition_id == expedition.id)
            .order_by(GameExpeditionMember.id.asc())
            .all()
        )

        if not members:
            return {
                "ok": False,
                "message": "В экспедиции нет участников",
                "expedition_id": expedition.id,
            }

        expedition_context = _get_expedition_runtime_context(db, expedition)

        if expedition_context["requires_lord_approval"] and not expedition_context["approved"]:
            return {
                "ok": False,
                "message": "Экспедиция не утверждена Лордом / Леди",
                "active_host_round": None,
                "expedition": {
                    "id": expedition.id,
                    "house_id": expedition.house_id,
                    "status": expedition.status,
                    "target_location_code": expedition.target_location_code,
                },
                "expedition_debug": expedition_context,
                "current_round": None,
            }

        first_member = members[0]
        first_player = (
            db.query(Player)
            .filter(Player.id == first_member.player_id)
            .first()
        )

        if not first_player:
            return {
                "ok": False,
                "message": "Первый участник экспедиции не найден",
                "player_id": first_member.player_id,
            }

        result = _explore_location_by_player(
            db=db,
            room_code=room_code,
            player_id=first_player.id,
            location_code=location_code.strip(),
            locations_file_path=MAP_LOCATIONS_FILE,
            expedition_id=expedition.id,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        expedition.status = "resolved"
        expedition.target_location_code = location_code.strip()

        expedition_role_codes = _get_expedition_roles(db, expedition.id)

        db.commit()

        result["expedition"] = {
            "id": expedition.id,
            "house_id": expedition.house_id,
            "status": expedition.status,
            "target_location_code": expedition.target_location_code,
            "member_ids": [m.player_id for m in members],
            "role_codes": expedition_role_codes,
            "leader_player_id": expedition.leader_player_id,
            "approved_by_player_id": expedition.approved_by_player_id,
            "approved_at": expedition.approved_at.isoformat() if expedition.approved_at else None,
        }

        if isinstance(result.get("expedition_debug"), dict):
            result["expedition_debug"]["approved"] = expedition_context["approved"]
            result["expedition_debug"]["approved_by_player_id"] = expedition_context["approved_by_player_id"]
            result["expedition_debug"]["leader_player_id"] = expedition_context["leader_player_id"]
            result["expedition_debug"]["members_count"] = expedition_context["members_count"]
            result["expedition_debug"]["approval_required"] = expedition_context["requires_lord_approval"]
            result["expedition_debug"]["fallback_without_lord"] = expedition_context["fallback_without_lord"]

        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось выполнить ход по карте через экспедицию",
            "error": str(e),
            "room_code": room_code,
        }

    finally:
        db.close()
@router.post("/houses/{house_id}/map/reset-moves")
def reset_house_map_moves(house_id: int, payload: dict = Body(default={})):
    db: Session = SessionLocal()

    try:
        if payload is None:
            payload = {}

        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        moves_total = payload.get("moves_total")

        if moves_total is not None and not isinstance(moves_total, int):
            return {
                "ok": False,
                "message": 'Поле "moves_total" должно быть целым числом или отсутствовать',
                "received_moves_total": moves_total,
            }

        result = _reset_map_moves_for_house(
            db=db,
            house_id=house_id,
            moves_total=moves_total,
        )

        if not result.get("ok"):
            db.rollback()
            return result

        db.commit()
        return result

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось сбросить ходы карты для дома",
            "error": str(e),
            "house_id": house_id,
        }

    finally:
        db.close()

@router.get("/game-master/{room_code}/state")
def get_game_master_state(room_code: str):
    db: Session = SessionLocal()

    try:
        return _get_game_master_state_logic(
            db=db,
            room_code=room_code,
            public_deal_status_fn=_public_deal_status,
            load_json_text_fn=_load_json_text,
        )

    finally:
        db.close()


@router.get("/game-master/{room_code}/tv-state")
def get_game_master_tv_state(room_code: str):
    db: Session = SessionLocal()

    try:
        return _get_game_master_tv_state_logic(
            db=db,
            room_code=room_code,
            public_deal_status_fn=_public_deal_status,
            load_json_text_fn=_load_json_text,
        )

    finally:
        db.close()

@router.post("/houses/{house_id}/gold-adjust")
def adjust_house_gold_via_ledger(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
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

        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        gold_delta = payload.get("gold_delta")
        reason = payload.get("reason")
        comment = payload.get("comment")
        performed_by_player_id = payload.get("performed_by_player_id")

        if not isinstance(gold_delta, int):
            return {
                "ok": False,
                "message": 'Поле "gold_delta" должно быть целым числом',
                "received_gold_delta": gold_delta,
            }

        if gold_delta == 0:
            return {
                "ok": False,
                "message": 'Поле "gold_delta" не должно быть равно нулю',
            }

        if not isinstance(reason, str) or not reason.strip():
            return {
                "ok": False,
                "message": 'Поле "reason" обязательно и должно быть непустой строкой',
            }

        if performed_by_player_id is not None and not isinstance(performed_by_player_id, int):
            return {
                "ok": False,
                "message": 'Поле "performed_by_player_id" должно быть целым числом или отсутствовать',
                "received_performed_by_player_id": performed_by_player_id,
            }

        result = apply_admin_gold_adjustment(
            db=db,
            house=house,
            gold_delta=gold_delta,
            reason=reason.strip(),
            comment=comment,
            performed_by_player_id=performed_by_player_id,
        )

        db.commit()
        db.refresh(house)

        return {
            "ok": True,
            "message": "Служебная корректировка золота проведена",
            "house": {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            },
            "gold_before": result.balance_before,
            "gold_after": result.balance_after,
            "gold_delta": gold_delta,
            "transaction_id": result.transaction_id,
            "reason": reason.strip(),
            "comment": comment,
            "performed_by_player_id": performed_by_player_id,
        }

    except Exception as e:
        db.rollback()
        return {
            "ok": False,
            "message": "Не удалось провести корректировку золота",
            "error": str(e),
            "house_id": house_id,
        }

    finally:
        db.close()

@router.post("/houses/{house_id}/resource-adjust")
def adjust_house_resource(house_id: int, payload: dict = Body(...)):
    db: Session = SessionLocal()

    try:
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

        if not isinstance(payload, dict):
            return {
                "ok": False,
                "message": "Тело запроса должно быть JSON-объектом",
            }

        resource = payload.get("resource")
        delta = payload.get("delta")
        if resource == "gold":
            return {
                "ok": False,
                "message": "Золото Дома нельзя изменять напрямую.",
                "hint": "Используйте сделки, PvP или решения казны.",
            }
        allowed_resources = {
            "gold": "resource_gold",
            "influence": "resource_influence",
            "stone": "resource_stone",
            "wood": "resource_wood",
            "iron": "resource_iron",
            "scroll": "resource_scroll",
            "key": "resource_key",
            "fire": "resource_fire",
        }

        if resource not in allowed_resources:
            return {
                "ok": False,
                "message": "Недопустимый ресурс",
                "allowed_resources": list(allowed_resources.keys()),
                "received_resource": resource,
            }

        if not isinstance(delta, int):
            return {
                "ok": False,
                "message": 'Поле "delta" должно быть целым числом',
                "received_delta": delta,
            }

        field_name = allowed_resources[resource]
        current_value = getattr(house, field_name, 0)
        new_value = current_value + delta

        if new_value < 0:
            new_value = 0

        setattr(house, field_name, new_value)

        db.commit()
        db.refresh(house)

        return {
            "ok": True,
            "message": "Ресурс дома обновлён",
            "house": {
                "id": house.id,
                "name": house.name,
                "house_key": house.house_key,
            },
            "resource": resource,
            "old_value": current_value,
            "delta": delta,
            "new_value": new_value,
            "resources": {
                "gold": house.resource_gold,
                "influence": house.resource_influence,
                "stone": house.resource_stone,
                "wood": house.resource_wood,
                "iron": house.resource_iron,
                "scroll": house.resource_scroll,
                "key": house.resource_key,
                "fire": house.resource_fire,
            },
        }

    finally:
        db.close()


@router.post("/questions/import")
async def import_questions_preview(
    file: UploadFile = File(...),
    dry_run: str = Form("true"),
    target_round_code: str = Form("imported_warmup_test"),
    true_false_limit: int = Form(5),
    single_choice_limit: int = Form(5),
    free_text_limit: int = Form(3),
    media_limit: int = Form(0),
    prefer_media: str = Form("false"),
    clear_existing: str = Form("false"),
):
    dry_run_value = str(dry_run or "").strip().lower()
    is_dry_run = dry_run_value in {"true", "1", "yes"}
    prefer_media_value = str(prefer_media or "").strip().lower() in {"true", "1", "yes"}
    clear_existing_value = str(clear_existing or "").strip().lower() in {"true", "1", "yes"}
    target_round_code = (target_round_code or "imported_warmup_test").strip() or "imported_warmup_test"

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".docx", ".xlsx"}:
        return {
            "ok": False,
            "message": "?????????????? ?????? ????? DOCX ? XLSX",
            "filename": file.filename,
        }

    temp_path = None
    db: Session | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            content = await file.read()
            tmp.write(content)

        preview = _build_questions_import_preview(temp_path)
        selected_preview = _select_questions_by_limits(
            preview.get("questions", []),
            true_false_limit=true_false_limit,
            single_choice_limit=single_choice_limit,
            free_text_limit=free_text_limit,
            media_limit=media_limit,
            prefer_media=prefer_media_value,
        )

        preview["filename"] = file.filename
        preview["target_round_code"] = target_round_code
        preview["dry_run"] = is_dry_run
        preview["media_limit"] = media_limit
        preview["prefer_media"] = prefer_media_value
        preview["preview_selected"] = selected_preview

        if is_dry_run:
            return preview

        db = SessionLocal()
        template = _resolve_questions_import_template(db)
        if not template:
            return {
                "ok": False,
                "message": "\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u043e\u043f\u0440\u0435\u0434\u0435\u043b\u0438\u0442\u044c \u0448\u0430\u0431\u043b\u043e\u043d \u0438\u0433\u0440\u044b \u0434\u043b\u044f \u0438\u043c\u043f\u043e\u0440\u0442\u0430 \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432",
                "filename": file.filename,
                "target_round_code": target_round_code,
            }

        round_template = (
            db.query(RoundTemplate)
            .filter(
                RoundTemplate.template_id == template.id,
                RoundTemplate.round_code == target_round_code,
            )
            .first()
        )

        if not round_template:
            round_template = RoundTemplate(
                template_id=template.id,
                scenario_id=None,
                round_code=target_round_code,
                import_key=f"question_import:{target_round_code}",
                title="",
                order_no=999,
                act_number=1,
                round_type="imported",
                round_kind="series",
                check_mode="auto",
                questions_total=0,
                time_limit_sec=None,
                is_host_led=True,
                is_optional=True,
                bar_window_opens=False,
                scoring_mode="standard",
                question_transition_mode="manual",
                round_transition_mode="manual",
                intro_text="",
                outro_text=None,
            )
            db.add(round_template)
            db.flush()

        round_template.import_key = f"question_import:{target_round_code}"
        round_template.title = f"\u0418\u043c\u043f\u043e\u0440\u0442 \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432: {target_round_code}"
        round_template.order_no = 999
        round_template.act_number = 1
        round_template.round_type = "imported"
        round_template.round_kind = "series"
        round_template.check_mode = "auto"
        round_template.time_limit_sec = None
        round_template.is_host_led = True
        round_template.is_optional = True
        round_template.bar_window_opens = False
        round_template.scoring_mode = "standard"
        round_template.question_transition_mode = "manual"
        round_template.round_transition_mode = "manual"
        round_template.intro_text = "\u0418\u043c\u043f\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0439 \u0442\u0435\u0441\u0442\u043e\u0432\u044b\u0439 \u0440\u0430\u0443\u043d\u0434 \u0432\u043e\u043f\u0440\u043e\u0441\u043e\u0432"
        round_template.outro_text = None

        if clear_existing_value:
            existing_question_ids = [
                row[0]
                for row in db.query(RoundQuestionTemplate.id)
                .filter(RoundQuestionTemplate.round_template_id == round_template.id)
                .all()
            ]
            existing_host_round_ids = [
                row[0]
                for row in db.query(GameHostRound.id)
                .filter(
                    GameHostRound.round_template_id == round_template.id,
                    GameHostRound.round_code == target_round_code,
                )
                .all()
            ]
            existing_runtime_question_ids = []
            if existing_host_round_ids:
                existing_runtime_question_ids = [
                    row[0]
                    for row in db.query(GameHostRoundQuestion.id)
                    .filter(GameHostRoundQuestion.host_round_id.in_(existing_host_round_ids))
                    .all()
                ]

            if existing_runtime_question_ids:
                db.query(GameAssignment).filter(
                    GameAssignment.host_round_question_id.in_(existing_runtime_question_ids)
                ).delete(synchronize_session=False)
                db.query(GameHostRoundQuestion).filter(
                    GameHostRoundQuestion.id.in_(existing_runtime_question_ids)
                ).delete(synchronize_session=False)

            if existing_host_round_ids:
                db.query(GameAssignment).filter(
                    GameAssignment.host_round_id.in_(existing_host_round_ids)
                ).delete(synchronize_session=False)
                db.query(GameHostRound).filter(
                    GameHostRound.id.in_(existing_host_round_ids)
                ).delete(synchronize_session=False)

            if existing_question_ids:
                db.query(RoundQuestionTemplate).filter(
                    RoundQuestionTemplate.id.in_(existing_question_ids)
                ).delete(synchronize_session=False)

        selected_questions = selected_preview["selected_questions"]
        created_question_codes: list[str] = []

        for sequence_no, item in enumerate(selected_questions, start=1):
            question_code = item.get("question_code") or f"{target_round_code}_{sequence_no:03d}"
            existing_question = (
                db.query(RoundQuestionTemplate)
                .filter(
                    RoundQuestionTemplate.round_template_id == round_template.id,
                    RoundQuestionTemplate.question_code == question_code,
                )
                .first()
            )

            if not existing_question:
                existing_question = RoundQuestionTemplate(
                    round_template_id=round_template.id,
                    question_code=question_code,
                )
                db.add(existing_question)

            question_type = item.get("type")
            ui_template = (
                "truth_lie" if question_type == "true_false"
                else "single_choice" if question_type == "single_choice"
                else "free_text"
            )

            existing_question.sequence_no = sequence_no
            existing_question.role_code = item.get("role_code") or "maester"
            existing_question.title = item.get("prompt")
            existing_question.prompt = item.get("prompt")
            existing_question.ui_template = ui_template
            existing_question.answer_mode = ANSWER_MODE_BY_UI_TEMPLATE.get(ui_template, "single")
            existing_question.auto_check = True
            existing_question.manual_check_allowed = False
            existing_question.allowed_house_keys = _dump_json([])
            existing_question.content_json = _dump_json(
                {
                    "options": item.get("options") or [],
                    "correct_answer": item.get("correct_answer"),
                    "explanation": item.get("explanation"),
                    "media_type": item.get("media_type") or "none",
                    "media_ref": item.get("media_ref") or "",
                    "is_media_question": bool(item.get("is_media_question")),
                    "difficulty": item.get("difficulty") or "easy",
                }
            )
            existing_question.reward_json = _dump_json({})
            existing_question.fail_effect_json = _dump_json({})
            created_question_codes.append(question_code)

        round_template.questions_total = len(selected_questions)
        db.commit()

        return {
            "ok": True,
            "filename": file.filename,
            "dry_run": False,
            "target_round_code": target_round_code,
            "template": {
                "id": template.id,
                "template_code": template.template_code,
                "name": template.name,
            },
            "imported_count": len(selected_questions),
            "by_type": selected_preview["by_type"],
            "created_question_codes": created_question_codes,
        }
    except Exception as exc:
        if db is not None:
            db.rollback()
        return {
            "ok": False,
            "message": f"?? ??????? ????????? ??? ????????????? ????: {exc}",
            "filename": file.filename,
        }
    finally:
        if db is not None:
            db.close()
        try:
            await file.close()
        except Exception:
            pass
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


@router.post("/questions/prepare-media")
def prepare_question_media(
    questions_file_path: str = Form("docs/question_import_templates/Вопросы на игру Пристолов.docx"),
    source_dir: str = Form("app/static/questions_media"),
    dry_run: str = Form("true"),
    force: str = Form("false"),
):
    try:
        dry_run_value = str(dry_run or "").strip().lower() in {"true", "1", "yes"}
        force_value = str(force or "").strip().lower() in {"true", "1", "yes"}
        result = _prepare_media_files(
            source_dir=source_dir,
            questions_file_path=questions_file_path,
            dry_run=dry_run_value,
            force=force_value,
        )
        result["slug_examples"] = {
            "Фен": _slugify_media_ref("Фен"),
            "Фото «Фен»": _slugify_media_ref("Фото «Фен»"),
            "Женщина будит жителей": _slugify_media_ref("Женщина будит жителей"),
            "Крысолов-2": _slugify_media_ref("Крысолов-2"),
            "BackRub": _slugify_media_ref("BackRub"),
        }
        return result
    except Exception as exc:
        return {
            "ok": False,
            "message": str(exc),
            "questions_file_path": questions_file_path,
            "source_dir": source_dir,
        }


@router.get("/court/state/{room_code}")
def get_court_state(room_code: str):
    db: Session = SessionLocal()
    try:
        return _get_court_state_logic(db, room_code=room_code)
    finally:
        db.close()


@router.post("/court/generate-bracket/{room_code}")
def generate_court_bracket(room_code: str):
    db: Session = SessionLocal()
    try:
        return _generate_court_bracket_logic(db, room_code=room_code)
    finally:
        db.close()


@router.post("/court/start-pair/{room_code}")
def start_court_pair(room_code: str, payload: dict = Body(default={})):
    db: Session = SessionLocal()
    try:
        raw_pair_no = (payload or {}).get("pair_no")
        pair_no = int(raw_pair_no) if raw_pair_no is not None else None
        return _start_court_pair_logic(db, room_code=room_code, pair_no=pair_no)
    except (TypeError, ValueError):
        return {
            "ok": False,
            "message": "pair_no должен быть числом",
        }
    finally:
        db.close()


@router.post("/court/open-question/{room_code}")
def open_court_question(room_code: str):
    db: Session = SessionLocal()
    try:
        return _open_court_question_logic(db, room_code=room_code)
    finally:
        db.close()


@router.post("/court/mark-result/{room_code}")
def mark_court_result(room_code: str, payload: dict = Body(default={})):
    db: Session = SessionLocal()
    try:
        return _mark_court_result_logic(
            db,
            room_code=room_code,
            side=(payload or {}).get("side"),
            result=(payload or {}).get("result"),
        )
    finally:
        db.close()


@router.post("/court/extra-question/{room_code}")
def court_extra_question(room_code: str):
    db: Session = SessionLocal()
    try:
        return _court_extra_question_logic(db, room_code=room_code)
    finally:
        db.close()


@router.post("/court/confirm-pair-winner/{room_code}")
def confirm_court_pair_winner(room_code: str, payload: dict = Body(default={})):
    db: Session = SessionLocal()
    try:
        winner_house_id = int((payload or {}).get("winner_house_id"))
    except (TypeError, ValueError):
        return {
            "ok": False,
            "message": "winner_house_id должен быть числом",
        }

    try:
        return _confirm_court_pair_winner_logic(
            db,
            room_code=room_code,
            winner_house_id=winner_house_id,
        )
    finally:
        db.close()


@router.post("/court/next-pair/{room_code}")
def next_court_pair(room_code: str):
    db: Session = SessionLocal()
    try:
        return _next_court_pair_logic(db, room_code=room_code)
    finally:
        db.close()


@router.get("/game-master/{room_code}", response_class=HTMLResponse)
async def game_master_page(request: Request, room_code: str):
    return templates.TemplateResponse(
        request,
        "game_master.html",
        {
            "room_code": room_code,
        },
    )


@router.get("/tv-screen/{room_code}", response_class=HTMLResponse)
async def tv_screen_page(request: Request, room_code: str):
    return templates.TemplateResponse(
        request,
        "tv_screen.html",
        {
            "room_code": room_code,
        },
    )


@router.get("/tv-mode/{room_code}", response_class=HTMLResponse)
async def dev_tv_mode_page(request: Request, room_code: str):
    return templates.TemplateResponse(
        request,
        "tv_mode_tv_state.html",
        {
            "room_code": room_code,
        },
    )


@router.get("/master-screen/{room_code}", response_class=HTMLResponse)
async def master_screen_page(request: Request, room_code: str):
    return templates.TemplateResponse(
        request,
        "master_screen.html",
        {
            "room_code": room_code,
        },
    )


@router.get("/gold-desk/{room_code}", response_class=HTMLResponse)
async def gold_desk_page(request: Request, room_code: str):
    return templates.TemplateResponse(
        request,
        "gold_desk.html",
        {
            "room_code": room_code,
        },
    )
# =========================
# HOST CONTROL v6 DEBUG API
# =========================

@router.get("/host-rounds/{host_round_id}/debug")
def host_round_debug(host_round_id: int):
    db: Session = SessionLocal()

    try:
        return _host_round_debug_logic(
            db=db,
            host_round_id=host_round_id,
        )

    finally:
        db.close()
