# Diplomacy + Мастер над шёпотом gameplay design audit V1

Date: 2026-06-29
Scope: docs-only gameplay design audit. No runtime implementation in this task.

## 1. Purpose

The post-rehearsal cleanup made the V1 technically stronger, but the political layer still needs sharper purpose.

Current product problem:

- Diplomacy exists, but after Crest/herb removal it lacks a strong object of trade/conflict that players instantly understand.
- `Мастер над шёпотом` has Last Whisper agency, but does not yet have a clear mid-game charge/подлянка identity.
- The game needs controlled House-vs-House tension: negotiate, betray, protect, scout, interfere.
- This tension should not bring back the full metaverse/resource system yet.
- V1 should stay host-readable, operator-confirmed, and safe to explain in a bar setting.

Goal of this audit:

- map what exists now;
- define a small Diplomacy purpose;
- define a small `Мастер над шёпотом` charge system concept;
- choose a minimal V1 slice for later approval/implementation.

## 2. Current implementation / audit map

### Diplomacy runtime surfaces found

Found in current app/code search:

- `app/routes/player.py`
  - `POST /player/deals/create/{player_id}`
  - `POST /player/deals/respond/{player_id}`
  - `POST /player/alliances/break/{player_id}`
  - role/phase gates for `diplomat` during `diplomacy` / `free_play`
  - active alliances and incoming deals serialized for player state
- `app/services/diplomacy_service.py`
  - `propose_diplomacy_deal_logic`
  - `respond_diplomacy_deal_logic`
  - `counter_diplomacy_deal_logic`
  - `cancel_diplomacy_deal_logic`
  - phase requirement for `diplomacy`
  - role/permission helpers for proposing/responding/canceling
- `app/routes/dev.py`
  - `GET /games/{room_code}/can-use-diplomacy`
  - `POST /games/{room_code}/diplomacy/propose-deal`
  - `POST /games/{room_code}/diplomacy/respond-deal/{deal_id}`
  - `POST /games/{room_code}/diplomacy/counter-deal/{deal_id}`
  - `POST /games/{room_code}/diplomacy/cancel-deal/{deal_id}`
  - `GET /games/{room_code}/deals`
- `app/models/game_deal.py`
  - existing `GameDeal` model is the main deal/alliance source of truth.
- `app/services/master_state_service.py`
  - serializes deals, active alliances, broken alliances, recent events.
- `app/templates/player_room.html`
  - Diplomat UI appears when role is `diplomat` and phase is `diplomacy` or `free_play`.
- `app/templates/master_screen.html`
  - Master phase controls include open/close Diplomacy.
  - Master announcement copy includes Diplomacy prompts.
- `app/templates/tv_mode_tv_state.html`
  - TV has Diplomacy scene/copy.

Current Diplomacy status model found indirectly:

- `pending`
- `countered`
- `alliance_active`
- `alliance_broken`
- `alliance_betrayed` appears in state serialization paths.
- resource/treasurer deal statuses also exist, but they should not be mixed into the diplomacy proposal without a separate product decision.

Current limitations:

- Diplomacy can create/accept deals and alliances, but the player-facing reason to make a deal is not yet strong enough.
- Some alliance break/betrayal surfaces exist, but high-trust/high-impact branches need dedicated smoke and product approval before promotion.
- Focused diplomacy lifecycle smoke is recommended in existing docs but not found as completed coverage.
- No clear public V1 “what is a good deal?” contract exists for live players.

### Мастер над шёпотом runtime surfaces found

Found in current app/code/docs search:

- `app/routes/player.py`
  - `POST /player/last-whisper/action/{player_id}`
  - available actions include:
    - `quiet_support`
    - `crown_tax`
    - `break_alliance`
  - one action per House is enforced through Last Whisper phase payload/state checks.
- `app/services/master_state_service.py`
  - builds `last_whisper` payload from active `last_whisper` phase.
  - serializes `last_whisper.latest_event` into recent event feeds.
- `app/templates/player_room.html`
  - player-facing Last Whisper controls for `quiet_support`, `crown_tax`, `break_alliance`.
- `app/templates/master_screen.html`
  - Last Whisper scene rendering and state hooks.
- `app/templates/tv_mode_tv_state.html`
  - Last Whisper scene rendering and event copy.
- `docs/control/WHISPER_MASTER_V1_CONTRACT.md`
  - documents current Last Whisper action contract and limitations.
