# Role Action Registry Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Status: audit after Master Whisper V1 checkpoint.

## Purpose

This document records the current role/action runtime after Master Whisper V1 and proposes the smallest canonical registry shape to use before adding new mechanics such as `embassy_offer`, `trade_contact`, or `map_route`.

It is an audit document only. It does not define a new runtime system yet.

## Current Source Of Truth

There is no single canonical runtime registry for role actions today.

Current action truth is mixed across:

- `app/game_templates/season1_core_v1/roles.yaml`: declared role assignment types.
- `app/game_templates/season1_core_v1/acts.yaml`: act-level enabled assignment types.
- `app/game_templates/season1_core_v1/task_pools_*.yaml`: assignment pools and task effects.
- `app/services/template_service.py`: validates allowed role assignment types.
- `app/routes/player.py`: hardcoded role gates and runtime mutations.
- `app/templates/player_room.html`: player-side control visibility and action submit calls.
- `app/services/master_state_service.py`: Master/TV state exposure.
- `docs/CHECKPOINT_MASTER_WHISPER_V1.md`: documents completed Last Whisper actions.

Models do not currently own action availability:

- `Role` stores `code`, `name`, and `description`.
- `Player` stores `role_id`, `house_id`, and links to assignments.
- `House` stores resources and identity.

## Current Role/Action Table

