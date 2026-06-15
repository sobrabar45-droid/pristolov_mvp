# Gold Desk Cashier Access and External Deployment Plan

## 1) Current routes
- Gold Desk UI screen: `GET /dev/gold-desk/{room_code}` (served from `app/routes/dev.py`).
- Gold assignment APIs used by the screen: `POST /gold/houses/{house_id}/*` (`grant-from-check`, `grant`, `spend`, etc.) from `app/routes/gold.py`.

## 2) Current access model
- Both `/dev` and `/gold` are operator routes in `app/main.py`.
- They are protected only when `ADMIN_ROUTE_TOKEN` is configured.
  - If `ADMIN_ROUTE_TOKEN` is unset/empty: accessible without token.
- No per-route cashier role/session guard exists in Gold Desk routes/API endpoints themselves.

## 3) Same-Wi‑Fi usage
- Cashier tablet can use Gold Desk on local Wi‑Fi if:
  - it can reach the backend host IP/port,
  - and network policy permits direct access.
- This is the fastest rehearsal mode.

## 4) External access risk assessment
- Exposing `http://host:.../dev/...` and `/gold/...` publicly without token is unsafe because:
  - operations can be triggered without authenticated operator/cashier identity,
  - `/dev` is operationally admin surface,
  - any discovered endpoint and house id can be targeted for unauthorized grants.

## 5) V1 external-access requirements (must be met before external use)
1. Set `ADMIN_ROUTE_TOKEN` (enforced by middleware for `/dev` and `/gold`).
2. Expose through HTTPS (domain or controlled tunnel), not plain LAN-only debug exposure.
3. Prefer network control: VPN and/or IP allowlist for admin devices.
4. Do not publicly expose `/dev` or `/gold` without guard; keep these paths internal-by-default.

## 6) Recommended deployment modes
A) Local Wi‑Fi rehearsal mode (recommended for first tests)
- Use local server IP/port only.
- Requires reachable same-subnet network.
- Keep token check enabled where practical.

B) Temporary tunnel (for controlled testing)
- Use a temporary tunnel only when same-Wi‑Fi is not possible.
- Ensure tunnel users are explicit and rotate quickly.
- Keep `ADMIN_ROUTE_TOKEN` enforced.

C) VPS/domain/HTTPS live mode (recommended for production-like use)
- Deploy with HTTPS and stable domain.
- Keep `ADMIN_ROUTE_TOKEN`, and add network restrictions (VPN/IP allowlist).
- Restrict operator/admin surfaces in reverse-proxy/access policy.

## 7) Do-not-do-now
- Do not implement runtime auth/role hardening in this step (defer to explicit runtime decision task).
- Do not change templates or modify Gold Desk UI behavior.
- Do not touch Court/Final logic.
- Do not patch gold core architecture.
