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

Role/player action surface audit completed

Findings:
- player_room exposes most role action surfaces, including treasurer deal confirmations.
- Treasurer Shop is isolated in `/dev/treasurer-shop/{room_code}` (separate screen).
- No runtime patch was made for this change.

Next task:

Decide Treasurer Shop entrypoint strategy

Options:
- A) Keep Treasurer Shop as operator/dev screen and document the intentional split.
- B) Expose Treasurer Shop entry/discovery in player_room for treasurer role.

Recommended model:
- Codex 5.3 for decision/docs work.
- Codex 5.5 only after entrypoint strategy is chosen.

### Decision mode

No runtime patch now; architecture/product decision only.
