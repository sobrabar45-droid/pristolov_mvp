# Smoke Coverage Audit

Project: `D:\Projects\pristolov_mvp`
Date: 2026-05-31
Scope: implemented runtime actions, state mutations, and automated smoke coverage.

## Purpose

This audit maps gameplay/runtime actions that mutate current game state and checks whether they have command-level smoke coverage.

It is documentation only. It does not change runtime code, mechanics, data models, or tests.

## Files Inspected

- `scripts/smoke_last_whisper_quiet_support.py`
- `scripts/smoke_last_whisper_crown_tax.py`
- `scripts/smoke_last_whisper_break_alliance.py`
- `scripts/smoke_recent_events_contract.py`
- `docs/CHECKPOINT_MASTER_WHISPER_V1.md`
- `docs/CHECKPOINT_HOUSE_DUEL_MVP.md`
- `docs/CHECKPOINT_MANUAL_GOLD_CONTROL.md`
- `docs/ROLE_ACTION_REGISTRY_AUDIT.md`
- `docs/DIPLOMACY_RUNTIME_AUDIT.md`
- `docs/EVENT_PRESENTATION_AUDIT.md`
- `app/routes/player.py`
- `app/routes/dev.py`
- `app/routes/gold.py`
- `app/services/assignment_service.py`
- `app/services/court_service.py`
- `app/services/diplomacy_service.py`
- `app/services/duel_service.py`
- `app/services/gold_service.py`
- `app/services/resource_service.py`
- `app/services/scenario_service.py`
- `app/services/expedition_service.py`
- `app/services/map_runtime_service.py`
- `app/services/master_state_service.py`

## Coverage Levels

- `DEDICATED`: a focused smoke script exists for this action or contract.
- `INDIRECT`: exercised only as setup or side path inside another smoke.
- `MANUAL_CHECKPOINT`: documented manual/live verification exists, but no command smoke.
- `NONE`: no smoke or clear command-level verification found.
- `SETUP_ONLY`: used by smoke scripts to prepare runtime, but not itself treated as gameplay coverage.

## Runtime Mutation Table

