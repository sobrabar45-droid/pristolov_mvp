# Role Action Registry Migration Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: audit only. No runtime migration implemented.

## Purpose

This audit defines the safest path from the current mixed role/action runtime to a canonical role-action registry.

The goal is not to add mechanics. The goal is to prevent new mechanics from becoming another hardcoded island across YAML, routes, templates, services, state builders, and docs.

## Files Inspected

- `docs/RUNTIME_STABILITY_VALIDATION_PASS.md`
- `docs/ROLE_ACTION_REGISTRY_AUDIT.md`
- `docs/CHECKPOINT_MASTER_WHISPER_V1.md`
- `app/game_templates/season1_core_v1/roles.yaml`
- `app/game_templates/season1_core_v1/acts.yaml`
- `app/game_templates/season1_core_v1/task_pools_diplomat.yaml`
- `app/game_templates/season1_core_v1/task_pools_lord.yaml`
- `app/game_templates/season1_core_v1/task_pools_maester.yaml`
- `app/game_templates/season1_core_v1/task_pools_treasurer.yaml`
- `app/game_templates/season1_core_v1/task_pools_whisper.yaml`
- `app/routes/player.py`
- `app/templates/player_room.html`
- `app/services/master_state_service.py`
- `app/models/player.py`
- `app/models/role.py`
- `app/models/house.py`

## Current Source Map

| Source | Owns Today | Notes |
|---|---|---|
| `roles.yaml` | declared assignment types per role | Not a live runtime registry. Contains placeholders and V2-style promises. |
| `acts.yaml` | act-level enabled assignment types | Old/template-level enablement. Does not gate current player-route mechanics. |
| `task_pools_*.yaml` | assignment/task pools and reward/fail payloads | Feeds assignment content; not a direct player action registry. |
| `app/routes/player.py` | real player-side runtime route gates and mutations | Main current source of truth for live player actions. |
| `app/templates/player_room.html` | visible controls and submit payloads | UI visibility can differ from YAML declarations. |
| `app/services/master_state_service.py` | Master/TV state exposure | Read-side contract for many actions. |
| `Role` model | role identity only | Stores `code`, `name`, `description`. No action metadata. |
| `Player` model | role assignment to player | No action metadata. |
| `House` model | resources/state affected by actions | No action metadata. |
| docs/checkpoints | human source of truth for readiness | Useful but not executable. |

## Current Definition Problem

There is no single canonical runtime role-action registry.

The project currently has three overlapping concepts:

- **Declared assignment types**: YAML labels such as `quiz`, `negotiation`, `truth_lie`, `treasury_choice`.
- **Route-driven live actions**: player endpoints such as duel challenge, deal create, Last Whisper action, expedition resolve.
- **Template-visible controls**: buttons and forms rendered by `player_room.html`.

These are not the same thing and should not be merged blindly.

## YAML-Declared But Not Implemented As Runtime Actions

These are declared in YAML but are not currently complete live player-route mechanics:

| role_code | declared action | status | recommendation |
|---|---|---|---|
| `lord_lady` | `strategic_choice` | partial assignment/UI concept | Freeze as assignment-only until redesigned. |
| `lord_lady` | `sanction` | declared only | Hide/defer. |
| `lord_lady` | `alliance_decision` | declared only | Hide/defer. |
| `diplomat` | `map_route` | declared/act-enabled only | Hide/defer; requires map/location contract audit. |
| `diplomat` | `embassy_offer` | declared only | Candidate after registry audit, but not V1 frozen runtime. |
| `diplomat` | `trade_contact` | declared only | Defer until payoff contract is clear. |
| `maester` | `matrix` | declared only | Hide/defer. |
| `maester` | `fill_table` | declared only | Hide/defer. |
| `maester` | `dossier_sort` | partial task-pool concept | Assignment-only until template support is verified. |
| `whisper_master` | `rumor` | declared only | Hide/defer; do not add new Whisper mechanics now. |
| `whisper_master` | `hidden_signal` | declared only | Hide/defer. |
| `whisper_master` | `blackmail` | declared only | Hide/defer. |
| `treasurer` | `exchange` | declared only | Hide/defer; economy risk. |
| `treasurer` | `investment` | declared only | Hide/defer; economy risk. |
| `house_sworn` | `support_task` | declared only | Hide/defer; role lacks V1 payoff. |
| `house_sworn` | `heraldic_step` | declared only | Hide/defer; crest/heraldry disabled in V1. |
| `house_sworn` | `field_action` | declared only | Hide/defer. |

