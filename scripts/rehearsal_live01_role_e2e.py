#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from fastapi.testclient import TestClient
from sqlalchemy.orm import joinedload


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models.game import Game
from app.models.game_assignment import GameAssignment
from app.models.game_deal import GameDeal
from app.models.game_duel import GameDuel
from app.models.game_expedition import GameExpedition
from app.models.game_host_round import GameHostRound
from app.models.game_map_state import GameMapState
from app.models.game_map_visit import GameMapVisit
from app.models.game_phase import GamePhase
from app.models.house import House
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.player import Player


ROOM_CODE = "LIVE01"
CONFIRM_RESET = "LIVE01_REHEARSAL_OK"
SCENARIO_CODE = "season1_mvp_live_v2"
TARGET_GOLD = 20


class RehearsalFailure(RuntimeError):
    pass


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise RehearsalFailure(message)


def redacted_token(token: str | None) -> str | None:
    if not token:
        return None
    token = str(token)
    if len(token) <= 12:
        return f"{token[:3]}...{token[-3:]}"
    return f"{token[:6]}...{token[-6:]}"


def safe_player_path(player_url: str) -> str:
    parsed = urlparse(str(player_url or ""))
    return parsed.path or str(player_url or "")


def protected_headers() -> dict[str, str]:
    token = (settings.ADMIN_ROUTE_TOKEN or "").strip()
    return {"X-Admin-Token": token} if token else {}


CLIENT = TestClient(app)


def request_json(method: str, path: str, payload: dict | None = None) -> dict:
    response = CLIENT.request(method, path, json=payload, headers=protected_headers())
    if response.status_code != 200:
        raise RehearsalFailure(f"{method} {path} returned {response.status_code}: {response.text[:500]}")
    try:
        data = response.json()
    except Exception as exc:
        raise RehearsalFailure(f"{method} {path} did not return JSON: {response.text[:500]}") from exc
    return data


def request_text(method: str, path: str, payload: dict | None = None) -> str:
    response = CLIENT.request(method, path, json=payload, headers=protected_headers())
    if response.status_code != 200:
        raise RehearsalFailure(f"{method} {path} returned {response.status_code}: {response.text[:500]}")
    return response.text


def room_snapshot(room_code: str) -> dict:
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()
        if not game:
            return {
                "room_code": room_code,
                "game_found": False,
                "players_count": 0,
                "houses_count": 0,
                "role_counts": {},
                "gold_transaction_count": 0,
                "deal_count": 0,
            }

        players = (
            db.query(Player)
            .options(joinedload(Player.role))
            .filter(Player.game_id == game.id)
            .all()
        )
        role_counts = Counter(
            player.role.code if player.role and player.role.code else "none"
            for player in players
        )
        houses = db.query(House).filter(House.game_id == game.id).all()
        return {
            "room_code": room_code,
            "game_found": True,
            "game_id": game.id,
            "title": game.title,
            "scenario_code": getattr(game, "scenario_code", None),
            "players_count": len(players),
            "houses_count": len(houses),
            "role_counts": dict(sorted(role_counts.items())),
            "gold_transaction_count": db.query(HouseGoldTransaction).filter(HouseGoldTransaction.game_id == game.id).count(),
            "deal_count": db.query(GameDeal).filter(GameDeal.game_id == game.id).count(),
            "active_phase_count": db.query(GamePhase).filter(GamePhase.game_id == game.id, GamePhase.status == "active").count(),
            "host_round_count": db.query(GameHostRound).filter(GameHostRound.game_id == game.id).count(),
            "assignment_count": db.query(GameAssignment).filter(GameAssignment.game_id == game.id).count(),
            "expedition_count": db.query(GameExpedition).filter(GameExpedition.game_id == game.id).count(),
            "duel_count": db.query(GameDuel).filter(GameDuel.game_id == game.id).count(),
            "map_state_count": db.query(GameMapState).filter(GameMapState.game_id == game.id).count(),
            "map_visit_count": db.query(GameMapVisit).filter(GameMapVisit.game_id == game.id).count(),
            "houses": [
                {
                    "id": house.id,
                    "name": house.name,
                    "gold": int(house.resource_gold or 0),
                    "influence": int(house.resource_influence or 0),
                    "players_count": db.query(Player).filter(Player.house_id == house.id).count(),
                }
                for house in houses
            ],
        }
    finally:
        db.close()


