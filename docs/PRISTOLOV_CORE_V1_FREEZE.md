# PRISTOLOV_CORE V1 Freeze

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: PRISTOLOV_CORE V1 is frozen and runtime-validated.

## 1. Purpose

V1 Freeze means the current PRISTOLOV_CORE V1 runtime boundary is locked for live-readiness work.

The freeze exists to prevent scope drift after runtime validation. From this point, work should focus on validation, UX clarity, operator readiness, browser visual checks, and safe production preparation, not new mechanics.

This does not mean the product is "done". It means V1 is the current playable contract. New gameplay systems belong to V2 unless explicitly approved as a V1 freeze exception.

## 2. V1 Included Contours

The following contours are included in PRISTOLOV_CORE V1:

| Contour | V1 status | Validation |
|---|---|---|
| Scenario Director | included | `scripts/smoke_scenario_director_advance.py`, `scripts/smoke_final_terminal_lifecycle.py` |
| Assignment system | included | `scripts/smoke_assignment_reward_loop.py` |
| Question reward loop | included | `scripts/smoke_assignment_reward_loop.py` |
| Diplomacy deals | included, contained | covered indirectly by treasurer and Last Whisper alliance setup smokes |
| Treasurer confirmation | included | `scripts/smoke_treasurer_resource_deal.py` |
| Duel system | included | `scripts/smoke_player_duel_lifecycle.py` |
| Expedition system | included | `scripts/smoke_expedition_lifecycle.py` |
| Court MVP | included | `scripts/smoke_court_lifecycle.py` |
| Last Whisper V1 | included | quiet support, crown tax, break alliance smokes |
| Final Show | included | `scripts/smoke_final_terminal_lifecycle.py` |
| Terminal | included | `scripts/smoke_final_terminal_lifecycle.py` |
| Master state | included | covered across state smokes and route shell smoke |
| TV state | included | covered across state smokes and route shell smoke |
| Player state | included | covered through player-side action smokes |
| `recent_events` | included | `scripts/smoke_recent_events_contract.py` |
| Production route shells | included as minimal validation | `scripts/smoke_visual_runtime_routes.py` |

V1 path confirmed:

```text
Scenario start
-> assignments/questions
-> diplomacy/resource/duel/expedition contours
-> Court
-> Last Whisper
-> Final Show
-> Terminal
```

Late-game path confirmed:

```text
court_finished
-> stage_last_whisper
-> stage_final_show
-> terminal
```

## 3. V1 Included Actions

`docs/ROLE_ACTION_REGISTRY_V1.yaml` is the source for the passive V1 action boundary.

The registry is not read by runtime code. Permission gates remain in existing routes, templates, services, and state builders.

### V1 Frozen Actions

These actions are part of the V1 runtime promise:

| action_code | role/surface | status | smoke |
|---|---|---|---|
| `quiet_support` | `whisper_master` | V1 frozen | `scripts/smoke_last_whisper_quiet_support.py` |
| `crown_tax` | `whisper_master` | V1 frozen | `scripts/smoke_last_whisper_crown_tax.py` |
| `break_alliance` | `whisper_master` | V1 frozen | `scripts/smoke_last_whisper_break_alliance.py` |
| `duel_challenge` | `lord_lady` | V1 frozen | `scripts/smoke_player_duel_lifecycle.py` |
| `duel_accept` | `lord_lady` | V1 frozen | `scripts/smoke_player_duel_lifecycle.py` |
| `duel_refuse` | `lord_lady` | V1 frozen | `scripts/smoke_player_duel_lifecycle.py` |
| `duel_host_resolve` | `master_operator` | V1 frozen | `scripts/smoke_player_duel_lifecycle.py` |
| `expedition_create` | `lord_lady` | V1 frozen | `scripts/smoke_expedition_lifecycle.py` |
| `expedition_choose_location` | expedition party | V1 frozen | `scripts/smoke_expedition_lifecycle.py` |
| `expedition_resolve` | expedition party | V1 frozen | `scripts/smoke_expedition_lifecycle.py` |
| `assignment_answer` | all roles | V1 frozen | `scripts/smoke_assignment_reward_loop.py` |
| `treasurer_confirm_deal` | `treasurer` | V1 frozen | `scripts/smoke_treasurer_resource_deal.py` |
| `scenario_start_next_round` | `master_operator` | V1 frozen | `scripts/smoke_scenario_director_advance.py` |
| `scenario_advance` | `master_operator` | V1 frozen | `scripts/smoke_scenario_director_advance.py`, `scripts/smoke_final_terminal_lifecycle.py` |
| `host_round_open_next_question` | `master_operator` | V1 frozen | `scripts/smoke_assignment_reward_loop.py` |
| `host_round_force_close_question` | `master_operator` | V1 frozen | `scripts/smoke_scenario_director_advance.py` |
| `host_round_continue` | `master_operator` | V1 frozen | `scripts/smoke_scenario_director_advance.py`, `scripts/smoke_final_terminal_lifecycle.py` |
| `court_lifecycle` | `master_operator` | V1 frozen | `scripts/smoke_court_lifecycle.py` |

### V1 Contained / Partial Actions

These exist in runtime or UI but should not be expanded without a separate smoke/audit:

| action_code | status | freeze rule |
|---|---|---|
| `deal_create` | V1 partial | keep contained; do not expand into new diplomat mechanics |
| `deal_respond` | V1 partial | keep contained; add dedicated diplomacy lifecycle smoke before expansion |
| `treasurer_reject_deal` | V1 partial | route support exists; do not promote without focused smoke |
| `alliance_break_peaceful` | V1 partial | implemented surface exists; do not promote/showcase without dedicated smoke and design approval |
| `alliance_betrayal` | V1 partial/high risk | do not promote in V1 without explicit exception |