## Implemented But Not Canonically Declared

These are real runtime actions but are not represented as canonical action entries in a registry:

| role_code | runtime action | source | mutates state | smoke |
|---|---|---|---:|---|
| `whisper_master` | `quiet_support` | `POST /player/last-whisper/action/{player_id}` | yes | `smoke_last_whisper_quiet_support.py` |
| `whisper_master` | `crown_tax` | `POST /player/last-whisper/action/{player_id}` | yes | `smoke_last_whisper_crown_tax.py` |
| `whisper_master` | `break_alliance` | `POST /player/last-whisper/action/{player_id}` | yes | `smoke_last_whisper_break_alliance.py` |
| `lord_lady` | `duel_challenge` | `POST /player/duels/challenge/{player_id}` | yes | `smoke_player_duel_lifecycle.py` |
| `lord_lady` | `duel_accept` | `POST /player/duels/accept/{player_id}/{duel_id}` | yes | `smoke_player_duel_lifecycle.py` |
| `lord_lady` | `duel_refuse` | `POST /player/duels/refuse/{player_id}/{duel_id}` | yes | `smoke_player_duel_lifecycle.py` |
| `lord_lady` | `alliance_break_peaceful` | `POST /player/alliances/break/{player_id}` | yes | none dedicated |
| `lord_lady` | `alliance_betrayal` | `POST /player/alliances/break/{player_id}` | yes | none dedicated |
| `lord_lady` | `expedition_create` | `POST /player/expedition/create/{player_id}` | yes | `smoke_expedition_lifecycle.py` |
| `lord_lady` / expedition party roles | `expedition_choose_location` | `POST /player/expedition/{expedition_id}/choose-location/{player_id}` | yes | `smoke_expedition_lifecycle.py` |
| `lord_lady` / expedition party roles | `expedition_resolve` | `POST /player/expedition/{expedition_id}/resolve/{player_id}` | yes | `smoke_expedition_lifecycle.py` |
| `diplomat` | `deal_create` | `POST /player/deals/create/{player_id}` | yes | indirect / treasurer smoke |
| any target House player | `deal_respond` | `POST /player/deals/respond/{player_id}` | yes | indirect |
| `treasurer` | `treasurer_confirm_deal` | `POST /player/deals/treasurer-confirm/{player_id}` | yes | `smoke_treasurer_resource_deal.py` |
| all roles | `assignment_answer` | `POST /player/assignments/{assignment_id}/answer` | yes | `smoke_assignment_reward_loop.py` |

## Template-Only / UI-Surface Actions

Some controls are visible or rendered in `player_room.html` but should not be treated as canonical until the registry is created:

| UI Surface | Runtime Backing | Risk |
|---|---|---|
| Last Whisper action buttons | backed by route and smoke | low |
| Duel challenge/accept/refuse | backed by route and smoke | low |
| Diplomacy deal create/respond | backed by route, partially smoked | medium |
| Treasurer confirm/reject | backed by route, confirm smoked | medium |
| Alliance peaceful break/betrayal | backed by route, not dedicated-smoked | high |
| Expedition create/route/resolve | backed by route and smoke | medium |
| Assignment answer UI | backed by route and smoke | medium |
| Crest piece deal fields | backed by diplomacy guard but V1 payoff unclear | medium/high |
| Resource deal fields | V1 UI limits resource types, but resource economy is mostly hidden | medium |

## V1 Frozen Action List

These are safe to freeze as V1 runtime actions because they exist, have an intended player role/surface, and are either smoke-covered or already part of covered setup.

