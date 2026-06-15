# Migration Checkpoint: Treasurer Shop V1.1

## Current repo state
- Project: `D:\Projects\pristolov_mvp`
- Working tree before migration checkpoint update: clean.
- Active flow: Treasurer Shop is operator-mediated at `/dev/treasurer-shop/{room_code}`.
- No `player_room` purchase buttons were added in V1 or V1.1.
- Last migration/runtime work: `50d2a01 Add Treasurer Shop V1.1 checkpoint`.

## Completed commits
- `2832eaa` Add Treasurer Shop V1.1 bar shelf items
- `50d2a01` Add Treasurer Shop V1.1 checkpoint
- Historical context (Treasurer Shop):
  - `5c92d76` Add Treasurer Shop gold spend runtime
  - `16833cf` Add Treasurer Shop V1 checkpoint
  - `52bab30` Align gold formula wording
  - `94fdfc7` Show Treasurer Shop events on master screen
  - `4be1656` Update Treasurer Shop event feed checkpoint
  - `ba99c6f` Update next Codex task after Treasurer Shop V1
  - `2627254` Update next task after role action surface audit
  - `9111c84` Record Treasurer Shop entrypoint decision
  - `c78c9c9` Document Treasurer Shop bar shelf prices
  - `153d319` Select Treasurer Shop V1.1 bar shelf candidates

## What is closed
- Treasurer Shop V1 full surface is closed:
  - `set_bar` — 5
  - `giraffe` — 10
  - `gift_to_ally` — 15
- Treasurer Shop V1.1 bar/social-only batch is closed:
  - `author_tea` — 3
  - `lemonade_02` — 2
  - `sobranie_pizza` — 6
  - `anna_pavlova` — 2
- Alcohol/legal-sensitive items remain deferred:
  - `champagne_premier`
  - `tincture_set`
  - `shihan_beer_giraffe`
  - `beer_set_any`
- `gift_to_ally` behavior is unchanged (alliance required, +1 influence each).
- Smoke checks passed for new items and regressions.

## What must not be touched in this stage
- No runtime/template edits.
- No Court/Final or diplomacy core changes.
- No player_room purchase flow changes.
- No new DB models/tables.
- No gold core architecture changes.

## Next recommended task
- Audit-only next narrow candidate selection for Treasurer Shop roadmap.
- No runtime patch in this handoff cycle.

## Bootstrap instruction for new chat
1. `git status --short`.
2. Read control docs in order:
   - `docs/control/CURRENT_STATE.md`
   - `docs/control/DECISIONS.md`
   - `docs/control/OPEN_TASKS.md`
   - `docs/control/CHANGELOG.md`
   - `docs/control/MIGRATION_CHECKPOINT_TREASURER_SHOP_V1_1.md`
   - `docs/control/NEXT_CODEX_TASK.md`
   - `docs/control/TREASURER_SHOP_BAR_SHELF.md`
   - `docs/control/TREASURER_SHOP_BAR_SHELF.md` (for candidate baseline)
3. Confirm that next task is audit-only and document-driven.
4. Keep next runtime scope restricted to documentation and control unless a new explicit runtime request arrives.