## 4. V1 Frozen Rules

These rules define the V1 change boundary:

- No new role mechanics without explicit V2 decision or documented V1 freeze exception.
- No new economy layer.
- No new diplomacy model.
- No new alliance system.
- No Court rewrite.
- No Final rewrite.
- No Terminal rewrite.
- No new DB models or tables for V1 gameplay.
- No role registry runtime consumption without separate approval.
- No replacement of existing route permission gates with registry-driven gates in V1.
- No new Master Whisper actions beyond `quiet_support`, `crown_tax`, and `break_alliance`.
- No expansion of crest, towers, scrolls, keys, or extended economy into V1 UI.
- No exposing placeholder YAML actions as player-facing promises.
- Browser/pixel polish is allowed if it does not change gameplay.
- Operator checklist/runbook updates are allowed.
- Smoke tests and documentation are allowed.
- Bug fixes are allowed when they preserve V1 behavior and have focused verification.

## 5. Explicitly Deferred To V2

The following are deferred to V2 or later, supported by the role registry audit, migration audit, and runtime validation checkpoint:

| Deferred item | Reason |
|---|---|
| `embassy_offer` | Candidate diplomat action, but not V1 frozen; needs dedicated diplomacy lifecycle smoke and payoff contract. |
| `trade_contact` | Needs clear gameplay payoff and economy/resource boundary. |
| `map_route` | Touches map/location/expedition contracts and can expand quickly. |
| `sanction` | Can conflict with diplomacy/Court balance. |
| `alliance_decision` | Overlaps existing deal/alliance routes. |
| `rumor` | New Whisper mechanics are frozen after V1 package completion. |
| `hidden_signal` | Hidden-information design risk. |
| `blackmail` | High gameplay/safety/trust risk. |
| `exchange` | Reopens unfinished economy layer. |
| `investment` | Reopens unfinished economy layer. |
| `matrix` | Declared only; not live runtime. |
| `fill_table` | Declared only; not live runtime. |
| `dossier_sort` | Partial assignment support only. |
| `support_task` | House sworn role lacks V1 payoff. |
| `heraldic_step` | Crest/heraldry payoff disabled in V1. |
| `field_action` | Role/design not ready. |
| Role registry runtime consumption | Passive registry only in V1; runtime gates remain in code. |
| Race-condition hardening | Important technical tail, but not a scope reason to add mechanics. |
| Browser automation suite | Deferred; manual/browser validation comes first. |
| VPS production hardening | Deployment contour, not V1 runtime mechanic. |
| Broad legacy encoding cleanup | Cleanup tail; avoid broad churn before live unless active production text is broken. |
| Crest / heraldry payoff | Deferred V2 system. |
| Towers | Deferred V2 system. |
| Scrolls and keys | Deferred V2/meta-resource layer. |
| Expanded economy | Deferred V2 system. |

## 6. Runtime Validation References

Key checkpoint and smoke references:

| Reference | Commit | Purpose |
|---|---:|---|
| `docs/CHECKPOINT_MASTER_WHISPER_V1.md` | `a5169c3` | Documents completed Last Whisper V1 actions. |
| `docs/CHECKPOINT_MVP_RUNTIME_STABILIZATION.md` | `680fa51` | Records command-level stabilization of main runtime contours. |
| `docs/RUNTIME_STABILITY_VALIDATION_PASS.md` | `95dbcf9` | Maps remaining validation risks after stabilization. |
| `docs/ROLE_ACTION_REGISTRY_MIGRATION_AUDIT.md` | `2e2018e` | Defines why registry migration must be passive/controlled. |
| `docs/ROLE_ACTION_REGISTRY_V1.yaml` / README | `86d255e` | Passive V1 action boundary. |
| `docs/FINAL_TERMINAL_READINESS_AUDIT.md` | `2a153d9` | Defines safe late-game validation boundary. |
| `scripts/smoke_final_terminal_lifecycle.py` | `bd05590` | Confirms Court -> Last Whisper -> Final -> Terminal. |
| `docs/CHECKPOINT_RUNTIME_VALIDATED.md` | `4a0acf2` | Records command-level runtime validation across main V1 lifecycle. |

Current V1 smoke gate:

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

## 7. Exit Criteria For V1 Freeze

V1 may be unfrozen only if one of these is true:

1. A production-blocking bug cannot be fixed without a scoped runtime change.
2. Browser/pixel validation finds a live-blocking visibility issue that requires a template-only patch.
3. Operator rehearsal identifies a critical runbook mismatch that requires a small state or UI correction.
4. Stakeholders explicitly approve a V1 freeze exception with:
   - named action/contour;
   - reason it cannot wait for V2;
   - changed files;
   - smoke/manual verification plan;
   - rollback plan.

What does not justify unfreezing V1:

- "This would be cool tonight."
- Adding role depth after runtime validation.
- Making deferred YAML actions real without smoke coverage.
- Starting role registry runtime migration because the passive registry exists.
- Reopening crest/towers/economy because the data structures exist.

## 8. Current Status

PRISTOLOV_CORE V1 is frozen and runtime-validated.

The current work priority is:

1. browser/pixel validation;
2. operator checklist update;
3. live rehearsal for UX/show quality;
4. V2 planning only after V1 behavior is stable.

V1 should now be treated as a protected launch slice.
