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
    get_json,
    get_text,
    http_request,
    post_json,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


LOCATION_CODE = "watchtower"
ROLE_CODES = ["lord_lady", "maester"]
RESOURCE_KEYS = ("gold", "influence", "scroll", "key", "wood", "stone", "iron", "fire")


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


def players_from_seed(seed_payload: dict) -> list[dict]:
    players = []
    for house in seed_payload.get("houses", []):
        for player in house.get("players", []):
            token = player.get("player_token")
            state = get_json(f"/player/me/{token}")
            players.append(
                {
                    "player_id": int(state["player"]["id"]),
                    "player_token": token,
                    "role_code": str(player.get("role_code") or ""),
                    "house_id": int(state["house"]["id"]),
                    "house_name": str(state["house"].get("name") or "").strip(),
                }
            )
    return players


def find_expedition_party(players: list[dict]) -> tuple[dict, dict]:
    for lord in [player for player in players if player["role_code"] == "lord_lady"]:
        maester = next(
            (
                player
                for player in players
                if player["house_id"] == lord["house_id"] and player["role_code"] == "maester"
            ),
            None,
        )
        if maester:
            return lord, maester
    raise SmokeFailure("Expected one house with both lord_lady and maester in technical seed")


def open_map_phase() -> None:
    result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/map")
    expect(result.get("ok") is True, f"open-phase/map failed: {result}")


def build_resource_map(state: dict) -> dict[int, dict[str, int]]:
    result = {}
    for house in state.get("houses", []):
        resources = house.get("resources") or {}
        result[int(house["id"])] = {
            key: int(resources.get(key) or 0)
            for key in RESOURCE_KEYS
        }
    return result


def find_expedition_in_bucket(state: dict, expedition_id: int, bucket_name: str) -> dict:
    expeditions = state.get("expeditions") or {}
    for item in expeditions.get(bucket_name) or []:
        if int(item.get("id") or 0) == expedition_id:
            return item
    raise SmokeFailure(f"Expedition {expedition_id} missing from state.expeditions.{bucket_name}")


def find_expedition_anywhere(state: dict, expedition_id: int) -> dict:
    expeditions = state.get("expeditions") or {}
    for bucket_name in ("planned", "approved", "recently_resolved"):
        for item in expeditions.get(bucket_name) or []:
            if int(item.get("id") or 0) == expedition_id:
                return item
    raise SmokeFailure(f"Expedition {expedition_id} missing from state.expeditions")


def find_map_event(state: dict, expedition_id: int, expected_text: str | None = None) -> dict:
    public_recent = ((state.get("map_events") or {}).get("public_recent") or [])
    for item in public_recent:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text") or item.get("outcome_text") or "").strip()
        if expected_text and text == expected_text:
            return item
        if item.get("location_code") == LOCATION_CODE and text:
            return item
    raise SmokeFailure(f"Map event for expedition {expedition_id} missing from state.map_events.public_recent")


def expected_resource_delta(resolve_result: dict) -> dict[str, int]:
    reward = resolve_result.get("reward") if isinstance(resolve_result.get("reward"), dict) else {}
    penalty = resolve_result.get("penalty") if isinstance(resolve_result.get("penalty"), dict) else {}
    expected = {key: 0 for key in RESOURCE_KEYS}
    for key, value in reward.items():
        if key in expected and isinstance(value, int):
            expected[key] += value
    for key, value in penalty.items():
        if key in expected and isinstance(value, int):
            expected[key] += value
    return {key: value for key, value in expected.items() if value != 0}


def assert_resource_delta(
    before: dict[int, dict[str, int]],
    after: dict[int, dict[str, int]],
    house_id: int,
    expected_delta: dict[str, int],
) -> None:
    for key in RESOURCE_KEYS:
        actual = after[house_id][key] - before[house_id][key]
        expected = expected_delta.get(key, 0)
        expect(actual == expected, f"house {house_id} resource {key} delta was {actual}, expected {expected}")

    for other_house_id, before_resources in before.items():
        if other_house_id == house_id:
            continue
        for key in RESOURCE_KEYS:
            actual = after.get(other_house_id, {}).get(key)
            expect(actual == before_resources.get(key), f"unrelated house {other_house_id} resource {key} changed")


