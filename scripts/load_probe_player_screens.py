"""Safe polling load probe for PRISTOLOV player/operator screens.

This script only sends HTTP requests to paths supplied by the operator. It does
not create players, houses, deals, or database rows by itself.
"""

from __future__ import annotations

import argparse
import os
import random
import statistics
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"


@dataclass
class Sample:
    status: int | None
    latency_ms: float
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a safe read-only HTTP polling probe against PRISTOLOV screens.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL to probe. Defaults to {DEFAULT_BASE_URL}.",
    )
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Path to poll, e.g. /health. Can be provided multiple times.",
    )
    parser.add_argument(
        "--paths-file",
        help="UTF-8 file with one path per line. Empty lines and # comments are ignored.",
    )
    parser.add_argument("--clients", type=int, default=10, help="Concurrent simulated clients.")
    parser.add_argument("--duration", type=float, default=30.0, help="Probe duration in seconds.")
    parser.add_argument("--interval", type=float, default=5.0, help="Seconds between requests per client.")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    parser.add_argument(
        "--jitter",
        type=float,
        default=0.2,
        help="Random per-client interval jitter fraction, e.g. 0.2 means +/-20%%.",
    )
    parser.add_argument(
        "--admin-token-env",
        default="",
        help="Optional env var name containing X-Admin-Token. Value is never printed.",
    )
    parser.add_argument(
        "--allow-production",
        action="store_true",
        help="Required when base URL host is not localhost/127.0.0.1.",
    )
    return parser.parse_args()


def read_paths(args: argparse.Namespace) -> list[str]:
    paths: list[str] = list(args.path or [])
    if args.paths_file:
        with open(args.paths_file, "r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    paths.append(stripped)
    if not paths:
        paths = ["/health"]
    normalized = []
    for path in paths:
        if not path.startswith("/"):
            raise SystemExit(f"path must start with '/': {path}")
        normalized.append(path)
    return normalized


def assert_safe_base_url(base_url: str, allow_production: bool) -> None:
    parsed = urlparse(base_url)
    host = (parsed.hostname or "").lower()
    if host not in {"127.0.0.1", "localhost"} and not allow_production:
        raise SystemExit(
            "Refusing non-localhost probe without --allow-production. "
            "Use this only after explicit approval."
        )


def request_once(base_url: str, path: str, timeout: float, admin_token: str | None) -> Sample:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    headers = {"User-Agent": "pristolov-load-probe/1.0"}
    if admin_token:
        headers["X-Admin-Token"] = admin_token
    request = Request(url, headers=headers, method="GET")
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            response.read()
            status = int(response.status)
            error = None
    except HTTPError as exc:
        exc.read()
        status = int(exc.code)
        error = f"HTTP {exc.code}"
    except URLError as exc:
        status = None
        error = str(exc.reason)
    except Exception as exc:  # noqa: BLE001 - probe should report unexpected transport failures.
        status = None
        error = type(exc).__name__
    latency_ms = (time.perf_counter() - started) * 1000.0
    return Sample(status=status, latency_ms=latency_ms, error=error)


def client_loop(
    client_id: int,
    base_url: str,
    paths: list[str],
    duration: float,
    interval: float,
    timeout: float,
    jitter: float,
    admin_token: str | None,
) -> list[Sample]:
    deadline = time.monotonic() + duration
    samples: list[Sample] = []
    path_index = client_id % len(paths)
    time.sleep(random.uniform(0, min(interval, 1.0)))
    while time.monotonic() < deadline:
        path = paths[path_index % len(paths)]
        path_index += 1
        samples.append(request_once(base_url, path, timeout, admin_token))
        jitter_factor = 1.0 + random.uniform(-jitter, jitter)
        time.sleep(max(0.05, interval * jitter_factor))
    return samples


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[index]


def summarize(samples: Iterable[Sample]) -> int:
    sample_list = list(samples)
    latencies = [sample.latency_ms for sample in sample_list]
    status_counts: dict[str, int] = {}
    error_count = 0
    for sample in sample_list:
        key = str(sample.status) if sample.status is not None else "transport_error"
        status_counts[key] = status_counts.get(key, 0) + 1
        if sample.error and (sample.status is None or sample.status >= 400):
            error_count += 1

    print(f"requests_total={len(sample_list)}")
    print(f"errors_total={error_count}")
    print("status_counts=" + ",".join(f"{key}:{status_counts[key]}" for key in sorted(status_counts)))
    if latencies:
        print(f"latency_min_ms={min(latencies):.1f}")
        print(f"latency_p50_ms={statistics.median(latencies):.1f}")
        print(f"latency_p95_ms={percentile(latencies, 95):.1f}")
        print(f"latency_p99_ms={percentile(latencies, 99):.1f}")
        print(f"latency_max_ms={max(latencies):.1f}")
    return 0 if error_count == 0 else 1


def main() -> int:
    args = parse_args()
    assert_safe_base_url(args.base_url, args.allow_production)
    if args.clients <= 0:
        raise SystemExit("--clients must be greater than 0")
    if args.duration <= 0:
        raise SystemExit("--duration must be greater than 0")
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than 0")

    paths = read_paths(args)
    admin_token = os.environ.get(args.admin_token_env, "") if args.admin_token_env else ""
    admin_token = admin_token or None

    print(f"base_url={args.base_url}")
    print(f"clients={args.clients}")
    print(f"duration_sec={args.duration}")
    print(f"interval_sec={args.interval}")
    print(f"paths_count={len(paths)}")
    print(f"admin_token={'SET' if admin_token else 'not_set'}")

    all_samples: list[Sample] = []
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=args.clients) as executor:
        futures = [
            executor.submit(
                client_loop,
                client_id,
                args.base_url,
                paths,
                args.duration,
                args.interval,
                args.timeout,
                args.jitter,
                admin_token,
            )
            for client_id in range(args.clients)
        ]
        for future in as_completed(futures):
            with lock:
                all_samples.extend(future.result())

    return summarize(all_samples)


if __name__ == "__main__":
    sys.exit(main())
