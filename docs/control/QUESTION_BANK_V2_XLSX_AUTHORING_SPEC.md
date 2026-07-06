# Question Bank V2 XLSX Authoring Spec

## 1. Purpose

This document defines how to build the future Question Bank V2 spreadsheet before any `.xlsx` file is created or imported.

It is a docs-only authoring specification.

It does not create an XLSX file. It does not import questions. It does not mutate the database. It does not touch production or `LIVE01`.

Use this spec to keep question writing, media planning, review statuses, and import safety consistent.

Source chain:

- `docs/control/QUESTION_BANK_V2_PREPARATION_PLAN.md`
- `docs/control/QUESTION_BANK_V2_BLUEPRINT.md`
- `docs/control/QUESTION_BANK_V2_DRAFT_LIST.md`
- `docs/control/QUESTION_BANK_V2_DRAFT_REVIEW.md`

Review verdict inherited from draft review:

```text
READY_FOR_XLSX_DRAFT_WITH_EDITORIAL_WORK
```

## 2. XLSX file purpose and scope

The future XLSX should be an authoring and review file first, not an immediate import artifact.

Primary goals:

- convert 48 candidate slots into editable rows;
- write final prompts, options, correct answers, and explanations;
- track review status;
- mark core vs reserve rows;
- mark image rows and media references;
- mark manual audio rows without runtime audio dependency;
- keep safety flags visible before import.

Out of scope for the XLSX draft:

- no import execution;
- no runtime audio patch;
- no DB mutation;
- no production action;
- no `LIVE01` action;
- no destructive `clear_existing=true` workflow.

## 3. Workbook structure

Recommended workbook filename:

```text
question_bank_v2_authoring_draft.xlsx
```

Recommended sheets:

| Sheet | Required | Purpose |
| --- | --- | --- |
| `questions` | yes | Main import-oriented authoring table. |
| `media_assets` | yes | Image/media asset tracking before files are placed under static media. |
| `manual_audio` | yes | Host-operated music/audio plan. |
| `review_notes` | optional | Editorial notes, approvals, cut decisions. |

Only the `questions` sheet should be treated as a future import candidate.

The other sheets are operational planning helpers and should not be imported as questions.

## 4. `questions` sheet columns

Use these columns in this order:

```text
slot
section
round_code
question_code
question_type
question
option_a
option_b
option_c
option_d
correct_answer
explanation
media_type
media_ref
difficulty
role_code
tags
review_status
source_note
host_note
asset_status
is_core
is_reserve
needs_victor
safe_to_import
```

Column definitions:

| Column | Required | Allowed / format | Notes |
| --- | --- | --- | --- |
| `slot` | yes | `1`-`48` | Matches draft-list slot. |
| `section` | yes | `warmup`, `main_1`, `main_2`, `court`, `final`, `reserve`, `duel`, `host_manual` | Human grouping. |
| `round_code` | yes | V2 round codes only | See allowed values below. |
| `question_code` | yes | stable slug, e.g. `v2_q001_oath_table` | Must be unique. |
| `question_type` | yes | importer-facing value | See mapping below. |
| `question` | yes before import | final playable prompt | Empty allowed during early authoring only. |
| `option_a` | conditional | text | Required for `single_choice` and true/false style rows. |
| `option_b` | conditional | text | Required for `single_choice` and true/false style rows. |
| `option_c` | conditional | text | Usually required for `single_choice`. |
| `option_d` | conditional | text | Usually required for `single_choice`. |
| `correct_answer` | yes before import | exact option/key/text | Must match expected importer behavior. |
| `explanation` | yes before import | text | Host/TV reveal explanation. |
| `media_type` | yes | `none` or `image` | Do not use runtime `audio` for this game. |
| `media_ref` | conditional | slug | Required if `media_type=image`; blank otherwise. |
| `difficulty` | yes | `easy`, `medium`, `hard` | Keep commercial flow mostly easy/medium. |
| `role_code` | optional | blank, `maester`, or confirmed role code | Usually blank. |
| `tags` | yes | comma-separated tags | Include reserve/media/manual flags. |
| `review_status` | yes | status workflow value | See below. |
| `source_note` | recommended | text | Fact/media/source/rights note. |
| `host_note` | recommended | text | Manual audio, pacing, fallback, Court note. |
| `asset_status` | recommended | asset workflow value | Required for image/manual audio rows. |
| `is_core` | yes | `yes` / `no` | Core/flex playable rows. |
| `is_reserve` | yes | `yes` / `no` | Reserve rows. |
| `needs_victor` | yes | `yes` / `no` | Required for local/tone/music decisions. |
| `safe_to_import` | yes | `yes` / `no` | Must remain `no` until final review. |

## 5. Allowed round codes

Use only these V2 round codes unless a later approved scenario mapping changes them:

```text
v2_warmup_oath
v2_signs_objects
v2_stories_tricks
v2_court_trial
v2_final_word
v2_reserve
```

Recommended grouping:

