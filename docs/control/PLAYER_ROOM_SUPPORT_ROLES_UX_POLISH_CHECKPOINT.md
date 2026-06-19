# Player Room Support Roles UX Polish Checkpoint

## Commit

- `53c7cf4` Polish Maester and sworn player room copy

## What was changed

- Updated only template copy in `app/templates/player_room.html`.
- Scope touched two support-role areas:
  - `maester` role description and “Что делать сейчас”.
  - `house_sworn` role description and “Что делать сейчас”.
  - no-active-assignment empty-state copy in the assignments block for both roles.

## Why this patch was needed

- A prior role audit identified `maester` and `house_sworn` as weak/empty on player-facing UX.
- This patch closes that gap with clearer role intent and phase-locked non-error messaging:
  - Maester is presented as an advisory/support role for logic, clues, and timing.
  - House Sworn is positioned as active participant through expedition/discussion/duel support, even when no personal button is available.

## Verification

- `python -m compileall app -q` passed.
- `rg -n "/dev" app/templates/player_room.html` returned no matches.
- Final status after checkpoint was clean.

## Exact scope and non-goals

- No backend changes.
- No new endpoints.
- No mechanic changes.
- No gold/resource effects.
- No Court/Final/Treasurer Shop/Treasurer Shop runtime logic changes.
- Text-only UX polish only.

## Next step

- Decide next step for deploy/smoke and production rollout timing in control docs.
- No new runtime patch is planned at this checkpoint.
