# Post-Rehearsal Technical Stability and Scalability Audit

Date: 2026-06-23

## 1. Incident summary

During live rehearsal, about 21 simultaneous player phones were enough for player screens to start dropping, freezing, or hanging. Refreshing helped briefly, but the instability returned. Switching between VPN/no VPN, browsers, Sobranie Wi-Fi, and mobile internet gave inconsistent partial improvements.

Operationally this is a game-tempo blocker: the host had to troubleshoot phones at tables instead of running the room.

## 2. Product decision

V1 keeps individual player phones and role screens. The system should not switch to one shared tablet per House now. One tablet per House remains only a V2 hypothesis.

The technical target is stable individual-phone operation:

- Reproduction threshold: 25-40 simultaneous clients.
- Required single-room target: at least 100 simultaneous player clients for one room.
- Operational screens are additional: Master, TV, cashier, Treasurer Shop/operator, dev/operator.
- Future architecture target: multiple simultaneous games in different rooms/cities.

## 3. What is known

- Player room has automatic polling:
  - `GET /player/me/{player_token}` every 5 seconds.
  - `GET /player/me/{player_token}/assignments` every 3 seconds.
- Both player polling endpoints call `_touch_last_seen(player)`.
- `GET /player/me/{player_token}` commits and refreshes the player on every poll.
- `GET /player/me/{player_token}/assignments` also commits on every poll.
- Master screen polls `GET /dev/game-master/{room_code}/state` every 5 seconds.
- TV mode polls `GET /dev/game-master/{room_code}/tv-state` every 10 seconds and may fetch `GET /dev/host-rounds/{activeRound.id}/debug`.
- Cashier Gold Desk is mostly action-driven; it does not appear to have continuous auto-polling, but it reloads after confirming a shop request.
- Treasurer Shop operator page loads `GET /dev/game-master/{room_code}/state` on page load and after purchases.
- Deployment docs describe a conservative production shape: Uvicorn on `127.0.0.1:8000`, `--workers 1`, no reload, behind nginx/systemd.
- The app uses SQLAlchemy `create_engine(settings.DATABASE_URL)` without app-level pool tuning in `app/database.py`.

## 4. What is unknown

- Actual production database engine from `DATABASE_URL` for the failed rehearsal.
- Whether production was running with one worker, reload mode, or a different process model.
- CPU/RAM/load/disk pressure during the incident.
- App and nginx 4xx/5xx rates during the incident.
- Endpoint latency under 25, 40, 100, and 120 concurrent polling clients.
- Whether freezes were server 5xx/timeout, browser JS errors, stale long requests, mobile network packet loss, or DB write contention.
- Whether protected/operator screens were open multiple times and adding load.

## 5. Hypotheses ranked by likelihood

1. High likelihood: player polling writes too often.
   Evidence: both frequent player GET endpoints update `last_seen_at` and commit. At 100 players this creates steady background DB writes even when nobody acts.

2. High likelihood: single-worker Uvicorn plus synchronous SQLAlchemy route handlers becomes saturated.
   Evidence: production docs prescribe `--workers 1`; route handlers are synchronous and rebuild JSON/template state per request.

3. High likelihood if SQLite was used: DB lock contention from write-heavy heartbeat polling.
   Evidence: deployment readiness docs already flagged SQLite with uncontrolled public concurrency as a no-go risk.

4. Medium likelihood: player state payload is too broad for high-frequency polling.
   Evidence: `/player/me/{token}` loads active phases, active host round, assignment count, expedition, incoming deals, available deal/duel houses, treasurer deals, alliances, crest blocks, duels, whisper feed, and last-whisper state.

5. Medium likelihood: Master/TV full-state rebuild adds periodic heavy reads.
   Evidence: Master/TV state functions rebuild house, player, host-round, question, deal, event, director, and court data on each poll.

6. Medium likelihood: network/Wi-Fi amplified the server problem.
   Evidence: Wi-Fi/mobile/VPN changes gave inconsistent results. This suggests network variance existed, but not as the only cause.

7. Medium likelihood: client-side JS failures under stale/partial responses.
   Evidence: user saw freezing/hanging; audit has not yet captured browser console logs from the incident.

