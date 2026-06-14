# CHANGELOG

## Latest checkpoint
- P1 Treasurer Shop V1 подготовлен как следующий контур после Gold Desk V1.
- Gold Desk V1 зафиксирован отдельным checkpoint: `2537910 Add Gold Desk check-based gold grants`.
- Контур находится на этапе реализации `Gold -> Spend -> Event / Effect` с тремя approved actions:
  - `set_bar`
  - `giraffe`
  - `gift_to_ally`.

## Planned change set
- Бэк: `GET /dev/treasurer-shop/{room_code}`, `POST /player/treasurer-shop/{player_id}/purchase`.
- Фронт: `app/templates/treasurer_shop.html`, ссылка на master screen.
- Логика: расход gold через gold runtime, события для Master/TV.
- Никаких архитектурных миграций в этой итерации.
