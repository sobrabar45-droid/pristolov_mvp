# Treasurer Shop V1.2 production rollout plan

## Commits to deploy

- `dc9c17a` Add Treasurer Shop request queue
- `0a03967` Add Treasurer Shop request confirmation
- `4aa61c3` Add Treasurer Shop V1.2 confirmation checkpoint

## Affected surfaces

- `player_room` Treasurer section:
  - visible only to treasurer role
  - safe shelf request buttons (`author_tea`, `lemonade_02`, `sobranie_pizza`, `anna_pavlova`)
  - request submission only (no gold spend until confirmation)
- `cashier_gold_desk`:
  - pending treasurer shop request queue
  - “Ожидает подтверждения” status
  - **Заказ принят** confirmation action
- `Master/TV` event feed:
  - event appears on confirmation path
  - no event on request creation

## Deployment sequence

1. Ensure local tree is clean (`git status --short` is clean).
2. Push:
   - `git push origin main`
3. On VPS:
   - `git fetch`
   - `git pull --ff-only`
4. Validate app bytecode:
   - `python -m compileall app -q`
5. Restart app service:
   - `systemctl restart pristolov`
6. Run production smoke checklist (below).

## Production smoke checklist

1. Treasurer flow
   - open player room for a treasurer
   - verify **«Харчевня / Магазин»** is visible
   - verify safe shelf is visible
2. Request creation
   - create `author_tea` request
   - verify response `ok=true`
   - verify house gold does not change on create
3. Cashier queue
   - open ` /cashier/gold-desk/{room_code}`
   - verify pending request appears
4. Confirmation
   - confirm request via **Заказ принят**
   - verify `ok=true`
   - verify house gold decreases by cost
   - verify request removed from pending
   - verify house transaction count increases
5. Event visibility
   - verify Master recent events contains purchase event
   - verify TV recent events contains same semantic event
6. Insufficient gold branch (if safe test data allows)
   - attempt confirmation with insufficient house gold
   - verify `ok=false`
   - request remains pending
   - no transaction created
7. Regression controls
   - existing cashier `+1` and check-amount modes still work

## Rollback/fallback

- If production queue/confirmation is unstable:
  - switch to operator-mediated Treasurer Shop flow (`/dev/treasurer-shop/{room_code}`)
- If cashier flow is blocked:
  - keep using manual `+1` grant in cashier as fallback

## Do-not-touch / blocked until next contour

- Do not expose/enable alcohol / 18+ shelf in this rollout.
- Do not introduce new model/table in V1.2.
- Do not patch Court/Final.
