# Full Scenario Combined Load Probe Plan

Date: 2026-06-24

## 1) Current Proven Result

Player polling optimization is validated for the current V1 individual-phone direction.

Production/player endpoint result after `4604611`:

| Load | Result |
|---|---|
| 25 player clients | `errors=0`, `p95=30.5 ms` |
| 40 player clients | `errors=0`, `p95=38.0 ms` |
| 100 player clients | `errors=0`, `p95=221.2 ms`, `p99=284.0 ms`, `max=362.3 ms` |

Validated endpoints:

- `/player/me/{player_token}`
- `/player/me/{player_token}/assignments`

Journal after probe had no known critical failure markers:

- no `Traceback`
- no `ERROR`
- no `sqlite locked`
- no timeout

## 2) What Remains Unproven

The successful player probe did not cover the full live operational surface:

- Master Screen polling
- TV Screen polling
- cashier Gold Desk
- Harchevnya / Treasurer Shop queue and confirmation surface
- phase transitions
- Expedition actions
- Diplomacy actions
- Duel actions
- Court flow
- Last Whisper actions
- Final flow
- active gameplay writes under simultaneous player polling load
- long-duration soak behavior
- multi-room or multi-city operation

## 3) Risk Model

The next likely risks are no longer simple player read polling failures. The remaining risk is mixed read/write pressure while operational screens keep polling.

High-risk areas:

- single process / worker throughput during simultaneous reads and writes
- DB transaction contention during active gameplay actions
- route handlers that rebuild room-wide state repeatedly
- Master/TV state endpoints under load
- cashier/shop confirmation writes during active polling
- phase transition endpoints that may trigger broad state recomputation
- network/browser instability during longer sessions

## 4) Required Fixtures

Use a disposable or explicitly approved role-complete room for Level 2 and Level 3.

Required fixture contents:

- room code
- at least 2 Houses
- ideally role-complete setup:
  - lord/lady
  - gold role
  - diplomat
  - whisper role
  - maester/support roles
- valid player tokens for all players
- cashier-protected access path if testing cashier endpoints
- active scenario/phase state suitable for transitions
- enough gold/resources for controlled action tests
- no real live guests in the room unless explicitly approved

Do not run mutating Level 2 or Level 3 probes on a real live room without explicit approval.

## 5) Required Tokens And Screens

Required player paths:

- `/player/me/{player_token}`
- `/player/me/{player_token}/assignments`

Required operator/read paths:

- `/dev/game-master/{room_code}/state`
- `/dev/game-master/{room_code}/tv-state`
- `/cashier/gold-desk/{room_code}` when protected access is configured for the probe environment
- `/dev/treasurer-shop/{room_code}` only in an internal/operator context

Required action endpoints depend on Level 3 scope and must be collected from the current routes before implementation.

## 6) Level 1: Combined Passive Polling

Goal: prove that all passive live screens can poll together without gameplay writes.

Load shape:

- 100 player polling clients
- Master state polling
- TV state polling
- cashier page polling if safe
- optional internal shop/operator page polling if safe
- duration: 5-10 minutes
- no phase transitions
- no gameplay writes

Metrics:

- `errors_total`
- `status_counts`
- `p50`
- `p95`
- `p99`
- `max`
- nginx 5xx count
- app journal failure markers

Suggested thresholds:

- GO: `errors_total=0`, no 5xx, player `p95 < 300 ms`, operator screen `p95 < 500 ms`
- Conditional GO: rare non-5xx transient errors or p95 spike that recovers, no journal failures
- No-Go: 5xx, timeouts, locked DB, Traceback, sustained p95 > 1000 ms, or frozen operational screens

## 7) Level 2: Scenario Phase Transition Probe

Goal: prove polling stability while the host advances phases and the UI state changes.

Load shape:

- same polling load as Level 1
- controlled Master/operator phase transitions
- no destructive resets
- no broad gameplay action spam

Transitions to cover if available in the test room:

