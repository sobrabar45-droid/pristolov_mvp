# OPEN_TASKS

## Что закрыто
- V1 реализован и проверен по коммитам:
  - `set_bar`, `giraffe`, `gift_to_ally` (ранее).
- V1.1 батч реализован и закрыт:
  - `author_tea` — 3 gold
  - `lemonade_02` — 2 gold
  - `sobranie_pizza` — 6 gold
  - `anna_pavlova` — 2 gold
- Проверено:
  - non-treasurer blocked
  - set_bar работает
  - giraffe работает
  - gift_to_ally без союза блокируется
  - gift_to_ally с союзом: `-15` gold и `+1` influence каждому
  - Master/TV события для новых V1.1 действий и существующих V1 действий видны

## Что делать дальше (audit-only)
- Выбрать следующий узкий кандидат на runtime/product-уровне.
- Обновить только документацию/контроль в `docs/control`.
- Не делать runtime patch в этом цикле.
