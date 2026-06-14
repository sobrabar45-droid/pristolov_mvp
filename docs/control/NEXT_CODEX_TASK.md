# NEXT_CODEX_TASK

## Приоритет 1
1. `git status --short`.
2. Реализовать отсутствующие `treasurer_shop` route/endpoint по спецификации.
3. Подтвердить role guard: только `treasurer`.
4. Реализовать валидации и расход gold через существующий gold runtime.
5. Реализовать `gift_to_ally` с проверкой active alliance и +1 influence для обоих домов.
6. Реализовать event emission для Master/TV: `event_type=treasurer_shop`, `source=treasurer_shop.purchase`.
7. Подготовить UI `app/templates/treasurer_shop.html` и ссылку на master screen.
8. Прогнать smoke (см. список ниже).

## Smoke-контур
- non-treasurer blocked.
- set_bar: gold -5 + event.
- giraffe: gold -10 + event.
- gift_to_ally without alliance blocked.
- active alliance -> gift_to_ally: gold -15, +1 influence sender, +1 influence ally, event.
- Master/TV recent_events совпадают.

## Проверочный порядок для этого шага
- Проверить `python -m compileall app`.
- trusted no-reload runtime.
- clean LIVE01.
- Smoke и cleanup LIVE01.
