#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from urllib.parse import urlparse

from smoke_last_whisper_quiet_support import (
    BASE_URL,
    ROOM_CODE,
    SCENARIO_CODE,
    SmokeFailure,
    expect,
    get_text,
    post_json,
)


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


MIN_HTML_LENGTH = 1000
MOJIBAKE_MARKERS = ("\ufffd", "Ð", "Ñ", "Ã")


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


def first_player_path(seed_payload: dict) -> str:
    for house in seed_payload.get("houses") or []:
        for player in house.get("players") or []:
            player_url = str(player.get("player_url") or "").strip()
            if player_url:
                parsed = urlparse(player_url)
                if parsed.path:
                    return parsed.path
    raise SmokeFailure("No player_url found in technical seed payload")


def assert_html_route(
    *,
    label: str,
    path: str,
    required_markers: list[str],
    forbidden_markers: tuple[str, ...] = MOJIBAKE_MARKERS,
) -> dict:
    expect("/dev/tv-screen/" not in path, f"{label} uses legacy TV route: {path}")

    response = get_text(path)
    expect(response.status == 200, f"{label} route returned HTTP {response.status}: {path}")

    html = response.body or ""
    expect(len(html.strip()) >= MIN_HTML_LENGTH, f"{label} HTML is unexpectedly small/blank")
    expect("<html" in html.lower(), f"{label} response does not look like HTML")

    missing = [marker for marker in required_markers if marker not in html]
    expect(not missing, f"{label} HTML missing markers: {missing}")

    found_forbidden = [marker for marker in forbidden_markers if marker in html]
    expect(not found_forbidden, f"{label} HTML contains mojibake markers: {found_forbidden}")

    return {
        "path": path,
        "status": response.status,
        "html_length": len(html),
        "markers_checked": required_markers,
    }


def main() -> int:
    summary = {
        "room_code": ROOM_CODE,
        "scenario_code": SCENARIO_CODE,
        "tooling": "command-level HTML fetch",
        "checks": [],
        "routes": {},
        "note": "Playwright is not required by this smoke; true pixel/browser rendering remains a manual/browser-tooling follow-up.",
    }

    try:
        reset_runtime()
        summary["checks"].append("runtime reset")

        seed_result = apply_scenario_and_seed()
        summary["checks"].append("scenario applied and technical run seeded")

        master_path = f"/dev/master-screen/{ROOM_CODE}"
        tv_path = f"/dev/tv-mode/{ROOM_CODE}"
        player_path = first_player_path(seed_result)

        summary["routes"]["master"] = assert_html_route(
            label="Master screen",
            path=master_path,
            required_markers=[
                "приСтолов",
                "Пульт ведущего",
                "eventFeedList",
                "/dev/game-master/${ROOM_CODE}/state",
            ],
        )
        summary["checks"].append("master screen HTML route rendered")

        summary["routes"]["tv"] = assert_html_route(
            label="TV mode",
            path=tv_path,
            required_markers=[
                "приСтолов",
                "TV Mode",
                "eventsFeed",
                "recent_events",
                "/dev/game-master/${ROOM_CODE}/tv-state",
            ],
        )
        summary["checks"].append("tv mode HTML route rendered")

        summary["routes"]["player"] = assert_html_route(
            label="Player room",
            path=player_path,
            required_markers=[
                "Игрок",
                "Состояние игры",
                "lastWhisperSection",
                "/player/me/",
            ],
        )
        summary["checks"].append("player room HTML route rendered")

        expect("/dev/tv-screen/" not in tv_path, "Production TV smoke accidentally selected legacy TV route")
        summary["checks"].append("legacy tv route avoided")

        print("VISUAL RUNTIME ROUTES SMOKE: PASS")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except SmokeFailure as exc:
        summary["failed"] = str(exc)
        print("VISUAL RUNTIME ROUTES SMOKE: FAIL", file=sys.stderr)
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    finally:
        try:
            reset_runtime()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
