# PRISTOLOV_CORE: controlled server pre-live import/setup plan

## 1. Executive summary

This document is a plan only. It does not authorize or execute any server action.

- The server is alive, `pristolov.service` is active, and the import endpoint exists.
- The server does not contain `QUESTION_DRYRUN_02` or its 19 Question Bank V2 questions.
- `LIVE01` exists as game ID `1` and is forbidden for every step in this plan.
- `TEST_ROOM_SETUP` exists as game ID `2`; it may be considered only after a separate read-only state audit and explicit approval.
- A server dry-run, write/import, or room setup requires separate explicit Victor approval before execution.

The safe sequence is: confirm prerequisites, transfer one verified artifact, run a server-local dry-run, review its response, obtain explicit write approval, import only to `QUESTION_DRYRUN_02`, then smoke only against an approved non-LIVE room.

## 2. Preconditions before any server action

All boxes must be confirmed for the specific execution window:

- [ ] Manual SSH access to `root@5.42.119.94` is confirmed.
- [ ] Server working tree is clean.
- [ ] Server branch and HEAD are recorded before action.
- [ ] `pristolov.service` is active.
- [ ] Working path is exactly `/opt/pristolov/app`.
- [ ] Endpoint target is server-local `http://127.0.0.1:8000`.
- [ ] No command, room code, or artifact references `LIVE01`.
- [ ] Server backup/checkpoint decision is made and recorded before write mode.
- [ ] Candidate XLSX identity, size, and checksum are recorded locally and on the server.
- [ ] Candidate is available at a dedicated safe server path.
- [ ] `clear_existing=false` is fixed in both dry-run and write templates.
- [ ] A server dry-run is performed first.
- [ ] Dry-run response passes every expected assertion.
- [ ] No write/import occurs without a new explicit Victor approval after the dry-run report.

Candidate artifact:

`docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`

Expected content:

- total questions: `19`
- `true_false`: `13`
- `single_choice`: `6`
- `free_text`: `0`
- media: `0`

## 3. Required artifact transfer plan

The local XLSX is not currently present on the server. Artifact transfer and import execution are separate approval boundaries.

### Option A: transfer only the candidate XLSX

Use `scp` under a separate explicit artifact-transfer approval to copy only the verified V2 candidate to a dedicated non-runtime path, for example:

`/opt/pristolov/prelive/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx`

Transfer rules:

- Do not overwrite application runtime files.
- Do not copy `.env`, tokens, credentials, local DB files, or unrelated docs.
- Record local and server SHA-256 checksums and require an exact match.
- Keep the candidate outside public static/media paths.
- Do not invoke the import endpoint during the transfer task.

### Option B: push/deploy the relevant repository commits first

This is allowed only under a separate push/deploy plan and approval. After the server repository contains the committed artifact, use its repository path.

Deploying code or docs still does not import questions into the server DB. The dry-run and write/import approval gates remain mandatory.

## 4. Server dry-run plan

Template only. Do not execute as part of this plan.

Run from the server shell against the loopback endpoint. Obtain the admin token through the approved server secret process and do not print or paste it into reports.

```bash
curl --fail-with-body --silent --show-error \
  -X POST "http://127.0.0.1:8000/dev/questions/import" \
  -H "X-Admin-Token: <SERVER_ADMIN_TOKEN>" \
  -F "file=@/opt/pristolov/prelive/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx" \
  -F "target_round_code=QUESTION_DRYRUN_02" \
  -F "dry_run=true" \
  -F "clear_existing=false" \
  -F "true_false_limit=13" \
  -F "single_choice_limit=6" \
  -F "free_text_limit=0" \
  -F "media_limit=0" \
  -F "prefer_media=false"
```

Expected dry-run assertions:

- HTTP status `200`.
- `ok=true`.
- `dry_run=true`.
- `target_round_code=QUESTION_DRYRUN_02`.
- selected question count `19`.
- selected by type: `13 true_false`, `6 single_choice`, `0 free_text`.
- response errors `0`.
- selected errors `0`.
- selected media count `0`.
- no DB write or clear/delete behavior.

Stop after the dry-run and issue an IF-report. Do not continue directly into write mode.

## 5. Server write/import plan

Template only. Do not execute without a successful server dry-run and a separate explicit Victor approval.