def count_gold_transactions(room_code: str) -> int:
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()
        if not game:
            return 0
        return db.query(HouseGoldTransaction).filter(HouseGoldTransaction.game_id == game.id).count()
    finally:
        db.close()


def house_gold(house_id: int) -> int:
    db = SessionLocal()
    try:
        house = db.query(House).filter(House.id == house_id).first()
        expect(house is not None, f"house {house_id} not found")
        return int(house.resource_gold or 0)
    finally:
        db.close()


def deal_status(deal_id: int) -> str | None:
    db = SessionLocal()
    try:
        deal = db.query(GameDeal).filter(GameDeal.id == deal_id).first()
        return deal.status if deal else None
    finally:
        db.close()


def pending_shop_request_count(room_code: str) -> int:
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_code == room_code).first()
        if not game:
            return 0
        deals = (
            db.query(GameDeal)
            .filter(GameDeal.game_id == game.id, GameDeal.status == "pending")
            .all()
        )
        return sum(
            1
            for deal in deals
            if isinstance(deal.offer, dict)
            and str(deal.offer.get("type") or "") == "treasurer_shop_request"
        )
    finally:
        db.close()


def find_players(seed_payload: dict) -> list[dict]:
    players: list[dict] = []
    for house_payload in seed_payload.get("houses") or []:
        for player_payload in house_payload.get("players") or []:
            token = player_payload.get("player_token")
            state = request_json("GET", f"/player/me/{token}")
            player_url = str(player_payload.get("player_url") or "")
            players.append(
                {
                    "player_id": int(state["player"]["id"]),
                    "token": token,
                    "token_redacted": redacted_token(token),
                    "player_path": safe_player_path(player_url),
                    "role_code": str(player_payload.get("role_code") or state["role"].get("code") or ""),
                    "house_id": int(state["house"]["id"]),
                    "house_name": str(state["house"].get("name") or ""),
                    "nickname": str(state["player"].get("nickname") or ""),
                }
            )
    return players


def first_role(players: list[dict], role_code: str, *, house_id: int | None = None, other_house_id: int | None = None) -> dict:
    for player in players:
        if player["role_code"] != role_code:
            continue
        if house_id is not None and player["house_id"] != house_id:
            continue
        if other_house_id is not None and player["house_id"] == other_house_id:
            continue
        return player
    raise RehearsalFailure(f"missing player role={role_code} house_id={house_id} other_house_id={other_house_id}")


def ensure_house_gold(house_id: int, target_gold: int, summary: dict) -> None:
    current = house_gold(house_id)
    delta = target_gold - current
    if delta == 0:
        return
    result = request_json(
        "POST",
        f"/dev/houses/{house_id}/gold-adjust",
        {
            "gold_delta": delta,
            "reason": "LIVE01 role-complete rehearsal setup",
        },
    )
    expect(result.get("ok") is True, f"gold-adjust failed for house {house_id}: {result}")
    summary["checks"].append(f"house {house_id} gold adjusted to {target_gold}")


def assert_no_dev_links(label: str, html: str) -> None:
    expect("/dev/" not in html, f"{label} contains /dev/ link")


