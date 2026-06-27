# Checkpoint: Harchevnya 18+ unlock shelf

Date: 2026-06-28

## 1. Summary

Runtime commit:

- `37058ed Add Harchevnya 18 unlock shelf`

Purpose:

- expose the Victor-approved Harchevnya shelf through the existing safe request flow;
- add a player-facing 18+ unlock for alcohol items;
- add cashier/bar warning for 18+ requests;
- preserve the current rule that gold is charged only after cashier/bar confirmation;
- preserve manual-only replacement policy.

Implemented behavior:

- Victor-approved Harchevnya shelf was added to the request flow.
- Non-18+ items are visible by default.
- 18+ items are hidden by default and shown after explicit player unlock.
- 18+ request metadata is stored in the existing request payload.
- Cashier queue shows an 18+ warning before confirmation.
- Legacy direct-spend endpoint is guarded so request-only 18+ items do not bypass cashier confirmation.
- No automatic replacement, refund, substitution, POS integration, inventory sync, migration, DB schema change, or scenario change was added.

Safe request flow preserved:

- `Мастер над золотом` creates a pending Harchevnya request.
- Cashier/bar reviews the request.
- Gold is charged only after cashier confirmation.
- If an item is unavailable, replacement is manual only.

## 2. Files changed by runtime patch

Runtime patch changed exactly these files:

- `app/routes/cashier.py`
- `app/routes/player.py`
- `app/templates/cashier_gold_desk.html`
- `app/templates/player_room.html`

## 3. Approved shelf

Victor-approved Harchevnya shelf:

| Item key | Display name | Gold price | 18+ |
|---|---|---:|---|
| `author_tea` | Авторский чай | 3 | NO |
| `premium_champagne_premier` | Шампанское Премиум премьер | 7 | YES |
| `tincture_set` | Сет настоек | 7 | YES |
| `beer_giraffe_shihan` | Жираф пива Шихан | 10 | YES |
| `lemonade_02` | Лимонад 0.2 л | 2 | NO |
| `sobranie_pizza` | Пицца Собрание | 6 | NO |
| `beer_set_any` | любой пивной сет (1, 2, 3, 4) | 10 | YES |
| `anna_pavlova` | Анна Павлова | 2 | NO |
| `tapas_set` | Сет тапасов | 7 | NO |

Default non-18+ player shelf:

- Авторский чай
- Лимонад 0.2 л
- Пицца Собрание
- Анна Павлова
- Сет тапасов

18+ shelf shown after unlock:

- Шампанское Премиум премьер
- Сет настоек
- Жираф пива Шихан
- любой пивной сет (1, 2, 3, 4)

## 4. 18+ behavior

Player-facing behavior:

- 18+ items are hidden by default.
- Player UI includes explicit checkbox: `Показать позиции 18+`.
- After unlock, only Victor-approved alcohol items are shown.
- Alcohol items are visibly marked as `18+`.
- Player copy says that 18+ positions are available only to adult guests.
- Player copy says the checkbox does not replace document/staff check.
- Player copy says the bar may refuse service regardless of House gold.

Cashier/bar behavior:

- Cashier queue receives `is_18_plus` metadata.
- Cashier queue shows warning for 18+ requests:
  - `18+ позиция. Перед подтверждением проверьте возможность выдачи с баром.`
  - `Бар может отказать в выдаче независимо от золота Дома.`
  - `Если позиция недоступна, замену согласуйте вручную.`

Staff/legal check:

- The game screen does not replace real-world staff/legal age checks.
- Staff may refuse service regardless of game gold.
- 18+ service remains real-world staff responsibility.

## 5. Charging and replacement

Charging policy:

- Request creation does not spend gold.
- Cashier confirmation spends gold.
- Gold remains charged only after cashier/bar confirmation.

Replacement policy:

- Replacement is manual only.
- Replacement is decided by staff/host/cashier.
- House/player must agree to replacement.
- No automatic substitution was added.
- No automatic equivalent-price replacement was added.
- No automatic alcohol replacement was added.
- No automatic refund/substitution logic was added.

## 6. Verification

Compile:

```text
python -m py_compile app\routes\player.py app\routes\cashier.py
```

Result:

- passed.

Focused local mutating smoke:

- room: `TEST_ROOM_SETUP`
- local/dev DB only
- production not touched
- `LIVE01` not touched

Safe item request:

```text
item=tapas_set
status_code=200
ok=true
request_id=97
status=pending
cost_gold=7
is_18_plus=false
replacement_policy=manual_only
gold before request=11
gold after request before confirmation=11
```

18+ item request:

```text
item=tincture_set
status_code=200
ok=true
request_id=98
status=pending
cost_gold=7
is_18_plus=true
category=alcohol
requires_bar_confirmation=true
replacement_policy=manual_only
cashier warning visible=true
gold before request=11
gold after request before confirmation=11
```

Cashier confirmation:

```text
confirmed request_id=97
status_code=200
ok=true
request_status=completed
transaction_id=135
transaction_amount=-7
gold before confirmation=11
gold after confirmation=4
```

## 7. Regression checks

Passed:

- invalid action rejected;
- request-only 18+ items blocked from legacy direct-spend endpoint;
- no invalid terminology found in touched files;
- no automatic substitution/refund/replacement logic added.

Direct-spend guard evidence:

- `tincture_set` was rejected by legacy direct-spend endpoint.
- gold before direct-spend guard check: `11`
- gold after direct-spend guard check: `11`

## 8. Local artifacts

Local smoke artifacts in `TEST_ROOM_SETUP`:

- `player_id=955 Test Treasurer`
- `request_id=97 tapas_set completed`
- `request_id=98 tincture_set pending`
- `transaction_id=135 amount=-7`
- `house_id=282 gold changed 11 -> 4`

These artifacts are local/dev DB artifacts only.

## 9. Not done / risks

Not done:

- production deployment not performed;
- production smoke not performed;
- `LIVE01` not touched;
- visual browser smoke not performed after patch;
- no POS/iiko integration;
- no inventory sync;
- no availability toggle;
- no automatic refund/cancel workflow;
- no DB schema change;
- no scenario JSON change.

Remaining risks:

- visual spacing/readability of player Harchevnya and cashier queue should still be checked in browser;
- local `TEST_ROOM_SETUP` contains smoke artifacts;
- 18+ legal/staff responsibility remains real-world staff responsibility;
- production HEAD/deployment status is not confirmed for this patch.

## 10. Next recommended task

Recommended next task options:

1. Local visual/browser smoke of player Harchevnya and cashier queue.
2. Production deployment/read-only status check before rollout, only by explicit user command.
3. Docs update for operator live checklist, including Harchevnya 18+ cashier/staff confirmation steps.

Do not run production deployment, production smoke, restart, migration, or LIVE01 actions without explicit user command.
