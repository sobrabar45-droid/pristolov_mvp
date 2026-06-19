# Treasurer Shop V1.2 production rollout result

## Deployed commits

- `dc9c17a` Add Treasurer Shop request queue
- `0a03967` Add Treasurer Shop request confirmation
- `4aa61c3` Add Treasurer Shop V1.2 confirmation checkpoint
- `59e7539` Add Treasurer Shop V1.2 production rollout plan

## VPS rollout result

- Deployed to production via:
  - `git pull --ff-only origin main`
  - VPS `HEAD` became `59e7539`
- `python -m compileall app -q` passed on VPS (or equivalent validation)
- `pristolov.service` restarted successfully and is active/running

## Production smoke result

- `cashier` screen: `200`
- `master` screen: `200`
- `tv` screen: `200`
- `shop_queue`: present
- `accept_button`: present
- `manual_grant`: present
- `dev_links`: none

## Confirmed player/cashier flow state

- Player path:
  - treasurer can open request flow and send shop requests
- Cashier path:
  - pending request queue visible
  - **«Заказ принят»** action present
  - manual +1 and check-amount cashier paths still available
- Safety/event expectations:
  - no `/dev` links exposed in cashier UI
  - V1.2 request-confirmation behavior is active in production

## Next step

- Create a development checkpoint / learning-pack decision before expanding to the next contour.
- No immediate runtime patch in this step.
