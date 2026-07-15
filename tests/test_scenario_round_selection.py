import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.models.game import Game
from app.models.game_host_round import GameHostRound
from app.models.game_template import GameTemplate
from app.models.round_template import RoundTemplate
from app.services.game_context_service import resolve_round_template_for_game
from app.services.scenario_service import (
    _classify_scenario_round_start_conflict,
    start_next_scenario_round_logic,
)


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *_args):
        return self

    def first(self):
        return self._result


class _FakeSession:
    def __init__(self, template, round_template):
        self._template = template
        self._round_template = round_template

    def query(self, model):
        if model is GameTemplate:
            return _FakeQuery(self._template)
        if model is RoundTemplate:
            return _FakeQuery(self._round_template)
        raise AssertionError(f"Unexpected model query: {model}")


class _StartQuery:
    def __init__(self, *, first_result=None, all_result=None):
        self._first_result = first_result
        self._all_result = all_result or []

    def filter(self, *_args):
        return self

    def with_for_update(self):
        return self

    def order_by(self, *_args):
        return self

    def first(self):
        return self._first_result

    def all(self):
        return self._all_result


class _StartSession:
    def __init__(self, game, round_template, host_rounds=None):
        self._game = game
        self._round_template = round_template
        self._host_rounds = host_rounds or []

    def query(self, model):
        if model is Game:
            return _StartQuery(first_result=self._game)
        if model is RoundTemplate:
            return _StartQuery(first_result=self._round_template)
        if model is GameHostRound:
            return _StartQuery(all_result=self._host_rounds)
        raise AssertionError(f"Unexpected model query: {model}")


class ScenarioRoundSelectionTests(unittest.TestCase):
    def setUp(self):
        self.template = GameTemplate(
            id=2,
            template_code="season1_mvp_live_v2",
        )
        self.game = SimpleNamespace(
            template_code="season1_mvp_live_v2",
            scenario_id=7,
        )

    def test_exact_versioned_round_template_is_returned(self):
        versioned_round = RoundTemplate(
            id=31,
            template_id=2,
            scenario_id=7,
            round_code="stage_intro",
        )

        result = resolve_round_template_for_game(
            _FakeSession(self.template, versioned_round),
            self.game,
            "stage_intro",
            round_template_id=31,
            scenario_id=7,
        )

        self.assertTrue(result["ok"])
        self.assertIs(result["round_template"], versioned_round)

    def test_original_scenario_round_is_rejected_for_versioned_selection(self):
        original_round = RoundTemplate(
            id=3,
            template_id=2,
            scenario_id=1,
            round_code="stage_intro",
        )

        result = resolve_round_template_for_game(
            _FakeSession(self.template, original_round),
            self.game,
            "stage_intro",
            round_template_id=31,
            scenario_id=7,
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["expected_round_template_id"], 31)
        self.assertEqual(result["resolved_round_template_id"], 3)

    def test_exact_duplicate_start_is_blocked(self):
        target = SimpleNamespace(id=31, round_code="stage_intro")
        existing = SimpleNamespace(
            id=100,
            round_template_id=31,
            round_code="stage_intro",
        )

        conflict = _classify_scenario_round_start_conflict([existing], target)

        self.assertEqual(conflict["type"], "duplicate_round_template")
        self.assertIs(conflict["host_round"], existing)

    def test_same_code_wrong_template_history_is_blocked(self):
        target = SimpleNamespace(id=31, round_code="stage_intro")
        existing = SimpleNamespace(
            id=100,
            round_template_id=3,
            round_code="stage_intro",
        )

        conflict = _classify_scenario_round_start_conflict([existing], target)

        self.assertEqual(conflict["type"], "round_code_template_mismatch")
        self.assertIs(conflict["host_round"], existing)

    def test_new_round_without_history_has_no_conflict(self):
        target = SimpleNamespace(id=31, round_code="stage_intro")

        self.assertIsNone(_classify_scenario_round_start_conflict([], target))

    def test_director_forwards_exact_round_and_scenario_ids(self):
        game = SimpleNamespace(id=10, room_code="PRELIVE_CLEAN", scenario_id=7)
        scenario = SimpleNamespace(id=7, code="season1_mvp_live_v2_qbank_v2")
        target = SimpleNamespace(
            id=31,
            round_code="stage_intro",
            round_type="intro",
            round_kind="intro",
        )
        director = {
            "active_host_round": None,
            "active_system_stage_phase": None,
            "next_round": {"id": 31, "round_code": "stage_intro"},
            "progress": {"total": 1},
            "rounds_overview": [
                {"round_code": "stage_intro"},
            ],
            "linked_scenario": {"id": 7},
        }
        captured = {}

        def start_series(_db, passed_game, round_code, **kwargs):
            captured.update(
                game=passed_game,
                round_code=round_code,
                **kwargs,
            )
            return {
                "ok": True,
                "round_template": {"id": 31},
                "host_round": {"id": 101},
            }

        with (
            patch(
                "app.services.scenario_service._get_linked_scenario",
                return_value=scenario,
            ),
            patch(
                "app.services.scenario_service._build_director_state",
                return_value=director,
            ),
            patch(
                "app.services.scenario_service._cleanup_stale_court_runtime",
                return_value=False,
            ),
            patch(
                "app.services.scenario_service.has_active_phase",
                return_value=True,
            ),
        ):
            result = start_next_scenario_round_logic(
                _StartSession(game, target),
                room_code=game.room_code,
                start_series_round_fn=start_series,
            )

        self.assertTrue(result["ok"])
        self.assertIs(captured["game"], game)
        self.assertEqual(captured["round_code"], "stage_intro")
        self.assertEqual(captured["round_template_id"], 31)
        self.assertEqual(captured["scenario_id"], 7)


if __name__ == "__main__":
    unittest.main()
