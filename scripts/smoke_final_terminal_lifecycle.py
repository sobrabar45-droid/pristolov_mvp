#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

from smoke_court_lifecycle import (
    ROOM_CODE,
    SCENARIO_CODE,
    SmokeFailure,
    advance_current_round,
    apply_scenario_and_seed,
    assert_master_tv_court,
    block_unfinished_scenario_advance,
    finish_court,
    generate_bracket,
    get_director,
    reach_court,
    reset_room,
    round_code,
)
from smoke_last_whisper_quiet_support import expect, get_json, post_json


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def active_phase_types(state: dict) -> list[str]:
    result = []
    for phase in state.get("active_phases") or []:
        if isinstance(phase, dict):
            phase_type = str(phase.get("phase_type") or "").strip()
            if phase_type:
                result.append(phase_type)
    return result


def assert_no_stale_court(label: str) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    expect(master_state.get("court_runtime") is None, f"master_state has stale court_runtime at {label}")
    expect(tv_state.get("court_runtime") is None, f"tv_state has stale court_runtime at {label}")


def assert_last_whisper_active(summary: dict) -> None:
    director = get_director()
    active_phase = director.get("active_system_stage_phase") or {}
    expect(round_code(director.get("current_round")) == "stage_last_whisper", f"director is not in stage_last_whisper: {director}")
    expect(active_phase.get("phase_type") == "last_whisper", f"active system phase is not last_whisper: {director}")
    expect(director.get("active_host_round") is None, f"last_whisper unexpectedly has host round: {director}")

    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    expect("last_whisper" in active_phase_types(master_state), f"master active_phases do not include last_whisper: {master_state.get('active_phases')}")
    expect("last_whisper" in active_phase_types(tv_state), f"tv active_phases do not include last_whisper: {tv_state.get('active_phases')}")
    expect(isinstance(master_state.get("last_whisper"), dict), "master_state missing last_whisper payload")
    expect(isinstance(tv_state.get("last_whisper"), dict), "tv_state missing last_whisper payload")
    summary["checks"].append("stage_last_whisper active and visible in master/tv state")


def start_last_whisper(summary: dict) -> None:
    director = get_director()
    expect(round_code(director.get("next_round")) == "stage_last_whisper", f"next round is not stage_last_whisper: {director}")

    result = post_json(f"/dev/games/{ROOM_CODE}/scenario/start-next-round")
    expect(result.get("ok") is True, f"start-next-round failed for stage_last_whisper: {result}")
    assert_last_whisper_active(summary)


def finish_last_whisper_and_start_final(summary: dict) -> int:
    result = post_json(f"/dev/games/{ROOM_CODE}/scenario/advance", {"auto_start_next": True})
    expect(result.get("ok") is True, f"advance from Last Whisper to Final failed: {result}")
    expect(result.get("auto_started") is True, f"Final did not auto-start after Last Whisper: {result}")
    started_round = result.get("started_round") or {}
    expect(started_round.get("round_code") == "stage_final_show", f"auto-started wrong round: {result}")

    director = get_director()
    host_round = director.get("active_host_round") or {}
    host_round_id = int(host_round.get("id") or 0)
    expect(round_code(director.get("current_round")) == "stage_final_show", f"director is not in stage_final_show: {director}")
    expect(host_round_id > 0, f"stage_final_show has no active host round: {director}")
    expect(host_round.get("round_code") == "stage_final_show", f"active host round is not stage_final_show: {director}")

    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    for label, state in (("master", master_state), ("tv", tv_state)):
        outcome = state.get("final_outcome")
        expect(isinstance(outcome, dict), f"{label} state missing final_outcome")
        expect(str(outcome.get("winner_house_name") or "").strip(), f"{label} final_outcome has no winner_house_name: {outcome}")
        expect(state.get("court_runtime") is None, f"{label} has stale court_runtime after entering Final")

    summary["final_host_round_id"] = host_round_id
    summary["checks"].append("stage_final_show active with final_outcome in master/tv state")
    return host_round_id


def finish_final_host_round(host_round_id: int, summary: dict) -> None:
    opened = post_json(f"/dev/host-rounds/{host_round_id}/open-next-question")
    expect(opened.get("ok") is True, f"open final question failed: {opened}")

    master_with_question = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_with_question = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    expect(master_with_question.get("current_question") is not None, "master_state missing final current_question after open")
    expect(tv_with_question.get("current_question") is not None, "tv_state missing final current_question after open")

    closed = post_json(f"/dev/host-rounds/{host_round_id}/force-close-question")
    expect(closed.get("ok") is True, f"force-close final question failed: {closed}")

    continued = post_json(f"/dev/host-rounds/{host_round_id}/host-continue")
    expect(continued.get("ok") is True, f"host-continue final round failed: {continued}")
    continued_round = continued.get("host_round") or {}
    expect(continued_round.get("status") == "finished", f"final host round did not finish: {continued}")

    director = get_director()
    expect(director.get("active_host_round") is None, f"final host round still active after host-continue: {director}")
    # Current runtime reaches terminal immediately after final host-continue.
    # Older audit notes expected one more scenario/advance, so the smoke follows the live code.
    expect(director.get("scenario_finished") is True, f"final host-continue did not finish scenario: {director}")
    expect(director.get("can_advance") is False, f"terminal director can_advance should be false: {director}")
    summary["checks"].append("final host round opened, closed, and completed")