def surface_checks(room_code: str, players: list[dict], summary: dict) -> None:
    for player in players:
        html = request_text("GET", player["player_path"])
        expect("<html" in html.lower(), f"player room for {player['role_code']} did not render HTML")
        assert_no_dev_links(f"player room {player['role_code']}", html)
    cashier = request_text("GET", f"/cashier/gold-desk/{room_code}")
    assert_no_dev_links("cashier", cashier)
    for marker in ("manualGrantButton", "grant-from-check", "queue-section", "data-confirm-shop-request"):
        expect(marker in cashier, f"cashier page missing marker {marker}")
    request_text("GET", f"/dev/master-screen/{room_code}")
    request_text("GET", f"/dev/tv-mode/{room_code}")
    summary["checks"].append("surface HTML checks passed for player/cashier/master/tv")


def run_treasurer_shop(room_code: str, treasurer: dict, summary: dict) -> None:
    before_gold = house_gold(treasurer["house_id"])
    before_tx = count_gold_transactions(room_code)

    create = request_json(
        "POST",
        f"/player/treasurer-shop/request/{treasurer['player_id']}",
        {"action_code": "author_tea"},
    )
    expect(create.get("ok") is True, f"treasurer shop request failed: {create}")
    request_id = int(create.get("request_id") or 0)
    expect(request_id > 0, f"treasurer shop request_id missing: {create}")
    expect(house_gold(treasurer["house_id"]) == before_gold, "shop request changed gold before confirmation")
    expect(count_gold_transactions(room_code) == before_tx, "shop request created gold transaction before confirmation")
    expect(pending_shop_request_count(room_code) >= 1, "pending shop request not visible in DB")

    cashier_html = request_text("GET", f"/cashier/gold-desk/{room_code}")
    expect(str(request_id) in cashier_html, "cashier queue does not include request id")
    expect("Заказ принят" in cashier_html, "cashier queue missing confirm button")

    confirm = request_json("POST", f"/cashier/treasurer-shop/requests/{request_id}/confirm")
    expect(confirm.get("ok") is True, f"shop confirm failed: {confirm}")
    expect(confirm.get("gold_before") == before_gold, f"shop confirm gold_before mismatch: {confirm}")
    expect(confirm.get("gold_after") == before_gold - 3, f"shop confirm gold_after mismatch: {confirm}")
    expect(house_gold(treasurer["house_id"]) == before_gold - 3, "house gold did not decrease by 3 on confirm")
    expect(count_gold_transactions(room_code) == before_tx + 1, "shop confirm did not create exactly one transaction")
    expect(deal_status(request_id) == "completed", "shop request did not become completed")

    master_state = request_json("GET", f"/dev/game-master/{room_code}/state")
    tv_state = request_json("GET", f"/dev/game-master/{room_code}/tv-state")
    master_events = json.dumps(master_state.get("recent_events") or [], ensure_ascii=False)
    tv_events = json.dumps(tv_state.get("recent_events") or [], ensure_ascii=False)
    expect("author_tea" in master_events or "Авторский" in master_events or "авторский" in master_events.lower(), "Master recent events missing shop purchase")
    expect("author_tea" in tv_events or "Авторский" in tv_events or "авторский" in tv_events.lower(), "TV recent events missing shop purchase")
    summary["treasurer_shop"] = {
        "request_id": request_id,
        "gold_before": before_gold,
        "gold_after": before_gold - 3,
        "transaction_delta": 1,
        "status": "completed",
    }
    summary["checks"].append("treasurer shop request/confirm passed")


def run_gold_desk(room_code: str, house_id: int, summary: dict) -> None:
    before_gold = house_gold(house_id)
    before_tx = count_gold_transactions(room_code)
    manual = request_json(
        "POST",
        f"/gold/houses/{house_id}/grant",
        {
            "amount": 1,
            "source_type": "cashier_manual",
            "reason": "LIVE01 rehearsal manual +1",
        },
    )
    expect(manual.get("ok") is True, f"manual grant failed: {manual}")
    expect(manual.get("gold_after") == before_gold + 1, f"manual grant gold mismatch: {manual}")

    check = request_json(
        "POST",
        f"/gold/houses/{house_id}/grant-from-check",
        {"amount_rub": 500, "check_id": 5001},
    )
    expect(check.get("ok") is True, f"check grant failed: {check}")
    expect(check.get("gold_after") == before_gold + 2, f"check grant gold mismatch: {check}")
    expect(count_gold_transactions(room_code) == before_tx + 2, "gold desk did not add exactly two transactions")
    summary["gold_desk"] = {
        "house_id": house_id,
        "gold_before": before_gold,
        "gold_after": before_gold + 2,
        "transaction_delta": 2,
    }
    summary["checks"].append("cashier manual +1 and check amount 500 passed")


