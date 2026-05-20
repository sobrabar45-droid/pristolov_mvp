# PRISTOLOV RUNTIME MAP

## 1. Runtime Overview
Runtime в проекте — это живая state-машина вечера. Она связывает офлайн-шоу и цифровую orchestration-логику.

Runtime соединяет:
- сценарий
- phases
- host rounds
- TV
- player screens
- Host Control

Ключевые правила:
- runtime mutates only through explicit POST actions
- GET state endpoints должны быть read-only

## 2. Core Runtime Flow
Базовый runtime flow вечера:
1. `scenario director` определяет текущий и следующий шаг сценария.
2. Активируется `stage` вечера.
3. Stage либо открывает `phase`, либо запускает `host_round`.
4. Если это host round, открывается `host_round_question`.
5. Для вопроса создаются `assignments` по ролям и условиям.
6. Игроки совершают действия или отвечают.
7. Runtime фиксирует изменения в сущностях игры.
8. `master_state_service` агрегирует состояние.
9. TV, master и player UI рендерят свои представления runtime.
10. Ведущий закрывает вопрос, завершает phase или двигает сценарий дальше.

## 3. Scenario Director Flow
Director endpoint:
- `/dev/games/{room_code}/scenario/director`

Director отдаёт:
- `current_round`
- `next_round`
- `can_start_next`
- `can_advance`
- `active_system_stage_phase`
- `has_active_host_round`
- `scenario_finished`

Смысл:
- director — orchestration layer поверх сценария
- он показывает, что сейчас живо в сценарии, но сам не должен создавать runtime побочными GET

Ключевой файл:
- `app/services/scenario_service.py`

## 4. Phase Runtime

`GamePhase` используется для открытых системных механик.

| phase_type | Зачем существует | Кто открывает | Кто закрывает | Кто зависит |
|---|---|---|---|---|
| `map` | этап карты и разведки | scenario stage | scenario advance | TV, master, player map/expedition layer |
| `diplomacy` | окно сделок и переговоров | scenario stage | scenario advance | TV, master, player deals |
| `crest` | этап герба / символического конструирования | scenario stage | scenario advance | TV, master |
| `duel` | системная фаза дуэлей | scenario stage | scenario advance | TV, master |
| `free_play` | свободная игровая фаза | scenario stage | scenario advance | TV, master, player |
| `court` | Court MVP runtime | scenario stage / court endpoints | scenario advance / court flow | TV court mode, master court panel |
| `host_round` | фаза вопросного раунда | start host round | finish/advance host round | TV, master, player assignments |

Важно:
- system stages открывают phases
- system stages не должны превращаться в обычные host_round

## 5. Host Round Runtime

Основные сущности:
- `GameHostRound`
- `GameHostRoundQuestion`
- `RoundTemplate`
- `RoundQuestionTemplate`

Flow:
1. Открывается `host_round`.
2. Ведущий открывает следующий вопрос.
3. Создаётся `GameHostRoundQuestion`.
4. По вопросу создаются `assignments`.
5. Идёт таймер и active question mode.
6. Ведущий делает `force close` или дожидается финала окна.
7. Вопрос переходит в reveal.
8. Ведущий делает `continue`.
9. Раунд завершается.

Ключевые файлы:
- `app/services/host_round_service.py`
- `app/services/assignment_service.py`

## 6. Assignment Flow
Assignments — это ключевая связь между runtime и игроком.

Что происходит:
- runtime-вопрос создаёт assignments
- assignments фильтруются по роли
- player screen получает assignment и UI для ответа/действия
- ответ проходит через assignment service
- дальше идёт auto-check или confirm/manual flow
- reveal pipeline читает уже зафиксированный результат

Что важно:
- role-targeting не ломать
- `answer_mode` и `ui_template` не путать
- confirm-mode уже используется для readiness/court confirm actions

## 7. State Aggregation
Главный агрегатор:
- `app/services/master_state_service.py`

Он собирает:
- `active_phases`
- `active_host_round`
- `current_question`
- deals
- expeditions
- `court_runtime`

Разделение:
- `master-state` — orchestration/state для master screen
- `tv-state` — show/state для TV
- player state — отдельный слой через `player.py`

Важно:
- GET state endpoints read-only
- P0 already fixed: court sync больше не происходит при GET

## 8. TV Runtime Flow
Главный файл:
- `app/templates/tv_mode_tv_state.html`