```bash
curl --fail-with-body --silent --show-error \
  -X POST "http://127.0.0.1:8000/dev/questions/import" \
  -H "X-Admin-Token: <SERVER_ADMIN_TOKEN>" \
  -F "file=@/opt/pristolov/prelive/question_bank_v2_text_only_import_compatible_candidate_v2.xlsx" \
  -F "target_round_code=QUESTION_DRYRUN_02" \
  -F "dry_run=false" \
  -F "clear_existing=false" \
  -F "true_false_limit=13" \
  -F "single_choice_limit=6" \
  -F "free_text_limit=0" \
  -F "media_limit=0" \
  -F "prefer_media=false"
```

Warnings:

- DO NOT RUN WITHOUT VICTOR'S EXPLICIT WRITE APPROVAL.
- NEVER use `LIVE01` or any production game room.
- NEVER use `clear_existing=true`.
- Stop if the response target defaults to `imported_warmup_test`.
- Stop if selected count is not exactly `19`.
- Stop if any response or selected errors are nonzero.
- Stop if any media is selected.
- Stop if the response indicates clearing, deleting, replacement, or an unexpected target.

Expected write response:

- HTTP status `200`.
- `ok=true`.
- `dry_run=false`.
- `target_round_code=QUESTION_DRYRUN_02`.
- selected/imported count `19`.
- errors `0`.
- media `0`.
- no clear/delete behavior.

## 6. Server room/state plan

`TEST_ROOM_SETUP` exists server-side as game ID `2`. Its name does not prove that it is empty or safe.

Before using it, run a separate read-only audit covering:

- houses and their state;
- players and role assignments;
- presence of a Maester;
- active/completed host rounds;
- active host-round questions;
- existing assignments and answers;
- current phase and scenario linkage;
- any gold, duel, shop, or other runtime state relevant to rehearsal.

If any state is dirty, ambiguous, shared, or risky, do not use `TEST_ROOM_SETUP`.

Alternative: create a dedicated server pre-live room under a separate explicit room-creation and setup plan. This document does not create, reset, clear, or mutate any room.

## 7. Post-import smoke plan

After a future approved import, verify in order:

- `QUESTION_DRYRUN_02` round template exists exactly once.
- Exactly `19` question templates are persisted with unique codes and expected sequence.
- Imported rows contain no media references.
- Master screen opens for the approved non-LIVE room.
- TV screen opens for the approved non-LIVE room.
- Player screen opens for the approved non-LIVE room.
- One imported question can be activated and revealed on Master and TV.
- A Maester receives the expected assignment when the approved role setup exists.
- Russian prompt text has no mojibake or replacement characters.
- No action or query targets `LIVE01`.

Question activation, role setup, and room-state changes require their own controlled smoke approval. Do not answer questions or advance farther than the minimum state required.

## 8. Stop conditions

Stop immediately if any of the following occurs:

- SSH access or operator identity is unclear.
- Server working tree is dirty.
- Service is inactive or unhealthy.
- Application path or endpoint target differs from the approved values.
- Candidate artifact is missing or checksum differs.
- Endpoint is not loopback/local to the server.
- `LIVE01` appears anywhere in an execution command.
- `clear_existing=true` appears anywhere.
- The server dry-run is skipped.
- `dry_run` is missing or not `true` during the required repeat dry-run.
- Response target is missing, defaulted, or not `QUESTION_DRYRUN_02`.
- Selected count is not `19`.
- Errors are nonzero.
- Any media is selected.
- Response indicates clearing or deleting.
- Backup/checkpoint decision is missing before write mode.
- Safety of the intended non-LIVE room is uncertain.

## 9. Decision tree

After preconditions and room-state review, choose exactly one outcome:

1. `KEEP REHEARSAL LOCAL` - no server artifact transfer, import, or room changes.
2. `SERVER DRY-RUN ONLY` - transfer the verified artifact and stop after a green server dry-run report.
3. `SERVER IMPORT TO QUESTION_DRYRUN_02` - only after green dry-run and explicit write approval; room smoke remains separately controlled.
4. `CREATE DEDICATED PRELIVE ROOM FIRST` - use a separate room-creation/setup plan before any active-state smoke.
5. `STOP / NO-GO SERVER SETUP` - use when any prerequisite, count, response, backup, or room-safety condition is unclear.

## 10. Safety confirmation

Creating this plan performed:

- no deploy;
- no push or pull;
- no service restart;
- no import or endpoint call;
- no DB mutation;
- no `LIVE01` action;
- no room creation, deletion, reset, or state change;
- no migration;
- no media or artifact copy;
- no server file edit;
- no secret or token exposure.
