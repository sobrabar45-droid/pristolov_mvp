# Question Bank V2: controlled dry-run plan

Purpose: define a safe future dry-run plan for Question Bank V2 without executing import, mutating DB, touching production/LIVE01, or copying media.

Sources:

- `docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx`
- `docs/question_bank_v2/QUESTION_BANK_V2_IMPORT_READINESS_AUDIT.md`

## 1. Safety status

| Check | Value |
| --- | --- |
| Workbook read-only during this plan | yes |
| `safe_to_import` values | `['no']` |
| `import_status` values | `['not_ready']` |
| Import executed | no |
| DB mutation | no |
| Production touched | no |
| LIVE01 touched | no |
| Media copied to app/static | no |

This plan does not override workbook safety gates. A separate explicit approval is required before any import dry-run.

## 2. Candidate split

| Group | Count | Slots |
| --- | ---: | --- |
| Active non-reserve rows | 30 | 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36 |
| Conservative future dry-run candidates | 27 | 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 32, 33, 34, 35, 36 |
| Text/no-media dry-run candidates | 21 | 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 35 |
| Visual dry-run candidates after media prep/check | 6 | 6, 30, 32, 33, 34, 36 |
| Visual rows needing media prep before real game use | 3 | 2, 16, 31 |
| Reserve rows excluded | 13 | 29, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48 |
| Technical cut rows excluded | 5 | 1, 10, 12, 17, 28 |

## 3. Rows allowed into future dry-run candidate set

These rows may be selected for a future dry-run candidate set only after explicit approval. This document does not mark them import-ready.

| Slot | Code | Round | Type | Visual | Answer present | Status |
| ---: | --- | --- | --- | --- | --- | --- |
| 3 | `v2_edited_q003` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 4 | `v2_edited_q004` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 5 | `v2_edited_q005` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 6 | `v2_edited_q006` | `v2_warmup_oath` | `plain_text` | yes | yes | `needs_media` |
| 7 | `v2_edited_q007` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 8 | `v2_edited_q008` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 9 | `v2_edited_q009` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 11 | `v2_edited_q011` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 13 | `v2_edited_q013` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 14 | `v2_edited_q014` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 15 | `v2_edited_q015` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 18 | `v2_edited_q018` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 19 | `v2_edited_q019` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 20 | `v2_edited_q020` | `v2_warmup_oath` | `plain_text` | no | yes | `needs_review` |
| 21 | `v2_edited_q021` | `v2_stories_tricks` | `plain_text` | no | yes | `needs_review` |
| 22 | `v2_edited_q022` | `v2_signs_objects` | `plain_text` | no | yes | `needs_review` |
| 23 | `v2_edited_q023` | `v2_stories_tricks` | `plain_text` | no | yes | `needs_source_check` |
| 24 | `v2_edited_q024` | `v2_signs_objects` | `plain_text` | no | yes | `needs_review` |
| 25 | `v2_edited_q025` | `v2_stories_tricks` | `plain_text` | no | yes | `needs_review` |
| 26 | `v2_edited_q026` | `v2_signs_objects` | `plain_text` | no | yes | `needs_review` |
| 27 | `v2_edited_q027` | `v2_stories_tricks` | `plain_text` | no | yes | `needs_review` |
| 30 | `v2_edited_q030` | `v2_signs_objects` | `image_clue` | yes | yes | `needs_media` |
| 32 | `v2_edited_q032` | `v2_signs_objects` | `image_clue` | yes | yes | `needs_media` |
| 33 | `v2_edited_q033` | `v2_signs_objects` | `image_clue` | yes | yes | `needs_source_check` |
| 34 | `v2_edited_q034` | `v2_signs_objects` | `image_clue` | yes | yes | `needs_media` |
| 35 | `v2_edited_q035` | `v2_stories_tricks` | `plain_text` | no | yes | `needs_source_check` |
| 36 | `v2_edited_q036` | `v2_signs_objects` | `image_clue` | yes | yes | `needs_media` |

## 4. Text/no-media dry-run candidates

These are the safest first-pass candidates because they do not depend on image preparation.

