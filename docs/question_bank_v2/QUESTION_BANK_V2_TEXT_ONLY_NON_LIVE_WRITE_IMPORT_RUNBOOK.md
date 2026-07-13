# Question Bank V2: controlled non-LIVE write/import runbook

## 1. Executive summary

This document is a plan for a future controlled write/import. It is not an execution record and does not authorize a write.

Green checkpoint already completed:

- local non-LIVE dry-run passed;
- `target_round_code=QUESTION_DRYRUN_02` was received correctly;
- `dry_run=true`;
- `clear_existing=false`;
- selected `19` questions;
- `13 true_false`, `6 single_choice`, `0 free_text`;
- `0` errors;
- `0` media;
- DB write was not expected during dry-run.

The next possible action is a controlled local/non-LIVE write/import only after explicit approval. Production and `LIVE01` are forbidden.

## 2. Preconditions

Confirm every item before any future write/import:

- [ ] working tree is clean;
- [ ] local environment only;
- [ ] URL is not production;
- [ ] no SSH or remote server;
- [ ] target is not `LIVE01`;
- [ ] candidate file exists;
- [ ] parser check passes without errors;
- [ ] green dry-run result exists;
- [ ] Victor explicitly approved write/import;
- [ ] DB backup/checkpoint decision was made before write mode;
- [ ] `clear_existing=false` is confirmed;
- [ ] response confirms `target_round_code=QUESTION_DRYRUN_02`.

If any item is not confirmed, do not run write/import.

## 3. Candidate

- XLSX: `docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`.
- Expected rows: `19`.
- `true_false`: `13`.
- `single_choice`: `6`.
- `free_text`: `0`.
- Media: `0`.
- Green dry-run result: `docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_LOCAL_DRY_RUN_V2_FORM_FIELDS_RESULT.md`.

## 4. Final dry-run repeat immediately before write

Repeat the dry-run immediately before write, locally only, through TestClient `data={...}` or `127.0.0.1:8000` with multipart form fields.

Template only; not executed in this task:

```powershell
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

Proceed toward write only if the response confirms `dry_run=true`, `target_round_code=QUESTION_DRYRUN_02`, `19` selected, `0` errors, and `0` media.

## 5. Controlled write/import template - NOT EXECUTED

**DO NOT RUN WITHOUT VICTOR EXPLICIT APPROVAL.**

**DO NOT RUN AGAINST PRODUCTION.**

**DO NOT USE `LIVE01`.**

**DO NOT USE `clear_existing=true`.**

Only after all preconditions and a green repeated dry-run:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/dev/questions/import" `
  -H "X-Admin-Token: <LOCAL_DEV_ADMIN_TOKEN>" `
  -F "file=@docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx" `
  -F "target_round_code=QUESTION_DRYRUN_02" `
  -F "dry_run=false" `
  -F "clear_existing=false" `
  -F "true_false_limit=13" `
  -F "single_choice_limit=6" `
  -F "free_text_limit=0" `
  -F "media_limit=0" `
  -F "prefer_media=false"
```

This is a future operator template. It was not executed in this task.

Stop immediately if:

- target round in the command or response is not `QUESTION_DRYRUN_02`;
- the response reports unexpected deletes or clears;
- selected count is not `19`;
- the response contains a validation error;
- `clear_existing` is not `false`.

## 6. Expected write response

Expected success indicators:

- HTTP `200`;
- `ok=true`;
- `dry_run=false`;
- `target_round_code=QUESTION_DRYRUN_02`;
- selected/imported count matches `19`;
- errors `0`;
- media `0`;
- no clear operation occurred;
- created/imported count, if present, matches selected rows.

Any deviation is a stop condition. Do not rerun and do not manually correct the DB.

## 7. Post-write checks

After a future write/import, run only approved checks:

- `git status` is unchanged;
- local DB question templates contain the expected target round code;
- no rows were deleted or cleared;
- Game Master question area opens in a non-LIVE test room;
- TV question reveal works for text-only questions;
- player screens are unaffected.

This runbook contains no DB mutation commands. Only read-only SELECT checks through an approved local tool are allowed.

## 8. Stop conditions

Do not start or stop immediately if any condition applies:

- unexpected dirty working tree;
- endpoint is not local;
- production URL or SSH/remote server is present;
- `LIVE01` is mentioned;
- repeated dry-run has missing or false `dry_run`;
- `clear_existing=true` or value is not confirmed as false;
- `target_round_code` is missing, defaulted, or differs from `QUESTION_DRYRUN_02`;
- parser errors;
- selected count is not `19`;
- selected media is greater than `0`;
- validation error;
- unexpected delete/clear behavior;
- no explicit Victor approval;
- no DB backup/checkpoint decision before write mode.

## 9. IF-report template for future execution

1. `preflight`
2. `parser check`
3. `repeated dry-run result`
4. `explicit Victor approval for write`
5. `write command used`, token redacted
6. `HTTP status`
7. `response target_round_code`
8. `selected/imported counts`
9. `errors/warnings`
10. `DB write confirmation`
11. `post-write checks`
12. `final git status`
13. `recommendation`

The future report must state that the write command ran locally/non-LIVE only and used `clear_existing=false`.

## 10. Safety confirmation for this runbook task

- Runbook creation did not call the endpoint.
- Import was not executed.
- DB was not changed.
- Production was not touched.
- `LIVE01` was not touched.
- Media was not copied.
- Runtime, routes, and templates were not changed.
- Deploy and migrations were not executed.
- No commit was made as part of runbook creation.