| action | source | mutates_state | smoke_script | coverage_level | risk | recommended_next_test |
|---|---|---:|---|---|---|---|
| `last_whisper.quiet_support` | `POST /player/last-whisper/action/{player_id}` in `app/routes/player.py` | yes: target House `+1 influence`, `GamePhase.payload["whisper_actions"]` | `scripts/smoke_last_whisper_quiet_support.py` | DEDICATED | LOW | Keep as regression gate before Whisper/event changes. |
| `last_whisper.crown_tax` | `POST /player/last-whisper/action/{player_id}` | yes: leader influence delta, whisper event | `scripts/smoke_last_whisper_crown_tax.py` | DEDICATED | LOW | Keep; extend only if leader rules change. |
| `last_whisper.break_alliance` | `POST /player/last-whisper/action/{player_id}` | yes: selected `GameDeal.status` to `alliance_broken`, offer break metadata, whisper event | `scripts/smoke_last_whisper_break_alliance.py` | DEDICATED | LOW | Keep; rerun before diplomacy/alliance changes. |
| `recent_events` derived contract | `app/services/master_state_service.py` | no gameplay mutation; read-only derived state | `scripts/smoke_recent_events_contract.py` | DEDICATED | LOW | Keep as presentation contract gate. |
| `player.deal_create` | `POST /player/deals/create/{player_id}` | yes: creates `GameDeal` | indirectly inside `scripts/smoke_last_whisper_break_alliance.py` | INDIRECT | MEDIUM | Add focused diplomacy smoke for create/respond/reject/counter/visibility. |
| `player.deal_respond_accept_alliance` | `POST /player/deals/respond/{player_id}` | yes: `GameDeal.status` to `alliance_active`, alliance influence bonus | indirectly inside `scripts/smoke_last_whisper_break_alliance.py` | INDIRECT | HIGH | Add alliance lifecycle smoke: create, accept, duplicate/alliance-conflict guard, Master/TV state. |
| `player.deal_respond_reject` | `POST /player/deals/respond/{player_id}` | yes: `GameDeal.status` to `rejected` | none | NONE | MEDIUM | Add reject branch to diplomacy smoke. |
| `player.deal_respond_resource_accept_waiting_treasurer` | `POST /player/deals/respond/{player_id}` | yes: resource deal to `accepted_waiting_treasurer` | none | NONE | HIGH | Add resource deal smoke before re-enabling resource economy in live UI. |
| `player.treasurer_confirm_deal` | `POST /player/deals/treasurer-confirm/{player_id}` | yes: transfers resources and completes/rejects deal | none | NONE | HIGH | Add treasurer resource-transfer smoke: confirm, reject, insufficient balance, Master/TV visibility. |
| `player.alliance_break_peaceful` | `POST /player/alliances/break/{player_id}` | yes: `GameDeal.status` to `alliance_broken` | none | NONE | HIGH | Add Lord/Lady alliance-break smoke or keep UI deferred; overlaps Whisper break but uses different role gate and route. |
| `player.alliance_break_betrayal` | `POST /player/alliances/break/{player_id}` | yes: alliance status plus gold/influence deltas | none | NONE | HIGH | Defer or add smoke before exposing; high trust-risk because it changes multiple resources. |
| `dev.diplomacy.propose_deal` | `POST /dev/games/{room_code}/diplomacy/propose-deal` | yes: creates `GameDeal` through legacy/dev service path | none | NONE | MEDIUM | Add only if dev diplomacy console remains supported; otherwise prefer player-route smoke. |
| `dev.diplomacy.respond_deal` | `POST /dev/games/{room_code}/diplomacy/respond-deal/{deal_id}` | yes: accepts/rejects deal, may transfer resources | none | NONE | MEDIUM | Cover indirectly through future diplomacy smoke only if route is still used. |
| `dev.diplomacy.counter_deal` | `POST /dev/games/{room_code}/diplomacy/counter-deal/{deal_id}` | yes: marks original `countered`, creates child `GameDeal` | none | NONE | MEDIUM | Add counter branch to diplomacy smoke if counter-offers are live-facing. |
| `dev.diplomacy.cancel_deal` | `POST /dev/games/{room_code}/diplomacy/cancel-deal/{deal_id}` | yes: cancels pending deal | none | NONE | MEDIUM | Add cancel branch to diplomacy smoke if exposed in Master UI. |
| `player.duel_challenge` | `POST /player/duels/challenge/{player_id}` | yes: creates `GameDuel` | none | NONE | HIGH | Highest-priority next smoke: Lord challenge, target accept/refuse, normal player blocked, Master/TV state. |
| `player.duel_accept` | `POST /player/duels/accept/{player_id}/{duel_id}` | yes: `GameDuel.status` to `accepted` | none | NONE | HIGH | Include in player-side duel lifecycle smoke. |
| `player.duel_refuse` | `POST /player/duels/refuse/{player_id}/{duel_id}` | yes: `GameDuel.status` to `refused`, influence transfer | none | NONE | HIGH | Include refusal branch; assert influence deltas and event/state visibility. |
| `dev.duel_challenge` | `POST /dev/games/{room_code}/duels/challenge` | yes: creates `GameDuel` | none | MANUAL_CHECKPOINT | MEDIUM | Existing duel checkpoint is manual; add dev console smoke only if operator route remains live-critical. |
| `dev.duel_accept` | `POST /dev/games/{room_code}/duels/{duel_id}/accept` | yes: `GameDuel.status` to `accepted` | none | MANUAL_CHECKPOINT | MEDIUM | Prefer player-side lifecycle smoke first. |
| `dev.duel_refuse` | `POST /dev/games/{room_code}/duels/{duel_id}/refuse` | yes: `GameDuel.status` to `refused`, influence transfer | none | MANUAL_CHECKPOINT | HIGH | Add coverage if host can still refuse from console. |
| `dev.duel_resolve` | `POST /dev/games/{room_code}/duels/{duel_id}/resolve` | yes: resolves duel, gold transfer, influence transfer, tower/live bonus metadata | none | MANUAL_CHECKPOINT | HIGH | Add resolve branch to duel smoke; assert gold ledger and influence deltas. |
| `gold.grant` | `POST /gold/houses/{house_id}/grant` | yes: `House.resource_gold`, `HouseGoldTransaction` | none | MANUAL_CHECKPOINT | MEDIUM | Add minimal gold ledger smoke if manual gold remains live operator tool. |
| `gold.spend` | `POST /gold/houses/{house_id}/spend` | yes: `House.resource_gold`, `HouseGoldTransaction` | none | MANUAL_CHECKPOINT | MEDIUM | Same smoke should assert overspend rejection. |
| `gold.grant_from_check` | `POST /gold/houses/{house_id}/grant-from-check` | yes or no depending threshold: gold transaction | none | NONE | MEDIUM | Add only when bar/check integration is live. |
| `gold.apply_expedition` | `POST /gold/houses/{house_id}/apply-expedition` | yes: expedition gold ledger path | none | NONE | MEDIUM | Cover through expedition smoke rather than standalone if possible. |
| `gold.pvp_resolve` | `POST /gold/pvp/resolve` | yes: PvP gold transfer ledger | none | NONE | HIGH | Prefer duel resolve smoke because it is the live owner of PvP gold. |
| `player.expedition_create` | `POST /player/expedition/create/{player_id}` | yes: creates `GameExpedition`, writes `GameMapVisit` plan event | none | NONE | HIGH | Add expedition lifecycle smoke: create, role/member validation, choose route, resolve. |
| `player.expedition_choose_location` | `POST /player/expedition/{expedition_id}/choose-location/{player_id}` | yes: records/updates `GameMapVisit` vote | none | NONE | MEDIUM | Include in expedition lifecycle smoke. |
| `player.expedition_resolve` | `POST /player/expedition/{expedition_id}/resolve/{player_id}` | yes: resolves expedition, applies reward/penalty resources, writes outcome visit | none | NONE | HIGH | Include exact resource delta and Master/TV map event visibility. |
| `player.explore_map_legacy` | `POST /player/explore/{player_id}` | yes: random resource mutation, `GameExpedition`, `GameMapVisit` | none | NONE | HIGH | Audit/deprecate or smoke before any live use; random outcome makes it brittle. |
| `dev.map_explore` | `POST /dev/games/{room_code}/map/explore` | yes: map visit/outcome through map runtime service | none | NONE | MEDIUM | Add only after map/location contract audit. |
| `dev.expedition_create` | `POST /dev/houses/{house_id}/expeditions` | yes: creates `GameExpedition` | none | NONE | MEDIUM | Prefer player expedition smoke first. |
| `dev.expedition_members` | `POST /dev/expeditions/{expedition_id}/members` | yes: expedition/member state | none | NONE | MEDIUM | Cover only if dev expedition tools remain used. |
| `dev.expedition_approve` | `POST /dev/expeditions/{expedition_id}/approve` | yes: expedition approval/status | none | NONE | MEDIUM | Cover only if dev expedition tools remain used. |
| `dev.map_explore_expedition` | `POST /dev/games/{room_code}/map/explore-expedition` | yes: expedition/map runtime outcome | none | NONE | MEDIUM | Cover through map/expedition smoke after contract audit. |
| `assignment.answer` | `POST /player/assignments/{assignment_id}/answer` and `POST /dev/answer-assignment/{assignment_id}` | yes: assignment status, answer/result payload, optional resources | none | NONE | HIGH | Add question reward smoke: correct answer gives +1 influence, wrong answer no delta, Master/TV/player feedback. |
| `host_round.start_series` | `POST /dev/host-rounds/start-series/{room_code}/{round_code}` | yes: starts `GameHostRound`, assignments/questions | none | NONE | HIGH | Add host question round smoke before public rehearsal automation. |
| `host_round.open_next_question` | `POST /dev/host-rounds/{host_round_id}/open-next-question` | yes: runtime question status, assignments, Court sync if court round | none | NONE | HIGH | Include in host question round smoke. |
| `host_round.host_continue` | `POST /dev/host-rounds/{host_round_id}/host-continue` | yes: advances/finishes host round | none | NONE | MEDIUM | Include after answer/reward smoke. |
| `host_round.force_close_question` | `POST /dev/host-rounds/{host_round_id}/force-close-question` | yes: closes active question | none | NONE | MEDIUM | Add only if operator uses it live. |
| `court.generate_bracket` | `POST /dev/court/generate-bracket/{room_code}` | yes: Court phase payload/bracket | none | MANUAL_CHECKPOINT | HIGH | Add Court lifecycle smoke: bracket, pair, question, mark, winner, next, finish. |
| `court.start_pair` | `POST /dev/court/start-pair/{room_code}` | yes: Court active pair state | none | MANUAL_CHECKPOINT | HIGH | Include in Court lifecycle smoke. |
| `court.open_question` | `POST /dev/court/open-question/{room_code}` | yes: Court question/runtime state | none | MANUAL_CHECKPOINT | HIGH | Include in Court lifecycle smoke. |
| `court.mark_result` | `POST /dev/court/mark-result/{room_code}` | yes: per-side Court result | none | MANUAL_CHECKPOINT | HIGH | Include in Court lifecycle smoke. |
| `court.extra_question` | `POST /dev/court/extra-question/{room_code}` | yes: Court tiebreak/extra question state | none | NONE | MEDIUM | Add branch after happy-path Court smoke exists. |
| `court.confirm_pair_winner` | `POST /dev/court/confirm-pair-winner/{room_code}` | yes: Court pair winner state | none | MANUAL_CHECKPOINT | HIGH | Include in Court lifecycle smoke. |
| `court.next_pair` | `POST /dev/court/next-pair/{room_code}` | yes: advances Court pair or finishes Court | none | MANUAL_CHECKPOINT | HIGH | Include in Court lifecycle smoke and transition to Last Whisper/Final. |
| `scenario.apply` | `POST /dev/games/{room_code}/scenario/apply` | yes: applies scenario/runtime setup | used by all smoke scripts | SETUP_ONLY | MEDIUM | Add scenario smoke only if scenario director changes. |
| `scenario.start_next_round` | `POST /dev/games/{room_code}/scenario/start-next-round` | yes: creates/starts next round or system phase | none | NONE | HIGH | Add flow smoke for active scenario order: diplomacy -> last_whisper -> final. |
| `scenario.advance` | `POST /dev/games/{room_code}/scenario/advance` | yes: closes current and advances scenario | none | NONE | HIGH | Add scenario director smoke because this guards live flow integrity. |
| `phase.open` | `POST /dev/games/{room_code}/open-phase/{phase_type}` | yes: opens `GamePhase` | used by smoke setup | SETUP_ONLY | MEDIUM | Covered as helper, but not verified as full phase lifecycle. |
| `phase.close` | `POST /dev/games/{room_code}/close-phase/{phase_type}` | yes: closes `GamePhase` | none | NONE | MEDIUM | Add if phase lifecycle bugs recur. |
| `dev.reset_runtime` | `POST /dev/games/{room_code}/reset-runtime` | yes: destructive test/runtime cleanup | used by smoke setup | SETUP_ONLY | LOW | Existing use is sufficient for smoke environment. |
| `dev.seed_technical_run` | `POST /dev/games/{room_code}/seed-technical-run` | yes: creates test Houses/Players | used by smoke setup | SETUP_ONLY | LOW | Existing use is sufficient for smoke environment. |
| `dev.resource_adjust` | `POST /dev/houses/{house_id}/resource-adjust` | yes: admin resource delta | used by crown-tax setup | SETUP_ONLY | MEDIUM | Add admin utility smoke only if operator relies on it. |
| `dev.gold_adjust` | `POST /dev/houses/{house_id}/gold-adjust` | yes: admin gold delta | none | NONE | MEDIUM | Add with manual gold smoke if master uses this route. |
| `dev.tower_add_part` | `POST /dev/games/{room_code}/tower/{house_id}/add-part` | yes: tower state | none | NONE | LOW | V2-disabled; no immediate smoke needed. |
| `dev.tower_apply_blueprint` | `POST /dev/games/{room_code}/tower/{house_id}/apply-blueprint` | yes: tower state | none | NONE | LOW | V2-disabled; defer. |

