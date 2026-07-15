from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from app.models.game_scenario_template import GameScenarioTemplate
from app.models.round_template import RoundTemplate
from app.services.serialization_utils import dump_json


TARGET_SCENARIO_CODE = "season1_mvp_live_v2_qbank_v2"
COURT_ROUND_CODE = "stage_court_battle"
EXPECTED_QUESTION_COUNT = 36
DEFAULT_PACKAGE_PATH = (
    Path(__file__).resolve().parents[1]
    / "game_templates"
    / "scenarios"
    / "season1_mvp_live_v2_qbank_v2_court_v1.json"
)


class CourtQuestionBankPackageError(ValueError):
    pass


def load_court_question_bank_package(package_path: Path | str = DEFAULT_PACKAGE_PATH) -> dict:
    path = Path(package_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    installer = payload.get("installer") or {}
    round_payload = payload.get("round") or {}
    questions = round_payload.get("questions") or []

    if payload.get("scenario") is not None:
        raise CourtQuestionBankPackageError("Court package must not define a separate scenario")
    if installer.get("target_scenario_code") != TARGET_SCENARIO_CODE:
        raise CourtQuestionBankPackageError("Unexpected target_scenario_code")
    if installer.get("import_mode") != "create":
        raise CourtQuestionBankPackageError("Court package must use create-only installation")
    if round_payload.get("round_code") != COURT_ROUND_CODE:
        raise CourtQuestionBankPackageError("Unexpected Court round_code")
    if round_payload.get("round_kind") != "question_bank":
        raise CourtQuestionBankPackageError("Court round must be an auxiliary question_bank")
    if round_payload.get("questions_total") != EXPECTED_QUESTION_COUNT or len(questions) != EXPECTED_QUESTION_COUNT:
        raise CourtQuestionBankPackageError("Court package must contain exactly 36 questions")

    question_codes = [str(item.get("question_code") or "").strip() for item in questions]
    if not all(question_codes) or len(set(question_codes)) != EXPECTED_QUESTION_COUNT:
        raise CourtQuestionBankPackageError("Court question codes must be non-empty and unique")

    for item in questions:
        content = item.get("content") or {}
        if content.get("media_type") != "none" or content.get("media_ref"):
            raise CourtQuestionBankPackageError("Commercial Court v1 must remain text-only")
        if item.get("reward") or item.get("fail_effect"):
            raise CourtQuestionBankPackageError("Court-bank questions must not apply automatic effects")

    return payload


def inspect_court_question_bank_installation(
    db: Session,
    *,
    package_path: Path | str = DEFAULT_PACKAGE_PATH,
) -> dict:
    package = load_court_question_bank_package(package_path)
    scenario = (
        db.query(GameScenarioTemplate)
        .filter(GameScenarioTemplate.code == TARGET_SCENARIO_CODE)
        .first()
    )
    existing_round = None
    if scenario is not None:
        existing_round = (
            db.query(RoundTemplate)
            .filter(
                RoundTemplate.scenario_id == scenario.id,
                RoundTemplate.round_code == COURT_ROUND_CODE,
            )
            .first()
        )

    return {
        "ok": scenario is not None,
        "target_scenario_code": TARGET_SCENARIO_CODE,
        "target_scenario_id": getattr(scenario, "id", None),
        "round_code": COURT_ROUND_CODE,
        "expected_questions": EXPECTED_QUESTION_COUNT,
        "package_questions": len(package["round"]["questions"]),
        "already_installed": existing_round is not None,
        "existing_round_id": getattr(existing_round, "id", None),
        "existing_questions_total": getattr(existing_round, "questions_total", None),
        "safe_to_create": scenario is not None and existing_round is None,
    }


def install_court_question_bank_logic(
    db: Session,
    *,
    package_path: Path | str = DEFAULT_PACKAGE_PATH,
    import_round_fn: Callable | None = None,
    dump_json_fn=dump_json,
) -> dict:
    package = load_court_question_bank_package(package_path)
    if import_round_fn is None:
        from app.services.scenario_service import import_scenario_round_logic

        import_round_fn = import_scenario_round_logic

    round_payload = copy.deepcopy(package["round"])
    round_payload["import_mode"] = "create"
    return import_round_fn(
        db,
        scenario_code=TARGET_SCENARIO_CODE,
        payload=round_payload,
        dump_json_fn=dump_json_fn,
    )
