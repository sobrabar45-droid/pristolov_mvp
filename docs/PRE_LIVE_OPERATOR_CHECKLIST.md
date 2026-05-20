# Pre-Live Operator Checklist

## 1. Подготовка до прихода гостей

### Поднять сервер

- Запустить `uvicorn` / локальный backend.
- Убедиться, что комната для прогона: `IRON01`.

### Подготовить чистое состояние

Сделать по порядку:

1. `POST /dev/games/IRON01/reset-runtime`
2. `POST /dev/games/IRON01/scenario/apply`
   - payload: `{"scenario_code":"season1_mvp_live_v2"}`

### Открыть рабочие экраны

- Master:
  - `/dev/master-screen/IRON01`
- TV:
  - `/dev/tv-mode/IRON01`
- Director:
  - `/dev/games/IRON01/scenario/director`
- Master state:
  - `/dev/game-master/IRON01/state`

### Что должно быть видно

- Director:
  - `next_round = stage_intro`
  - `can_start_next = true`
- Master:
  - нет активного раунда
  - нет активной court-сцены
- TV:
  - нет stale вопроса или суда

## 2. Проверка TV

Перед гостями проверить:

- TV открывается без ошибки.
- При смене этапа меняется сцена.
- После закрытия этапа не остаётся stale screen от предыдущего режима.

Быстрый признак нормы:

- `tv-state` соответствует тому, что видно на TV.

## 3. Проверка master

Перед стартом проверить:

- action-panel отвечает;
- director меняется после нажатий;
- host controls появляются только когда реально есть host round;
- court controls появляются только на этапе `stage_court`.

Быстрый признак нормы:

- `master-screen` и `scenario/director` показывают один и тот же текущий этап.

## 4. Пошаговый flow вечера

## Intro

Ведущий видит:
- стартовый раунд

TV показывает:
- стартовую сцену вечера

Действия:
1. Нажать `Start next round`
2. Открыть вопрос
3. Закрыть вопрос
4. Нажать `Host continue`

Если что-то пошло не так:
- проверить `/dev/games/IRON01/scenario/director`
- проверить `/dev/game-master/IRON01/state`

## Truth / Lie

Ведущий видит:
- раунд `stage_truth_lie_opening`

TV показывает:
- обычный question / reveal flow

Действия:
1. `Start next round`
2. Для каждого вопроса:
   - `Open next question`
   - при необходимости `Force close question`
3. После последнего вопроса:
   - `Host continue`

Проверка:
- `active_host_round = stage_truth_lie_opening`

## Four Options

Ведущий видит:
- раунд `stage_four_options`

TV показывает:
- обычный question / reveal flow

Действия:
- те же, что и в Truth / Lie

Проверка:
- director после раунда переводит на следующий stage

## Map

Ведущий видит:
- system stage, не quiz round

TV показывает:
- map phase

Действия:
1. `Start next round`
2. После завершения блока нажать `Scenario advance`

Проверка:
- нет обычного `active_host_round`
- есть `active_system_stage_phase = map`

## Diplomacy

Ведущий видит:
- diplomacy phase

TV показывает:
- сцену дипломатии / политического окна

Действия:
1. `Start next round`
2. После завершения окна `Scenario advance`

Проверка:
- `active_system_stage_phase = diplomacy`

## Crest

Ведущий видит:
- crest phase

TV показывает:
- stage герба

Действия:
1. `Start next round`
2. После завершения блока `Scenario advance`

## Free Play

Ведущий видит:
- свободную игровую фазу

TV показывает:
- нейтральную show-сцену свободной игры

Действия:
1. `Start next round`
2. После окна `Scenario advance`

## Duels

Ведущий видит:
- duel phase

TV показывает:
- stage дуэлей

Действия:
1. `Start next round`
2. После блока дуэлей `Scenario advance`

Проверка:
- следующий stage должен стать `stage_court`

## Court

Ведущий видит:
- court panel

TV показывает:
- court mode

Действия:
- использовать отдельный court flow из раздела ниже

После `court_finished`:
1. Убедиться, что Суд действительно завершён
2. Нажать `Scenario advance`

Проверка:
- следующий этап должен стать `stage_final_show`

## Final Show

Ведущий видит:
- финальную сцену, а не обычный generic вопрос

TV показывает:
- `final_show` mode

