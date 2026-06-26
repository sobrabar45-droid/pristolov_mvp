from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.player import Player
from app.models.game_assignment import GameAssignment
from app.models.game_host_round import GameHostRound
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.game_template_task_pool import GameTemplateTaskPool
from app.models.game_template_task import GameTemplateTask
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate
from app.services.phase_service import is_phase_active

def open_next_question_for_host_round(
    db: Session,
    host_round: GameHostRound,
    *,
    house_key_allowed_fn,
):
    if host_round.status != "active":
        return {
            "ok": False,
            "message": f'Нельзя открыть следующий вопрос: host round в статусе "{host_round.status}"',
        }

    if not is_phase_active(db, host_round.game_id, "host_round"):
        return {
            "ok": False,
            "message": "Нельзя открыть вопрос вне фазы host_round",
        }

    round_template = (
        db.query(RoundTemplate)
        .filter(RoundTemplate.id == host_round.round_template_id)
        .first()
    )

    current_active_question = (
        db.query(GameHostRoundQuestion)
        .filter(
            GameHostRoundQuestion.host_round_id == host_round.id,
            GameHostRoundQuestion.status == "active",
        )
        .first()
    )

    if current_active_question:
        return {
            "ok": False,
            "message": "Нельзя открыть следующий вопрос, пока текущий ещё active",
            "active_question_id": current_active_question.id,
            "active_sequence_no": current_active_question.sequence_no,
        }

    next_sequence_no = (host_round.current_question_no or 0) + 1

    if round_template.questions_total and next_sequence_no > round_template.questions_total:
        return {
            "ok": False,
            "message": "Все вопросы в серии уже пройдены",
            "questions_total": round_template.questions_total,
        }

    question_template = (
        db.query(RoundQuestionTemplate)
        .filter(
            RoundQuestionTemplate.round_template_id == round_template.id,
            RoundQuestionTemplate.sequence_no == next_sequence_no,
        )
        .first()
    )

    if not question_template:
        return {
            "ok": False,
            "message": "Следующий вопрос в серии не найден",
            "expected_sequence_no": next_sequence_no,
            "round_code": host_round.round_code,
        }

    runtime_question = GameHostRoundQuestion(
        host_round_id=host_round.id,
        question_template_id=question_template.id,
        sequence_no=next_sequence_no,
        status="active",
        answers_open=False,
        check_mode=round_template.check_mode or "auto",
        started_at=None,
    )
    db.add(runtime_question)
    db.flush()

    eligible_players = (
        db.query(Player)
        .filter(Player.game_id == host_round.game_id)
        .all()
    )

    created_assignment_ids = []

    for player in eligible_players:
        if not player.role:
            continue

        if question_template.role_code and player.role.code != question_template.role_code:
            continue

        if not player.house:
            continue

        if not house_key_allowed_fn(question_template.allowed_house_keys, player.house.house_key):
            continue

        assignment = GameAssignment(
            game_id=player.game_id,
            house_id=player.house_id,
            player_id=player.id,
            host_round_id=host_round.id,
            host_round_question_id=runtime_question.id,
            template_pool_id=None,
            template_task_id=None,
            role_code=player.role.code if player.role else None,
            delivery_mode="host_round_series",
            answer_mode=question_template.answer_mode,
            auto_check=question_template.auto_check,
            status="issued",
            is_correct=None,
            result_applied=False,
            triggered_by_host=True,
            answered_by_player_id=None,
            answer_payload=None,
            result_payload=None,
        )
        db.add(assignment)
        db.flush()

        created_assignment_ids.append(assignment.id)

    host_round.answers_open = False
    host_round.current_question_no = next_sequence_no

    return {
        "ok": True,
        "runtime_question": runtime_question,
        "question_template": question_template,
        "created_assignment_ids": created_assignment_ids,
    }


def open_answers_for_current_question(db: Session, host_round: GameHostRound):
    if not host_round:
        return {
            "ok": False,
            "message": "Host round не найден",
        }

    if host_round.status != "active":
        return {
            "ok": False,
            "message": f'Нельзя открыть ответы у раунда со статусом "{host_round.status}"',
        }

    if not is_phase_active(db, host_round.game_id, "host_round"):
        return {
            "ok": False,
            "message": "Нельзя открыть ответы вне фазы host_round",
        }

    current_question = (
        db.query(GameHostRoundQuestion)
        .filter(
            GameHostRoundQuestion.host_round_id == host_round.id,
            GameHostRoundQuestion.status == "active",
        )
        .first()
    )

    if not current_question:
        return {
            "ok": False,
            "message": "У этого host round нет активного вопроса",
        }

    current_question.answers_open = True
    current_question.started_at = datetime.now(timezone.utc)
    host_round.answers_open = True

    db.flush()

    return {
        "ok": True,
        "message": "Ответы на текущий вопрос открыты",
        "host_round": host_round,
        "runtime_question": current_question,
    }


