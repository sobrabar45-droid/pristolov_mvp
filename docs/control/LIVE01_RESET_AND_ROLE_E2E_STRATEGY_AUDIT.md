# LIVE01 reset/test setup and role-complete E2E strategy audit

## 1) Where is the reset-for-test path?

The dev/rehearsal reset button is in `app/templates/master_screen.html` and runs `resetRoomForRehearsal()`.

It calls:

- `POST /dev/games/${ROOM_CODE}/reset-runtime`
- then `GET /dev/reset-delegations/${ROOM_CODE}`

## 2) Endpoint behavior

- `POST /dev/games/{room_code}/reset-runtime` (route in `app/routes/dev.py`)
  - Allowed only for `LIVE01` and `IRON01`.
  - Returns JSON `{ok, deleted}` with counters.
- `GET /dev/reset-delegations/{room_code}` (route in `app/routes/delegation.py`)
  - Deletes players and houses and returns HTML confirmation.

## 3) What reset-runtime currently clears

`/dev/games/{room_code}/reset-runtime` deletes:
- `GameAssignment`
- `GameHostRoundQuestion`
- `GameExpeditionMember`
- `GameExpedition`
- `GameDeal` (including treasurer shop requests)
- `GameDuel`
- `GameHostRound`
- `GamePhase` (court + all non-court)
- `GameMapVisit`
- `GameMapState`

It does not delete:
- `House` and `Player` entities
- `HouseGoldTransaction`
- `Role`, `Game`, `Scenario` metadata

Role assignments are not directly reset by this endpoint:
- primary role on `Player` stays
- only `GameAssignment` rows are cleared

## 4) What reset-delegations clears

`/dev/reset-delegations/{room_code}` deletes:
- `Player`
- `House`
- `HouseGoldTransaction`
- `GameHouseTower`

## 5) Safety assessment for LIVE01

- Technically available for LIVE01, but destructive for active game flow.
- It does not preserve question/round progression continuity after run.
- It can erase live operational state, so should not be used without explicit freeze window.
- No automatic role/phase rebuild is performed.

Important: this is a rehearsal path, not a safe production recovery path.

## 6) Does it create role-complete state for LIVE01?

No.

- `reset-runtime` clears runtime artifacts only.
- `seed-technical-run` (same dev route family) creates a technical fixture with required roles,
  but requires an existing room and does not handle custom scenario narrative setup.

## 7) Strategy comparison

| Option | Summary | Risk | Can cover destructive E2E |
|---|---|---|---|
| A. Use LIVE01 reset-for-test then reconfigure | Possible with full-room downtime | Medium-high | Yes |
| B. Use separate disposable room | Safer by isolation | Low | Yes |
| C. LIVE01 non-destructive only | Safe, but incomplete role/action coverage | Low | No |
| D. Hybrid: disposable room for destructive, LIVE01 for final non-destructive checks | Best practical path | Lowest overall | Yes for disposable room |

## 8) Recommended safe strategy

Recommended: **D (Hybrid)** = B as execution anchor + LIVE01 non-destructive final checks.

Exact sequence:
1. Prepare/validate a separate test room with expected code and players.
2. Run rehearsal reset: `POST /dev/games/{room_code}/reset-runtime`.
3. If needed, run `GET /dev/reset-delegations/{room_code}` for full teardown.
4. Seed technical fixture: `POST /dev/games/{room_code}/seed-technical-run`.
5. Execute role-complete E2E per `ROLE_COMPLETE_E2E_SMOKE_PLAN_PRE_LIVE.md`.
6. If successful, run LIVE01 readiness checks only (non-destructive routes/state checks).

## 9) LIVE01 questions/court/final implications

- LIVE01 currently lacks treasurer/diplomat/whisper_master/house_sworn.
- `reset-runtime` does not guarantee court/final narrative restoration.
- Use non-destructive checks on LIVE01 until role/phase/e2e smoke proves ready in separate room.

## 10) Explicit do-not-execute note

Do not execute LIVE01 reset or role rewiring yet.

## 11) Next Codex task

- Create/validate role-complete disposable room and run role/action E2E.
- Then publish conditional/no-go before any LIVE01 live-scenario mutation.
