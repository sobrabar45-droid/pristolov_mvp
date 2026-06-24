# Room Setup MVP production smoke checkpoint

## Background

- Room Setup MVP helper was added in commit `2e8b7c4`.
- Goal of this checkpoint: verify production ability to create a non-LIVE room safely and verify core operational entrypoints without reset/reset-delegations mutations.
- Scope was limited to smoke/readiness proof for one non-LIVE room.

## Commit tested

- `2e8b7c4 Add room setup MVP helper`

## VPS deployment status at smoke time

- VPS was pulled to helper commit `2e8b7c4`.
- Service/runtime status was healthy and endpoints were reachable during smoke.
- `compileall` passed in production context.

## Dry-run result

Command:

```bash
python scripts/setup_room_mvp.py --room-code KURGAN02 --dry-run
```

Dry-run output:

- `ok=true`
- `status=dry_run`
- `room_code=KURGAN02`
- `room would_create`
- Scenario `season1_mvp_live_v2` exists
- `scenario_id=1`
- `rounds_count=11`
- `scenario_apply would_apply`
- `players_count=0`
- `houses_count=0`
- `urls_generated=true`

## Real test room result (production)

Command:

```bash
python scripts/setup_room_mvp.py --room-code TEST_ROOM_SETUP --title "PRISTOLOV TEST ROOM SETUP"
```

Output:

- `ok=true`
- `status=ready`
- `room_code=TEST_ROOM_SETUP`
- `room id=2`
- scenario `season1_mvp_live_v2` applied
- `scenario_id=1`
- `already_applied=false`
- `players_count=0`
- `houses_count=0`
- `urls_generated=true`

## Registration smoke

Command:

```bash
GET http://127.0.0.1:8000/delegation/start?game_code=TEST_ROOM_SETUP&entry_mode=random
```

- `start=200`
- `time=0.002892`

## Operational screen smoke (with admin token for protected routes)

| Screen URL | Status | Time |
| --- | ---: | ---: |
| `/dev/master-screen/TEST_ROOM_SETUP` | 200 | 0.040028s |
| `/dev/game-master/TEST_ROOM_SETUP` | 200 | 0.005917s |
| `/dev/tv-mode/TEST_ROOM_SETUP` | 200 | 0.029198s |
| `/cashier/gold-desk/TEST_ROOM_SETUP` | 200 | 0.006432s |
| `/dev/gold-desk/TEST_ROOM_SETUP` | 200 | 0.004946s |
| `/dev/treasurer-shop/TEST_ROOM_SETUP` | 200 | 0.005146s |

## Safety confirmation

- LIVE01 not touched.
- No players created.
- No houses created during smoke.
- No `reset-runtime` or `reset-delegations` executed.
- No production config edits.
- No DB reset or destructive reset action in this smoke.

## Result

- Room Setup MVP production smoke is **green**.
- A new non-LIVE room can be created in production.
- Operational screens for that room open successfully.
- One-QR entry smoke was successful.

## Remaining risks

- No cleanup/archive helper for `TEST_ROOM_SETUP` yet.
- No public franchise admin UI yet.
- No per-city/operator auth separation yet.
- No multi-room simultaneous active gameplay stress/load test yet.
- `TEST_ROOM_SETUP` remains in production DB until explicitly cleaned later.

## Recommended next contour

- Option A: build a cleanup / safe archive helper and run room cleanup workflow.
- Option B: if immediate live schedule allows, return to product P0 (stability and gameplay readiness) with room-setup foundation already proven.

## Reference and handoff

- This result supports moving from room-setup technical setup to either
  - room cleanup tooling, or
  - next product-readiness P0 tasks that do not modify room loader runtime assumptions.
