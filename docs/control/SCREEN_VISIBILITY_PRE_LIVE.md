# Pre-live screen visibility matrix

## Cashier links

- Route: `/cashier/gold-desk/{room_code}`
- Audience: Cashier device/tablet
- Protection: App middleware prefix `/cashier` (requires `X-Admin-Token` when `ADMIN_ROUTE_TOKEN` is set) + production proxy guard
- Safe to share: **Yes (authorized cashiers only)**
- Notes:
  - This is the intended tablet-facing route for gold assignment.
  - Keep credentials/instructions separate and controlled.
  - Use the route, not `/dev`, for live operations.

- Route: `/gold/houses/{house_id}/grant`
- Route: `/gold/houses/{house_id}/grant-from-check`
- Audience: Cashier/admin API usage only
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/gold` + production guard chain
- Safe to share: **No**
- Notes:
- Do not share direct API endpoints with any user-facing links.

## Host/operator links

- Route: `/dev/master-screen/{room_code}`
- Audience: Host/operator/admin
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Full control UI with operational actions.

- Route: `/dev/scenario-admin`
- Audience: Host/operator/admin/developer
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Internal scenario import/admin tool.

- Route: `/dev/treasurer-shop/{room_code}`
- Audience: Host/operator/admin
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Internal treasurer operator surface.

- Route: `/dev/gold-desk/{room_code}`
- Audience: Host/operator/admin
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Internal gold desk route; not meant for tablet cashier workflow.

- Route: `/` (home)
- Audience: Public/ops
- Protection: none
- Safe to share: **Yes**
- Notes:
  - Public landing page only.

- Route: `/health`
- Audience: Public/ops
- Protection: none
- Safe to share: **Yes**
- Notes:
  - Infrastructure health check.

## TV/projector links

- Route: `/dev/tv-mode/{room_code}`
- Audience: Host/operator/TV operator
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - TV mode control endpoint path is under operator namespace.

## Player links

- Route: `/player/me/{player_token}`
- Audience: Player (tokenized session)
- Protection: tokenized request flow
- Safe to share: **Conditional / private**
- Notes:
  - Share only as player-private link; do not publish.

- Route pattern: `/house/{invite_code}/player/{player_id}`
- Audience: Player
- Protection: tokenless page route in game templates
- Safe to share: **Conditional / private**
- Notes:
  - Share only through invitation/distribution channels expected for players.

## Internal/admin-only routes

- Route: `/dev/host-round*`
- Audience: Host/operator
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Runtime phase and host control operations.

- Route: `/dev/court/*`
- Audience: Host/operator
- Protection: `PROTECTED_ROUTE_PREFIXES` includes `/dev`
- Safe to share: **No**
- Notes:
  - Court runtime controls.

- Route: `/scenario-admin`
- Audience: Host/operator/admin
- Protection: `/dev` mount/prefix + admin token when enabled
- Safe to share: **No**
- Notes:
  - Internal developer admin tool.

## Never-share routes

- `/dev/*` (all operator internals)
- `/gold/*` (gold management APIs)
- `/player/*` raw endpoints (use only in authenticated private player context)

## Pre-live smoke checklist

1. Confirm production URL path availability:
   - `https://pristolov.ru/cashier/gold-desk/{room_code}` loads for authorized cashier.
2. Confirm `/gold/*` endpoints only used from cashier UI and not shown as links.
3. Confirm `/dev/*` links are withheld from players/guests and public docs.
4. Confirm player links are private and distributed only to intended player group.
5. Confirm proxy+app protection for `/cashier`, `/dev`, and `/gold`.
6. Confirm no token/API secrets appear in UI, logs, screenshots, or pasted docs.
7. Final role check:
   - no route in live player briefing points to operator/internal namespaces.
