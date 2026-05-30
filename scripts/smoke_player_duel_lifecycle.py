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


STAKE_GOLD = 3
SETUP_GOLD = 6


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
                    "house_name": str(state["house"].get("name") or ""),
                }
            )
    return players


def find_lords(players: list[dict]) -> tuple[dict, dict]:
    lords = [player for player in players if player["role_code"] == "lord_lady"]
    expect(len(lords) >= 2, "Expected at least two Lord/Lady players in technical seed")
    first = lords[0]
    second = next((player for player in lords if player["house_id"] != first["house_id"]), None)
    expect(second is not None, "Expected Lord/Lady players from two different Houses")
    return first, second


def find_non_lord(players: list[dict]) -> dict:
    candidate = next((player for player in players if player["role_code"] != "lord_lady"), None)
    expect(candidate is not None, "Expected at least one non-Lord player in technical seed")
    return candidate


def build_resource_map(master_state: dict) -> dict[int, dict]:
    result = {}
    for house in master_state.get("houses", []):
        house_id = int(house["id"])
        resources = house.get("resources") or {}
        result[house_id] = {
            "gold": int(resources.get("gold") or 0),
            "influence": int(resources.get("influence") or 0),
        }
    return result


def set_house_gold(house_id: int, target_gold: int) -> None:
    master_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    current = build_resource_map(master_state).get(house_id, {}).get("gold", 0)
    delta = target_gold - current
    if delta == 0:
        return
    result = post_json(
        f"/dev/houses/{house_id}/gold-adjust",
        {
            "gold_delta": delta,
            "reason": "Duel lifecycle smoke setup",
        },
    )
    expect(result.get("ok") is True, f"gold-adjust failed for house {house_id}: {result}")


def open_duel_phase() -> None:
    result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/duel")
    expect(result.get("ok") is True, "open-phase/duel did not return ok=true")


def get_master_duel(duel_id: int) -> dict:
    state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    for bucket in ("active_or_pending", "challenged", "accepted", "recent"):
        for duel in (state.get("duels") or {}).get(bucket, []):
            if int(duel.get("id") or 0) == duel_id:
                return duel
    raise SmokeFailure(f"Duel {duel_id} missing from master_state.duels")


def get_tv_duel(duel_id: int) -> dict:
    state = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    for bucket in ("active_or_pending", "challenged", "accepted", "recent"):
        for duel in (state.get("duels") or {}).get(bucket, []):
            if int(duel.get("id") or 0) == duel_id:
                return duel
    raise SmokeFailure(f"Duel {duel_id} missing from tv_state.duels")


def recent_event_texts(state: dict) -> list[str]:
    texts = []
    for item in state.get("recent_events") or []:
        if isinstance(item, dict) and item.get("text"):
            texts.append(str(item.get("text")))
    return texts


def assert_no_negative_gold(resource_map: dict[int, dict]) -> None:
    for house_id, resources in resource_map.items():
        expect(resources["gold"] >= 0, f"House {house_id} has negative gold")


def run_insufficient_gold_case(summary: dict, challenger: dict, target: dict) -> None:
    result = post_json(
        f"/player/duels/challenge/{challenger['player_id']}",
        {
            "target_house_id": target["house_id"],
            "stake_gold": STAKE_GOLD,
        },
    )
    expect(result.get("ok") is False, "Duel challenge with insufficient gold unexpectedly succeeded")
    expect("message" in result, "Insufficient gold result did not include a message")
    summary["insufficient_gold_case"] = {
        "ok": result.get("ok"),
        "message": result.get("message"),
    }


def run_non_lord_guard(summary: dict, non_lord: dict, target: dict) -> None:
    result = post_json(
        f"/player/duels/challenge/{non_lord['player_id']}",
        {
            "target_house_id": target["house_id"],
            "stake_gold": STAKE_GOLD,
        },
    )
    expect(result.get("ok") is False, "Non-Lord player unexpectedly created duel challenge")
    summary["non_lord_guard"] = {
        "player_id": non_lord["player_id"],
        "role_code": non_lord["role_code"],
        "message": result.get("message"),
    }


