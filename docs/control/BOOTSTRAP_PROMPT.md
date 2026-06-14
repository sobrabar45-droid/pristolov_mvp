# BOOTSTRAP_PROMPT

## Goal
P1 Treasurer Shop V1 — spend gold on bar shelf actions.

## Initial context
- `Gold Desk` exists and is in scope by checkpoint `2537910`.
- Next runtime patch: Gold Spend event-effect layer.

## Exact bootstrap checklist
1. `git status --short`.
2. If tree dirty — stop before patch.
3. Read/verify:
   - `app/services/gold_service.py`
   - `app/routes/gold.py`
   - `app/routes/player.py`
   - `app/routes/dev.py`
   - `app/services/master_state_service.py`
   - `app/templates/master_screen.html`
   - `app/templates/treasurer_shop.html`
   - `app/templates/player_room.html`

## Runtime requirements to follow
- Add screen route: `GET /dev/treasurer-shop/{room_code}`.
- Add action route: `POST /player/treasurer-shop/{player_id}/purchase`.
- `gift_to_ally` validation:
  - requires `target_house_id`
  - same game
  - active alliance check
- Use existing gold spending runtime.
- Emit event to Master/TV with readable text.

## Required output
- `app/templates/treasurer_shop.html` created.
- Small master link: `Открыть Treasurer Shop`.
- No new models, no refactor, no commit.
