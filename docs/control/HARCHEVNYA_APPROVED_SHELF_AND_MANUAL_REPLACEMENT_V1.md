# Harchevnya approved shelf and manual replacement policy V1

Date: 2026-06-27

## 1. Purpose

This document is the operational truth layer for Harchevnya V1.

Victor confirmed that the approved Harchevnya shelf already exists. This document records that approved shelf, separates it from current runtime visibility, and locks the replacement rule before any UI/runtime expansion.

Core principles:

- the approved shelf is known from Victor/operator input;
- current runtime does not yet expose the full approved shelf safely;
- replacement/substitution is manual only;
- gold is charged only after cashier/bar confirmation;
- 18+ service still requires real staff/legal confirmation.

This document is documentation only. It does not add runtime items, unlock 18+ items, change charging logic, or design automatic replacement.

## 2. Source of approved shelf

Sources inspected:

- `docs/control/HARCHEVNYA_18_AVAILABILITY_AUDIT_V1.md`
- `app/routes/player.py`
- `app/routes/cashier.py`
- `app/templates/player_room.html`
- `app/templates/treasurer_shop.html`
- `app/services/master_state_service.py`
- existing `docs/control/*.md` references found by search

Search result:

- Formal repo/doc source for the full approved shelf: `NOT FOUND IN REPO`.
- Operational source for the full approved shelf: `Victor confirmed approved shelf in chat`.
- Current safe player-facing shelf was found in code/templates.
- Broader historical/operator items were found in code/templates.

Conclusion:

- The approved shelf is known from operator input and is recorded below.
- The full approved shelf should later be mirrored into repo docs/config if it becomes runtime-owned.
- Runtime expansion should not happen until visibility, 18+ copy, and staff confirmation flow are explicitly decided.

## 3. Victor-confirmed approved Harchevnya shelf

Approval status used here:

- `APPROVED_VISIBLE_BY_VICTOR` - approved by Victor as a valid Harchevnya shelf position.

| Item key | Display name | Gold price | Category | 18+ | Visibility | Fulfillment owner | Approval status | Source / evidence | Notes |
|---|---|---:|---|---|---|---|---|---|---|
| `author_tea` | Авторский чай | 3 | Bar / drink | NO | Currently visible in safe player-facing shelf | Cashier/bar | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; found in `player_room.html`, `player.py`, `cashier.py` | Already represented in current safe request flow. |
| `premium_champagne_premier` | Шампанское Премиум премьер | 7 | Alcohol / premium drink | YES | Approved by Victor, not yet represented in runtime safe shelf | Cashier/bar/staff | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; formal repo source not found | Requires 18+ lock/copy and staff/legal confirmation before player-facing runtime exposure. |
| `tincture_set` | Сет настоек | 7 | Alcohol / tinctures | YES | Approved by Victor, not yet represented in runtime safe shelf | Cashier/bar/staff | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; formal repo source not found | Requires 18+ lock/copy and staff/legal confirmation before player-facing runtime exposure. |
| `beer_giraffe_shihan` | Жираф пива Шихан | 10 | Alcohol / beer | YES | Operator/dev `giraffe` action exists, exact Shihan label not in safe shelf | Cashier/bar/staff | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; `giraffe` found in `player.py`, `treasurer_shop.html` | Runtime action exists only as broader `giraffe`; exact approved item needs config/copy if exposed. |
| `lemonade_02` | Лимонад 0.2 л | 2 | Bar / non-alcohol drink | NO | Currently visible in safe player-facing shelf as `Лимонад 0.2` | Cashier/bar | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; found in `player_room.html`, `player.py`, `cashier.py` | Runtime label omits `л`; align copy later if needed. |
| `sobranie_pizza` | Пицца Собрание | 6 | Food | NO | Currently visible in safe player-facing shelf | Cashier/bar/kitchen | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; found in `player_room.html`, `player.py`, `cashier.py` | Already represented in current safe request flow. |
| `beer_set_any` | Любой пивной сет (1, 2, 3, 4) | 10 | Alcohol / beer set | YES | Approved by Victor, not yet represented in runtime safe shelf | Cashier/bar/staff | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; formal repo source not found | Requires clear staff choice flow; no automatic selection. |
| `anna_pavlova` | Анна Павлова | 2 | Dessert | NO | Currently visible in safe player-facing shelf as `Десерт Анна Павлова` | Cashier/bar/kitchen | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; found in `player_room.html`, `player.py`, `cashier.py` | Runtime label includes `Десерт`; align copy later if needed. |
| `tapas_set` | Сет тапасов | 7 | Food / tapas | NO | Approved by Victor, not yet represented in runtime safe shelf | Cashier/bar/kitchen | `APPROVED_VISIBLE_BY_VICTOR` | Victor input; formal repo source not found | Needs kitchen/bar availability confirmation before runtime exposure. |

## 4. Current runtime visibility

Currently visible in the safe player-facing request shelf:

- `author_tea` - Авторский чай - 3 золота.
- `lemonade_02` - Лимонад 0.2 - 2 золота.
- `sobranie_pizza` - Пицца Собрание - 6 золота.
- `anna_pavlova` - Десерт Анна Павлова - 2 золота.

