# Player Room Support Roles UX Production Rollout Result

## Deployed commits

- `53c7cf4` Polish Maester and sworn player room copy
- `8524ef0` Add support roles UX polish checkpoint
- `a5e9cae` Fix player room phase label encoding

## VPS rollout

- `VPS pull` completed: local/production state advanced from commit `8524ef0` to `a5e9cae`.
- `compileall app` passed on VPS before restart.
- `pristolov` service restarted successfully.
- `pristolov` service is active/running.

## Smoke summary (production)

- `/master` endpoint check: HTTP 200
- `/tv-mode` endpoint check: HTTP 200
- `/cashier/gold-desk/LIVE01` endpoint check: HTTP 200

## What was included

- Support-role UX copy fixes for `maester` and `house_sworn` in player room are included.
- Player room phase label encoding fix for `last_whisper` label was included as well (`a5e9cae`).

## Next step

- Complete browser visual smoke for:
  - `maester` copy rendering
  - `house_sworn` copy rendering
  - player-room phase label readability and “Текущая фаза” value
- Decide the next contour after visual confirmation.

## Next control task

- No further runtime patch is planned in this rollout document.
- Transition to: visual verification and next contour selection.
