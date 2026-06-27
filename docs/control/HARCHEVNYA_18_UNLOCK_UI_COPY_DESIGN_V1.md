# Harchevnya 18+ unlock UI/copy design V1

Date: 2026-06-28

## 1. Purpose

This document defines a small, safe UI/copy design for exposing Victor-approved Harchevnya alcohol items.

Current audit result:

- Player-facing Harchevnya does not have a working 18+ checkbox/unlock.
- Player-facing Harchevnya currently shows only the safe four-item shelf.
- No runtime 18+ item metadata or backend branching exists.
- Cashier confirmation has no 18+ warning.

This is a design-before-code document. It does not change runtime code, templates, schema, scenario data, production, or LIVE01.

## 2. Design goals

The V1 unlock should:

- keep non-18+ items visible by default;
- keep alcohol hidden or locked until the player explicitly opens the 18+ section;
- clearly say that unlock is not age verification;
- require real staff/bar confirmation before service;
- preserve current safe flow where gold is charged only after cashier/bar confirmation;
- keep all replacement/substitution manual only;
- avoid POS/iiko, inventory, legal automation, and broad shop redesign.

## 3. Approved shelf basis

Victor-approved shelf:

| Item key | Display name | Gold price | 18+ |
|---|---|---:|---|
| `author_tea` | Авторский чай | 3 | NO |
| `premium_champagne_premier` | Шампанское Премиум премьер | 7 | YES |
| `tincture_set` | Сет настоек | 7 | YES |
| `beer_giraffe_shihan` | Жираф пива Шихан | 10 | YES |
| `lemonade_02` | Лимонад 0.2 л | 2 | NO |
| `sobranie_pizza` | Пицца Собрание | 6 | NO |
| `beer_set_any` | Любой пивной сет (1, 2, 3, 4) | 10 | YES |
| `anna_pavlova` | Анна Павлова | 2 | NO |
| `tapas_set` | Сет тапасов | 7 | NO |

Current runtime safe shelf:

- `author_tea` - Авторский чай.
- `lemonade_02` - Лимонад 0.2.
- `sobranie_pizza` - Пицца Собрание.
- `anna_pavlova` - Десерт Анна Павлова.

Gap:

- full Victor-approved shelf is not currently represented in the safe player-facing request shelf;
- `giraffe` exists in an older/operator surface, but not as exact `Жираф пива Шихан` player-facing item;
- champagne, tincture set, beer set, and tapas set are not currently safe player-facing request items.

## 4. Player-facing default state

Default state should show non-18+ items:

- Авторский чай - 3 золота.
- Лимонад 0.2 л - 2 золота.
- Пицца Собрание - 6 золота.
- Анна Павлова - 2 золота.
- Сет тапасов - 7 золота, only if Victor/bar confirms it should be visible immediately.

Default copy:

```text
Харчевня
Заявку отправляет Мастер над золотом.
Золото спишется только после подтверждения кассиром и баром.
```

Availability copy:

```text
Позиции зависят от наличия на баре. Если чего-то нет, замену предлагает сотрудник вручную.
```

18+ locked section teaser:

```text
Есть позиции 18+.
Они показываются отдельно и выдаются только после подтверждения сотрудниками бара.
```

## 5. 18+ unlock behavior

Recommended V1 behavior:

- render an explicit checkbox before alcohol items;
- keep alcohol items hidden until checked;
- after checked, show approved alcohol items with `18+` badge and staff-confirmation copy;
- do not treat checkbox as legal age verification;
- do not store age confirmation in DB in V1 unless future legal/product review requires it;
- submit request payload with item metadata such as `is_18_plus: true` if possible without schema change.

Checkbox label:

```text
Показать позиции 18+
```

Checkbox warning copy:

```text
18+ позиции доступны только совершеннолетним гостям.
Отметка здесь не заменяет проверку документов и решение сотрудников бара.
Бар может отказать в выдаче независимо от золота Дома.
```

After unlock section title:

```text
Позиции 18+
```

Alcohol section hint:

```text
Выдача подтверждается баром. Золото спишется только после подтверждения кассиром.
```

## 6. Alcohol item display

After unlock, show only Victor-approved alcohol items:

| Item key | Player label | Price | Badge | Item copy |
|---|---|---:|---|---|
| `premium_champagne_premier` | Шампанское Премиум премьер | 7 | `18+` | Выдача только после подтверждения бара. |
| `tincture_set` | Сет настоек | 7 | `18+` | Выдача только после подтверждения бара. |
| `beer_giraffe_shihan` | Жираф пива Шихан | 10 | `18+` | Выдача только после подтверждения бара. |
| `beer_set_any` | Любой пивной сет (1, 2, 3, 4) | 10 | `18+` | Конкретный сет выбирается вручную с баром. |

Important:

- Do not show non-approved alcohol names.
- Do not show automatic replacement options.
- Do not imply availability is guaranteed.
- Do not let item copy replace staff/legal checks.

## 7. Cashier/bar confirmation copy

Cashier queue should show a visible warning for 18+ requests.

Cashier card copy for alcohol request:

```text
18+ позиция. Перед подтверждением проверьте возможность выдачи с баром.
Золото списывается только после подтверждения.
```

Staff refusal copy:

```text
Бар может отказать в выдаче независимо от золота Дома.
Если позиция недоступна, замену согласуйте вручную.
```

Confirm button can remain:

```text
Заказ принят
```

But the warning should be near the button for 18+ items.

## 8. Charging policy

Keep current safe flow:

- `Мастер над золотом` creates request.
- Cashier/bar reviews request.
- Gold is charged only when cashier/bar confirms.
- No charge happens while item availability or 18+ service is uncertain.
- Confirmed spend appears in events/state.

Do not add direct player spend for alcohol in V1.

## 9. Replacement policy

Manual-only policy:

- Any replacement is manual only.
- Replacement is decided by staff/host/cashier, not automatic game logic.
- If the requested item is unavailable, staff offers replacement verbally/in person.
- House/player must agree to replacement.
- Cashier/bar confirms the final served item.
- Gold is charged only after confirmation.
- No automatic substitution in V1.
- No automatic equivalent-price replacement in V1.
- No automatic alcohol replacement in V1.
- No automatic refund/substitution logic in V1.

## 10. Minimal future implementation surface

Likely smallest future runtime patch:

- `app/templates/player_room.html`
  - extend item list with full Victor-approved shelf;
  - add `is_18_plus` metadata;
  - render non-18+ items by default;
  - render 18+ checkbox and hide/show alcohol items in JS;
  - add safe copy around availability and staff confirmation.

- `app/routes/player.py`
  - extend `TREASURER_SHOP_REQUEST_ACTIONS` with approved shelf items;
  - include request metadata such as `is_18_plus`, `category`, and approved display label in `GameDeal.offer`;
  - preserve pending request creation and no-spend-on-request behavior.

- `app/routes/cashier.py`
  - allow the same approved request action codes;
  - pass `is_18_plus` / warning metadata to cashier template;
  - preserve spend only on confirmation.

- `app/templates/cashier_gold_desk.html`
  - show 18+ warning on alcohol requests;
  - keep confirmation button flow.

Avoid if possible:

- DB schema change;
- migration;
- POS/iiko integration;
- automatic availability/refund/substitution logic;
- legal age verification automation.

## 11. Backend/item metadata recommendation

Use a single in-code/config item structure if patching:

```text
code
label
cost
is_18_plus
category
public_visible
requires_bar_confirmation
replacement_policy = manual_only
```

For V1 this can live in runtime constants without DB schema if the project wants the smallest patch.

If multiple rooms/franchise shelf customization becomes important later, move shelf config into scenario/game config or an operator-owned setup layer.

## 12. What not to implement in V1

Do not implement:

- automatic substitution;
- automatic refund/substitution logic;
- automatic alcohol replacement;
- legal age verification automation;
- POS/iiko integration;
- broad inventory sync;
- public guarantee that alcohol is always available;
- new economy model;
- direct alcohol spend before cashier/bar confirmation.

## 13. Recommended next task

Recommended next task:

- implement a tiny Harchevnya shelf unlock patch only after confirming this copy/design.

Patch acceptance criteria:

- default player shelf shows non-18+ items;
- checking `Показать позиции 18+` reveals only Victor-approved alcohol items;
- all alcohol items are marked `18+`;
- player copy says staff/bar confirmation is required;
- cashier warning appears for 18+ requests;
- gold is charged only after cashier confirmation;
- no automatic replacement/refund/substitution is added.
