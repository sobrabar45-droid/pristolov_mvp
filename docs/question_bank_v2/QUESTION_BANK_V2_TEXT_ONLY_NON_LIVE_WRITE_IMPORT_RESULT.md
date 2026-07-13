# Question Bank V2: controlled local non-LIVE write/import result

## 1. Executive summary

The controlled local non-LIVE write/import completed successfully.

- Imported `19` text-only questions.
- Target round code: `QUESTION_DRYRUN_02`.
- Imported media: `0`.
- Production was not touched.
- `LIVE01` was not touched.

This document is an evidence checkpoint for the completed local/test DB action. It is not approval for production import or another write.

## 2. Input artifact

- Candidate XLSX: `docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`.
- Runbook: `docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_NON_LIVE_WRITE_IMPORT_RUNBOOK.md`.
- Baseline commit before write/import: `4ef489b Add question bank v2 non-live import runbook`.
- Local DB: PostgreSQL at `localhost:5432/pristolov_mvp`.

## 3. Pre-write safety

Parser verification:

```text
PARSED_COUNT 19
ERROR_COUNT 0
TYPE_COUNTS {'true_false': 13, 'single_choice': 6}
MEDIA_COUNT 0
```

Repeated multipart dry-run immediately before write:

```text
DRY_HTTP 200
DRY_OK True
DRY_MODE True
DRY_TARGET QUESTION_DRYRUN_02
DRY_SELECTED 19
DRY_BY_TYPE {'true_false': 13, 'single_choice': 6, 'free_text': 0}
DRY_MEDIA 0
DRY_ERRORS 0
DRY_ASSERT True
```

Victor explicitly approved the controlled local non-LIVE write/import.

`pg_dump` was unavailable. A targeted logical pre-write checkpoint was created at:

```text
C:\Users\sobra\AppData\Local\Temp\pristolov_question_dryrun_02_prewrite_20260713_143119.json
```

State before write:

```text
PRE_ROUND_COUNT 0
PRE_QUESTION_COUNT 0
```

## 4. Write/import response

The endpoint was called locally through FastAPI TestClient with multipart `data={...}` fields:

- `dry_run=false`;
- `clear_existing=false`;
- `target_round_code=QUESTION_DRYRUN_02`;
- limits `13 / 6 / 0`;
- `media_limit=0`;
- `prefer_media=false`;
- no token was exposed or logged.

Response:

```text
WRITE_HTTP 200
WRITE_OK True
WRITE_DRY_RUN False
WRITE_TARGET QUESTION_DRYRUN_02
WRITE_IMPORTED_COUNT 19
WRITE_BY_TYPE {'true_false': 13, 'single_choice': 6, 'free_text': 0}
WRITE_CREATED_CODES_COUNT 19
WRITE_MESSAGE None
WRITE_ASSERT True
```

## 5. DB confirmation

- Created round template ID: `74`.
- `questions_total=19`.
- Persisted question rows: `19`.
- Unique question codes: `19`.
- Sequence range: `1-19`.
- Media refs: none.
- `POST_DB_ASSERT True`.

Internal answer-mode mapping:

- `13` true/false source rows stored with `answer_mode=single_choice`;
- `6` single-choice source rows stored with `answer_mode=single`.

## 6. Post-write smoke

Read-only local GET checks:

```text
MASTER /dev/master-screen/TEST_ROOM_SETUP 200 text/html; charset=utf-8
TV /dev/tv-mode/TEST_ROOM_SETUP 200 text/html; charset=utf-8
PLAYER /house/204B48/player/955 200 text/html; charset=utf-8
```

## 7. Warnings

- `pg_dump` was not available in the local environment.
- A targeted logical checkpoint was used instead of a full PostgreSQL dump.
- The target round did not exist before write: `0` rounds and `0` questions.
- `clear_existing=false` was used.
- Because the target was absent and clear mode was disabled, no existing target rows could have been cleared.

## 8. Safety confirmation

- Production was not touched.
- `LIVE01` was not touched.
- Media was not copied.
- Deploy, migrations, and restart were not performed.
- Runtime, routes, templates, and XLSX files were not changed.
- The write/import was local and non-LIVE only.
- Final git status after execution was clean.
- No commit was made during execution.

## 9. Next recommended step

1. Run a non-LIVE screen/content smoke for the imported text-only round.
2. Prepare a separate checklist for a `10-15` participant local load-smoke.
3. Do not repeat write/import or move to production without a separate explicit decision.
