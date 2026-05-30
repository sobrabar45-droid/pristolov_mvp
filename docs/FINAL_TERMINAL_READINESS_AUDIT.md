# Final / Terminal Readiness Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Scope: readiness to add focused command-level smoke coverage for the final runtime zone.

## Purpose

This audit determines whether the end-of-game lifecycle can be safely smoke-tested and defines the smallest validation boundary.

The historical risk zone is the transition from the end of Court into the final scene and then into terminal state. The current V1 scenario now includes Last Whisper between Court and Final, so the real live path is:

```text
court_finished -> stage_last_whisper -> stage_final_show -> terminal
```

## Files Inspected

- `docs/FULL_SCENARIO_REHEARSAL_REPORT.md`
- `docs/COURT_MVP_STABILIZATION_REPORT.md`
- `docs/LIVE_DRY_RUN_SCRIPT.md`
- `docs/PRE_LIVE_OPERATOR_CHECKLIST.md`
- `app/game_templates/scenarios/season1_mvp_live_v2.json`
- `app/services/scenario_service.py`
- `app/routes/dev.py`
- `app/services/master_state_service.py`
- `app/templates/master_screen.html`
- `app/templates/tv_mode_tv_state.html`
- `scripts/smoke_court_lifecycle.py`
- `scripts/smoke_scenario_director_advance.py`

## Lifecycle Diagram

```text
stage_court active
  -> Court service reaches court_runtime.status = court_finished
  -> POST /dev/games/{room_code}/scenario/advance
  -> stage_court system phase closes
  -> next_round = stage_last_whisper
  -> POST /dev/games/{room_code}/scenario/start-next-round
  -> active system phase: phase_type = last_whisper
  -> POST /dev/games/{room_code}/scenario/advance {"auto_start_next": true}
  -> last_whisper closes
  -> stage_final_show starts as host_round/final
  -> POST /dev/host-rounds/{host_round_id}/open-next-question
  -> POST /dev/host-rounds/{host_round_id}/force-close-question
  -> POST /dev/host-rounds/{host_round_id}/host-continue
  -> POST /dev/games/{room_code}/scenario/advance
  -> terminal state
```

## Source Of Truth

### Final

Final is not a separate DB model and does not have a dedicated template.

Current source of truth:

- `RoundTemplate.round_code == "stage_final_show"`
- `round_type == "final"` / `round_kind == "final"`
- active `GameHostRound` for `stage_final_show`
- `master_state_service._build_final_outcome_payload(...)`
- leader ranking from `leaders.by_influence`, with gold fallback
- optional final question content config for jackpot display

Master/TV rendering:

- `app/templates/master_screen.html` detects final via `stage_final_show`, `round_kind == "final"`, or `scenario_finished`.
- `app/templates/tv_mode_tv_state.html` uses `isFinalShowRound(...)` and `final_outcome` to render `final_show` mode.

### Terminal

Terminal is not a separate route, model, or template.

Current source of truth:

- `scenario_director.scenario_finished == true`
- `scenario_director.current_round == null`
- `scenario_director.next_round == null`
- `scenario_director.last_completed_round.round_code == "stage_final_show"`
- `active_host_round == null`
- `current_question == null`
- `active_phases == []`
- `court_runtime == null`

Master/TV stay on the same production screens and render a completed final/neutral terminal state from derived state.

## State Transition Map

| Step | Mutation endpoint | Expected state markers |
|---|---|---|
| Court completed | Court endpoints already covered by `scripts/smoke_court_lifecycle.py` | `court_runtime.status == "court_finished"` while director still has `current_round.stage_court` |
| Leave Court | `POST /dev/games/{room_code}/scenario/advance` | `stage_court` closes, `court_runtime == null` in Master/TV, `next_round.stage_last_whisper` |
| Open Last Whisper | `POST /dev/games/{room_code}/scenario/start-next-round` | active phase `last_whisper`, director `current_round.stage_last_whisper`, no active host round |
| Finish Last Whisper and start Final | `POST /dev/games/{room_code}/scenario/advance {"auto_start_next": true}` | active host round `stage_final_show`, director `current_round.stage_final_show`, `final_outcome` present |
| Open final question | `POST /dev/host-rounds/{host_round_id}/open-next-question` | `current_question` present, final scene still detected as final |
| Close final question | `POST /dev/host-rounds/{host_round_id}/force-close-question` | final host round can reach completed/waiting state |
| Host continue final | `POST /dev/host-rounds/{host_round_id}/host-continue` | final host round `status == "finished"`, host_round phase closes when no active rounds remain |
| Terminal advance | `POST /dev/games/{room_code}/scenario/advance` | `scenario_finished == true`, no active host round, no active phases, `last_completed_round.stage_final_show` |

