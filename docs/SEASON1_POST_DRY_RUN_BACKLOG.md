# Season 1 Post Dry-Run Backlog

## 1. P0 — ломает live-flow

### Wrong scene priority

- Symptom:
  - активный runtime есть, но master или TV показывают не ту сцену;
  - финал, Суд или системная фаза могут быть визуально перекрыты обычным question scene.
- Где проявилось:
  - Court MVP;
  - final_show;
  - переходы между phase и host_round.
- Почему опасно:
  - ведущий теряет доверие к пульту;
  - зал видит не ту стадию шоу;
  - live-flow визуально разваливается.
- Expected behavior:
  - Court scene имеет приоритет над stale host_round;
  - final_show имеет приоритет над generic question view;
  - завершённые сцены не перетягивают фокус назад.
- Какие файлы вероятно затронуть:
  - [D:\Projects\pristolov_mvp\app\templates\master_screen.html](D:/Projects/pristolov_mvp/app/templates/master_screen.html)
  - [D:\Projects\pristolov_mvp\app\templates\tv_mode_tv_state.html](D:/Projects/pristolov_mvp/app/templates/tv_mode_tv_state.html)
  - [D:\Projects\pristolov_mvp\app\services\master_state_service.py](D:/Projects/pristolov_mvp/app/services/master_state_service.py)
- Критерий готовности:
  - на каждом этапе master и TV показывают только актуальную сцену;
  - stale scene не возвращается после перехода.

### Scene cleanup issues

- Symptom:
  - после завершения этапа остаётся старый envelope: `host_round`, `court`, `crest` или другой scene-shell.
- Где проявилось:
  - terminal cleanup после final_show;
  - ранее — после Court MVP.
- Почему опасно:
  - director уже ушёл дальше, а UI визуально застрял в прошлом этапе;
  - ведущий может нажать не ту кнопку.
- Expected behavior:
  - после завершения этапа закрываются phase и host_round оболочки;
  - master и TV переходят в новый state без хвостов.
- Какие файлы вероятно затронуть:
  - [D:\Projects\pristolov_mvp\app\routes\dev.py](D:/Projects/pristolov_mvp/app/routes/dev.py)
  - [D:\Projects\pristolov_mvp\app\services\scenario_service.py](D:/Projects/pristolov_mvp/app/services/scenario_service.py)
  - [D:\Projects\pristolov_mvp\app\services\master_state_service.py](D:/Projects/pristolov_mvp/app/services/master_state_service.py)
- Критерий готовности:
  - после переходов `court -> final_show` и `final_show -> terminal` не остаётся stale scene;
  - `active_phases = []` в terminal.

### Stale crest scene during court

- Symptom:
  - во время Суда может всплывать след предыдущей crest-сцены или другого системного этапа.
- Где проявилось:
  - переход из system stages в Court MVP.
- Почему опасно:
  - шоу-слой теряет ясность;
  - зал получает смешанный сигнал о текущем этапе.
- Expected behavior:
  - при старте Court TV и master переходят в чистый court mode без следов crest.
- Какие файлы вероятно затронуть:
  - [D:\Projects\pristolov_mvp\app\templates\tv_mode_tv_state.html](D:/Projects/pristolov_mvp/app/templates/tv_mode_tv_state.html)
  - [D:\Projects\pristolov_mvp\app\templates\master_screen.html](D:/Projects/pristolov_mvp/app/templates/master_screen.html)
  - [D:\Projects\pristolov_mvp\app\services\master_state_service.py](D:/Projects/pristolov_mvp/app/services/master_state_service.py)
- Критерий готовности:
  - при входе в Суд crest scene не виден ни на master, ни на TV.

### Final question not rendered

- Symptom:
  - финальная сцена или финальный вопрос не отображаются ожидаемым образом.
- Где проявилось:
  - `stage_final_show`.
- Почему опасно:
  - кульминация вечера превращается в технический сбой;
  - ведущий теряет финальный ритм.
- Expected behavior:
  - master показывает final scene;
  - TV показывает `final_show` mode;
  - финальный вопрос рендерится без ошибок.
- Какие файлы вероятно затронуть:
  - [D:\Projects\pristolov_mvp\app\templates\master_screen.html](D:/Projects/pristolov_mvp/app/templates/master_screen.html)
  - [D:\Projects\pristolov_mvp\app\templates\tv_mode_tv_state.html](D:/Projects/pristolov_mvp/app/templates/tv_mode_tv_state.html)
