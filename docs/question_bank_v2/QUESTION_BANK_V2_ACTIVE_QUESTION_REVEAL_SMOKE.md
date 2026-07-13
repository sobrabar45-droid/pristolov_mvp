# Question Bank V2: active-question reveal smoke

## 1. Executive summary

Verdict: `PARTIAL_PASS_PLAYER_BLOCKED`.

- Master and TV active-question state passed.
- The imported question text is readable Unicode; the stored prompt had zero replacement characters.
- Player state requests returned `200` and showed the active round, but no player received an assignment.
- The player blocker is the test setup: all imported questions use `role_code=maester`, while `TEST_ROOM_SETUP` has no Maester.
- This is not an import, parser, Master, TV, or text-encoding failure.

## 2. Controlled state

- Room: `TEST_ROOM_SETUP`
- Runtime host round ID: `654`
- Round code: `QUESTION_DRYRUN_02`
- Runtime question ID: `2050`
- Sequence: `1`
- Question code: `import_true_false_001`
- Question status: `active`
- Answers: closed

The smoke opened question 1 only. No answer was submitted and the round was not advanced.

## 3. Master/TV verification

- Master state: `200`
- Master page: `200 text/html`
- TV state: `200`
- TV page: `200 text/html`
- Target round present in both state payloads: yes
- Exact imported question present in both state payloads: yes
- Stored Russian prompt: valid Unicode
- Replacement-character count: `0`

## 4. Player verification

- All three player-state requests returned `200`.
- Players could see `QUESTION_DRYRUN_02` as the active round.
- Player assignment count: `0`.
- No player received the active question assignment.

The reason is setup eligibility, not screen rendering: `TEST_ROOM_SETUP` contains two `lord_lady` players and one `treasurer`, but no Maester.

## 5. Blocker

All `19` imported questions in `QUESTION_DRYRUN_02` use `role_code=maester`. Since the selected non-LIVE test room has no Maester, the assignment layer has no eligible player for these questions.

Required follow-up: prepare a separate controlled non-LIVE test setup with a Maester, then repeat player assignment and reveal verification.

## 6. Safety confirmation

- No importer endpoint was called during this smoke.
- Production was not accessed.
- `LIVE01` was not touched.
- No media was copied.
- No deploy, migration, or runtime edit was performed.
- No question answer was submitted.
- No round advancement occurred beyond opening question 1.

## 7. Next recommendation

1. Prepare a separate controlled non-LIVE Maester test setup.
2. Repeat player assignment and active-question reveal verification.
3. Treat that setup change as requiring explicit approval because it changes local test-player or phase state.

This document records the smoke result only and does not authorize another import or any production action.
