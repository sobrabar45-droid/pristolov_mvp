# LIVE01 real-game cleanup and rebuild plan

## 1. Current state summary (reality check)

- LIVE01 is currently a role-complete rehearsal fixture from `0112e3b`.
- It contains rehearsal artifacts and is not clean for real players.
- This task is docs-only: it prepares the safest cleanup + rebuild sequence.
- **No reset or DB mutation is performed here.**

## 2. Pre-reset evidence checklist

Run these checks before any destructive action:

- Git/repo evidence:
  - `git status --short`
  - `git rev-parse --short HEAD`
- Build/service readiness:
  - `python -m compileall app -q`
  - VPS service status: `systemctl status pristolov --no-pager`
- LIVE01 state snapshot (counts):
  - houses
  - players
  - role counts
  - HouseGoldTransaction count
  - GameDeal count
  - active phases
  - expeditions
  - map visits
- Template/scenario presence:
  - `app/game_templates/scenarios/season1_mvp_live_v2.json` exists/readable
  - `app/game_templates/season1_core_v1/*.yaml` exists/readable

Known current rehearsal remnants to remove (from docs/audits):
- test-like gameplay runtime objects
- treasurer shop technical requests
- test role/action state and history trails

## 3. Reset execution plan (exact order; do not execute yet)

1. `POST /dev/games/LIVE01/reset-runtime`
2. `GET /dev/reset-delegations/LIVE01`

Order rationale:
- first clear runtime simulation artifacts,
- then optionally clear houses/players/financial rows for real rebuild.

Endpoint paths in code:
- `app/routes/dev.py` (`/dev/games/{room_code}/reset-runtime`)
- `app/routes/delegation.py` (`/dev/reset-delegations/{room_code}`)

## 4. Expected destructive effects and post-reset state

`reset-runtime` (destructive):
- clears GameAssignment, GameHostRoundQuestion, GameExpedition, GameExpeditionMember
- clears GameDeal (including treasurer request deals)
- clears GameDuel
- clears GameHostRound and active phases
- clears GameMapVisit and GameMapState
- does not clear Role/Game/Scenario metadata
- does not clear Player/House
- does not clear HouseGoldTransaction / GameHouseTower

`reset-delegations`:
- clears Player
- clears House
- clears HouseGoldTransaction
- clears GameHouseTower

Expected after both calls:
- LIVE01 remains as a game shell,
- no previous roster,
- no technical rehearsal traces in gameplay/runtime,
- manual rebuild required.

Rollback limitation:
- no automatic rollback; treat as irreversible without backup/restoration plan.

## 5. Real rebuild required inputs (user/operator)

### 5.1 Official house roster
- Дом Волка
- Дом Башни
- Дом Солнца
- Дом Меча
- Дом Свитка
- Дом Печати
- Дом Ключа
- Дом Огня
- Дом Ворона
- Дом Чаши

### 5.2 Players and roles
- Player names / attendance list
- House-to-player assignment
- Role assignment to cover these role codes:
  - `lord_lady`
  - `treasurer`
  - `diplomat`
  - `whisper_master`
  - `maester`
  - `house_sworn`

### 5.3 Resource baseline and scenario decisions
- starting gold/resource values (default behavior: baseline as configured for role start)
- confirm use of scenario `season1_mvp_live_v2`
- confirm whether court question import is done before or after first player onboarding

## 6. Rebuild strategy

### What can be automated
- scenario/template verification after reset,
- role/action smoke per route/API matrix,
- cashier/master/tv/player open checks.

### What is manual
- roster collection and role map,
- final house naming and player-card mapping,
- opening sequence for live session.

### No new script now
- Avoid new model/script changes at this stage.
- Existing helpers are only for existing workflows:
  - `scripts/bootstrap_live01_vps.py` (bootstrap control)
  - `scripts/rehearsal_live01_role_e2e.py` (rehearsal-only; do not use for real setup).

## 7. Question / scenario handling decision

Current scenario base:
- `season1_mvp_live_v2` from `app/game_templates/scenarios/season1_mvp_live_v2.json`
- 10 rounds and 13 questions configured in scenario payload.

Question bank context:
- draft extraction shows 45 clean court questions available
- external source folder has DOCX + 22 media files and was not imported

Recommendation:
- **Prefer deferred question import/replacement until after real roster is confirmed**, unless organizers request pre-build replacement earlier.
- Keep `season1_mvp_live_v2` active for this cleanup/rebuild step.

## 8. Post-rebuild automated smoke checklist

Run and confirm PASS before real players:
- `GET /cashier/gold-desk/LIVE01` (200, protected path)
- `GET /dev/master-screen/LIVE01` (200)
- `GET /dev/tv-mode/LIVE01` (200)
- player-room open for each required role set where test links are available
- player room and cashier contain no `/dev` links
- economy still reads `500 ₽ = 1 золото`
- no pending treasurer shop requests by default
- no rehearsal-only deals/delegations/expeditions should be present
- treasury request confirmation still spends on confirm only (no pre-spend)

## 9. Final manual acceptance (human verification)

- one player-room check per key role (`lord_lady`, `treasurer`, `diplomat`, `whisper_master`, `maester`, `house_sworn`)
- Master screen and TV are readable and stable
- cashier Gold Desk works for manual +1 and check-amount flow
- moderator flow and cheat sheet align with real-room setup

## 10. Go/No-go and approval gate

- **Ready to reset**: operator approval phrase received + required input package ready.
- **Reset done, waiting roster**: destructive cleanup done, setup pending.
- **Rebuild done, waiting acceptance**: checks pass, manual role spot-check pending.
- **No-Go**: missing scenario/questions, required roles, or approval condition not met.

Proceed only after exact phrase:

`APPROVE LIVE01 RESET FOR REAL SETUP`

No reset is executed by this plan.
