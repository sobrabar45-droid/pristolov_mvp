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
    post_json,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


RESOURCE_TYPE = "gold"
RESOURCE_AMOUNT = 2
FROM_HOUSE_GOLD = 5
TO_HOUSE_GOLD = 0


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


def find_flow_players(players: list[dict]) -> tuple[dict, dict, dict]:
    treasurers = [player for player in players if player["role_code"] == "treasurer"]
    expect(treasurers, "Expected at least one treasurer in technical seed")
    treasurer = treasurers[0]

    from_diplomat = next(
        (
            player
            for player in players
            if player["role_code"] == "diplomat" and player["house_id"] == treasurer["house_id"]
        ),
        None,
    )
    expect(from_diplomat is not None, "Expected a diplomat in treasurer house")

    to_diplomat = next(
        (
            player
            for player in players
            if player["role_code"] == "diplomat" and player["house_id"] != treasurer["house_id"]
        ),
        None,
    )
    expect(to_diplomat is not None, "Expected a counterparty diplomat in another house")
    return from_diplomat, treasurer, to_diplomat


def build_resource_map(state: dict) -> dict[int, dict]:
    resources_by_house = {}
    for house in state.get("houses", []):
        house_id = int(house["id"])
        resources = house.get("resources") or {}
        resources_by_house[house_id] = {
            "gold": int(resources.get("gold") or 0),
            "influence": int(resources.get("influence") or 0),
            "stone": int(resources.get("stone") or 0),
            "wood": int(resources.get("wood") or 0),
            "iron": int(resources.get("iron") or 0),
            "scroll": int(resources.get("scroll") or 0),
            "key": int(resources.get("key") or 0),
            "fire": int(resources.get("fire") or 0),
        }
    return resources_by_house


def set_house_gold(house_id: int, target_gold: int) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    current_gold = build_resource_map(master_state).get(house_id, {}).get("gold", 0)
    delta = target_gold - current_gold
    if delta == 0:
        return

    result = post_json(
        f"/dev/houses/{house_id}/gold-adjust",
        {
            "gold_delta": delta,
            "reason": "Treasurer resource deal smoke setup",
        },
    )
    expect(result.get("ok") is True, f"gold-adjust failed for house {house_id}: {result}")


def open_diplomacy_phase() -> None:
    result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/diplomacy")
    expect(result.get("ok") is True, f"open-phase/diplomacy failed: {result}")


def iter_state_deals(state: dict):
    deals = state.get("deals")
    if isinstance(deals, list):
        for deal in deals:
            yield deal
        return

    if isinstance(deals, dict):
        for bucket_name in ("pending", "countered", "recent_closed"):
            for deal in deals.get(bucket_name) or []:
                yield deal


def find_deal(state: dict, deal_id: int) -> dict:
    for deal in iter_state_deals(state):
        if not isinstance(deal, dict):
            continue
        if int(deal.get("id") or 0) == deal_id:
            return deal
    raise SmokeFailure(f"Deal {deal_id} missing from state")


def find_recent_event_for_deal(state: dict) -> dict | None:
    for event in state.get("recent_events") or []:
        if not isinstance(event, dict):
            continue
        if event.get("type") == "deal" and event.get("source") == "deals.recent_closed":
            return event
    return None


def assert_deal_visible(state: dict, deal_id: int, expected_status: str, label: str) -> dict:
    deal = find_deal(state, deal_id)
    expect(
        deal.get("status") == expected_status,
        f"{label} deal status was {deal.get('status')}, expected {expected_status}",
    )
    offer = deal.get("offer") or {}
    expect(offer.get("type") == "resource", f"{label} deal offer.type mismatch: {offer}")
    expect(offer.get("resource_type") == RESOURCE_TYPE, f"{label} deal resource_type mismatch: {offer}")
    expect(offer.get("resource_amount") == RESOURCE_AMOUNT, f"{label} deal resource_amount mismatch: {offer}")
    return deal


