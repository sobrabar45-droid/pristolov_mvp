import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from app.services.court_service import _select_court_round_template
from app.services.court_question_bank_installer import (
    TARGET_SCENARIO_CODE,
    install_court_question_bank_logic,
    load_court_question_bank_package,
)
from app.services.scenario_service import _is_scenario_director_round


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_PATH = (
    PROJECT_ROOT
    / "app"
    / "game_templates"
    / "scenarios"
    / "season1_mvp_live_v2_qbank_v2_court_v1.json"
)


class CourtQuestionBankV2Tests(unittest.TestCase):
    def test_versioned_bank_has_36_safe_text_questions(self):
        payload = load_court_question_bank_package(SCENARIO_PATH)
        self.assertNotIn("scenario", payload)
        self.assertEqual(payload["installer"]["target_scenario_code"], TARGET_SCENARIO_CODE)
        self.assertEqual(payload["installer"]["import_mode"], "create")

        bank = payload["round"]
        questions = bank["questions"]

        self.assertEqual(bank["round_type"], "question_bank")
        self.assertEqual(bank["round_kind"], "question_bank")
        self.assertTrue(bank["is_optional"])
        self.assertEqual(bank["questions_total"], 36)
        self.assertEqual(len(questions), 36)
        self.assertEqual([item["sequence_no"] for item in questions], list(range(1, 37)))
        self.assertEqual(len({item["question_code"] for item in questions}), 36)
        self.assertEqual(
            {item["content"]["source_slot"] for item in questions},
            {
                2, 6, 9, 11, 13, 14, 15, 16, 18, 19, 20, 22,
                30, 31, 32, 33, 34, 36, 38, 39, 40, 41, 42, 43,
                44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55,
            },
        )

        for question in questions:
            content = question["content"]
            self.assertEqual(question["role_code"], "court_mvp")
            self.assertEqual(question["ui_template"], "text")
            self.assertEqual(question["answer_mode"], "text")
            self.assertFalse(question["auto_check"])
            self.assertTrue(question["manual_check_allowed"])
            self.assertTrue(question["prompt"].strip())
            self.assertTrue(str(content["correct_answer"]).strip())
            self.assertEqual(content["media_type"], "none")
            self.assertEqual(content["media_ref"], "")
            self.assertFalse(content["is_media_question"])
            self.assertEqual(question["reward"], {})
            self.assertEqual(question["fail_effect"], {})

    def test_installer_targets_existing_qbank_v2_scenario(self):
        captured = {}
        target_scenario_id = 17

        def import_round(db, *, scenario_code, payload, dump_json_fn):
            installed_round = SimpleNamespace(
                id=41,
                template_id=2,
                scenario_id=target_scenario_id,
                round_code=payload["round_code"],
            )
            captured.update(
                db=db,
                scenario_code=scenario_code,
                payload=payload,
                dump_json_fn=dump_json_fn,
                installed_round=installed_round,
            )
            return {"ok": True, "round": {"round_code": payload["round_code"], "questions_total": 36}}

        db = object()
        result = install_court_question_bank_logic(
            db,
            package_path=SCENARIO_PATH,
            import_round_fn=import_round,
            dump_json_fn=json.dumps,
        )

        self.assertTrue(result["ok"])
        self.assertIs(captured["db"], db)
        self.assertEqual(captured["scenario_code"], "season1_mvp_live_v2_qbank_v2")
        self.assertEqual(captured["payload"]["import_mode"], "create")
        self.assertEqual(captured["payload"]["round_code"], "stage_court_battle")
        self.assertEqual(len(captured["payload"]["questions"]), 36)

        game = SimpleNamespace(template_id=2, scenario_id=target_scenario_id)
        newer_other_scenario = SimpleNamespace(id=99, template_id=2, scenario_id=16)
        selected = _select_court_round_template(
            [newer_other_scenario, captured["installed_round"]],
            game,
        )
        self.assertIs(selected, captured["installed_round"])

    def test_question_bank_is_not_a_director_stage(self):
        self.assertFalse(_is_scenario_director_round(SimpleNamespace(round_kind="question_bank")))
        self.assertTrue(_is_scenario_director_round(SimpleNamespace(round_kind="host_round_series")))

    def test_court_bank_selection_prefers_exact_game_scenario(self):
        game = SimpleNamespace(template_id=2, scenario_id=17)
        exact = SimpleNamespace(id=41, template_id=2, scenario_id=17)
        newer_wrong_scenario = SimpleNamespace(id=99, template_id=2, scenario_id=16)
        legacy = SimpleNamespace(id=80, template_id=2, scenario_id=None)

        selected = _select_court_round_template([newer_wrong_scenario, legacy, exact], game)

        self.assertIs(selected, exact)

    def test_court_bank_selection_preserves_legacy_fallback(self):
        game = SimpleNamespace(template_id=2, scenario_id=17)
        legacy = SimpleNamespace(id=80, template_id=2, scenario_id=None)
        wrong_template = SimpleNamespace(id=99, template_id=1, scenario_id=None)

        selected = _select_court_round_template([wrong_template, legacy], game)

        self.assertIs(selected, legacy)


if __name__ == "__main__":
    unittest.main()