- opening/current baseline phase
- map/expedition phase
- diplomacy phase
- duel phase
- Court phase
- Last Whisper phase
- Final/show phase

Validation:

- player endpoints continue returning 200
- Master state continues returning 200
- TV state continues returning 200
- cashier remains reachable
- no stale/frozen endpoint symptoms
- journal remains clean

This level should run on a disposable room or a room explicitly approved for test transitions.

## 8) Level 3: Active Gameplay Action Probe

Goal: prove that gameplay writes remain safe while 100 players and operator screens poll.

This must use a disposable/test room unless explicitly approved.

Candidate scripted actions:

- Expedition selection / finish if a disposable room has map state
- Diplomacy deal creation / acceptance if safe
- Duel challenge / resolve if safe
- Harchevnya request / cashier confirmation if safe
- Last Whisper action if phase and roles are configured
- Court action only if isolated from real live state
- Final action only if isolated from real live state

Action rules:

- one controlled action at a time
- record before/after state
- verify expected 200/ok response
- verify no unexpected side effects outside the test room
- verify journal after each batch

Suggested thresholds:

- GO: action success, polling remains under Level 1 thresholds, no journal errors
- Conditional GO: action succeeds but creates latency spike that recovers quickly
- No-Go: action failure under load, 5xx, DB lock, timeout, stuck phase, or wrong state mutation

## 9) Metrics To Capture

For each level:

- room code
- deployed git HEAD
- app service status
- duration
- client counts
- path counts
- requests total
- `errors_total`
- `status_counts`
- `p50`
- `p95`
- `p99`
- `max`
- nginx 5xx summary
- journalctl failure marker summary
- DB lock/timeout summary

## 10) Go / No-Go Summary

GO:

- Level 1 green at 100 players plus operational screens
- Level 2 green for controlled transitions
- Level 3 green for selected safe actions in disposable room
- no Traceback, no DB lock, no nginx 5xx cluster

Conditional GO:

- Level 1 green, Level 2 partially covered, Level 3 deferred
- acceptable for live if gameplay actions are manually controlled and there is an operator fallback

No-Go:

- player polling regresses above target
- Master/TV/cashier endpoints fail under mixed passive load
- phase transition causes endpoint timeouts
- active writes produce DB locks or stuck state

## 11) Recommended Next Implementation Task

Create a combined load probe helper that extends current tooling without touching gameplay runtime.

Suggested output:

- `scripts/load_probe_combined_screens.py`

Scope:

- Level 1 first
- read-only/passive only
- reuse `load_probe_player_screens.py` where possible
- require explicit `--room-code`
- default to `http://127.0.0.1:8000`
- collect player paths via existing helper/query pattern
- add Master/TV/cashier paths as configured
- print p50/p95/p99/status/errors
- print exact journalctl/nginx commands to run separately

After Level 1 tooling is green, decide whether Level 2 and Level 3 should become separate scripts or manual controlled protocols.

## 12) Level 1 Helper Added

Implemented helper:

- `scripts/load_probe_combined_screens.py`

Scope:

- read-only Level 1 combined passive polling;
- resolves real room player tokens through `Player.game_id` -> `Game.room_code`;
- probes player paths and operational state paths in parallel subprocesses;
- includes Master state and TV state by default;
- can include cashier Gold Desk GET page with `--include-cashier`;
- reads admin token only from env var (`ADMIN_ROUTE_TOKEN` by default);
- refuses non-localhost base URLs unless `--allow-production` is provided.

Recommended first production command after deployment:

```bash
cd /opt/pristolov/app
export ADMIN_ROUTE_TOKEN="$(grep '^ADMIN_ROUTE_TOKEN=' /etc/pristolov/pristolov.env | cut -d= -f2-)"
python scripts/load_probe_combined_screens.py --room-code LIVE01 --base-url http://127.0.0.1:8000 --duration 300 --player-clients 100 --screen-clients 1 --include-cashier
```

Run journal/nginx checks printed by the helper after the probe.
