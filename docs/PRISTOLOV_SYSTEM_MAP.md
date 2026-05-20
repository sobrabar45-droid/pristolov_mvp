# PRISTOLOV SYSTEM MAP

## 1. Product Identity
«Игра приСтолов» — не классический квиз. Это барная командная игра Домов, где цифровой контур не заменяет офлайн-шоу, а усиливает его: помогает ведущему, связывает экраны, фиксирует решения и показывает последствия.

Ключевые элементы системы:
- Дома
- роли
- золото
- влияние
- ресурсы
- герб
- карта
- дипломатия
- дуэли
- Суд Домов
- TV-экран
- master / host control
- player screens

## 2. Core Game Loop
Базовый цикл игры:
1. Ведущий открывает этап сценария.
2. TV показывает текущее состояние мира или вопрос.
3. Игроки получают задания, решения или статусные экраны.
4. Дома взаимодействуют через ответы, сделки, дипломатию, ресурсы и системные механики.
5. Runtime обновляет состояние игры.
6. TV и master показывают последствия.
7. Сценарий движется к следующему этапу.

## 3. Architecture Layers

| Слой | Назначение | Ключевые файлы | Что нельзя смешивать |
|---|---|---|---|
| `app/models` | Доменные и runtime-сущности | `game.py`, `player.py`, `house.py`, `game_phase.py`, `game_host_round.py`, `game_host_round_question.py`, `game_assignment.py`, `game_deal.py`, `round_template.py`, `round_question_template.py` | Не класть orchestration и HTTP-логику |
| `app/services` | Бизнес-логика и orchestration | `scenario_service.py`, `host_round_service.py`, `assignment_service.py`, `master_state_service.py`, `diplomacy_service.py`, `court_service.py`, `phase_service.py` | Не превращать в слой HTML/API |
| `app/routes` | HTTP endpoints и entrypoints экранов | `dev.py`, `player.py`, `join.py`, `delegation.py` | Routes не должны зависеть от routes; не держать там тяжёлую доменную логику |
| `app/templates` | UI-экраны и клиентский JS | `master_screen.html`, `tv_mode_tv_state.html`, `player_room.html` | Не делать backend-orchestration внутри шаблонов |
| `app/game_templates` | Source of truth для сценариев и шаблонов | `scenarios/*.json` | Не подменять живой runtime логикой шаблонов |
| `app/static/questions_media` | Медиа для импортированных вопросов | файлы изображений вопросов | Не смешивать с runtime payload |
| `docs` | Инженерная карта и договорённости | этот документ и вспомогательные заметки | Не хранить там runtime-логику |

## 4. Runtime Entities

### GamePhase
- Отвечает за открытую фазу игры.
- Используется для `map`, `diplomacy`, `crest`, `free_play`, `duel`, `court`, а также для `host_round`.
- Важно не ломать: `phase_type`, `status`, `payload` и lifecycle открытия/закрытия.

### GameHostRound
- Отвечает за runtime раунд ведущего.
- Используется для вопросных/заданийных этапов и для court question bank.
- Важно не ломать: `round_code`, `current_question_no`, `questions_total`, `answers_open`, `status`.

### GameHostRoundQuestion
- Отвечает за runtime текущего вопроса внутри host round.
- Используется в reveal pipeline и для таймера/TV/player state.
- Важно не ломать: `status`, `answers_open`, последовательность вопросов.

### GameAssignment
- Отвечает за задание/вопрос, выданный конкретному игроку.
- Используется player screen и assignment flow.
- Важно не ломать: `answer_mode`, `status`, `answer_payload`, `result_payload`.

### GameDeal
- Отвечает за сделки между Домами.
- Используется в дипломатии, counter-offer, подтверждении, казначейских действиях.
- Важно не ломать: статусы сделки, JSON offer/payload, связь с ресурсными изменениями.

### court_runtime
- Отвечает за runtime Суда Домов.
- Хранится в `GamePhase.payload` для `phase_type = "court"`.
- Используется master panel, TV court mode и court endpoints.
- Важно не ломать: `bracket`, `current_pair`, `history`, `status`, `current_question`.

## 5. Scenario Model
Главная архитектурная истина:

