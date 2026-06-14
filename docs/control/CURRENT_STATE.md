# CURRENT_STATE

## Контур
- Проект: `D:\Projects\pristolov_mvp`
- Цель: `P1 Treasurer Shop V1 — spend gold on bar shelf actions`

## Активный контекст
- `Gold Desk` уже введён: `2537910 Add Gold Desk check-based gold grants`.
- Сейчас требуется следующий минимальный контур `Gold -> Spend -> Event / Effect`.

## Задача
- Реализовать Treasurer Shop V1 с тремя действиями:
  - `set_bar` — 5 gold
  - `giraffe` — 10 gold
  - `gift_to_ally` — 15 gold

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
