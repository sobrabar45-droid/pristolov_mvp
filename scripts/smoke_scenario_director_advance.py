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


EARLY_ROUNDS = (
    ("stage_intro", "stage_truth_lie_opening"),
    ("stage_truth_lie_opening", "stage_four_options"),
    ("stage_four_options", "stage_map_entry"),
)


def reset_room() -> None:
    post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")
    reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    if reset_delegations.status >= 500:
        reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    expect(reset_delegations.status == 200, f"reset-delegations failed with {reset_delegations.status}")


def apply_scenario_and_seed() -> None:
    apply_result = post_json(
        f"/dev/games/{ROOM_CODE}/scenario/apply",
        {"scenario_code": SCENARIO_CODE},
    )
    expect(apply_result.get("ok") is True, "scenario apply did not return ok=true")

    seed_result = post_json(f"/dev/games/{ROOM_CODE}/seed-technical-run")
    expect(seed_result.get("ok") is True, "seed-technical-run did not return ok=true")


def get_director() -> dict:
    director = get_json(f"/dev/games/{ROOM_CODE}/scenario/director")
    expect(director.get("ok") is True, f"scenario director did not return ok=true: {director}")
    return director


def round_code(round_payload: dict | None) -> str | None:
    if not isinstance(round_payload, dict):
        return None
    value = round_payload.get("round_code")
    return str(value) if value else None


def active_host_round_id(director: dict) -> int:
    host_round = director.get("active_host_round") or {}
    host_round_id = int(host_round.get("id") or 0)
    expect(host_round_id > 0, f"director has no active_host_round.id: {director}")
    return host_round_id


def director_snapshot(director: dict) -> dict:
    active_host_round = director.get("active_host_round") or {}
    active_system_stage = director.get("active_system_stage_phase") or {}
    progress = director.get("progress") or {}
    return {
        "current_round": round_code(director.get("current_round")),
        "next_round": round_code(director.get("next_round")),
        "active_host_round_id": active_host_round.get("id"),
        "active_host_round_code": active_host_round.get("round_code"),
        "active_host_round_status": active_host_round.get("status"),
        "active_system_stage_type": active_system_stage.get("phase_type"),
        "active_system_stage_status": active_system_stage.get("status"),
        "completed_count": progress.get("completed_count"),
    }


def assert_state_gets_do_not_mutate(summary: dict, label: str) -> None:
    before = director_snapshot(get_director())
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after = director_snapshot(get_director())

    expect(before == after, f"GET state calls mutated scenario director at {label}: before={before}, after={after}")
    expect("scenario_director" in master_state, "master_state does not expose scenario_director")
    expect("scenario_director" in tv_state, "tv_state does not expose scenario_director")
    summary["get_state_no_mutation_checks"].append(label)


def start_next_round(expected_round_code: str) -> int:
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
    host_round_id = active_host_round_id(after)
    active_host_round = after.get("active_host_round") or {}
    expect(
        active_host_round.get("round_code") == expected_round_code,
        f"active_host_round round_code did not match {expected_round_code}: {after}",
    )
    return host_round_id


def host_round_state(host_round_id: int) -> dict:
    state = get_json(f"/dev/host-rounds/{host_round_id}")
    host_round = state.get("host_round") or state
    expect(int(host_round.get("id") or 0) == host_round_id, f"host round state id mismatch: {state}")
    return host_round


def open_question(host_round_id: int, expected_sequence: int) -> int:
    result = post_json(f"/dev/host-rounds/{host_round_id}/open-next-question")
    expect(result.get("ok") is True, f"open-next-question failed: {result}")
    runtime_question = result.get("runtime_question") or {}
    runtime_question_id = int(runtime_question.get("id") or 0)
    expect(runtime_question_id > 0, f"open-next-question did not return runtime_question.id: {result}")
    expect(
        int(runtime_question.get("sequence_no") or 0) == expected_sequence,
        f"runtime question sequence mismatch: {runtime_question}",
    )
    return runtime_question_id


def assert_question_visible(runtime_question_id: int) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    master_question = master_state.get("current_question") or {}
    tv_question = tv_state.get("current_question") or {}
    expect(
        int(master_question.get("id") or 0) == runtime_question_id,
        f"master_state current_question mismatch for {runtime_question_id}: {master_question}",
    )
    expect(
        int(tv_question.get("id") or 0) == runtime_question_id,
        f"tv_state current_question mismatch for {runtime_question_id}: {tv_question}",
    )


