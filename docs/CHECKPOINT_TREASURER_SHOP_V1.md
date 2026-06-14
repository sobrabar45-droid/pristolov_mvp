# Treasurer Shop V1 Checkpoint

Project: `D:\Projects\pristolov_mvp`
Date: 2026-06-14
Status: Treasurer Shop V1 runtime package completed and verified by endpoint smoke.

## Purpose

This checkpoint records the completed Treasurer Shop V1 package after the gold spend runtime was committed and smoke-verified.

The package gives the `treasurer` role a real gold spending surface without creating new models, new tables, a new economy framework, or a POS integration.

## Commit

Commit: `5c92d76 Add Treasurer Shop gold spend runtime`

## Scope

Implemented V1 shop actions:

- `set_bar`: costs `5 gold`, creates a bar/social event, no influence effect.
- `giraffe`: costs `10 gold`, creates a bar/social event, no influence effect.
- `gift_to_ally`: costs `15 gold`, requires an active alliance, gives `+1 influence` to sender House and `+1 influence` to allied target House.

Runtime behavior:

- `GET /dev/treasurer-shop/{room_code}` renders a simple cashier/operator Treasurer Shop screen.
- `POST /player/treasurer-shop/{player_id}/purchase` executes the purchase.
- Only players with role code `treasurer` can purchase.
- Gold spending uses the existing gold runtime through `spend_gold_for_action`.
- Events are exposed to Master/TV through existing `recent_events`.
- `gift_to_ally` validates active alliance through the existing `GameDeal` diplomacy source of truth.

## Changed Files

Commit `5c92d76` changed:

- `app/routes/dev.py`
- `app/routes/player.py`
- `app/services/master_state_service.py`
- `app/templates/master_screen.html`
- `app/templates/treasurer_shop.html`

## Smoke Checklist Result

Smoke was run against trusted local runtime on `LIVE01` after:

```powershell
python -m compileall app -q
```

Endpoint smoke result: PASS.

Verified:

- Treasurer Shop screen opens: `GET /dev/treasurer-shop/LIVE01` returns `200` HTML with no traceback.
- Non-treasurer purchase is blocked with `ok=false`; gold remains unchanged.
- `set_bar` spends exactly `5 gold`.
- `set_bar` creates a Treasurer Shop event visible in Master `recent_events`.
- `set_bar` creates the same semantic event visible in TV `recent_events`.
- `giraffe` spends exactly `10 gold`.
- `giraffe` creates a Treasurer Shop event visible in Master `recent_events`.
- `giraffe` creates the same semantic event visible in TV `recent_events`.
- `gift_to_ally` without active alliance is blocked with `ok=false`.
- Blocked `gift_to_ally` does not change gold.
- Blocked `gift_to_ally` does not change influence.
- Real active alliance was created through the existing diplomacy flow.
- `gift_to_ally` with active alliance spends exactly `15 gold`.
- Sender House receives exactly `+1 influence`.
- Target allied House receives exactly `+1 influence`.
- `gift_to_ally` creates a Treasurer Shop event visible in Master `recent_events`.
- `gift_to_ally` creates the same semantic event visible in TV `recent_events`.
- Regression check passed: Master screen opens, TV state responds, player route opens, and no new traceback appeared in server logs.

## Source Of Truth Notes

Gold remains in the existing House resource model:

- `House.resource_gold`
- `HouseGoldTransaction`
- `app/services/gold_service.py`

Treasure Shop purchase events are derived from existing gold transactions:

- `HouseGoldTransaction.source_type == "treasurer_shop"`
- `reason` stores the readable event text
- Master/TV expose these events through the existing `recent_events` contract

Alliances remain in the existing diplomacy source of truth:

- model: `GameDeal`
- active alliance: `status == "alliance_active"` and `offer.type == "alliance"`
- alliance pair: `from_house_id` / `to_house_id`

## Protected Zones Not Touched

This package did not change:

- Court lifecycle
- Final lifecycle
- Terminal lifecycle
- diplomacy core architecture
- core gold architecture
- database models
- database tables
- POS integration
- V2 economy mechanics

## Known Warning

During staging, Git reported LF-to-CRLF normalization warnings for the touched files.

This was not a runtime blocker. Compile and endpoint smoke passed after the warning.

## Known Risks

- Smoke was endpoint-level, not browser pixel automation.
- Treasurer Shop screen has not yet been separately polished for cashier UX under live pressure.
- Race-condition hardening for near-simultaneous purchases remains outside this checkpoint.
- House name grammar in event text is heuristic.
- Legacy encoding noise exists in unrelated historical strings.

## Next Recommended Contour

Do not add another economy mechanic immediately from inside this checkpoint.

Recommended next decision after this checkpoint:

- move to the next approved P1 item, or
- polish Master/TV/Treasurer Shop presentation if live rehearsal shows the event visibility is not strong enough.
