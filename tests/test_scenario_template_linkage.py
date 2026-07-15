import unittest

from app.models.game_scenario_template import GameScenarioTemplate
from app.models.game_template import GameTemplate
from app.services.scenario_service import (
    _ensure_backing_template,
    _resolve_scenario_backing_template,
)


class _FakeQuery:
    def __init__(self, result):
        self._result = result

    def filter(self, *_args):
        return self

    def first(self):
        return self._result


class _FakeSession:
    def __init__(self, result):
        self._result = result
        self.added = []

    def query(self, _model):
        return _FakeQuery(self._result)

    def add(self, value):
        self.added.append(value)


class ScenarioTemplateLinkageTests(unittest.TestCase):
    def test_explicit_backing_template_is_reused_without_metadata_changes(self):
        template = GameTemplate(
            id=2,
            template_code="season1_mvp_live_v2",
            name="Original commercial template",
            version=2,
        )
        session = _FakeSession(template)

        resolved = _ensure_backing_template(
            session,
            {
                "code": "season1_mvp_live_v2_qbank_v2",
                "backing_template_code": "season1_mvp_live_v2",
                "name": "Versioned scenario",
                "version": 3,
            },
        )

        self.assertIs(resolved, template)
        self.assertEqual(template.name, "Original commercial template")
        self.assertEqual(template.version, 2)
        self.assertEqual(session.added, [])

    def test_explicit_missing_backing_template_is_rejected(self):
        session = _FakeSession(None)

        with self.assertRaisesRegex(ValueError, "missing_template"):
            _ensure_backing_template(
                session,
                {
                    "code": "versioned_scenario",
                    "backing_template_code": "missing_template",
                },
            )

        self.assertEqual(session.added, [])

    def test_scenario_application_resolves_backing_template_code(self):
        template = GameTemplate(
            id=2,
            template_code="season1_mvp_live_v2",
        )
        scenario = GameScenarioTemplate(
            id=3,
            template_id=2,
            code="season1_mvp_live_v2_qbank_v2",
        )

        resolved = _resolve_scenario_backing_template(_FakeSession(template), scenario)

        self.assertEqual(resolved.template_code, "season1_mvp_live_v2")

    def test_scenario_application_rejects_missing_backing_template(self):
        scenario = GameScenarioTemplate(
            id=3,
            template_id=999,
            code="versioned_scenario",
        )

        with self.assertRaisesRegex(ValueError, "versioned_scenario"):
            _resolve_scenario_backing_template(_FakeSession(None), scenario)


if __name__ == "__main__":
    unittest.main()
