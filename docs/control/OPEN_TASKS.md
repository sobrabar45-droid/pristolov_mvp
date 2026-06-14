# OPEN_TASKS

## Что нужно сделать
- Проверить `git status --short` и остановиться при dirty tree до изменения (для чистого шага выполнения).
- Реализовать/проверить маршрут: `GET /dev/treasurer-shop/{room_code}`.
- Реализовать/проверить маршрут: `POST /player/treasurer-shop/{player_id}/purchase`.
- Проверить guard роли `treasurer`.
- Реализовать список действий с ценами:
  - `set_bar` — 5
  - `giraffe` — 10
  - `gift_to_ally` — 15
- Реализовать валидацию `gift_to_ally`:
  - `target_house_id` обязателен;
  - target дом существует в той же игре;
  - между домами есть активный союз.
- Убедиться, что `spend_gold_for_action` используется для списания.
- Вписать влияние по `gift_to_ally`:
  - +1 sender house
  - +1 target house
- Emit Master/TV событие (`event_type = treasurer_shop`, `source = treasurer_shop.purchase`).
- Создать шаблон `app/templates/treasurer_shop.html`.
- Добавить ссылку в master screen: `Открыть Treasurer Shop`.

## Что проверять
- non-treasurer blocked.
- set_bar: gold -5, событие видно.
- giraffe: gold -10, событие видно.
- gift_to_ally без союза: отказ.
- gift_to_ally с союзом: gold -15 и +1 influence каждому.
- Master/TV recent events отражают событие.
- cleanup LIVE01 после smoke.
