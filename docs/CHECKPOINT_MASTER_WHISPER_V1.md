# Master Whisper V1 Checkpoint

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: V1 runtime package completed and verified by command-level smoke tests.

## Purpose

This checkpoint records the completed Master Whisper V1 runtime package after the third Last Whisper action, `break_alliance`, passed smoke verification.

The package gives the Master Whisper role a real final-window impact before the Final stage without introducing new models, new tables, or a new diplomacy system.

## Implemented Actions

### `quiet_support`

Commit: `f46d16a Add Last Whisper quiet support effect`

Effect:

- Master Whisper selects a target House.
- Target House receives `+1 influence`.
- Master/TV expose the event through `last_whisper.latest_event`.

Smoke:

```powershell
python scripts/smoke_last_whisper_quiet_support.py
```

### `crown_tax`

Commit: `1b8cc41 Add Last Whisper crown tax effect`

Effect:

- Finds a single influence leader.
- If there is a clear leader, applies `-1 influence`.
- If there is a tie, no influence changes.
- If the leader is already at zero, text reflects the real zero delta.

Smoke:

```powershell
python scripts/smoke_last_whisper_crown_tax.py
```

### `break_alliance`

Commit: `8ad7dbf Add Last Whisper break alliance effect`

Effect:

- Master Whisper selects one active alliance.
- Selected `GameDeal` changes from `alliance_active` to `alliance_broken`.
- `offer.break_mode = "whisper_break"`.
- `offer.broken_at` stores UTC ISO timestamp.
- `offer.broken_by_house_id` stores the acting Whisper House id.
- `offer.break_text` stores readable Russian event text.

Smoke:

```powershell
python scripts/smoke_last_whisper_break_alliance.py
```

## Source Of Truth Notes

Last Whisper actions are stored in the active `GamePhase` payload:

- `GamePhase.phase_type == "last_whisper"`
- `GamePhase.status == "active"`
- `GamePhase.payload["whisper_actions"]`

Alliances remain in the existing diplomacy source of truth:

- model: `GameDeal`
- active alliance: `status == "alliance_active"` and `offer.type == "alliance"`
- broken alliance: `status == "alliance_broken"`
- alliance pair: `from_house_id` / `to_house_id`

Influence changes use existing resource/effect logic. No new resource system was introduced.

## State Contracts

Player state:

- `last_whisper.active`
- `last_whisper.viewer_can_act`
- `last_whisper.viewer_has_acted`
- `last_whisper.available_actions`
- `last_whisper.available_target_houses`
- `last_whisper.available_alliances`
- `last_whisper.latest_event`

Master state:

- `last_whisper.events`
- `last_whisper.latest_event`
- `alliances`
- `broken_alliances_recent`
- `deals`

TV state:

- `last_whisper.latest_event`
- `alliances`
- `broken_alliances_recent`
- `deals.pending`
- `deals.countered`
- `deals.recent_closed`

## Smoke Tests

The current V1 package is covered by command-level smoke tests:

```powershell
python scripts/smoke_last_whisper_quiet_support.py
python scripts/smoke_last_whisper_crown_tax.py
python scripts/smoke_last_whisper_break_alliance.py
```

The latest verified `break_alliance` smoke confirmed:

- runtime reset
- scenario applied
- technical run seeded
- alliance created through live player routes
- alliance accepted through live player routes
- Master/TV expose active alliance
- Last Whisper breaks selected alliance
- selected deal becomes `alliance_broken`
- Master/TV expose `broken_alliances_recent`
- `last_whisper.latest_event.tv_text` is readable Russian
- repeat submit is blocked
- no-alliance branch fails safely with readable Russian message

## Known Risks

- Race-condition risk remains on near-simultaneous double submit.
- `GameDeal.status` values are stringly typed.
- House name grammar is still heuristic in some messages.
- Old encoding noise exists in unrelated legacy strings.
- Current smoke coverage is command-level, not browser UI automation.

## Next Recommended Contour

Do not add new Whisper mechanics immediately.

Recommended next options:

1. Role Action Registry cleanup.
2. Master/TV event presentation polish.
3. Diplomacy extension: `embassy_offer` / `trade_contact`.

Avoid `map_route` first because it touches map/location contracts and is likely to expand beyond a small runtime patch.
