# CHECKPOINT_CASHIER_GOLD_DESK

## Commit
- `3bc9e5f` Add standalone cashier Gold Desk screen

## Scope
- Runtime files changed:
  - `app/main.py`
  - `app/routes/cashier.py`
  - `app/templates/cashier_gold_desk.html`

## Implemented runtime
- Added `admin` route protection for `/cashier`:
  - `app/main.py`: `PROTECTED_ROUTE_PREFIXES = ("/dev", "/gold", "/cashier")`
- Added dedicated cashier route:
  - `GET /cashier/gold-desk/{room_code}`
- Added cashier-only template:
  - `app/templates/cashier_gold_desk.html`

## Protection model
- `/cashier` and `/gold` are protected by middleware token check when `ADMIN_ROUTE_TOKEN` is set.
- `/dev` remains internal/developer path and is not the cashier entrypoint.

## Smoke results
- `python -m compileall app -q`: passed.
- With `ADMIN_ROUTE_TOKEN` unset:
  - `GET /cashier/gold-desk/LIVE01` -> `200`
  - no `/dev` links in cashier template output
  - `POST /gold/houses/{house_id}/grant-from-check` with `amount_rub: 500` -> `ok=true` (`gold 0 -> 1`)
  - `GET /dev/gold-desk/LIVE01` still `200`
- With `ADMIN_ROUTE_TOKEN` set:
  - `/cashier/gold-desk/...` without token -> `403`
  - `/gold/...` without token -> `403`
  - `/cashier/gold-desk/...` with `X-Admin-Token` -> `200`

## Deployment caveat
- Browser does not auto-send `X-Admin-Token` for normal page navigation/FETCH.
- For pristolov.ru safe external access, use one of:
  - reverse-proxy auth check,
  - reverse-proxy header injection,
  - or trusted-network controls (VPN/IP allowlist).
- For now, no app-level cashier login implemented.

## Next recommended task
- Verify pristolov.ru deployment/proxy access path before any new runtime changes.
- Keep as docs/audit-first task: finalize external access policy and guard mode for production use.
