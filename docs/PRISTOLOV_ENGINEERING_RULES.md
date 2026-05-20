# PRISTOLOV ENGINEERING RULES

## 1. Project Engineering Principles
- offline-first
- digital augmentation
- runtime safety first
- additive changes preferred
- no destructive refactors during MVP
- explicit orchestration over magic
- show-first UX

Практический смысл:
- офлайн-шоу важнее интерфейса
- цифровой слой усиливает ведущего, а не заменяет его
- стабильный runtime важнее “красивой архитектуры”
- во время MVP правки должны быть минимальными и проверяемыми

## 2. Stage / Phase / Host Round Rules
Базовая истина:
- `stage != phase != host_round`

Определения:
- `stage` — глобальный этап вечера в сценарии
- `phase` — открытое runtime-окно механики
- `host_round` — runtime вопросов / заданий

Правила:
- `system_stage` не должен автоматически создавать обычный `host_round`
- `host_round` используется только для вопросного или заданийного flow
- `phase` открывает системную механику: карта, дипломатия, герб, дуэли, суд

Примеры:
- `stage_map_entry` → открывает `phase=map`, не `host_round`
- `stage_diplomacy_1` → открывает `phase=diplomacy`
- `stage_court` → открывает `phase=court`, а не legacy `court_q1`
- `stage_truth_lie_opening` → это `host_round`

## 3. State Rules
Главное правило:
- `GET state endpoints must be read-only`

Фиксации:
- `GET` не мутирует runtime
- sync выполняется только в explicit `POST` actions
- state должен быть predictable
- shape state нельзя менять хаотично
- derived view допустим, скрытая запись в БД — нет

## 4. Master / TV / Player Contracts
Стабильные контракты:

| Contract | Что должно быть стабильно |
|---|---|
| `master-state` | `active_host_round`, `current_question`, `active_phases`, `court_runtime`, deals, control state |
| `tv-state` | `active_host_round`, `current_question`, reveal data, `court_runtime`, show state |
| `player-state` | assignments, deals, resources, role actions, player-specific context |

Обязательные поля, которые нельзя ломать без причины:
- `active_host_round`
- `current_question`
- `active_phases`
- `court_runtime`
- deals sections
- assignments

## 5. Court MVP Rules
- `court_runtime` живёт в `GamePhase.payload`
- Court MVP остаётся `master-operated`
- phones в Court MVP пока passive/status
- Court использует existing `host_round` question pipeline
- `stage_court_battle` — question bank, а не сценарный stage
- `stage_court` — phase-driven этап суда

Нельзя:
- выносить Court MVP в отдельную БД-модель без реальной причины
- превращать Суд в обычный quiz round

## 6. Route Rules
Запрещено:
- route-to-route imports
- бизнес-логика в routes
- ORM orchestration inside HTML templates

Разрешено:
- thin routes
- validation / parsing запроса
- вызов service layer как source of truth

Правило:
- routes должны координировать HTTP, а не держать доменную логику

## 7. Service Rules
- services отвечают за domain logic
- orchestration в services допустим
- side effects должны быть explicit
- state aggregation должна быть отделена от mutation logic
- shared helpers должны жить в services, не в routes

Запрет:
- read-only сервис не должен скрыто писать в runtime

## 8. Template Rules
Ключевые runtime UIs:
- `master_screen.html`
- `tv_mode_tv_state.html`
- `player_room.html`

Правила:
- это stateful runtime UIs, а не простые статичные шаблоны
- нельзя переписывать их целиком во время MVP
- изменения должны быть additive
- нельзя ломать existing scenes ради одной новой механики
- нельзя плодить fallback chaos в данных и рендеринге

Практика:
- сначала локализовать сцену/блок
- потом вносить точечную правку

## 9. Scenario Rules
- JSON scenario = source of truth
- linked scenario в БД не должен drift'ить от JSON
- для live scenarios использовать `import_mode=replace`
- system stages открывают phases
- court stage должен быть phase-driven

Запрет:
- не использовать question-bank как отдельный ранний stage сценария, если он не задуман как stage

## 10. Runtime Safety Rules
Запрещено:
- implicit runtime creation on `GET`
- hidden sync on polling
- multiple active `host_round` без реальной причины
- silent fallback logic, которая скрывает поломки

Разрешено:
- explicit runtime mutation через `POST`
- явный cleanup runtime

## 11. Performance / Scale Rules
Подготовка к `8–10` Домам:
- polling должен быть безопасным
- state должен оставаться lightweight
- избегать тяжёлой повторной агрегации без причины
- cleanup runtime должен быть явным
- `reset-runtime` должен знать все runtime systems

Правило:
- любое добавление новой runtime-механики требует проверки cleanup и polling-поведения

## 12. Future Multi-Role Rules
- не размазывать single-role assumptions по всему проекту
- не хардкодить role checks в UI, если можно вынести в helper/service
- permission checks вести через service/helper layer

Пока:
- БД не трогаем
- но новые изменения не должны усиливать жёсткую привязку к `player.role.code`

## 13. Codex Workflow Rules
Работа с Codex:
1. Сначала диагноз.
2. Потом точечная правка.
3. Потом проверка.
4. Потом отчёт.

Обязательный отчёт:
- changed files
- что изменено
- проверки
- риски

Правило:
- минимальная правка лучше большого “архитектурного улучшения”, если live уже работает

## 14. What Must Not Be Touched During MVP
Не трогать без крайней необходимости:
- `host_round` pipeline
- `court_runtime` architecture
- `game_templates` как source of truth
- core runtime `TV/master`
- state contracts без явной причины
- massive refactors

Особенно нельзя:
- ломать existing `question/reveal/timer` flow
- переписывать runtime orchestration “с нуля”

## 15. Current Known Risks
- `dev.py` overload
- большие HTML runtime files
- unstable UI contracts
- onboarding duplication
- future multi-role pressure
- performance under polling

Это known debt, а не сигнал переписывать проект целиком прямо сейчас.

## 16. Next Engineering Targets
### P0
- state stabilization
- runtime predictability
- Court MVP stabilization
- UI contract hardening

### P1
- service extraction
- player domain split
- diplomacy normalization

### P2
- safe scaling
- performance stabilization
- multi-role preparation
