#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


BASE_URL = "http://127.0.0.1:8000"
ROOM_CODE = "LIVE01"
SCENARIO_CODE = "season1_mvp_live_v2"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


SUCCESS_TEXT_PART = "потерял 1 влияние"
TIE_TEXT = "Корона не нашла единственного носителя. Влияние не изменилось."
ZERO_DELTA_TEXT = "Корона стала тяжелее, но влияние {house_name} уже не может быть уменьшено."


class SmokeFailure(RuntimeError):
    pass


@dataclass
class HttpResult:
    status: int
    body: str


def http_request(method: str, path: str, payload=None) -> HttpResult:
    url = f"{BASE_URL}{path}"
    data = None
    headers = {}

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            return HttpResult(status=response.status, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return HttpResult(status=exc.code, body=body)
    except urllib.error.URLError as exc:
        raise SmokeFailure(f"Cannot reach runtime at {url}: {exc}") from exc


def http_form_post(path: str, payload: dict[str, str | int]) -> HttpResult:
    url = f"{BASE_URL}{path}"
    encoded = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=encoded,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8", errors="replace")
            return HttpResult(status=response.status, body=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return HttpResult(status=exc.code, body=body)
    except urllib.error.URLError as exc:
        raise SmokeFailure(f"Cannot reach runtime at {url}: {exc}") from exc


def get_json(path: str) -> dict:
    response = http_request("GET", path)
    if response.status != 200:
        raise SmokeFailure(f"GET {path} returned {response.status}: {response.body[:300]}")
    return json.loads(response.body)


def post_json(path: str, payload=None) -> dict:
    response = http_request("POST", path, payload=payload)
    if response.status != 200:
        raise SmokeFailure(f"POST {path} returned {response.status}: {response.body[:300]}")
    return json.loads(response.body)


def get_text(path: str) -> HttpResult:
    return http_request("GET", path)


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def expect_readable_russian(text: str, *, field_name: str) -> None:
    normalized = str(text or "").strip()
    expect(bool(normalized), f"{field_name} is empty")
    mojibake_fragments = ("�", "Ð", "Ñ", "Ã", "Р", "С")
    expect(
        not any(fragment in normalized for fragment in mojibake_fragments),
        f"{field_name} contains mojibake: {normalized!r}",
    )
    cyrillic_count = sum(1 for char in normalized if "\u0400" <= char <= "\u04FF")
    expect(cyrillic_count >= 5, f"{field_name} does not look like readable Russian: {normalized!r}")


def reset_room() -> None:
    post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")
    reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    if reset_delegations.status >= 500:
        reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
    expect(reset_delegations.status == 200, f"reset-delegations failed with {reset_delegations.status}")


def apply_scenario_and_seed() -> dict:
    apply_scenario()
    seed_result = post_json(f"/dev/games/{ROOM_CODE}/seed-technical-run")
    expect(seed_result.get("ok") is True, "seed-technical-run did not return ok=true")
    return seed_result


def apply_scenario() -> None:
    apply_result = post_json(
        f"/dev/games/{ROOM_CODE}/scenario/apply",
        {"scenario_code": SCENARIO_CODE},
    )
    expect(apply_result.get("ok") is True, "scenario apply did not return ok=true")


def find_whisper_players(seed_payload: dict) -> list[dict]:
    whisper_players = []
    for house in seed_payload.get("houses", []):
        for player in house.get("players", []):
            if player.get("role_code") == "whisper_master":
                state = get_json(f"/player/me/{player['player_token']}")
                whisper_players.append(
                    {
                        "player_id": int(state["player"]["id"]),
                        "player_token": player["player_token"],
                        "house_id": int(state["house"]["id"]),
                        "house_name": str(state["house"]["name"]),
                    }
                )
    expect(len(whisper_players) >= 2, "Expected at least two whisper masters in technical seed")
    return whisper_players


def build_influence_map(master_state: dict) -> dict[int, int]:
    result = {}
    for house in master_state.get("houses", []):
        resources = house.get("resources") or {}
        result[int(house["id"])] = int(resources.get("influence") or 0)
    return result


def build_house_name_map(master_state: dict) -> dict[int, str]:
    result = {}
    for house in master_state.get("houses", []):
        result[int(house["id"])] = str(house.get("name") or "").strip()
    return result


def build_house_genitive(name: str) -> str:
    normalized = str(name or "").strip()
    if normalized.startswith("Дом "):
        return f"Дома {normalized[4:]}"
    return f"Дома {normalized}"


def validate_event_text(master_after: dict, tv_after: dict) -> str:
    latest_master_event = ((master_after.get("last_whisper") or {}).get("latest_event") or {})
    latest_tv_event = ((tv_after.get("last_whisper") or {}).get("latest_event") or {})
    master_text = str(latest_master_event.get("tv_text") or "").strip()
    tv_text = str(latest_tv_event.get("tv_text") or "").strip()
    expect_readable_russian(master_text, field_name="Master latest_event.tv_text")
    expect(tv_text == master_text, "TV latest_event.tv_text does not match master-state")
    expect_readable_russian(tv_text, field_name="TV latest_event.tv_text")
    return master_text


def open_last_whisper() -> None:
    open_result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/last_whisper")
    expect(open_result.get("ok") is True, "open-phase/last_whisper did not return ok=true")


def adjust_influence(house_id: int, delta: int) -> dict:
    result = post_json(
        f"/dev/houses/{house_id}/resource-adjust",
        {"resource": "influence", "delta": delta},
    )
    expect(result.get("ok") is True, f"resource-adjust failed for house {house_id} delta {delta}")
    return result


def create_single_house_with_whisper_player() -> dict:
    start_response = http_form_post(
        "/delegation/start",
        {
            "game_code": ROOM_CODE,
            "leader_nickname": "Zero Leader",
            "team_size_declared": 2,
            "entry_mode": "random",
        },
    )
    expect(start_response.status == 200, f"delegation/start returned {start_response.status}")
    invite_match = re.search(r"invite_code=([A-Z0-9]+)", start_response.body)
    expect(invite_match is not None, "Could not parse invite_code from delegation/start response")
    invite_code = str(invite_match.group(1))

    join_response = http_form_post(
        "/delegation/join",
        {
            "game_code": ROOM_CODE,
            "invite_code": invite_code,
            "nickname": "Zero Whisper",
        },
    )
    expect(join_response.status == 200, f"delegation/join returned {join_response.status}")
    player_match = re.search(rf"/house/{invite_code}/player/(\d+)", join_response.body)
    expect(player_match is not None, "Could not parse joined player_id from delegation/join response")
    player_id = int(player_match.group(1))

    assign_response = get_text(f"/house/{invite_code}/assign-role/{player_id}/whisper_master")
    expect(assign_response.status == 200, f"assign-role whisper_master returned {assign_response.status}")

    return {
        "invite_code": invite_code,
        "player_id": player_id,
    }


def run_happy_path(summary: dict) -> None:
    seed_result = apply_scenario_and_seed()
    whisper_players = find_whisper_players(seed_result)
    preparer = whisper_players[0]
    attacker = whisper_players[1]

    open_last_whisper()

    before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_map = build_influence_map(before_master)

    leader_house_id = attacker["house_id"]
    setup_result = post_json(
        f"/player/last-whisper/action/{preparer['player_id']}",
        {"action_code": "quiet_support", "target_house_id": leader_house_id},
    )
    expect(setup_result.get("ok") is True, "quiet_support setup did not return ok=true")

    after_setup_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    after_setup_map = build_influence_map(after_setup_master)
    expect(
        after_setup_map[leader_house_id] - before_map[leader_house_id] == 1,
        "quiet_support setup did not create a clear leader",
    )

    crown_before = after_setup_map
    crown_result = post_json(
        f"/player/last-whisper/action/{attacker['player_id']}",
        {"action_code": "crown_tax"},
    )
    expect(crown_result.get("ok") is True, "crown_tax action was not accepted")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    crown_after = build_influence_map(master_after)
    deltas = {house_id: crown_after[house_id] - crown_before[house_id] for house_id in crown_before}

    expect(deltas.get(leader_house_id) == -1, "Leader did not lose exactly 1 influence from crown_tax")
    for house_id, delta in deltas.items():
        if house_id != leader_house_id:
            expect(delta == 0, f"Non-leader house {house_id} changed by {delta} influence")

    latest_master_event = ((master_after.get("last_whisper") or {}).get("latest_event") or {})
    expect(
        int(latest_master_event.get("target_house_id") or 0) == leader_house_id,
        "Master latest_event.target_house_id mismatch",
    )
    latest_text = validate_event_text(master_after, tv_after)
    expect(SUCCESS_TEXT_PART in latest_text, "Success text for crown_tax is missing influence loss wording")

    repeat_result = post_json(
        f"/player/last-whisper/action/{attacker['player_id']}",
        {"action_code": "crown_tax"},
    )
    expect(repeat_result.get("ok") is False, "Repeated crown_tax submission was not blocked")

    summary["happy_path"] = {
        "preparer_player_id": preparer["player_id"],
        "attacker_player_id": attacker["player_id"],
        "leader_house_id": leader_house_id,
        "influence_deltas": deltas,
        "latest_event_text": latest_text,
        "repeat_submit_message": repeat_result.get("message"),
    }


def run_tie_case(summary: dict) -> None:
    reset_room()
    seed_result = apply_scenario_and_seed()
    whisper_players = find_whisper_players(seed_result)
    attacker = whisper_players[0]

    open_last_whisper()

    before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_map = build_influence_map(before_master)

    crown_result = post_json(
        f"/player/last-whisper/action/{attacker['player_id']}",
        {"action_code": "crown_tax"},
    )
    expect(crown_result.get("ok") is True, "crown_tax tie-case action was not accepted")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after_map = build_influence_map(master_after)
    deltas = {house_id: after_map[house_id] - before_map[house_id] for house_id in before_map}

    for house_id, delta in deltas.items():
        expect(delta == 0, f"Tie case changed house {house_id} by {delta} influence")

    latest_text = validate_event_text(master_after, tv_after)
    expect(latest_text == TIE_TEXT, "Tie-case text does not match safe no-target wording")

    summary["tie_case"] = {
        "attacker_player_id": attacker["player_id"],
        "influence_deltas": deltas,
        "latest_event_text": latest_text,
    }


def run_zero_delta_case(summary: dict) -> None:
    reset_room()
    apply_scenario()
    single_house = create_single_house_with_whisper_player()

    open_last_whisper()

    before_master = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    before_map = build_influence_map(before_master)
    house_names = build_house_name_map(before_master)
    expect(len(before_map) == 1, f"Zero-delta setup expected exactly one house, got {len(before_map)}")
    target_house_id = next(iter(before_map))
    target_house_name = house_names[target_house_id]
    expect(before_map.get(target_house_id) == 0, "Zero-delta setup expected the only house to be at 0 influence")

    crown_result = post_json(
        f"/player/last-whisper/action/{single_house['player_id']}",
        {"action_code": "crown_tax"},
    )
    expect(crown_result.get("ok") is True, "crown_tax zero-delta action was not accepted")

    master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
    tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
    after_map = build_influence_map(master_after)
    deltas = {house_id: after_map[house_id] - before_map[house_id] for house_id in before_map}

    for house_id, delta in deltas.items():
        expect(delta == 0, f"Zero-delta case changed house {house_id} by {delta} influence")

    latest_master_event = ((master_after.get("last_whisper") or {}).get("latest_event") or {})
    expect(
        int(latest_master_event.get("target_house_id") or 0) == target_house_id,
        "Zero-delta case latest_event.target_house_id mismatch",
    )
    latest_text = validate_event_text(master_after, tv_after)
    expect(
        latest_text == ZERO_DELTA_TEXT.format(house_name=build_house_genitive(target_house_name)),
        "Zero-delta case text does not match honest clamped wording",
    )

    summary["zero_delta_case"] = {
        "attacker_player_id": single_house["player_id"],
        "leader_house_id": target_house_id,
        "influence_deltas": deltas,
        "latest_event_text": latest_text,
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

        run_tie_case(summary)
        summary["checks"].append("tie case")

        run_zero_delta_case(summary)
        summary["checks"].append("zero-delta case")

        print("LAST WHISPER CROWN TAX SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("LAST WHISPER CROWN TAX SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_room()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
