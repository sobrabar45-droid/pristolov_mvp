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
- Current task: pre-live production smoke protocol was prepared as `PRODUCTION_SMOKE_PROTOCOL_PRE_LIVE.md`.
- Codex SSH smoke is pending because SSH execution hung in the Codex environment.
- Current step completed: VPS production smoke protocol was run manually and documented in `PRODUCTION_SMOKE_RESULT_PRE_LIVE.md`.
- Result: conditional GO for surface readiness, no-go for full role/action E2E on LIVE01 because required roles are absent.
- Next recommended task: create or validate a role-complete test room (or approved controlled LIVE01 variant), then execute the role/action E2E sequence from `ROLE_COMPLETE_E2E_SMOKE_PLAN_PRE_LIVE.md` and publish final go/no-go.
- Keep manual visual acceptance for final check only after automated smoke and protocol pass.

## Audit task result (2026-06-20)

- `7af5f18` selected next contour: pre-live readiness audit.
- `9bc6639` and `509c40f` confirmed LIVE01 is role-incomplete (no treasurer/diplomat/whisper_master/house_sworn).
- `84cbf92` documented role-complete E2E plan.
- `d46c820` prepared production smoke protocol and `509c40f` documented production smoke result.
- New reset strategy audit created: `LIVE01_RESET_AND_ROLE_E2E_STRATEGY_AUDIT.md`.

## Immediate next recommended control task

- Do **not execute LIVE01 reset/delegations now**.
- Create/validate a dedicated role-complete test room for destructive E2E setup:
  - `POST /dev/games/{room_code}/reset-runtime`
  - optional `GET /dev/reset-delegations/{room_code}`
  - `POST /dev/games/{room_code}/seed-technical-run`
  - then execute `ROLE_COMPLETE_E2E_SMOKE_PLAN_PRE_LIVE.md` actions.
- After clean test-room E2E, run LIVE01 final non-destructive readiness checks only.
- Then publish final go/no-go before game window.

## LIVE01 role-complete rehearsal E2E completed

- Controlled LIVE01 rehearsal was approved because there are no real players yet.
- Runner added: `scripts/rehearsal_live01_role_e2e.py`.
- Result documented in `LIVE01_ROLE_COMPLETE_REHEARSAL_E2E_RESULT.md`.
- Codex-first E2E result: PASS.
- LIVE01 was intentionally left as a role-complete rehearsal fixture for final browser/manual acceptance.
- Next step: final manual visual acceptance on player/cashier/master/TV screens, then decide whether to keep rehearsal fixture or rebuild LIVE01 for the real player roster.
- No runtime patch is currently recommended.

## Next immediate control task (pre-live, docs-only)

- `42efc36` selected next contour: pre-live readiness audit.
- `9bc6639` completed readiness audit with conditional no-go due LIVE01 role incompleteness.
- `d46c820` prepared production smoke protocol and it is now blocked by external execution constraints.
- `509c40f` documented live production smoke result and role blocker.
- New control artifact created: `ROLE_COMPLETE_E2E_SMOKE_PLAN_PRE_LIVE.md`.
- Next immediate task is to prepare role-complete controlled room and run E2E smoke plan before any other runtime patch.