## Coverage Summary

Dedicated command-level smoke coverage currently exists for:

- `last_whisper.quiet_support`
- `last_whisper.crown_tax`
- `last_whisper.break_alliance`
- `recent_events` state contract

Indirect coverage exists for:

- alliance `deal_create`
- alliance `deal_respond` / activation
- scenario apply, runtime reset, technical seed, phase open as smoke setup

Manual checkpoint coverage exists for:

- House duel MVP
- manual gold control
- Court/live rehearsal paths in older reports

No focused smoke coverage was found for:

- player-side duel lifecycle
- duel resolve and gold ledger settlement
- diplomacy reject/counter/cancel/resource transfer branches
- treasurer confirmation/rejection
- Lord/Lady alliance break and betrayal
- expedition lifecycle
- assignment/question answer reward loop
- host round lifecycle
- Court lifecycle
- scenario director advance flow
- map runtime exploration

## Highest-Risk Uncovered Actions

1. `player.duel_challenge` -> `player.duel_accept/refuse` -> `dev.duel_resolve`

   This is live-facing, touches role gates, duel status, gold, influence, Master state, and TV state.

2. `assignment.answer` and host question round lifecycle

   This is the core question reward loop. It mutates assignment state and can apply influence/resource rewards.

3. Court lifecycle

   Court is a major live stage with multi-step runtime state and transition importance.

