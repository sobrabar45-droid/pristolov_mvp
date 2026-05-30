# Role Action Registry Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Scope: role action declarations, player routes, runtime effects, Master/TV visibility, and smoke coverage.

## Summary

The project now has a strong V1 runtime core for:

- Maester question participation
- Lord/Lady duel ownership
- Diplomat negotiation/deal flow
- Treasurer deal confirmation
- Master Whisper V1 actions

The largest mismatch is still between declared role action codes in templates and the smaller set of actions that have real runtime effects.

## Role Status Table

| Role | Status | Ready actions | Partial actions | Placeholder actions |
|---|---|---|---|---|
| `lord_lady` | PARTIAL | expedition planning, duel challenge/accept/refuse, alliance break | strategic choice | sanction, alliance decision |
| `diplomat` | PARTIAL | negotiation, deal create/respond | none | map_route, embassy_offer, trade_contact |
| `maester` | READY/PARTIAL | quiz, timeline-style assignments | dossier_sort | matrix, fill_table |
| `whisper_master` | READY for V1 | truth_lie, quiet_support, crown_tax, break_alliance | none | rumor, hidden_signal, blackmail |
| `treasurer` | PARTIAL | treasury_choice, treasurer_confirm | risk_trade | exchange, investment |
| `house_sworn` | PLACEHOLDER | none | none | support_task, heraldic_step, field_action |

## Existing Runtime Effects

### Lord/Lady

Runtime-ready surfaces:

- expedition planning and completion
- player-side duel challenges
- duel accept/refuse
- alliance break route

Smoke coverage:

- No focused command-level smoke found for the Lord/Lady action set.

### Diplomat

Runtime-ready surfaces:

- create deal
- respond to deal
- create alliance
- accept alliance

Current deal types:

- `resource`
- `crest_piece`
- `open_agreement`
- `alliance`

Smoke coverage:

- No dedicated diplomacy smoke yet.
- Last Whisper break-alliance smoke uses live diplomacy routes to create and accept an alliance.

### Maester

Runtime-ready surfaces:

- assignment answer pipeline
- question/reward feedback pipeline

Smoke coverage:

- No focused Maester smoke found.

### Master Whisper

Runtime-ready V1 surfaces:

- `quiet_support`: selected House gains `+1 influence`
- `crown_tax`: single influence leader loses `1 influence`, with honest zero-delta text
- `break_alliance`: selected active alliance changes from `alliance_active` to `alliance_broken`

Smoke coverage:

- `scripts/smoke_last_whisper_quiet_support.py`
- `scripts/smoke_last_whisper_crown_tax.py`
- `scripts/smoke_last_whisper_break_alliance.py`

### Treasurer

Runtime-ready surfaces:

- treasury assignment flow
- confirmation of accepted resource deals

Smoke coverage:

- No focused Treasurer smoke found.

### House Sworn

Runtime-ready surfaces:

- No dedicated V1 action found.

Smoke coverage:

- None found.

## Top Mismatches

1. `roles.yaml` declares more role action codes than the runtime currently supports.
2. `diplomat` declares `map_route`, `embassy_offer`, and `trade_contact`, but only negotiation/deal flow exists.
3. `house_sworn` is declared but has no meaningful runtime action surface.
4. `treasurer` declares economy-style actions, but the real runtime is mostly assignment flow plus deal confirmation.
5. `whisper_master` template actions such as `rumor`, `hidden_signal`, and `blackmail` are separate from the now-working Last Whisper V1 action framework.

## Recommendation

Safest next role/action after Master Whisper V1:

- `diplomat.embassy_offer`

Most valuable next role/action:

- `diplomat.trade_contact`, once the expected payoff is defined.

Most dangerous action to defer:

- `diplomat.map_route`, because it touches map/location contracts and can become a broader scenario-system change.

## Risks

- Stringly typed role/action/status values can drift.
- Template-declared actions can imply gameplay that does not exist yet.
- Several role surfaces lack command-level smoke coverage.
- Old legacy strings still contain encoding noise in unrelated files.
- Master/TV visibility works best for existing state contracts; adding new action families should avoid creating parallel feeds.