| Slot | Code | Round | Status |
| ---: | --- | --- | --- |
| 3 | `v2_edited_q003` | `v2_warmup_oath` | `needs_review` |
| 4 | `v2_edited_q004` | `v2_warmup_oath` | `needs_review` |
| 5 | `v2_edited_q005` | `v2_warmup_oath` | `needs_review` |
| 7 | `v2_edited_q007` | `v2_warmup_oath` | `needs_review` |
| 8 | `v2_edited_q008` | `v2_warmup_oath` | `needs_review` |
| 9 | `v2_edited_q009` | `v2_warmup_oath` | `needs_review` |
| 11 | `v2_edited_q011` | `v2_warmup_oath` | `needs_review` |
| 13 | `v2_edited_q013` | `v2_warmup_oath` | `needs_review` |
| 14 | `v2_edited_q014` | `v2_warmup_oath` | `needs_review` |
| 15 | `v2_edited_q015` | `v2_warmup_oath` | `needs_review` |
| 18 | `v2_edited_q018` | `v2_warmup_oath` | `needs_review` |
| 19 | `v2_edited_q019` | `v2_warmup_oath` | `needs_review` |
| 20 | `v2_edited_q020` | `v2_warmup_oath` | `needs_review` |
| 21 | `v2_edited_q021` | `v2_stories_tricks` | `needs_review` |
| 22 | `v2_edited_q022` | `v2_signs_objects` | `needs_review` |
| 23 | `v2_edited_q023` | `v2_stories_tricks` | `needs_source_check` |
| 24 | `v2_edited_q024` | `v2_signs_objects` | `needs_review` |
| 25 | `v2_edited_q025` | `v2_stories_tricks` | `needs_review` |
| 26 | `v2_edited_q026` | `v2_signs_objects` | `needs_review` |
| 27 | `v2_edited_q027` | `v2_stories_tricks` | `needs_review` |
| 35 | `v2_edited_q035` | `v2_stories_tricks` | `needs_source_check` |

## 5. Visual rows requiring media preparation before real game use

These rows have visual/media needs. Even if a row can be dry-run planned, final game use requires media prep, source/status check, and app/static copy in a separate approved task.

| Slot | Code | Candidate group | media_ref | Selected file | Image status | Required before real game |
| ---: | --- | --- | --- | --- | --- | --- |
| 2 | `v2_edited_q002` | needs media prep first | `v2_edited_playing_card_money` | `none` | `needs_mapping` | map/select source file |
| 6 | `v2_edited_q006` | dry-run candidate after media check | `v2_edited_backrub` | `v2_edited_backrub.jpg` | `source_available_unverified` | source/rights check |
| 16 | `v2_edited_q016` | needs media prep first | `v2_edited_banany` | `v2_edited_banany.jfif` | `needs_crop_or_replace` | crop or replace |
| 29 | `v2_edited_q029` | reserve/excluded | `v2_edited_parrot_cage` | `none` | `needs_mapping` | map/select source file |
| 30 | `v2_edited_q030` | dry-run candidate after media check | `v2_edited_knocker_up` | `v2_edited_knocker_up.jpeg` | `source_available_unverified` | source/rights check |
| 31 | `v2_edited_q031` | needs media prep first | `v2_edited_beauty_contest` | `v2_edited_beauty_contest.png` | `needs_replacement` | replace image |
| 32 | `v2_edited_q032` | dry-run candidate after media check | `v2_edited_two_penny_hangover` | `v2_edited_two_penny_hangover.jpg` | `source_available_unverified` | source/rights check |
| 33 | `v2_edited_q033` | dry-run candidate after media check | `v2_edited_bear_back` | `v2_edited_bear_back.png` | `needs_source_check` | source/rights check |
| 34 | `v2_edited_q034` | dry-run candidate after media check | `v2_edited_vinaigrette_box` | `v2_edited_vinaigrette_box.jpg` | `source_available_unverified` | source/rights check |
| 36 | `v2_edited_q036` | dry-run candidate after media check | `v2_edited_buttonhook` | `v2_edited_buttonhook.jpg` | `source_available_unverified` | source/rights check |
| 40 | `v2_edited_q040` | reserve/excluded | `v2_edited_time_salad` | `none` | `needs_mapping` | map/select source file |
| 41 | `v2_edited_q041` | reserve/excluded | `v2_edited_kodak_2` | `v2_edited_kodak_2.jpg` | `source_available_unverified` | source/rights check |
| 42 | `v2_edited_q042` | reserve/excluded | `v2_edited_microwave` | `v2_edited_microwave.jpg` | `source_available_unverified` | source/rights check |
| 43 | `v2_edited_q043` | reserve/excluded | `v2_edited_dishwasher` | `v2_edited_dishwasher.jfif` | `source_available_unverified` | source/rights check |
| 44 | `v2_edited_q044` | reserve/excluded | `v2_edited_ratcatcher_2` | `v2_edited_ratcatcher_2.jfif` | `source_available_unverified` | source/rights check |
| 45 | `v2_edited_q045` | reserve/excluded | `v2_edited_time_seller` | `v2_edited_time_seller.jpg` | `source_available_unverified` | source/rights check |
| 48 | `v2_edited_q048` | reserve/excluded | `v2_edited_card_kings` | `v2_edited_card_kings.jpg` | `needs_clean_source` | clean source |