| role_code | action_code | phase | source_of_truth | smoke_required |
|---|---|---|---|---|
| `whisper_master` | `quiet_support` | `last_whisper` | `GamePhase.payload["whisper_actions"]`, House influence | yes |
| `whisper_master` | `crown_tax` | `last_whisper` | `GamePhase.payload["whisper_actions"]`, House influence | yes |
| `whisper_master` | `break_alliance` | `last_whisper` | `GameDeal`, `GamePhase.payload["whisper_actions"]` | yes |
| `lord_lady` | `duel_challenge` | `duel` | `GameDuel` | yes |
| `lord_lady` | `duel_accept` | `duel` | `GameDuel` | yes |
| `lord_lady` | `duel_refuse` | `duel` | `GameDuel` | yes |
| `lord_lady` | `expedition_create` | `map`, `free_play` | `GameExpedition`, `GameMapVisit` | yes |
| `expedition_party` | `expedition_choose_location` | expedition active | `GameMapVisit` vote | yes |
| `expedition_party` | `expedition_resolve` | expedition active | `GameExpedition`, `GameMapVisit`, House resources | yes |
| `diplomat` | `deal_create` | `diplomacy`, `free_play` | `GameDeal` | should add dedicated diplomacy smoke before expansion |
| `house_member` | `deal_respond` | `diplomacy`, `free_play` | `GameDeal` | should add dedicated diplomacy smoke before expansion |
| `treasurer` | `treasurer_confirm_deal` | `diplomacy`, `free_play` | `GameDeal`, House resources | yes |
| `all_roles` | `assignment_answer` | active assignment | `GameAssignment`, House resources | yes |

V1 freeze rule:

```text
If an action is not in this list, do not expose it as a live player promise without a separate audit and smoke.
```

## V2 / Deferred Action List

| action_code | reason to defer |
|---|---|
| `embassy_offer` | safe candidate, but should wait for registry shape. |
| `trade_contact` | needs clear payoff contract. |
| `map_route` | touches map/location/expedition contracts. |
| `sanction` | can conflict with diplomacy/Court balance. |
| `alliance_decision` | overlaps existing deal/alliance routes. |
| `alliance_break_peaceful` | route exists but needs dedicated smoke and V1 design decision before promotion. |
| `alliance_betrayal` | route exists, mutates resources, high trust-risk. |
| `rumor` | overlaps completed Last Whisper layer; do not expand Whisper now. |
| `hidden_signal` | hidden-info design risk. |
| `blackmail` | high gameplay/safety risk. |
| `exchange` | reopens economy layer. |
| `investment` | reopens economy layer. |
| `matrix` | declared only. |
| `fill_table` | declared only. |
| `dossier_sort` | partial assignment support only. |
| `support_task` | house_sworn role lacks V1 payoff. |
| `heraldic_step` | crest/heraldry disabled in V1. |
| `field_action` | role/design not ready. |

## Proposed Canonical Schema

The safest first registry should be passive data, not runtime-driving logic.

Recommended shape:

```yaml
version: 1
actions:
  - action_code: quiet_support
    label: "Тихая поддержка"
    role_codes: ["whisper_master"]
    action_family: last_whisper
    phase_types: ["last_whisper"]
    surface: player
    status: v1_active
    implementation:
      route: "POST /player/last-whisper/action/{player_id}"
      service: null
      template: "app/templates/player_room.html"
    source_of_truth:
      model: "GamePhase"
      payload_path: "payload.whisper_actions"
      secondary_models: ["House"]
    mutates_state: true
    state_contract:
      player: ["last_whisper"]
      master: ["last_whisper", "recent_events"]
      tv: ["last_whisper", "recent_events"]
    smoke:
      command: "python scripts/smoke_last_whisper_quiet_support.py"
      required_before_ready: true
    risk: low
    v1_visibility: visible
```

Required fields:

- `action_code`
- `label`
- `role_codes`
- `action_family`
- `phase_types`
- `surface`
- `status`
- `implementation.route` or `implementation.assignment_type`
- `source_of_truth`
- `mutates_state`
- `state_contract`
- `smoke.command`
- `risk`
- `v1_visibility`