TV flow:
1. polling `tv-state`
2. active scene resolution
3. question mode / reveal mode
4. timer pipeline
5. question media pipeline
6. court mode
7. fallback scene, если нет активного вопроса

Важно:
- TV — show layer
- TV не должен содержать бизнес-логику
- TV не должен мутировать runtime

## 9. Master Runtime Flow
Главный файл:
- `app/templates/master_screen.html`

Master flow:
1. polling `master-state`
2. scenario control
3. host round control
4. phase control
5. court control
6. визуализация текущего orchestration status

Важно:
- master = orchestration/operator layer
- бизнес-логика должна жить в services, а не в большом HTML

## 10. Player Runtime Flow
Основные файлы:
- `app/routes/player.py`
- `app/templates/player_room.html`

Игрок получает:
- assignments
- diplomacy / deals
- expeditions
- resources
- role actions
- статусные экраны по фазам

Важно:
- player layer пока partially overloaded
- там смешаны assignments, deals, expeditions и часть role-actions

## 11. Court MVP Runtime
Court MVP сейчас устроен так:

- `stage_court` — сценарный этап суда
- `court_runtime` хранится в `GamePhase.payload`
- `stage_court_battle` — question-bank для court questions
- phones пока passive/status-only

### Court Runtime Structure
Ключевые поля:
- `bracket`
- `current_pair_index`
- `current_pair`
- `history`
- `status`
- `current_question`

### Pair Flow
1. `generate-bracket`
2. `start-pair`
3. `open-question`
4. `force-close-question`
5. `mark-result`
6. `pair_result`
7. `confirm-pair-winner`
8. `next-pair`
9. `court_finished`

### Question Flow
- Суд не создаёт новый question engine
- Он использует existing host_round runtime
- `stage_court_battle` держит sequence вопросов

### mark-result
Ожидаемая логика:
- `side=a, result=correct` → выбывает `B`
- `side=a, result=wrong` → выбывает `A`
- `side=b, result=correct` → выбывает `A`
- `side=b, result=wrong` → выбывает `B`

### Текущее важное
- `court_runtime` остаётся в `GamePhase.payload`
- `stage_court_battle` не должен становиться сценарием, это question-bank
- завершение суда должно приводить к `court_finished`

### Current Known Risks
- `bye` при нечётном числе Домов
- question sequencing
- pair score validation

## 12. State Endpoint Map

### GET

| Endpoint | Что читает | Что не должен делать |
|---|---|---|
| `/dev/game-master/{room_code}/state` | master aggregate state | не должен мутировать runtime |
| `/dev/game-master/{room_code}/tv-state` | TV aggregate state | не должен мутировать runtime |
| `/dev/games/{room_code}/scenario/director` | orchestration status сценария | не должен создавать runtime |
| `/dev/court/state/{room_code}` | Court MVP runtime | только читать |

### POST

| Endpoint | Что мутирует |
|---|---|
| `scenario/apply` | game → linked scenario |
| `scenario/start-next-round` | stage start / phase open / host_round start |
| `scenario/advance` | stage close / round finish / phase close |
| `open-next-question` | `GameHostRoundQuestion`, assignments |
| `force-close-question` | current runtime question → reveal |
| `host-continue` | host round finish |
| `court/generate-bracket` | court payload / bracket |
| `court/start-pair` | current court pair |
| `court/open-question` | court question flow inside `stage_court_battle` |
| `court/mark-result` | pair score / eliminations / history |
| `court/confirm-pair-winner` | pair winner confirmation |
| `court/next-pair` | pair transition / `court_finished` |

## 13. Runtime Safety Rules
- GET state endpoints are read-only
- runtime mutates only through POST
- system stages != host_round
- TV не должен мутировать runtime
- master не должен содержать бизнес-логику
- scenario director не должен иметь hidden side effects
- `court_runtime` нельзя выносить из payload без причины
- `host_round` flow — самый стабильный контур проекта

## 14. Current Live Status
- active scenario: `season1_mvp_live_v2`
- dev room: `IRON01`
- Court MVP active
- system stages stabilized
- guard against accidental `scenario/advance` on unfinished `stage_court` уже добавлен

## 15. Next Runtime Targets

### P0
- court stabilization
- `bye` flow
- question sequencing
- pair score correctness

### P1
- state contracts
- player runtime split
- diplomacy normalization

### P2
- multi-role runtime
- performance stabilization
- websocket / event model later
