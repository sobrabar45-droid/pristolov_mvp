# Question Bank V2: corrected local dry-run с multipart form fields

## 1. Summary

Исправленный local non-LIVE dry-run V2 успешно пройден после перехода с query-параметров на multipart form fields.

- `HTTP_STATUS 200`
- `RESPONSE_OK True`
- `RESPONSE_TARGET_ROUND_CODE QUESTION_DRYRUN_02`
- `RESPONSE_DRY_RUN True`
- выбрано `19` вопросов;
- ошибок ответа `0`;
- ошибок выбранных вопросов `0`;
- запись в DB не ожидалась.

Это только evidence checkpoint, не разрешение на write/import.

## 2. Input and execution

- Baseline: `b3b58f2 Correct question bank v2 dry-run form fields`.
- Runbook: `docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_LOCAL_DRY_RUN_COMMAND_PLAN.md`.
- Candidate: `docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`.
- Endpoint: `/dev/questions/import`.
- Execution: local TestClient only.
- Передача параметров: multipart `data={...}` / form fields.

## 3. Parameters

- `target_round_code=QUESTION_DRYRUN_02`
- `dry_run=true`
- `clear_existing=false`
- `true_false_limit=13`
- `single_choice_limit=6`
- `free_text_limit=0`
- `media_limit=0`
- `prefer_media=false`

## 4. Response

```text
HTTP_STATUS 200
CONTENT_TYPE application/json
RESPONSE_OK True
RESPONSE_SOURCE_TYPE xlsx
RESPONSE_FILENAME question_bank_v2_text_only_import_compatible_candidate_v2.xlsx
RESPONSE_TARGET_ROUND_CODE QUESTION_DRYRUN_02
RESPONSE_DRY_RUN True
RESPONSE_MEDIA_LIMIT 0
RESPONSE_PREFER_MEDIA False
RESPONSE_QUESTIONS_COUNT 19
RESPONSE_SECTIONS {'true_false': 13, 'single_choice': 6, 'free_text': 0}
SELECTED_COUNT 19
SELECTED_BY_TYPE {'true_false': 13, 'single_choice': 6, 'free_text': 0}
SELECTED_MEDIA_COUNT 0
RESPONSE_ERROR_COUNT 0
SELECTED_ERROR_COUNT 0
ASSERTIONS_PASSED True
DB_WRITE_EXPECTED False
```

Ключевое исправление подтверждено: response получил именно `QUESTION_DRYRUN_02`, а не default `imported_warmup_test`.

## 5. Safety and non-actions

- Working tree во время запуска оставался clean.
- `dry_run=false` не использовался.
- `clear_existing=true` не использовался.
- DB write не выполнялся.
- Production не затрагивался.
- `LIVE01` не затрагивался.
- Media не копировались.
- Deploy и migrations не выполнялись.
- Runtime changes не выполнялись.
- Write/import режим не запускался.

## 6. Next decision

V2 text-only candidate теперь имеет подтверждённый local dry-run с корректной передачей target round form field. Любой write/import остаётся отдельной задачей с явным одобрением, non-LIVE target и отдельным safety runbook.
