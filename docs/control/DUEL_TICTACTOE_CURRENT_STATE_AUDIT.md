# Duel / Tic-Tac-Toe Current State Audit

Date: 2026-06-27
Task: audit current Duel / tic-tac-toe flow before runtime changes.
Scope: audit only; no runtime, template, schema, scenario, DB, or production config changes.

## 1. Executive summary

The current Duel system is implemented as a House challenge lifecycle, not as a full in-app tic-tac-toe board engine.

Runtime supports:

- creating a House duel challenge during active `duel` phase;
- accepting or refusing the challenge;
- Master/operator resolving the duel by choosing one winner House;
- applying stake-gold, influence, refusal, and tower-advantage effects;
- surfacing duel state to player, Master, TV, and recent event feeds.

Runtime does not currently support:

- tic-tac-toe move storage;
- a board state;
- per-move validation;
- draw/tie result;
- a no-winner resolution path;
- question-before-move logic;
- explicit stale accepted-but-not-played cleanup.

This matches the rehearsal symptom: if a physical/host-led tic-tac-toe duel ends in a draw, the Master screen only offers winner buttons, so the host has no safe button to press.

Recommended next patch: small V1 draw/status patch, not a full duel redesign. Add a safe draw/tie path or manual tie-break guidance first, plus clearer Master copy for accepted duels. Treat question-before-move as V2 design because it needs a new mini-game/question loop, not just copy.

## 2. Files inspected

- `app/services/duel_service.py`
- `app/models/game_duel.py`
- `app/routes/player.py`
- `app/routes/dev.py`
- `app/services/master_state_service.py`
- `app/templates/player_room.html`
- `app/templates/master_screen.html`
- `app/templates/tv_mode_tv_state.html`
- `app/game_templates/scenarios/season1_mvp_live_v2.json`
- `docs/control/NEXT_CODEX_TASK.md`

## 3. Current Duel flow

### Phase gate

Duel actions are gated by active phase type `duel` in `app/services/duel_service.py`.

If the phase is not active, service returns a blocked response.

### Challenge creation

Creation paths:

- player-facing: `POST /player/duels/challenge/{player_id}`
- dev/operator-facing: `POST /dev/games/{room_code}/duels/challenge`

Player-facing creation requires:

- player exists;
- player has a House;
- player role is `lord_lady`;
- target House is selected;
- duel phase is active;
- target is not own House;
- target is not official ally;
- both Houses can cover the stake;
- target House is not under low-gold protection.

Default stake is 3 gold.

### Acceptance/refusal

Acceptance paths:

- player-facing: `POST /player/duels/accept/{player_id}/{duel_id}`
- operator-facing: `POST /dev/games/{room_code}/duels/{duel_id}/accept`

Refusal paths:

- player-facing: `POST /player/duels/refuse/{player_id}/{duel_id}`
- operator-facing: `POST /dev/games/{room_code}/duels/{duel_id}/refuse`

Player-facing accept/refuse requires the target House Lord/Lady.

Refusal is not neutral: it applies influence transfer from target/refusing House to challenger House.

### Resolution

Operator resolution path:

- `POST /dev/games/{room_code}/duels/{duel_id}/resolve`

Resolution requires `winner_house_id` equal to either challenger House or target House.

Resolution applies:

- PvP gold movement through `resolve_pvp_gold`;
- loser influence -1;
- winner influence transfer +1;
- winner bonus influence +1;
- possible tower advantage influence bonus;
- status becomes `resolved`;
- `winner_house_id` is set.

There is no player-facing resolve endpoint.

## 4. Challenge creation/acceptance lifecycle

Known statuses in service/model:

- `challenged`
- `accepted`
- `refused`
- `resolved`
- `canceled`

Observed transitions:

- create -> `challenged`
- accept -> `accepted`
- refuse -> `refused`
- resolve -> `resolved`

`canceled` exists as an allowed/status display concept, but this audit did not find a clear active cancel endpoint in the inspected duel flow.

## 5. Current tic-tac-toe board lifecycle

The code uses `duel_format = "tic_tac_toe"` as a format label and for tower-advantage text.

No runtime board lifecycle was found:

- no board field;
- no move endpoint;
- no move table;
- no X/O state;
- no player turn state;
- no draw detection;
- no automated winner detection.

Therefore, tic-tac-toe currently appears to be a host-led/offline duel format, with the app only recording challenge status and final winner.

## 6. Master UX

Master screen can:

- create a duel challenge as operator;
- accept/refuse a selected duel;
- resolve a selected duel by pressing one of two winner buttons.

Master display includes:

- challenge status;
- stake;
- format label such as `Крестики-нолики`;
- stage note / live bonus text;
- winner if already resolved.

Main weakness:

- accepted duel has no explicit “draw / tie-break needed / replay” action;
- Master can resolve even a `challenged` duel, not only accepted, because `resolve_duel` allows both `challenged` and `accepted`;
- operator panel chooses one primary duel from pending list, so several accepted/challenged duels can exist but the UI focuses on one.

## 7. TV UX

TV state receives duel blocks from `master_state_service`:

- `active_or_pending`
- `challenged`
- `accepted`
- `recent`

TV renders duel activity during the duel stage and shows recent/pending duel items.

TV does not render a tic-tac-toe board or draw state. It shows House vs House, stake/status/bonus metadata, and generic duel copy.

## 8. Player UX

Player room duel section appears during active `duel` phase.

For `lord_lady`:

- can create challenge;
- can see incoming challenges;
- can accept/refuse incoming challenge;
- can see current duels for their House.

For non-`lord_lady`:

- sees explanatory copy that Lord/Lady controls challenge/accept/refuse and other players should coordinate.

Player screens do not play tic-tac-toe moves; they manage challenge/accept/refuse only.

## 9. Status model / state model

Storage model is `GameDuel`.

Fields include:

- `game_id`
- `challenger_house_id`
- `target_house_id`
- `status`
- `stake_gold`
- `winner_house_id`
- `refused_at`
- `resolved_at`
- `notes_json`
- tower/live bonus fields
- `duel_format`
- influence/bonus payload fields

There is no status or field for `draw`, `tie`, `replay_needed`, or `tie_break_required`.

## 10. Draw/tie support check

No draw/tie support was found.

The resolver requires a winner from one of the two Houses. If a physical tic-tac-toe game ends in a draw, current runtime choices are all unsafe or awkward:

- force one House as winner even though the table saw a draw;
- leave duel as `accepted`, creating stale state;
- invent a manual host rule outside the app.

This is the most urgent confirmed gap.

## 11. Duplicate challenge check

No explicit duplicate-pair protection was found in `create_duel_challenge`.

The service checks:

- phase active;
- not self;
- not official allies;
- stake validity;
- enough gold;
- target protection.

It does not appear to block:

- duplicate `challenged` duel for the same pair;
- reverse duplicate `challenged` duel;
- duplicate `accepted` duel for the same pair;
- a House opening several simultaneous challenges.

This can explain “only some visible/processed” confusion if multiple challenges compete for Master attention.

## 12. Accepted-but-not-played risk

Accepted-but-not-played states are possible.

An accepted duel remains `accepted` until Master resolves it. There is no timeout, draw, cancel, stale warning, or “needs tie-break” state.

If the host does not resolve after a draw, the duel remains active/pending in state payloads and may continue to occupy Master/TV attention.

## 13. Parallel duel / side-action readiness

The data model allows multiple duels per game because `GameDuel` rows are independent and list endpoints return all rows.

However, V1 operational UX is not fully side-action-ready:

- Master operator panel picks one primary duel, preferring challenged then accepted;
- TV shows up to several items, but not a queue with stage ownership;
- no explicit duel queue / assigned table / in-progress board state;
- no “side duel completed elsewhere” flow beyond Master choosing winner.

Conclusion: side-action duels are possible as manual/offline events, but the current UI is better suited to one highlighted duel at a time.

## 14. Question-before-move feasibility

No existing question-before-move hook was found inside duel logic.

A real version would need at least:

- board/move state or a table-led proxy state;
- per-duel current actor/turn;
- question selection source;
- answer validation;
- wrong-answer consequence: lose move, skip move, or lose duel;
- draw/tie-break rules;
- Master/TV/player UX for the mini-game loop.

This is feasible, but it is not a minimal patch. It should be designed as Duel V2, after V1 draw/stale state is fixed.

## 15. What is already good enough

- House challenge lifecycle exists.
- Role gate is correct: Lord/Lady creates and responds on player side.
- Duel phase gate exists.
- Stake and low-gold protection exist.
- Refusal has a clear consequence.
- Resolution already applies gold/influence and event feed state.
- Master/TV/player all receive duel state.
- `tic_tac_toe` is already a supported format label.

## 16. What is missing or risky

Highest priority:

- no draw/tie handling;
- no safe button for host when tic-tac-toe ends in draw;
- accepted-but-not-played duels can linger;
- duplicate pair challenges are not clearly blocked.

Medium priority:

- Master UX does not clearly separate “accepted and waiting to be played” from “ready to resolve”; it only offers winner buttons;
- multiple parallel duels are stored but not strongly managed as a queue;
- TV/player text does not explain what happens after accepted duel if physical play stalls.

Lower priority / V2:

- question-before-move mini-game;
- fully in-app tic-tac-toe board;
- side-action duel table orchestration.

## 17. Recommended next patch

Recommended next patch: **draw/tie handling + status clarity**.

Smallest safe V1 options:

1. Add a `draw` or `tie_break_required` status using existing `status` string and `notes_json`, without DB schema change.
2. Add a Master button for “Ничья / нужен тай-брейк”.
3. On draw, do not move gold/influence automatically.
4. Show the duel as requiring host tie-break/replay instead of leaving it as `accepted`.
5. Optionally add a follow-up resolve path where host can later pick winner after tie-break.
6. Add duplicate protection for active same-pair/reverse-pair challenges if included safely, or make it the next separate patch.

Do not implement question-before-move in the same patch.

## 18. Proposed minimal task after audit

Task: `Add Duel draw handling and Master status clarity`.

Patch boundaries:

- minimal runtime/template patch;
- no DB schema migration;
- no scenario JSON change;
- no scoring/balance change except draw does not force reward;
- add draw/tie-break status path;
- update Master/TV/player copy for accepted/draw states;
- optionally block duplicate active pair challenges if low-risk.

Suggested validation:

- create duel in test room;
- accept duel;
- mark draw/tie-break required;
- confirm no gold/influence transaction on draw;
- confirm duel no longer looks silently accepted/stuck;
- resolve after tie-break if supported;
- confirm normal winner resolution still works.

## 19. Runtime untouched confirmation

This audit changed only docs/control files. Runtime code, templates, DB schema, scenario JSON, production config, and LIVE01 state were not changed.
