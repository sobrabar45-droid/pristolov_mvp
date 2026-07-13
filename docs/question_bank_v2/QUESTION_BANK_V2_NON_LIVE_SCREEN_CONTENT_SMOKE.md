# Question Bank V2: non-LIVE screen/content smoke

## 1. Executive summary

Read-only non-LIVE screen/content smoke passed at HTTP level after the local Question Bank V2 import.

- Imported round exists in the local database.
- `19` questions were verified read-only.
- Master, TV, and Player screens returned successful HTML responses.
- Active question reveal still needs a separate controlled non-LIVE state smoke; the initial screen HTML does not render question text until an active question is selected.

## 2. DB/content verification

The verification used read-only database queries only.

- Round template ID: `74`
- Round code: `QUESTION_DRYRUN_02`
- Import key: `question_import:QUESTION_DRYRUN_02`
- Persisted questions: `19`
- Sequence range: `1-19`
- Question codes: unique
- Database mutation during this smoke: none

## 3. Screen smoke

All checks were local and non-LIVE.

| Screen | Path | Result |
|---|---|---|
| Master | `/dev/master-screen/TEST_ROOM_SETUP` | `200 text/html` |
| TV | `/dev/tv-mode/TEST_ROOM_SETUP` | `200 text/html` |
| Player | `/house/204B48/player/955` | `200 text/html` |

## 4. Content-flow note

The imported round is present in the local database, but question text is not expected in the initial HTML response until an active question state is selected. Therefore, this checkpoint confirms route availability and imported content presence, but does not claim that active question reveal has been visually verified.

## 5. Safety confirmation

- No importer endpoint call was made during this smoke.
- No database mutation was performed.
- Production was not accessed.
- `LIVE01` was not touched.
- No media was copied.
- No deploy, migration, or restart was performed.
- No runtime files, templates, routes, or XLSX files were edited.

## 6. Next recommended step

1. Run controlled non-LIVE active-game/question-reveal smoke and verify that one imported question appears correctly on Master, TV, and Player screens.
2. After that, prepare a 10-15 participant load-smoke checklist for the same non-LIVE environment.

This document records the read-only result only; it does not authorize another import or any production action.
