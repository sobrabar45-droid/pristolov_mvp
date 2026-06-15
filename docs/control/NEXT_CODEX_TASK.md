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

Select next runtime candidate (documentation decision first): Treasurer Shop bar shelf V1.1 candidate.

- Keep V1 runtime unchanged and operator-mediated.
- Use this as a product decision artifact before any runtime implementation.
- Scope of next candidate:
  - map product labels to stable `action_code` values,
  - define whether each item triggers only bar/social events or also influence changes,
  - prepare public/legal wording checks for alcohol labels.

Recommended model:
- Codex 5.3 docs/audit only.

### Decision mode

No runtime patch now; architecture/product decision only.