def assert_resource_transfer(before: dict[int, dict], after: dict[int, dict], from_house_id: int, to_house_id: int) -> None:
    from_delta = after[from_house_id][RESOURCE_TYPE] - before[from_house_id][RESOURCE_TYPE]
    to_delta = after[to_house_id][RESOURCE_TYPE] - before[to_house_id][RESOURCE_TYPE]
    expect(from_delta == -RESOURCE_AMOUNT, f"from house {RESOURCE_TYPE} delta was {from_delta}, expected -{RESOURCE_AMOUNT}")
    expect(to_delta == RESOURCE_AMOUNT, f"to house {RESOURCE_TYPE} delta was {to_delta}, expected +{RESOURCE_AMOUNT}")

    for house_id, before_resources in before.items():
        if house_id in {from_house_id, to_house_id}:
            continue
        after_resources = after.get(house_id, {})
        expect(after_resources.get(RESOURCE_TYPE) == before_resources.get(RESOURCE_TYPE), f"unrelated house {house_id} {RESOURCE_TYPE} changed")


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "resource_type": RESOURCE_TYPE,
        "resource_amount": RESOURCE_AMOUNT,
        "checks": [],
    }

    try:
        reset_room()
        summary["checks"].append("runtime reset")

        seed_result = apply_scenario_and_seed()
        players = players_from_seed(seed_result)
        from_diplomat, treasurer, to_diplomat = find_flow_players(players)
        from_house_id = int(from_diplomat["house_id"])
        to_house_id = int(to_diplomat["house_id"])
        summary["from_house_id"] = from_house_id
        summary["to_house_id"] = to_house_id
        summary["from_diplomat_id"] = from_diplomat["player_id"]
        summary["treasurer_id"] = treasurer["player_id"]
        summary["to_diplomat_id"] = to_diplomat["player_id"]
        summary["checks"].append("technical run seeded and players selected")

        set_house_gold(from_house_id, FROM_HOUSE_GOLD)
        set_house_gold(to_house_id, TO_HOUSE_GOLD)
        setup_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        setup_resources = build_resource_map(setup_master)
        expect(setup_resources[from_house_id][RESOURCE_TYPE] == FROM_HOUSE_GOLD, "from house setup gold mismatch")
        expect(setup_resources[to_house_id][RESOURCE_TYPE] == TO_HOUSE_GOLD, "to house setup gold mismatch")
        summary["checks"].append("resource setup complete")

        open_diplomacy_phase()
        summary["checks"].append("diplomacy phase opened")

        create_result = post_json(
            f"/player/deals/create/{from_diplomat['player_id']}",
            {
                "target_house_id": to_house_id,
                "deal_type": "resource",
                "resource_type": RESOURCE_TYPE,
                "resource_amount": RESOURCE_AMOUNT,
                "offer_text": "Передача золота для smoke проверки",
            },
        )
        expect(create_result.get("ok") is True, f"resource deal create failed: {create_result}")
        deal_id = int((create_result.get("deal") or {}).get("id") or 0)
        expect(deal_id > 0, f"resource deal create did not return deal.id: {create_result}")
        summary["deal_id"] = deal_id
        summary["checks"].append("resource deal created")

        master_after_create = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        assert_deal_visible(master_after_create, deal_id, "pending", "master after create")

        respond_result = post_json(
            f"/player/deals/respond/{to_diplomat['player_id']}",
            {
                "deal_id": deal_id,
                "action": "accept",
            },
        )
        expect(respond_result.get("ok") is True, f"resource deal accept failed: {respond_result}")
        expect(
            (respond_result.get("deal") or {}).get("status") == "accepted_waiting_treasurer",
            f"resource deal accept did not wait for treasurer: {respond_result}",
        )
        summary["checks"].append("counterparty accepted, waiting treasurer")

        master_after_accept = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        assert_deal_visible(master_after_accept, deal_id, "accepted_waiting_treasurer", "master after accept")

        before_confirm_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        before_resources = build_resource_map(before_confirm_master)

        confirm_result = post_json(
            f"/player/deals/treasurer-confirm/{treasurer['player_id']}",
            {
                "deal_id": deal_id,
                "action": "confirm",
            },
        )
        expect(confirm_result.get("ok") is True, f"treasurer confirm failed: {confirm_result}")
        expect((confirm_result.get("deal") or {}).get("status") == "completed", f"deal did not complete: {confirm_result}")
        transferred = confirm_result.get("transferred") or {}
        expect(transferred.get("resource_type") == RESOURCE_TYPE, f"transferred.resource_type mismatch: {transferred}")
        expect(transferred.get("resource_amount") == RESOURCE_AMOUNT, f"transferred.resource_amount mismatch: {transferred}")
        summary["checks"].append("treasurer confirmed")

        master_after_confirm = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after_confirm = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        after_resources = build_resource_map(master_after_confirm)
        tv_after_resources = build_resource_map(tv_after_confirm)

        assert_resource_transfer(before_resources, after_resources, from_house_id, to_house_id)
        assert_resource_transfer(before_resources, tv_after_resources, from_house_id, to_house_id)
        summary["checks"].append("resources transferred exactly once in Master/TV state")

        assert_deal_visible(master_after_confirm, deal_id, "completed", "master after confirm")
        summary["checks"].append("completed deal visible in Master state; TV reflects result via resources")

        master_event = find_recent_event_for_deal(master_after_confirm)
        tv_event = find_recent_event_for_deal(tv_after_confirm)
        if master_event and tv_event:
            master_text = str(master_event.get("text") or "").strip()
            tv_text = str(tv_event.get("text") or "").strip()
            expect_readable_russian(master_text, field_name="Master recent deal event text")
            expect_readable_russian(tv_text, field_name="TV recent deal event text")
            expect(master_text == tv_text, "Master/TV recent deal event text mismatch")
            summary["recent_event_text"] = master_text
            summary["checks"].append("readable recent deal event visible in Master/TV state")
        else:
            summary["checks"].append("no dedicated recent deal event found; deal visibility checked via deals state")

        repeat_result = post_json(
            f"/player/deals/treasurer-confirm/{treasurer['player_id']}",
            {
                "deal_id": deal_id,
                "action": "confirm",
            },
        )
        expect(repeat_result.get("ok") is False, f"repeat treasurer confirm unexpectedly succeeded: {repeat_result}")

        after_repeat_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        after_repeat_resources = build_resource_map(after_repeat_master)
        expect(after_repeat_resources == after_resources, "repeat treasurer confirm changed resources")
        assert_deal_visible(after_repeat_master, deal_id, "completed", "master after repeat")
        summary["checks"].append("repeat confirm blocked without resource mutation")

        print("TREASURER RESOURCE DEAL SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        print("TREASURER RESOURCE DEAL SMOKE: FAIL", file=sys.stderr)
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
