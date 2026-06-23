"""Build real player polling paths and run the safe load probe.

This helper is read-only: it queries existing player tokens for a room and
delegates HTTP probing to scripts/load_probe_player_screens.py.
"""

from __future__ import annotations

import argparse
import tempfile
from functools import partial
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.database import SessionLocal
from app.models.game import Game
from app.models.player import Player


DEFAULT_PATHS_FILE = Path(tempfile.gettempdir()) / "pristolov_player_paths.txt"
DEFAULT_BASE_URL = "http://127.0.0.1:8000"
print = partial(print, flush=True)


def parse_clients(value: str) -> list[int]:
    clients: list[int] = []
    for part in value.split(","):
        stripped = part.strip()
        if not stripped:
            continue
        try:
            client_count = int(stripped)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid clients value: {stripped}") from exc
        if client_count <= 0:
            raise argparse.ArgumentTypeError("client counts must be positive")
        clients.append(client_count)
    if not clients:
        raise argparse.ArgumentTypeError("at least one client count is required")
    return clients


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe load probes against real PRISTOLOV player polling endpoints.",
    )
    parser.add_argument("--room-code", default="LIVE01", help="Room code to inspect. Default: LIVE01.")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help=f"Probe base URL. Default: {DEFAULT_BASE_URL}.")
    parser.add_argument("--clients", type=parse_clients, default=parse_clients("25,40,100"), help="Comma-separated client counts. Default: 25,40,100.")
    parser.add_argument("--duration", type=float, default=30.0, help="Probe duration per client count in seconds.")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between requests per client.")
    parser.add_argument("--jitter", type=float, default=0.2, help="Per-client interval jitter fraction.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument("--paths-file", default=str(DEFAULT_PATHS_FILE), help=f"Where to write generated paths. Default: {DEFAULT_PATHS_FILE}.")
    parser.add_argument("--allow-empty", action="store_true", help="Exit successfully when no player tokens exist.")
    parser.add_argument("--show-paths", action="store_true", help="Debug only: print generated token paths.")
    parser.add_argument("--allow-production", action="store_true", help="Forwarded to load_probe_player_screens.py for non-localhost URLs.")
    parser.add_argument("--admin-token-env", default="", help="Optional env var name for X-Admin-Token, forwarded to probe script.")
    return parser.parse_args()


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


def write_paths(tokens: list[str], paths_file: Path, show_paths: bool) -> int:
    paths_file.parent.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    for token in tokens:
        paths.append(f"/player/me/{token}")
        paths.append(f"/player/me/{token}/assignments")
    paths_file.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
    if show_paths:
        print("== generated paths ==")
        for path in paths:
            print(path)
    return len(paths)


def run_probe(args: argparse.Namespace, clients: int, paths_file: Path) -> int:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "load_probe_player_screens.py"),
        "--base-url",
        args.base_url,
        "--paths-file",
        str(paths_file),
        "--clients",
        str(clients),
        "--duration",
        str(args.duration),
        "--interval",
        str(args.interval),
        "--jitter",
        str(args.jitter),
        "--timeout",
        str(args.timeout),
    ]
    if args.allow_production:
        command.append("--allow-production")
    if args.admin_token_env:
        command.extend(["--admin-token-env", args.admin_token_env])

    print(f"\n== probe clients={clients} duration={args.duration}s interval={args.interval}s ==")
    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), check=False)
    print("suggested_log_check=journalctl -u pristolov.service -n 120 --no-pager | grep -Ei 'Traceback|ERROR|Exception|sqlite|locked|timeout' || true")
    return int(completed.returncode)


def main() -> int:
    args = parse_args()
    room_code = args.room_code.strip().upper()
    paths_file = Path(args.paths_file)

    players_found, tokens = find_player_tokens(room_code)
    paths_written = write_paths(tokens, paths_file, args.show_paths)

    print(f"room_code={room_code}")
    print(f"players_found={players_found}")
    print(f"tokens_found={len(tokens)}")
    print(f"paths_written={paths_written}")
    print(f"paths_file={paths_file}")

    if paths_written == 0:
        print("no_player_paths=stop: room has no players with player_token")
        return 0 if args.allow_empty else 2

    worst_return_code = 0
    for clients in args.clients:
        return_code = run_probe(args, clients, paths_file)
        worst_return_code = max(worst_return_code, return_code)

    return worst_return_code


if __name__ == "__main__":
    sys.exit(main())