def run_accept_resolve_path(summary: dict, challenger: dict, target: dict) -> None:
    set_house_gold(challenger["house_id"], SETUP_GOLD)
    set_house_gold(target["house_id"], SETUP_GOLD)

    before_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_resources = build_resource_map(before_state)

    challenge = post_json(
        f"/player/duels/challenge/{challenger['player_id']}",
        {
            "target_house_id": target["house_id"],
            "stake_gold": STAKE_GOLD,
            "note": "Duel lifecycle smoke",
        },
    )
    expect(challenge.get("ok") is True, f"player duel challenge failed: {challenge}")
    duel = challenge.get("duel") or {}
    duel_id = int(duel.get("id") or 0)
    expect(duel_id > 0, "Challenge did not return duel.id")
    expect(duel.get("status") == "challenged", "Challenge did not create challenged duel")

    master_challenged = get_master_duel(duel_id)
    tv_challenged = get_tv_duel(duel_id)
    expect(master_challenged.get("status") == "challenged", "master_state did not expose challenged duel")
    expect(tv_challenged.get("status") == "challenged", "tv_state did not expose challenged duel")

    accept = post_json(f"/player/duels/accept/{target['player_id']}/{duel_id}", {})
    expect(accept.get("ok") is True, f"player duel accept failed: {accept}")
    expect((accept.get("duel") or {}).get("status") == "accepted", "Accept did not return accepted duel")

    master_accepted = get_master_duel(duel_id)
    tv_accepted = get_tv_duel(duel_id)
    expect(master_accepted.get("status") == "accepted", "master_state did not expose accepted duel")
    expect(tv_accepted.get("status") == "accepted", "tv_state did not expose accepted duel")

    resolve = post_json(
        f"/dev/games/{ROOM_CODE}/duels/{duel_id}/resolve",
        {
            "winner_house_id": challenger["house_id"],
            "note": "Duel lifecycle smoke resolve",
        },
    )
    expect(resolve.get("ok") is True, f"host duel resolve failed: {resolve}")
    resolved_duel = resolve.get("duel") or {}
    expect(resolved_duel.get("status") == "resolved", "Resolve did not return resolved duel")
    expect(int(resolved_duel.get("winner_house_id") or 0) == challenger["house_id"], "Winner mismatch")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after_resources = build_resource_map(master_after)
    master_resolved = get_master_duel(duel_id)
    tv_resolved = get_tv_duel(duel_id)

    expect(master_resolved.get("status") == "resolved", "master_state did not expose resolved duel")
    expect(tv_resolved.get("status") == "resolved", "tv_state did not expose resolved duel")
    expect((master_resolved.get("winner_house") or {}).get("id") == challenger["house_id"], "master_state winner mismatch")

    expected_winner_delta = STAKE_GOLD - 1
    expected_loser_delta = -STAKE_GOLD
    winner_gold_delta = after_resources[challenger["house_id"]]["gold"] - before_resources[challenger["house_id"]]["gold"]
    loser_gold_delta = after_resources[target["house_id"]]["gold"] - before_resources[target["house_id"]]["gold"]
    expect(winner_gold_delta == expected_winner_delta, f"Winner gold delta was {winner_gold_delta}, expected {expected_winner_delta}")
    expect(loser_gold_delta == expected_loser_delta, f"Loser gold delta was {loser_gold_delta}, expected {expected_loser_delta}")
    assert_no_negative_gold(after_resources)

    gold_result = resolve.get("gold_result") or {}
    expect(gold_result.get("winner_house_id") == challenger["house_id"], "gold_result winner mismatch")
    expect(gold_result.get("stake_per_house") == STAKE_GOLD, "gold_result stake mismatch")
    expect(gold_result.get("prize_to_winner") == STAKE_GOLD * 2 - 1, "gold_result prize mismatch")

    master_events = recent_event_texts(master_after)
    tv_events = recent_event_texts(tv_after)
    expect(any("Дуэль" in text or "дуэли" in text.lower() for text in master_events), "Master recent_events missing duel text")
    expect(any("Дуэль" in text or "дуэли" in text.lower() for text in tv_events), "TV recent_events missing duel text")

    summary["accept_resolve_path"] = {
        "duel_id": duel_id,
        "challenger_house_id": challenger["house_id"],
        "target_house_id": target["house_id"],
        "winner_house_id": challenger["house_id"],
        "winner_gold_delta": winner_gold_delta,
        "loser_gold_delta": loser_gold_delta,
        "master_status": master_resolved.get("status"),
        "tv_status": tv_resolved.get("status"),
    }


