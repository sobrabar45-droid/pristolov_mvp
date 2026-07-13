# Question Bank V2: text-only local dry-run command plan

Purpose: define an exact safe runbook for a future local non-LIVE dry-run of the importer-compatible Question Bank V2 text-only candidate.

This document is a plan only. The import endpoint is not called in this task.

## 1. Candidate artifact

Importer-compatible candidate:

```text
docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx
```

Companion report:

```text
docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_IMPORT_COMPATIBLE_CANDIDATE_V2_REPORT.md
```

Known parser verification:

```text
PARSED_COUNT 19
ERROR_COUNT 0
TYPE_COUNTS {'single_choice': 6, 'true_false': 13}
MEDIA_REFS_NONEMPTY []
```

## 2. Hard safety rules

Do not run this plan unless Victor explicitly approves the local dry-run.

Required constraints:

- local environment only;
- non-LIVE room only;
- `dry_run=true`;
- `clear_existing=false`;
- no production;
- no `LIVE01`;
- no DB mutation expected;
- no media copy;
- no runtime/template/route changes;
- no migration/deploy/restart;
- stop if route/token/server/room is uncertain.

## 3. Preflight commands

Run these before any future dry-run command:

```powershell
cd D:\Projects\pristolov_mvp

git status --short
git log --oneline -5

python -m py_compile app\routes\dev.py app\services\question_import_service.py
```

Expected:

- working tree clean;
- latest commits include `57564f2 Add question bank v2 import-compatible text-only candidate`;
- compile passes.

## 4. Candidate parse verification command

Run this local read-only parse check before any HTTP dry-run:

```powershell
cd D:\Projects\pristolov_mvp

$env:PYTHONPATH = "D:\Projects\pristolov_mvp"
python -c "from pathlib import Path; from app.services.question_import_service import parse_questions_xlsx, build_questions_import_preview; p=Path('docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx'); items=parse_questions_xlsx(p); preview=build_questions_import_preview(p); print('PARSED_COUNT', len(items)); print('PREVIEW_COUNT', preview.get('questions_count')); print('SECTIONS', preview.get('sections')); print('ERROR_COUNT', sum(1 for x in items if x.get('has_errors'))); print('MEDIA_REFS_NONEMPTY', [x.get('media_ref') for x in items if x.get('media_ref')]);"
```

Expected:

```text
PARSED_COUNT 19
PREVIEW_COUNT 19
SECTIONS {'true_false': 13, 'single_choice': 6, 'free_text': 0}
ERROR_COUNT 0
MEDIA_REFS_NONEMPTY []
```

## 5. Local server requirement

The endpoint exists inside the local FastAPI app. A local server must be running before the HTTP dry-run.

If a local server is not already running, start only local dev server, not production:

```powershell
cd D:\Projects\pristolov_mvp

python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Do not restart production. Do not SSH. Do not deploy.

## 6. Admin token requirement

The import endpoint is under `/dev` and may require the local admin/protected access token depending on middleware and environment.

Before running the dry-run, confirm the local token source used by this project. Do not guess if protected access fails.

Use placeholder below until local token is confirmed:

```text
<LOCAL_DEV_ADMIN_TOKEN>
```

## 7. Future dry-run command - NOT EXECUTED

Only after Victor explicitly approves, local server is confirmed, token is confirmed, and target room is confirmed non-LIVE, use a command shaped like this:

```powershell
cd D:\Projects\pristolov_mvp

curl.exe -X POST "http://127.0.0.1:8000/dev/questions/import" `
  -H "X-Admin-Token: <LOCAL_DEV_ADMIN_TOKEN>" `
  -F "file=@docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx" `
  -F "target_round_code=QUESTION_DRYRUN_02" `
  -F "dry_run=true" `
  -F "clear_existing=false" `
  -F "true_false_limit=13" `
  -F "single_choice_limit=6" `
  -F "free_text_limit=0" `
  -F "media_limit=0" `
  -F "prefer_media=false"
```

Important:

- this should return preview JSON only;
- it must not write to DB because `dry_run=true`;
- it must not clear anything because `clear_existing=false`;
- `target_round_code` must be sent as a multipart form field, not a query parameter;
- the endpoint does not accept `room_code`; `QUESTION_DRYRUN_02` is the target round label for this plan;
- it should select all 19 rows by limits: 13 true/false + 6 single-choice + 0 free-text.

## 8. Expected dry-run response checks

After a future dry-run response, verify:

```text
ok=true
source_type=xlsx
questions_count=19
dry_run=true
media_limit=0
prefer_media=false
preview_selected.selected_count=19
preview_selected.by_type.true_false=13
preview_selected.by_type.single_choice=6
preview_selected.by_type.free_text=0
preview_selected.media_count=0
```

Also verify no question has:

```text
has_errors=true
media_ref not empty
media_type != none
```

## 9. Stop conditions

Stop immediately and do not proceed if:

- working tree is dirty unexpectedly;
- local server is not clearly local `127.0.0.1:8000`;
- token/protected access is uncertain;
- any room/target mentions `LIVE01`;
- response says `dry_run=false`;
- response selects fewer or more than 21 questions;
- any question has parser errors;
- command would run against production or SSH;
- anyone suggests `clear_existing=true`.

## 10. Non-actions in this planning task

- No import endpoint was called.
- No DB mutation happened.
- No production action happened.
- No `LIVE01` touch happened.
- No media copy happened.
- No runtime/template/route changes happened.
- No deploy/migration/restart happened.
- No `clear_existing` was used.

## 11. Recommended next step

If Victor approves, run a separate local dry-run task using this plan. That task should report the actual HTTP response and confirm that no DB mutation occurred.