def assert_repeat_resolve_blocked(expedition_id: int, lord_id: int) -> str:
    response = http_request("POST", f"/player/expedition/{expedition_id}/resolve/{lord_id}")
    expect(response.status in {400, 403}, f"repeat resolve returned unexpected HTTP {response.status}: {response.body[:300]}")
    try:
        payload = json.loads(response.body)
    except Exception:
        payload = {}
    detail = str(payload.get("detail") or payload.get("message") or response.body[:200]).strip()
    expect(detail, "repeat resolve did not provide an error detail/message")
    return detail


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "location_code": LOCATION_CODE,
        "role_codes": ROLE_CODES,
        "checks": [],
    }

    try:
        reset_room()
        summary["checks"].append("runtime reset")

        seed = apply_scenario_and_seed()
        players = players_from_seed(seed)
        lord, maester = find_expedition_party(players)
        house_id = int(lord["house_id"])
        summary["house_id"] = house_id
        summary["lord_id"] = lord["player_id"]
        summary["maester_id"] = maester["player_id"]
        summary["checks"].append("scenario applied and technical run seeded")

        open_map_phase()
        summary["checks"].append("map phase opened")

        create_result = post_json(
            f"/player/expedition/create/{lord['player_id']}",
            {
                "members_count": len(ROLE_CODES),
                "role_codes": ROLE_CODES,
            },
        )
        expect(create_result.get("ok") is True, f"expedition create failed: {create_result}")
        expedition_id = int(create_result.get("expedition_id") or 0)
        expect(expedition_id > 0, f"expedition create did not return expedition_id: {create_result}")
        expect(create_result.get("members_count") == len(ROLE_CODES), f"members_count mismatch: {create_result}")
        summary["expedition_id"] = expedition_id
        summary["checks"].append("expedition created")

        master_after_create = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after_create = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        created_master = find_expedition_in_bucket(master_after_create, expedition_id, "planned")
        created_tv = find_expedition_in_bucket(tv_after_create, expedition_id, "planned")
        expect(created_master.get("status") == "planned", f"master planned status mismatch: {created_master}")
        expect(created_tv.get("members_count") == len(ROLE_CODES), "tv planned expedition members_count mismatch")
        summary["checks"].append("planned expedition visible in Master/TV state")

        for player in (lord, maester):
            choose_result = post_json(
                f"/player/expedition/{expedition_id}/choose-location/{player['player_id']}",
                {"location_code": LOCATION_CODE},
            )
            expect(choose_result.get("ok") is True, f"choose-location failed for {player['role_code']}: {choose_result}")
            expect(choose_result.get("location_code") == LOCATION_CODE, f"choose-location returned wrong location: {choose_result}")
        summary["checks"].append("expedition route chosen by all members")

        tv_after_votes = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        voted_expedition = find_expedition_in_bucket(tv_after_votes, expedition_id, "planned")
        expect(voted_expedition.get("choices_count") == len(ROLE_CODES), f"choices_count mismatch: {voted_expedition}")
        expect(voted_expedition.get("unique_locations_count") == 1, f"unique_locations_count mismatch: {voted_expedition}")
        summary["checks"].append("vote state visible in TV state before resolve")

        before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        before_resources = build_resource_map(before_master)

        resolve_result = post_json(f"/player/expedition/{expedition_id}/resolve/{lord['player_id']}")
        expect(resolve_result.get("ok") is True, f"expedition resolve failed: {resolve_result}")
        expect(resolve_result.get("success") is True, f"expedition did not resolve as successful route: {resolve_result}")
        expect(resolve_result.get("chosen_locations") == [LOCATION_CODE], f"chosen_locations mismatch: {resolve_result}")
        outcome_text = str(resolve_result.get("outcome_text") or resolve_result.get("message") or "").strip()
        expect_readable_russian(outcome_text, field_name="expedition outcome_text")
        expected_delta = expected_resource_delta(resolve_result)
        summary["expected_resource_delta"] = expected_delta
        summary["outcome_text"] = outcome_text
        summary["checks"].append("expedition resolved")

        master_after_resolve = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after_resolve = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        after_master_resources = build_resource_map(master_after_resolve)
        after_tv_resources = build_resource_map(tv_after_resolve)
        assert_resource_delta(before_resources, after_master_resources, house_id, expected_delta)
        assert_resource_delta(before_resources, after_tv_resources, house_id, expected_delta)
        summary["checks"].append("resource delta matches resolved reward/penalty in Master/TV state")

        resolved_master = find_expedition_in_bucket(master_after_resolve, expedition_id, "recently_resolved")
        resolved_tv = find_expedition_in_bucket(tv_after_resolve, expedition_id, "recently_resolved")
        expect(resolved_master.get("status") == "resolved", f"master resolved status mismatch: {resolved_master}")
        expect(resolved_tv.get("status") == "resolved", f"tv resolved status mismatch: {resolved_tv}")
        expect(resolved_master.get("target_location_code") == LOCATION_CODE, f"master target location mismatch: {resolved_master}")
        expect(resolved_tv.get("target_location_code") == LOCATION_CODE, f"tv target location mismatch: {resolved_tv}")
        summary["checks"].append("resolved expedition visible in Master/TV state")

        tv_event = find_map_event(tv_after_resolve, expedition_id, expected_text=outcome_text)
        tv_event_text = str(tv_event.get("text") or tv_event.get("outcome_text") or "").strip()
        expect_readable_russian(tv_event_text, field_name="TV map event text")

        master_expedition_events = [
            item for item in (master_after_resolve.get("event_feed") or [])
            if isinstance(item, dict) and item.get("type") == "expedition"
        ]
        expect(master_expedition_events, "Master event_feed does not include expedition event")
        master_event_text = str(master_expedition_events[0].get("text") or "").strip()
        expect_readable_russian(master_event_text, field_name="Master expedition event text")
        summary["checks"].append("TV map event and Master expedition event visible")

        repeat_detail = assert_repeat_resolve_blocked(expedition_id, lord["player_id"])
        after_repeat_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        after_repeat_resources = build_resource_map(after_repeat_master)
        expect(after_repeat_resources == after_master_resources, "repeat resolve changed resources")
        find_expedition_anywhere(after_repeat_master, expedition_id)
        summary["repeat_resolve_detail"] = repeat_detail
        summary["checks"].append("repeat resolve blocked without mutation")

        print("EXPEDITION LIFECYCLE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        print("EXPEDITION LIFECYCLE SMOKE: FAIL", file=sys.stderr)
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
