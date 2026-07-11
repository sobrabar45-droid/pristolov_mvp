# Question Bank V2: text-only dry-run candidate artifact report

## 1. Purpose

This report documents the first filtered text-only Question Bank V2 dry-run candidate artifact.

The artifact is an authoring/safety package only. It is not import-ready and must not be imported without a separate explicit approval and dry-run task.

## 2. Artifact

Created XLSX artifact:

```text
docs/question_bank_v2/question_bank_v2_text_only_dry_run_candidate.xlsx
```

Source workbook:

```text
docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx
```

Source scope document:

```text
docs/question_bank_v2/QUESTION_BANK_V2_TEXT_ONLY_DRY_RUN_SCOPE.md
```

## 3. Selected text-only slots

The filtered `questions` sheet contains exactly 21 selected text-only slots:

```text
3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 35
```

These rows exclude:

- all active visual/media rows;
- all reserve rows;
- all cut rows.

## 4. Workbook sheets

The candidate workbook contains:

```text
README
questions
review_status
excluded_rows
scope_21_rows
```

## 5. Verification result

Verification already passed:

```text
SOURCE_UNCHANGED True
XLSX_EXISTS True
XLSX_SIZE 23687
QUESTION_ROWS 22
SAFE_VALUES ['no']
IMPORT_VALUES ['not_ready']
MEDIA_TYPES ['none']
MEDIA_REFS_NONEMPTY []
REVIEW_STATUS_ROWS 22
EXCLUDED_ROWS 28
SCOPE_ROWS 22
```

Meaning:

- source workbook was not changed;
- candidate XLSX opens;
- `questions` sheet has 21 data rows plus header;
- all rows remain `safe_to_import=no`;
- all rows remain `import_status=not_ready`;
- no media rows are included;
- no `media_ref` values are present.

## 6. Safety status

This artifact remains safety-locked:

- no import was run;
- no DB mutation happened;
- no production action happened;
- no `LIVE01` touch happened;
- no media copy happened;
- no runtime/template/route changes happened;
- no migration/deploy/restart happened;
- no `clear_existing` was used;
- nothing was marked import-ready.

## 7. First-attempt note

The first creation script attempt failed before artifact creation because `review_status` did not use a `slot` column. The final creation retried with `question_code` mapping and completed successfully.

## 8. Recommended next step

Before any dry-run command is considered:

1. Review the candidate XLSX as a package.
2. Confirm whether the 21 text-only rows are the intended first dry-run scope.
3. If approved, create a separate explicit local dry-run task using `dry_run=true` and `clear_existing=false` in a non-LIVE room.

Do not import this artifact until Victor explicitly approves the dry-run.
