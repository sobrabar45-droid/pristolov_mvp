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


ROUND_CODE = "stage_truth_lie_opening"


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


def players_from_seed(seed_payload: dict) -> dict[int, dict]:
    players = {}
    for house in seed_payload.get("houses", []):
        for player in house.get("players", []):
            token = player.get("player_token")
            state = get_json(f"/player/me/{token}")
            player_id = int(state["player"]["id"])
            players[player_id] = {
                "player_id": player_id,
                "player_token": token,
                "role_code": str(player.get("role_code") or ""),
                "house_id": int(state["house"]["id"]),
                "house_name": str(state["house"].get("name") or ""),
            }
    return players


def build_resource_map(state: dict) -> dict[int, dict]:
    result = {}
    for house in state.get("houses", []):
        resources = house.get("resources") or {}
        result[int(house["id"])] = {
            "gold": int(resources.get("gold") or 0),
            "influence": int(resources.get("influence") or 0),
        }
    return result


def open_host_round_phase() -> None:
    result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/host_round")
    expect(result.get("ok") is True, "open-phase/host_round did not return ok=true")


def start_round() -> int:
    result = post_json(f"/dev/host-rounds/start-series/{ROOM_CODE}/{ROUND_CODE}")
    expect(result.get("ok") is True, f"start-series/{ROUND_CODE} did not return ok=true: {result}")
    host_round_id = int((result.get("host_round") or {}).get("id") or 0)
    expect(host_round_id > 0, "start-series did not return host_round.id")
    return host_round_id


def open_question(host_round_id: int) -> dict:
    result = post_json(f"/dev/host-rounds/{host_round_id}/open-next-question")
    expect(result.get("ok") is True, f"open-next-question failed: {result}")
    expect(result.get("created_assignments_count", 0) > 0, "open-next-question created no assignments")
    question = result.get("question_template") or {}
    content = question.get("content") or {}
    correct_answer = content.get("correct_answer")
    expect(correct_answer is not None, "opened question has no content.correct_answer")
    reward = question.get("reward") or {}
    expect(reward.get("influence") == 1, f"opened question reward is not +1 influence: {reward}")
    return result


def get_assignment(host_round_id: int, player_id: int) -> dict:
    state = get_json(f"/dev/host-rounds/{host_round_id}")
    for assignment in state.get("assignments") or []:
        if int(assignment.get("player_id") or 0) == player_id:
            return assignment
    raise SmokeFailure(f"Assignment for player {player_id} not found in host round {host_round_id}")


def get_any_assignment(host_round_id: int, players_by_id: dict[int, dict]) -> tuple[dict, dict]:
    state = get_json(f"/dev/host-rounds/{host_round_id}")
    assignments = state.get("assignments") or []
    expect(assignments, "host round has no assignments")
    for assignment in assignments:
        player_id = int(assignment.get("player_id") or 0)
        player = players_by_id.get(player_id)
        if player and player.get("player_token"):
            return assignment, player
    raise SmokeFailure("Could not match any assignment to a seeded player token")