def terminal_snapshot() -> dict:
    director = get_director()
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    return {
        "director": {
            "scenario_finished": director.get("scenario_finished"),
            "current_round": director.get("current_round"),
            "next_round": director.get("next_round"),
            "last_completed_round_code": round_code(director.get("last_completed_round")),
            "active_host_round": director.get("active_host_round"),
            "active_system_stage_phase": director.get("active_system_stage_phase"),
            "can_start_next": director.get("can_start_next"),
            "can_advance": director.get("can_advance"),
        },
        "master": {
            "active_phases": master_state.get("active_phases"),
            "active_host_round": master_state.get("active_host_round"),
            "current_question": master_state.get("current_question"),
            "court_runtime": master_state.get("court_runtime"),
            "final_outcome": master_state.get("final_outcome"),
        },
        "tv": {
            "active_phases": tv_state.get("active_phases"),
            "active_host_round": tv_state.get("active_host_round"),
            "current_question": tv_state.get("current_question"),
            "court_runtime": tv_state.get("court_runtime"),
            "final_outcome": tv_state.get("final_outcome"),
        },
    }


def assert_terminal_snapshot(snapshot: dict) -> None:
    director = snapshot["director"]
    expect(director["scenario_finished"] is True, f"terminal scenario_finished is not true: {director}")
    expect(director["current_round"] is None, f"terminal current_round is not null: {director}")
    expect(director["next_round"] is None, f"terminal next_round is not null: {director}")
    expect(director["last_completed_round_code"] == "stage_final_show", f"terminal last_completed_round is wrong: {director}")
    expect(director["active_host_round"] is None, f"terminal director has active_host_round: {director}")
    expect(director["active_system_stage_phase"] is None, f"terminal director has active system phase: {director}")
    expect(director["can_start_next"] is False, f"terminal can_start_next is not false: {director}")
    expect(director["can_advance"] is False, f"terminal can_advance is not false: {director}")

    for label in ("master", "tv"):
        state = snapshot[label]
        expect(state["active_phases"] == [], f"{label} terminal active_phases is not empty: {state['active_phases']}")
        expect(state["active_host_round"] is None, f"{label} terminal active_host_round is not null")
        expect(state["current_question"] is None, f"{label} terminal current_question is not null")
        expect(state["court_runtime"] is None, f"{label} terminal court_runtime is not null")
        outcome = state["final_outcome"]
        expect(isinstance(outcome, dict), f"{label} terminal final_outcome missing")
        expect(str(outcome.get("winner_house_name") or "").strip(), f"{label} terminal final_outcome has no winner")


def reach_terminal(summary: dict) -> None:
    first_snapshot = terminal_snapshot()
    assert_terminal_snapshot(first_snapshot)
    second_snapshot = terminal_snapshot()
    expect(first_snapshot == second_snapshot, "GET state calls mutated terminal state")

    summary["terminal"] = {
        "scenario_finished": first_snapshot["director"]["scenario_finished"],
        "last_completed_round": first_snapshot["director"]["last_completed_round_code"],
        "winner_house_name": first_snapshot["master"]["final_outcome"].get("winner_house_name"),
    }
    summary["checks"].append("terminal state reached and GET state calls are read-only")


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "checks": [],
        "pre_court_rounds_started": [],
        "pre_court_rounds_completed": [],
        "pair_count": 0,
        "pairs_completed": [],
    }

    try:
        reset_room()
        summary["checks"].append("runtime reset")

        seed_result = apply_scenario_and_seed()
        summary["seeded_houses"] = len(seed_result.get("houses") or [])
        summary["checks"].append("scenario applied and technical run seeded")

        reach_court(summary)
        generate_bracket(summary)
        assert_master_tv_court("bracket_ready")
        block_unfinished_scenario_advance(summary)
        finish_court(summary)
        assert_master_tv_court("court_finished")
        summary["checks"].append("court_finished reached and visible")

        advance_current_round("stage_court")
        assert_no_stale_court("after leaving Court")
        summary["checks"].append("advanced from court_finished to stage_last_whisper preview")

        start_last_whisper(summary)
        final_host_round_id = finish_last_whisper_and_start_final(summary)
        finish_final_host_round(final_host_round_id, summary)
        reach_terminal(summary)

        print("FINAL TERMINAL LIFECYCLE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        print("FINAL TERMINAL LIFECYCLE SMOKE: FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
