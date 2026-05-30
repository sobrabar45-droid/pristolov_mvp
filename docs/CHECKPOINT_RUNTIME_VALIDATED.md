# Runtime Validated Checkpoint

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: PRISTOLOV_CORE MVP runtime has command-level validation across the main game lifecycle.

## Purpose

This checkpoint records the point where the MVP runtime moved from "stabilized in separate contours" to "validated across the main command-level lifecycle".

The key new closure is the late-game path:

```text
Court -> Last Whisper -> Final Show -> Terminal
```

The runtime is not finished as a production show product, but the core V1 gameplay paths now have repeatable smoke coverage that can be run before live rehearsal or before future mechanics work.

## Validation Scope

Validated by command-level smoke scripts:

- scenario preparation and early director advancement;
- question/assignment reward loop;
- Master Whisper V1 actions;
- read-only Master/TV `recent_events`;
- player-side duel lifecycle with host resolve;
- treasurer resource deal confirmation;
- expedition lifecycle;
- Court lifecycle through `court_finished`;
- Final / Terminal lifecycle through `scenario_finished`;
- minimal production route HTML validation for Master, TV, and player screens.

These smokes verify HTTP route behavior, state transitions, derived Master/TV state, key event text, and repeat-submit/idempotency guards where covered.

## Smoke Coverage Matrix

| Contour | Command | Commit | Coverage |
|---|---|---:|---|
| Last Whisper `quiet_support` | `python scripts/smoke_last_whisper_quiet_support.py` | `f46d16a` | player action -> +1 influence -> Master/TV event -> repeat blocked |
| Last Whisper `crown_tax` | `python scripts/smoke_last_whisper_crown_tax.py` | `1b8cc41` | clear leader, tie case, zero-delta honest text, repeat blocked |
| Last Whisper `break_alliance` | `python scripts/smoke_last_whisper_break_alliance.py` | `8ad7dbf` | active alliance break, no-alliance safe failure, Master/TV visibility |
| Master/TV `recent_events` | `python scripts/smoke_recent_events_contract.py` | `be95d1a` | shared read-only recent event contract in Master and TV state |
| Player duel lifecycle | `python scripts/smoke_player_duel_lifecycle.py` | `61dc636` | Lord challenge, accept/refuse, host resolve, gold/state visibility |
| Assignment reward loop | `python scripts/smoke_assignment_reward_loop.py` | `0e0cb52` | assignment answer -> evaluation -> reward -> Master/TV visibility |
| Scenario director advance | `python scripts/smoke_scenario_director_advance.py` | `e0fc9e7` | early scenario advancement, state consistency, read-only GET checks |
| Treasurer resource deal | `python scripts/smoke_treasurer_resource_deal.py` | `3525013` | deal create/respond/treasurer confirm/resource transfer protection |
| Expedition lifecycle | `python scripts/smoke_expedition_lifecycle.py` | `c7f9505` | expedition create/start/resolve, reward/state visibility, repeat protection |
| Court lifecycle | `python scripts/smoke_court_lifecycle.py` | `b4bdfd4` | Court active -> bracket -> pair -> questions/results -> `court_finished` |
| Final / Terminal lifecycle | `python scripts/smoke_final_terminal_lifecycle.py` | `bd05590` | `court_finished -> stage_last_whisper -> stage_final_show -> terminal` |
| Production route shell validation | `python scripts/smoke_visual_runtime_routes.py` | `2211a3a` | Master/TV/player production routes return non-empty HTML and expected shell markers |

## Checkpoint References

| Document / checkpoint | Commit | Meaning |
|---|---:|---|
| `docs/CHECKPOINT_MVP_RUNTIME_STABILIZATION.md` | `680fa51` | Main runtime contours became command-smoke-covered except Final/Terminal. |
| `docs/RUNTIME_STABILITY_VALIDATION_PASS.md` | `95dbcf9` | Mapped remaining runtime gaps after stabilization. |
| `docs/ROLE_ACTION_REGISTRY_MIGRATION_AUDIT.md` | `2e2018e` | Identified role/action source-of-truth risk. |
| `docs/ROLE_ACTION_REGISTRY_V1.yaml` / README | `86d255e` | Passive frozen V1 role/action registry; runtime does not read it yet. |
| `docs/VISUAL_RUNTIME_VALIDATION_AUDIT.md` | `1fea28a` | Defined production Master/TV/player visual validation scope. |
| `docs/FINAL_TERMINAL_READINESS_AUDIT.md` | `2a153d9` | Defined safe late-game smoke boundary. |
| `scripts/smoke_final_terminal_lifecycle.py` | `bd05590` | Closed command-level late-game validation gap. |

## Late-Game Path Confirmation

The current real V1 path is:

```text
court_finished
-> stage_last_whisper
-> stage_final_show
-> terminal
```

