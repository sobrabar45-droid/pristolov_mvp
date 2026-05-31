# Deployment Readiness Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: PRISTOLOV_CORE V1 is runtime-validated locally, but not yet deployment-ready for an unprotected public VPS.

## Purpose

This audit defines the safest path to run PRISTOLOV_CORE V1 on a public server so players do not need to share the same Wi-Fi and the game is not tied to a local laptop.

It does not deploy the app and does not change runtime code.

## Files Inspected

- `requirements.txt`
- `.env` keys only, without recording secret values
- `app/main.py`
- `app/config.py`
- `app/database.py`
- `app/routes/dev.py`
- `app/routes/delegation.py`
- `app/routes/player.py`
- `app/routes/gold.py`
- `app/routes/join.py`
- `scripts/start_dev_server.ps1`
- `docs/CHECKPOINT_RUNTIME_VALIDATED.md`
- `docs/PRISTOLOV_CORE_V1_FREEZE.md`
- `docs/ROLE_ACTION_REGISTRY_V1_README.md`
- `docs/ROLE_ACTION_REGISTRY_V1.yaml`
- recent git log for checkpoint/smoke references

## Current Local Assumptions

The current project is optimized for a trusted local runtime.

Observed assumptions:

- `scripts/start_dev_server.ps1` binds to `127.0.0.1` by default.
- The local launcher prints and validates `http://127.0.0.1:8000/dev/master-screen/LIVE01`.
- Smoke scripts assume `BASE_URL = "http://127.0.0.1:8000"` and `ROOM_CODE = "LIVE01"`.
- Operator docs still reference `IRON01` in several runbooks.
- `app/config.py` requires `DATABASE_URL` from `.env` or environment variables.
- Current `.env` contains keys for `APP_NAME`, `APP_HOST`, `APP_PORT`, `DEBUG`, `DATABASE_URL`, and `SECRET_KEY`.
- The currently configured `DATABASE_URL` type is PostgreSQL.
- `app/main.py` creates/ensures schema at startup through SQLAlchemy `create_all` plus explicit schema helpers; no migration runner is used.
- Production route shell validation is command-level, not true browser pixel validation.
- The V1 freeze explicitly keeps runtime behavior stable and defers production/VPS hardening as a deployment contour.

## Target Deployment Architecture

Recommended V1 architecture:

```text
Players / Operator / TV browsers
        |
        | HTTPS
        v
Nginx or Caddy reverse proxy
        |
        | localhost only
        v
Uvicorn app process, bound to 127.0.0.1:8000
        |
        v
PostgreSQL database on the same VPS or managed Postgres
```

Recommended deployment properties:

- Run the app behind TLS on a real public domain.
- Bind Uvicorn to `127.0.0.1`, not directly to `0.0.0.0`.
- Use Nginx or Caddy as the only public listener on ports `80` and `443`.
- Use a process manager such as `systemd`.
- Prefer one Uvicorn worker for V1 to reduce race-condition exposure during live play.
- Use PostgreSQL for the first public game.
- Protect operator/dev/control routes at the reverse proxy layer before exposing the server.
- Keep `scripts/start_dev_server.ps1` as local-only tooling, not a production launcher.

## Database Recommendation

PostgreSQL is recommended for the first public VPS game.

Rationale:

- `requirements.txt` already includes `psycopg2-binary`.
- The current local `.env` is already configured as a PostgreSQL-style database.
- Public players create concurrent writes across assignments, deals, duels, expeditions, Last Whisper, and Court/Final state.
- PostgreSQL gives safer backup/restore and better lock behavior than SQLite under live traffic.

SQLite is acceptable only for an emergency controlled rehearsal if all of the following are true:

- one Uvicorn process and one worker;
- very small trusted player count;
- local disk, not network storage;
- no auto-reload;
- pre-game DB backup exists;
- operator accepts file-locking and recovery risk.

SQLite should not be the default public VPS choice for V1.

## Public Routes

These routes can be public in V1, assuming HTTPS and normal rate limiting:

| Route | Purpose | Notes |
|---|---|---|
| `/` | Landing page | Safe if no debug data is exposed. |
| `/static/*` | Static assets | Public. |
| `/static/questions_media/*` | Question media | Public if media is intended for players/TV. |
| `/delegation/start` | House creation/onboarding | Public only if public House creation is intended; otherwise operator-gated. |
| `/delegation/join` | Invite/join flow | Public player onboarding surface. |
| `/house/{invite_code}` | House lobby | Public by invite code. |
| `/house/{invite_code}/player/{player_id}` | Player room | Public player route; player token is embedded in page state. |
| `/house/{invite_code}/join-qr.svg` | Invite QR | Public by invite code. |
| `/player/me/{player_token}` | Player state API | Public by unguessable token. |
| `/player/me/{player_token}/assignments` | Player assignment state | Public by unguessable token. |
| `/player/assignments/{assignment_id}/answer` | Player answer submit | Requires `player_token` in payload. |
| `/player/...` role action endpoints | Player-side role actions | Public because player UI needs them, but current routes often use `player_id`; keep invite/player URLs unguessable and monitor abuse. |