4. `player.treasurer_confirm_deal`

   This can transfer resources between Houses and complete/reject deals. It is high trust-risk if resources reappear in live UI.

5. Expedition lifecycle

   Expedition can create map visits and apply resource outcomes. It has several role/member/location guards and no command smoke.

6. Scenario director advance flow

   Flow integrity matters because recent V1 simplification and Last Whisper bridge changed scenario order.

7. Lord/Lady alliance break / betrayal

   Separate from Whisper break and can mutate both deal status and resources. It should not be assumed covered by `break_alliance`.

## Recommended Next Smoke

Recommended next test: `scripts/smoke_player_duel_lifecycle.py`

Minimum shape:

1. Reset runtime and delegations.
2. Apply `season1_mvp_live_v2`.
3. Seed technical run.
4. Open `duel` phase.
5. Find two Lord/Lady players from different Houses.
6. Ensure both Houses have enough gold for stake.
7. Lord A creates a challenge through `POST /player/duels/challenge/{player_id}`.
8. Assert `GameDuel.status == "challenged"` in Master and TV state.
9. Lord B accepts through `POST /player/duels/accept/{player_id}/{duel_id}`.
10. Assert `status == "accepted"`.
11. Resolve through the existing Master/dev resolve route.
12. Assert status, winner, gold ledger deltas, influence deltas, `duels` state, and `recent_events` if applicable.
13. Reset and run refusal branch.
14. Assert normal player cannot challenge or accept/refuse.

Why this smoke first:

- It protects a visible live mechanic.
- It covers both player ownership and host resolve.
- It touches the highest number of state contracts without creating new mechanics.
- It is not covered by current Last Whisper smoke.

Second recommended smoke: `scripts/smoke_question_influence_reward.py`

This should verify host round start/open question, player answer, correct-answer `+1 influence`, wrong-answer zero delta, Master/TV/player feedback, and no accidental Court/Final mutation.

Third recommended smoke: `scripts/smoke_court_lifecycle.py`

This should cover bracket generation, pair start, question open, result marking, winner confirmation, next pair, Court completion, and transition safety toward Last Whisper/Final.

## Notes

- Existing smoke tests require a running local runtime at `http://127.0.0.1:8000`.
- Current smoke is command-level, not browser UI automation.
- Some older docs and route strings contain legacy mojibake; this audit intentionally does not clean encoding noise.
- `recent_events` is a state contract smoke, not gameplay mutation coverage.
- Dev/admin routes are listed where they mutate live runtime state, but player-facing routes should be prioritized for V1 smoke coverage.
