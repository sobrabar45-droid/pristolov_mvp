# Question Bank V2: результат локального text-only dry-run V2

## 1. Executive summary

Локальный non-LIVE dry-run для исправленного Question Bank V2 успешно пройден.

- Выбрано `19` вопросов.
- Ошибок ответа нет: `0`.
- Использованы `dry_run=true` и `clear_existing=false`.
- Запись в DB не ожидалась.
- Production и `LIVE01` не затрагивались.

Это только evidence checkpoint. Результат не является разрешением на write/import.

## 2. Input artifact

- Candidate V2: `docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`.
- Candidate report: `docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_IMPORT_COMPATIBLE_CANDIDATE_V2_REPORT.md`.
- В V2 исправлена русская кодировка: visible question/answer/option/explanation fields проверены, `MOJIBAKE_COUNT 0`.
- Состав V2: `13` вопросов `true_false` и `6` вопросов `single_choice`.

## 3. Dry-run parameters

- Endpoint: `/dev/questions/import`.
- Режим: local non-LIVE dry-run.
- Candidate: `question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`.
- `dry_run=true`.
- `clear_existing=false`.
- Room: `QUESTION_DRYRUN_02`.
- `true_false_limit=13`.
- `single_choice_limit=6`.
- `free_text_limit=0`.
- `media_limit=0`.
- `prefer_media=false`.

## 4. Response summary

```text
HTTP_STATUS 200
RESPONSE_OK True
RESPONSE_DRY_RUN True
RESPONSE_QUESTIONS_COUNT 19
SELECTED_COUNT 19
SELECTED_BY_TYPE {'true_false': 13, 'single_choice': 6}
SELECTED_MEDIA_COUNT 0
RESPONSE_ERROR_COUNT 0
SELECTED_ERROR_COUNT 0
ASSERTIONS_PASSED True
DB_WRITE_EXPECTED False
```

## 5. Warning and follow-up blocker

В ответе endpoint вернул:

```text
RESPONSE_TARGET_ROUND_CODE imported_warmup_test
```

Ожидалось значение:

```text
QUESTION_DRYRUN_02
```

Похоже, переданный `target_round_code` был проигнорирован, и endpoint использовал значение по умолчанию `imported_warmup_test`. Это не повлияло на текущий dry-run: он вернул `200`, `19` выбранных вопросов и `0` ошибок.

Тем не менее это blocker перед любым write/import runbook. Сначала нужен отдельный read-only audit обработки `target_round_code` и фактического имени параметра. До понимания поведения write/import не рекомендуется.

## 6. Safety confirmation

- Production не затрагивался.
- `LIVE01` не затрагивался.
- `dry_run=false` не использовался.
- `clear_existing=true` не использовался.
- DB write не выполнялся.
- Media не копировались.
- Deploy, migrations и restart не выполнялись.
- Endpoint повторно не вызывался в рамках создания этого отчёта.
- Финальный git status после dry-run был clean.

## 7. Next decision

Допустимые следующие варианты:

1. Остановиться на этом V2 dry-run checkpoint.
2. Провести read-only audit обработки `target_round_code`.
3. Подготовить visual/media track отдельно.

Write/import не планировать до того, как поведение `target_round_code` будет понято и зафиксировано отдельным безопасным runbook.
