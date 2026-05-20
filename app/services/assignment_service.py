from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.house import House
from app.models.player import Player
from app.models.game_assignment import GameAssignment
from app.models.game_template_task import GameTemplateTask
from app.models.game_host_round_question import GameHostRoundQuestion
from app.models.round_template import RoundTemplate
from app.models.round_question_template import RoundQuestionTemplate


def normalize_boolean_answer(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return bool(value)

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "1", "yes", "y", "да", "истина"}:
            return True

        if normalized in {"false", "0", "no", "n", "нет", "ложь"}:
            return False

    return value


def compare_ordered_list(user_answer, correct_answer):
    if not isinstance(user_answer, list):
        return False

    if not isinstance(correct_answer, list):
        return False

    return user_answer == correct_answer


SUPPORTED_SINGLE_MODES = {
    "single",
    "single_choice",
    "truth_lie",
}

SUPPORTED_CONFIRM_MODES = {
    "confirm",
}


def _is_legacy_confirm_round_question(round_question_template: RoundQuestionTemplate | None, assignment: GameAssignment) -> bool:
    if not round_question_template:
        return False

    question_code = str(getattr(round_question_template, "question_code", "") or "").strip()
    role_code = str(getattr(round_question_template, "role_code", "") or getattr(assignment, "role_code", "") or "").strip()
    ui_template = str(getattr(round_question_template, "ui_template", "") or "").strip()

    return (
        question_code in {"intro_q1", "court_q1"}
        and role_code == "lord_lady"
        and ui_template == "text"
    )


def _get_effective_answer_mode(assignment: GameAssignment, round_question_template: RoundQuestionTemplate | None = None) -> str:
    explicit_mode = str(getattr(assignment, "answer_mode", "") or "").strip()
    if explicit_mode:
        if explicit_mode in SUPPORTED_CONFIRM_MODES:
            return explicit_mode
        if explicit_mode != "text":
            return explicit_mode

    if _is_legacy_confirm_round_question(round_question_template, assignment):
        return "confirm"

    return explicit_mode


def evaluate_answer_by_mode(answer_mode: str, user_answer, correct_answer):
    if answer_mode in SUPPORTED_SINGLE_MODES:
        return user_answer == correct_answer

    if answer_mode in SUPPORTED_CONFIRM_MODES:
        if isinstance(user_answer, dict):
            return bool(user_answer.get("confirmed")) is True
        return bool(user_answer) is True

    if answer_mode == "boolean":
        normalized_user = normalize_boolean_answer(user_answer)
        normalized_correct = normalize_boolean_answer(correct_answer)
        return normalized_user == normalized_correct

    if answer_mode == "ordered_list":
        return compare_ordered_list(user_answer, correct_answer)

    raise ValueError(f"Неподдерживаемый answer_mode: {answer_mode}")


