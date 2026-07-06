# Checkpoint: Public Homepage Production Deploy

## 1. Summary

Public homepage and `/join` polish were deployed successfully to production.

The deploy completed the narrow public UI exception before the live game:

- `/` now serves the public `приСтолов` homepage.
- `/join` now visually matches the public homepage style.
- The game runtime surfaces were not changed as part of this deploy.

## 2. Production target

- Previous production HEAD: `45ec008 Add public homepage`
- New production HEAD: `be04f4c Polish public homepage and join page`
- Service: `pristolov.service`
- Status after restart: `active`

## 3. What changed

Public `/` homepage:

- Homepage visual composition was improved.
- Hero image now behaves as a large atmospheric background layer.
- Public footer contacts were replaced with real contacts:
  - `553-553`
  - `8 912 835-35-53`
  - `vk.ru/pristolov45`
  - `@sobranie_kgn`

Public `/join` page:

- `/join` was restyled to match the public `приСтолов` visual direction.
- Existing join behavior was preserved.
- `POST /join` contract preserved:
  - `method="post"`
  - `action="/join"`
  - `name="room_code"`

## 4. Verification

Production verification passed:

- Compile check: passed
- `GET /` = `200 text/html; charset=utf-8`
- `GET /join` = `200 text/html; charset=utf-8`
- `GET /static/homepage/hero_council_room.png` = `200 image/png`
- Content check: passed
- Forbidden check: `FORBIDDEN_NONE`

Content confirmed on production:

- `приСтолов`
- `Войти в игру`
- `Харчевня`
- `Дипломатия`
- `Суд`
- `/join`
- `Вход в игру приСтолов`
- `Код комнаты`
- `IRON01`
- `На главную`

Contacts confirmed on production:

- `553-553`
- `8 912 835-35-53`
- `vk.ru/pristolov45`
- `@sobranie_kgn`

## 5. Explicit non-actions

The deploy did not include:

- no `LIVE01` touch
- no migrations
- no DB/schema changes
- no `/dev` actions
- no mutating smoke
- no Master/TV/Player/Cashier changes
- no route changes
- no `app/main.py` changes

## 6. Remaining visual checks

Victor should review production `/` and `/join` on a real phone.

Check:

- first-screen readability;
- hero/background balance;
- button clarity;
- `/join` input usability;
- contact visibility and correctness;
- no confusing public promises before the game.

If small visual fixes are needed, make them as a separate narrow public UI patch.

## 7. Next recommended step

Stay in pre-game safety mode.

Recommended order:

1. Do only visual/public UI fixes if Victor finds a blocker.
2. Otherwise return to live-game preparation.
3. Use the production browser smoke protocol for any further non-LIVE checks.
4. Do not expand mechanics before the game unless there is a confirmed P0/P1 blocker and explicit approval.
