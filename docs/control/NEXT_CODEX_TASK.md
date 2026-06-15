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

The current state marks Treasurer Shop V1 implementation as complete.

## Next recommended task

Standalone Gold Desk access strategy is selected for V1.

Decision:
- Use external cashier entrypoint `GET /cashier/gold-desk/{room_code}` on pristolov.ru.
- Keep `/dev/gold-desk/{room_code}` internal-only (do not expose as cashier path).
- `/cashier` and `/gold` must be protected by operator-level guard in V1.
- `X-Admin-Token` is not auto-sent by browser requests, so V1 should rely on reverse-proxy auth/allowlist and/or header injection in front of these paths.

Next task:

- Codex 5.5 runtime patch (minimal): add standalone `/cashier` route + protection alignment and cashier-safe Gold Desk template updates.
- No app-level cashier login in this cycle.

Recommended model:
- Access decision and hardening docs: **Codex 5.3**.
- Minimal runtime patch: **Codex 5.5**.

### Decision mode

Do runtime patch only for minimal standalone cashier enablement after docs signoff.
