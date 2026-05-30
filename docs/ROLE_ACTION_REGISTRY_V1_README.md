# Passive V1 Role Action Registry

## Purpose

`docs/ROLE_ACTION_REGISTRY_V1.yaml` is a passive registry of the frozen V1 role/action surface.

It exists to prevent scope creep before V2. It documents what is implemented, what is partially covered, what is smoke-covered, and what must stay deferred.

## Important Contract

This registry is not read by runtime code.

Permission gates remain in the existing implementation:

- `app/routes/player.py`
- `app/templates/player_room.html`
- `app/services/master_state_service.py`
- scenario/dev/operator routes
- existing service guards

Do not treat this YAML file as an authorization layer.

## How To Use It

Use this registry as a review checklist before adding or exposing role mechanics:

1. If an action is `v1_frozen`, it is part of the current V1 runtime promise.
2. If an action is `v1_partial`, it exists but should not be expanded without dedicated smoke coverage or a small audit.
3. If an action is `v2_deferred`, it should not appear as a live player promise in V1.
4. If a new button, route, or state block is added, update the passive registry in the same documentation pass.

## Migration Rule

Future migration should start read-only.

Safe first steps:

- compare visible UI controls against this registry;
- attach missing smoke scripts to `v1_partial` actions;
- use registry labels/help text only after behavior is already stable;
- keep route guards hardcoded until a dedicated gate-migration project.

Unsafe first steps:

- replacing route permission checks with registry checks;
- making `roles.yaml` the live runtime action source;
- exposing YAML-declared placeholder actions as real mechanics;
- adding new role mechanics during registry migration.

## Smoke Gate

All `v1_frozen` state-mutating actions should keep their smoke commands green before any role/action migration:

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

## Next Recommended Step

Before adding new Diplomat actions, create a dedicated diplomacy lifecycle smoke that covers:

- deal create;
- accept;
- reject;
- duplicate guard;
- alliance conflict guard;
- Master/TV visibility.

Only after that should `embassy_offer` or `trade_contact` be reconsidered.