- Критерий готовности:
  - final question и final scene стабильно видны при повторном GUI-smoke.

### Unicode / encoding issue on TV

- Symptom:
  - на TV вопросы или подписи отображаются кракозябрами.
- Где проявилось:
  - imported question text;
  - отдельные TV text blocks.
- Почему опасно:
  - зал не может прочитать вопрос;
  - весь show-layer визуально ломается.
- Expected behavior:
  - кириллица и смешанные тексты на TV отображаются стабильно.
- Какие файлы вероятно затронуть:
  - [D:\Projects\pristolov_mvp\app\templates\tv_mode_tv_state.html](D:/Projects/pristolov_mvp/app/templates/tv_mode_tv_state.html)
  - question import source files в [D:\Projects\pristolov_mvp\docs\question_import_templates](D:/Projects/pristolov_mvp/docs/question_import_templates)
  - возможные import utilities, если баг подтвердится
- Критерий готовности:
  - на реальных court/final вопросах TV не показывает битую кодировку.

## 2. P1 — мешает вести игру

### Непонятная сборка герба

- Что видит игрок:
  - тематический этап без ясной практической ценности.
- Что должен понять:
  - герб — это лицо Дома и часть политической идентичности.
- Минимальное решение:
  - короткое master/TV объяснение, зачем герб важен;
  - 1 ясная выгода или символический результат.
- Полноценное решение позже:
  - связать герб с дальнейшими бонусами, статусом и TV-reveal.

### Неочевидная дипломатия

- Что видит игрок:
  - есть сделки, но неясно, почему именно сейчас надо договариваться.
- Что должен понять:
  - дипломатия — это способ изменить шансы Дома до следующего конфликта.
- Минимальное решение:
  - добавить framing через речь ведущего и TV-callout;
  - явно показать, что можно выиграть или потерять.
- Полноценное решение позже:
  - ввести pressure windows, ограниченные возможности и видимые последствия союзов.

### Ресурсы не объясняют себя

- Что видит игрок:
  - цифры и иконки без сильной связи с выборами.
- Что должен понять:
  - ресурсы — это не фон, а инструмент давления и усиления.
- Минимальное решение:
  - дать краткие объяснения на этапе и в reveal;
  - показать хотя бы 1-2 понятных spending/use case.
- Полноценное решение позже:
  - построить вокруг ресурсов устойчивый decision loop.

### Золото не имеет явного spending loop

- Что видит игрок:
  - счётчик золота.
- Что должен понять:
  - золото можно тратить ради преимуществ, а не только копить.
- Минимальное решение:
  - ввести один явный момент траты перед Court или Final.
- Полноценное решение позже:
  - полноценная экономическая петля с выбором, риском и обменом.

### Нет экрана “последний заказ перед судом”

- Что видит игрок:
  - переход в Суд без сильного bridge-экрана.
- Что должен понять:
  - это последний шанс усилиться, купить, договориться, рискнуть.
- Минимальное решение:
  - отдельный TV/master bridge screen перед `stage_court`.
- Полноценное решение позже:
  - мини-фаза последнего экономического окна перед Судом.

### Финал не фиксирует приз / джекпот

- Что видит игрок:
  - финальная сцена есть, но не всегда ясно, что именно выиграл Дом.
- Что должен понять:
  - финал завершает вечер и фиксирует награду/приз/статус победителя.
- Минимальное решение:
  - добавить явную формулировку приза или титула победителя на master/TV.
- Полноценное решение позже:
  - встроить джекпот, награду или финальное распределение престижа в шоу-сцену.

## 3. P2 — продуктовые усиления

### Грязная политика

- Зачем нужно:
  - даёт выход для интриги, саботажа и скрытого давления.
- Что даст игре:
  - усилит роль мастера над шёпотом и добавит социальную напряжённость.
- Почему не делать всё сразу:
  - сначала нужно закрепить базовый live-loop без новых скрытых систем.

### Последние сделки

- Зачем нужно:
  - создаёт предфинальное окно решений и нервозность.
- Что даст игре:
  - усилит чувство “ещё можно перевернуть расклад”.
- Почему не делать всё сразу:
  - без понятной дипломатии такой этап станет просто лишней паузой.

### Великая битва