Public player endpoints are not anonymous-safe in a hostile internet sense. They are acceptable for a closed live event if the URLs are shared only with participants and operator/control routes are protected.

## Protected Routes

These routes must not be exposed to the public internet without protection.

Minimum protection for V1:

- HTTP Basic Auth at reverse proxy; and/or
- IP allowlist or VPN for operator devices; and
- separate admin subdomain if possible.

### `/dev/*`

`app/main.py` mounts `dev_router` under `/dev`. This includes both production operator screens and highly dangerous mutation endpoints.

Protect all of `/dev/*` by default.

Important examples:

| Route | Risk |
|---|---|
| `/dev/master-screen/{room_code}` | Master/operator control UI. |
| `/dev/tv-mode/{room_code}` | Production TV route; should be visible only to the room display or protected display browser. |
| `/dev/tv-screen/{room_code}` | Legacy TV route; avoid and block if possible. |
| `/dev/game-master/{room_code}/state` | Full Master state JSON. |
| `/dev/game-master/{room_code}/tv-state` | Full TV state JSON. |
| `/dev/games/{room_code}/scenario/director` | Scenario director state. |
| `/dev/games/{room_code}/scenario/apply` | Scenario mutation. |
| `/dev/games/{room_code}/scenario/start-next-round` | Runtime mutation. |
| `/dev/games/{room_code}/scenario/advance` | Runtime mutation. |
| `/dev/games/{room_code}/reset-runtime` | Destructive cleanup for `IRON01`/`LIVE01`. |
| `/dev/reset-delegations/{room_code}` | Destructive delegation/House cleanup. |
| `/dev/games/{room_code}/seed-technical-run` | Creates technical test state. |
| `/dev/host-rounds/*` | Host round mutation. |
| `/dev/court/*` | Court runtime mutation. |
| `/dev/games/{room_code}/duels/*` | Dev duel mutation. |
| `/dev/houses/{house_id}/gold-adjust` | Manual gold mutation. |
| `/dev/houses/{house_id}/resource-adjust` | Manual resource mutation. |
| `/dev/questions/import` | Question import. |
| `/dev/questions/prepare-media` | Media preparation. |
| `/dev/import-template-*` | Template import/debug routes. |

### `/gold/*`

`gold_router` is mounted publicly under `/gold`. It includes mutating endpoints such as manual grant/spend and PvP resolve.

Protect all of `/gold/*` unless each endpoint is separately audited and intentionally exposed.

Important examples:

- `/gold/houses/{house_id}/grant`
- `/gold/houses/{house_id}/spend`
- `/gold/houses/{house_id}/grant-from-check`
- `/gold/houses/{house_id}/apply-expedition`
- `/gold/pvp/resolve`
- `/gold/houses/{house_id}/transactions`
- `/gold/houses/{house_id}/analytics`

### Legacy Join/Admin Surfaces

`app/routes/join.py` exposes older join/role-select/roster flows:

- `/join`
- `/game/{room_code}`
- `/game/{room_code}/join-house`
- `/player/{player_id}/role-select`
- `/game/{room_code}/roster`

These should be reviewed before public use. Prefer the validated production player route:

```text
/house/{invite_code}/player/{player_id}
```

## Recommended URL Structure

Use explicit public/admin split:

```text
https://play.example.com/
https://play.example.com/delegation/start
https://play.example.com/delegation/join?game_code=LIVE01&invite_code=...
https://play.example.com/house/{invite_code}
https://play.example.com/house/{invite_code}/player/{player_id}
```

Protected operator/display URLs:

```text
https://admin.example.com/dev/master-screen/LIVE01
https://admin.example.com/dev/games/LIVE01/scenario/director
https://tv.example.com/dev/tv-mode/LIVE01
```

Avoid:

```text
/dev/tv-screen/{room_code}
```

For the first deployment, `admin.example.com` and `tv.example.com` may point to the same VPS and same app, but they should be protected separately at the reverse proxy layer.

## Environment Variables / Config

Required:

- `DATABASE_URL`

Currently present in `.env`:

- `APP_NAME`
- `APP_HOST`
- `APP_PORT`
- `DEBUG`
- `DATABASE_URL`
- `SECRET_KEY`

Runtime code currently only requires `DATABASE_URL` through `app/config.py`. Other keys may be launcher/operator conventions rather than active app configuration.

Recommended deployment config:

```text
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@127.0.0.1:5432/pristolov_v1
```

Operational config outside the app:

- Uvicorn bind host: `127.0.0.1`
- Uvicorn port: `8000`
- process manager: `systemd`
- reverse proxy public hostnames;
- TLS certificate paths;
- Basic Auth credentials for admin/dev routes;
- backup location and retention.

Current app code does not expose a canonical `PUBLIC_BASE_URL` setting. QR/invite generation in `delegation.py` uses `request.base_url`, so reverse proxy headers must preserve the public host/proto correctly. If QR links show `127.0.0.1` or internal hostnames after deployment, fix proxy forwarded headers or add a scoped public-base-url config patch later.

## Minimal VPS Checklist

Before the first public game:

1. Provision VPS with firewall open only for `22`, `80`, and `443`.
2. Create a dedicated non-root app user.
3. Install Python, PostgreSQL, Nginx or Caddy, and TLS tooling.
4. Clone the repository into the app user's home or `/opt/pristolov`.
5. Create a virtual environment and install `requirements.txt`.
6. Configure `DATABASE_URL` in an environment file not committed to git.
7. Create PostgreSQL database/user and verify app connection.
8. Start app once in a controlled shell to verify schema creation.
9. Configure `systemd` service for Uvicorn bound to `127.0.0.1:8000`.
10. Configure reverse proxy and HTTPS.
11. Protect `/dev/*` and `/gold/*`.
12. Block or protect `/dev/tv-screen/*`.
13. Confirm player/public routes remain reachable.
14. Confirm QR/invite links use the public HTTPS domain.
15. Run post-deploy smoke checklist.
16. Take a database backup before admitting real players.
17. Prepare operator runbook with exact Master, TV, and Player URLs.

Recommended Uvicorn shape:

```text
uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Do not use `--reload` in production.

## Post-Deploy Smoke Checklist

Run command-level smokes on the VPS against the local app endpoint after the service is up:

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

Current smokes assume `http://127.0.0.1:8000` and `LIVE01`, so run them on the VPS host or through an SSH session unless they are later parameterized.

Also run deployment checks from an external browser/network:

- `GET https://play.example.com/health` returns app/db healthy, or is intentionally protected.
- `GET https://play.example.com/house/{invite_code}` opens a House lobby.
- `GET https://play.example.com/house/{invite_code}/player/{player_id}` opens player room.
- `GET https://admin.example.com/dev/master-screen/LIVE01` is reachable only with admin protection.
- `GET https://tv.example.com/dev/tv-mode/LIVE01` opens the production TV screen for the display browser.
- `/dev/tv-screen/LIVE01` is not used.
- unauthenticated external access to `/dev/games/LIVE01/reset-runtime` is denied.
- unauthenticated external access to `/gold/houses/{house_id}/grant` is denied.

## What Should Remain Local-Only

- `scripts/start_dev_server.ps1`
- local `tmp/` runtime markers and logs
- smoke setup/reset helpers
- scenario import/debug helpers
- `/dev/games/{room_code}/reset-runtime`
- `/dev/reset-delegations/{room_code}`
- `/dev/games/{room_code}/seed-technical-run`
- `/dev/import-template-*`
- `/dev/questions/import`
- `/dev/questions/prepare-media`
- direct DB access
- `/dev/tv-screen/{room_code}` legacy TV route

## No-Go Risks

Do not run a public VPS game if any of these remain true:

- `/dev/*` is reachable from the public internet without protection.
- `/gold/*` is reachable from the public internet without protection.
- reset/seed/import/debug endpoints can be called by players or strangers.
- Master screen is opened over plain HTTP on an untrusted network.
- Player QR/invite links point to `localhost`, `127.0.0.1`, or a private IP.
- Production app is running with `--reload`.
- Production app is bound directly to public `0.0.0.0` without reverse proxy protections.
- SQLite is used with multiple workers or uncontrolled public concurrency.
- No database backup exists before the game starts.
- Operator intends to use `/dev/tv-screen/{room_code}` instead of `/dev/tv-mode/{room_code}`.
- No post-deploy smoke pass has been run against the actual server.

## Blockers Before Public VPS

Hard blockers:

1. Protect `/dev/*`.
2. Protect `/gold/*`.
3. Decide and verify production `DATABASE_URL`.
4. Confirm public HTTPS QR/invite URLs.
5. Configure production process manager without reload.
6. Run the post-deploy smoke suite on the VPS.
7. Create a DB backup/restore plan.

Soft blockers:

- Browser pixel validation is still not complete.
- Race-condition testing is not complete.
- Legacy encoding cleanup is still open in older strings.
- Current smoke scripts are not parameterized for arbitrary public base URLs.
- Role Action Registry is passive and not an authorization source.

## Recommended Minimal Safe Plan For V1

1. Use PostgreSQL.
2. Use one Uvicorn worker behind Nginx/Caddy.
3. Use HTTPS public domain.
4. Route players through `/house/{invite_code}/player/{player_id}`.
5. Route Master through protected `/dev/master-screen/LIVE01`.
6. Route TV through protected `/dev/tv-mode/LIVE01`.
7. Protect all `/dev/*` and `/gold/*`.
8. Keep V1 frozen; do not add deployment-driven mechanics.
9. Run all command smokes on VPS localhost.
10. Perform one manual browser validation pass from real player phones and the TV display.

## Recommendation

PRISTOLOV_CORE V1 can be prepared for VPS deployment without runtime code changes if protection is handled at the reverse proxy layer.

The safest path is not "make the FastAPI app public as-is." The safest path is:

```text
public player routes only
+ protected operator/dev/gold routes
+ PostgreSQL
+ one trusted app process
+ post-deploy smoke suite
+ manual browser validation
```

Until `/dev/*` and `/gold/*` are protected, deployment should be considered blocked for any public internet exposure.
