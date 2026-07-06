# Question Bank V2 Authoring Draft

## What this is

`question_bank_v2_authoring_draft.xlsx` is the first local authoring draft workbook for the next commercial `?????????` question bank.

It is an authoring draft only. It is not import-ready.

## Safety status

- No DB mutation.
- No production action.
- No LIVE01 touch.
- No import was run.
- No migrations.
- No media files were created or copied into `app/static/questions_media`.
- All question rows are `safe_to_import=no`.
- All question rows have `import_status=not_ready`.
- `clear_existing=true` is forbidden without separate explicit approval and rollback plan.

## Workbook sheets

1. `questions` - 48 authoring rows for candidate questions.
2. `media_assets` - 13 planned visual/image candidates.
3. `manual_audio` - 4 host-operated/offline manual audio moments.
4. `review_status` - 48 review tracking rows.

## Manual audio rule

Manual audio is host-operated/offline only.

The app is not expected to play audio. Manual audio rows use `media_type=none`, include `manual_audio` in tags, and require fallback text before live use.

## Image rule

Images still need assets/source checks.

No image is claimed to exist yet. Image rows and media assets must be reviewed for source/rights, filename alignment, local open check, and TV readability before dry-run.

## Import rule

Import only after review and dry-run approval.

Safe future defaults:

```text
dry-run first
clear_existing=false
target_round_code=v2_commercial_test_round
no LIVE01
```

## Next steps

1. Victor/content review.
2. Fill final prompts/options/correct answers.
3. Select final 10-12 image rows.
4. Prepare media assets.
5. Mark rows `ready_for_dry_run` only after review.
6. Run dry-run import only after explicit approval.