def run_diplomacy(room_code: str, diplomat_a: dict, diplomat_b: dict, summary: dict) -> int:
    opened = request_json("POST", f"/dev/games/{room_code}/open-phase/diplomacy")
    expect(opened.get("ok") is True, f"open diplomacy failed: {opened}")
    create = request_json(
        "POST",
        f"/player/deals/create/{diplomat_a['player_id']}",
        {
            "target_house_id": diplomat_b["house_id"],
            "deal_type": "alliance",
            "offer_text": "LIVE01 rehearsal alliance",
        },
    )
    expect(create.get("ok") is True, f"alliance create failed: {create}")
    deal_id = int((create.get("deal") or {}).get("id") or 0)
    expect(deal_id > 0, f"alliance deal id missing: {create}")
    respond = request_json(
        "POST",
        f"/player/deals/respond/{diplomat_b['player_id']}",
        {"deal_id": deal_id, "action": "accept"},
    )
    expect(respond.get("ok") is True, f"alliance accept failed: {respond}")
    expect((respond.get("deal") or {}).get("status") == "alliance_active", f"alliance not active: {respond}")
    summary["diplomacy"] = {
        "alliance_deal_id": deal_id,
        "status": "alliance_active",
    }
    summary["checks"].append("diplomacy alliance create/accept passed")
    return deal_id


def run_last_whisper(room_code: str, whisper: dict, target_house_id: int, summary: dict) -> None:
    opened = request_json("POST", f"/dev/games/{room_code}/open-phase/last_whisper")
    expect(opened.get("ok") is True, f"open last_whisper failed: {opened}")
    action = request_json(
        "POST",
        f"/player/last-whisper/action/{whisper['player_id']}",
        {"action_code": "quiet_support", "target_house_id": target_house_id},
    )
    expect(action.get("ok") is True, f"quiet_support failed: {action}")
    repeat = request_json(
        "POST",
        f"/player/last-whisper/action/{whisper['player_id']}",
        {"action_code": "quiet_support", "target_house_id": target_house_id},
    )
    expect(repeat.get("ok") is False, f"quiet_support repeat was not blocked: {repeat}")
    summary["last_whisper"] = {
        "action": "quiet_support",
        "first_ok": True,
        "repeat_blocked": True,
        "target_house_id": target_house_id,
    }
    summary["checks"].append("last whisper quiet_support and repeat block passed")


def run_lord_lady(room_code: str, lord: dict, summary: dict) -> None:
    opened = request_json("POST", f"/dev/games/{room_code}/open-phase/map")
    expect(opened.get("ok") is True, f"open map failed: {opened}")
    result = request_json(
        "POST",
        f"/player/expedition/create/{lord['player_id']}",
        {
            "members_count": 2,
            "role_codes": ["treasurer", "maester"],
        },
    )
    expect(result.get("ok") is True, f"lord expedition create failed: {result}")
    summary["lord_lady"] = {
        "expedition_id": result.get("expedition_id"),
        "members_count": result.get("members_count"),
        "role_codes": result.get("role_codes"),
    }
    summary["checks"].append("lord/lady expedition creation passed")


