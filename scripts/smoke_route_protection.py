import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"
TOKEN = "route-protection-smoke-token"
WRONG_TOKEN = "wrong-route-protection-token"
HOST = "127.0.0.1"
PORT = int(os.environ.get("ROUTE_PROTECTION_SMOKE_PORT", "8765"))
BASE_URL = f"http://{HOST}:{PORT}"


class SmokeFailure(Exception):
    pass


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def request(method: str, path: str, token: str | None = None, payload: dict | None = None):
    data = None
    headers = {}
    if token is not None:
        headers["X-Admin-Token"] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            body = response.read().decode("utf-8", errors="replace")
            return response.status, body
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return exc.code, body


def wait_for_server(process: subprocess.Popen, stderr_path: Path) -> None:
    deadline = time.time() + 25
    while time.time() < deadline:
        if process.poll() is not None:
            stderr = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
            raise SmokeFailure(f"uvicorn exited early with code {process.returncode}: {stderr[-2000:]}")
        try:
            status, _ = request("GET", "/")
            if status == 200:
                return
        except Exception:
            time.sleep(0.25)
    raise SmokeFailure("uvicorn did not become ready in time")


def expect_status(method: str, path: str, expected: int, label: str, token: str | None = None, payload: dict | None = None):
    status, _ = request(method, path, token=token, payload=payload)
    expect(status == expected, f"{label} expected {expected}, got {status}")


def expect_blocked(method: str, path: str, label: str, token: str | None = None, payload: dict | None = None):
    expect_status(method, path, 403, label, token=token, payload=payload)


def expect_not_auth_blocked(method: str, path: str, label: str, token: str, payload: dict | None = None):
    status, _ = request(method, path, token=token, payload=payload)
    expect(status != 403, f"{label} unexpectedly hit auth block")


def main() -> int:
    expect(VENV_PYTHON.exists(), f"venv python not found: {VENV_PYTHON}")

    env = os.environ.copy()
    env["ADMIN_ROUTE_TOKEN"] = TOKEN

    stderr_path = Path(os.environ.get("TEMP", str(PROJECT_ROOT / "tmp"))) / "pristolov_route_protection_uvicorn.stderr.log"
    stdout_path = Path(os.environ.get("TEMP", str(PROJECT_ROOT / "tmp"))) / "pristolov_route_protection_uvicorn.stdout.log"
    with stdout_path.open("w", encoding="utf-8") as stdout_file, stderr_path.open("w", encoding="utf-8") as stderr_file:
        process = subprocess.Popen(
            [
                str(VENV_PYTHON),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                HOST,
                "--port",
                str(PORT),
                "--log-level",
                "warning",
            ],
            cwd=PROJECT_ROOT,
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
        )

        try:
            wait_for_server(process, stderr_path)

            expect_status("GET", "/", 200, "public /")
            expect_status("GET", "/delegation/start", 200, "public /delegation/start")

            expect_blocked("GET", "/dev/master-screen/LIVE01", "GET /dev/master-screen/LIVE01 without token")
            expect_blocked("GET", "/dev/master-screen/LIVE01", "GET /dev/master-screen/LIVE01 with wrong token", token=WRONG_TOKEN)
            expect_not_auth_blocked("GET", "/dev/master-screen/LIVE01", "GET /dev/master-screen/LIVE01 with correct token", token=TOKEN)

            expect_blocked("GET", "/dev/game-master/LIVE01/state", "GET /dev/game-master/LIVE01/state without token")
            expect_not_auth_blocked("GET", "/dev/game-master/LIVE01/state", "GET /dev/game-master/LIVE01/state with correct token", token=TOKEN)

            expect_blocked("POST", "/dev/games/LIVE01/reset-runtime", "POST /dev/games/LIVE01/reset-runtime without token")

            expect_blocked("GET", "/dev/reset-delegations/LIVE01", "GET /dev/reset-delegations/LIVE01 without token")
            expect_not_auth_blocked("GET", "/dev/reset-delegations/LIVE01", "GET /dev/reset-delegations/LIVE01 with correct token", token=TOKEN)

            expect_blocked(
                "GET",
                "/gold/houses/999999999/transactions",
                "GET /gold/houses/999999999/transactions without token",
            )
            expect_blocked(
                "GET",
                "/gold/houses/999999999/transactions",
                "GET /gold/houses/999999999/transactions with wrong token",
                token=WRONG_TOKEN,
            )
            expect_not_auth_blocked(
                "GET",
                "/gold/houses/999999999/transactions",
                "GET /gold/houses/999999999/transactions with correct token",
                token=TOKEN,
            )

        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print("ROUTE PROTECTION SMOKE: PASS")
    print("protected_prefixes=/dev,/gold")
    print("public_routes_checked=/,/delegation/start")
    print("token_source=temporary smoke subprocess environment")
    print("runtime_mode=temporary uvicorn subprocess")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SmokeFailure as exc:
        print(f"ROUTE PROTECTION SMOKE: FAIL - {exc}", file=sys.stderr)
        raise SystemExit(1)