**Stage / этап вечера ≠ HostRound ≠ Phase**

- `Stage` — глобальный шаг сценария вечера.
- `HostRound` — вопросный или заданийный runtime.
- `Phase` — открытая системная механика.

Что из этого важно:
- карта, дипломатия, герб, дуэли, суд — это не обычные `host_round`
- `host_round` нужен только для вопросов и заданий
- один сценарный этап может открывать фазу, а не раунд
- Суд Домов — это сценарный этап + court runtime + court question bank, а не старый `court_q1`

## 6. Live MVP Sequence
Текущий live-сценарий: `season1_mvp_live_v2`

| order_no | round_code | Смысл |
|---|---|---|
| 10 | `stage_intro` | readiness и запуск вечера |
| 20 | `stage_truth_lie_opening` | быстрый старт на вопросах правда/ложь |
| 30 | `stage_four_options` | лёгкий вопросный блок с 4 вариантами |
| 40 | `stage_map_entry` | вход в карту и разведочный слой |
| 50 | `stage_diplomacy_1` | окно дипломатии и барных переговоров |
| 60 | `stage_crest` | этап герба / символического усиления Дома |
| 70 | `stage_free_play` | свободный игровой цикл решений и взаимодействий |
| 80 | `stage_duels` | дуэли Домов |
| 90 | `stage_court` | Суд Домов как отдельная court-механика |
| 100 | `stage_final_show` | простой финальный show-step |

## 7. UI Map

### Master
- URL: `/dev/master-screen/{room_code}`
- Файл: `app/templates/master_screen.html`
- Роль: пульт ведущего / операторский экран / control panel

### TV
- URL: `/dev/tv-mode/{room_code}`
- Файл: `app/templates/tv_mode_tv_state.html`
- Роль: экран зала / show layer / reveal / системные сцены

### Player
- Routes: `app/routes/player.py`
- Template: `app/templates/player_room.html`
- Роль: экран игрока / роли / задания / решения / сделки / статусы

## 8. State Map

| Endpoint | Назначение |
|---|---|
| `/dev/game-master/{room_code}/state` | агрегированный state для master screen |
| `/dev/game-master/{room_code}/tv-state` | агрегированный state для TV screen |
| `/dev/games/{room_code}/scenario/director` | director сценария: текущий шаг, следующий шаг, доступность advance/start |
| `/dev/court/state/{room_code}` | состояние Court MVP |

Ключевое правило:
- GET state endpoints должны быть read-only
- runtime меняется только через explicit POST actions

## 9. Court MVP Map
Текущий Суд Домов устроен так:
- `stage_court` — сценарный этап суда
- `court_runtime` хранится в `GamePhase.payload`
- `stage_court_battle` — question-bank для вопросов суда
- master court panel управляет парами и исходами
- TV court mode показывает пары, счёт, вопросы, reveal и завершение суда
- player пока passive/status-only

Текущие риски и зоны внимания:
- `bye` при нечётном числе Домов
- контроль последовательности court questions
- корректность `mark-result`
- чистое завершение суда
- polish финального court-screen

## 10. Engineering Rules
- не превращать игру в квиз
- не смешивать `stage` / `host_round` / `phase`
- не делать GET с side effects
- runtime mutates only through POST
- не ломать existing `host_round` flow
- не делать большой рефакторинг без причины
- не переписывать большие HTML целиком
- Codex-задачи делать минимальными, проверяемыми и локальными

## 11. Current Live Status
- active scenario: `season1_mvp_live_v2`
- dev room: `IRON01`
- Court MVP активен и встроен в live-сценарий
- P0-1 закрыт: read-only state стабилизирован
- P0-2 закрыт: `player.py` больше не импортирует helpers из `dev.py`
- текущий фокус: stabilization Court MVP after GUI run

## 12. Next Engineering Targets

### P0
- Court MVP stabilization:
  - убрать duplicate button
  - проверить question sequencing
  - проверить `mark-result` score logic
  - обработать `bye` / `court_finished`

### P1
- state contracts
- player domain services
- diplomacy cleanup

### P2
- multi-role preparation
- performance / polling optimization