`scripts/smoke_final_terminal_lifecycle.py` confirms:

- Court reaches `court_finished`.
- Scenario advances from Court to Last Whisper preview.
- `stage_last_whisper` becomes active and visible in Master/TV state.
- Last Whisper advances to `stage_final_show`.
- Final host round appears in Master/TV state.
- `final_outcome` exists and has `winner_house_name`.
- Final question can be opened and force-closed.
- Final host round can be completed.
- Terminal state is reached with:
  - `scenario_director.scenario_finished == true`
  - `current_round == null`
  - `next_round == null`
  - `last_completed_round.round_code == "stage_final_show"`
  - `active_phases == []`
  - `active_host_round == null`
  - `current_question == null`
  - `court_runtime == null`
- Repeated Master/TV state GET calls do not mutate terminal markers.

Important implementation note: current runtime reaches terminal immediately after `host-continue` for `stage_final_show`; no extra `scenario/advance` is required after final host continue.

## Operational Meaning

Manual full rehearsal is now primarily for:

- UX clarity;
- operator pacing;
- show quality;
- visual readability;
- room logistics;
- human confidence.

It is no longer the only proof that the basic runtime can survive the MVP flow.

Before this checkpoint, a rehearsal had to discover fundamental runtime survival bugs. After this checkpoint, the main runtime survival contours are command-verifiable.

## What Is Still Not Validated

### Browser Pixel Rendering

`scripts/smoke_visual_runtime_routes.py` verifies production route shells, not true rendered layout.

Still open:

- TV readability from room distance;
- Master operator clarity under pressure;
- player mobile layout and action affordance clarity;
- Final/Terminal visual presentation on actual screens;
- screenshot-level regression checks.

### Concurrency / Race Conditions

Current smokes verify normal repeat-submit blocking, not near-simultaneous concurrent requests.

Open risk areas:

- Last Whisper one-action-per-house;
- treasurer confirmation;
- assignment reward application;
- duel resolve;
- expedition resolve;
- scenario advance buttons under rapid operator input.

### Legacy Encoding Cleanup

New critical event text is guarded in focused smokes where relevant, but old legacy mojibake remains in historical docs and some legacy/runtime strings.

This should not block V1 if the production screens and active event strings are visually checked, but it remains a cleanup tail.

### Production / VPS Deployment

This checkpoint validates local trusted runtime behavior.

Not covered:

- VPS process manager behavior;
- environment variables;
- filesystem permissions;
- database backup/restore;
- network latency;
- real browser/device matrix;
- production logging/observability.

### Full Browser Automation

The project now has smokeable command-level runtime confidence. It does not yet have a browser automation suite for end-to-end DOM/screenshot checks.

## Remaining Risks

- Role Action Registry remains passive and is not a runtime authorization source.
- Some role/action declarations are still V2/deferred and must not be exposed as V1 promises.
- Dev/operator routes can still be dangerous if used outside the runbook.
- Final payoff is state-validated but should still be judged for show strength in live rehearsal.
- Browser-visible event prominence remains a UX/show risk, not a backend-state risk.

## Next Recommended Steps

1. Browser / pixel validation.

   Use Master, TV Mode, and player room production routes. Confirm real DOM, CSS, screenshot, and room-distance readability for Court, Last Whisper, Final, Terminal, and recent events.

2. Operator checklist update.

   Update runbook/checklist to reflect the validated path and the correct production routes:

   - `/dev/master-screen/{room_code}`
   - `/dev/tv-mode/{room_code}`
   - `/house/{invite_code}/player/{player_id}`

   Keep `/dev/tv-screen/{room_code}` marked as legacy/avoid.

3. Role registry future migration only after V1 freeze.

   Keep `docs/ROLE_ACTION_REGISTRY_V1.yaml` passive. Do not replace runtime gates or add new role mechanics until V1 live behavior is frozen and browser validation has passed.

## Recommended Smoke Gate Before Rehearsal

Run the current validation suite against a trusted local runtime:

```powershell
python scripts/smoke_last_whisper_quiet_support.py
python scripts/smoke_last_whisper_crown_tax.py
python scripts/smoke_last_whisper_break_alliance.py
python scripts/smoke_recent_events_contract.py
python scripts/smoke_player_duel_lifecycle.py
python scripts/smoke_assignment_reward_loop.py
python scripts/smoke_scenario_director_advance.py
python scripts/smoke_treasurer_resource_deal.py
python scripts/smoke_expedition_lifecycle.py
python scripts/smoke_court_lifecycle.py
python scripts/smoke_final_terminal_lifecycle.py
python scripts/smoke_visual_runtime_routes.py
```

## Checkpoint Judgment

PRISTOLOV_CORE MVP runtime is command-validated for the main V1 lifecycle.

The next risk is no longer basic runtime survival. The next risk is whether the live room sees and understands the game clearly enough.
