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

Gold Desk access hardening decision (documentation + operator policy).

Decision:
- Keep `Gold Desk` under operator route path model until we define external policy.
- Use `docs/control/GOLD_DESK_CASHIER_ACCESS.md` as the source of truth.
- Next cycle is docs-first audit/selection; no runtime patch in this task.

Recommended model:
- **Codex 5.3** for access decision and docs update.
- **Codex 5.5** only if/when enforcing runtime guard/route hardening (e.g., token-required policy changes or role/session checks).

Next task:

- Choose one deployment mode for V1 cashier use and complete rollout checklist:
  1) local Wi‑Fi rehearsal policy,
  2) temporary tunnel policy, or
  3) VPS/domain HTTPS policy with guard/IP strategy.

### Decision mode

No new runtime patch yet; selection/plan only.
