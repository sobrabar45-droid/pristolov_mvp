# Runtime Stability Validation Pass

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Checkpoint baseline: `680fa51 Add MVP runtime stabilization checkpoint`

## Purpose

This validation pass maps what remains unproven after the MVP runtime stabilization checkpoint.

The runtime now has meaningful command-level smoke coverage, but not every route, branch, UI surface, or live-room failure mode is validated. This document separates covered contours, uncovered contours, open risks, production blockers, non-blockers, and the recommended next contour.

## Covered Contours

The following contours have focused command-level smoke coverage:

| Contour | Smoke | Status |
|---|---|---|
| Master Whisper `quiet_support` | `scripts/smoke_last_whisper_quiet_support.py` | covered |
| Master Whisper `crown_tax` | `scripts/smoke_last_whisper_crown_tax.py` | covered |
| Master Whisper `break_alliance` | `scripts/smoke_last_whisper_break_alliance.py` | covered |
| Master/TV `recent_events` contract | `scripts/smoke_recent_events_contract.py` | covered |
| Player-side duel lifecycle | `scripts/smoke_player_duel_lifecycle.py` | covered |
| Assignment/question reward loop | `scripts/smoke_assignment_reward_loop.py` | covered |
| Scenario director early advance flow | `scripts/smoke_scenario_director_advance.py` | covered |
| Treasurer resource deal confirmation | `scripts/smoke_treasurer_resource_deal.py` | covered |
| Expedition lifecycle | `scripts/smoke_expedition_lifecycle.py` | covered |
| Court lifecycle to `court_finished` | `scripts/smoke_court_lifecycle.py` | covered |

These smokes verify the core runtime state mutations through live HTTP routes. They do not replace browser-visible validation or a full end-to-end production rehearsal.

## Partially Covered Contours

| Contour | Current Coverage | Remaining Gap |
|---|---|---|
| Diplomacy alliance creation/acceptance | indirectly covered by `break_alliance` smoke | reject, cancel, counter, duplicate alliance conflict, old dev diplomacy routes |
| Resource deals | covered for one treasurer confirmation path | rejection branch, insufficient-resource edge cases, multiple simultaneous deals |
| Duels | challenge, accept, refuse, resolve, insufficient gold, non-Lord blocked | dev/operator duel console edge cases, concurrent challenge/resolve behavior |
| Assignment rewards | one answer/reward lifecycle covered | broader assignment template variants, manual-check assignments, all declared role task types |
| Scenario director | early stage advance covered | full scenario through Last Whisper and Final is not covered by one command |
| Court | happy path to `court_finished` covered | sudden death, extra question, large bracket, browser presentation, post-Court transition into Last Whisper/Final |
| Expedition | one lifecycle covered | alternative locations/outcomes, role composition edge cases, old dev expedition routes |
| `recent_events` | backend Master/TV state contract covered | browser-visible prominence and visual ranking are not covered |

## Uncovered Contours

### Final / Terminal

Final outcome is derived in `master_state_service.py` and rendered in Master/TV templates, but there is no focused smoke for:

- reaching `stage_final_show`;
- verifying final winner selection;
- verifying Final Master state;
- verifying Final TV state;
- verifying Terminal/end-of-game behavior if used.

This is the largest remaining launch-critical runtime gap.

### Full Scenario Rehearsal Smoke

There is no single smoke that moves through the complete intended V1 live flow:

```text
intro -> questions -> map/diplomacy/free_play/duels -> Court -> Last Whisper -> Final
```

Individual contours are covered, but integration between all contours in one run remains mostly manual.

### Browser-Visible Master / TV / Player Checks

Current smoke verifies JSON state contracts. It does not prove that the room sees:

- latest event prominence on TV;
- Court scene clarity;
- Final scene clarity;
- player-side controls in actual browser DOM;
- no broken CSS/hidden controls;
- QR/onboarding visibility after the latest runtime changes.

### Role Action Registry Runtime Source Of Truth

`docs/ROLE_ACTION_REGISTRY_AUDIT.md` exists, but runtime gates are still mixed across:

- YAML declarations;
- `player.py`;
- `player_room.html`;
- service-specific guards;
- Master/TV state builders.

This is architectural risk rather than an immediate crash risk.

### Legacy / Dev Routes

Some dev/admin routes still mutate runtime state and are not fully covered:

- legacy dev diplomacy propose/respond/counter/cancel;
- dev map explore;
- dev expedition management;
- manual gold routes;
- tower routes.

Many are not V1-facing, but they remain dangerous if used during a live game by mistake.

### Concurrency / Race Conditions

Existing smokes verify normal repeat-submit blocking. They do not prove safety under near-simultaneous requests for:

- Last Whisper one-action-per-house;
- treasurer confirmation;
- assignment answer reward application;
- duel resolve;
- expedition resolve.

This is a known technical risk.

