# MVP Runtime Stabilization Checkpoint

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: main MVP runtime contours are checkpointed with command-level smoke coverage.

## Purpose

This checkpoint records the post-run stabilization cycle for PRISTOLOV_CORE MVP runtime.

The goal of the cycle was not to add new gameplay, but to make the already implemented runtime contours verifiable by repeatable command-level smoke scripts before adding more role mechanics or broader architecture changes.

## What Was Stabilized

The following runtime contours now have focused command-level verification:

- Master Whisper V1 action effects.
- Read-only Master/TV `recent_events` state contract.
- Player-side duel lifecycle with host resolve.
- Assignment/question reward loop.
- Scenario director advance flow.
- Treasurer resource deal confirmation flow.
- Expedition lifecycle.
- Court lifecycle through `court_finished`, stopping before Final/Terminal.

This does not mean all gameplay is complete. It means the main MVP runtime paths now have executable smoke coverage that can catch regressions before another mechanics pass.

## Smoke Coverage Matrix

| Contour | Smoke / Doc | Commit | Coverage Status | Notes |
|---|---|---|---|---|
| Master Whisper V1 checkpoint | `docs/CHECKPOINT_MASTER_WHISPER_V1.md` | `a5169c3` | CHECKPOINTED | Documents completed V1 actions and state contracts. |
| Last Whisper `quiet_support` | `scripts/smoke_last_whisper_quiet_support.py` | `f46d16a` | DEDICATED | Verifies player action, `+1 influence`, Master/TV event text, repeat guard. |
| Last Whisper `crown_tax` | `scripts/smoke_last_whisper_crown_tax.py` | `1b8cc41` | DEDICATED | Verifies clear leader, tie, zero-delta honest text, repeat guard. |
| Last Whisper `break_alliance` | `scripts/smoke_last_whisper_break_alliance.py` | `8ad7dbf` | DEDICATED | Verifies active alliance break, no-alliance safe failure, Master/TV visibility. |
| Event presentation audit | `docs/EVENT_PRESENTATION_AUDIT.md` | `983de77` | AUDITED | Identified missing shared Master/TV event contract. |
| Master/TV `recent_events` contract | `scripts/smoke_recent_events_contract.py` | `be95d1a` | DEDICATED | Verifies read-only derived recent events in Master and TV state. |
| Smoke coverage audit | `docs/SMOKE_COVERAGE_AUDIT.md` | `32a7fd5` | AUDITED | Baseline audit; some uncovered items listed there are now closed by later smokes. |
| Player duel lifecycle | `scripts/smoke_player_duel_lifecycle.py` | `61dc636` | DEDICATED | Verifies challenge/accept/host resolve and Master/TV duel visibility. |
| Assignment reward loop | `scripts/smoke_assignment_reward_loop.py` | `0e0cb52` | DEDICATED | Verifies assignment answer, evaluation, reward application, visibility, double protection. |
| Scenario director advance | `scripts/smoke_scenario_director_advance.py` | `e0fc9e7` | DEDICATED | Verifies early-stage scenario advancement and read-only state calls. |
| Treasurer resource deal | `scripts/smoke_treasurer_resource_deal.py` | `3525013` | DEDICATED | Verifies resource deal creation/response/treasurer confirmation and transfer protection. |
| Expedition lifecycle | `scripts/smoke_expedition_lifecycle.py` | `c7f9505` | DEDICATED | Verifies expedition create/start/resolve state progression and visibility. |
| Court readiness audit | `docs/COURT_READINESS_AUDIT.md` | `3c106b5` | AUDITED | Defined safe smoke boundary for Court. |
| Court lifecycle | `scripts/smoke_court_lifecycle.py` | `b4bdfd4` | DEDICATED | Verifies Court active -> bracket -> pair -> question/results -> confirm winner -> `court_finished`. Stops before Final/Terminal. |

## Current Smoke Commands

Run these against a trusted local runtime at `http://127.0.0.1:8000`:

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
```

## Source-Of-Truth Notes

Current runtime remains intentionally pragmatic:

- Role actions are still mixed across routes, templates, assignment/task YAML, services, and docs.
- Last Whisper actions are implemented in the existing Last Whisper route/state path.
- Alliances remain `GameDeal` records.
- Court runtime remains `GamePhase` payload plus `court_service.py`.
- Recent events are derived read-only from existing state, not persisted as a new event system.
- Smoke scripts use live HTTP/dev/player routes rather than direct service mutation.

## Known Remaining Tails

### Role Action Registry

`docs/ROLE_ACTION_REGISTRY_AUDIT.md` exists and is normalized, but the registry is not yet a runtime source of truth.

Current risk: adding new role actions directly in templates/routes can recreate action sprawl.

### Race Conditions

The near-simultaneous double-submit risk remains open for some action paths.

Current smoke scripts verify normal repeat submit behavior, but they do not prove transactional protection under concurrent requests.

### Legacy Encoding Cleanup

Unrelated legacy mojibake remains in older strings and docs/code paths.

Current smoke scripts protect key new Russian event text where relevant, but they do not perform broad encoding cleanup.

### Visual TV Validation

Current stabilization is command-level. It verifies state contracts and event text, not browser-visible prominence.

TV and Master UI presentation still need browser-level or screenshot-level validation before a public rehearsal.

### Final / Terminal

Court smoke deliberately stops at `court_finished`.

Final and Terminal should remain separate smoke contours rather than being folded into Court lifecycle coverage.

## Recommendation

Treat MVP runtime stabilization as checkpointed.

Recommended next architectural contour:

```text
Role Action Registry Runtime Migration Audit
```

Purpose of that audit:

- decide the canonical runtime registry shape;
- map existing route/template gates to registry entries;
- identify which entries can be passive documentation first;
- prevent new role mechanics from being added as another hardcoded island.

Do not add new role mechanics until that audit is complete.

Recommended order:

1. Role Action Registry Runtime Migration Audit.
2. Small passive registry or contract draft.
3. Master/TV browser-visible event presentation polish.
4. Only then consider new Diplomat actions such as `embassy_offer` or `trade_contact`.

Avoid `map_route` first because it touches map/location/expedition contracts and is likely to expand beyond a safe MVP patch.

## Stabilization Judgment

The MVP runtime is not finished, but it is now materially safer to change.

The important shift is that core runtime paths are no longer validated only by manual rehearsal memory. They have command-level smoke scripts that can be rerun before the next mechanics contour.
