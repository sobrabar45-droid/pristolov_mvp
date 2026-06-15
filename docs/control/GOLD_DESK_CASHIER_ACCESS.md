# Gold Desk Cashier Access and External Deployment Plan

## 1) Selected V1 strategy
- Standalone tablet entrypoint: `GET /cashier/gold-desk/{room_code}`.
- ` /dev/gold-desk/{room_code}` remains operator/debug path and must **not** be exposed as cashier access.
- This is the recommended path for pristolov.ru external use without local Wi‑Fi.

## 2) Why /cashier needs dedicated protection
- Current browser-based page calls are not protected by default headers.
- `X-Admin-Token` is read by middleware when present, but browsers do not automatically send custom admin tokens unless page/Javascript or reverse-proxy/auth layer injects/configures it.
- Therefore standalone `/cashier` must be guarded through middleware/proxy same level as `/gold` to avoid unauthorized use.

## 3) Route and API access rules (V1)
- Keep `/dev` path internal-only for operator/developer use.
- Protect:
  - `POST/GET` under `/cashier` (at least `/cashier/gold-desk/{room_code}`), and
  - all `/gold/*` grant/adjust APIs.
- Use HTTPS + pristolov.ru domain in front of app.
- Prefer reverse-proxy authentication and/or IP allowlist/VPN to reduce token exposure risk.

## 4) Browser token constraint (important)
- `X-Admin-Token` is not automatically attached by browser navigation on normal public pages.
- For V1 safest posture:
  1) put a reverse-proxy header injection / auth check in front of `/cashier` and `/gold`, or
  2) enforce trusted network (VPN/allowlist) with admin surface restrictions so tablet can reach only approved paths.

## 5) V1 deployment target (preferred)
- pristolov.ru + HTTPS.
- Reverse-proxy guard (auth/basic allowlist or token injection) for `/cashier` and `/gold`.
- `/dev` not publicly exposed.
- No app-level cashier login added in this patch.

## 6) Do-not-do-now
- Do not expose `/dev` publicly.
- Do not weaken `/gold` protection.
- Do not implement app-level cashier/session login yet.
- Do not touch Court/Final/Gold-core architecture in this task.