Recommended `status` values:

- `v1_active`
- `v1_hidden`
- `v2_deferred`
- `declared_only`
- `deprecated`

Recommended `action_family` values:

- `assignment`
- `diplomacy`
- `duel`
- `expedition`
- `last_whisper`
- `alliance`
- `economy`
- `map`
- `court`
- `admin`

## Migration Phases

### Phase 0: Freeze

Do not add new role mechanics.

Use the V1 frozen action list as the temporary human contract. Keep all existing smoke tests green.

### Phase 1: Passive Registry Document

Create a registry document or YAML file that mirrors current runtime behavior without being imported by runtime code.

Recommended path:

```text
docs/ROLE_ACTION_REGISTRY_V1_FROZEN.md
```

or, if a machine-readable file is preferred:

```text
app/game_templates/season1_core_v1/role_action_registry.v1.yaml
```

Do not wire it into runtime yet.

### Phase 2: Visibility Audit Against Registry

Compare `player_room.html` visible controls against the passive registry.

Output should identify:

- visible but not registry-approved controls;
- registry-approved but hidden controls;
- placeholder controls that must stay disabled or hidden.

### Phase 3: State Contract Annotation

For each registry action, document the exact player/master/tv state paths it depends on.

Do not refactor `master_state_service.py` yet.

### Phase 4: Smoke Gate Mapping

Attach a smoke command to every `v1_active` state-mutating action.

If no smoke exists, action cannot be promoted to `v1_active`.

### Phase 5: Optional Runtime Consumption

Only after the passive registry matches current runtime and all smokes pass, consider importing the registry for read-only UI metadata.

Initial runtime consumption should be limited to labels/help text, not permission gates.

### Phase 6: Permission Gate Migration

Move hardcoded role/phase gates behind registry only after:

- route behavior is unchanged;
- smoke tests pass before and after;
- every action has explicit source-of-truth and state-contract fields.

This phase should be a separate implementation project, not a cleanup side-effect.

## No-Go Risks

Do not do these during the first migration:

- Do not replace route guards with registry guards in one patch.
- Do not make YAML `roles.yaml` the live action registry by default.
- Do not expose declared-only actions because they appear in YAML.
- Do not merge assignment types and route actions into a single flat concept without `action_family`.
- Do not add `embassy_offer`, `trade_contact`, or `map_route` during migration.
- Do not migrate `alliance_betrayal` into V1 without dedicated smoke and gameplay approval.
- Do not refactor `master_state_service.py` as part of registry creation.
- Do not add DB models/tables for registry in V1.

## Smoke Tests That Must Remain Green

Before and after any registry-related implementation, run:

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

Additional recommended smoke before promoting diplomacy actions:

```powershell
python scripts/smoke_diplomacy_lifecycle.py
```

This smoke does not exist yet. It should cover deal create/respond reject/accept, duplicate guards, alliance conflict guards, and Master/TV visibility.

## Safest Migration Path

The safest path is:

1. Freeze current V1 action list in docs.
2. Create a passive registry matching existing runtime.
3. Use the registry as a review/checklist artifact.
4. Add missing diplomacy lifecycle smoke before any Diplomacy expansion.
5. Only then let templates consume registry labels/help text.
6. Leave route guards hardcoded until a dedicated gate-migration pass.

This approach avoids breaking current smoke tests because the first registry versions do not control runtime behavior.

## Findings

- YAML currently defines role assignment promises, not the real runtime action contract.
- `player.py` and `player_room.html` are the actual V1 role-action implementation surface.
- `master_state_service.py` is the read-side contract but not an action registry.
- `Role`, `Player`, and `House` models do not carry action metadata.
- The V1 active set is now smoke-backed enough to freeze.
- The biggest immediate risk is not missing mechanics; it is accidentally exposing declared-only or partially implemented role actions.

## Recommendation

Do not implement new mechanics next.

Next artifact should be a passive frozen registry:

```text
docs/ROLE_ACTION_REGISTRY_V1_FROZEN.md
```

After that, add a focused diplomacy lifecycle smoke before promoting any new Diplomat action.