- Зачем нужно:
  - нужна общая кульминация перед финалом.
- Что даст игре:
  - переведёт вечер от набора этапов к ощущению большого showdown.
- Почему не делать всё сразу:
  - сначала нужно понять, где лучшее место для общей кульминации относительно Суда и Финала.

### Усиление домов / башня

- Зачем нужно:
  - даёт долгую арку роста Дома.
- Что даст игре:
  - усиливает накопление, стратегию и House identity.
- Почему не делать всё сразу:
  - без понятной экономики механика усиления будет декоративной.

### Рынок / скрытые действия

- Зачем нужно:
  - добавляет риск, тайные решения и асимметрию.
- Что даст игре:
  - повышает replayability и глубину переговоров.
- Почему не делать всё сразу:
  - легко перегрузить MVP лишними кнопками и правилами.

## 3.1. Final Jackpot Clarity Update

- Что уже сделано:
  - master показывает final jackpot outcome;
  - TV показывает final jackpot outcome;
  - поддержаны preview query params:
    - `jackpot_preview=won`
    - `jackpot_preview=carry_over`
    - `jackpot_amount=45000`
  - terminal state остаётся clean;
  - `final_show` удерживается на TV после `scenario_finished`.
- Что остаётся pending:
  - настоящая сумма jackpot не хранится как persisted runtime/business data;
  - outcome `won / carry_over` пока не фиксируется через backend;
  - ведущий и оператор должны проговорить и подтвердить outcome вручную.
- Будущая задача `P1/P2 — Persisted Jackpot Decision`:
  - откуда берётся `jackpot amount`;
  - кто подтверждает `won / carry_over`;
  - где хранится outcome;
  - как это влияет на следующую игру.

## 3.2. Lord Dashboard MVP Update

- Что уже сделано:
  - `Lord Dashboard MVP` создан;
  - Лорд больше не застревает в `delegation setup`;
  - появился экран Дома:
    - `/house/{invite_code}`
  - на экране Дома видны:
    - состав;
    - роли;
    - золото;
    - влияние;
    - текущий этап;
  - есть invite link для поздних игроков;
  - есть кнопка возврата из `player screen` Лорда;
  - `late join` стал понятнее и операционно проще.

- Что остаётся pending:
  - `ready-state` пока хранится в `localStorage`, а не в backend;
  - QR для присоединения Дома пока не отдельная картинка;
  - `opportunities` пока informational, а не action buttons;
  - нет persisted `House Ready` для `master / TV`;
  - нет полноценного `Lord command center` для экспедиций, дуэлей и союзов.

- Следующая задача:
  - `House Ready + QR invite flow`
  - нужно добавить:
    - persisted ready status;
    - QR join link на экране Лорда;
    - видимость готовности Домов на master;
    - счётчик готовности вида `готово X/Y Домов` на TV.

## 4. Immediate Next Codex Tasks

1. `P0 scene priority cleanup`
   - проверить и зачистить приоритет сцен на master/TV при переходах `system_stage -> court -> final -> terminal`.
2. `P0 final question render check`
   - повторно прогнать финальный GUI-smoke и убедиться, что финальный вопрос не выпадает ни на master, ни на TV.
3. `P0 TV unicode check`
   - проверить реальные импортированные вопросы на TV, особенно court/final тексты.
4. `P1/P2 persisted jackpot decision`
   - определить источник `jackpot amount`, момент подтверждения `won / carry_over`, storage outcome и связь со следующей игрой.
5. `P1 pre-court order cutoff screen`
   - добавить bridge-screen перед Судом: последний шанс купить, договориться, усилиться.
6. `P1 crest explanation/narration`
   - добавить ясное объяснение смысла герба и его эмоционального веса.
7. `P1 House Ready + QR invite flow`
   - вынести ready status из local UI в persisted state;
   - показать QR / join link на экране Лорда;
   - отдать готовность Домов в master / TV.
8. Потом только `product mechanics`
   - грязная политика;
   - последние сделки;
   - великая битва;
   - рынок и скрытые действия;
   - усиление домов.

## 5. Что заморозить

- `Court MVP runtime`
- `scenario director architecture`
- `host_round pipeline`
- `stage_court_battle` как question bank
- existing terminal flow

Заморозка означает:
- не перепридумывать архитектуру;
- не трогать стабильные P0-участки без нового фактического бага;
- расширять продукт через additive задачи.