8. Lower likelihood as sole cause: VPS raw capacity.
   Evidence: possible, but should be proven with CPU/RAM/load/log data before upgrading blindly.

## 6. Frequent endpoint and polling map

| Surface | Endpoint(s) | Frequency | Writes? | Notes |
| --- | --- | ---: | --- | --- |
| Player room | `/player/me/{player_token}` | every 5s | yes, `last_seen_at` commit | Broad state payload; high-risk at 100+ clients. |
| Player assignments | `/player/me/{player_token}/assignments` | every 3s | yes, `last_seen_at` commit | More frequent than main state; likely hottest endpoint. |
| Master screen | `/dev/game-master/{room_code}/state` | every 5s | expected read-only | Large room-wide payload; also triggers other JS fetches in load flow. |
| Master screen | `/dev/host-rounds/{id}/debug`, round/director config endpoints | on load/state flow | read | Adds operator overhead. |
| TV mode | `/dev/game-master/{room_code}/tv-state` | every 10s | expected read-only | Large public display payload. |
| TV mode | `/dev/host-rounds/{activeRound.id}/debug` | during active round | read | Extra request after TV state. |
| Cashier | `/cashier/gold-desk/{room_code}` | manual/open | read | No continuous polling found. |
| Cashier actions | `/gold/houses/{id}/grant`, `/grant-from-check`, `/cashier/treasurer-shop/requests/{id}/confirm` | on click | write | Operational writes, not background load. |
| Treasurer Shop operator | `/dev/game-master/{room_code}/state` | page load / after purchase | read | Not continuous by default. |

## 7. Expected request-load estimate

Player-only background polling:

| Clients | `/assignments` at 3s | `/me` at 5s | Player total |
| ---: | ---: | ---: | ---: |
| 25 | 8.3 rps | 5.0 rps | 13.3 rps |
| 40 | 13.3 rps | 8.0 rps | 21.3 rps |
| 100 | 33.3 rps | 20.0 rps | 53.3 rps |
| 120 | 40.0 rps | 24.0 rps | 64.0 rps |

Operational screens add a small request count but larger payloads:

- Master: about 0.2 rps for `/state`, plus extra config/debug calls.
- TV: about 0.1 rps for `/tv-state`, plus possible debug call.
- Cashier/Treasurer/operator: mostly click-driven.

The request count alone is not huge for a tuned stack, but it is risky when most player polls create DB writes and a single worker handles synchronous route logic.

## 8. Potential server capacity risks

- Single worker can queue all slow requests behind one busy process.
- Uvicorn worker count, reload mode, and process memory are unverified for the incident.
- Nginx timeout/proxy buffering settings are unverified.
- CPU steal/load/disk I/O are unverified.
- If DB is local SQLite, file locks and disk writes can become visible quickly.

## 9. Potential application bottlenecks

- GET polling writes `last_seen_at` too frequently.
- Main player state endpoint returns broad role/game/deal/duel/expedition/whisper payload.
- Assignments endpoint loads all assignments for the player, then filters in Python.
- Master/TV state builders rebuild room-wide data every poll.
- Master screen load flow can call additional state/config/debug endpoints.
- No visible client-side backoff, jitter, stale-response protection, or “offline but keep last screen” mode in player polling.
- Polling intervals are synchronized by page load patterns; many players scanning links at once can create bursts.

## 10. Potential database bottlenecks

- Background polling creates write transactions.
- SQLite would be especially sensitive to concurrent writes.
- SQLAlchemy engine uses default settings; no app-level pool sizing or timeout policy was found.
- Several state builders use multiple ORM queries and then Python-side grouping/filtering.
- Master/TV full-state queries are read-heavy; player polling is write-heavy; together they can compete.

## 11. Potential network/client risks

- Venue Wi-Fi and mobile networks may add packet loss and high latency.
- Phones may suspend background JS or throttle timers when screen locks or tab loses focus.
- VPN may route differently and change latency.
- Browser fetch failures are logged only to console; players/host do not get a stable degraded-mode screen.
- Current player screen has no visible server-lag indicator or automatic slow-mode fallback.

## 12. Safe VPS diagnostic command block

Run manually on the VPS. This is read-only: no restart, no config edit, no reset, no secret printing.

