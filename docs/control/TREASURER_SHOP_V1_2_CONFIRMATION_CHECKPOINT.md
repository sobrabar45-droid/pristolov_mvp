# Treasurer Shop V1.2 confirmation checkpoint

## Completed commits

- `dc9c17a` Add Treasurer Shop request queue
- `0a03967` Add Treasurer Shop request confirmation

## Scope (V1.2 confirmation flow)

- Treasurer creates pending request from `player_room` (no gold spent yet).
- Cashier queue in `cashier_gold_desk` shows pending Treasurer Shop requests.
- Cashier confirms via **“Заказ принят”**.
- Gold spend happens on confirm only.
- Request status transitions to `completed` after successful confirmation.
- No new model/table introduced.
- `HouseGoldTransaction` is only created on confirmation (not on request creation).
- Runtime behavior currently does not include reject/cancel controls.

## Changed files

- `app/routes/player.py`
- `app/routes/cashier.py`
- `app/templates/player_room.html`
- `app/templates/cashier_gold_desk.html`

## Smoke results

- `python -m compileall app -q` passed.
- Request creation did not spend gold.
  - House gold: `29 -> 29`
  - transaction count: `22 -> 22`
- Cashier confirmation returned `ok=true`.
  - House gold: `29 -> 26`
  - request status: `completed`
  - transaction count: `22 -> 23`
  - pending queue removed confirmed request.
- Insufficient gold path:
  - confirm returns `ok=false`
  - request stays `pending`
  - gold unchanged
  - transaction count unchanged
- Master and TV recent events show confirmed purchase event.
- Non-treasurer request creation blocked.
- Existing cashier modes still work: manual `+1` and check-amount flow.
- No `/dev` links in changed flows.

## Deferred to next step

- reject/cancel actions for pending requests
- 18+/alcohol/full shelf expansion
- dedicated `ShopRequest` model/table

## Next task

- **Treasurer Shop V1.2 production rollout plan and smoke checklist**
- mode: docs/audit first, no additional runtime patch at this step
