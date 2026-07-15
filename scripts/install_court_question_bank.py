#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app.models  # noqa: F401 - register SQLAlchemy relationships
from app.database import SessionLocal
from app.services.court_question_bank_installer import (
    TARGET_SCENARIO_CODE,
    inspect_court_question_bank_installation,
    install_court_question_bank_logic,
)


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def main() -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Install the create-only commercial Court question bank")
    parser.add_argument("--apply", action="store_true", help="Perform the DB installation")
    parser.add_argument(
        "--confirm-scenario-code",
        default="",
        help="Required with --apply; must exactly match the package target scenario",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        plan = inspect_court_question_bank_installation(db)
        print("COURT_BANK_INSTALL_PLAN", json.dumps(plan, ensure_ascii=False, sort_keys=True))
        if not plan["ok"]:
            print("COURT_BANK_INSTALL_STOP target scenario not found")
            return 2
        if plan["already_installed"]:
            print("COURT_BANK_INSTALL_STOP exact scenario Court bank already exists")
            return 3
        if not args.apply:
            print("COURT_BANK_INSTALL_DRY_RUN_ONLY True")
            return 0
        if args.confirm_scenario_code != TARGET_SCENARIO_CODE:
            print("COURT_BANK_INSTALL_STOP exact --confirm-scenario-code is required")
            return 4

        result = install_court_question_bank_logic(db)
        print("COURT_BANK_INSTALL_RESULT", json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if result.get("ok") else 5
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
