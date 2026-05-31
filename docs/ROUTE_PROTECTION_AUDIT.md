# Route Protection Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-06-01  
Status: audit only; no runtime code changes.

## Purpose

This audit identifies the smallest safe protection layer for `/dev/*` and `/gold/*` before public VPS deployment.

The deployment plan requires:

- public player routes;
- protected operator/dev routes;
- protected gold/economy-control routes;
- HTTPS reverse proxy;
- simple and reliable V1 protection.

## Files Inspected

- `app/main.py`
- `app/config.py`
- `.env` keys only, without secret values
- `requirements.txt`
- `app/routes/dev.py`
- `app/routes/gold.py`
- `app/routes/player.py`
- `app/routes/delegation.py`
- `app/routes/join.py`
- `docs/DEPLOYMENT_READINESS_AUDIT.md`
- `docs/DEPLOYMENT_V1_PLAN.md`

## Findings

### Router Mounts

`/dev/*` is mounted in `app/main.py`:

```python
app.include_router(dev_router, prefix="/dev", tags=["dev"])
```

`/gold/*` is mounted through `gold_router`, which declares its own prefix:

```python
router = APIRouter(prefix="/gold", tags=["gold"])
app.include_router(gold_router)
```

Player/delegation/join routes are mounted without a global protection layer:

```python
app.include_router(join_router)
app.include_router(delegation_router)
app.include_router(player_router)
```

### Current Config

`app/config.py` currently requires only:

```text
DATABASE_URL
```

Local `.env` keys observed:

- `APP_NAME`
- `APP_HOST`
- `APP_PORT`
- `DEBUG`
- `DATABASE_URL`
- `SECRET_KEY`

There is no current app-level admin auth setting for `/dev` or `/gold`.

### Current Risk

If the FastAPI app is exposed publicly as-is:

- `/dev/*` exposes Master screen, TV state, scenario controls, reset, seed, import/debug, Court controls, and manual resource controls.
- `/gold/*` exposes gold grant/spend/check/expedition/PvP mutation endpoints plus transaction/analytics reads.
- Reverse proxy config mistakes can immediately expose destructive controls.

This is a public deployment blocker.

## Protection Options

| Option | Summary | Pros | Cons | V1 Fit |
|---|---|---|---|---|
| Reverse proxy Basic Auth only | Protect `/dev/*` and `/gold/*` in Nginx/Caddy | no app code, simple ops | one proxy mistake opens critical routes; local direct port exposure remains dangerous | acceptable only with strict ops |
| FastAPI middleware | One app-level guard checks path prefixes before route handling | small patch, covers all current/future `/dev` and `/gold` routes | needs env vars and smoke updates | best minimal app fallback |
| Dependency per router | Add dependency to `dev_router` and `gold_router` | idiomatic FastAPI, targeted | misses non-router `/dev/reset-delegations` if not mounted through same router pattern; more file churn | workable but less minimal |
| Dependency per route | Add auth dependency to every route | explicit | large risky patch, easy to miss route | not recommended |
| VPN/IP allowlist only | Restrict admin network | strong if stable | brittle for venues/mobile operator, not enough alone | good add-on |
| Both proxy + app guard | Proxy protects public edge; app guard prevents accidental exposure | defense in depth, still small | requires one small runtime patch | recommended V1 |

## Recommended V1 Protection Design

Use defense in depth:

1. Reverse proxy protects `/dev/*` and `/gold/*`.
2. FastAPI app also enforces a small header-token guard for `/dev/*` and `/gold/*`.
3. Uvicorn remains bound to `127.0.0.1`.
4. Player/delegation/static routes remain public.

Recommended app-level guard:

- add a minimal HTTP middleware in `app/main.py` or small helper module;
- check request path before route handling;
- protect prefixes:
  - `/dev`
  - `/gold`
- allow only when a configured header token matches;
- return `404` or `403` for unauthenticated access;
- do not use cookies/sessions for V1;
- do not protect `/player/*`, `/house/*`, `/delegation/*`, `/static/*`.

Recommended header:

```text
X-Pristolov-Admin-Token: <secret>
```

Recommended env vars:

| Variable | Required | Purpose |
|---|---:|---|
| `DATABASE_URL` | yes | existing DB config |
| `ADMIN_ROUTE_TOKEN` | yes for public deploy | app-level token for `/dev/*` and `/gold/*` |
| `ADMIN_ROUTE_PROTECTION_ENABLED` | optional | defaults to enabled when token is present; can be explicit |

Suggested behavior:

| Condition | Result |
|---|---|
| path does not start with `/dev` or `/gold` | allow |
| path starts with `/dev` or `/gold`, token matches | allow |
| path starts with `/dev` or `/gold`, token missing/wrong | reject |
| protection enabled but `ADMIN_ROUTE_TOKEN` missing | fail closed for protected paths |
| local dev without token | either disabled explicitly or use local `.env` token |

Recommended rejection code:

- `404` if we want to hide protected route existence;
- `403` if we want clearer smoke assertions.

For V1 smoke clarity, `403` is easier to verify. For internet-hardening, `404` is slightly quieter. Either is acceptable if documented; choose one and smoke it.

## What Remains Public

| Route family | Exposure | Notes |
|---|---|---|
| `/` | public | landing page |
| `/static/*` | public | assets |
| `/static/questions_media/*` | public | media assets |
| `/delegation/start` | public or event-policy gated | public only if open House creation is intended |
| `/delegation/join` | public | invite onboarding |
| `/house/{invite_code}` | public by invite | House lobby |
| `/house/{invite_code}/player/{player_id}` | public by invite/player URL | player room |
| `/house/{invite_code}/join-qr.svg` | public by invite | QR SVG |
| `/player/me/{player_token}` | public by token | player state |
| `/player/me/{player_token}/assignments` | public by token | assignments |
| `/player/assignments/{assignment_id}/answer` | public with token payload | answer submit |
| `/player/duels/*` | public by player context | V1 player-side duel actions |
| `/player/expedition/*` | public by player context | V1 expedition actions |
| `/player/deals/*` | public by player context | V1 deal actions |
| `/player/last-whisper/action/{player_id}` | public by player context | V1 Master Whisper |

Known caveat:

Some player action routes use `player_id`, not only `player_token`. This is outside this `/dev`/`/gold` protection patch and should not be mixed into it.

## What Must Be Protected

| Route family | Examples | Reason |
|---|---|---|
| `/dev/*` | all `dev_router` routes | operator/dev/control surface |
| `/dev/master-screen/{room_code}` | Master UI | operator only |
| `/dev/tv-mode/{room_code}` | TV screen | room display only; still under protected path |
| `/dev/tv-screen/{room_code}` | legacy TV | avoid/block |
| `/dev/game-master/{room_code}/state` | Master JSON state | full state exposure |
| `/dev/game-master/{room_code}/tv-state` | TV JSON state | full display state exposure |
| `/dev/games/{room_code}/scenario/*` | scenario apply/advance | runtime mutation |
| `/dev/games/{room_code}/reset-runtime` | reset | destructive |
| `/dev/reset-delegations/{room_code}` | reset delegations | destructive; declared in `delegation.py` but path starts with `/dev` |
| `/dev/games/{room_code}/seed-technical-run` | seed test state | destructive/test setup |
| `/dev/host-rounds/*` | host round controls | runtime mutation |
| `/dev/court/*` | Court controls | runtime mutation |
| `/dev/questions/*` | import/media prep | content mutation |
| `/dev/houses/{house_id}/gold-adjust` | manual gold | economy mutation |
| `/dev/houses/{house_id}/resource-adjust` | manual resources | economy mutation |
| `/gold/*` | all gold router routes | economy mutation/read surface |
| `/gold/houses/{house_id}/grant` | grant gold | economy mutation |
| `/gold/houses/{house_id}/spend` | spend gold | economy mutation |
| `/gold/houses/{house_id}/grant-from-check` | check-based grant | economy mutation |
| `/gold/houses/{house_id}/apply-expedition` | expedition gold outcome | economy mutation |
| `/gold/pvp/resolve` | PvP gold resolution | economy mutation |
| `/gold/houses/{house_id}/transactions` | ledger read | sensitive read |
| `/gold/houses/{house_id}/analytics` | analytics read | sensitive read |

## Reverse Proxy vs App Code

### Leave To Nginx/Caddy

The reverse proxy should handle:

- HTTPS/TLS;
- Basic Auth prompts for browsers;
- IP allowlist/VPN restrictions if used;
- rate limiting if configured;
- blocking `/dev/tv-screen/*` if desired;
- forwarding `X-Pristolov-Admin-Token` to the app for protected upstream requests.

### Enforce In App Code Too

The FastAPI app should enforce:

- `/dev/*` requires admin token;
- `/gold/*` requires admin token;
- missing token fails closed on protected paths;
- public routes are unaffected.

Why app enforcement is recommended:

- prevents accidental public exposure if proxy auth is removed or misconfigured;
- protects local direct access if Uvicorn is accidentally bound publicly;
- covers `/dev/reset-delegations/{room_code}`, which lives in `delegation.py` but still has a `/dev` path;
- protects every current and future route under these prefixes without touching route bodies.

## Smallest Safe Implementation Plan

Recommended code patch, not implemented in this audit:

1. Extend `Settings` in `app/config.py`:
   - `ADMIN_ROUTE_TOKEN: str | None = None`
   - `ADMIN_ROUTE_PROTECTION_ENABLED: bool = True`

2. Add a small middleware in `app/main.py`:
   - define protected prefixes `("/dev", "/gold")`;
   - if path starts with protected prefix, compare `request.headers.get("X-Pristolov-Admin-Token")` with `settings.ADMIN_ROUTE_TOKEN`;
   - use constant-time compare from `secrets.compare_digest`;
   - reject missing/wrong token;
   - allow all other paths unchanged.

3. Keep all route files unchanged:
   - no route refactor;
   - no per-route dependencies;
   - no gameplay changes.

4. Configure reverse proxy:
   - Basic Auth for browser access;
   - inject or pass `X-Pristolov-Admin-Token` only after successful auth;
   - deny unauthenticated `/dev/*` and `/gold/*`.

5. Update deployment docs/runbook after implementation.

Why middleware instead of dependencies:

- one small patch;
- protects route families rather than individual routes;
- catches `/dev/reset-delegations/{room_code}` even though it is declared outside `dev_router`;
- avoids touching high-risk route code before deployment.

## Smoke Test Plan

Create focused smoke after implementation:

```text
scripts/smoke_route_protection.py
```

Required checks:

1. Runtime starts with `ADMIN_ROUTE_TOKEN` configured.
2. Public route without token succeeds:
   - `GET /`
   - `GET /delegation/start`
3. Player/delegation route without token succeeds after seed/setup if needed:
   - `GET /house/{invite_code}` or production route shell equivalent.
4. Protected `/dev` route without token is rejected:
   - `GET /dev/master-screen/LIVE01`
   - `GET /dev/game-master/LIVE01/state`
5. Protected `/dev` mutating route without token is rejected:
   - `POST /dev/games/LIVE01/reset-runtime`
6. Protected `/gold` route without token is rejected:
   - `POST /gold/houses/1/grant`
7. Same protected routes with valid token are allowed far enough to prove auth pass:
   - may return normal 200/404/domain error depending on setup;
   - must not return auth rejection.
8. Wrong token is rejected.
9. Smoke must verify no protected mutation occurs when token is missing.

Suggested command:

```powershell
python scripts/smoke_route_protection.py
```

Optional deployment smoke:

- from outside the VPS, verify unauthenticated `/dev/*` and `/gold/*` are denied at reverse proxy before reaching app.

## No-Go Risks

Do not deploy publicly if:

- `/dev/*` is unprotected at proxy and app levels;
- `/gold/*` is unprotected at proxy and app levels;
- token is committed to git;
- app protection can be disabled accidentally in production;
- public player routes require admin auth after the patch;
- `/dev/reset-delegations/{room_code}` is missed;
- `/gold/houses/{house_id}/grant` is reachable without auth;
- smoke does not prove failed unauthenticated mutations are non-mutating;
- proxy Basic Auth works but app-level fallback is missing and Uvicorn is reachable directly.

## Recommendation

The safest V1 approach is:

```text
Reverse proxy Basic Auth/IP rules
+ app-level protected-prefix middleware for /dev and /gold
+ ADMIN_ROUTE_TOKEN in environment
+ focused route protection smoke
```

This is smaller and safer than per-route edits, while avoiding a single point of failure in Nginx/Caddy config.

Do not implement role/player auth changes in the same patch. Keep the protection patch strictly scoped to operator/dev/gold exposure before public deployment.
