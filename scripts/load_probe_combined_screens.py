"""Run a safe passive combined load probe for PRISTOLOV screens.

This helper is read-only by design. It collects real player polling paths for a
room, adds passive operational screen/state paths, and delegates HTTP probing to
scripts/load_probe_player_screens.py.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from functools import partial
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.game import Game
from app.models.player import Player


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_PLAYER_PATHS_FILE = Path(tempfile.gettempdir()) / "pristolov_combined_player_paths.txt"
DEFAULT_OPERATIONAL_PATHS_FILE = Path(tempfile.gettempdir()) / "pristolov_combined_operational_paths.txt"
print = partial(print, flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a read-only combined load probe for PRISTOLOV player and operational screens.",
    )
    parser.add_argument("--room-code", default="LIVE01", help="Room code to inspect. Default: LIVE01.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Probe base URL. Default: {DEFAULT_BASE_URL}.")
    parser.add_argument("--player-clients", type=int, default=100, help="Concurrent simulated player clients.")
    parser.add_argument("--screen-clients", type=int, default=1, help="Concurrent simulated operational screen clients.")
    parser.add_argument("--duration", type=float, default=300.0, help="Probe duration in seconds.")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between requests per client.")
    parser.add_argument("--jitter", type=float, default=0.2, help="Per-client interval jitter fraction.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--admin-token-env", default="ADMIN_ROUTE_TOKEN", help="Env var containing X-Admin-Token.")
    parser.add_argument("--include-cashier", action="store_true", help="Include cashier Gold Desk GET page.")
    parser.add_argument("--allow-production", action="store_true", help="Required for non-localhost base URLs.")
    parser.add_argument("--show-paths", action="store_true", help="Debug only: print generated paths, including tokens.")
    parser.add_argument(
        "--player-paths-file",
        default=str(DEFAULT_PLAYER_PATHS_FILE),
        help=f"Where to write generated player paths. Default: {DEFAULT_PLAYER_PATHS_FILE}.",
    )
    parser.add_argument(
        "--operational-paths-file",
        default=str(DEFAULT_OPERATIONAL_PATHS_FILE),
        help=f"Where to write generated operational paths. Default: {DEFAULT_OPERATIONAL_PATHS_FILE}.",
    )
    return parser.parse_args()


def assert_safe_base_url(base_url: str, allow_production: bool) -> None:
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "localhost"} and not allow_production:
        raise SystemExit(
            "Refusing non-localhost probe without --allow-production. "
            "Use production probes only after explicit approval."
        )


def validate_args(args: argparse.Namespace) -> None:
    if args.player_clients <= 0:
        raise SystemExit("--player-clients must be greater than 0")
    if args.screen_clients <= 0:
        raise SystemExit("--screen-clients must be greater than 0")
    if args.duration <= 0:
        raise SystemExit("--duration must be greater than 0")
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than 0")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than 0")


def find_player_tokens(room_code: str) -> tuple[int, list[str]]:
    normalized_room_code = room_code.strip().upper()
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.room_code == normalized_room_code).first()
        if not game:
            return 0, []
        players = (
            db.query(Player)
            .filter(Player.game_id == game.id)
            .order_by(Player.id.asc())
            .all()
        )
        tokens = [
            str(player.player_token).strip()
            for player in players
            if player.player_token and str(player.player_token).strip()
        ]
        return len(players), tokens
    finally:
        db.close()


def build_player_paths(tokens: list[str]) -> list[str]:
    paths: list[str] = []
    for token in tokens:
        paths.append(f"/player/me/{token}")
        paths.append(f"/player/me/{token}/assignments")
    return paths


def build_operational_paths(room_code: str, include_cashier: bool) -> list[str]:
    paths = [
        f"/dev/game-master/{room_code}/state",
        f"/dev/game-master/{room_code}/tv-state",
    ]
    if include_cashier:
        paths.append(f"/cashier/gold-desk/{room_code}")
    return paths


def write_paths(paths: list[str], paths_file: Path, show_paths: bool, label: str) -> int:
    paths_file.parent.mkdir(parents=True, exist_ok=True)
    paths_file.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
    if show_paths:
        print(f"== {label} paths ==")
        for path in paths:
            print(path)
    return len(paths)


def build_probe_command(
    *,
    base_url: str,
    paths_file: Path,
    clients: int,
    duration: float,
    interval: float,
    jitter: float,
    timeout: float,
    allow_production: bool,
    admin_token_env: str,
) -> list[str]:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "load_probe_player_screens.py"),
        "--base-url",
        base_url,
        "--paths-file",
        str(paths_file),
        "--clients",
        str(clients),
        "--duration",
        str(duration),
        "--interval",
        str(interval),
        "--jitter",
        str(jitter),
        "--timeout",
        str(timeout),
    ]
    if allow_production:
        command.append("--allow-production")
    if admin_token_env:
        command.extend(["--admin-token-env", admin_token_env])

    return command


def print_log_checks() -> None:
    print("\n== suggested post-probe checks ==")
    print("journalctl_check=journalctl -u pristolov.service -n 160 --no-pager | grep -Ei 'Traceback|ERROR|Exception|sqlite|locked|timeout' || true")
    print("nginx_5xx_check=grep -E '\" 5[0-9][0-9] ' /var/log/nginx/access.log | tail -50 || true")


def main() -> int:
    args = parse_args()
    assert_safe_base_url(args.base_url, args.allow_production)
    validate_args(args)

    room_code = args.room_code.strip().upper()
    player_paths_file = Path(args.player_paths_file)
    operational_paths_file = Path(args.operational_paths_file)
    admin_token = os.environ.get(args.admin_token_env, "") if args.admin_token_env else ""

    players_found, tokens = find_player_tokens(room_code)
    player_paths = build_player_paths(tokens)
    operational_paths = build_operational_paths(room_code, args.include_cashier)

    player_paths_written = write_paths(player_paths, player_paths_file, args.show_paths, "player")
    operational_paths_count = write_paths(operational_paths, operational_paths_file, args.show_paths, "operational")

    print(f"room_code={room_code}")
    print(f"base_url={args.base_url}")
    print(f"players_found={players_found}")
    print(f"tokens_found={len(tokens)}")
    print(f"player_paths_written={player_paths_written}")
    print(f"player_paths_file={player_paths_file}")
    print(f"operational_paths_count={operational_paths_count}")
    print(f"operational_paths_file={operational_paths_file}")
    print(f"include_cashier={args.include_cashier}")
    print(f"admin_token_env={args.admin_token_env}")
    print(f"admin_token={'SET' if admin_token else 'not_set'}")

    if player_paths_written == 0:
        print("no_player_paths=stop: room has no players with player_token")
        return 2
    if operational_paths_count == 0:
        print("no_operational_paths=stop: no operational paths generated")
        return 2

    player_command = build_probe_command(
        base_url=args.base_url,
        paths_file=player_paths_file,
        clients=args.player_clients,
        duration=args.duration,
        interval=args.interval,
        jitter=args.jitter,
        timeout=args.timeout,
        allow_production=args.allow_production,
        admin_token_env=args.admin_token_env,
    )
    operational_command = build_probe_command(
        base_url=args.base_url,
        paths_file=operational_paths_file,
        clients=args.screen_clients,
        duration=args.duration,
        interval=args.interval,
        jitter=args.jitter,
        timeout=args.timeout,
        allow_production=args.allow_production,
        admin_token_env=args.admin_token_env,
    )

    print(f"\n== starting combined passive probe duration={args.duration}s ==")
    print(f"player_probe_clients={args.player_clients}")
    print(f"operational_probe_clients={args.screen_clients}")
    player_process = subprocess.Popen(player_command, cwd=str(PROJECT_ROOT))
    operational_process = subprocess.Popen(operational_command, cwd=str(PROJECT_ROOT))
    player_result = int(player_process.wait())
    operational_result = int(operational_process.wait())

    print_log_checks()

    if player_result != 0:
        print(f"player_probe_failed={player_result}")
    if operational_result != 0:
        print(f"operational_probe_failed={operational_result}")

    return max(player_result, operational_result)


if __name__ == "__main__":
    sys.exit(main())
