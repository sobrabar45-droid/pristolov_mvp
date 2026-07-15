import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.services import duel_service


ROOT = Path(__file__).resolve().parents[1]
MASTER_TEMPLATE = ROOT / "app" / "templates" / "master_screen.html"
TV_TEMPLATE = ROOT / "app" / "templates" / "tv_mode_tv_state.html"
COURT_SERVICE = ROOT / "app" / "services" / "court_service.py"
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
        cls.court_service = COURT_SERVICE.read_text(encoding="utf-8")
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

    def test_duel_errors_use_inline_master_status_without_native_alert(self):
        block = _function_block(
            self.master,
            "function showDuelMessage(data) {",
            "async function createHouseDuel",
        )
        self.assertNotIn("alert(", block)
        self.assertIn('document.getElementById("psActionStatus")', block)
        self.assertIn("logLine", block)

    def test_primary_court_action_starts_first_pair(self):
        resolver = _function_block(
            self.master,
            "function resolveCourtPrimaryAction(state) {",
            "function resolveScenarioAction",
        )
        scene_step = _function_block(
            self.master,
            "function resolveSceneStep(state) {",
            "function resolveNextMasterAction",
        )
        handler_block = _function_block(
            self.master,
            "const ACTION_HANDLERS = {",
            "async function runSceneStep",
        )
        start_pair = _function_block(
            self.master,
            "async function startNextCourtPair() {",
            "async function openCourtQuestion",
        )

        self.assertIn("court?.can_start_next_pair", resolver)
        self.assertIn('action: "court_start_next_pair"', resolver)
        self.assertIn('"Начать первую пару"', resolver)
        self.assertIn('scenarioAction?.action === "court_start_next_pair"', scene_step)
        self.assertIn("court_start_next_pair: async", handler_block)
        self.assertIn("await startNextCourtPair()", handler_block)
        self.assertIn("/dev/court/start-pair/${ROOM_CODE}", start_pair)
        self.assertNotIn("alert(", start_pair)
        self.assertIn('document.getElementById("psActionStatus")', start_pair)

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

    def test_court_question_is_opened_for_adjudication_before_runtime_sync(self):
        block = self.court_service.split("def open_court_question_logic", 1)[1]
        activate = "activation_result = _open_answers_for_current_question(db, host_round)"
        synchronize = "sync_result = sync_court_question_runtime_logic"

        self.assertIn(activate, block)
        self.assertIn('if not activation_result.get("ok"):', block)
        self.assertLess(block.index(activate), block.index(synchronize))

    def test_master_hides_court_result_buttons_until_question_is_open(self):
        self.assertIn("const canMarkCourtResult = Boolean(", self.master)
        self.assertIn('currentCourtQuestion?.status === "active"', self.master)
        self.assertIn("currentCourtQuestion?.answers_open === true", self.master)

        guarded_controls = self.master.split("if (canMarkCourtResult) {", 1)[1].split(
            "if (showExtraQuestion)", 1
        )[0]
        self.assertIn("markCourtResult('a','correct')", guarded_controls)
        self.assertIn("markCourtResult('b','wrong')", guarded_controls)

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
        self.assertIn("const hasActiveCourtRuntime = Boolean(", runtime_gate)
        self.assertIn("!courtFinished", runtime_gate)
        self.assertIn("if (hasActiveCourtRuntime) return true;", runtime_gate)
        self.assertIn("return renderCourtSetupActivity(data)", scene)
        self.assertIn("winner_house_id", scene)
        self.assertIn("court-loser", scene)
        self.assertIn("house_a_alive", scene)
        self.assertIn("house_b_alive", scene)

    def test_tv_active_court_runtime_outranks_last_whisper_scene(self):
        fetch_block = _function_block(
            self.tv,
            "async function fetchTvState(){",
            "fetchTvState();",
        )

        court_gate = "const shouldForceCourtScene = hasCourtRuntime(data);"
        special_gate = "const shouldForceSpecialScene = shouldForceCourtScene || Boolean(directorSceneModel?.mode);"
        court_render = "if (shouldForceCourtScene){"
        fallback_render = "renderInsights(houses, pending, counters, closed, directorSceneModel, data);"

        self.assertIn(court_gate, fetch_block)
        self.assertIn(special_gate, fetch_block)
        self.assertIn(court_render, fetch_block)
        self.assertIn(fallback_render, fetch_block)
        self.assertLess(fetch_block.index(court_render), fetch_block.index(fallback_render))

    def test_last_whisper_tv_scene_has_compact_viewport_safe_layout(self):
        final_block = _function_block(
            self.tv,
            "function renderFinalShowActivity(state){",
            "function renderLastWhisperActivity(state){",
        )
        whisper_block = _function_block(
            self.tv,
            "function renderLastWhisperActivity(state){",
            "function renderCourtSetupActivity(state){",
        )

        self.assertIn('class="court-scene last-whisper-scene"', whisper_block)
        self.assertNotIn("last-whisper-scene", final_block)
        self.assertIn('class="last-whisper-countdown-label"', whisper_block)
        self.assertIn('class="last-whisper-countdown-value"', whisper_block)
        self.assertNotIn("Кор...", whisper_block)
        self.assertIn(".last-whisper-scene .court-stage{", self.tv)
        self.assertIn('"whisper-header whisper-window"', self.tv)
        self.assertIn("grid-template-columns:repeat(3, minmax(0, 1fr));", self.tv)
        self.assertIn("white-space:normal;", self.tv)
        self.assertIn("white-space:nowrap;", self.tv)
        self.assertIn("overflow-wrap:anywhere;", self.tv)
        self.assertIn("@media (max-width:1600px), (max-height:900px){", self.tv)

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


