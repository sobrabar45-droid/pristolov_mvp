# Harchevnya / 18+ / availability audit V1

Date: 2026-06-27

## 1. Purpose

Harchevnya / game shop needs an audit before any new implementation because it sits at the boundary between game economy and real bar fulfillment.

Main risks:

- guest expectation risk: players may assume that every visible item can actually be served tonight;
- real bar fulfillment risk: the bar may be busy, out of stock, or unable to serve a premium item at game tempo;
- 18+ clarity risk: age-restricted items must not appear as casually available game rewards;
- game economy clarity risk: players must know when gold is actually spent;
- cashier/bar/operator handoff risk: game request, payment confirmation, and real-world service must be aligned.

This audit is documentation only. It does not enable new items, age-restricted items, or code paths.

## 2. Current implementation map

### Routes found

| Surface | Route / file | Current role |
|---|---|---|
| Player shop request | `POST /player/treasurer-shop/request/{player_id}` in `app/routes/player.py` | Creates pending Harchevnya request from a player with role `treasurer` / current display role `Мастер над золотом`. |
| Legacy/direct shop purchase | `POST /player/treasurer-shop/{player_id}/purchase` in `app/routes/player.py` | Directly spends House gold for configured shop actions. Used by operator-style shop surface. |
| Cashier Gold Desk | `GET /cashier/gold-desk/{room_code}` in `app/routes/cashier.py` | Shows pending Harchevnya requests and normal cashier gold controls. |
| Cashier confirmation | `POST /cashier/treasurer-shop/requests/{request_id}/confirm` in `app/routes/cashier.py` | Confirms pending request, spends gold, marks request completed. |
| Operator/dev shop page | `GET /dev/treasurer-shop/{room_code}` in `app/routes/dev.py` | Renders `app/templates/treasurer_shop.html`; operator-mediated direct-spend screen. |
| Master/TV event state | `app/services/master_state_service.py` | Reads `HouseGoldTransaction.source_type == "treasurer_shop"` into Master/TV recent events after spend/confirmation. |

### Templates found

| Template | Current behavior |
|---|---|
| `app/templates/player_room.html` | Shows `Харчевня / Магазин` section only for the House gold role. Shows safe request items only. Copy says gold is spent after cashier confirmation. |
| `app/templates/cashier_gold_desk.html` | Shows `Заявки из Харчевни`; each pending request has `Заказ принят` confirmation button. |
| `app/templates/treasurer_shop.html` | Operator/dev shop page. Contains direct purchase items and direct spend flow. Text appears partially mojibake in terminal output, but routes/actions are clear from source constants. |

### Services / state found

- `app/services/gold_service.py` provides `spend_gold_for_action(...)` and records `HouseGoldTransaction`.
- `app/services/master_state_service.py` exposes confirmed shop spends as `treasurer_shop_events` and recent events.
- No dedicated `ShopRequest` model/table was found in this audit; V1.2 request flow uses `GameDeal` with `offer.type == "treasurer_shop_request"`.

### Current buyer / confirmer / spend timing

- Buyer/requester: only a player with role code `treasurer`, displayed as `Мастер над золотом`.
- Request creation: player-room flow creates a pending `GameDeal` and does not spend gold.
- Confirmation: cashier confirms with `Заказ принят`.
- Spend point: gold is spent only at cashier confirmation in the safe request flow.
- Master/TV events: confirmed spends appear through `HouseGoldTransaction.source_type == "treasurer_shop"`.

### Missing pieces

- No visible 18+ checkbox/unlock found in current player room shop UI.
- No availability flag per item found.
- No substitution/refund workflow found for unavailable items after request/confirmation.
- No dedicated status lifecycle beyond pending/completed through `GameDeal` for shop requests.
- No staff-approved current-night shelf list found in runtime.
- No explicit real-world staff confirmation wording found in the current player-facing shop UI.

## 3. Current shelf / catalog audit

### Player-facing safe request shelf

Found in `app/templates/player_room.html`, `app/routes/player.py`, and `app/routes/cashier.py`.