Approved by Victor but likely not currently visible in the safe player-facing shelf:

- Шампанское Премиум премьер - 7 золота.
- Сет настоек - 7 золота.
- Жираф пива Шихан - 10 золота.
- любой пивной сет (1, 2, 3, 4) - 10 золота.
- Сет тапасов - 7 золота.

Operator/dev evidence:

- `giraffe` exists in the older/operator direct-spend surface, but the current code evidence does not show the exact public label `Жираф пива Шихан`.
- `set_bar` exists in the older/operator direct-spend surface, but Victor-approved `Сет тапасов`, `Сет настоек`, and `пивной сет` are not represented by exact runtime keys found in this search.
- `gift_to_ally` exists as a game/social action and should remain separate from Harchevnya bar shelf unless explicitly redesigned.

## 5. Deferred runtime/UI exposure decisions

The full Victor-approved shelf is approved operationally, but runtime exposure still needs a tiny design/implementation decision.

Do not expose the full shelf in player-facing UI until these are decided:

- whether alcohol items are hidden, locked, or operator-only;
- exact player-facing 18+ copy;
- whether `Жираф пива Шихан` maps to existing `giraffe` or needs a new item key;
- how `любой пивной сет (1, 2, 3, 4)` is selected manually;
- whether `Сет тапасов` is always available or staff-confirmed per event;
- whether current labels should be aligned with Victor labels.

## 6. Manual-only replacement policy

Mandatory V1 policy from Victor:

- Any replacement is manual only.
- Replacement is decided by staff/host/cashier, not by automatic game logic.
- If the requested item is unavailable, staff offers replacement verbally/in person.
- House/player must agree to the replacement.
- Cashier/bar confirms the final served item.
- Gold is charged only after cashier/bar confirmation.
- If gold was already charged by mistake, correction/refund is a manual operator action.
- No automatic substitution rules in V1.
- No automatic equivalent-price replacement in V1.
- No automatic alcohol replacement in V1.
- No automatic refund/substitution logic in V1.

Practical flow:

1. `Мастер над золотом` requests an item.
2. Cashier/bar reviews the request.
3. If unavailable, staff offers a replacement in person.
4. House/player accepts or refuses.
5. Cashier/bar confirms only the final served/accepted item.
6. Gold is charged only after confirmation.

## 7. 18+ policy

Conservative V1 policy:

- 18+ items are approved as shelf positions, but service still requires staff/legal confirmation.
- Game screen does not replace real-world age check.
- Staff may refuse service regardless of game gold.
- 18+ items should require clear lock/copy before player-facing runtime expansion.
- Any 18+ replacement is manual only and must be approved by staff.
- No automatic alcohol replacement is allowed.

Items marked 18+ in the approved shelf:

- Шампанское Премиум премьер.
- Сет настоек.
- Жираф пива Шихан.
- любой пивной сет (1, 2, 3, 4).

Items marked non-18+ in the approved shelf:

- Авторский чай.
- Лимонад 0.2 л.
- Пицца Собрание.
- Анна Павлова.
- Сет тапасов.

## 8. Charging policy

Preserve the current safe flow:

- `Мастер над золотом` creates request.
- Cashier/bar reviews request.
- Gold is charged only when cashier/bar confirms.
- No charge should happen while item availability is uncertain.
- Replacement does not happen automatically.
- If staff cannot fulfill the item, cashier should not confirm the original request.
- If a mistaken confirmation happens, correction/refund is manual operator action until a dedicated refund/cancel design exists.

Current economy reference:

- 500 ₽ = 1 золото.

## 9. Current implementation fit

Current flow supports the manual-only policy for the existing safe shelf:

- `POST /player/treasurer-shop/request/{player_id}` creates a pending request.
- Cashier queue receives the request.
- `POST /cashier/treasurer-shop/requests/{request_id}/confirm` confirms and spends gold.
- Confirmed spend appears in events/state.

Runtime gaps:

- full approved shelf is not fully represented in current safe player-facing runtime shelf;
- no active 18+ checkbox/unlock found from prior audit;
- no automatic replacement needed or wanted;
- no availability toggle found;
- no refund/cancel route found;
- no item-level age metadata found;
- no exact runtime keys found for `premium_champagne_premier`, `tincture_set`, `beer_set_any`, or `tapas_set`;
- existing `giraffe` key may need relabeling/mapping before public use.

Design implication:

- Keep the current safe confirmation flow.
- Do not add automatic replacement/refund/substitution.
- Treat full shelf exposure as a narrow UI/copy/config task, not a shop redesign.

## 10. Next recommended task

Recommended next task:

- tiny UI/copy/config audit for exposing Victor-approved shelf safely;
- separate 18+ lock/copy design before exposing alcohol items;
- no code until final decision on whether alcohol items are hidden, locked, or operator-only.

Suggested concrete next output:

- `docs/control/HARCHEVNYA_APPROVED_SHELF_RUNTIME_EXPOSURE_PLAN.md`

That plan should decide:

- exact public labels;
- which approved items are visible immediately;
- which approved items are 18+ locked;
- whether 18+ items require an explicit checkbox/unlock;
- whether any items remain operator-only;
- how current safe request flow is preserved.
