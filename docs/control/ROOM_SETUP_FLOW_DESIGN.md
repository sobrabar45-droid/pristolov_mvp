# ROOM_SETUP_FLOW_DESIGN.md

## 1) Purpose

The game already has a mostly multi-room data model, but room creation and scenario loading are still manually assembled from separate routes and scripts.  
Before scaling to franchise/multi-city, we need an operator-safe Room Setup / Loader foundation so each new room can be prepared consistently without developer intervention.

## 2) Operator goal

Create and prepare a new game room safely and repeatably with one controlled flow:
- choose a unique room identifier,
- bind scenario and rules,
- prepare registration channels,
- generate operational links,
- run smoke checks,
- mark the room ready for guests.

The target is zero ambiguity for non-developer operators.

## 3) Minimal room setup flow (required)

1. Choose `room_code` and room metadata.
2. Create game record (`Game`) for that room.
3. Select scenario/template (eg. `season1_mvp_live_v2`) for the room.
4. Apply scenario to room.
5. Configure economy parameters:
   - base conversion (currently 500 ₽ = 1 золото),
   - starting gold behavior (manual mode 10 / random mode +1 bonus = 11).
6. Configure House registration mode:
   - manual house choice,
   - random/blind draw,
   - mixed mode if supported.
7. Open registration workflow:
   - publish one-QR route for room,
   - verify invite/join flow for additional House members.
8. Generate and verify operational URLs:
   - One-QR house creation URL,
   - Master screen URL,
   - TV URL,
   - cashier URL,
   - player registration URL.
9. Run automated smoke checks for room isolation.
10. Mark room as `ready_for_registration` / ready state.

## 4) Required operator inputs

- `room_code` (required, unique)
- city/location and contact person
- target date/time
- scenario/template
- registration mode (manual/random/mixed)
- economy rule (must be explicit)
- starting gold policy:
  - manual: 10,
  - random: 11
- question bank source (existing template / approved replacement set)
- house policy:
  - all 10,
  - limited,
  - on-demand.

## 5) Safety rules (hard requirements)

- Never default-destruct LIVE01.
- Never run reset or destructive flow without explicit room code confirmation.
- Never apply scenario globally; always target explicit room.
- No cross-room player leakage:
  - player token scope must resolve only inside selected room.
- No shared mutable state between rooms.
- Smoke checks must include room isolation checks before opening guest entry.
- Never create new runtime links to wrong room (especially one-QR fallback defaults).

## 6) Validation and smoke checklist

For each new room:
- Room exists and `room_code` matches expected value.
- Scenario/template applied to this room.
- Pre-registration player/house count is 0 (or expected baseline in migration/reuse mode).
- One-QR URL opens in room mode with expected `game_code`.
- Master URL opens room-specific master screen.
- TV URL opens room-specific state.
- Cashier URL opens room-specific room page.
- Registration creates House in selected room.
- Player token opens expected room/player page.
- LIVE01 (or any active room) remains isolated and unaffected.

## 7) Proposed MVP implementation options

A. **CLI/utility helper script**
- Command-like interface for room create + scenario apply + URL generation + smoke checks.
- Fast to ship, easy to run in terminal/automation.

B. **Dev/operator web screen**
- Operator-facing screen for room provisioning.
- Better operator ergonomics, slower to implement safely.

C. **Hybrid (recommended MVP)**
- CLI for deterministic bootstrap + later operator screen for visibility and reuse.
- Avoids broad operator UI risk in first release.

## 8) Recommended MVP

- Start with **CLI/helper** or dev-only operator command flow:
  - deterministic outputs,
  - explicit room code,
  - scenario apply,
  - URL generation,
  - smoke summary.
- Add generated URL/QR artifacts to handoff package.
- Keep one-click public franchise admin out of first release.

## 9) Future franchise layer

After MVP is stable:
- city/operator accounts and role-based access,
- room ownership and accountability,
- scoped operator permissions per room/city,
- room logs/audit trail,
- per-room configuration profiles,
- multi-room dashboard with health + quick smoke status.

## 10) Candidate next implementation task

Immediate next implementation task after doc approval:
**Room setup CLI/helper MVP**
- create a non-destructive setup command path,
- support `create|apply-scenario|generate-urls|smoke|mark-ready`,
- enforce explicit room confirmation for destructive actions.