def force_close_question(host_round_id: int) -> dict:
    result = post_json(f"/dev/host-rounds/{host_round_id}/force-close-question")
    expect(result.get("ok") is True, f"force-close-question failed: {result}")
    return result


def finish_host_round(host_round_id: int, expected_round_code: str, summary: dict) -> None:
    initial_state = host_round_state(host_round_id)
    questions_total = int(initial_state.get("questions_total") or 0)
    expect(questions_total > 0, f"host round {host_round_id} has no questions_total")

    for sequence_no in range(1, questions_total + 1):
        runtime_question_id = open_question(host_round_id, sequence_no)
        assert_question_visible(runtime_question_id)
        assert_state_gets_do_not_mutate(summary, f"{expected_round_code}:question_{sequence_no}_open")

        closed = force_close_question(host_round_id)
        if sequence_no == questions_total:
            expect(
                closed.get("completed_waiting_host") is True,
                f"last question did not mark host round completed_waiting_host: {closed}",
            )
        assert_state_gets_do_not_mutate(summary, f"{expected_round_code}:question_{sequence_no}_closed")

    continued = post_json(f"/dev/host-rounds/{host_round_id}/host-continue")
    expect(continued.get("ok") is True, f"host-continue failed for {expected_round_code}: {continued}")
    host_round = continued.get("host_round") or {}
    expect(host_round.get("status") == "finished", f"host round did not finish: {continued}")

    advanced = post_json(f"/dev/games/{ROOM_CODE}/scenario/advance", {})
    expect(advanced.get("ok") is True, f"scenario advance failed after {expected_round_code}: {advanced}")
    completed_round = advanced.get("completed_round") or {}
    expect(
        completed_round.get("round_code") == expected_round_code,
        f"scenario advance completed wrong round: {advanced}",
    )


def assert_director_position(expected_completed: str, expected_next: str) -> None:
    director = get_director()
    last_completed = director.get("last_completed_round") or {}
    expect(
        round_code(last_completed) == expected_completed,
        f"director last_completed_round was {round_code(last_completed)}, expected {expected_completed}",
    )
    expect(
        round_code(director.get("next_round")) == expected_next,
        f"director next_round was {round_code(director.get('next_round'))}, expected {expected_next}",
    )
    expect(
        not director.get("active_host_round"),
        f"director still has active_host_round after completion: {director.get('active_host_round')}",
    )
    expect(
        not director.get("active_system_stage_phase"),
        f"director unexpectedly has active_system_stage_phase: {director.get('active_system_stage_phase')}",
    )


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "completed_rounds": [],
        "get_state_no_mutation_checks": [],
    }

    try:
        reset_room()
        summary["checks"] = ["runtime reset"]

        apply_scenario_and_seed()
        summary["checks"].append("scenario applied and technical run seeded")

        initial_director = get_director()
        expect(
            round_code(initial_director.get("next_round")) == "stage_intro",
            f"initial next_round is not stage_intro: {initial_director}",
        )
        assert_state_gets_do_not_mutate(summary, "initial")

        for expected_round_code, expected_next_round_code in EARLY_ROUNDS:
            host_round_id = start_next_round(expected_round_code)
            summary["checks"].append(f"{expected_round_code} started")

            finish_host_round(host_round_id, expected_round_code, summary)
            assert_director_position(expected_round_code, expected_next_round_code)
            assert_state_gets_do_not_mutate(summary, f"{expected_round_code}:after_advance")
            summary["completed_rounds"].append(expected_round_code)
            summary["checks"].append(f"{expected_round_code} completed and advanced")

        final_director = get_director()
        expect(
            round_code(final_director.get("next_round")) == "stage_map_entry",
            f"smoke should stop before stage_map_entry, got director: {final_director}",
        )
        summary["next_round_after_smoke"] = "stage_map_entry"
        summary["checks"].append("stopped before map/court/final/terminal")

        print("SCENARIO DIRECTOR ADVANCE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        print("SCENARIO DIRECTOR ADVANCE SMOKE: FAIL", file=sys.stderr)
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