## 6. Reserve/cut rows excluded

These rows must not be included in the next dry-run candidate set unless Victor explicitly reopens them later.

| Slot | Code | Exclusion reason |
| ---: | --- | --- |
| 29 | `v2_edited_q029` | reserve, needs_video_check |
| 37 | `v2_edited_q037` | reserve |
| 38 | `v2_edited_q038` | reserve |
| 39 | `v2_edited_q039` | reserve |
| 40 | `v2_edited_q040` | reserve |
| 41 | `v2_edited_q041` | reserve |
| 42 | `v2_edited_q042` | reserve |
| 43 | `v2_edited_q043` | reserve |
| 44 | `v2_edited_q044` | reserve |
| 45 | `v2_edited_q045` | reserve |
| 46 | `v2_edited_q046` | reserve |
| 47 | `v2_edited_q047` | reserve |
| 48 | `v2_edited_q048` | reserve |
| 1 | `v2_edited_q001` | cut |
| 10 | `v2_edited_q010` | cut |
| 12 | `v2_edited_q012` | cut |
| 17 | `v2_edited_q017` | cut |
| 28 | `v2_edited_q028` | cut |

## 7. Exact future dry-run command template - NOT EXECUTED

Do not run this until Victor explicitly approves the dry-run and the target non-LIVE room/code is confirmed.

```powershell
cd D:\Projects\pristolov_mvp

# Example only. Replace ROOM_CODE and file path after explicit approval.
# Must stay dry_run=true and clear_existing=false.
curl.exe -X POST "http://127.0.0.1:8000/dev/questions/import?room_code=NON_LIVE_ROOM&dry_run=true&clear_existing=false" ^
  -H "X-Admin-Token: <LOCAL_DEV_ADMIN_TOKEN>" ^
  -F "file=@docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx"
```

Required command constraints:

- `dry_run=true` only;
- `clear_existing=false` only;
- non-LIVE room only;
- no production unless separately approved;
- no `LIVE01`;
- no DB mutation;
- no media copy as part of dry-run command;
- do not expose `/dev/questions/import` publicly.

## 8. Recommended next steps

1. Victor approves which of the 27 conservative candidates are in the first dry-run set.
2. Decide whether the first dry-run should be text-only or include selected visual rows.
3. If visual rows are included, run a separate media-prep task first.
4. Create an import-ready copy/export only after explicit approval; do not mutate this authoring workbook directly into import-ready state.
5. Run local dry-run only in a non-LIVE room with `dry_run=true` and `clear_existing=false`.

## 9. Non-actions in this task

- No workbook edits.
- No import.
- No DB mutation.
- No production action.
- No LIVE01 touch.
- No media copy.
- No runtime/template/route changes.
- No deploy/migration/restart.
- No `clear_existing`.
