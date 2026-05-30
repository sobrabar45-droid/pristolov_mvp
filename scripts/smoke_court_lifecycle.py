#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

from smoke_last_whisper_quiet_support import (
    ROOM_CODE,
    SCENARIO_CODE,
    SmokeFailure,
    expect,
    get_json,
    get_text,
    post_json,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


PRE_COURT_ROUNDS = (
    "stage_intro",
    "stage_truth_lie_opening",
    "stage_four_options",
    "stage_map_entry",
    "stage_diplomacy_1",
    "stage_free_play",
    "stage_duels",
)


def reset_room() -> None:
    post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")
    reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    if reset_delegations.status >= 500:
        reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    expect(reset_delegations.status == 200, f"reset-delegations failed with {reset_delegations.status}")


def apply_scenario_and_seed() -> dict:
    apply_result = post_json(
        f"/dev/games/{ROOM_CODE}/scenario/apply",
        {"scenario_code": SCENARIO_CODE},
    )
    expect(apply_result.get("ok") is True, "scenario apply did not return ok=true")

    seed_result = post_json(f"/dev/games/{ROOM_CODE}/seed-technical-run")
    expect(seed_result.get("ok") is True, "seed-technical-run did not return ok=true")
    return seed_result


def round_code(round_payload: dict | None) -> str | None:
    if not isinstance(round_payload, dict):
        return None
    value = round_payload.get("round_code")
    return str(value) if value else None


def get_director() -> dict:
    director = get_json(f"/dev/games/{ROOM_CODE}/scenario/director")
    expect(director.get("ok") is True, f"scenario director did not return ok=true: {director}")
    return director


def start_next_round(expected_round_code: str) -> dict:
    before = get_director()
    expect(
        round_code(before.get("next_round")) == expected_round_code,
        f"director next_round was {round_code(before.get('next_round'))}, expected {expected_round_code}",
    )

    result = post_json(f"/dev/games/{ROOM_CODE}/scenario/start-next-round")
    expect(result.get("ok") is True, f"start-next-round failed for {expected_round_code}: {result}")

    after = get_director()
    expect(
        round_code(after.get("current_round")) == expected_round_code,
        f"director current_round did not become {expected_round_code}: {after}",
    )
    return after


def finish_active_host_round(expected_round_code: str) -> None:
    director = get_director()
    host_round = director.get("active_host_round") or {}
    host_round_id = int(host_round.get("id") or 0)
    expect(host_round_id > 0, f"{expected_round_code} has no active host round: {director}")

    state = get_json(f"/dev/host-rounds/{host_round_id}")
    host_round_state = state.get("host_round") or state
    questions_total = int(host_round_state.get("questions_total") or 0)
    expect(questions_total > 0, f"{expected_round_code} host round has no questions")

    for _index in range(questions_total):
        opened = post_json(f"/dev/host-rounds/{host_round_id}/open-next-question")
        expect(opened.get("ok") is True, f"open-next-question failed for {expected_round_code}: {opened}")
        closed = post_json(f"/dev/host-rounds/{host_round_id}/force-close-question")
        expect(closed.get("ok") is True, f"force-close-question failed for {expected_round_code}: {closed}")

    continued = post_json(f"/dev/host-rounds/{host_round_id}/host-continue")
    expect(continued.get("ok") is True, f"host-continue failed for {expected_round_code}: {continued}")
    continued_round = continued.get("host_round") or {}
    expect(continued_round.get("status") == "finished", f"{expected_round_code} did not finish: {continued}")


def advance_current_round(expected_round_code: str) -> dict:
    result = post_json(f"/dev/games/{ROOM_CODE}/scenario/advance", {})
    expect(result.get("ok") is True, f"scenario advance failed for {expected_round_code}: {result}")
    completed_round = result.get("completed_round") or {}
    expect(
        completed_round.get("round_code") == expected_round_code,
        f"scenario advance completed wrong round for {expected_round_code}: {result}",
    )
    return result


def reach_court(summary: dict) -> None:
    for expected_round_code in PRE_COURT_ROUNDS:
        director = start_next_round(expected_round_code)
        summary["pre_court_rounds_started"].append(expected_round_code)

        if director.get("active_host_round"):
            finish_active_host_round(expected_round_code)

        advance_current_round(expected_round_code)
        summary["pre_court_rounds_completed"].append(expected_round_code)

    start_next_round("stage_court")
    director = get_director()
    active_phase = director.get("active_system_stage_phase") or {}
    expect(active_phase.get("phase_type") == "court", f"stage_court did not open court phase: {director}")
    summary["checks"].append("stage_court opened through scenario director")


def court_status(court_payload: dict | None) -> str:
    if not isinstance(court_payload, dict):
        return ""
    return str(court_payload.get("status") or "").strip()


def get_court() -> dict:
    state = get_json(f"/dev/court/state/{ROOM_CODE}")
    expect(state.get("ok") is True, f"court state did not return ok=true: {state}")
    court = state.get("court")
    expect(isinstance(court, dict), f"court state has no court payload: {state}")
    return court


def assert_master_tv_court(expected_status: str | None = None) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    master_court = master_state.get("court_runtime")
    tv_court = tv_state.get("court_runtime")
    expect(isinstance(master_court, dict), f"master_state does not expose court_runtime: {master_state.keys()}")
    expect(isinstance(tv_court, dict), f"tv_state does not expose court_runtime: {tv_state.keys()}")
    if expected_status is not None:
        expect(
            court_status(master_court) == expected_status,
            f"master court status was {court_status(master_court)}, expected {expected_status}",
        )
        expect(
            court_status(tv_court) == expected_status,
            f"tv court status was {court_status(tv_court)}, expected {expected_status}",
        )


def assert_state_gets_do_not_mutate(label: str) -> None:
    before = get_court()
    before_snapshot = {
        "status": before.get("status"),
        "current_pair": before.get("current_pair"),
        "bracket": before.get("bracket"),
    }
    assert_master_tv_court()
    after = get_court()
    after_snapshot = {
        "status": after.get("status"),
        "current_pair": after.get("current_pair"),
        "bracket": after.get("bracket"),
    }
    expect(before_snapshot == after_snapshot, f"GET state calls mutated court at {label}")


def generate_bracket(summary: dict) -> dict:
    result = post_json(f"/dev/court/generate-bracket/{ROOM_CODE}")
    expect(result.get("ok") is True, f"generate court bracket failed: {result}")
    court = result.get("court") or {}
    bracket = court.get("bracket") or []
    expect(bracket, f"court bracket is empty: {result}")
    expect(court_status(court) == "bracket_ready", f"court status after bracket was not bracket_ready: {court}")
    summary["pair_count"] = len(bracket)
    summary["checks"].append("court bracket generated")
    return court


def block_unfinished_scenario_advance(summary: dict) -> None:
    result = post_json(f"/dev/games/{ROOM_CODE}/scenario/advance", {})
    expect(result.get("ok") is False, f"unfinished Court scenario advance unexpectedly succeeded: {result}")
    expect(result.get("needs_confirmation") is True, f"unfinished Court advance did not request confirmation: {result}")
    summary["checks"].append("scenario advance blocked before court_finished")


def finish_current_pair(summary: dict) -> None:
    started = post_json(f"/dev/court/start-pair/{ROOM_CODE}", {})
    expect(started.get("ok") is True, f"start court pair failed: {started}")
    court = started.get("court") or {}
    current_pair = court.get("current_pair") or {}
    pair_no = int(current_pair.get("pair_no") or 0)
    winner_house_id = int(current_pair.get("house_a_id") or 0)
    expect(pair_no > 0, f"started court pair has no pair_no: {started}")
    expect(winner_house_id > 0, f"started court pair has no house_a_id: {started}")

    summary["pairs_completed"].append(pair_no)

    while True:
        court = get_court()
        current_pair = court.get("current_pair") or {}
        if current_pair.get("status") == "pair_result":
            break

        opened = post_json(f"/dev/court/open-question/{ROOM_CODE}")
        expect(opened.get("ok") is True, f"open court question failed for pair {pair_no}: {opened}")
        expect(opened.get("warning") != "court_question_bank_exhausted", f"court question bank exhausted: {opened}")

        marked = post_json(f"/dev/court/mark-result/{ROOM_CODE}", {"side": "a", "result": "correct"})
        expect(marked.get("ok") is True, f"mark court result failed for pair {pair_no}: {marked}")
        marked_pair = (marked.get("court") or {}).get("current_pair") or {}
        expect(
            int(marked_pair.get("questions_used") or 0) <= int(marked_pair.get("max_questions") or 7),
            f"court pair exceeded max questions: {marked_pair}",
        )

    premature_next = post_json(f"/dev/court/next-pair/{ROOM_CODE}")
    expect(premature_next.get("ok") is False, f"next-pair before winner confirmation unexpectedly succeeded: {premature_next}")

    confirmed = post_json(f"/dev/court/confirm-pair-winner/{ROOM_CODE}", {"winner_house_id": winner_house_id})
    expect(confirmed.get("ok") is True, f"confirm court pair winner failed: {confirmed}")
    confirmed_pair = (confirmed.get("court") or {}).get("current_pair") or {}
    expect(
        int(confirmed_pair.get("winner_house_id") or 0) == winner_house_id,
        f"confirmed winner mismatch: {confirmed}",
    )


def finish_court(summary: dict) -> None:
    while True:
        finish_current_pair(summary)
        next_pair = post_json(f"/dev/court/next-pair/{ROOM_CODE}")
        expect(next_pair.get("ok") is True, f"next court pair failed: {next_pair}")
        court = next_pair.get("court") or {}
        status = court_status(court)
        if status == "court_finished":
            summary["checks"].append("court_finished reached")
            return
        expect(status == "bracket_ready", f"unexpected court status after next-pair: {court}")


def assert_not_final_or_terminal(summary: dict) -> None:
    director = get_director()
    expect(
        round_code(director.get("current_round")) == "stage_court",
        f"smoke advanced beyond stage_court unexpectedly: {director}",
    )
    expect(
        round_code(director.get("next_round")) == "stage_last_whisper",
        f"unexpected next round after court smoke: {director}",
    )
    summary["checks"].append("stopped before Last Whisper / Final / Terminal")


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
        assert_state_gets_do_not_mutate("after_bracket")

        block_unfinished_scenario_advance(summary)
        finish_court(summary)

        assert_master_tv_court("court_finished")
        assert_state_gets_do_not_mutate("court_finished")
        assert_not_final_or_terminal(summary)

        print("COURT LIFECYCLE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        print("COURT LIFECYCLE SMOKE: FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")
        except Exception as exc:  # pragma: no cover - smoke cleanup best effort
            print(f"cleanup warning: {exc}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
