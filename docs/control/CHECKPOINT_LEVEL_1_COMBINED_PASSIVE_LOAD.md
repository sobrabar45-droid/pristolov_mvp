Date: 2026-06-24

## 1. Background

After player polling optimization and helper rollout, we needed one more safety gate for V1 individual-phone capacity at scale.

Goal:

- verify combined passive load for real LIVE01 endpoints
- include player polling + Master + TV + cashier read screens
- confirm behavior under 100 player clients for 5 minutes
- confirm no critical runtime errors in logs

This task had a hard constraint: only passive reads, no gameplay mutations, no phase changes.

## 2. What was tested

Level 1 combined passive load probe run on production VPS using:

- commit: `1edfb1c`
- commit context from previous patches:
  - `b840b0e`
  - `967a646`
  - `4604611`
- `compileall` on VPS: OK
- service status: active
- room: `LIVE01`
- base URL: `http://127.0.0.1:8000`
- `script`: `scripts/load_probe_combined_screens.py`
- `room-code`: `LIVE01`
- `duration`: `300` seconds
- `player-clients`: `100`
- `screen-clients`: `1`
- `include-cashier`: enabled

## 3. Production data snapshot before probe

- players_found: `22`
- tokens_found: `22`
- player_paths_written: `44`
- operational_paths_count: `3`
- admin_token: `SET`

## 4. Probe methodology

- Resolve real players for room code through `Player.game_id -> Game.room_code`
- Generate player paths:
  - `/player/me/{token}`
  - `/player/me/{token}/assignments`
- Generate operational paths:
  - `/dev/game-master/{room_code}/state`
  - `/dev/game-master/{room_code}/tv-state`
  - `/cashier/gold-desk/{room_code}` (optional, enabled by flag)
- Run concurrent polling via shared helper process for each path set
- Collect:
  - `requests_total`
  - `errors_total`
  - `status_counts`
  - `p50`, `p95`, `p99`, `max`
  - journal check (`Traceback`, `ERROR`, `Exception`, `sqlite locked`, `timeout`)
  - nginx 5xx / upstream errors

## 5. Results: Player screens (10 minutes equivalent per script run parameters: 300 sec)

| Metric | Value |
|---|---:|
| requests_total | `27435` |
| errors_total | `0` |
| status_counts | `200: 27435` |
| p50 | `72.4 ms` |
| p95 | `241.7 ms` |
| p99 | `311.1 ms` |
| max | `525.9 ms` |

## 6. Results: Operational screens

| Metric | Value |
|---|---:|
| requests_total | `259` |
| errors_total | `0` |
| status_counts | `200: 259` |
| p50 | `116.7 ms` |
| p95 | `374.0 ms` |
| p99 | `471.2 ms` |
| max | `686.9 ms` |

## 7. Journal check result

- no `Traceback`
- no `ERROR`
- no `Exception`
- no `sqlite locked`
- no `timeout`

## 8. Nginx 502 follow-up

One event was observed:

- `502` on `GET /dev/games/LIVE01/scenario/director`
- time matched service restart in app logs:
  - `Stopping PRISTOLOV Core FastAPI`
  - `Shutting down`
  - `Started PRISTOLOV Core FastAPI`

Interpretation:

- this `502` came from upstream restart window (`connect() failed (111) while connecting to upstream`)
- it is consistent with service restart timing
- not a sustained probe or load failure

## 9. What was not tested

Level 1 does **not** prove full gameplay behavior under load:

- phase transitions
- active gameplay writes
- Expedition path under mixed load
- Diplomacy flow under mixed load
- Duel flow under mixed load
- Harchevnya actions under mixed load
- Court flow under mixed load
- Last Whisper under mixed load
- Final flow under mixed load
- long-duration soak beyond 5 minutes
- multi-room or multi-city operation

## 10. Conclusion

Level 1 combined passive load is **green** for V1 current direction.

- 100 players + Master + TV + cashier passive screens over 300s: all requests returned `200`
- `errors_total = 0` for player and operational paths
- no runtime-critical log markers in journal check
- supports continuing with current individual-phone model for V1 without introducing blocking architecture changes

The current stability target is met for passive combined load; remaining work is to move to Level 2/3 operational proof for active game behavior.

## 11. Recommended next contour

Recommended next contour:

- if a safe disposable/test room exists and live event timing requires higher confidence: run Level 2 controlled phase-transition probe
- if no immediate complex live load is scheduled now: pause technical contour and return to product P0 tasks (announcements, expedition UX, question timer/reveal, duel tie handling), then re-open combined load when needed

## 12. Why this still matters now

- The original freeze/reconnect issue is no longer supported by evidence in this mixed-screen passive case.
- The remaining risk is not polling read stability itself, but the interaction with stateful phase changes and active writes.