def finalize_host_round_by_host(db: Session, host_round: GameHostRound):
    if not host_round:
        return {
            "ok": False,
            "message": "Host round не найден",
        }

    if host_round.status != "completed_waiting_host":
        return {
            "ok": False,
            "message": (
                f'Нельзя вручную завершить раунд со статусом "{host_round.status}". '
                'Ожидается статус "completed_waiting_host".'
            ),
        }

    if not is_phase_active(db, host_round.game_id, "host_round"):
        return {
            "ok": False,
            "message": "Нельзя завершить раунд вне фазы host_round",
        }

    host_round.status = "finished"
    host_round.answers_open = False

    db.flush()

    return {
        "ok": True,
        "host_round": host_round,
    }

def force_close_current_question_by_host(db: Session, host_round: GameHostRound):
    if not host_round:
        return {
            "ok": False,
            "message": "Host round не найден",
        }

    if host_round.status != "active":
        return {
            "ok": False,
            "message": f'Нельзя принудительно закрыть вопрос у раунда со статусом "{host_round.status}"',
        }

    if not is_phase_active(db, host_round.game_id, "host_round"):
        return {
            "ok": False,
            "message": "Нельзя закрыть вопрос вне фазы host_round",
        }

    current_question = (
        db.query(GameHostRoundQuestion)
        .filter(
            GameHostRoundQuestion.host_round_id == host_round.id,
            GameHostRoundQuestion.status == "active",
        )
        .first()
    )

    if not current_question:
        return {
            "ok": False,
            "message": "У этого host round нет активного вопроса",
        }

    current_question.status = "resolved"
    current_question.answers_open = False
    current_question.resolved_at = datetime.now(timezone.utc)

    related_assignments = (
        db.query(GameAssignment)
        .filter(GameAssignment.host_round_question_id == current_question.id)
        .all()
    )

    expired_assignment_ids = []

    for assignment in related_assignments:
        if assignment.status == "issued":
            assignment.status = "expired"
            expired_assignment_ids.append(assignment.id)

    host_round.answers_open = False

    is_last_question = (
        host_round.questions_total is not None
        and current_question.sequence_no >= host_round.questions_total
    )

    if is_last_question:
        host_round.status = "completed_waiting_host"

    db.flush()

    return {
        "ok": True,
        "message": "Текущий вопрос принудительно закрыт",
        "host_round": host_round,
        "runtime_question": current_question,
        "expired_assignment_ids": expired_assignment_ids,
        "completed_waiting_host": is_last_question,
    }


def pick_runtime_task_for_player(
    db: Session,
    player,
    *,
    resolve_template_for_game_fn,
    house_key_allowed_fn,
):
    if not player.role:
        return {
            "ok": False,
            "message": "РЈ РёРіСЂРѕРєР° РµС‰С‘ РЅРµ РЅР°Р·РЅР°С‡РµРЅР° СЂРѕР»СЊ",
        }

    house = player.house
    game = player.game

    template_resolution = resolve_template_for_game_fn(db, game)
    if not template_resolution.get("ok"):
        return template_resolution

    template = template_resolution["template"]
    role_code = player.role.code

    pools = (
        db.query(GameTemplateTaskPool)
        .filter(
            GameTemplateTaskPool.template_id == template.id,
            GameTemplateTaskPool.role_code == role_code,
        )
        .order_by(GameTemplateTaskPool.id.asc())
        .all()
    )

    if not pools:
        return {
            "ok": False,
            "message": f'Р”Р»СЏ СЂРѕР»Рё "{role_code}" РЅРµ РЅР°Р№РґРµРЅРѕ РЅРё РѕРґРЅРѕРіРѕ РїСѓР»Р°',
        }

    pool_ids = [pool.id for pool in pools]

    candidate_tasks = (
        db.query(GameTemplateTask)
        .filter(GameTemplateTask.template_id == template.id)
        .filter(GameTemplateTask.pool_id.in_(pool_ids))
        .order_by(GameTemplateTask.id.asc())
        .all()
    )

    filtered_tasks = []
    for task in candidate_tasks:
        if house_key_allowed_fn(task.allowed_house_keys, house.house_key):
            filtered_tasks.append(task)

    if not filtered_tasks:
        return {
            "ok": False,
            "message": f'Р”Р»СЏ СЂРѕР»Рё "{role_code}" РЅРµС‚ РїРѕРґС…РѕРґСЏС‰РёС… Р·Р°РґР°С‡ РїРѕРґ РґРѕРј "{house.house_key}"',
        }

    issued_task_ids = {
        row.template_task_id
        for row in db.query(GameAssignment)
        .filter(
            GameAssignment.game_id == game.id,
            GameAssignment.house_id == house.id,
            GameAssignment.player_id == player.id,
        )
        .all()
        if row.template_task_id is not None
    }

    selected_task = None

    for task in filtered_tasks:
        if task.id not in issued_task_ids:
            selected_task = task
            break

    if not selected_task:
        selected_task = filtered_tasks[0]

    selected_pool = (
        db.query(GameTemplateTaskPool)
        .filter(GameTemplateTaskPool.id == selected_task.pool_id)
        .first()
    )

    return {
        "ok": True,
        "template": template,
        "template_fallback_used": template_resolution.get("fallback_used", False),
        "pool": selected_pool,
        "task": selected_task,
    }
