# LIVE01 real-game cleanup and rebuild plan

## 1) Scope and objective

- Current base: `LIVE01` currently contains a role-complete rehearsal fixture and rehearsal artifacts.
- Runtime changes and reset operations are **not** executed by this task.
- Goal: prepare a safe cleanup + real setup workflow before inviting real players.
- Refs:
  - `0112e3b` role-complete rehearsal E2E result
  - `fb8a8e5` real-game setup readiness audit
  - `LIVE01_RESET_AND_ROLE_E2E_STRATEGY_AUDIT.md`

## 2) Pre-reset evidence checklist

Run before any destructive action:

- Git/service/build:
  - `git rev-parse --short HEAD`
  - `python -m compileall app -q`
  - production service check on VPS: `systemctl status pristolov --no-pager`
- LIVE01 inventory snapshot:
  - `houses_count`, `players_count`, `role_counts`
  - `gold transaction count`
  - `deal count`
  - `active phase count`
  - `expedition count`
  - `map visit/state count`
- Scenario/template presence:
  - `app/game_templates/scenarios/season1_mvp_live_v2.json` exists/readable
  - `app/game_templates/season1_core_v1/*.yaml` exists/readable

Last captured LIVE01 snapshot (from rehearsal doc, now stale for real setup):

- Houses: `2`
- Players: `10`
- Roles:
  - `lord_lady: 2`, `diplomat: 2`, `maester: 2`, `treasurer: 1`, `whisper_master: 2`, `house_sworn: 1`
- Gold transactions: `5`
- Deals: `2`
- Active phases: `3`
- Expeditions: `1`
- Map visits: `1`

Known route paths for reset-like actions:

- `POST /dev/games/{room_code}/reset-runtime`
- `GET /dev/reset-delegations/{room_code}`

## 3) Reset execution plan (no execution yet)

**Exact required order**

1. `POST /dev/games/LIVE01/reset-runtime`
2. `GET /dev/reset-delegations/LIVE01`

This order is deliberate: first clears gameplay/runtime state, then optionally removes delegations/houses/players.

## 4) Expected destructive effects

`reset-runtime` removes:

- house/round assignments
- host round questions
- expeditions and expedition members
- diplomacy deals
- duels
- host rounds and active phases
- map visits/map state rows
- treasurer shop request deals

`reset-delegations` removes:

- `Player` rows for LIVE01
- `House` rows for LIVE01
- `HouseGoldTransaction` history
- `GameHouseTower` rows

## 5) Expected post-reset state after both calls

- Game exists (`LIVE01`) and scenario/template references can be present if previously applied.
- No live roster data (`Player`, `House`) if both calls were run.
- No rehearsal runtime artifacts listed above.
- No leftover rehearsal shop queue for technical treasurer requests.
- No guarantee of role/roster restoration; this must be done via operator setup.

## 6) Rollback / safety note

- These operations are destructive and do not have automatic rollback.
- Do not execute until explicit user approval and freeze window.
- Keep a roster backup (names + roles + house assignment plan) before execution.
- This plan is **approval-gated** and does not request execution.

## 7) Real rebuild plan (after approved reset)

### User-provided data required

- Real house list (exact house names) and team mapping.
- Player names and attendance list by house.
- Planned role assignment mapping (`role_code` per player).
- Starting gold/resource baseline (if not default).
- Decision to continue with:
  - `season1_mvp_live_v2` as scenario source, and `season1_core_v1` template bundle.

### What can be automated after data is provided

- Apply scenario/template checks via existing script (`bootstrap_live01_vps.py`) for LIVE01 baseline integrity:
  - ensures `season1_mvp_live_v2`
  - ensures required role records exist
  - applies template bundles
- Verify scenario presence/rounds/questions from scenario metadata.
- Operator performs roster import/assignment through existing delegation/admin workflows.
- Gold/resource prefill per house through existing operations only.

### What remains manual/operator

- Register players for real tournament flow.
- Assign houses and roles to match physical/operational roster plan.
- Confirm role inventory for the expected mix.
- Seed/confirm opening phase state and initial game instructions.

## 8) Post-rebuild automated smoke checklist

- Surface and route smoke:
  - `/cashier/gold-desk/LIVE01` (protected)
  - `/dev/master-screen/LIVE01`
  - `/dev/tv-mode/LIVE01`
  - `/dev/treasurer-shop/LIVE01`
- No `/dev` links visible on public-facing pages (`player_room`, cashier).
- Scenario/phase label readable (including “Последний Шёпот”).
- Player-room smoke for expected role set.
- Cashier:
  - manual +1 visible and works
  - check amount mode visible and works
  - request queue is empty by default
  - no pending legacy rehearsal requests
- Treasurer Shop V1.2 state:
  - pending queue absent initially
  - confirm path works when request created during real play

## 9) Post-rebuild manual acceptance (after automated checks)

- Master sees proper live scenario/room status.
- TV rendering is clear and stable.
- Cashier page is usable and free from `/dev` links.
- One player per role opens expected player_room state for verification.
- No rehearsal-only wording or fixture artifacts.

## 10) Go / no-go states

- **Ready to reset**:
  - explicit approval phrase confirmed
  - scenario/template files present
  - no real players already in game
- **Reset done, waiting roster**:
  - gameplay reset complete
  - roster cleared and rebuild setup pending
- **Rebuild done, waiting final acceptance**:
  - all automated checks pass
  - manual acceptance still pending
- **No-go**:
  - scenario/questions unavailable
  - required roles absent after setup
  - reset/delegations fail or leave unrecoverable state

## 11) Required approval phrase

- Proceed only after explicit user confirmation:  
  `APPROVE LIVE01 RESET FOR REAL SETUP`

