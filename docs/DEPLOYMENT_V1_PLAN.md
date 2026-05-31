# Deployment V1 Implementation Plan

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-06-01  
Status: implementation plan only; no deploy and no runtime code changes.

## Purpose

This plan turns `docs/DEPLOYMENT_READINESS_AUDIT.md` into a concrete safe path for public VPS deployment of PRISTOLOV_CORE V1.

The goal is to make the game reachable from normal mobile internet while keeping operator, debug, reset, and economy-control routes protected.

## Source Context

Primary source:

- `e3036a3 Add deployment readiness audit`
- `docs/DEPLOYMENT_READINESS_AUDIT.md`

Supporting sources:

- `app/main.py`
- `app/config.py`
- `app/database.py`
- `requirements.txt`
- `app/routes/dev.py`
- `app/routes/gold.py`
- `app/routes/player.py`
- `app/routes/delegation.py`
- `app/routes/join.py`
- `scripts/start_dev_server.ps1`
- `docs/CHECKPOINT_RUNTIME_VALIDATED.md`
- `docs/PRISTOLOV_CORE_V1_FREEZE.md`

## 1. Target Architecture

Recommended V1 architecture:

```text
Public internet
  |
  | HTTPS
  v
Nginx or Caddy reverse proxy
  |
  | localhost only
  v
Uvicorn app, 1 worker, bound to 127.0.0.1:8000
  |
  v
PostgreSQL database
```

Required properties:

- public access goes through HTTPS only;
- Uvicorn is not directly exposed to the internet;
- Uvicorn binds to `127.0.0.1:8000`;
- `/dev/*` is protected before public launch;
- `/gold/*` is protected before public launch;
- player routes remain public;
- PostgreSQL is used for the public live game;
- one Uvicorn worker is used for V1 to reduce race-condition exposure;
- `scripts/start_dev_server.ps1` remains local-only and is not used as production supervisor.

## 2. VPS Requirements

Minimum recommended VPS:

| Requirement | Recommendation |
|---|---|
| OS | Ubuntu/Debian LTS |
| CPU | 2 vCPU minimum |
| RAM | 2 GB minimum, 4 GB safer |
| Disk | 20 GB minimum, SSD |
| Network | Public IPv4, stable outbound package access |
| Firewall | `22`, `80`, `443` only |
| User | dedicated non-root app user |
| Process manager | `systemd` |
| Reverse proxy | Nginx or Caddy |
| TLS | Let's Encrypt or provider-managed TLS |
| Database | local PostgreSQL or managed PostgreSQL |

Operational requirement:

- SSH key access must be configured before deployment.
- Password SSH login should be disabled if possible.
- Server time should be correct through NTP.
- Backups must be tested before real players join.

## 3. PostgreSQL Setup Requirements

PostgreSQL is the recommended V1 database.

Requirements:

- create a dedicated database, for example `pristolov_v1`;
- create a dedicated database user with password auth;
- grant only required privileges to that user;
- store the connection string outside git;
- confirm app startup can create/ensure schema;
- create a pre-game backup before live play;
- create a post-game backup immediately after live play.

Recommended connection shape:

```text
DATABASE_URL=postgresql+psycopg2://pristolov_app:<password>@127.0.0.1:5432/pristolov_v1
```

Current app behavior:

- `app/config.py` requires `DATABASE_URL`.
- `app/database.py` creates SQLAlchemy engine from `DATABASE_URL`.
- `app/main.py` runs `Base.metadata.create_all(bind=engine)` and several explicit schema ensure helpers on startup.
- There is no migration runner in the deployment path.

Deployment implication:

- first production startup should be done deliberately and observed in logs;
- schema changes should not be introduced during live play;
- DB backup/restore is the primary rollback safety net.

## 4. Environment Variables

Runtime-required:

| Variable | Required | Purpose |
|---|---:|---|
| `DATABASE_URL` | yes | SQLAlchemy database connection string |
| `ADMIN_ROUTE_TOKEN` | yes for public VPS | app-level guard token for `/dev/*` and `/gold/*` |

Currently observed in local `.env` keys:

| Variable | Runtime status | Deployment note |
|---|---|---|
| `APP_NAME` | not required by current app config | optional operator convention |
| `APP_HOST` | not required by current app config | systemd/proxy config should define host separately |
| `APP_PORT` | not required by current app config | systemd/proxy config should define port separately |
| `DEBUG` | not required by current app config | do not rely on it for production safety |
| `DATABASE_URL` | required | must be set |
| `SECRET_KEY` | not required by current app config | reserve for future auth/session work |
| `ADMIN_ROUTE_TOKEN` | required for public VPS | must be set before exposing `/dev/*` or `/gold/*` |

Recommended production env file:

```text
DATABASE_URL=postgresql+psycopg2://pristolov_app:<password>@127.0.0.1:5432/pristolov_v1
ADMIN_ROUTE_TOKEN=<long-random-secret>
```

Do not commit production env files.

If `ADMIN_ROUTE_TOKEN` is empty, `/dev/*` and `/gold/*` remain open for local/dev compatibility. Public VPS deployment without `ADMIN_ROUTE_TOKEN` is a no-go.

## 5. Reverse Proxy / HTTPS Requirements

Reverse proxy must do four jobs:

1. terminate TLS;
2. forward public player routes to Uvicorn;
3. protect `/dev/*`;
4. protect `/gold/*`.

Required headers:

```text
Host
X-Forwarded-Proto
X-Forwarded-For
X-Real-IP
```

Reason:

- QR/invite generation in `delegation.py` uses `request.base_url`.
- If proxy headers are wrong, QR links can point to internal hostnames or `http://127.0.0.1`.

Recommended route policy:

```text
/                  public
/static/*          public
/delegation/*      public or operator-gated by event policy
/house/*           public
/player/*          public, but only by invite/player/token URLs
/health            protected or limited
/dev/*             protected
/gold/*            protected
/game/*            protect or avoid legacy route
/join              protect or avoid legacy route
/player/{id}/role-select  protect or avoid legacy route
```

## 6. Public Routes

Recommended public V1 routes:

| Route | Exposure | Reason |
|---|---|---|
| `/` | public | landing page |
| `/static/*` | public | assets |
| `/static/questions_media/*` | public | question/media assets |
| `/delegation/start` | public or operator-gated | House creation; public only if open onboarding is intended |
| `/delegation/join` | public | invite join flow |
| `/house/{invite_code}` | public | House lobby |
| `/house/{invite_code}/player/{player_id}` | public | production player room |
| `/house/{invite_code}/join-qr.svg` | public | QR for invite |
| `/player/me/{player_token}` | public by token | player state |
| `/player/me/{player_token}/assignments` | public by token | player assignment state |
| `/player/assignments/{assignment_id}/answer` | public with token payload | assignment answer |
| `/player/duels/*` | public by player URL context | V1 Lord/Lady duel actions |
| `/player/expedition/*` | public by player URL context | V1 expedition actions |
| `/player/deals/*` | public by player URL context | V1 deal actions |
| `/player/last-whisper/action/{player_id}` | public by player URL context | V1 Master Whisper action |

Important caveat:

Some player action endpoints are keyed by `player_id` rather than only by token. For a closed event this is acceptable only if URLs are shared narrowly and operator/control routes are protected. This should not be treated as internet-grade authentication.

## 7. Protected Routes

Must be protected before any public VPS launch:

| Route | Exposure | Reason |
|---|---|---|
| `/dev/*` | protected | includes Master UI, TV state, scenario controls, reset, seed, import, debug |
| `/gold/*` | protected | includes manual gold grant/spend/PvP mutation |
| `/health` | protected or limited | exposes DB health; useful for ops but not players |
| `/dev/tv-screen/*` | block or protect | legacy TV route; avoid |
| `/join` | protect or avoid | legacy join flow |
| `/game/{room_code}` | protect or avoid | legacy game flow |
| `/game/{room_code}/join-house` | protect or avoid | legacy House join flow |
| `/player/{player_id}/role-select` | protect or avoid | legacy role select |
| `/game/{room_code}/roster` | protect or avoid | legacy roster |

## 8. Auth Protection Strategy For `/dev` And `/gold`

