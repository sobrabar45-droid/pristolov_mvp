# NEXT_CODEX_TASK

## Treasurer Shop V1: CLOSED

Implemented and smoke-verified in these commits:

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
- `2832eaa` Add Treasurer Shop V1.1 bar shelf items
- `50d2a01` Add Treasurer Shop V1.1 checkpoint
- `3bc9e5f` Add standalone cashier Gold Desk screen
- `f360c49` Add cashier Gold Desk checkpoint

The current state marks Treasurer Shop V1 implementation as complete.

## Cashier Gold Desk status

Standalone cashier Gold Desk runtime closed in:
- `3bc9e5f` Add standalone cashier Gold Desk screen.
- `f360c49` Add cashier Gold Desk checkpoint.

## Cashier rollout status

- PRISTOLOV.ru cashier rollout is closed in production (`/cashier/gold-desk/{room_code}`).
- Nginx `/cashier/` protection is active; `/dev` remains internal.
- Next work is audit-only; no runtime patch now.

## Next recommended task

- Support-role UX polish for `maester`/`house_sworn` was completed (commits: `53c7cf4`, `8524ef0`, `a5e9cae`).
- Production rollout for this block is complete.
- Pre-live full readiness audit completed (contour A in `NEXT_CONTOUR_SELECTION_AFTER_SUPPORT_ROLES_UX.md`) with findings in `PRE_LIVE_READINESS_AUDIT_AFTER_TREASURER_SHOP_V1_2.md`.
- Result: **conditional no-go pending production smoke/protocol execution** (network/access not available from audit environment).
- Next step (no runtime patch): execute `PRE_LIVE_SMOKE_EXECUTION_PROTOCOL.md` on the real pre-live room and publish final go/no-go decision.
- Keep manual visual acceptance for final check only after automated smoke and protocol pass.