| round_code | section | intended slots |
| --- | --- | --- |
| `v2_warmup_oath` | `warmup` | 1-6 |
| `v2_signs_objects` | `main_1` | 7-14 |
| `v2_stories_tricks` | `main_2` | 15-22 |
| `v2_court_trial` | `court` | 23-28 |
| `v2_final_word` | `final` | 29-32 |
| `v2_reserve` | `reserve`, `duel`, `host_manual` | 33-48 |

## 6. Question type mapping

The draft list uses descriptive authoring types. The XLSX should use importer-facing values where possible.

Recommended importer-facing `question_type` values:

```text
true_false
single_choice
free_text
```

Authoring-type mapping:

| Draft type | XLSX `question_type` | Required tag |
| --- | --- | --- |
| `plain_text` | `single_choice` or `true_false` | none unless reserve/final/etc. |
| `image_clue` | `single_choice` | `image_clue` |
| `image_after_timer` | `single_choice` | `image_after_timer` |
| `image_reveal` | `single_choice` or `free_text` | `image_reveal` |
| `manual_audio` | `single_choice` | `manual_audio` |
| `music_knowledge` | `single_choice` | `manual_audio` |
| `role_prompt` | `single_choice` or `free_text` | `role_prompt` |
| `court_question` | `single_choice` or `free_text` | `court_safe` |
| `duel_question` | `true_false` or `single_choice` | `duel_ready` |
| `host_manual_moment` | usually not imported | `host_manual` |

Notes:

- Most commercial game rows should become `single_choice`.
- Use `true_false` only for very fast warmup/Duel rows.
- Use `free_text` sparingly for Court/final/host-judged rows.
- `host_manual_moment` rows may remain in XLSX as planning rows with `safe_to_import=no`.

## 7. Review status workflow

Allowed `review_status` values:

```text
idea
needs_write
needs_fact_check
needs_media
needs_victor
ready_for_dry_run
reserve
cut
```

Meaning:

| review_status | Meaning | Can import? |
| --- | --- | --- |
| `idea` | Rough concept only. | no |
| `needs_write` | Needs final prompt/options/correct answer. | no |
| `needs_fact_check` | Wording exists but source/fact not confirmed. | no |
| `needs_media` | Image/audio/source asset not ready. | no |
| `needs_victor` | Needs Victor/operator approval. | no |
| `ready_for_dry_run` | Ready for import dry-run preview only. | maybe, dry-run only |
| `reserve` | Backup row, not core sequence. | only if selected later |
| `cut` | Removed from current bank. | no |

Rule:

- `safe_to_import` must be `no` unless `review_status=ready_for_dry_run` and all required fields are complete.
- `approved` is intentionally not used as an early status in this spec. Use `ready_for_dry_run` first.

## 8. Tags

Use comma-separated tags.

Allowed/common tags:

```text
image_clue
image_after_timer
image_reveal
image_decorate
manual_audio
court_safe
final_safe
duel_ready
reserve
needs_fact_check
needs_image
needs_host_note
needs_victor
local_reference
sobranie_reference
host_manual
```

Rules:

- Reserve rows must include `reserve`.
- Manual audio rows must include `manual_audio`.
- Image rows should include one image usage tag.
- Court rows should include `court_safe` unless intentionally experimental.
- Duel rows should include `duel_ready`.
- Local references should include `local_reference`.
- Direct Собрание references should include `sobranie_reference`.

## 9. Media/image handling

For this game, image questions are the primary runtime media feature.

XLSX rules:

- Use `media_type=image` only for selected image rows.
- Use stable Latin slug-style `media_ref` values.
- Do not include file extensions in `media_ref` unless importer expectations require it later.
- Keep `media_ref` aligned with future filename under `app/static/questions_media`.

Recommended `media_ref` examples:

```text
v2_q003_table_object_closeup
v2_q007_old_tool
v2_q009_ad_fragment
v2_q016_food_closeup
```

Image readiness requirements before `ready_for_dry_run`:

- source identified;
- rights/source approved or acceptable for event use;
- image readable from far tables;
- crop planned;
- filename planned;
- `media_ref` matches asset list;
- fallback exists if image fails.

Do not mark an image row `safe_to_import=yes` until the asset exists or the dry-run goal explicitly allows missing-media discovery.

## 10. Manual audio/music handling

Runtime audio is not reliable enough for this game.

XLSX rules:

- Do not use `media_type=audio`.
- Use `media_type=none` for manual audio rows.
- Add `manual_audio` to `tags`.
- Explain host action in `host_note`.
- Track source/legal status in `source_note` or the `manual_audio` sheet.
- Every manual audio row needs a text-only fallback.

Primary manual audio rows from review:

| question_code | recommended status |
| --- | --- |
| `v2_q017_manual_audio_mood` | primary |
| `v2_q022_manual_audio_instrument` | primary if source simple |
| `v2_q031_final_manual_audio` | optional primary/final |
| `v2_q042_reserve_audio_fallback` | reserve fallback |

## 11. Core vs reserve selection

Recommended first-pass authoring:

- Include all 48 rows as candidate rows.
- Mark slots 1-36 as `is_core=yes` unless cut later.
- Mark slots 37-48 as `is_reserve=yes`.
- Some slots inside 1-36 may still have `safe_to_import=no` if they are host-manual or need approval.

Reserve rules:

- Reserve rows must have `tags=reserve`.
- Reserve rows should not be imported into the core live sequence by accident.
- Reserve rows may still be imported into a reserve/test round if explicitly selected later.

## 12. Court and Duel handling

Court rules:

- Court rows should be short and robust.
- Prefer `single_choice` or short `free_text`.
- Avoid fragile media unless TV-smoke-tested.
- Avoid real people accusations or toxic claims.
- Avoid questions that imply automatic gold/resource mutation.

Recommended Court row tags:

```text
court_safe
needs_fact_check
needs_victor
```

Duel rules:

- Duel rows should be fast to understand.
- Prefer `true_false` or short `single_choice`.
- Keep Duel rows reserve/core-flex, not mandatory flow.
- No Duel V2 question-before-move engine.
- No runtime tic-tac-toe expansion.

Recommended Duel row tag:

```text
duel_ready
```

## 13. `media_assets` sheet

Recommended columns:

```text
media_ref
filename
question_code
round_code
usage
source
rights_status
needs_crop
needs_compress
readability_status
asset_status
notes
```

Allowed `usage` values:

```text
clue
reveal
after_timer
decorate
reserve
```

Allowed `rights_status` values:

```text
unknown
needs_approval
approved_for_event
public_domain
original_asset
rejected
```

Allowed `asset_status` values:

```text
planned
source_found
rights_ok
edited
ready_in_static
smoke_passed
rejected
```

## 14. `manual_audio` sheet

Recommended columns:

```text
question_code
moment_name
round_code
host_action
source_or_file
start_point
play_duration
volume_note
fallback_text
rights_status
owner
status
notes
```

Allowed `status` values:

```text
planned
source_found
rights_ok
device_ready
volume_checked
fallback_ready
ready
rejected
```

Rule:

- Manual audio may be used in live play only if source/device/fallback are ready.
- The app should not be expected to play the audio.

## 15. Import safety rules to keep visible

Before any import task:

- Do not import into `LIVE01`.
- Do not mutate production DB.
- Do not run migrations.
- Do not use `clear_existing=true`.
- Do not expose `/dev/questions/import` publicly.
- Do not add homepage links to import/admin routes.
- Do not import rows with `safe_to_import=no`.
- Do not rely on runtime audio.

Safe dry-run defaults:

```text
dry_run=true
clear_existing=false
target_round_code=v2_commercial_test_round
```

## 16. Dry-run readiness checklist

A question row can be considered `ready_for_dry_run` only when:

- `question` is final enough to preview;
- required options are filled;
- `correct_answer` is filled;
- `explanation` is filled;
- `round_code` is valid;
- `question_type` is importer-facing;
- `media_type` is `none` or `image`;
- `media_ref` is filled for image rows;
- manual audio rows use `media_type=none` and `tags=manual_audio`;
- reserve rows are tagged `reserve`;
- local/Sobranie references are approved or marked `needs_victor`;
- `safe_to_import=yes` is intentionally set for dry-run candidates only.

## 17. Suggested first-pass row defaults

Default values for first XLSX authoring pass:

| Row group | review_status | safe_to_import | tags |
| --- | --- | --- | --- |
| Plain core rows | `needs_write` | `no` | blank or topic tag |
| Selected image rows | `needs_media` | `no` | image usage tag |
| Manual audio rows | `needs_victor` | `no` | `manual_audio` |
| Court rows | `needs_fact_check` | `no` | `court_safe` |
| Duel rows | `needs_write` | `no` | `duel_ready` |
| Reserve rows | `reserve` | `no` | `reserve` |
| Host manual rows | `needs_victor` or `cut` | `no` | `host_manual` |

## 18. What not to do in XLSX V2

Do not:

- add final answers without fact-check;
- include copyrighted lyrics;
- use real people accusations;
- create offensive/toxic prompts;
- imply automatic gold/resource mutation;
- create runtime audio dependency;
- use `media_type=audio`;
- import reserve rows as core by accident;
- use `clear_existing=true`;
- import to `LIVE01`;
- treat the XLSX as production-ready without dry-run.

## 19. Next recommended artifact

After this spec is accepted, create one of:

1. `QUESTION_BANK_V2_AUTHORING_DRAFT_ROWS.md`
   - Markdown preview of the first spreadsheet rows before actual XLSX creation.

2. `question_bank_v2_authoring_draft.xlsx`
   - Actual spreadsheet draft, still local/docs artifact only.

3. `QUESTION_BANK_V2_MEDIA_ASSET_LIST.md`
   - Media list before any files are copied into `app/static/questions_media`.

Recommended next step:

- Create Markdown preview rows first if Victor wants one more review layer.
- Create XLSX only after the column/status scheme is accepted.