def run_refuse_path(summary: dict, challenger: dict, target: dict) -> None:
    reset_room()
    seed = apply_scenario_and_seed()
    players = players_from_seed(seed)
    challenger, target = find_lords(players)
    open_duel_phase()
    set_house_gold(challenger["house_id"], SETUP_GOLD)
    set_house_gold(target["house_id"], SETUP_GOLD)

    before_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_resources = build_resource_map(before_state)

    challenge = post_json(
        f"/player/duels/challenge/{challenger['player_id']}",
        {
            "target_house_id": target["house_id"],
            "stake_gold": STAKE_GOLD,
        },
    )
    expect(challenge.get("ok") is True, f"refuse-path challenge failed: {challenge}")
    duel_id = int((challenge.get("duel") or {}).get("id") or 0)
    expect(duel_id > 0, "refuse-path challenge did not return duel.id")

    refuse = post_json(f"/player/duels/refuse/{target['player_id']}/{duel_id}", {})
    expect(refuse.get("ok") is True, f"player duel refuse failed: {refuse}")
    expect((refuse.get("duel") or {}).get("status") == "refused", "Refuse did not return refused duel")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after_resources = build_resource_map(master_after)
    master_refused = get_master_duel(duel_id)
    tv_refused = get_tv_duel(duel_id)
    expect(master_refused.get("status") == "refused", "master_state did not expose refused duel")
    expect(tv_refused.get("status") == "refused", "tv_state did not expose refused duel")

    challenger_influence_delta = after_resources[challenger["house_id"]]["influence"] - before_resources[challenger["house_id"]]["influence"]
    target_influence_delta = after_resources[target["house_id"]]["influence"] - before_resources[target["house_id"]]["influence"]
    expect(challenger_influence_delta == 1, f"Refuse challenger influence delta was {challenger_influence_delta}, expected +1")
    expect(target_influence_delta <= 0, f"Refuse target influence delta was {target_influence_delta}, expected <= 0")
    assert_no_negative_gold(after_resources)

    master_events = recent_event_texts(master_after)
    tv_events = recent_event_texts(tv_after)
    expect(any("отказ" in text.lower() or "отказался" in text.lower() for text in master_events), "Master recent_events missing refuse text")
    expect(any("отказ" in text.lower() or "отказался" in text.lower() for text in tv_events), "TV recent_events missing refuse text")

    summary["refuse_path"] = {
        "duel_id": duel_id,
        "challenger_influence_delta": challenger_influence_delta,
        "target_influence_delta": target_influence_delta,
        "master_status": master_refused.get("status"),
        "tv_status": tv_refused.get("status"),
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

        seed = apply_scenario_and_seed()
        players = players_from_seed(seed)
        challenger, target = find_lords(players)
        non_lord = find_non_lord(players)
        summary["checks"].append("scenario applied and technical run seeded")

        open_duel_phase()
        summary["checks"].append("duel phase opened")

        run_insufficient_gold_case(summary, challenger, target)
        summary["checks"].append("insufficient gold challenge blocked")

        run_non_lord_guard(summary, non_lord, target)
        summary["checks"].append("non-Lord challenge blocked")

        run_accept_resolve_path(summary, challenger, target)
        summary["checks"].append("challenge accept resolve path verified")

        run_refuse_path(summary, challenger, target)
        summary["checks"].append("challenge refuse path verified")

        print("PLAYER DUEL LIFECYCLE SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("PLAYER DUEL LIFECYCLE SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_room()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
