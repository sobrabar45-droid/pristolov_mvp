# Question Bank V2: audit обработки `target_round_code`

## 1. Scope and safety

Это read-only audit текущей обработки параметров endpoint `/dev/questions/import`.

- Endpoint не вызывался в рамках этого аудита.
- Import не выполнялся.
- XLSX, runtime, routes, templates, DB и media не изменялись.
- Production и `LIVE01` не затрагивались.

## 2. Route definition

Endpoint определён в `app/routes/dev.py`:

```python
@router.post("/questions/import")
async def import_questions_preview(
    file: UploadFile = File(...),
    dry_run: str = Form("true"),
    target_round_code: str = Form("imported_warmup_test"),
    true_false_limit: int = Form(5),
    single_choice_limit: int = Form(5),
    free_text_limit: int = Form(3),
    media_limit: int = Form(0),
    prefer_media: str = Form("false"),
    clear_existing: str = Form("false"),
):
```

Точный параметр для target round: `target_round_code`.

Параметр принимается как multipart form field через `Form(...)`, а не как query parameter.

## 3. Default behavior

Если поле не передано в форме, передано пустым или после очистки пусто, код нормализует значение к:

```text
imported_warmup_test
```

Фактическая логика:

```python
target_round_code = (target_round_code or "imported_warmup_test").strip() or "imported_warmup_test"
```

Это значение затем записывается в preview response как `target_round_code`. В write mode оно также используется для поиска/создания `RoundTemplate` и формирования `import_key`.

## 4. Why the previous dry-run returned the default

Предыдущий локальный TestClient-вызов передал параметры через `params={...}`. Это отправляет значения в query string.

Но endpoint объявляет `dry_run`, `target_round_code`, limits, `prefer_media` и `clear_existing` через `Form(...)`. Query-параметры для этих аргументов не являются источником значений функции.

Поэтому переданный query value:

```text
QUESTION_DRYRUN_02
```

не попал в аргумент endpoint, и response вернул default:

```text
imported_warmup_test
```

Это не означает, что endpoint игнорирует `target_round_code`. Он принимает его, если передать правильным способом.

## 5. Room code boundary

В сигнатуре `/questions/import` нет параметра `room_code`. Endpoint работает с импортируемым `RoundTemplate`, а не с room/session code.

Следовательно:

- `QUESTION_DRYRUN_02` в предыдущем вызове был только внешним обозначением теста;
- он не был принят endpoint как room code;
- его нельзя считать target room или DB room isolation mechanism;
- room/non-LIVE safety должна контролироваться отдельно операторским runbook и локальным окружением.

## 6. Correct future parameter set

Для будущего local non-LIVE dry-run параметры должны передаваться как multipart form fields:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/dev/questions/import" ^
  -H "X-Admin-Token: <LOCAL_DEV_ADMIN_TOKEN>" ^
  -F "dry_run=true" ^
  -F "target_round_code=QUESTION_DRYRUN_02" ^
  -F "true_false_limit=13" ^
  -F "single_choice_limit=6" ^
  -F "free_text_limit=0" ^
  -F "media_limit=0" ^
  -F "prefer_media=false" ^
  -F "clear_existing=false" ^
  -F "file=@docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx"
```

Это только command template. В рамках текущего аудита он не выполнялся.

Для TestClient аналогично нужно передавать значения в `data={...}`, а не в `params={...}`:

```python
client.post(
    "/dev/questions/import",
    data={"target_round_code": "QUESTION_DRYRUN_02", "dry_run": "true"},
    files={"file": (...)},
)
```

## 7. Correctness and safety rules

Перед будущим dry-run нужно проверить response:

- `dry_run=True`;
- `target_round_code=QUESTION_DRYRUN_02` или другое явно утверждённое значение;
- `clear_existing` не используется как `true`;
- выбранное количество и типы вопросов ожидаемы;
- нет parser errors.

Для write/import эти же параметры нельзя считать достаточными сами по себе: потребуется отдельное явное одобрение, non-LIVE target, backup/rollback plan и отдельный runbook.

## 8. Conclusion

Причина расхождения — correction command plan, а не runtime bug: значения передавались в query string вместо form fields. Code change не требуется.

Нужна только корректировка будущего command plan и, если потребуется, отдельный read-only verification правильной multipart-передачи. До этого write/import не рекомендуется.
