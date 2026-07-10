# Question Bank V2 XLSX Update From Edited DOCX Report

## Summary

Updated `question_bank_v2_authoring_draft.xlsx` from the edited DOCX source audit and committed source materials.

This is still authoring-only. It is not import-ready.

## Counts

- Questions updated: 48
- Core rows: 36
- Reserve rows: 12
- Visual/image rows in `questions`: 17
- Rows with option drafts: 38
- Rows with `correct_answer_draft`: 10
- Media assets mapped/listed: 22
- Manual audio rows preserved: 4

## Safety confirmation

- `safe_to_import=no` remains required for all question rows.
- `import_status=not_ready` remains required for all question rows.
- No import was run.
- No DB mutation.
- No production action.
- No LIVE01 touch.
- No media copied to `app/static/questions_media`.
- No `clear_existing` action.

## Remaining unresolved decisions

- Victor/content review for exact wording and difficulty.
- Fact-check for all true/false and open-answer claims.
- Source rights check for every image asset.
- TV readability check after final image preparation.
- Final selection of 10-12 image questions.
- Decide which reserve rows become playable, if any.
- Only after review: create a separate dry-run import task; do not use `LIVE01`.
