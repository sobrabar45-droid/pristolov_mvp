# Pre-live smoke execution protocol (30–60 min before game)

## 0. Preconditions

- Confirm correct room code and exact player count for the session.
- Confirm `pristolov.ru` is reachable from all intended devices (cashier, operator host, TV/projector, players).
- Confirm no deployment/reload is in progress.
- Confirm operator credentials and approved admin access method are available.
- Prepare one known test house in the session for non-destructive verification (prefer a non-critical training game or clearly documented test scenario).

## 1. Cashier screen smoke

- Open `https://pristolov.ru/cashier/gold-desk/{room_code}`.
- Verify auth challenge appears before access when required by infra path.
- Verify page opens successfully after authorization.
- Confirm no `/dev` links exist in page actions/HTML.
- Confirm “Ручное начисление” section is visible.
- Confirm check-amount mode is visible and operational.

## 2. Host/operator smoke

- Open `/dev/master-screen/{room_code}`.
  - Confirm operator can access and page loads.
  - Confirm no obvious broken critical controls.
- Open `/dev/gold-desk/{room_code}`.
  - Confirm internal operator surface is usable by host.
- Open `/dev/treasurer-shop/{room_code}`.
  - Confirm treasury/operator surface is available.

## 3. TV/projector smoke

- Open `/dev/tv-mode/{room_code}`.
- Confirm public display output is readable and updates are expected for current game state.
- Confirm private operator controls are not visible as part of the shared display flow.

## 4. Player flow smoke

- Open player invite/QR entry URL for at least one player.
- Confirm player room opens and renders fully.
- Confirm role/action blocks render (where applicable for role).
- Confirm no operator-only controls are shown in player room for that player role.

## 5. Critical action smoke

- Cashier manual mode:
  - On test house, perform manual `+1` once and confirm only +1 delta if safe for a rehearsal check.
- Treasurer Shop visibility:
  - Confirm the treasurer role surface and items are visible to that role in player room.
  - Do not submit destructive or irreversible game state changes.
- Defer any state-changing actions not required for pre-live readiness.

## 6. Security smoke

- Verify `/dev/*` is blocked without auth.
- Verify `/gold/*` is blocked without auth.
- Verify `/cashier/*` is blocked without auth.
- Scan visible pages/docs:
  - no admin token in URL
  - no token in page body
  - no token in pasted links/screenshots

## 7. Go / No-go decision

Green (GO):
- Cashier screen accessible and functional with expected controls.
- `/dev` and `/gold` blocking and `/cashier` access are confirmed.
- Player room opens reliably.
- TV/projector readable to audience.
- No accidental token exposure in visible UI/docs.

Yellow (GO WITH WATCH):
- Minor cosmetic text/render quirks outside critical controls.
- One non-critical surface unavailable but no impact on game flow.
- Delay/latency issues that do not block core actions.

Red (NO GO):
- Any unresolved block for `/cashier`, `/dev`, or `/gold`.
- Broken player room load.
- Token exposure or public sharing of admin route/API links.
- Any route mismatch between printed operational links and runtime reality.

## 8. Rollback / fallback

- If cashier is unavailable:
  - use local/manual backup process (head cashier role to alternate authorized device) and postpone new cash operations until restored.
- If TV/projector is unavailable:
  - switch to host narration and manual score/state updates per host procedure.
- If player phones fail:
  - continue with offline/manual callouts and restore after reconnection.