Recommended V1 strategy:

1. Protect `/dev/*` and `/gold/*` at reverse proxy level.
2. Set `ADMIN_ROUTE_TOKEN` so the FastAPI app also blocks `/dev/*` and `/gold/*`.
3. Forward the protected header only after successful proxy auth:
   - `X-Admin-Token: <token>`
4. Use HTTP Basic Auth for fastest safe V1 deployment.
5. If venue operator IPs are known, add IP allowlist on top of Basic Auth.
6. If available, use VPN/Tailscale for admin access.
7. Keep TV protected unless it must run unauthenticated on a fixed display device.

Recommended split:

| Surface | Protection |
|---|---|
| Master screen | Basic Auth + optional IP allowlist |
| Scenario director | Basic Auth + optional IP allowlist |
| TV mode | Basic Auth, semi-protected display-only browser, or IP allowlist |
| Dev JSON state | Basic Auth |
| Reset/seed/import/debug | Basic Auth + strongest restriction available |
| Gold mutation routes | Basic Auth + strongest restriction available |

No-go:

- do not deploy public VPS without `ADMIN_ROUTE_TOKEN`;
- do not expose `/dev/games/{room_code}/reset-runtime`;
- do not expose `/dev/reset-delegations/{room_code}`;
- do not expose `/dev/games/{room_code}/seed-technical-run`;
- do not expose `/gold/houses/{house_id}/grant`;
- do not expose `/gold/houses/{house_id}/spend`.

## 9. Systemd Service Plan

Recommended service shape:

```text
[Unit]
Description=PRISTOLOV_CORE V1
After=network.target postgresql.service

[Service]
User=pristolov
Group=pristolov
WorkingDirectory=/opt/pristolov_mvp
EnvironmentFile=/etc/pristolov/pristolov.env
ExecStart=/opt/pristolov_mvp/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Production rules:

- no `--reload`;
- no direct public bind;
- no multiple workers for V1 unless race-condition risks are separately reviewed;
- logs must be visible through `journalctl`;
- restart must not reset the database;
- deployment must not rely on an interactive terminal.

## 10. Pre-Deploy Local Checklist

Before touching a VPS:

1. Confirm git working tree is clean.
2. Confirm V1 freeze remains current.
3. Confirm no new runtime mechanics are pending.
4. Run local command smoke suite against trusted no-reload runtime:

```powershell
python scripts/smoke_last_whisper_quiet_support.py
python scripts/smoke_last_whisper_crown_tax.py
python scripts/smoke_last_whisper_break_alliance.py
python scripts/smoke_recent_events_contract.py
python scripts/smoke_player_duel_lifecycle.py
python scripts/smoke_assignment_reward_loop.py
python scripts/smoke_scenario_director_advance.py
python scripts/smoke_treasurer_resource_deal.py
python scripts/smoke_expedition_lifecycle.py
python scripts/smoke_court_lifecycle.py
python scripts/smoke_final_terminal_lifecycle.py
python scripts/smoke_visual_runtime_routes.py
```

5. Confirm production domain decision.
6. Confirm room code decision, likely `LIVE01`.
7. Confirm admin protection decision.
8. Confirm database backup policy.
9. Confirm operator has exact Master/TV/Player URLs.
10. Confirm rollback owner and procedure.

## 11. Deploy Checklist

Recommended sequence:

1. Provision VPS.
2. Configure firewall.
3. Create app user.
4. Install system packages:
   - Python;
   - PostgreSQL client/server or managed DB client;
   - Nginx or Caddy;
   - TLS tooling.
5. Clone repository.
6. Checkout intended commit.
7. Create virtual environment.
8. Install `requirements.txt`.
9. Create PostgreSQL database/user.
10. Create production env file with `DATABASE_URL` and `ADMIN_ROUTE_TOKEN`.
11. Start app manually bound to `127.0.0.1:8000` for first schema check.
12. Verify `/health` locally.
13. Install systemd unit.
14. Start service through systemd.
15. Verify `journalctl` has no startup errors.
16. Configure reverse proxy.
17. Configure TLS.
18. Configure Basic Auth/IP rules for `/dev/*` and `/gold/*`.
19. Verify unauthenticated `/dev/*` and `/gold/*` are denied externally.
20. Verify player routes are reachable externally.
21. Run post-deploy smoke suite on VPS.
22. Create pre-game DB backup.
23. Run manual browser validation on real devices.
24. Mark deployment ready only if all no-go checks pass.

## 12. Post-Deploy Smoke Checklist

Run on the VPS host or SSH session against local `127.0.0.1:8000`:

```powershell
python scripts/smoke_last_whisper_quiet_support.py
python scripts/smoke_last_whisper_crown_tax.py
python scripts/smoke_last_whisper_break_alliance.py
python scripts/smoke_recent_events_contract.py
python scripts/smoke_player_duel_lifecycle.py
python scripts/smoke_assignment_reward_loop.py
python scripts/smoke_scenario_director_advance.py
python scripts/smoke_treasurer_resource_deal.py
python scripts/smoke_expedition_lifecycle.py
python scripts/smoke_court_lifecycle.py
python scripts/smoke_final_terminal_lifecycle.py
python scripts/smoke_visual_runtime_routes.py
```

External route checks:

| Check | Expected |
|---|---|
| `https://<domain>/` | HTTP 200 |
| `https://<domain>/house/<invite_code>` | House lobby loads |
| `https://<domain>/house/<invite_code>/player/<player_id>` | Player room loads |
| `https://<domain>/house/<invite_code>/join-qr.svg` | QR SVG loads and points to public HTTPS domain |
| `https://<domain>/dev/master-screen/<room_code>` | protected; opens after auth |
| `https://<domain>/dev/tv-mode/<room_code>` | protected or display-controlled; production TV route |
| `https://<domain>/dev/tv-screen/<room_code>` | blocked/protected; not used |
| unauthenticated `/dev/games/<room_code>/reset-runtime` | denied |
| unauthenticated `/gold/houses/<house_id>/grant` | denied |

Manual visual checks:

- player phone can join over mobile internet;
- Master screen is usable by operator;
- TV mode is readable on the display;
- QR invite does not show localhost/private IP;
- Last Whisper, Court, Final, Terminal states are visually understandable.

## 13. Rollback / Emergency Plan

Before game:

1. Keep previous known-good git commit recorded.
2. Take database backup.
3. Confirm restore command has been tested on non-live DB or staging clone.
4. Keep local laptop fallback only as emergency, not primary plan.

During game:

- If app process crashes, restart systemd service once and inspect logs.
- If DB is reachable and service restarts cleanly, continue.
- If a route protection issue is discovered, pause game and block route at proxy.
- If game state is corrupted, stop game and restore from pre-game backup only if operator accepts losing in-game progress.
- If public QR/domain fails, switch to manual player links only if player routes still work.

After game:

- take post-game DB backup;
- preserve system logs;
- document incidents before any cleanup;
- do not run reset/seed endpoints until backup is complete.

Rollback commands are intentionally not stored as executable scripts in this plan. They should be prepared for the chosen VPS/provider after domain, database, and service names are final.

## 14. Recommended Route Exposure Table

| Route family | Example | Exposure | Decision |
|---|---|---|---|
| Landing | `https://<domain>/` | public | allow |
| Static assets | `https://<domain>/static/...` | public | allow |
| Question media | `https://<domain>/static/questions_media/...` | public | allow if intended |
| Delegation start | `https://<domain>/delegation/start` | public or operator-gated | decide by event policy |
| Delegation join | `https://<domain>/delegation/join?...` | public | allow |
| House lobby | `https://<domain>/house/<invite_code>` | public by invite | allow |
| Player room | `https://<domain>/house/<invite_code>/player/<player_id>` | public by invite/player URL | allow |
| Player APIs | `https://<domain>/player/...` | public by player context | allow with monitoring |
| Master screen | `https://<domain>/dev/master-screen/<room_code>` | protected | Basic Auth/IP/VPN |
| TV mode | `https://<domain>/dev/tv-mode/<room_code>` | protected or semi-protected | Basic Auth/IP/display device |
| TV legacy | `https://<domain>/dev/tv-screen/<room_code>` | blocked/protected | avoid |
| Master state | `https://<domain>/dev/game-master/<room_code>/state` | protected | Basic Auth/IP/VPN |
| TV state | `https://<domain>/dev/game-master/<room_code>/tv-state` | protected or display-controlled | Basic Auth/IP/display device |
| Scenario director | `https://<domain>/dev/games/<room_code>/scenario/director` | protected | Basic Auth/IP/VPN |
| Reset/seed/import | `/dev/*reset*`, `/dev/*seed*`, `/dev/*import*` | protected | strongest restriction |
| Gold routes | `https://<domain>/gold/...` | protected | strongest restriction |
| Legacy join | `/join`, `/game/...`, `/player/{id}/role-select` | protect or avoid | not production primary |
| Health | `/health` | protected or limited | ops only if possible |

## 15. Suggested Public URL Examples

Player:

```text
https://<domain>/house/<invite_code>/player/<player_id>
```

Master, protected:

```text
https://<domain>/dev/master-screen/<room_code>
```

TV, protected or semi-protected:

```text
https://<domain>/dev/tv-mode/<room_code>
```

Recommended production default:

```text
https://<domain>/dev/master-screen/LIVE01
https://<domain>/dev/tv-mode/LIVE01
```

Avoid:

```text
https://<domain>/dev/tv-screen/LIVE01
```

## 16. Open Decisions

These must be decided before deployment starts:

| Decision | Options | Recommended default |
|---|---|---|
| Domain/subdomain | one domain, `admin`/`tv` split, or path-only split | one domain is acceptable for V1 if `/dev` and `/gold` are protected |
| VPS provider | any stable provider with Ubuntu/Debian and public IPv4 | choose provider with easy snapshots/backups |
| Database location | local PostgreSQL or managed PostgreSQL | local PostgreSQL for simplest V1; managed if ops support exists |
| Route protection | Basic Auth, VPN, IP allowlist, or combined | Basic Auth + optional IP allowlist |
| TV protection | Basic Auth, fixed IP, or semi-public display URL | protect if possible; never expose mutation routes |
| Backup policy | manual `pg_dump`, provider snapshot, managed backups | pre-game `pg_dump` + post-game `pg_dump`; provider snapshot if available |
| Room code | `LIVE01`, `IRON01`, or event-specific | `LIVE01` for production; avoid mixing with old `IRON01` docs |
| Health route exposure | public, protected, or IP-limited | protected or IP-limited |
| Smoke base URL | run smokes on VPS localhost or parameterize later | run on VPS localhost for V1 |

## 17. No-Go Gate

Deployment is not ready if any item is false:

- PostgreSQL `DATABASE_URL` is configured and verified.
- `ADMIN_ROUTE_TOKEN` is configured and not empty.
- Uvicorn binds only to `127.0.0.1`.
- Service runs without `--reload`.
- `/dev/*` is protected externally.
- `/gold/*` is protected externally.
- `/dev/tv-screen/*` is blocked/protected and not used.
- QR/invite URLs use public HTTPS.
- Post-deploy smoke suite passes.
- Pre-game DB backup exists.
- Operator can open Master.
- TV can open `tv-mode`.
- Player phone can open player room over mobile internet.

## 18. Implementation Order

Recommended order:

1. Decide domain/provider/auth/backup policy.
2. Provision VPS and PostgreSQL.
3. Deploy app behind localhost-only Uvicorn.
4. Add reverse proxy and TLS.
5. Protect `/dev/*` and `/gold/*`.
6. Verify external route exposure table.
7. Run command smokes on VPS.
8. Run mobile/TV browser validation.
9. Take pre-game DB backup.
10. Freeze deployment commit and document exact URLs for operator.

## Final Recommendation

Do not deploy PRISTOLOV_CORE V1 by simply binding FastAPI to the public interface.

The safe V1 implementation is:

```text
PostgreSQL
+ systemd Uvicorn on 127.0.0.1:8000
+ HTTPS reverse proxy
+ public player routes
+ protected /dev and /gold
+ VPS-local smoke suite
+ manual browser validation
+ pre-game backup
```

This keeps the runtime freeze intact while making the game reachable from public internet.
