# SERVER CODE / ARTIFACT DEPLOY RESULT

## 1. Executive summary

Server code/artifact deployment passed.

- Server now runs HEAD `39f9cfc` on `main`.
- `pristolov.service` was restarted and is active.
- Loopback and public smoke are green.
- XLSX fallback parser sanity passed without `openpyxl`.
- No import was run.
- DB and `LIVE01` remain untouched.

## 2. Local and origin state

- Local HEAD: `39f9cfc`.
- `origin/main`: `39f9cfc`.
- Local working tree: clean.

## 3. Server fast-forward result

- Server path: `/opt/pristolov/app`.
- Previous server HEAD: `37a7fc8`.
- New server HEAD: `39f9cfc`.
- Fast-forward status: passed.
- Final server branch: `main`.
- Final server working tree: clean.

## 4. Parser / artifact sanity

The deployed hotfix was:

`39f9cfc Fix XLSX fallback sheet path resolution`

Results:

- `py_compile` passed for `app/services/question_import_service.py`.
- Fallback parser ran on the V2 candidate without `openpyxl`.
- Parsed: `19`.
- Errors: `0`.
- Types: `13 true_false`, `6 single_choice`.
- Media refs: `0`.
- `FALLBACK_ASSERTIONS_PASSED True`.

## 5. Service restart and smoke

- Service: `pristolov.service`.
- Status: `active`.
- Uvicorn: listening on `127.0.0.1:8000`.

Loopback smoke:

- `HEALTH 200`.
- `HOME 200`.
- `JOIN 200`.

Public smoke:

- `PUBLIC_HOME 200`.
- `PUBLIC_JOIN 200`.

## 6. Safety confirmation

- No `/dev/questions/import` endpoint call.
- No import.
- No DB mutation.
- No migration.
- No package installation.
- No room creation, deletion, or change.
- No `LIVE01` action.
- No `clear_existing` action.
- No media copy outside git-tracked artifacts.

## 7. Known note

The first immediate loopback curl after restart returned `Connection refused` because the smoke ran too early. A follow-up diagnostic confirmed that the service was active, Uvicorn was listening on port `8000`, and health/home/join returned `200`.

The server journal also contains unrelated public internet scanner requests, including phpMyAdmin, wp-login, and OWA probes returning `404`/`405`. These are not part of this deploy and are not blocking the current pre-live deployment.

## 8. Next recommendation

The next gate is a controlled server dry-run for `QUESTION_DRYRUN_02` only:

- `dry_run=true`;
- `clear_existing=false`;
- expected `19` questions;
- expected `0` errors;
- expected `0` media.

Do not run write/import mode until the server dry-run is green and Victor explicitly approves it.
