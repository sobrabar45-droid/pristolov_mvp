# LIVE01 real-game setup readiness audit

## 1) Current LIVE01 rehearsal state (as left after role-complete rehearsal)

Based on `LIVE01_ROLE_COMPLETE_REHEARSAL_E2E_RESULT.md`:

- Room: `LIVE01`
- Houses: `2`
- Players: `10`
- Roles present:
  - `lord_lady`: 2
  - `maester`: 2
  - `diplomat`: 2
  - `treasurer`: 1
  - `whisper_master`: 2
  - `house_sworn`: 1
- Transactions: `5`
- Deals: `2`
- Active phases: `3`
- Expeditions: `1`
- Map visits: `1`
- Treasurer shop queue is technical and was used during rehearsal smoke.

This state is valid for rehearsal coverage but **not** for real-game launch.

## 2) What must be cleaned before real play

Minimum cleanup for real-game transition:

- Active gameplay state from rehearsal:
  - assignments, host round questions, expeditions, expedition members
  - diplomacy/alliance deals, duels
  - active game rounds and phase state
  - map visits and map state
- Treasurer Shop technical artifacts:
  - technical `treasurer_shop_request` deals
- Optional but usually required for a fresh roster:
  - HouseGoldTransaction history
  - houses/players if replacing real participants

Cleanup mechanism behavior:

- `POST /dev/games/LIVE01/reset-runtime` clears most runtime objects and phase rows.
- `GET /dev/reset-delegations/LIVE01` additionally removes `Player`, `House`, `HouseGoldTransaction`, and `GameHouseTower`.

## 3) Real-game setup data required

### Houses / players / roles

- Build real house roster and assign players before opening links.
- Ensure role inventory is present for expected game roles:
  - `lord_lady`, `diplomat`, `maester`, `whisper_master`, `treasurer`, `house_sworn`.

### Questions and scenario

- Live scenario used in current bootstrap: `season1_mvp_live_v2`.
- Scenario location:
  - `app/game_templates/scenarios/season1_mvp_live_v2.json`
  - 10 rounds, 13 questions (current payload snapshot).
- Scenario/template/base-role data location:
  - `app/game_templates/season1_core_v1/*.yaml`
  - key files: `game_template.yaml`, `roles.yaml`, `houses.yaml`, `rounds.yaml`, `round_questions.yaml`, `task_pools_*.yaml`, `events.yaml`.

### Phases / map / expedition / diplomacy / shop

- Start phases should be opened by operator flow after live setup.
- Ensure map/expedition/duel/diplomacy state is clean before first real use.
- Treasurer shop queue and open confirmations should be empty prior to first real player interaction.

### Gold / resources

- Rehearsal ended with non-zero/changed resources (house gold modified by smoke).
- Decide real baseline (typically initial zero or controlled admin adjustment).
- Confirm all houses have expected starting resources before player actions begin.

## 4) Reset strategy audit: can `reset-runtime + reset-delegations` prepare LIVE01?

- `reset-runtime` (dev route) + `reset-delegations` (dev route) are sufficient to wipe rehearsal gameplay + current roster artifacts.
- They are **not** sufficient to configure a real participant roster because no automatic production player registration is performed.
- `seed-technical-run` is rehearsal-only and **recreates a fixed technical fixture**, so it should not be used for real-game onboarding.
- `scripts/bootstrap_live01_vps.py` sets roles/template/scenario but does not create players/houses.

## 5) Recommended safe strategy

Selected safe path (docs-only recommendation): **D**.

1. Explicitly approve LIVE01 rebuild window.
2. Run technical cleanup:
   - `POST /dev/games/LIVE01/reset-runtime`
   - `GET /dev/reset-delegations/LIVE01` (if replacing players/houses).
3. Reconfirm scenario/template:
   - verify `season1_mvp_live_v2` is applied.
4. Build real roster via delegation/lobby and role assignment.
5. Set gold/starting resources and clear/verify treasurer queue baseline.
6. Run automated then manual readiness checks before first live invite.

## 6) Question/scenario readiness section

- Template + scenario sources are present and readable in repo.
- No missing required template or scenario files were found.
- `bootstrap_live01_vps.py` can be used as a controlled bootstrap/validation aid but still requires operator-led roster setup.
- `scripts/rehearsal_live01_role_e2e.py` is not for real game setup (it intentionally performs technical reset/seed).

## 7) Role/house/player setup section

- For real launch, role inventory should be validated after setup via a read-only role-count check.
- House count and membership must match announced player count.
- `house_sworn` and `maester` should be distributed according to expected physical seats, not auto-fixed technical names.

## 8) Automated smoke checklist after rebuild

- `GET /dev/players/LIVE01`, `GET /dev/houses/LIVE01` role/roster inventory.
- Protected route smoke:
  - `/cashier/gold-desk/LIVE01`
  - `/dev/master-screen/LIVE01`
  - `/dev/tv-mode/LIVE01`
  - `/dev/gold-desk/LIVE01`
  - `/dev/treasurer-shop/LIVE01`
- Player-room smoke by role (where possible), plus:
  - no `/dev/` links visible in player/cashier public sections.
- Treasurer Shop V1.2:
  - request creation should not spend gold,
  - confirmation should spend only when executed.
- Gold desk manual +1 and check-amount smoke.

## 9) Final manual acceptance checklist

- Scenario version visible in operator/master screen matches `season1_mvp_live_v2`.
- All players can open role pages with expected sections.
- Cashier and Master/TV states look clean and usable.
- No rehearsal-only or technical artifacts remain.
- Operator confirms first-session flow is clear and no rollback is pending.

## 10) Risks / blockers / unknowns

- `reset-runtime` is destructive and restricted to `LIVE01`/`IRON01`.
- There is no dedicated API route to create a brand-new arbitrary room from scratch.
- Historical event feed retention policy during full cleanup is not fully verified from route layer.
- Any rebuild in LIVE01 should be explicitly approved before execution because there is no automatic "dry-run" mode.

## 11) Recommended next task

- `D` execute LIVE01 cleanup/rebuild after explicit user approval, then publish the final launch-readiness result.


