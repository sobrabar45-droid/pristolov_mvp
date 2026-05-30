#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

from smoke_last_whisper_quiet_support import (
    ROOM_CODE,
    SCENARIO_CODE,
    SmokeFailure,
    expect,
    expect_readable_russian,
    find_whisper_master,
    get_json,
    get_text,
    post_json,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def build_influence_map(master_state: dict) -> dict[int, int]:
    result = {}
    for house in master_state.get("houses", []):
        resources = house.get("resources") or {}
        result[int(house["id"])] = int(resources.get("influence") or 0)
    return result


def reset_runtime() -> None:
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


def recent_event_texts(state: dict) -> list[str]:
    events = state.get("recent_events")
    expect(isinstance(events, list), "recent_events is missing or not a list")
    texts = []
    for item in events:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            if text:
                texts.append(text)
    return texts


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "checks": [],
    }

    try:
        reset_runtime()
        summary["checks"].append("runtime reset")

        seed_result = apply_scenario_and_seed()
        whisper_player_id, whisper_house_id = find_whisper_master(seed_result)
        summary["checks"].append("scenario applied and technical run seeded")

        open_phase_result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/last_whisper")
        expect(open_phase_result.get("ok") is True, "open-phase/last_whisper did not return ok=true")
        summary["checks"].append("last whisper opened")

        before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        before_influence = build_influence_map(before_master)
        target_house_id = next((house_id for house_id in before_influence if house_id != whisper_house_id), None)
        expect(target_house_id is not None, "Could not determine target house")

        action_result = post_json(
            f"/player/last-whisper/action/{whisper_player_id}",
            {
                "action_code": "quiet_support",
                "target_house_id": target_house_id,
            },
        )
        expect(action_result.get("ok") is True, "quiet_support action was not accepted")
        summary["checks"].append("quiet support applied")

        master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        master_after_second_get = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after_second_get = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")

        latest_master_event = ((master_after.get("last_whisper") or {}).get("latest_event") or {})
        expected_text = str(latest_master_event.get("tv_text") or "").strip()
        expect_readable_russian(expected_text, field_name="Master last_whisper.latest_event.tv_text")

        master_texts = recent_event_texts(master_after)
        tv_texts = recent_event_texts(tv_after)
        expect(expected_text in master_texts, "Master recent_events does not contain Last Whisper event text")
        expect(expected_text in tv_texts, "TV recent_events does not contain Last Whisper event text")
        expect_readable_russian(expected_text, field_name="recent_events Last Whisper text")
        summary["checks"].append("master and tv recent_events contain Last Whisper text")

        second_master_texts = recent_event_texts(master_after_second_get)
        second_tv_texts = recent_event_texts(tv_after_second_get)
        expect(master_texts == second_master_texts, "Master recent_events changed across GET calls")
        expect(tv_texts == second_tv_texts, "TV recent_events changed across GET calls")

        influence_after = build_influence_map(master_after)
        influence_after_second_get = build_influence_map(master_after_second_get)
        expect(influence_after == influence_after_second_get, "GET state calls changed influence resources")
        summary["checks"].append("GET state calls did not mutate recent_events or influence")

        summary["latest_event_text"] = expected_text
        summary["recent_events_count_master"] = len(master_after.get("recent_events") or [])
        summary["recent_events_count_tv"] = len(tv_after.get("recent_events") or [])

        print("RECENT EVENTS CONTRACT SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("RECENT EVENTS CONTRACT SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_runtime()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
