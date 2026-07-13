# PRISTOLOV_CORE: server pre-live readiness audit after SSH

## 1. Executive summary

Manual read-only SSH audit completed successfully against the PRISTOLOV_CORE server.

Verdict: `READY_FOR_CONTROLLED_PRELIVE_PLAN_WITH_DB_AUDIT_PENDING`.

- Server Git working tree is clean on `main` at `be04f4c`.
- `pristolov.service` is active and public endpoint smoke passed.
- Server code already includes the multipart `/dev/questions/import` endpoint and correct `target_round_code` form-field handling.
- Server database inventory remains partially unknown because no database query was run.
- Local Question Bank V2 artifacts and imported local DB state are not present on the server merely because they exist locally.
- No deployment, import, restart, or server mutation was performed.

## 2. Server target

- SSH host: `root@5.42.119.94`
- Hostname: `msk-1-vm-uetq`
- Application path: `/opt/pristolov/app`
- Branch: `main`
- Server HEAD: `be04f4c`
- Working tree: clean

## 3. Server Git state

Recent server commits:

1. `be04f4c Polish public homepage and join page`
2. `45ec008 Add public homepage`
3. `a27594d Add homepage content pack v1`
4. `338b058 Add homepage landing v3 prototype`
5. `64e1f86 Add homepage landing concept v1`
6. `d3dd64c Add pre-game freeze checkpoint v1`
7. `8d48266 Add post-game feedback sheet v1`
8. `ab52ecb Add host game pack v1`
9. `723cdb0 Add production browser smoke protocol`
10. `052b689 Add live operator checklist v2`

## 4. Service state

- Service: `pristolov.service`
- State: `active`
- Command: `/opt/pristolov/venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
- Active since: `Fri 2026-07-10 03:08:32 UTC`
- No service crash was observed in the reviewed logs.
- Recent public probe requests for `.env...` paths returned `404`; no secret exposure was observed.

## 5. Endpoint smoke

| Endpoint | Result |
|---|---:|
| Health | `200` |
| Home | `200` |
| Join | `200` |

## 6. Question import capability

`rg` was unavailable on the server, so the read-only source check used `grep`.

The server contains:

- `app/routes/dev.py:3792:@router.post("/questions/import")`
- `dry_run: str = Form("true")`
- `target_round_code: str = Form("imported_warmup_test")`
- `true_false_limit: int = Form(5)`
- `single_choice_limit: int = Form(5)`
- `free_text_limit: int = Form(3)`
- `media_limit: int = Form(0)`
- `prefer_media: str = Form("false")`
- `clear_existing: str = Form("false")`

Conclusion:

- `/dev/questions/import` already exists on the server.
- Import parameters are multipart form fields.
- The corrected local `-F` command style is compatible with server code.
- No runtime change is required for `target_round_code` handling.
- This audit does not authorize or execute an import.

## 7. Database configuration and remaining uncertainty

- A `.env*` file contains `DATABASE_URL` at line 11.
- The value was redacted and no secret was printed.
- The current interactive shell did not expose a set database environment variable.
- No database query was run.

Therefore these facts remain `UNVERIFIED`:

- Existing non-LIVE room inventory.
- Whether a dedicated safe pre-live room already exists.
- Whether `QUESTION_DRYRUN_02` exists in the server database.
- Server-side Question Bank V2 question count and role configuration.
- Current server-side test runtime state.

`LIVE01` was not queried or accessed.

## 8. Local/server mismatch

- Server HEAD: `be04f4c`.
- Local branch contains many later commits covering Question Bank V2 artifacts, local import evidence, reveal smoke reports, and the participant load-smoke checklist.
- Those local files are not available on the server unless a later push and controlled deployment are separately approved.
- Local database imports are not transferred through Git or code deployment.
- Deploying code alone will not populate the server database with the 19 imported questions.

## 9. Risk map

### Verified low-risk readiness

- Server application responds.
- Service is active.
- Server working tree is clean.
- Existing import endpoint supports the required multipart form fields.

### Remaining blockers before setup execution

- Server database inventory has not been audited.
- A dedicated non-LIVE pre-live room has not been confirmed.
- Question Bank V2 artifacts have not been pushed or deployed to the server.
- The 19 questions have not been imported into the server database.
- No server-side Master/TV/player or 10-15 participant smoke has been run for Question Bank V2.

## 10. Recommended controlled sequence

1. Perform a separate read-only server database inventory excluding `LIVE01`.
2. Select or explicitly approve a dedicated non-LIVE pre-live room.
3. Decide which local commits and artifacts should be pushed.
4. Prepare a narrow deployment plan only if server files are required.
5. Transfer the approved importer-compatible XLSX through a separately approved method.
6. Repeat server-side dry-run with `dry_run=true` and `clear_existing=false`.
7. Only after explicit approval, run a controlled non-LIVE server import.
8. Run Master, TV, Maester player, and 10-15 participant pre-live smoke.

Production deployment and any `LIVE01` action remain forbidden until separately approved.

## 11. Safety and non-actions

- No deploy.
- No `git pull` or `git push`.
- No service restart.
- No import or importer call.
- No database mutation or migration.
- No room creation or deletion.
- No media copy.
- No server file edit.
- No `LIVE01` access.
- No private key, token, password, or database URL was exposed.

This document records the observed manual read-only audit only.
