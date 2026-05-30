#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys

from smoke_last_whisper_crown_tax import (
    ROOM_CODE,
    SCENARIO_CODE,
    SmokeFailure,
    apply_scenario_and_seed,
    expect,
    expect_readable_russian,
    get_json,
    open_last_whisper,
    post_json,
    reset_room,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


NO_ALLIANCE_TEXT = "Нет активных союзов для разрыва."


def find_players_by_role(seed_payload: dict, role_code: str) -> list[dict]:
    players = []
    for house in seed_payload.get("houses", []):
        for player in house.get("players", []):
            if player.get("role_code") != role_code:
                continue
            state = get_json(f"/player/me/{player['player_token']}")
            players.append(
                {
                    "player_id": int(state["player"]["id"]),
                    "player_token": player["player_token"],
                    "house_id": int(state["house"]["id"]),
                    "house_name": str(state["house"]["name"] or "").strip(),
                }
            )
    expect(players, f"Expected at least one player with role {role_code}")
    return players


def build_deal_status_map(master_state: dict) -> dict[int, str]:
    result = {}
    for deal in master_state.get("deals", []):
        deal_id = int(deal.get("id") or 0)
        if deal_id:
            result[deal_id] = str(deal.get("status") or "").strip()
    return result


def get_last_whisper_event(master_state: dict) -> dict:
    event = ((master_state.get("last_whisper") or {}).get("latest_event") or {})
    expect(isinstance(event, dict) and event, "Missing last_whisper.latest_event in master state")
    return event


def validate_shared_event_text(master_state: dict, tv_state: dict) -> str:
    master_event = get_last_whisper_event(master_state)
    tv_event = ((tv_state.get("last_whisper") or {}).get("latest_event") or {})
    master_text = str(master_event.get("tv_text") or "").strip()
    tv_text = str(tv_event.get("tv_text") or "").strip()
    expect_readable_russian(master_text, field_name="Master latest_event.tv_text")
    expect(tv_text == master_text, "TV latest_event.tv_text does not match master-state")
    expect_readable_russian(tv_text, field_name="TV latest_event.tv_text")
    return master_text


def create_and_accept_alliance(seed_payload: dict) -> tuple[dict, dict, dict, int]:
    diplomats = find_players_by_role(seed_payload, "diplomat")
    whispers = find_players_by_role(seed_payload, "whisper_master")
    expect(len(diplomats) >= 2, "Expected at least two diplomats in technical seed")
    expect(len(whispers) >= 2, "Expected at least two whisper masters in technical seed")

    house_a_id = diplomats[0]["house_id"]
    diplomat_a = next(item for item in diplomats if item["house_id"] == house_a_id)
    whisper_a = next(item for item in whispers if item["house_id"] == house_a_id)

    diplomat_b = next(item for item in diplomats if item["house_id"] != house_a_id)
    whisper_b = next(item for item in whispers if item["house_id"] == diplomat_b["house_id"])

    open_diplomacy = post_json(f"/dev/games/{ROOM_CODE}/open-phase/diplomacy")
    expect(open_diplomacy.get("ok") is True, "open-phase/diplomacy did not return ok=true")

    create_result = post_json(
        f"/player/deals/create/{diplomat_a['player_id']}",
        {
            "target_house_id": diplomat_b["house_id"],
            "deal_type": "alliance",
            "offer_text": "Союз перед шёпотом",
        },
    )
    expect(create_result.get("ok") is True, "Alliance create did not return ok=true")
    deal_payload = create_result.get("deal") or {}
    deal_id = int(deal_payload.get("id") or 0)
    expect(deal_id > 0, "Alliance create did not return deal.id")

    respond_result = post_json(
        f"/player/deals/respond/{diplomat_b['player_id']}",
        {
            "deal_id": deal_id,
            "action": "accept",
        },
    )
    expect(respond_result.get("ok") is True, "Alliance accept did not return ok=true")

    master_after_accept = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    status_map = build_deal_status_map(master_after_accept)
    expect(status_map.get(deal_id) == "alliance_active", "Accepted alliance is not active in master state")

    alliances = master_after_accept.get("alliances") or []
    expect(
        any(int(item.get("id") or 0) == deal_id for item in alliances),
        "Master state alliances does not include the accepted alliance",
    )

    return whisper_a, whisper_b, diplomat_b, deal_id


def run_happy_path(summary: dict) -> None:
    seed_result = apply_scenario_and_seed()
    whisper_a, whisper_b, _diplomat_b, deal_id = create_and_accept_alliance(seed_result)

    open_last_whisper()

    before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_status_map = build_deal_status_map(before_master)
    expect(before_status_map.get(deal_id) == "alliance_active", "Selected alliance was not active before break_alliance")

    action_result = post_json(
        f"/player/last-whisper/action/{whisper_a['player_id']}",
        {
            "action_code": "break_alliance",
            "target_deal_id": deal_id,
        },
    )
    expect(action_result.get("ok") is True, "break_alliance action was not accepted")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after_status_map = build_deal_status_map(master_after)

    expect(after_status_map.get(deal_id) == "alliance_broken", "Selected alliance did not become alliance_broken")
    for other_deal_id, before_status in before_status_map.items():
        if other_deal_id == deal_id:
            continue
        expect(after_status_map.get(other_deal_id) == before_status, f"Unrelated deal {other_deal_id} changed status")

    remaining_alliances = master_after.get("alliances") or []
    expect(
        not any(int(item.get("id") or 0) == deal_id for item in remaining_alliances),
        "Broken alliance still appears in master_state.alliances",
    )

    broken_recent = master_after.get("broken_alliances_recent") or []
    expect(
        any(int(item.get("id") or 0) == deal_id for item in broken_recent),
        "Broken alliance is missing from master_state.broken_alliances_recent",
    )

    tv_broken_recent = tv_after.get("broken_alliances_recent") or []
    expect(
        any(int(item.get("id") or 0) == deal_id for item in tv_broken_recent),
        "Broken alliance is missing from tv_state.broken_alliances_recent",
    )

    latest_text = validate_shared_event_text(master_after, tv_after)
    expect("разрушил союз" in latest_text.lower(), "Break-alliance event text is missing alliance-break wording")

    repeat_result = post_json(
        f"/player/last-whisper/action/{whisper_a['player_id']}",
        {
            "action_code": "break_alliance",
            "target_deal_id": deal_id,
        },
    )
    expect(repeat_result.get("ok") is False, "Repeated break_alliance submission was not blocked")

    summary["happy_path"] = {
        "attacker_player_id": whisper_a["player_id"],
        "other_house_whisper_player_id": whisper_b["player_id"],
        "deal_id": deal_id,
        "latest_event_text": latest_text,
        "repeat_submit_message": repeat_result.get("message"),
    }


def run_no_alliance_case(summary: dict) -> None:
    reset_room()
    seed_result = apply_scenario_and_seed()
    whispers = find_players_by_role(seed_result, "whisper_master")
    attacker = whispers[0]

    open_last_whisper()

    before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_status_map = build_deal_status_map(before_master)
    expect(not (before_master.get("alliances") or []), "No-alliance branch started with an unexpected active alliance")

    action_result = post_json(
        f"/player/last-whisper/action/{attacker['player_id']}",
        {
            "action_code": "break_alliance",
            "target_deal_id": 999999,
        },
    )
    expect(action_result.get("ok") is False, "No-alliance break_alliance did not fail safely")
    expect(str(action_result.get("message") or "").strip() == NO_ALLIANCE_TEXT, "No-alliance message mismatch")

    after_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    after_status_map = build_deal_status_map(after_master)
    expect(after_status_map == before_status_map, "No-alliance branch mutated deal statuses")
    expect(not (((after_master.get("last_whisper") or {}).get("events")) or []), "No-alliance branch unexpectedly wrote a whisper event")

    summary["no_alliance_case"] = {
        "attacker_player_id": attacker["player_id"],
        "message": action_result.get("message"),
    }


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "checks": [],
    }

    try:
        reset_room()
        summary["checks"].append("runtime reset")

        run_happy_path(summary)
        summary["checks"].append("happy path")

        run_no_alliance_case(summary)
        summary["checks"].append("no-alliance case")

        print("LAST WHISPER BREAK ALLIANCE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("LAST WHISPER BREAK ALLIANCE SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_room()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