Действия:
1. Открыть финальный вопрос
2. Закрыть вопрос
3. Нажать `Host continue`
4. Перед финальным объявлением уточнить текущую сумму jackpot
5. После финала ведущий объявляет один из двух исходов:
   - `Счёт Дома покрыт`
   - `Джекпот переходит на следующую игру`

Если используется preview для репетиции или live-подсказки:
- открыть master/TV с query params:
  - `?jackpot_preview=won&jackpot_amount=45000`
  - `?jackpot_preview=carry_over&jackpot_amount=45000`

Проверка:
- после завершения финала сценарий должен уйти в terminal state

## Terminal

Что должно быть:

- сценарий завершён
- новых этапов нет
- stale `court` / `host_round` нет

## 5. Court MVP operator flow

Порядок работы:

1. `Generate bracket`
2. Убедиться, что пары появились на master и TV
3. `Start pair`
4. `Open question`
5. После ответа:
   - `Mark result`
6. Повторять:
   - `Open question`
   - `Mark result`
7. Когда пара закончена:
   - `Confirm pair winner`
8. Затем:
   - `Next pair`
9. После последней пары:
   - дождаться `court_finished`
10. Только после этого:
   - `Scenario advance`

Норма:

- master и TV оба в court mode
- `current_pair` есть, пока Суд не завершён
- после `court_finished`:
  - `current_pair = null`
  - `court_runtime.status = court_finished`

## 6. Финал

Порядок:

1. После `stage_court` нажать `Scenario advance`
2. Убедиться, что активен `stage_final_show`
3. `Open final question`
4. `Force close question`
5. `Host continue`
6. Перед объявлением результата уточнить сумму jackpot
7. Со сцены озвучить:
   - `счёт Дома покрыт`
   - или `джекпот переходит на следующую игру`
8. Если нужен preview нужного исхода, открыть master/TV с query params:
   - `?jackpot_preview=won&jackpot_amount=45000`
   - `?jackpot_preview=carry_over&jackpot_amount=45000`

Как понять, что всё завершилось правильно:

- `scenario_finished = true`
- `current_round = null`
- `active_host_round = null`
- `active_phases = []`

## 7. Быстрые признаки проблем

### Stale host_round

Признак:
- в UI нет вопроса, но `active_host_round` всё ещё висит

Проверить:
- `/dev/game-master/IRON01/state`
- `/dev/games/IRON01/scenario/director`

### Stale court scene

Признак:
- Суд уже закончен, а master или TV всё ещё показывают court как активный

Проверить:
- `/dev/court/state/IRON01`
- `court_runtime.status`

### TV не обновляется

Признак:
- state уже изменился, а экран зала остался старым

Проверить:
- `/dev/game-master/IRON01/tv-state`

### Phase зависла

Признак:
- director не двигается дальше
- старый stage не закрывается

Проверить:
- `active_system_stage_phase`
- `active_phases`

### Director не advance

Признак:
- `can_advance = false`, хотя этап должен быть завершён

Проверить:
- не остался ли `active_host_round`
- не остался ли `court` незавершённым

### Question не открывается

Признак:
- `Open next question` или `Open question` возвращает ошибку

Проверить:
- не активен ли уже текущий вопрос
- не забыли ли закрыть предыдущий

## 8. Минимальный recovery flow

### Что можно безопасно нажимать

- `Force close question`
- `Host continue`
- `Scenario advance` только когда этап реально завершён
- court actions:
  - `Generate bracket`
  - `Start pair`
  - `Open question`
  - `Mark result`
  - `Confirm pair winner`
  - `Next pair`

### Чего нельзя делать

- не жать `Scenario advance` посреди активного Court, если Суд не завершён
- не открывать новый вопрос, если предыдущий ещё active
- не пытаться “лечить” runtime руками через БД

### Когда НЕ жать advance

Не жать `advance`, если:

- active question ещё не закрыт
- court pair ещё не доведена до winner confirm
- `court_runtime.status` ещё не `court_finished`

### Если совсем сломалось

Без SQL:

1. Проверить `director`
2. Проверить `master-state`
3. Закрыть активный вопрос штатной кнопкой / POST
4. Завершить текущий раунд или фазу штатным путём
5. Только если тестовая комната и запуск можно повторить:
   - `reset-runtime`
   - `apply scenario`

## 9. Итоговый healthy terminal state

Норма в конце вечера:

- `scenario_finished = true`
- `active_phases = []`
- `active_host_round = null`
- `current_round = null`
