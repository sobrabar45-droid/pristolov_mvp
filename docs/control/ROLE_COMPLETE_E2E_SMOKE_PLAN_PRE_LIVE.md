# Role-complete E2E smoke plan (pre-live)

## 1) Current blocker from production evidence

- LIVE01 currently has only:
  - `lord_lady` (1)
  - `maester` (1)
- Missing for full E2E:
  - `treasurer`
  - `diplomat`
  - `whisper_master`
  - `house_sworn`
- Production result `PRODUCTION_SMOKE_RESULT_PRE_LIVE.md` therefore marks full role/action E2E as no-go on LIVE01.

## 2) Required role inventory for full role E2E

Minimum role set for this smoke:

- `lord_lady`
- `treasurer`
- `diplomat`
- `whisper_master`
- `maester`
- `house_sworn`

## 3) Safe setup options found

### Option A: existing dedicated rehearsal room
- Preferred if present: use a non-live room with enough roles (example: rehearsal room such as `IRON01`).
- Must satisfy:
  - isolated from live data
  - allowed to run destructive setup operations
- Dev routes available:
  - `/dev/games/{room_code}/scenario/apply` (reapply scenario)
  - `/dev/games/{room_code}/seed-technical-run` (creates full technical role inventory for target room)
  - `/dev/reset-delegations/{room_code}` (delegation cleanup via `delegation.py`)

### Option B: controlled LIVE01 variant (limited fallback)
- Use only for full role check if no dedicated room exists and with explicit operator approval.
- Must include complete backup/restore / rollback window because this changes live room player/house composition.
- Run only after a "no active game" window.

### Option C: manual room build through lobby routes
- Create house/lobby flow via `/delegation/start` + `/delegation/join`.
- Assign missing roles manually with:
  - `/house/{invite_code}/assign-role/{player_id}/{role_code}` (house leader path)
  - `/house/{invite_code}/clear-role/{player_id}` (cleanup)
- This is slower and more manual; useful if dedicated scripted room cannot be guaranteed.

## 4) Is there an existing safe API to create a disposable room?

- `seed-technical-run` does **not** create a room; it requires an existing `room_code`.
- No explicit route was found to create a fresh arbitrary room in API docs reviewed.
- `POST /dev/games/{room_code}/reset-runtime` has a room guard and is limited to `IRON01` and `LIVE01`.
- Therefore automation for a brand-new disposable room from APIs is currently limited; a pre-existing rehearsal room is preferred, otherwise Option C (manual build + role assignment) is the fallback.

## 5) E2E role/action matrix

| Area | Route | Non-mutating check | Controlled mutating check | Notes |
|---|---|---|---|---|
| Player room per role | `GET /player/me/{token}` via player links | confirms role visibility and action sections for: `lord_lady`, `treasurer`, `diplomat`, `whisper_master`, `maester`, `house_sworn` | N/A | Required for all roles in same smoke run |
| Treasurer Shop V1.2 queue | `POST /player/treasurer-shop/request/{player_id}`, `GET /cashier/gold-desk/{room_code}`, `POST /cashier/treasurer-shop/requests/{request_id}/confirm` | endpoint existence and empty/pending queue shape | create request (author_tea) → pending row appears → confirm → pending removed and HouseGoldTransaction increments | verify gold decreases only on confirm |
| Gold Desk direct actions | `POST /gold/houses/{house_id}/grant-from-check`, `POST /gold/houses/{house_id}/grant` | none required | one controlled check and one controlled + amount check | manual +1 and check amount modes stay present |
| Last Whisper | `POST /player/last-whisper/action/{player_id}` | wrong phase blocked, wrong/no-op state messages readable | run happy path on active `last_whisper` phase; repeat should be blocked | requires phase-open and valid targets |
| Diplomacy | `POST /player/deals/create/{player_id}`, `POST /player/deals/respond/{player_id}`, `POST /player/alliances/break/{player_id}` | no-target/invalid-role no-op visibility | create alliance → respond/accept → break by whisper task -> verify status transitions | avoid running on live game |
| Expedition / Duel / Lord actions | `POST /player/expedition/create/{player_id}`, `POST /player/duels/challenge/{player_id}`, `POST /player/duels/accept/{player_id}/{duel_id}` | no unauthorized access for wrong role/phase | challenge/accept + expedition action in valid phase | must ensure required host round/expedition phase preconditions |

## 6) Recommended exact strategy

1. Choose a dedicated rehearsal room:
   - If exists: use it with setup/seed commands.
   - If not: create a manual role-complete rehearsal setup via delegation + role assignment (fallback).
2. Pre-smoke setup:
   - apply scenario to room if needed
   - `seed-technical-run` (or fallback manual equivalent) and collect player IDs/tokens.
3. Run non-mutating role surface checks first (all links/routes).
4. Run controlled mutating checks in this order:
   - Lord/Lady: minimal expedition/duel path in allowed phase
   - Treasurer Shop: request → cashier confirm
   - Diplomat: create/accept alliance
   - Whisper: each last-whisper action in active phase
   - House/sworn and maester: confirm no hidden/legacy no-op regressions
5. Validate event visibility after each checked action via `/dev/game-master/{room_code}/state` and `/dev/game-master/{room_code}/tv-state`.
6. If any mutable step can leak to LIVE01, abort and rollback plan before continuing.

## 7) Rollback/cleanup

- Rollback priority:
  1. `POST /dev/games/{room_code}/close-phase/{phase_type}` for opened phases.
  2. `POST /dev/reset-delegations/{room_code}` and/or `POST /dev/games/{room_code}/reset-runtime` where allowed.
  3. Re-seed room from scratch if reusable rehearsal room must continue.
- Never run destructive smoke steps on a room containing real event participants without explicit freeze/approval.

## 8) Go/no-go criteria

- **GO**: role-complete room available and all matrix checks pass with expected readable messages.
- **CONDITIONAL GO**: non-mutating checks pass but one or more mutating flows blocked by missing setup.
- **NO-GO**: no safe room, missing required roles, or any destructive path affecting active live participants.

## 9) Next Codex task

- Create/finalize role-complete disposable test room (or validate existing rehearsal room with required roles), then run role/action smoke protocol from this plan and record blockers/results.