| Code | Display item | Price | Category | 18+ represented? | Visible to player? | Fulfillment dependency | Risk / comment |
|---|---|---:|---|---|---|---|---|
| `author_tea` | Авторский чай | 3 gold | bar / non-age-restricted safe shelf | Not represented | Yes, for `Мастер над золотом` | Bar availability | Safe candidate, but still needs tonight availability. |
| `lemonade_02` | Лимонад 0.2 | 2 gold | bar / non-age-restricted safe shelf | Not represented | Yes, for `Мастер над золотом` | Bar availability | Safe candidate, but size/serving must match bar reality. |
| `sobranie_pizza` | Пицца Собрание | 6 gold | food | Not represented | Yes, for `Мастер над золотом` | Kitchen availability/time | Needs kitchen capacity and substitution/refund rule. |
| `anna_pavlova` | Десерт Анна Павлова | 2 gold | food/dessert | Not represented | Yes, for `Мастер над золотом` | Kitchen/bar availability | Needs availability check. |

### Operator/dev direct-spend shop actions

Found in `TREASURER_SHOP_ACTIONS` in `app/routes/player.py` and rendered by `app/templates/treasurer_shop.html`.

| Code | Display item | Price | Category | 18+ represented? | Visible to player? | Fulfillment dependency | Risk / comment |
|---|---|---:|---|---|---|---|---|
| `set_bar` | Сет у стойки | 5 gold | bar/social direct spend | Not represented | Not in player-room safe request shelf | Bar availability | Operator-only/direct spend path; not safe as public promise without availability. |
| `giraffe` | Жираф | 10 gold | bar/social direct spend | Not represented | Not in player-room safe request shelf | Bar availability; may imply beverage service | High expectation risk if players expect a real beer giraffe. Needs staff-approved label and 18+/availability policy before public use. |
| `gift_to_ally` | Подарок союзнику | 15 gold | political/social action | Not represented | Not in player-room safe request shelf | Active alliance + game state | Not a normal bar SKU; has influence effect. Keep separate from real menu. |
| `author_tea` | Авторский чай | 3 gold | bar/social direct spend | Not represented | Safe request shelf also exists | Bar availability | In safe request flow, preferred path is cashier-confirmed request. |
| `lemonade_02` | Лимонад 0.2 | 2 gold | bar/social direct spend | Not represented | Safe request shelf also exists | Bar availability | In safe request flow, preferred path is cashier-confirmed request. |
| `sobranie_pizza` | Пицца Собрание | 6 gold | food direct spend | Not represented | Safe request shelf also exists | Kitchen availability/time | In safe request flow, preferred path is cashier-confirmed request. |
| `anna_pavlova` | Десерт Анна Павлова | 2 gold | dessert direct spend | Not represented | Safe request shelf also exists | Kitchen/bar availability | In safe request flow, preferred path is cashier-confirmed request. |

### Previously proposed but deferred full shelf

Found in `docs/control/TREASURER_SHOP_BAR_SHELF.md` and `docs/control/TREASURER_SHOP_V1_2_REQUEST_FLOW.md`.

Deferred items include:

- premium champagne candidate;
- tincture set candidate;
- beer giraffe candidate;
- beer set candidate;
- tapas set candidate.

Audit status: these are not safe to expose as available in player-facing UI until staff approves exact item names, serving rules, availability, age-restricted handling, and substitution/refund policy.

## 4. 18+ audit

### What exists

- Prior docs describe an 18+ checkbox concept.
- Prior docs explicitly say alcohol-named items were deferred.
- Prior docs say full shelf remains future scope and legal/public wording must be reviewed.

### What was not found in current runtime

- No active 18+ checkbox/unlock was found in `player_room.html` safe shop UI.
- No active 18+ checkbox/unlock was found in `treasurer_shop.html` in the inspected output.
- No per-item `age_restricted` / `is_18_plus` flag was found in current runtime constants.
- No staff/legal age-confirmation wording was found in the current player-facing safe shelf.
- No runtime enforcement was found that separates age-restricted items from non-age-restricted items because current player-facing safe shelf does not include those items.

### Risk assessment

Current safe request shelf avoids direct age-restricted promise by not exposing deferred age-restricted candidates. That is good.

The risk is product/UX expectation: players saw or expected a fuller shelf, but the system does not yet have a clear public 18+ unlock or staff approval process. Adding the full shelf without that process would be unsafe.

### Current accidental promise prevention

- Player-facing safe request shelf does not list premium champagne, tincture set, beer set, or beer giraffe candidates.
- Cashier confirmation spends gold only for the whitelisted safe request actions.
- Operator/dev direct-spend page still includes broader historical actions such as `giraffe`, so it should not be treated as the public player-facing shelf until reviewed.

## 5. Availability / substitution policy draft

V1 policy draft for staff/operator review:

1. Items can be bought only if available tonight.
2. The public player-facing shelf should show only staff-approved items for the current event.
3. Bar/operator may mark an item unavailable before or during the game.
4. If an item becomes unavailable after request but before confirmation:
   - cashier should not confirm the request;
   - staff offers replacement or rejects/refunds by not spending gold.
5. If an item becomes unavailable after confirmation:
   - staff offers a comparable replacement;
   - if no replacement is accepted, operator should refund gold manually or through a future refund action.
6. Age-restricted items require real-world staff confirmation.
7. Game screen is not legal age verification and must not replace staff checks.
8. Item names should match what the bar can actually serve that night.
9. Premium/limited items should be marked “only if staff confirms” or hidden until approved.

## 6. Fulfillment flow

### Desired safe flow

1. House decides what to order.
2. `Мастер над золотом` submits request from player room.
3. Request appears in cashier queue.
4. Cashier/bar checks real availability.
5. If available, cashier confirms `Заказ принят`.
6. Gold is spent only at confirmation.
7. Staff serves item.
8. Confirmed purchase appears as Master/TV event.

### What current implementation supports

- Player safe request from `Мастер над золотом`.
- Pending request stored as `GameDeal` with `offer.type == "treasurer_shop_request"`.
- Cashier queue displays pending requests.
- Cashier confirmation validates action code and cost.
- Gold spend happens at confirmation, not request creation.
- Confirmed spend enters transaction ledger and Master/TV event state.

### What current implementation does not yet support

- Reject/cancel action in cashier queue.
- Availability toggle per item.
- Staff note/status such as “готовится”, “выдано”, “замена”.
- Refund path for confirmed but unfulfilled order.
- Dedicated shop request model/table.
- Age-restricted item gating.
- Public copy explaining “items depend on tonight availability”.
- Clear distinction in UI between public safe shelf and operator/dev direct-spend shelf.

## 7. What not to implement yet

Do not implement these in V1 without a separate approval and design task:

- full POS/iiko integration;
- automatic age/legal checks;
- complex inventory sync;
- full franchise shop admin;
- new economy model;
- broad shop redesign;
- public full shelf without staff-approved availability list;
- premium or age-restricted public menu promises;
- automatic substitution logic without staff workflow;
- direct public spend path for unconfirmed bar items.

## 8. V1 product recommendation

Recommended next step: docs-only staff-approved shelf and fulfillment policy.

Why this first:

- Current safe request flow is technically safer than exposing the full shelf.
- The gap is not only UI; it is operational truth: what can the bar actually serve tonight, at what price, and under what constraints.
- Expanding UI before staff approval risks promising unavailable items.
- The 18+ concept cannot be solved by checkbox copy alone; it needs a staff/legal/fulfillment policy.

Recommended V1 sequence:

1. Create a staff-approved shelf list for the next event.
2. Mark each item as safe public, staff-confirmed only, age-restricted, or unavailable.
3. Decide whether age-restricted items are hidden entirely or visible with a lock/explanation.
4. Decide substitution/refund policy.
5. Only after that, implement a narrow UI/copy patch:
   - “availability tonight” copy;
   - visible safe shelf;
   - optional staff-confirmed status;
   - no new broad shop mechanics.

If an immediate tiny UI patch is needed before staff list:

- keep the safe/truncated shelf;
- add copy that all Harchevnya items depend on cashier/bar confirmation;
- do not add full shelf or 18+ items yet.

## 9. Open questions for Victor/operator

- Which items are actually available every game night?
- Which items are available only sometimes?
- Which items require staff age confirmation?
- Should age-restricted items be hidden entirely or visible with lock/explanation?
- Which exact item names may be shown publicly?
- Are premium items allowed during the game tempo?
- What happens if the bar is busy and cannot fulfill quickly?
- Who can approve substitutions?
- Should gold be charged only after item is physically accepted by staff, or after cashier accepts the game request?
- Should an unavailable item be replaced, rejected, or refunded?
- Should `giraffe` remain an operator-only atmosphere action or become a real staff-approved item?
- Should `gift_to_ally` stay separate from normal Harchevnya shelf because it has game influence effect?

## 10. Next recommended task

Recommended next task: create a docs-only staff shelf approval list.

Suggested output:

- `docs/control/HARCHEVNYA_STAFF_APPROVED_SHELF_V1.md`
- table columns:
  - item label;
  - action code candidate;
  - price in gold;
  - public-visible yes/no;
  - age-restricted yes/no;
  - available every event yes/no;
  - substitution option;
  - fulfillment owner;
  - notes.

Do not implement code until staff-approved shelf and availability policy are reviewed.