## Historical Failures

Existing reports identify this area as previously fragile:

- `stage_final_show -> terminal` could leave a stale `host_round` phase active.
- Master/TV could continue showing stale host-round envelope even after director reached terminal.
- Court completion previously risked losing or misreading scenario metadata, preventing clean transition after `court_finished`.
- Stale `court_runtime` after entering Final was a known failure mode.

These bugs are documented as fixed, but they do not yet have a dedicated focused smoke for the full end zone.

## Readiness Findings

1. Final/Terminal can be smoke-tested without new runtime architecture.
2. The future smoke should reuse existing explicit POST endpoints only.
3. The smoke should not mutate state from GET calls.
4. The smoke should build on `scripts/smoke_court_lifecycle.py` setup/reach helpers or duplicate the minimal safe sequence.
5. The smoke must include Last Whisper because it is now a real stage in `season1_mvp_live_v2`.
6. The safe boundary is terminal state, not browser visual validation.
7. Browser-visible Final/Terminal validation should remain a separate follow-up after command-level state smoke.
8. There are no dedicated final/terminal templates to inspect; Master/TV final presentation is embedded in production templates.

## Minimum Safe Smoke Boundary

The safest smoke should start from a clean runtime, drive the scenario through Court using the existing deterministic Court smoke path, then continue only through:

```text
court_finished
-> stage_last_whisper opened
-> stage_final_show opened
-> final host round completed
-> terminal state reached
```

It should stop after proving terminal state. It should not attempt jackpot business logic, browser screenshot validation, or new final gameplay.

## Proposed Smoke Plan

Create a focused script:

```text
scripts/smoke_final_terminal_lifecycle.py
```

Suggested command:

```powershell
python scripts/smoke_final_terminal_lifecycle.py
```

Suggested checks:

1. Runtime reset.
2. Scenario applied: `season1_mvp_live_v2`.
3. Technical run seeded.
4. Reach Court using the same deterministic path as `scripts/smoke_court_lifecycle.py`.
5. Complete Court to `court_finished`.
6. Assert Master/TV expose `court_runtime.status == "court_finished"`.
7. `POST /dev/games/{room_code}/scenario/advance`.
8. Assert director no longer has active Court and `next_round == stage_last_whisper`.
9. Start Last Whisper with `POST /dev/games/{room_code}/scenario/start-next-round`.
10. Assert active phase `last_whisper`, no active host round.
11. Finish Last Whisper with `POST /dev/games/{room_code}/scenario/advance {"auto_start_next": true}`.
12. Assert active host round exists with `round_code == "stage_final_show"`.
13. Assert Master state and TV state expose non-empty `final_outcome`.
14. Assert Master/TV no longer expose stale `court_runtime`.
15. Open final question.
16. Force close final question.
17. Host continue final round.
18. Assert no active host-round phase remains.
19. Advance scenario once more.
20. Assert terminal markers:
    - `scenario_director.scenario_finished == true`
    - `scenario_director.current_round == null`
    - `scenario_director.next_round == null`
    - `scenario_director.last_completed_round.round_code == "stage_final_show"`
    - `active_phases == []`
    - `active_host_round == null`
    - `current_question == null`
    - `court_runtime == null`
    - `final_outcome` still present and has `winner_house_name`
21. Fetch Master and TV state twice and assert GET calls do not change terminal markers.
22. Cleanup runtime.

## Risks

- The future smoke may be lengthy because it must reach Court first.
- Reusing helpers from `smoke_court_lifecycle.py` can reduce duplication, but imports between smoke scripts should remain simple and explicit.
- Final winner selection is derived from current leader state, not a separate final scoring model.
- Jackpot outcome remains operator/manual unless configured in final question content or preview params.
- Terminal has no standalone object, so assertions must be state-marker based.
- Old docs contain legacy encoding noise, but the active code paths for new state markers are clear.
- Browser-visible Final/Terminal presentation is still not proven by command-level state smoke.

## Recommendation

Final/Terminal is ready for a focused command-level smoke.

Recommended next patch:

```text
Add focused smoke test for Final / Terminal lifecycle
```

Do not change runtime mechanics. The smoke should validate state transitions only and should deliberately include Last Whisper as the real bridge between Court and Final.

After that smoke is green, run a separate browser visual validation pass for final scenes on:

- `/dev/master-screen/{room_code}`
- `/dev/tv-mode/{room_code}`

## Readiness Judgment

Safe to smoke-test with a bounded command-level script.

Not yet safe to call visually production-verified until Master/TV browser checks confirm that Final and terminal states are legible on the actual screens.
