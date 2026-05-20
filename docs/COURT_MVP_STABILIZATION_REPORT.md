# COURT MVP Stabilization Report

## Статус checkpoint

- Court MVP проходит полный цикл до `court_finished`.
- `master-screen` и `TV court mode` не зависают после завершения Суда.
- stale `stage_court_battle` больше не управляет `master-state` после завершения суда.
- `scenario/advance` после `court_finished` работает корректно.
- после `advance` сценарий переходит на `stage_final_show`.

## Найденный и исправленный баг

### Симптом

После завершения Суда scenario director не всегда выходил из `stage_court` корректно:

- `court_runtime` уже был `court_finished`;
- но director мог терять активный `stage_court` как system-stage;
- `next_round` снова выглядел как `stage_court` вместо перехода дальше.

### Причина

В `generate_court_bracket_logic(...)` court payload пересобирался через `_default_court_payload()`.

Из-за этого из `GamePhase.payload` терялась сценарная metadata:

- `scenario_id`
- `scenario_code`
- `round_template_id`

Именно по этой metadata director связывает активную `court` phase с текущим этапом сценария.

### Исправление

Вместо:

```python
payload = _default_court_payload()
```

используется:

```python
payload = _normalize_court_payload(phase.payload)
```

Это сохраняет сценарную привязку phase и не ломает Court runtime.

## Что подтверждено после фикса

- `stage_court` остаётся текущим этапом, пока Court реально не завершён.
- после `court_finished` director разрешает `scenario/advance`.
- `scenario/advance` закрывает `court` phase штатно.
- следующий этап после `stage_court` — `stage_final_show`.
- после перехода:
  - `court_runtime = null` в `master-state`
  - `court_runtime = null` в `tv-state`
  - активным становится только `stage_final_show`

## Update: question bank expanded

- `stage_court_battle` расширен до **45 уникальных вопросов**.
- source-of-truth файл импорта:
  - `docs/question_import_templates/stage_court_battle_45.xlsx`
- подтверждённая разбивка:
  - `15` `true_false`
  - `20` `single_choice`
  - `10` `free_text`
- результат штатного импорта:
  - `imported_count = 45`
- runtime-проверка:
  - `35` открытий court-вопросов прошли без `court_question_bank_exhausted`
  - `used_questions_count = 35`
  - warnings отсутствуют
- полный Court MVP после пополнения банка снова проходит до `court_finished`
- `scenario/advance` после завершения Суда переводит сценарий на `stage_final_show`

## Audit: stage_court_battle question bank

### Фактический размер банка

После пополнения в `stage_court_battle` реально доступно **45 уникальных вопросов**.

Баланс типов:

- `15` `true_false`
- `20` `single_choice`
- `10` `free_text`

Старое ядро из 13 вопросов сохранено:

1. `import_true_false_001`
2. `import_true_false_002`
3. `import_true_false_003`
4. `import_true_false_004`
5. `import_true_false_005`
6. `import_single_choice_026`
7. `import_single_choice_027`
8. `import_single_choice_028`
9. `import_single_choice_029`
10. `import_single_choice_030`
11. `import_free_text_051`
12. `import_free_text_052`
13. `import_free_text_053`

### Максимальная потребность в вопросах

Текущая боевая логика Суда:

- в каждой паре старт `4 vs 4`
- каждый вопрос всегда выбивает ровно одного игрока
- значит одна пара гарантированно завершается максимум за **7 вопросов**

Следовательно:

| Домов | Пар | Bye | Максимум вопросов |
|---|---:|---:|---:|
| 8 | 4 | 0 | 28 |
| 9 | 4 | 1 | 28 |
| 10 | 5 | 0 | 35 |

### Важное наблюдение

При текущей backend-логике `extra question / sudden death` почти не нужен как математическая необходимость:

- на каждом вопросе уходит один боец;
- при старте `4 vs 4` к 7-му вопросу одна из сторон уже должна остаться без бойцов.

То есть для текущей реализации верхняя граница одной пары — **7 вопросов**.

## Риск exhaustion

После пополнения банка до 45 вопросов риск exhaustion для MVP-прогона снят.

Подтверждено runtime-проверкой:

- `35` открытий court-вопросов прошли без повторов
- `court_question_bank_exhausted` не появлялся
- `used_questions_count = 35`
- warnings отсутствуют

## Рекомендованный минимум question bank

Минимально безопасный размер банка без повторов:

- **35 уникальных вопросов**

Практический рекомендуемый запас:

- **40–45 вопросов**

Текущий банк в 45 вопросов этот запас уже покрывает.

## Update: Final Show and terminal flow

- `stage_final_show` проверен после Court MVP.
- Финал работает как `host_round final`, но отображается как отдельная final scene.
- `master-screen` показывает финальную сцену, а не generic question scene.
- `tv-mode` показывает `final_show` mode.
- stale `court_runtime` после перехода в финал отсутствует.

### Подтверждённый terminal state

- `scenario_finished = true`
- `active_host_round = null`
- `current_round = null`
- `can_start_next = false`
- `can_advance = false`

### Final GUI-smoke

- Финальный GUI-smoke пройден.
- Активный финал:
  - `tmp/gui_smoke/master_final_show_fixed.png`
  - `tmp/gui_smoke/tv_final_show_fixed.png`
- Terminal state:
  - `tmp/gui_smoke/master_scenario_finished.png`
  - `tmp/gui_smoke/tv_scenario_finished.png`

- После завершения final host round `scenario/advance` корректно доводит сценарий до terminal state.

## Итог

Court MVP сейчас стабилизирован по runtime-выходу:

- Court доходит до `court_finished`;
- master/TV не зависают;
- stale `stage_court_battle` подавлен;
- переход сценария после Суда работает;
- `scenario/advance` ведёт на `stage_final_show`.

После пополнения `stage_court_battle` до `45` вопросов Court MVP закрывает и runtime-P0, и content-P0:

- банк вопросов достаточен для live-прогона без exhaustion;
- полный Суд проходит штатно;
- сценарий после Суда продолжается корректно.

Финальный блок вечера тоже подтверждён:

- `stage_final_show` визуально отличается от обычного question-round;
- master показывает финальную сцену;
- TV показывает отдельный `final_show` mode;
- terminal state сценария чистый.

## P0 status

P0 по Court MVP считается **закрытым**.
