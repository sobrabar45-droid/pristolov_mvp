# CHANGELOG

## Latest checkpoint
- P1 Treasurer Shop V1.1 завершён после `2832eaa` и `50d2a01` (runtime + checkpoint).
- Закрыт checkpoint `50d2a01 Add Treasurer Shop V1.1 checkpoint`.
- Исторические checkpoints по Treasurer Shop до V1.1:
  - `5c92d76` Add Treasurer Shop gold spend runtime
  - `16833cf` Add Treasurer Shop V1 checkpoint
  - `52bab30` Align gold formula wording
  - `94fdfc7` Show Treasurer Shop events on master screen
  - `4be1656` Update Treasurer Shop event feed checkpoint
  - `ba99c6f` Update next Codex task after Treasurer Shop V1
  - `2627254` Update next task after role action surface audit
  - `9111c84` Record Treasurer Shop entrypoint decision
  - `c78c9c9` Document Treasurer Shop bar shelf prices
  - `153d319` Select Treasurer Shop V1.1 bar shelf candidates
  - `2832eaa` Add Treasurer Shop V1.1 bar shelf items
  - `50d2a01` Add Treasurer Shop V1.1 checkpoint
- Gold Desk V1 зафиксирован отдельным checkpoint: `2537910 Add Gold Desk check-based gold grants`.
- Реализованы `approved` действий:
  - `set_bar`
  - `giraffe`
  - `gift_to_ally`.
  - `author_tea`
  - `lemonade_02`
  - `sobranie_pizza`
  - `anna_pavlova`.

## Planned change set
- Бэк: `GET /dev/treasurer-shop/{room_code}`, `POST /player/treasurer-shop/{player_id}/purchase` (операторский экран).
- Фронт: `app/templates/treasurer_shop.html`.
- Логика: расход gold через существующий gold runtime, события для Master/TV.
- Закрытые ограничения после V1.1:
  - нет `player_room` purchase buttons
  - нет Court/Final и diplomacy core изменений
  - no new models/tables
- Следующий шаг: audit-only выбор следующего узкого кандидата по Treasuer Shop (без runtime patch).
