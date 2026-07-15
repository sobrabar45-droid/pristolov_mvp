import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.models.game_assignment import GameAssignment
from app.models.game_host_round_question import GameHostRoundQuestion
from app.services.assignment_service import (
    evaluate_answer_by_mode,
    process_assignment_answer,
)


class _FakeQuery:
    def __init__(self, *, first=None, count=0):
        self._first = first
        self._count = count

    def filter(self, *_args):
        return self

    def first(self):
        return self._first

    def count(self):
        return self._count


class _FakeSession:
    def __init__(self, runtime_question):
        self.runtime_question = runtime_question
        self.flush_count = 0

    def query(self, model):
        if model is GameHostRoundQuestion:
            return _FakeQuery(first=self.runtime_question)
        if model is GameAssignment:
            return _FakeQuery(count=1)
        raise AssertionError(f"Unexpected query model: {model}")

    def flush(self):
        self.flush_count += 1


class TrueFalseAssignmentFlowTests(unittest.TestCase):
    def test_true_false_mode_normalizes_commercial_labels(self):
        self.assertTrue(evaluate_answer_by_mode("true_false", "правда", "true"))
        self.assertTrue(evaluate_answer_by_mode("true_false", "ложь", "false"))
        self.assertFalse(evaluate_answer_by_mode("true_false", "ложь", "правда"))

    def test_commercial_host_round_assignment_resolves_true_false_answer(self):
        question_template = SimpleNamespace(
            content_json=json.dumps(
                {"correct_answer": "правда"},
                ensure_ascii=False,
            ),
            reward_json=json.dumps({"influence": 1}),
            fail_effect_json=json.dumps({}),
        )
        runtime_question = SimpleNamespace(
            id=2050,
            question_template=question_template,
            answers_open=True,
            status="active",
            host_round=None,
        )
        house = SimpleNamespace(id=282)
        assignment = SimpleNamespace(
            status="issued",
            template_task_id=None,
            host_round_question_id=runtime_question.id,
            house=house,
            house_id=house.id,
            player=None,
            player_id=None,
            game_id=3,
            role_code="maester",
            answer_mode="true_false",
            auto_check=True,
            is_correct=None,
            result_applied=False,
            answered_by_player_id=None,
            answer_payload=None,
            result_payload=None,
            answered_at=None,
        )
        db = _FakeSession(runtime_question)

        result = process_assignment_answer(
            db=db,
            assignment=assignment,
            payload={"answer": "правда"},
            load_json_text_fn=lambda value: json.loads(value),
            dump_json_fn=lambda value: json.dumps(value, ensure_ascii=False),
            apply_house_effect_fn=lambda _db, resolved_house, effect: {
                "applied": resolved_house is house and effect == {"influence": 1},
                "resources_changed": {"influence": 1},
            },
            build_house_resources_snapshot_fn=lambda resolved_house: {
                "house_id": resolved_house.id,
            },
            open_next_question_for_host_round_fn=lambda *_args: self.fail(
                "The next question must not open while another assignment is issued"
            ),
        )

        self.assertTrue(assignment.is_correct)
        self.assertEqual(assignment.status, "resolved")
        self.assertTrue(assignment.result_applied)
        self.assertEqual(json.loads(assignment.answer_payload), "правда")
        self.assertEqual(result["result_payload"]["answer_mode"], "true_false")
        self.assertEqual(result["result_payload"]["is_correct"], True)
        self.assertEqual(result["house_resources_after"], {"house_id": house.id})
        self.assertGreaterEqual(db.flush_count, 1)

    def test_player_assignment_submit_uses_inline_error_and_restores_buttons(self):
        template_path = (
            Path(__file__).resolve().parents[1]
            / "app"
            / "templates"
            / "player_room.html"
        )
        template = template_path.read_text(encoding="utf-8")
        submit_block = template.split(
            "async function submitAnswer(assignmentId, code) {",
            1,
        )[1].split("async function submitConfirmAnswer", 1)[0]

        self.assertNotIn("alert(", submit_block)
        self.assertIn("button.dataset.originalText = button.textContent", submit_block)
        self.assertIn("button.textContent = button.dataset.originalText", submit_block)
        self.assertIn('tone: "error"', submit_block)
        self.assertIn("renderAssignmentFeedback(window.latestAssignmentFeedback)", submit_block)


if __name__ == "__main__":
    unittest.main()
