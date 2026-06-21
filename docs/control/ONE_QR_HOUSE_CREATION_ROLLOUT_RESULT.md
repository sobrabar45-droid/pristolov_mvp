# One QR House Creation Rollout Result

## Implemented commits

- `0ef82df` Add one QR House creation flow
- `749203d` Add printable create House QR card

## Rollout target URL

- `https://pristolov.ru/delegation/start?game_code=LIVE01&entry_mode=random`

## User-confirmed smoke result

- QR is working and opens House creation on pristolov.ru.
- Expected behavior confirmed:
  - opens House creation screen,
  - `game_code=LIVE01` is prefilled,
  - `entry_mode=random` is selected,
  - page shows “Жребий даёт +1 золото”,
  - Lord/Lady can create a House and then share lobby/join link with players.

## Current live entrance workflow

- Entrance uses one shared QR card/URL.
- Route: `/delegation/start?game_code=LIVE01&entry_mode=random`.
- Flow:
  - scan QR,
  - create House as first Lord/Lady,
  - choose manual or random/jrbey draw mode,
  - receive house invite link/code,
  - share with other House players.

## What is done

- Runtime code for one-QR entry is implemented and smoke-tested previously.
- Public printable card created in `docs/print/` with required copy and URL.

## Not yet done

- LIVE01 is still not cleaned for real-game live roster (currently not converted to final game-ready state).
- No additional runtime changes pending in this block.

## Next step

- Collect real roster / house setup inputs from user.
- Execute LIVE01 real cleanup/rebuild only after explicit approval phrase:
  `APPROVE LIVE01 RESET FOR REAL SETUP`.
- After approval and rebuild, run final pre-live automated smoke and manual acceptance.
