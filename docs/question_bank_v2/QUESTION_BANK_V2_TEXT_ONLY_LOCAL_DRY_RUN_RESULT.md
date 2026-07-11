# Question Bank V2: text-only local dry-run result

## 1. Summary

The first local non-LIVE dry-run for the Question Bank V2 text-only importer-compatible candidate completed successfully.

This was a local TestClient dry-run only. It did not run production, did not touch `LIVE01`, did not use write/import mode, and did not mutate the database.

## 2. Baseline and candidate

Relevant commits:

```text
7621183 Add question bank v2 local dry-run command plan
57564f2 Add question bank v2 import-compatible text-only candidate
```

Candidate file:

```text
docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate.xlsx
```

Endpoint exercised locally:

```text
/dev/questions/import
```

Execution method:

```text
local FastAPI TestClient
```

## 3. Dry-run parameters

```text
dry_run=true
clear_existing=false
target_round_code=QUESTION_DRYRUN_01
true_false_limit=13
single_choice_limit=8
free_text_limit=0
media_limit=0
prefer_media=false
```

Safety meaning:

- `dry_run=true` returns preview before DB write path;
- `clear_existing=false` does not request deletion/clearing;
- `media_limit=0` keeps this text-only;
- `QUESTION_DRYRUN_01` is a non-LIVE dry-run target marker.

## 4. Parser verification before dry-run

```text
PARSE_PARSED_COUNT 21
PARSE_PREVIEW_COUNT 21
PARSE_SECTIONS {'true_false': 13, 'single_choice': 8, 'free_text': 0}
PARSE_ERROR_COUNT 0
PARSE_MEDIA_REFS_NONEMPTY []
```

## 5. Dry-run HTTP/TestClient result

```text
HTTP_STATUS 200
CONTENT_TYPE application/json
RESPONSE_OK True
RESPONSE_SOURCE_TYPE xlsx
RESPONSE_FILENAME question_bank_v2_text_only_import_compatible_candidate.xlsx
RESPONSE_TARGET_ROUND_CODE QUESTION_DRYRUN_01
RESPONSE_DRY_RUN True
RESPONSE_MEDIA_LIMIT 0
RESPONSE_PREFER_MEDIA False
RESPONSE_QUESTIONS_COUNT 21
RESPONSE_SECTIONS {'true_false': 13, 'single_choice': 8, 'free_text': 0}
SELECTED_COUNT 21
SELECTED_BY_TYPE {'true_false': 13, 'single_choice': 8, 'free_text': 0}
SELECTED_MEDIA_COUNT 0
RESPONSE_ERROR_COUNT 0
SELECTED_ERROR_COUNT 0
RESPONSE_MEDIA_REFS_NONEMPTY []
SELECTED_TYPES {'single_choice': 8, 'true_false': 13}
ASSERTIONS_PASSED True
DB_WRITE_EXPECTED False
```

## 6. Result interpretation

The candidate XLSX is compatible with the current importer parser for a text-only preview dry-run.

Confirmed:

- 21 rows parsed;
- 21 rows selected;
- 13 true/false rows;
- 8 single-choice rows;
- 0 free-text rows;
- 0 media rows;
- 0 parser errors;
- 0 selected-row errors;
- no media refs;
- dry-run returned preview JSON successfully.

## 7. Warning observed

The compile precheck:

```powershell
python -m py_compile app\routes\dev.py app\services\question_import_service.py
```

hit a local pycache write/rename issue:

```text
[WinError 5] Access is denied: app\routes\__pycache__\dev.cpython-311.pyc... -> app\routes\__pycache__\dev.cpython-311.pyc
```

Interpretation:

- treat this as a local filesystem / `__pycache__` permission issue;
- not treated as a syntax/import blocker;
- modules loaded successfully immediately afterward;
- TestClient dry-run passed all assertions.

## 8. Explicit non-actions

No production action happened.

No `LIVE01` touch happened.

No write/import mode was used:

```text
dry_run=false was not used
```

No destructive clearing was used:

```text
clear_existing=true was not used
```

Also not performed:

- no DB mutation;
- no media copy;
- no deploy;
- no migrations;
- no runtime/template/route changes;
- no commit during dry-run.

Final git status after dry-run was clean.

## 9. Remaining decisions before any write/import mode

Do not proceed to write/import mode without a separate explicit approval.

Before any future non-dry-run import, decide:

1. exact non-LIVE target room/round;
2. whether to create DB rows from this text-only set;
3. rollback/cleanup plan;
4. whether to keep `clear_existing=false`;
5. whether to run a DB snapshot/backup first;
6. whether visual/media rows remain excluded.

## 10. Recommended next step

Commit this result checkpoint.

Then choose one of:

1. prepare a non-LIVE write/import runbook, still not executed;
2. keep this as dry-run-only evidence and move to visual/media prep;
3. review the 21 selected questions editorially before any DB write.
