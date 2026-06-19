# Treasurer Shop V1.2 Request Queue Checkpoint

## Commit and Scope

Implemented in commit `dc9c17a`:

- `Add Treasurer Shop request queue`
- Runtime files:
  - `app/routes/player.py`
  - `app/routes/cashier.py`
  - `app/templates/player_room.html`
  - `app/templates/cashier_gold_desk.html`

## Current V1.2 Request Lifecycle (implemented)

- Treasurers open `player_room` and see the new `Харчевня / Магазин` section.
- Treasurers can submit safe-shelf requests:
  - `author_tea` — 3 gold
  - `lemonade_02` — 2 gold
  - `sobranie_pizza` — 6 gold
  - `anna_pavlova` — 2 gold
- Request endpoint creates `GameDeal` with `offer.type = "treasurer_shop_request"` and status `pending`.
- No cash deduction happens at request creation time.
- Cashier page shows pending queue rows with:
  - House
  - Item
  - Cost
  - Status label “Ожидает подтверждения”
- Confirm/reject execution is not implemented in this patch.

## Smoke summary

- `python -m compileall app -q` passed.
- Treasurers can open `player_room` and see the shop section (safe shelf visible).
- Request for `author_tea` returned `ok=true` and `request_id=90`.
- House gold did not change on request creation (`29 -> 29` in test check).
- Gold transaction ledger count unchanged on request creation (`22 -> 22`).
- `/cashier/gold-desk/LIVE01` shows pending row with:
  - House
  - `Авторский чай`
  - `3 золота`
  - status `pending` / “Ожидает подтверждения”
- Non-treasurer request creation blocked with role error message.
- Cashier manual `+1` and check-amount modes remain visible.
- No `/dev` links are shown in player shop or cashier queue sections.

## Explicit non-goals for this commit

- No cashier confirmation/rejection yet.
- No gold spend at request creation.
- No `HouseGoldTransaction` entry for request creation.
- No change to `Court/Final`, `Treasure Shop operator screen`, `player_room` non-shop sections, or cash desk internals.

## Next step

- Next runtime patch: Treasurer Shop V1.2 cashier confirmation flow.
- Cashier confirmation should:
  - validate pending `treasurer_shop_request`
  - spend gold only on confirmation
  - create `HouseGoldTransaction` for confirmed spend
  - transition request status accordingly
- No new model/table for this next V1.2 batch.
