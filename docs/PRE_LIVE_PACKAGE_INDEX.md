# Pre-Live Package Index

## 1. Что уже считается стабилизированным

- Court MVP P0
- `stage_court_battle` расширен до `45` вопросов
- `stage_final_show`
- terminal state
- full scenario rehearsal
- operator checklist

## 2. Главные документы

- [COURT_MVP_STABILIZATION_REPORT.md](D:/Projects/pristolov_mvp/docs/COURT_MVP_STABILIZATION_REPORT.md)
- [FULL_SCENARIO_REHEARSAL_REPORT.md](D:/Projects/pristolov_mvp/docs/FULL_SCENARIO_REHEARSAL_REPORT.md)
- [PRE_LIVE_OPERATOR_CHECKLIST.md](D:/Projects/pristolov_mvp/docs/PRE_LIVE_OPERATOR_CHECKLIST.md)
- [PRISTOLOV_SYSTEM_MAP.md](D:/Projects/pristolov_mvp/docs/PRISTOLOV_SYSTEM_MAP.md)
- [PRISTOLOV_RUNTIME_MAP.md](D:/Projects/pristolov_mvp/docs/PRISTOLOV_RUNTIME_MAP.md)
- [PRISTOLOV_PRODUCT_MAP.md](D:/Projects/pristolov_mvp/docs/PRISTOLOV_PRODUCT_MAP.md)
- [PRISTOLOV_ENGINEERING_RULES.md](D:/Projects/pristolov_mvp/docs/PRISTOLOV_ENGINEERING_RULES.md)

## 3. Главные runtime URL для `IRON01`

- master-screen:
  - `/dev/master-screen/IRON01`
- tv-mode:
  - `/dev/tv-mode/IRON01`
- scenario/director:
  - `/dev/games/IRON01/scenario/director`
- master state:
  - `/dev/game-master/IRON01/state`
- tv-state:
  - `/dev/game-master/IRON01/tv-state`
- court state:
  - `/dev/court/state/IRON01`

## 4. Главные known-good проверки

- Court MVP доходит до `court_finished`
- `scenario/advance` после Суда переводит на `stage_final_show`
- финал доходит до terminal state
- в terminal:
  - `active_phases = []`
  - `scenario_finished = true`

## 5. Что НЕ считается закрытым

- настоящая репетиция с живым ведущим
- нагрузка от нескольких операторских действий одновременно
- качество всех вопросов как продукта
- player mobile UX
- физическая логистика зала

## 6. Следующие рекомендуемые шаги

- live dry run с ведущим
- контентная вычитка вопросов
- тест на планшете и TV в заведении
- emergency reset / recovery сценарий
- чек-лист реквизита и ролей команды