def run_rehearsal(room_code: str) -> dict:
    summary: dict = {
        "ok": False,
        "room_code": room_code,
        "scenario_code": SCENARIO_CODE,
        "checks": [],
        "approval": "user approved LIVE01 rehearsal because no real players yet",
        "final_state_policy": "left_as_role_complete_rehearsal_fixture",
    }
    summary["pre_state"] = room_snapshot(room_code)

    reset_runtime = request_json("POST", f"/dev/games/{room_code}/reset-runtime")
    expect(reset_runtime.get("ok") is True, f"reset-runtime failed: {reset_runtime}")
    summary["reset_runtime"] = reset_runtime

    reset_delegations_html = request_text("GET", f"/dev/reset-delegations/{room_code}")
    expect("LIVE01" in reset_delegations_html or room_code in reset_delegations_html, "reset-delegations response did not mention room")
    summary["reset_delegations"] = {"ok": True, "html_length": len(reset_delegations_html)}
    summary["checks"].append("reset-runtime and reset-delegations completed")

    scenario = request_json("POST", f"/dev/games/{room_code}/scenario/apply", {"scenario_code": SCENARIO_CODE})
    expect(scenario.get("ok") is True, f"scenario apply failed: {scenario}")
    summary["checks"].append("scenario applied")

    seed = request_json("POST", f"/dev/games/{room_code}/seed-technical-run")
    expect(seed.get("ok") is True, f"seed-technical-run failed: {seed}")
    players = find_players(seed)
    summary["fixture"] = {
        "houses_count": len(seed.get("houses") or []),
        "players_count": len(players),
        "players_redacted": [
            {
                "player_id": player["player_id"],
                "role_code": player["role_code"],
                "house_id": player["house_id"],
                "house_name": player["house_name"],
                "token": player["token_redacted"],
                "player_path": player["player_path"],
            }
            for player in players
        ],
    }
    summary["checks"].append("technical role-complete fixture seeded")

    role_counts = Counter(player["role_code"] for player in players)
    for required_role in ("lord_lady", "treasurer", "diplomat", "whisper_master", "maester", "house_sworn"):
        expect(role_counts[required_role] >= 1, f"missing required role after seed: {required_role}")
    summary["role_inventory"] = dict(sorted(role_counts.items()))

    houses = sorted({player["house_id"] for player in players})
    expect(len(houses) >= 2, "expected at least two houses for diplomacy/whisper checks")
    for house_id in houses:
        ensure_house_gold(house_id, TARGET_GOLD, summary)

    surface_checks(room_code, players, summary)

    treasurer = first_role(players, "treasurer")
    run_treasurer_shop(room_code, treasurer, summary)
    run_gold_desk(room_code, treasurer["house_id"], summary)

    diplomat_a = first_role(players, "diplomat", house_id=treasurer["house_id"])
    diplomat_b = first_role(players, "diplomat", other_house_id=treasurer["house_id"])
    run_diplomacy(room_code, diplomat_a, diplomat_b, summary)

    whisper = first_role(players, "whisper_master", house_id=treasurer["house_id"])
    target_house_id = diplomat_b["house_id"]
    run_last_whisper(room_code, whisper, target_house_id, summary)

    lord = first_role(players, "lord_lady", house_id=treasurer["house_id"])
    run_lord_lady(room_code, lord, summary)

    summary["post_state"] = room_snapshot(room_code)
    summary["go_no_go"] = "conditional_go_for_final_manual_acceptance"
    summary["blockers"] = []
    summary["ok"] = True
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled LIVE01 role-complete rehearsal E2E.")
    parser.add_argument("--room", required=True)
    parser.add_argument("--confirm-reset", required=True)
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    if args.room != ROOM_CODE or args.confirm_reset != CONFIRM_RESET:
        print(
            "Refusing to run. Required flags: --room LIVE01 --confirm-reset LIVE01_REHEARSAL_OK",
            file=sys.stderr,
        )
        return 2

    try:
        summary = run_rehearsal(args.room)
    except Exception as exc:
        print("LIVE01 ROLE-COMPLETE REHEARSAL E2E: FAIL", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    print("LIVE01 ROLE-COMPLETE REHEARSAL E2E: PASS")
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