```bash
set -e
echo "== time/head/status =="
date -Is
cd /opt/pristolov/app
git rev-parse --short HEAD
git status --short | wc -l

echo "== service =="
systemctl is-active pristolov.service || true
systemctl status pristolov.service --no-pager | sed -n '1,18p'

echo "== compile =="
python -m compileall app -q && echo "compile=OK"

echo "== system resources =="
uptime
free -h
df -h /
ps -eo pid,ppid,cmd,%cpu,%mem --sort=-%cpu | head -20

echo "== listening ports/process model =="
ss -lntp | grep -E ':80|:443|:8000' || true
pgrep -af 'uvicorn|gunicorn|python.*app.main' || true

echo "== app logs recent errors =="
journalctl -u pristolov.service -n 250 --no-pager | grep -Ei 'Traceback|ERROR|Exception|sqlite|locked|timeout|too many|worker|killed' || true

echo "== nginx recent errors =="
tail -n 200 /var/log/nginx/error.log | grep -Ei 'error|upstream|timeout|connect|refused|502|504' || true

echo "== nginx recent status sample =="
tail -n 500 /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c | sort -nr || true

echo "== protected endpoint latency via upstream =="
TOKEN="$(grep '^ADMIN_ROUTE_TOKEN=' /etc/pristolov/pristolov.env | cut -d= -f2-)"
for path in \
  /health \
  /dev/master-screen/LIVE01 \
  /dev/tv-mode/LIVE01 \
  /cashier/gold-desk/LIVE01 \
  /dev/game-master/LIVE01/state \
  /dev/game-master/LIVE01/tv-state
do
  code_time="$(curl -sS -o /dev/null -w '%{http_code} %{time_total}' -H "X-Admin-Token: ${TOKEN}" "http://127.0.0.1:8000${path}" || true)"
  echo "$path $code_time"
done

echo "== env presence, redacted =="
test -f /etc/pristolov/pristolov.env && echo "env_file=present" || echo "env_file=missing"
grep -E '^(ADMIN_ROUTE_TOKEN|DATABASE_URL)=' /etc/pristolov/pristolov.env | sed 's#=.*#=SET#' || true
```

Paste back only the command output. Do not paste token values.

## 13. Load-test plan

Stage 1: local/staging only.

- Use `scripts/load_probe_player_screens.py`.
- Start with `--clients 5`, then 25, 40.
- Use a local/staging base URL first.
- Prefer real player screen polling paths from a disposable room or known test tokens.
- Record p50/p95/p99, status-code distribution, and error count.

Stage 2: controlled production only after explicit approval.

- Run against `http://127.0.0.1:8000` on VPS, not public internet first.
- Use read-only polling GETs.
- Run 25-40 clients to reproduce rehearsal threshold.
- Then run 100-120 clients for the single-room target.
- Watch `journalctl`, nginx logs, CPU/RAM, and DB locked/timeouts.

Stage 3: future multi-room target.

- Repeat with multiple room/player-token sets.
- Target multiple simultaneous room groups only after single-room 100+ is stable.

## 14. Recommended next step

Do not upgrade the VPS blindly. Collect production evidence first, then run controlled load probes.

Recommended sequence:

1. Run the VPS diagnostic command block manually.
2. Run local/staging load probe at 25, 40, 100, 120 clients.
3. If the same symptoms reproduce, prioritize:
   - remove DB writes from frequent GET polling or throttle `last_seen_at`;
   - add client polling jitter/backoff;
   - split assignment polling from full player state or lower frequency;
   - measure and optimize `/player/me/{token}` query payload;
   - review DB engine and concurrency model;
   - review Uvicorn worker model after DB write safety is understood.
4. Only then decide whether the fix is polling optimization, worker/process change, DB move/tuning, server upgrade, or client degraded-mode UX.

## 15. Go / no-go for next game

- No-Go for 100+ individual phones until production diagnostics and 40-client reproduction load probe are green.
- Conditional Go for smaller rehearsal only if the room has an operational fallback and the host is not expected to troubleshoot phones during play.
- Go for the 100+ target only after 100-120 client load probe stays within acceptable latency and error thresholds.
