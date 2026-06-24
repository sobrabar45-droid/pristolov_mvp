# FRANCHISE_MULTI_ROOM_AND_ROOM_LOADER_AUDIT.md

## 1) Executive summary

Current runtime already has a partially working multi-room core: most gameplay entities are `game_id`-scoped and key user flows can target a specific `room_code`.
This allows multiple rooms in principle, but the operator experience for creating/loading rooms is fragmented and partly legacy-oriented to LIVE01.

For safe continuation of gameplay features, **mechanics can continue on top of current V1 data model**, but a room setup foundation layer is required before large-scale franchise expansion.

## 2) Current room/game architecture

- Primary external identity for game selection is `room_code`.
- Core runtime state is mostly stored per-game/`game_id`.
- Main flows already accept room-scoped paths (`/player`/token based routes are implicitly scoped via player->game; `/cashier`, `/dev`, `/delegation`, join routes include room or invite references).
- Scenario import/apply can be targeted to a room through `dev` endpoints and services.

## 3) What is already multi-room safe

### Data model
- `House`, `Player`, `GamePhase`, `GameAssignment`, `GameDeal`, `HouseGoldTransaction`, `GameHostRound`, `GameHostRoundQuestion`, expedition/court/duel/map state models are game-scoped through `game_id`/FKs.
- `Game` contains `room_code` and is the central tenant boundary.
- Role/house/player resolution in `/player/...` routes comes from `player_token -> Player -> Game`, not hardcoded current room.

### Route behavior
- `/player/me/{player_token}` and `/player/me/{player_token}/assignments` are room-implicit via token resolution.
- `/cashier/gold-desk/{room_code}` and `/delegation/join*`, `/game/{room_code}` routes are explicit room-anchored.
- `/dev/game-master/{room_code}`, `/dev/tv-mode/{room_code}`, `/dev/gold-desk/{room_code}`, `/dev/reset-delegations/{room_code}`, `/games/{room_code}/scenario` are room-aware.
- `app/routes/gold.py`, `cashier`, `player`, `delegation`, `dev`, `join` show route-level room scoping patterns.

### Scenario loading core
- Scenario templates can be loaded/edited in reusable templates and applied to a selected game via scenario service + routes (dev APIs).
- Scenario director operations are per-room.

## 4) What is potentially unsafe/global

- `delegation.py`:
  - `GET /delegation/start` defaults `game_code="LIVE01"` and `entry_mode="random"` which can silently route guests to LIVE01 if query args are omitted.
- `dev.py`:
  - `reset-runtime` is restricted to explicit set of room codes (`IRON01`, `LIVE01`), which blocks generic room operations via that endpoint in normal automation.
- Several scripts are room-specific and one-room focused.
- Any shared operator auth (`/dev` endpoints) is global by design in current model.
- No dedicated room-setup wizard: setup requires multiple manual calls or scripts.

## 5) LIVE01 hardcoding/default-game risks

| Area | Risk |
|---|---|
| One-QR flow | default `game_code` = LIVE01 can misroute guests if QR or link misses params |
| Reset scripts | `bootstrap_live01_vps.py` and rehearsal scripts are fixed on LIVE01 |
| Admin debug routes | reset/delegations historically assumes specific room list in one path |
| Operational discipline | safe room switching depends on operators manually managing room_code consistently |

## 6) Route isolation matrix

| Route family | Room scope | Risk level | Note |
|---|---|---|---|
| `player` (`/player/me/{token}`) | yes (token -> player -> game) | Low | No room param in path, safe only if token is room-correct |
| `join` (`/game/{room_code}` etc.) | explicit | Low | Good for self-serve room entry |
| `cashier` (`/cashier/.../{room_code}`) | explicit | Low | Protected by middleware when `ADMIN_ROUTE_TOKEN` set |
| `tv/master` dev routes (`/dev/game-master`, `/dev/tv-mode`) | explicit | Medium | Admin-only, room query is explicit |
| `delegation/start` | room optional via query default | Medium | Defaults to LIVE01 if omitted |
| `dev/games/{room_code}/scenario*` | explicit | Medium | Powerful admin operations; no shared room abstraction outside manual workflow |
| `dev/games/{room_code}/reset-runtime` | explicit + whitelist check | High | Operationally unsafe default for generic automation |
| `court`/`expedition`/`duel` in dev routes | explicit | Medium | Room-param routes exist; still manual sequencing heavy |

## 7) Data model scoping matrix