def process_assignment_answer(
    db: Session,
    assignment: GameAssignment,
    payload: dict,
    *,
    load_json_text_fn,
    dump_json_fn,
    apply_house_effect_fn,
    build_house_resources_snapshot_fn,
    open_next_question_for_host_round_fn,
):
    if assignment.status not in {"issued"}:
        raise ValueError(
            f'Нельзя ответить на assignment со статусом "{assignment.status}". Разрешён только статус "issued".'
        )

    template_task = None
    round_question_template = None
    runtime_question = None

    if assignment.template_task_id:
        template_task = (
            db.query(GameTemplateTask)
            .filter(GameTemplateTask.id == assignment.template_task_id)
            .first()
        )

        if not template_task:
            raise ValueError("Шаблонная задача для assignment не найдена")

        raw_content = load_json_text_fn(template_task.content_json)
        reward_data = load_json_text_fn(template_task.reward_json)
        fail_effect_data = load_json_text_fn(template_task.fail_effect_json)

    elif assignment.host_round_question_id:
        runtime_question = (
            db.query(GameHostRoundQuestion)
            .filter(GameHostRoundQuestion.id == assignment.host_round_question_id)
            .first()
        )

        if not runtime_question:
            raise ValueError("Runtime-вопрос серии для assignment не найден")

        round_question_template = runtime_question.question_template
        if not round_question_template:
            raise ValueError("Шаблон вопроса серии для assignment не найден")

        raw_content = load_json_text_fn(round_question_template.content_json)
        reward_data = load_json_text_fn(round_question_template.reward_json)
        fail_effect_data = load_json_text_fn(round_question_template.fail_effect_json)

        if not runtime_question.answers_open:
            raise ValueError("Ответы на этот вопрос уже закрыты")

    else:
        raise ValueError("У assignment отсутствует и template_task_id, и host_round_question_id")

    resolved_house = getattr(assignment, "house", None)

    if resolved_house is None and getattr(assignment, "house_id", None):
        resolved_house = (
            db.query(House)
            .filter(House.id == assignment.house_id)
            .first()
        )

    if resolved_house is None and getattr(assignment, "player", None) and getattr(assignment.player, "house", None):
        resolved_house = assignment.player.house

    if resolved_house is None and getattr(assignment, "player_id", None):
        assignment_player = (
            db.query(Player)
            .filter(Player.id == assignment.player_id)
            .first()
        )
        if assignment_player and assignment_player.house:
            resolved_house = assignment_player.house

    if not resolved_house:
        raise ValueError("У assignment не найден дом")

    if not isinstance(payload, dict):
        raise ValueError("Тело запроса должно быть JSON-объектом")

    if "answer" not in payload:
        raise ValueError('В теле запроса отсутствует обязательное поле "answer"')

    if not isinstance(raw_content, dict):
        raw_content = {}

    effective_answer_mode = _get_effective_answer_mode(assignment, round_question_template)
    user_answer = payload.get("answer")
    answered_by_player_id = payload.get("answered_by_player_id")

    correct_answer = raw_content.get("correct_answer")
    if effective_answer_mode == "confirm":
        if user_answer is None:
            user_answer = {"confirmed": True}
        elif isinstance(user_answer, bool):
            user_answer = {"confirmed": user_answer}
        elif not isinstance(user_answer, dict):
            user_answer = {"confirmed": bool(user_answer)}
        correct_answer = {"confirmed": True}

    assignment.answer_payload = dump_json_fn(user_answer)
    assignment.answered_at = datetime.now(timezone.utc)

    if answered_by_player_id is not None:
        answered_by_player = (
            db.query(Player)
            .filter(Player.id == answered_by_player_id)
            .first()
        )

        if not answered_by_player:
            raise ValueError("Игрок answered_by_player_id не найден")

        if answered_by_player.game_id != assignment.game_id:
            raise ValueError("Игрок answered_by_player_id принадлежит другой игре")

        if answered_by_player.house_id != assignment.house_id:
            raise ValueError("Игрок answered_by_player_id принадлежит другому дому")

        assignment.answered_by_player_id = answered_by_player_id

    result_payload = {
        "answer_mode": effective_answer_mode,
        "auto_check": assignment.auto_check,
        "checked": False,
        "is_correct": None,
        "correct_answer": correct_answer,
        "applied_effect": None,
        "resources_changed": {},
        "source_type": "template_task" if template_task else "round_question_template",
        "auto_advanced_to_question": None,
        "round_completed_waiting_host": False,
    }

    if assignment.auto_check:
        is_correct = evaluate_answer_by_mode(
            answer_mode=effective_answer_mode,
            user_answer=user_answer,
            correct_answer=correct_answer,
        )

        assignment.is_correct = is_correct

        selected_effect = reward_data if is_correct else fail_effect_data
        effect_result = apply_house_effect_fn(db, resolved_house, selected_effect)

        assignment.result_applied = effect_result.get("applied", False)
        assignment.status = "resolved"

        result_payload["checked"] = True
        result_payload["is_correct"] = is_correct
        result_payload["applied_effect"] = selected_effect
        result_payload["resources_changed"] = effect_result.get("resources_changed", {})
    else:
        assignment.status = "answered"
        assignment.is_correct = None
        assignment.result_applied = False

    assignment.result_payload = dump_json_fn(result_payload)

    db.flush()

    if assignment.host_round_question_id and runtime_question:
        sibling_unresolved = (
            db.query(GameAssignment)
            .filter(
                GameAssignment.host_round_question_id == runtime_question.id,
                GameAssignment.status == "issued",
            )
            .count()
        )

        if sibling_unresolved == 0 and runtime_question.status != "resolved":
            runtime_question.status = "resolved"
            runtime_question.answers_open = False
            runtime_question.resolved_at = datetime.now(timezone.utc)

            host_round = runtime_question.host_round

            if host_round:
                host_round.answers_open = False
                db.flush()

                if runtime_question.sequence_no >= host_round.questions_total:
                    host_round.status = "completed_waiting_host"
                    result_payload["round_completed_waiting_host"] = True
                else:
                    round_template = None

                    if host_round.round_template_id:
                        round_template = (
                            db.query(RoundTemplate)
                            .filter(RoundTemplate.id == host_round.round_template_id)
                            .first()
                        )

                    if round_template and round_template.question_transition_mode == "auto":
                        auto_open_result = open_next_question_for_host_round_fn(db, host_round)

                        if auto_open_result.get("ok"):
                            next_runtime_question = auto_open_result["runtime_question"]
                            result_payload["auto_advanced_to_question"] = {
                                "runtime_question_id": next_runtime_question.id,
                                "sequence_no": next_runtime_question.sequence_no,
                            }
                            host_round.answers_open = True
                        else:
                            result_payload["auto_advanced_to_question"] = {
                                "error": auto_open_result
                            }

            db.flush()
            assignment.result_payload = dump_json_fn(result_payload)

    return {
        "assignment": assignment,
        "template_task": template_task,
        "round_question_template": round_question_template,
        "result_payload": result_payload,
        "house_resources_after": build_house_resources_snapshot_fn(resolved_house),
    }