def assert_master_tv_question_visible(runtime_question_id: int) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    master_question = master_state.get("current_question") or {}
    tv_question = tv_state.get("current_question") or {}
    expect(
        int(master_question.get("id") or 0) == runtime_question_id,
        "master_state current_question mismatch",
    )
    expect(
        int(tv_question.get("id") or 0) == runtime_question_id,
        "tv_state current_question mismatch",
    )


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "round_code": ROUND_CODE,
        "checks": [],
    }

    try:
        reset_room()
        summary["checks"].append("runtime reset")

        seed = apply_scenario_and_seed()
        players_by_id = players_from_seed(seed)
        summary["checks"].append("scenario applied and technical run seeded")

        open_host_round_phase()
        host_round_id = start_round()
        opened = open_question(host_round_id)
        runtime_question_id = int((opened.get("runtime_question") or {}).get("id") or 0)
        correct_answer = (opened.get("question_template") or {}).get("content", {}).get("correct_answer")
        summary["host_round_id"] = host_round_id
        summary["runtime_question_id"] = runtime_question_id
        summary["checks"].append("host round started and question opened")

        assignment, player = get_any_assignment(host_round_id, players_by_id)
        assignment_id = int(assignment["assignment_id"])
        house_id = int(assignment["house_id"])
        expect(assignment.get("status") == "issued", "assignment did not start as issued")
        summary["assignment_id"] = assignment_id
        summary["player_id"] = player["player_id"]
        summary["house_id"] = house_id
        summary["checks"].append("assignment issued")

        before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        before_tv = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        before_resources = build_resource_map(before_master)
        before_tv_resources = build_resource_map(before_tv)

        answer_result = post_json(
            f"/player/assignments/{assignment_id}/answer",
            {
                "player_token": player["player_token"],
                "answer_payload": {
                    "answer": correct_answer,
                    "answered_by_player_id": player["player_id"],
                },
            },
        )
        expect(answer_result.get("ok") is True, f"assignment answer was not accepted: {answer_result}")
        result_payload = answer_result.get("result_payload") or {}
        resources_changed = result_payload.get("resources_changed") or {}
        influence_change = resources_changed.get("influence") or {}
        expect(result_payload.get("checked") is True, "answer result was not checked")
        expect(result_payload.get("is_correct") is True, "answer result was not correct")
        expect(influence_change.get("delta") == 1, f"influence delta was not +1 in result_payload: {resources_changed}")
        expect((answer_result.get("assignment") or {}).get("status") == "resolved", "answer did not resolve assignment")
        expect((answer_result.get("assignment") or {}).get("result_applied") is True, "assignment result_applied is not true")
        summary["checks"].append("answer submitted and reward applied")

        after_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        after_tv = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        after_resources = build_resource_map(after_master)
        after_tv_resources = build_resource_map(after_tv)

        master_delta = after_resources[house_id]["influence"] - before_resources[house_id]["influence"]
        tv_delta = after_tv_resources[house_id]["influence"] - before_tv_resources[house_id]["influence"]
        expect(master_delta == 1, f"master_state influence delta was {master_delta}, expected +1")
        expect(tv_delta == 1, f"tv_state influence delta was {tv_delta}, expected +1")
        summary["checks"].append("Master/TV state reflect influence reward")

        host_assignment = get_assignment(host_round_id, player["player_id"])
        expect(host_assignment.get("status") == "resolved", "dev host-round assignment status is not resolved")
        expect(host_assignment.get("is_correct") is True, "dev host-round assignment is_correct is not true")
        expect(host_assignment.get("result_applied") is True, "dev host-round assignment result_applied is not true")

        assert_master_tv_question_visible(runtime_question_id)
        summary["checks"].append("assignment status and question state visible")

        repeat_result = post_json(
            f"/player/assignments/{assignment_id}/answer",
            {
                "player_token": player["player_token"],
                "answer_payload": {
                    "answer": correct_answer,
                    "answered_by_player_id": player["player_id"],
                },
            },
        )
        expect(repeat_result.get("ok") is False, "double answer unexpectedly succeeded")

        after_repeat_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        after_repeat_resources = build_resource_map(after_repeat_master)
        repeat_delta = after_repeat_resources[house_id]["influence"] - after_resources[house_id]["influence"]
        expect(repeat_delta == 0, f"double answer changed influence by {repeat_delta}")
        summary["checks"].append("double answer blocked and reward not repeated")

        summary["result"] = {
            "correct_answer": correct_answer,
            "master_influence_delta": master_delta,
            "tv_influence_delta": tv_delta,
            "repeat_ok": repeat_result.get("ok"),
            "repeat_message": repeat_result.get("message"),
        }

        print("ASSIGNMENT REWARD LOOP SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("ASSIGNMENT REWARD LOOP SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_room()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