class DuelReplayFinalizationTests(unittest.TestCase):
    def test_needs_replay_can_be_finalized_after_duel_phase_closed(self):
        challenger = SimpleNamespace(id=1, resource_gold=10)
        target = SimpleNamespace(id=2, resource_gold=10)
        duel = SimpleNamespace(
            id=77,
            game_id=3,
            status="needs_replay",
            challenger_house_id=challenger.id,
            target_house_id=target.id,
            challenger_house=challenger,
            target_house=target,
            stake_gold=3,
            winner_house_id=None,
            resolved_at=None,
            influence_transfer_amount=0,
            bonus_payload_json=None,
            notes_json="{}",
            updated_at=None,
            duel_advantage_side=None,
            duel_advantage_class=None,
            duel_format=None,
            live_bonus_side=None,
            live_bonus_code=None,
            live_bonus_label=None,
            live_bonus_host_text=None,
            live_bonus_tv_text=None,
            live_bonus_payload_json=None,
        )
        db = SimpleNamespace(flush=lambda: None)
        tower_result = {
            "tower_bonus_applied": False,
            "extra_influence_applied": 0,
            "right_to_error": False,
            "winner_matched_advantage": False,
        }

        with (
            patch.object(duel_service, "_ensure_duel_phase_active", return_value={"ok": False}) as phase_guard,
            patch.object(duel_service, "resolve_pvp_gold", return_value={"ok": True}),
            patch.object(duel_service, "apply_house_effect", return_value={"ok": True}),
            patch.object(duel_service, "apply_duel_advantage_bonus", return_value=tower_result),
            patch.object(duel_service, "serialize_duel", side_effect=lambda item: {"id": item.id, "status": item.status}),
        ):
            result = duel_service.resolve_duel(
                db,
                duel,
                {"winner_house_id": challenger.id, "note": "host tiebreak"},
            )

        self.assertTrue(result["ok"])
        self.assertEqual(duel.status, "resolved")
        self.assertEqual(duel.winner_house_id, challenger.id)
        phase_guard.assert_not_called()

    def test_non_replay_duel_still_requires_active_duel_phase(self):
        duel = SimpleNamespace(game_id=3, status="accepted")
        with patch.object(
            duel_service,
            "_ensure_duel_phase_active",
            return_value={"ok": False, "message": "duel phase inactive"},
        ) as phase_guard:
            result = duel_service.resolve_duel(object(), duel, {"winner_house_id": 1})

        self.assertFalse(result["ok"])
        self.assertEqual(result["message"], "duel phase inactive")
        phase_guard.assert_called_once_with(unittest.mock.ANY, 3)


if __name__ == "__main__":
    unittest.main()
