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

Treasurer Shop V1.1 runtime patch is complete.

Decision:
- V1 Treasurer Shop remains separate operator/dev screen at `/dev/treasurer-shop/{room_code}`.
- player_room will not get Treasurer Shop purchase buttons in this phase.
- Future player_room work may add only informational discovery, but no runtime action buttons are planned in this task.

Next task:

Next task:

- Select next narrow Treasurer Shop runtime/product candidate (audit-only).
- Keep `codex` recommendation doc-driven.
- Candidate is for decisioning only: scope, legality wording, and implementation prerequisites.
- No runtime patch in this task.

Recommended model:
- Audit-only for next narrow candidate (no runtime changes in this task).

### Decision mode

No full runtime rollout now; candidate-limited implementation only.
