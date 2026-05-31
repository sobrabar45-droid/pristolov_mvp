# Deployment V1 Ops Bundle

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-06-01  
Status: operations bundle only; no deploy and no runtime behavior changes.

## Purpose

This bundle turns the V1 deployment plan into concrete operator-facing files and checklists for public VPS launch.

It assumes:

- PRISTOLOV_CORE V1 is frozen and runtime-validated.
- PostgreSQL is used for public V1.
- Uvicorn runs behind a reverse proxy.
- `/dev/*` and `/gold/*` are protected by both reverse proxy policy and `ADMIN_ROUTE_TOKEN`.
- Player routes remain public.

## Included Template Files

- `.env.production.example`
- `deploy/systemd/pristolov.service.example`
- `deploy/nginx/pristolov.nginx.example`

All examples use placeholders only:

- `<DOMAIN>`
- `<PROJECT_DIR>`
- `<USER>`
- `<ADMIN_ROUTE_TOKEN>`
- `<DATABASE_URL>`

Do not commit real production values.

## 1. VPS Preparation Checklist

1. Choose VPS provider and region.
2. Provision Ubuntu/Debian LTS.
3. Configure SSH key access.
4. Disable password SSH login if possible.
5. Create dedicated app user:
   - `<USER>`
6. Configure firewall:
   - allow `22/tcp`
   - allow `80/tcp`
   - allow `443/tcp`
   - deny direct app port `8000/tcp` externally
7. Install system packages:
   - Python 3
   - Python venv package
   - PostgreSQL client/server or managed DB client
   - Nginx
   - certbot or provider TLS tooling
8. Create project directory:
   - `<PROJECT_DIR>`
9. Clone repository into `<PROJECT_DIR>`.
10. Checkout the intended release commit.

## 2. Python / Venv Setup

Recommended shape:

```bash
cd <PROJECT_DIR>
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt
```

Runtime command shape:

```bash
./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1
```

Production rules:

- Do not use `--reload`.
- Do not bind Uvicorn to public `0.0.0.0`.
- Keep one worker for V1 unless race-condition hardening is separately reviewed.

## 3. PostgreSQL Setup Checklist

1. Create database:
   - `pristolov_v1`
2. Create dedicated DB user:
   - `pristolov_app`
3. Grant only required privileges.
4. Build production `DATABASE_URL`.
5. Store `DATABASE_URL` only in server environment file.
6. Start app once and watch logs for schema creation/ensure errors.
7. Create pre-game backup:

```bash
pg_dump <DATABASE_URL> > pristolov_v1_pre_game.sql
```

8. Create post-game backup immediately after live play:

```bash
pg_dump <DATABASE_URL> > pristolov_v1_post_game.sql
```

Do not use SQLite for public V1 except as emergency/local fallback.

## 4. `.env.production` Creation Checklist

Use `.env.production.example` as source.

Recommended server file:

```text
/etc/pristolov/pristolov.env
```

Required variables:

```text
DATABASE_URL=<DATABASE_URL>
ADMIN_ROUTE_TOKEN=<ADMIN_ROUTE_TOKEN>
```

Rules:

- `DATABASE_URL` should point to PostgreSQL for public V1.
- `ADMIN_ROUTE_TOKEN` must be long and random.
- Do not commit the real env file.
- If `ADMIN_ROUTE_TOKEN` is empty, `/dev/*` and `/gold/*` remain open for local/dev compatibility.
- Public VPS deployment without `ADMIN_ROUTE_TOKEN` is a no-go.

## 5. Systemd Service Example

Template:

- `deploy/systemd/pristolov.service.example`

Install shape:

```bash
sudo cp deploy/systemd/pristolov.service.example /etc/systemd/system/pristolov.service
sudo sed -i 's#<PROJECT_DIR>#/opt/pristolov_mvp#g' /etc/systemd/system/pristolov.service
sudo sed -i 's#<USER>#pristolov#g' /etc/systemd/system/pristolov.service
sudo systemctl daemon-reload
sudo systemctl enable pristolov
sudo systemctl start pristolov
sudo journalctl -u pristolov -n 100 --no-pager
```

Before live game:

- confirm service starts cleanly;
- confirm logs do not contain startup schema errors;
- confirm Uvicorn is bound to `127.0.0.1:8000`;
- confirm app restarts after `sudo systemctl restart pristolov`.

## 6. Nginx Reverse Proxy Example

Template:

- `deploy/nginx/pristolov.nginx.example`

Expected behavior:

- public routes are proxied without admin header;
- `/dev/*` requires Basic Auth and receives `X-Admin-Token`;
- `/gold/*` requires Basic Auth and receives `X-Admin-Token`;
- `/dev/tv-screen/*` is blocked;
- Uvicorn remains private on `127.0.0.1:8000`.

Install shape:

```bash
sudo cp deploy/nginx/pristolov.nginx.example /etc/nginx/sites-available/pristolov
sudo sed -i 's/<DOMAIN>/example.com/g' /etc/nginx/sites-available/pristolov
sudo sed -i 's/<ADMIN_ROUTE_TOKEN>/<real-token>/g' /etc/nginx/sites-available/pristolov
sudo ln -s /etc/nginx/sites-available/pristolov /etc/nginx/sites-enabled/pristolov
sudo nginx -t
sudo systemctl reload nginx
```

For Basic Auth:

```bash
sudo htpasswd -c /etc/nginx/.htpasswd_pristolov <admin_user>
```

Do not commit the generated htpasswd file.

## 7. HTTPS Checklist

1. Point `<DOMAIN>` DNS to VPS public IP.
2. Confirm `http://<DOMAIN>` reaches Nginx.
3. Issue TLS certificate.
4. Redirect HTTP to HTTPS.
5. Confirm:
   - `https://<DOMAIN>/`
   - `https://<DOMAIN>/house/<invite_code>`
   - `https://<DOMAIN>/dev/master-screen/<room_code>` after auth
6. Confirm QR/invite links use `https://<DOMAIN>`, not localhost/private IP.

## 8. `ADMIN_ROUTE_TOKEN` Usage

`ADMIN_ROUTE_TOKEN` is app-level defense in depth.

When set:

- `/dev/*` requires `X-Admin-Token: <ADMIN_ROUTE_TOKEN>`;
- `/gold/*` requires `X-Admin-Token: <ADMIN_ROUTE_TOKEN>`;
- missing/wrong token returns `403`;
- route handlers do not execute before token check.

Recommended production pattern:

- browser sees Basic Auth prompt at Nginx;
- after successful Basic Auth, Nginx forwards:

```text
X-Admin-Token: <ADMIN_ROUTE_TOKEN>
```

No-go:

- exposing `ADMIN_ROUTE_TOKEN` to players;
- placing token in public JS;
- putting token into URLs;
- committing token to git;
- deploying public VPS without token.

## 9. Protected Route Smoke Commands

Run locally after route protection patch:

```bash
python scripts/smoke_route_protection.py
```

Expected:

```text
ROUTE PROTECTION SMOKE: PASS
```

External VPS checks:

```bash
curl -i https://<DOMAIN>/dev/master-screen/LIVE01
curl -i https://<DOMAIN>/dev/games/LIVE01/reset-runtime
curl -i https://<DOMAIN>/gold/houses/1/grant
```

Expected unauthenticated result:

- `401` from Basic Auth, or
- `403` from app guard if proxy forwards request without token.

Authenticated operator route should work through browser after Basic Auth.

## 10. Post-Deploy Smoke Commands

Run on the VPS host, against local app service:

```bash
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
python scripts/smoke_route_protection.py
```

Manual browser checks:

- open player route from mobile internet;
- open Master route after auth;
- open TV mode route after auth or on protected display device;
- confirm `/dev/tv-screen/<room_code>` is not used;
- confirm QR code points to public HTTPS domain.

## 11. Emergency Rollback Steps

Before live game:

1. Record deployed git commit.
2. Create DB backup.
3. Confirm systemd service can restart.
4. Confirm Nginx config can reload.

If app fails after deploy:

1. Stop live traffic if possible.
2. Inspect:

```bash
sudo journalctl -u pristolov -n 200 --no-pager
sudo nginx -t
```

3. Roll back git checkout to previous known-good commit.
4. Reinstall dependencies only if requirements changed.
5. Restart app:

```bash
sudo systemctl restart pristolov
```

6. Re-run smoke route and basic runtime checks.

If DB state is corrupted:

1. Stop app service.
2. Restore from pre-game backup only with operator approval.
3. Start service.
4. Re-run route and visual checks.

After game:

- create post-game DB backup;
- preserve logs;
- do not run reset endpoints until backup is complete.

## 12. No-Go Checklist Before Live Game

Do not start the live game unless all are true:

- VPS firewall exposes only expected ports.
- Uvicorn is bound to `127.0.0.1:8000`.
- HTTPS is active.
- PostgreSQL `DATABASE_URL` is configured.
- `ADMIN_ROUTE_TOKEN` is configured and not empty.
- `/dev/*` is protected externally.
- `/gold/*` is protected externally.
- `/dev/tv-screen/*` is blocked/protected and not used.
- Player route works over mobile internet.
- Master route works after auth.
- TV mode route works on display device.
- QR/invite uses public HTTPS domain.
- Route protection smoke passes.
- Runtime smoke suite passes.
- Pre-game DB backup exists.
- Operator has exact URLs and rollback contact.

## Remaining Deployment Decisions

- Final `<DOMAIN>`.
- VPS provider.
- Actual `<PROJECT_DIR>`.
- Actual `<USER>`.
- Basic Auth username/password.
- Whether TV uses Basic Auth, IP allowlist, or fixed display network.
- Backup retention policy.
- Whether `/delegation/start` is public or operator-gated for the event.