- `docs/control/LAST_WHISPER_SMOKE_PROTOCOL.md`
  - documents smoke protocol for Last Whisper actions.

Current Last Whisper action effects:

- `quiet_support`
  - target House gets `+1 influence`.
- `crown_tax`
  - clear influence leader can lose `-1 influence`; no-op/tie cases exist.
- `break_alliance`
  - selected `GameDeal` alliance moves from `alliance_active` to `alliance_broken`.

Current limitations:

- These are final-window Last Whisper actions, not mid-game charges.
- No general mid-game “3 whisper charges per House” system found.
- No repeated mid-game подлянки layer found.
- No private messaging system found.
- No automatic hidden chaos engine found.
- No generic `rumor`, `blackmail`, `hidden_signal`, or similar V1-safe mid-game effects should be promoted without a fresh design/smoke pass.

### Resource/influence hooks found

Found:

- Houses have `resource_gold` and `resource_influence`.
- Court ranking uses influence/gold ordering in current audits.
- Duel and Last Whisper can affect influence/gold in specific paths.
- Harchevnya and cashier use gold.
- `gift_to_ally` exists historically/operator-style and can affect influence when active alliance exists, but it is not part of the current safe public Harchevnya shelf.

NOT FOUND as ready V1 product contract:

- a generalized diplomacy reward system;
- automatic protection tokens;
- automatic spying/scouting tiers;
- automatic attack/defense engine;
- broad multi-resource trading for live V1;
- clear mid-game Whisper charge economy.

## 3. Design principle

Keep V1 small.

Design rules:

- No full attack/defense engine.
- No new resource system.
- No Duel V2.
- No automatic hidden chaos.
- No private messaging system.
- No heavy DB/schema changes yet.
- Preserve host control and operator truth.
- Prefer manual/host-confirmed social effects first.
- Prefer clear public consequences over secret bookkeeping.
- Use gold/influence only where existing mechanics already make them understandable.
- Make every action explainable in one sentence at a loud table.

Good V1 political actions should be:

- visible enough to create drama;
- bounded enough to avoid resentment;
- simple enough to run manually;
- strong enough that players care;
- reversible or host-confirmed when trust-risk is high.

## 4. Diplomacy V1 proposal

Diplomacy should become the phase where Houses convert conversation into public leverage.

### Option A: Public alliance announcement

What player does:

- Дипломат proposes an alliance to another House.
- Other House accepts or rejects.

Host/operator confirms:

- Host may announce active alliance publicly.

Visible on TV/Master/player:

- Active alliance appears in deal/alliance state.
- TV can mention alliance in event/feed if current state supports it.

Manual-only V1:

- Already close to runtime-supported.

Risk:

- Alliance is socially meaningful only if players know why it matters.
- Needs clear promise: “allies may support each other politically, but betrayal is possible if host allows it.”

V1-safe:

- Yes, if treated as social/public alignment, not a complex treaty engine.

### Option B: Court support promise

What player does:

- Houses publicly promise support before Court: advice, cheering, choosing a side, or future favor.

Host/operator confirms:

- Host records/announces promise manually.

Visible on TV/Master/player:

- Optional event text; no automatic runtime effect in V1.

Manual-only V1:

- Yes.

Risk:

- If no mechanical effect, may feel cosmetic.
- If mechanical effect is added too early, Court balance can be distorted.

V1-safe:

- Yes as a manual/social promise. Mechanical Court bonus should wait.

### Option C: Gold support promise

What player does:

- House promises to help another House with gold-related action or bar/social support.

Host/operator confirms:

- If actual gold transfer is involved, Мастер над золотом/cashier/operator must confirm.

Visible on TV/Master/player:

- Deal can be logged as a promise/alliance-style event if current flow supports it.

Manual-only V1:

- Yes if no automatic transfer is promised.

Risk:

- Gold is a real score/resource; accidental promises can become arguments.

V1-safe:

- Only as a promise unless runtime transfer path is deliberately used and smoked.

### Option D: Information trade

What player does:

- House trades public or semi-public information: “we know who is leading”, “we saw a deal”, “we will not challenge you.”

Host/operator confirms:

- Host does not need to verify all social claims unless they become official effects.

Visible on TV/Master/player:

- Usually not needed; can be announced manually if dramatic.

Manual-only V1:

- Yes.

Risk:

- False information is fun but can become chaotic if players think system confirmed it.

V1-safe:

- Yes if framed as social/player claims, not system truth.

### Option E: Joint pressure against third House

What player does:

- Two Houses publicly coordinate against a leader or rival.

Host/operator confirms:

- Host may announce “two Houses put pressure on X” as drama.

Visible on TV/Master/player:

- Optional event/feed. No automatic penalty in V1.

Manual-only V1:

- Yes.

Risk:

- Can feel like bullying if repeated against one House.

V1-safe:

- Yes with host moderation and repeat-target limits.

### Option F: Protection token / manual promise

What player does:

- House promises not to duel/betray/target another House for one window.

Host/operator confirms:

- Host can record a manual “protection promise”.

Visible on TV/Master/player:

- Manual board/host note first; runtime later if approved.

Manual-only V1:

- Yes.

Risk:

- Binding rules require enforcement and edge-case handling.

V1-safe:

- Yes only as non-binding social promise unless a future patch defines enforcement.

## 5. Мастер над шёпотом V1 proposal

`Мастер над шёпотом` should become the House role for controlled interference and information pressure.

Proposed concept:

- Each House receives 3 whisper charges per game.
- Charges are submitted by `Мастер над шёпотом`.
- Effects are host-confirmed first.
- V1 starts manual/docs-first before runtime.
- Effects should be visible enough to create drama but not so strong that they ruin trust.

### Candidate effect: разведка

Timing:

- During Diplomacy / Free Play windows.

Target:

- One other House.

Cost:

- 1 whisper charge.

Effect:

- Host privately tells acting House an approximate tier of target House:
  - low / middle / high gold;
  - or low / middle / high influence.

Visibility:

- Private to acting House, unless host chooses to narrate generally.

Host confirmation:

- Required.

Abuse risk:

- Low to medium. Repeated targeting can feel oppressive.

V1-safe:

- Yes, if approximate only and limited by charges.

### Candidate effect: слух

Timing:

- During Diplomacy / Free Play, or just before Court.

Target:

- One House or one active alliance.

Cost:

- 1 whisper charge.

Effect:

- Host announces a short rumor/hint:
  - “По залу пошёл слух, что Дом X слишком быстро набирает влияние.”
  - “Говорят, союз Y не так крепок.”

Visibility:

- Public/semi-public.

Host confirmation:

- Required; host rewrites unsafe wording.

Abuse risk:

- Medium. Needs no personal insults and no real-world targeting.

V1-safe:

- Yes as narrative effect only, no automatic resource delta.

### Candidate effect: помеха

Timing:

- Before a question, Duel, or Court pair.

Target:

- One House or one participant.

Cost:

- 1 whisper charge.

Effect:

- Target loses a small convenience, not a hard punishment. Examples:
  - host asks a harder tie-break style question;
  - target cannot receive one manual hint;
  - target must answer without table discussion for one short moment.

Visibility:

- Public, because secret penalties feel unfair.

Host confirmation:

- Required.

Abuse risk:

- High if too punitive.

V1-safe:

- Borderline. Keep as V1.1, not first slice.

### Candidate effect: тень сделки

Timing:

- During Diplomacy / Free Play.

Target:

- Two Houses or one active alliance.

Cost:

- 1 whisper charge.

Effect:

- Acting House learns whether the target House currently has an active alliance/deal.

Visibility:

- Private to acting House.

Host confirmation:

- Required.

Abuse risk:

- Low to medium.

V1-safe:

- Yes if limited and approximate: “есть политическая связь / нет явной связи”.

### Candidate effect: перехват

Timing:

- When a diplomatic promise/alliance is announced.

Target:

- One promise/alliance.

Cost:

- 1 whisper charge.

Effect:

- Acting House can force the host to publicly ask: “Вы точно подтверждаете эту сделку?”
- Or delay public confirmation until the end of the diplomacy window.

Visibility:

- Public.

Host confirmation:

- Required.

Abuse risk:

- Medium. Could slow the game.

V1-safe:

- Maybe later, not first slice.

### Candidate effect: шёпот в Суд

Timing:

- Before Court pair starts.

Target:

- One House or one pair.

Cost:

- 1 whisper charge.

Effect:

- Small manual advantage/disadvantage in Court.

Visibility:

- Public or semi-public.

Host confirmation:

- Required.

Abuse risk:

- High because Court is standings-flip drama.

V1-safe:

- Defer. Needs Court balance decision first.

## 6. Recommended V1 slice

Recommended first slice: **manual Diplomacy + Whisper cards, no runtime patch yet**.

V1 content:

1. Diplomacy has three approved social objects:
   - public alliance;
   - Court support promise;
   - information trade / joint pressure.
2. `Мастер над шёпотом` gets 3 manual charges per House.
3. Only two Whisper effects are allowed in first slice:
   - `разведка`: learn approximate gold or influence tier of one House;
   - `слух`: host-approved public rumor with no automatic resource effect.
4. Optional third effect after host approval:
   - `тень сделки`: learn whether one House has an active political connection.
5. All effects are host-confirmed.
6. No automatic resource mutation.
7. No DB/schema changes.
8. TV event feed is optional later, not required for manual V1.
9. Manual cards/sheets are created before runtime implementation.

Why this slice:

- Gives Diplomacy a reason: create public promises and political targets.
- Gives `Мастер над шёпотом` mid-game agency without chaos.
- Uses existing concepts: gold, influence, alliances, public rumor.
- Avoids full attack/defense engine.
- Keeps host in control.
- Can be playtested with paper before code.

Suggested table language:

- “Дипломатия — это не пауза. Это время договориться, кого поддержать, кого сдержать и кому можно верить.”
- “Мастер над шёпотом не ломает игру. Он создаёт давление: узнать, намекнуть, посеять сомнение.”
- “Любой шёпот подтверждает ведущий. Если действие тормозит игру или портит атмосферу, ведущий его отклоняет.”

## 7. What not to implement now

Do not implement now:

- full attack/defense engine;
- full spy economy;
- hidden automatic penalties;
- new resource metaverse;
- Duel V2;
- House perks;
- private messaging system;
- anonymous harassment mechanics;
- irreversible effects without host confirmation;
- automatic Court advantages;
- automatic repeated target punishment;
- broad betrayal system without smoke and trust design;
- runtime charge counter before manual rules are approved.

## 8. Operator flow

### Before game

Host prepares:

- Diplomacy mini-rule card;
- Whisper charge cards or tokens: 3 per House;
- host sheet with House list and notes.

### When Diplomacy opens

Host says:

- “Дипломаты могут двигаться. Цель — заключить союз, получить обещание поддержки или создать давление на соперников.”
- “Сделка становится игровой правдой только когда её подтвердили участники и ведущий.”

Player flow:

1. Дипломат talks to other Houses.
2. Лорд / Леди approves House-level promise.
3. Host/operator records public alliance or promise if needed.
4. TV/host may announce major alliance/promise.

### When Whisper is used

Player flow:

1. `Мастер над шёпотом` gives one charge card/token to host.
2. Player names effect and target.
3. Host accepts, adjusts, or rejects.
4. Host resolves effect manually.
5. Host decides visibility:
   - private info for `разведка` / `тень сделки`;
   - public line for `слух`.

### Abuse prevention

Rules:

- Host can reject any whisper that targets a person instead of a House.
- No insulting real people.
- No repeated pressure on the same House more than host allows.
- No secret irreversible penalties.
- No alcohol/bar/service manipulation through Whisper.
- Whisper cannot override staff/legal decisions.
- Whisper cannot force automatic gold/resource movement in V1.

## 9. Open questions for Victor

Human decisions needed:

- Are whisper effects public, private, or semi-public?
- Can a House target the same House repeatedly?
- Should `Мастер над шёпотом` be visible to everyone or semi-private?
- Can whispers affect Court at all, or is Court protected from Whisper V1?
- Should Diplomacy deals be binding or social/non-binding?
- Should betrayal be allowed, announced, or deferred?
- Should gold be involved in diplomacy promises, or only social support?
- Should public alliance give any automatic influence, or remain social?
- Should `разведка` reveal gold tier, influence tier, or host-chosen vague clue?
- Should `слух` always be public, or can it be whispered to one House only?
- How many total charges feels right: 2, 3, or phase-based?
- Should unused charges expire before Court/Final?

## 10. Next recommended task

Recommended next task:

**Create printable/manual cards for Diplomacy + Whisper V1.**

Suggested output:

- one host card explaining Diplomacy window;
- one Дипломат card with valid deal/promise types;
- one `Мастер над шёпотом` card;
- three Whisper charge tokens per House;
- a host approval checklist;
- examples of safe/unsafe rumor wording.

Alternative next task if runtime confidence is needed first:

- create a tiny runtime audit for existing Diplomacy/Whisper action surfaces and smoke coverage, focused on `GameDeal` lifecycle and Last Whisper actions.

Do not prepare a runtime implementation task until Victor approves the V1 manual design slice.