| role_code | action_code | label | phase | implemented | mutates_state | smoke_covered | source_file | risk | recommendation |
|---|---|---|---|---|---|---|---|---|---|
| `lord_lady` | `expedition_create` | Create expedition | map/free play UI | yes | yes | no | `app/routes/player.py`, `player_room.html` | MEDIUM | Keep as existing runtime action; add smoke before expanding. |
| `lord_lady` | `expedition_choose_location` | Choose expedition route | expedition active | yes | yes | no | `app/routes/player.py`, `player_room.html` | MEDIUM | Keep; document as expedition sub-action. |
| `lord_lady` | `expedition_resolve` | Resolve expedition | expedition active | yes | yes | no | `app/routes/player.py`, `player_room.html` | MEDIUM | Add focused smoke if expedition becomes launch-critical. |
| `lord_lady` | `duel_challenge` | Challenge House to duel | duel | yes | yes | no | `app/routes/player.py`, `player_room.html`, `duel_service.py` | MEDIUM | Keep; add smoke for player-side duel lifecycle. |
| `lord_lady` | `duel_accept` | Accept duel | duel | yes | yes | no | `app/routes/player.py`, `player_room.html`, `duel_service.py` | MEDIUM | Keep; add smoke with challenge/refuse/resolve visibility. |
| `lord_lady` | `duel_refuse` | Refuse duel | duel | yes | yes | no | `app/routes/player.py`, `player_room.html`, `duel_service.py` | MEDIUM | Keep; add smoke with refusal branch. |
| `lord_lady` | `alliance_break` | Break active alliance | diplomacy/free play | yes | yes | no | `app/routes/player.py`, `player_room.html` | HIGH | Keep separate from Whisper break; needs smoke if used in live V1. |
| `lord_lady` | `right_of_move` | Right of move assignment | assignment flow | partial | yes | no | `task_pools_lord.yaml`, `assignment_service.py` | MEDIUM | Treat as assignment action, not direct player route. |
| `lord_lady` | `strategic_choice` | Strategic choice | declared/template | partial | unclear | no | `roles.yaml`, `task_pools_lord.yaml` | MEDIUM | Normalize naming with `right_of_move` before adding more. |
| `lord_lady` | `sanction` | Sanction | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; do not implement without separate design. |
| `lord_lady` | `alliance_decision` | Alliance decision | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; avoid until diplomacy registry is clearer. |
| `diplomat` | `deal_create` | Create deal | diplomacy/free_play | yes | yes | indirect | `app/routes/player.py`, `player_room.html` | MEDIUM | Canonicalize as runtime action behind `negotiation`. |
| `diplomat` | `deal_respond` | Respond to deal | diplomacy/free_play | yes | yes | indirect | `app/routes/player.py`, `player_room.html` | MEDIUM | Canonicalize as runtime action behind `negotiation`. |
| `diplomat` | `negotiation` | Negotiation assignment | assignment/diplomacy | partial | yes | indirect | `task_pools_diplomat.yaml`, `app/routes/player.py` | MEDIUM | Keep as parent action for deal create/respond. |
| `diplomat` | `embassy_offer` | Embassy offer | declared only | no | no | no | `roles.yaml`, `template_service.py` | LOW | Safest next action; implement through `GameDeal.offer`/`open_agreement`. |
| `diplomat` | `trade_contact` | Trade contact | declared only | no | no | no | `roles.yaml`, `template_service.py` | MEDIUM | Valuable next action; needs payoff contract first. |
| `diplomat` | `map_route` | Map route | declared/act-enabled | no | no | no | `roles.yaml`, `acts.yaml`, `template_service.py` | HIGH | Defer; requires map/location audit. |
| `maester` | `quiz` | Quiz assignment | assignment flow | yes | yes | no | `task_pools_maester.yaml`, `assignment_service.py` | LOW | Keep as assignment action; add answer/reward smoke later. |
| `maester` | `timeline` | Timeline assignment UI | assignment flow | yes | yes | no | `task_pools_maester.yaml`, `player_room.html` | LOW | Treat as UI mode under `quiz`/assignment pipeline. |
| `maester` | `dossier_sort` | Dossier sort | declared/partial pool | partial | unclear | no | `roles.yaml`, `task_pools_maester.yaml` | MEDIUM | Audit assignment template support before expanding. |
| `maester` | `matrix` | Matrix | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; defer. |
| `maester` | `fill_table` | Fill table | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; defer. |
| `whisper_master` | `truth_lie` | Truth/lie assignment | assignment flow | yes | yes | no | `task_pools_whisper.yaml`, `assignment_service.py` | LOW | Keep separate from Last Whisper actions. |
| `whisper_master` | `quiet_support` | Tikhaya podderzhka | last_whisper | yes | yes | yes | `app/routes/player.py`, `player_room.html`, `master_state_service.py` | LOW | Complete V1 action. |
| `whisper_master` | `crown_tax` | Nalog na koronu | last_whisper | yes | yes | yes | `app/routes/player.py`, `player_room.html`, `master_state_service.py` | LOW | Complete V1 action. |
| `whisper_master` | `break_alliance` | Razryv soyuza | last_whisper | yes | yes | yes | `app/routes/player.py`, `player_room.html`, `master_state_service.py` | LOW | Complete V1 action. |
| `whisper_master` | `rumor` | Rumor | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Do not add new Whisper mechanics immediately. |
| `whisper_master` | `hidden_signal` | Hidden signal | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Defer; overlaps hidden-information design. |
| `whisper_master` | `blackmail` | Blackmail | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Defer; needs separate design and safety review. |
| `treasurer` | `treasury_choice` | Treasury choice assignment | assignment flow | yes | yes | no | `task_pools_treasurer.yaml`, `assignment_service.py` | MEDIUM | Keep as assignment action; verify resource effects before expansion. |
| `treasurer` | `treasurer_confirm` | Confirm resource deal | diplomacy/free_play | yes | yes | no | `app/routes/player.py`, `player_room.html` | MEDIUM | Add smoke if resource deals return to V1 focus. |
| `treasurer` | `risk_trade` | Risk trade | assignment option | partial | yes | no | `task_pools_treasurer.yaml`, `assignment_service.py` | MEDIUM | Treat as option inside `treasury_choice`, not top-level action yet. |
| `treasurer` | `exchange` | Exchange | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; defer. |
| `treasurer` | `investment` | Investment | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; defer. |
| `house_sworn` | `support_task` | Support task | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; needs role design before implementation. |
| `house_sworn` | `heraldic_step` | Heraldic step | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; crest/heraldry is not active V1 payoff. |
| `house_sworn` | `field_action` | Field action | declared only | no | no | no | `roles.yaml`, `template_service.py` | HIGH | Placeholder; defer. |
| `all_roles` | `assignment_answer` | Answer assignment | assignment flow | yes | yes | no | `app/routes/player.py`, `assignment_service.py`, `player_room.html` | MEDIUM | Treat as shared transport, not a role-specific mechanic. |

## What Mutates Runtime State

State-mutating action families:

- Last Whisper actions: `quiet_support`, `crown_tax`, `break_alliance`.
- Diplomacy actions: `deal_create`, `deal_respond`, `treasurer_confirm`, `alliance_break`.
- Duel actions: `duel_challenge`, `duel_accept`, `duel_refuse`.
- Expedition actions: `expedition_create`, `expedition_choose_location`, `expedition_resolve`.
- Assignment answers: `assignment_answer`, including role task rewards/fail effects.

Display/status-only surfaces:

- `last_whisper.available_actions`
- `last_whisper.available_target_houses`
- `last_whisper.available_alliances`
- Master/TV deal lists
- Master/TV Last Whisper event rendering
- player role hints and phase guidance

## Smoke Coverage

Focused command-level smoke exists for:

- `quiet_support`: `scripts/smoke_last_whisper_quiet_support.py`
- `crown_tax`: `scripts/smoke_last_whisper_crown_tax.py`
- `break_alliance`: `scripts/smoke_last_whisper_break_alliance.py`

Indirect smoke coverage:

- `deal_create` / `deal_respond` are exercised by the `break_alliance` smoke because it creates and accepts an alliance through live player routes.

Missing smoke coverage:

- Player-side duel lifecycle.
- Expedition lifecycle.
- Treasurer resource deal confirmation.
- Generic assignment answer/reward pipeline.
- Browser UI automation for Last Whisper controls.

## Safe Candidates Next

1. `diplomat.embassy_offer`

Use existing `GameDeal` and `offer` payload. The smallest shape is an `open_agreement` with a stable metadata marker, for example `offer.meta_action = "embassy_offer"`.

2. Master/TV event presentation polish

This can improve clarity without changing core mechanics.

3. Role Action Registry cleanup

Create a code-level registry only after this audit is accepted, ideally as a read-only declaration first.

## Dangerous Candidates

- `diplomat.map_route`: touches map/location/expedition contracts and should get a separate audit.
- `whisper_master.blackmail`: likely needs hidden-information and safety rules.
- `treasurer.exchange` / `treasurer.investment`: can reopen the unfinished economy layer.
- `house_sworn.*`: currently lacks a clear V1 role promise.
- `lord_lady.sanction` / `lord_lady.alliance_decision`: can conflict with diplomacy and court/final balance.

## Minimal Canonical Registry Shape

Recommended future registry item shape:

```yaml
- role_code: diplomat
  action_code: embassy_offer
  label: "Embassy offer"
  phase_types: ["diplomacy", "free_play"]
  surface: "player"
  implementation:
    route: "/player/deals/create/{player_id}"
    service: null
    template: "app/templates/player_room.html"
  state_contract:
    player: ["incoming_deals", "available_deal_houses"]
    master: ["deals"]
    tv: ["deals"]
  mutates_state: true
  source_of_truth:
    model: "GameDeal"
    payload_path: "offer"
  smoke:
    command: null
    required_before_ready: true
  status: "planned"
  risk: "LOW"
```

Minimum required fields:

- `role_code`
- `action_code`
- `label`
- `phase_types`
- `surface`
- `route` or `assignment_type`
- `source_of_truth`
- `mutates_state`
- `state_contract`
- `smoke.command`
- `status`
- `risk`

The registry should initially be documentation or a passive data file. It should not drive runtime gates until the existing hardcoded role gates are reconciled.

## Recommendations

1. Do not add new Whisper mechanics immediately.
2. Treat `LAST_WHISPER_ACTIONS` as a completed V1 local registry, not the global role registry.
3. Normalize Diplomacy next, starting with `embassy_offer`.
4. Before implementing `trade_contact`, decide whether it is only a recorded diplomatic contact or a real resource/influence payoff.
5. Avoid `map_route` until map/location and expedition contracts are audited together.
6. Add smoke tests before marking any new action `READY`.

## Risks And Unknowns

- There is no code-level canonical action registry yet.
- Several declared actions in `roles.yaml` are placeholders and can overpromise UI/gameplay.
- Some action labels and legacy strings still contain unrelated encoding noise in older files.
- Current smoke coverage is strong only for Last Whisper V1.
- Near-simultaneous Last Whisper double submit still has a known race-condition risk.
