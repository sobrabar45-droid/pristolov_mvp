#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


BASE_URL = "http://127.0.0.1:8000"
ROOM_CODE = "LIVE01"
SCENARIO_CODE = "season1_mvp_live_v2"


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


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

    mojibake_fragments = ("�", "Ð", "Ñ", "Ã")
    expect(
        not any(fragment in normalized for fragment in mojibake_fragments),
        f"{field_name} contains mojibake: {normalized!r}",
    )

    cyrillic_count = sum(1 for char in normalized if "\u0400" <= char <= "\u04FF")
    expect(cyrillic_count >= 5, f"{field_name} does not look like readable Russian: {normalized!r}")


def find_whisper_master(seed_payload: dict) -> tuple[int, int]:
    for house in seed_payload.get("houses", []):
        for player in house.get("players", []):
            if player.get("role_code") == "whisper_master":
                player_url = str(player.get("player_url") or "")
                player_id = int(player_url.rstrip("/").split("/")[-1])
                house_state = get_json(f"/player/me/{player['player_token']}")
                house_id = int(house_state["house"]["id"])
                return player_id, house_id
    raise SmokeFailure("Whisper Master not found in seed payload")


def build_influence_map(master_state: dict) -> dict[int, int]:
    result = {}
    for house in master_state.get("houses", []):
        house_id = int(house["id"])
        resources = house.get("resources") or {}
        result[house_id] = int(resources.get("influence") or 0)
    return result


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "checks": [],
    }

    try:
        post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")

        reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
        if reset_delegations.status >= 500:
            reset_delegations = get_text(f"/dev/reset-delegations/{ROOM_CODE}")
        expect(reset_delegations.status == 200, f"reset-delegations failed with {reset_delegations.status}")
        summary["checks"].append("runtime reset")

        apply_result = post_json(
            f"/dev/games/{ROOM_CODE}/scenario/apply",
            {"scenario_code": SCENARIO_CODE},
        )
        expect(apply_result.get("ok") is True, "scenario apply did not return ok=true")
        summary["checks"].append("scenario applied")

        seed_result = post_json(f"/dev/games/{ROOM_CODE}/seed-technical-run")
        expect(seed_result.get("ok") is True, "seed-technical-run did not return ok=true")
        whisper_player_id, whisper_house_id = find_whisper_master(seed_result)
        summary["whisper_player_id"] = whisper_player_id
        summary["whisper_house_id"] = whisper_house_id
        summary["checks"].append("technical run seeded")

        open_phase_result = post_json(f"/dev/games/{ROOM_CODE}/open-phase/last_whisper")
        expect(open_phase_result.get("ok") is True, "open-phase/last_whisper did not return ok=true")
        summary["checks"].append("last whisper opened")

        player_state = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        before_map = build_influence_map(player_state)
        target_house_id = next((house_id for house_id in before_map if house_id != whisper_house_id), None)
        expect(target_house_id is not None, "Could not determine target house for quiet support")
        summary["target_house_id"] = target_house_id

        apply_action_result = post_json(
            f"/player/last-whisper/action/{whisper_player_id}",
            {"action_code": "quiet_support", "target_house_id": target_house_id},
        )
        expect(apply_action_result.get("ok") is True, "quiet_support action was not accepted")
        summary["checks"].append("quiet support applied")

        master_after = get_json(f"/dev/game-master/{ROOM_CODE}/state")
        tv_after = get_json(f"/dev/game-master/{ROOM_CODE}/tv-state")
        after_map = build_influence_map(master_after)

        deltas = {
            house_id: after_map.get(house_id, 0) - before_map.get(house_id, 0)
            for house_id in before_map
        }
        summary["influence_deltas"] = deltas

        expect(deltas.get(target_house_id) == 1, "Target house did not gain exactly +1 influence")
        for house_id, delta in deltas.items():
            if house_id != target_house_id:
                expect(delta == 0, f"Non-target house {house_id} changed by {delta} influence")
        summary["checks"].append("influence delta exact")

        expected_event_text = None
        latest_master_event = ((master_after.get("last_whisper") or {}).get("latest_event") or {})
        latest_tv_event = ((tv_after.get("last_whisper") or {}).get("latest_event") or {})

        expect(int(latest_master_event.get("target_house_id") or 0) == target_house_id, "Master latest_event.target_house_id mismatch")
        expected_event_text = str(latest_master_event.get("tv_text") or "").strip()
        expect_readable_russian(expected_event_text, field_name="Master latest_event.tv_text")
        expect(
            str(latest_tv_event.get("tv_text") or "").strip() == expected_event_text,
            "TV latest_event.tv_text does not match master-state",
        )
        expect_readable_russian(str(latest_tv_event.get("tv_text") or "").strip(), field_name="TV latest_event.tv_text")
        summary["latest_event_text"] = expected_event_text
        summary["checks"].append("master and tv event exposed")

        repeat_action_result = post_json(
            f"/player/last-whisper/action/{whisper_player_id}",
            {"action_code": "quiet_support", "target_house_id": target_house_id},
        )
        expect(repeat_action_result.get("ok") is False, "Repeated submission was not blocked")
        summary["repeat_submit_message"] = repeat_action_result.get("message")
        summary["checks"].append("repeat submit blocked")

        print("LAST WHISPER QUIET SUPPORT SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0

    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("LAST WHISPER QUIET SUPPORT SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            post_json(f"/dev/games/{ROOM_CODE}/reset-runtime")
        except Exception:
            pass
        try:
            get_text(f"/dev/reset-delegations/{ROOM_CODE}")
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
