import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MASTER_TEMPLATE = ROOT / "app" / "templates" / "master_screen.html"
TV_TEMPLATE = ROOT / "app" / "templates" / "tv_mode_tv_state.html"
SCENARIO_PATH = (
    ROOT
    / "app"
    / "game_templates"
    / "scenarios"
    / "season1_mvp_live_v2_qbank_v2.json"
)


def _function_block(template: str, start: str, end: str) -> str:
    return template.split(start, 1)[1].split(end, 1)[0]


class CommercialRescueP0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = MASTER_TEMPLATE.read_text(encoding="utf-8")
        cls.tv = TV_TEMPLATE.read_text(encoding="utf-8")
        cls.scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))

    def test_duel_operator_keeps_needs_replay_actionable(self):
        block = _function_block(
            self.master,
            "function getOperatorDuel(state) {",
            "function showDuelMessage",
        )
        self.assertIn(
            'pending.find(duel => duel?.status === "needs_replay")',
            block,
        )

    def test_master_court_controls_activate_for_scenario_stage(self):
        block = _function_block(
            self.master,
            "function hasCourtRuntime(state) {",
            "function courtPairStatusLabel",
        )
        self.assertIn('currentRoundCode === "stage_court"', block)
        self.assertIn('id="courtControlPanel"', self.master)
        self.assertIn("markCourtResult('a','correct')", self.master)
        self.assertIn("markCourtResult('b','wrong')", self.master)

    def test_tv_court_scene_activates_and_keeps_elimination_dynamics(self):
        runtime_gate = _function_block(
            self.tv,
            "function hasCourtRuntime(data){",
            "function getCourtHouseName",
        )
        scene = _function_block(
            self.tv,
            "function renderCourtMvpScene(data){",
            "function renderInsights",
        )
        self.assertIn('currentRoundCode === "stage_court"', runtime_gate)
        self.assertIn("return renderCourtSetupActivity(data)", scene)
        self.assertIn("winner_house_id", scene)
        self.assertIn("court-loser", scene)
        self.assertIn("house_a_alive", scene)
        self.assertIn("house_b_alive", scene)

    def test_all_commercial_single_choice_answers_match_player_values(self):
        mismatches = []
        checked_codes = []

        for round_item in self.scenario.get("rounds", []):
            for question in round_item.get("questions", []):
                if question.get("answer_mode") != "single_choice":
                    continue

                content = question.get("content") or {}
                player_values = []
                for index, option in enumerate(content.get("options") or []):
                    if isinstance(option, dict):
                        player_values.append(
                            str(option.get("code") or option.get("value") or index)
                        )
                    else:
                        player_values.append(str(option))

                question_code = question.get("question_code")
                checked_codes.append(question_code)
                correct_answer = str(content.get("correct_answer") or "")
                if correct_answer not in player_values:
                    mismatches.append(
                        {
                            "question_code": question_code,
                            "correct_answer": correct_answer,
                            "player_values": player_values,
                        }
                    )

        self.assertEqual(len(checked_codes), 5)
        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main()
