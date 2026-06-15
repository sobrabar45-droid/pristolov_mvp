# CURRENT_STATE

## Контур
- Проект: `D:\Projects\pristolov_mvp`
- Цель: `P1 Treasurer Shop V1.1 — закрыт после внедрения первого батча барных SKU`

## Активный контекст
- `Gold Desk` уже введён: `2537910 Add Gold Desk check-based gold grants`.
- Закрыт контур `Gold -> Spend -> Event / Effect` для Treasurer Shop V1 и V1.1.

## Задача
- Реализовать Treasurer Shop V1:
  - `set_bar` — 5 gold
  - `giraffe` — 10 gold
  - `gift_to_ally` — 15 gold
- Реализован V1.1 батч барных SKU (bar/social-only):
  - `author_tea` — 3 gold
  - `lemonade_02` — 2 gold
  - `sobranie_pizza` — 6 gold
  - `anna_pavlova` — 2 gold

## Ограничения исполнения
- Не вводить новые DB models.
- Не менять core gold architecture.
- Не менять Court/Final, diplomacy core.
- Не делать POS integration.
- Не делать refactor.
- Не делать commit автоматически.

## Ключевой прогресс
- API должен содержать:
  - `GET /dev/treasurer-shop/{room_code}`
  - `POST /player/treasurer-shop/{player_id}/purchase`
- UI должен быть отдельным экраном `app/templates/treasurer_shop.html`.
- `gift_to_ally` требует активный союз между домами.
- События о покупке должны быть видны Master/TV.
- Oператорный маршрут по-прежнему: ` /dev/treasurer-shop/{room_code}`.
- Кнопки покупки в `player_room` не добавлялись и не менялись.
- Алькогольные/юридически спорные позиции остаются отложены:
  - `champagne_premier`
  - `tincture_set`
  - `shihan_beer_giraffe`
  - `beer_set_any`.
