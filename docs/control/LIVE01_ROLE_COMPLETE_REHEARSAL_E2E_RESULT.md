# LIVE01 role-complete rehearsal E2E result

## Context

- User explicitly approved mutating `LIVE01` for rehearsal because there are no real players yet.
- Prior blocker: production smoke was green for surfaces, but `LIVE01` lacked required roles for full E2E.
- Runner added: `scripts/rehearsal_live01_role_e2e.py`.
- Runner requires:
  - `--room LIVE01`
  - `--confirm-reset LIVE01_REHEARSAL_OK`

## Execution

Command executed locally through FastAPI `TestClient`, without starting a dev server and without SSH:

```powershell
python scripts\rehearsal_live01_role_e2e.py --room LIVE01 --confirm-reset LIVE01_REHEARSAL_OK
```

Compile check:

```powershell
python -m compileall app scripts\rehearsal_live01_role_e2e.py -q
```

Result: `PASS`.

## Pre-state Summary

Before the successful rehearsal run, `LIVE01` was already a role-complete rehearsal fixture from the prior partial/retry run:

- game found: yes
- houses: 2
- players: 10
- roles:
  - `lord_lady`: 2
  - `maester`: 2
  - `diplomat`: 2
  - `treasurer`: 1
  - `whisper_master`: 2
  - `house_sworn`: 1
- gold transactions: 4
- deals: 1
- active phases: 0

## Reset Result

The successful run executed:

- `POST /dev/games/LIVE01/reset-runtime`
- `GET /dev/reset-delegations/LIVE01`
- `POST /dev/games/LIVE01/scenario/apply`
- `POST /dev/games/LIVE01/seed-technical-run`

`reset-runtime` deleted:

- deals: 1
- assignments: 0
- host round questions: 0
- expeditions: 0
- duels: 0
- host rounds: 0
- court phases: 0
- other phases: 0
- map visits: 0
- map states: 0

## Fixture Created

After reset/seed, `LIVE01` had:

- 2 Houses
- 10 players
- all required smoke roles:
  - `lord_lady`
  - `treasurer`
  - `diplomat`
  - `whisper_master`
  - `maester`
  - `house_sworn`

The runner printed only redacted player tokens. Full tokens were not documented.

## E2E Matrix Result

| Area | Result |
|---|---|
| Player rooms | PASS: player room opened for every seeded role |
| Cashier screen | PASS: opened, no `/dev/` links, manual +1/check amount/shop queue markers present |
| Master screen | PASS: opened |
| TV screen | PASS: opened |
| Treasurer Shop V1.2 request | PASS: `author_tea` request created with no gold spend |
| Cashier confirmation | PASS: request confirmed, request completed |
| Gold spend timing | PASS: gold changed only on confirmation (`20 -> 17`) |
| HouseGoldTransaction | PASS: transaction count increased by exactly 1 on confirmation |
| Master/TV shop event | PASS: confirmed purchase appeared in recent events |
| Gold Desk manual +1 | PASS |
| Gold Desk check amount 500 | PASS |
| Diplomacy | PASS: alliance created and accepted |
| Last Whisper | PASS: `quiet_support` succeeded once; repeat was blocked |
| Lord/Lady | PASS: expedition creation succeeded |

## Final LIVE01 State

Chosen final state: `LIVE01` was left as a role-complete rehearsal fixture for final browser/manual acceptance.

Post-state:

- houses: 2
- players: 10
- roles:
  - `lord_lady`: 2
  - `maester`: 2
  - `diplomat`: 2
  - `treasurer`: 1
  - `whisper_master`: 2
  - `house_sworn`: 1
- gold transactions: 5
- deals: 2
- active phases: 3
- expeditions: 1
- map visits: 1

House resource state after E2E:

- `Дом Огня`: 19 gold, 1 influence
- `Дом Волка`: 20 gold, 2 influence

## Blockers

No E2E blockers found.

Two runner-only corrections happened during recovery:

- cashier queue marker was adjusted to match the actual template (`queue-section` / `data-confirm-shop-request`)
- check grant smoke switched to numeric `check_id` because ledger `source_id` is integer

No runtime mechanics were changed for those corrections.

## Go / No-Go

Recommendation: **Conditional GO for final manual acceptance**.

Meaning:

- Codex-first role/action E2E is green.
- Manual browser/phone acceptance can now verify the live-facing screens visually.
- Before real play, decide whether to keep this rehearsal fixture, reset/rebuild LIVE01 with real player roster, or run a controlled live setup path.

## Final Manual Acceptance Checklist

- Open one role-complete player room for each important role:
  - lord/lady
  - treasurer
  - diplomat
  - whisper master
  - maester
  - house sworn
- Open cashier Gold Desk.
- Open Master screen.
- Open TV screen.
- Confirm the current rehearsal state is acceptable or explicitly reset/rebuild before inviting real players.
