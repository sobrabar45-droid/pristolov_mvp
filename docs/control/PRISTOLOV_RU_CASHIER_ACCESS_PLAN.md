# PRISTOLOV.RU Cashier Access Plan

## Target URL
- Public cashier page: `https://pristolov.ru/cashier/gold-desk/{room_code}`
- Example for LIVE event: `https://pristolov.ru/cashier/gold-desk/LIVE01`

## Protection boundaries
- Protected upstream paths: `/cashier` and `/gold`
  - `/cashier` serves the standalone cashier screen.
  - `/gold` performs cashier grant operations.
- Blocked/internal path: `/dev`
  - Do not expose `/dev` in public ingress.
  - Do not link or redirect from cashier flow to `/dev` routes.

## Required runtime environment
- App server must have `ADMIN_ROUTE_TOKEN` set (non-empty) to keep app-level guard active for `/cashier` and `/gold`.

## Deployment model (V1)
- Public domain + HTTPS on pristolov.ru.
- Reverse proxy must authenticate cashier access before forwarding `/cashier` and `/gold`.
- Reverse proxy must inject or forward upstream header:
  - `X-Admin-Token: <ADMIN_ROUTE_TOKEN>`
- `/gold` and `/cashier` should be restricted by proxy policy (Basic Auth + optional allowlist/VPN) and app middleware.
- `/dev` must remain blocked/not publicly exposed.

## Token secrecy
- `ADMIN_ROUTE_TOKEN` must never appear in:
  - HTML
  - JavaScript source
  - URLs
  - QR codes
  - screenshots/logs/screenshare URLs

## Optional hardening
- Add IP allowlist/VPN for cashier devices in addition to proxy auth.
- Keep proxy logs access-level only; avoid logging full headers with secrets.

## Tablet smoke checklist (pristolov.ru)
1. Open `https://pristolov.ru/cashier/gold-desk/LIVE01` on tablet.
2. Confirm access requires operator/cashier proxy authentication and succeeds after auth.
3. Confirm page loads without `/dev` links.
4. Perform a sample grant via check:
   - open a valid house
   - enter RUB amount and submit
   - verify gold increased by `amount_rub / 500`.
5. Verify `GET /gold/houses/{house_id}/transactions` and `POST /gold/houses/{house_id}/grant-from-check` fail without proxy auth and succeed with it.
6. Verify `GET /dev/gold-desk/LIVE01` is inaccessible from public path.

## Rollback if cashier access breaks live
- Pause cashier operations immediately.
- Switch to owner laptop fallback if available.
- Keep game state unchanged; do not run any reset/import/seed endpoints.
- Remove proxy change if needed, restore previous proxy config.
- Verify database backup exists before retrying changes.
- Re-test proxy auth + token forwarding before resuming tablet use.