| Entity | `game_id` | `room_code` direct | Global risk |
|---|---:|---:|---|
| `Game` | yes (primary key) | yes (`room_code`) | `room_code` should be unique and validated |
| `House` | yes | no | scoped by `game_id` |
| `Player` | yes | no | scoped by `game_id` |
| `GamePhase` | yes | no | scoped by `game_id` |
| `GameAssignment` | yes | no | scoped |
| `GameDeal` | yes | no | scoped |
| `HouseGoldTransaction` | yes | no | scoped |
| `GameHostRound` | yes | no | scoped |
| `GameHostRoundQuestion` | via round | no | scoped |
| `Duel/Expedition/Map` entities | mostly via game_id | no | scoped |
| template tables (`RoundTemplate`, `ScenarioTemplate`) | no | no | shared template catalog; this is expected global layer |

## 8) Scenario/question loading current reality

### How scenario import/apply works now
1. Scenario file is parsed/imported into template structures.
2. Templates are stored/reused by scenario code/name.
3. Runtime application attaches scenario/round context to specific `room_code` game.

### How questions enter runtime
- Questions become available via game host-round linkage when scenario is applied and runtime rounds are started.
- Developer/dev tooling exposes scenario/director operations and seeding-like helpers.

### Operator usability today
- Non-developer operations are partially possible through routes but not packaged as one-step setup.
- No single “upload scenario + assign to new room + prefill question source + smoke URLs” operator flow exists.
- Imports and scenario switching remain multi-step and dev-centric.

## 9) Room creation/setup current reality

### What exists today
- Room/house/player flow via join/delegation endpoints.
- One-QR flow for house creation and invite-based join is available (`/delegation/start`, `/house/{invite_code}`, `/join`).
- Dev/dev helper endpoints can reset scenario, phases, and relations by `room_code`.
- Bootstrap/rehearsal scripts can prepare LIVE01 quickly.

### What is missing for general KURGAN01/TYUMEN01 onboarding
- No first-class room creation assistant CLI/UI that chains:
  - create room,
  - choose scenario,
  - load question bank,
  - open registration,
  - verify generated URLs.
- No generic room bootstrap command in-tree (scripts are currently hardcoded to LIVE01).
- Reset and scenario operations are split across endpoints; error-prone for operators without checklist discipline.

## 10) Operator pain points

- DEFAULT/implicit behavior can silently hit LIVE01.
- Room whitelist behavior on some dev maintenance routes (`reset-runtime`) is non-obvious.
- No uniform post-creation smoke checklist by room at onboarding.
- Scenario/template changes require dev-level knowledge of route order and tokenized checks.
- Global admin surface (`/dev`) is powerful but operationally shared, increasing blast radius in shared use.

## 11) Franchise/multi-city readiness assessment

### What works now
- Data model mostly supports multiple games simultaneously.
- Room isolation is present in most primary routes.

### What is weak for multi-city/franchise
- No dedicated room lifecycle UI/CLI.
- No clear guarded operator onboarding guardrails for non-technical staff.
- Hardcoded LIVE01 defaults/scripts reduce confidence for replica-room repeatability.
- Missing “room wizard” means scaling to KURGAN01/TYUMEN01 is manual and inconsistent.

## 12) Risk of future fundamental rework

- **Low architectural risk**: core model is sufficiently game-scoped to avoid immediate data-layer refactor.
- **Medium product/ops risk**: current control plane is fragmented and requires explicit operator discipline.
- **High operational risk if growing franchise**: without a setup layer, mistakes in room selection/scenario/registration may be frequent and hard to audit.

## 13) Decision recommendation

Mechanics can continue for single-game V1, but for franchise expansion and safe future operator self-service, we should **pause broader mechanic expansion** and implement room setup foundation first.

Recommended priority:
1. Room setup loader design (operator-facing, one-command/one-screen),
2. then controlled room setup helper/CLI,
3. then multi-room smoke protocol.

## 14) Proposed Room Setup Wizard / Game Loader MVP

Minimum viable wizard steps:
1. Create/select game room (`room_code`, display name, host name).
2. Pick scenario template from known catalog.
3. Optional question pack choice (`do not import` unless explicitly approved).
4. Reset/Clean existing room state if selected.
5. Open registration mode (`delegation` random/manual entry settings, house caps).
6. Generate key URLs/QR links for:
   - One-QR house creation,
   - Master,
   - TV,
   - Cashier,
   - Join page.
7. Run room-isolation smoke checks (`player/master/tv/cashier` 200).
8. Persist setup summary for audit.

## 15) Candidate next tasks

A. Room setup flow design doc (fast, minimal risk, no runtime change).  
B. Room setup CLI/helper command.  
C. Dev/operator room lifecycle screen (create room/apply scenario/reset/start-smoke).  
D. Multi-room isolation smoke test pack.  
E. Scenario/question import simplification for non-developer operators.  
F. Franchise auth model for operator roles and per-city admin.

## Recommended next Codex task

### A. Room setup flow design doc

Start with explicit process/API contract and operator checklist before runtime changes.

