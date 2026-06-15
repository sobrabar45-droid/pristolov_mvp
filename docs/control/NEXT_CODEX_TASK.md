# NEXT_CODEX_TASK

## Treasurer Shop V1: CLOSED

Implemented and smoke-verified in these commits:

- `5c92d76` Add Treasurer Shop gold spend runtime
- `16833cf` Add Treasurer Shop V1 checkpoint
- `52bab30` Align gold formula wording
- `94fdfc7` Show Treasurer Shop events on master screen
- `4be1656` Update Treasurer Shop event feed checkpoint

The current state marks Treasurer Shop V1 implementation as complete.

## Next recommended task

Decide Treasurer Shop entrypoint strategy (V1) completed: Option A chosen.

Decision:
- V1 Treasurer Shop remains separate operator/dev screen at `/dev/treasurer-shop/{room_code}`.
- player_room will not get Treasurer Shop purchase buttons in this phase.
- Future player_room work may add only informational discovery, but no runtime action buttons are planned in this task.

Next task:

Select next runtime candidate:

- Codex 5.5 runtime patch for Treasurer Shop Bar Shelf V1.1.
- Scope-limited implementation: add only these items now:
  - `author_tea` (3 gold, bar/social only)
  - `lemonade_02` (2 gold, bar/social only)
  - `sobranie_pizza` (6 gold, bar/social only)
  - `anna_pavlova` (2 gold, bar/social only)
- Keep V1 runtime unchanged and operator-mediated for all other items.
- Defer alcohol-named items (`champagne_premier`, `tincture_set`, `shihan_beer_giraffe`, `beer_set_any`) and related wording/legal checks to a later candidate.
- Keep `gift_to_ally` as existing political/social action only; not treated as a bar shelf SKU in this batch.

Recommended model:
- Codex 5.5 runtime patch only (first batch, no court/final changes).

### Decision mode

No full runtime rollout now; candidate-limited implementation only.
