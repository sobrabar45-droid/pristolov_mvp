import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.routes import dev as dev_routes


class _FakeSession:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class ScenarioRouteAdapterTests(unittest.TestCase):
    def test_start_next_round_forwards_exact_round_identity(self):
        db = _FakeSession()
        game = SimpleNamespace(id=3, room_code="PRELIVE_ROUTE_TEST")

        def start_next_logic(db_obj, *, room_code, start_series_round_fn):
            self.assertIs(db_obj, db)
            self.assertEqual(room_code, game.room_code)
            return start_series_round_fn(
                db_obj,
                game,
                "stage_intro",
                round_template_id=31,
                scenario_id=7,
            )

        with (
            patch.object(dev_routes, "SessionLocal", return_value=db),
            patch.object(
                dev_routes,
                "_start_next_scenario_round_logic",
                side_effect=start_next_logic,
            ),
            patch.object(
                dev_routes,
                "_start_series_host_round_logic",
                return_value={"ok": True},
            ) as start_series,
        ):
            result = dev_routes.start_next_scenario_round(game.room_code)

        self.assertEqual(result, {"ok": True})
        start_series.assert_called_once_with(
            db,
            game,
            "stage_intro",
            round_template_id=31,
            scenario_id=7,
        )
        self.assertTrue(db.closed)

    def test_advance_and_start_forwards_exact_round_identity(self):
        db = _FakeSession()
        game = SimpleNamespace(id=3, room_code="PRELIVE_ROUTE_TEST")
        payload = {"action": "advance_and_start"}

        def advance_logic(
            db_obj,
            *,
            room_code,
            payload,
            finalize_host_round_fn,
            start_series_round_fn,
        ):
            self.assertIs(db_obj, db)
            self.assertEqual(room_code, game.room_code)
            self.assertEqual(payload, {"action": "advance_and_start", "force": True})
            self.assertIs(finalize_host_round_fn, dev_routes._finalize_host_round_by_host)
            return start_series_round_fn(
                db_obj,
                game,
                "stage_truth_lie_opening",
                round_template_id=32,
                scenario_id=7,
            )

        with (
            patch.object(dev_routes, "SessionLocal", return_value=db),
            patch.object(
                dev_routes,
                "_advance_scenario_logic",
                side_effect=advance_logic,
            ),
            patch.object(
                dev_routes,
                "_start_series_host_round_logic",
                return_value={"ok": True},
            ) as start_series,
        ):
            result = dev_routes.advance_scenario(
                game.room_code,
                force=True,
                payload=payload,
            )

        self.assertEqual(result, {"ok": True})
        start_series.assert_called_once_with(
            db,
            game,
            "stage_truth_lie_opening",
            round_template_id=32,
            scenario_id=7,
        )
        self.assertTrue(db.closed)


if __name__ == "__main__":
    unittest.main()