### Placeholder / Declared-Only Role Actions

Several declared actions remain non-runtime or partial:

- `diplomat.embassy_offer`
- `diplomat.trade_contact`
- `diplomat.map_route`
- `lord_lady.sanction`
- `lord_lady.alliance_decision`
- `whisper_master.rumor`
- `whisper_master.hidden_signal`
- `whisper_master.blackmail`
- `treasurer.exchange`
- `treasurer.investment`
- `house_sworn.*`

These should not be presented as live-ready mechanics until the registry is normalized.

## Open Risks

### Architectural Risks

- No canonical runtime role/action registry.
- Stringly typed statuses for `GameDeal`, `GameDuel`, Court payloads, and scenario phases.
- Derived state is spread across large state builders.
- Some state contracts are documented through smoke behavior rather than a formal schema.
- Old dev routes can bypass the intended player-side source of truth.

### Gameplay Risks

- Final payoff is still weaker than Court and not smoke-validated.
- Placeholder actions can overpromise role agency.
- Resource economy remains partially hidden in V1 but still exists in runtime paths.
- Lord/Lady alliance break and betrayal are separate from Whisper break and remain risky if exposed.
- Map/location/expedition contracts are only lightly validated relative to their design scope.

### UI-Only Risks

- TV/Master event visibility is state-covered but not browser-verified.
- Legacy encoding noise remains in older strings.
- Some old templates may still contain stale phase or resource language.
- Player controls may be state-valid but visually unclear on mobile or live browser dimensions.

### Live-Game Failure Risks

- Runtime server not running or wrong runtime instance on port `8000`.
- Operator accidentally using uncovered dev routes.
- Full scenario transition into Final not validated by command smoke.
- Browser-visible TV scene failing despite state contract passing.
- Race-condition double-submit under real players tapping at the same time.
- Unclear role/action availability confusing players during the first production run.

## Production Blockers

Before the first real production game, the following should be resolved or explicitly accepted as manual risk:

1. Add or perform a Final/Terminal validation.

   Minimum: verify `stage_final_show`, `final_outcome`, Master state, TV state, and no crash after Last Whisper -> Final transition.

2. Run a full scenario rehearsal.

   Minimum: use the current scenario order and stop only after Final state is visible. This may be manual plus command checks if a full smoke is too broad.

3. Browser-validate the room-facing surfaces.

   Minimum: Master screen, TV mode, player room, Lord Dashboard/onboarding link/QR, Court, Last Whisper, and Final.

4. Freeze role/action promises for V1.

   Minimum: do not expose placeholder role actions as live mechanics, and avoid new role mechanics until the Role Action Registry Runtime Migration Audit is complete.

5. Operator safety pass.

   Minimum: confirm the runbook says which routes/buttons are live-safe and which dev tools should not be touched during production.

## Non-Blockers

These can safely wait if they remain hidden or explicitly out of V1:

- V2 tower mechanics.
- Crest/heraldry payoff.
- Scrolls and keys.
- `map_route`.
- `blackmail`, `hidden_signal`, and new Whisper mechanics.
- `exchange` / `investment` economy mechanics.
- Full legacy encoding cleanup.
- Full concurrency hardening, if the first production run is small and operator-mediated.
- Dev route smoke coverage for tools not used in live production.

## Recommended Next Contour

Recommended next contour:

```text
Role Action Registry Runtime Migration Audit
```

Why this next:

- The runtime is now stable enough to avoid panic-patching mechanics.
- The largest remaining architectural risk is action sprawl.
- New Diplomat or role mechanics should not be added until the project knows where action truth lives.
- A passive registry can become the bridge between docs, templates, routes, services, and smoke coverage.

Recommended shape of the next audit:

- map every visible player action to a canonical `role_code/action_code`;
- map each action to route, phase, source of truth, state mutation, and smoke command;
- identify which hardcoded gates can remain for V1;
- identify which UI placeholders must stay hidden;
- propose a passive registry file before any runtime migration.

## What Should Be Done Before First Real Production Game

1. Run the full existing smoke suite against a trusted no-reload runtime.
2. Add or manually perform Final/Terminal validation.
3. Browser-check Master, TV, player, Court, Last Whisper, Final, and onboarding QR.
4. Confirm V1 role/action visibility matches what is actually implemented.
5. Keep new mechanics frozen until after the Role Action Registry Runtime Migration Audit.

## What Can Wait

- New role mechanics.
- V2 disabled systems.
- Broad refactor of `master_state_service.py`.
- New persistence/event models.
- Full browser automation suite.
- Concurrency hardening beyond known repeat-submit guards.

## Validation Judgment

The MVP runtime is stabilized, not finished.

The project has moved from manual-confidence-only to command-verifiable runtime confidence for the main gameplay contours. The remaining work is now less about emergency stabilization and more about production readiness, action governance, and browser-visible trust.
