# Question Bank V2 Draft Review

## 1. Purpose

This document reviews `QUESTION_BANK_V2_DRAFT_LIST.md` before XLSX authoring.

It is an approval/editing layer, not an import file.

Use it to decide:

- which slots should move into the first XLSX draft;
- which slots need stronger wording;
- which slots need media work;
- which slots need Victor/local approval;
- which slots should stay reserve;
- what must not be imported yet.

No runtime changes, imports, database mutation, production action, or `LIVE01` touch are part of this review.

## 2. Source documents reviewed

Source chain:

- `docs/control/QUESTION_BANK_V2_PREPARATION_PLAN.md`
- `docs/control/QUESTION_BANK_V2_BLUEPRINT.md`
- `docs/control/QUESTION_BANK_V2_DRAFT_LIST.md`

Current committed baseline:

- `bb309bd Add question bank v2 preparation plan`
- `ac1e2af Add question bank v2 blueprint`
- `631d65c Add question bank v2 draft list`

## 3. High-level review verdict

Verdict: `READY_FOR_XLSX_DRAFT_WITH_EDITORIAL_WORK`.

The structure is strong enough to become an authoring spreadsheet, but not every row should be treated as final content.

Strengths:

- Clear 48-slot structure.
- Round codes match the blueprint.
- Visual/image target is realistic.
- Manual audio is safely offline/host-operated.
- Court and Duel are separated from main quiz flow.
- Reserve coverage is sufficient.
- No final answers/options were prematurely invented.

Main editing needs:

- Convert prompt ideas into real playable prompts.
- Choose 10-12 image slots from 13 candidates.
- Confirm local/Kurgan/Sobranie references with Victor.
- Confirm music/audio source/legal plan.
- Decide whether operational/onboarding questions belong in the actual game or only host script.
- Keep Court/Duel questions short and low ambiguity.

## 4. Recommended XLSX first-pass selection

Recommended first XLSX draft shape:

| Bucket | Count | Recommendation |
| --- | ---: | --- |
| Core playable rows | 36 | Move slots 1-36 into XLSX draft, but rewrite prompts/options. |
| Reserve rows | 10-12 | Move selected reserve slots 37-48 into reserve section. |
| Image rows | 10-12 | Select from visual candidates after asset availability check. |
| Manual audio rows | 3 | Use 3 rows first; keep 1 reserve audio fallback. |
| Court rows | 6 + 1 reserve | Keep robust and mostly non-media. |
| Duel rows | 2-3 | Keep as reserve/core-flex, not mandatory flow. |

Practical first-pass decision:

- Include all 48 rows in the XLSX authoring draft as candidates.
- Mark reserve rows explicitly with `tags=reserve`.
- Do not import all 48 as live sequence until final curation.
- Use the spreadsheet to write final options/correct answers, not this Markdown file.

## 5. Slot classification

### A. Good candidates for first-pass XLSX authoring

These slots have clear purpose and should move forward first:

| question_code | reason | next action |
| --- | --- | --- |
| `v2_q001_oath_table` | Fast onboarding/warmup. | Write concise true/false or single-choice. |
| `v2_q002_gold_rhythm` | Reinforces gold without changing economy. | Write simple choices. |
| `v2_q003_table_object_closeup` | Safe first image. | Find/crop readable image. |
| `v2_q004_house_roles` | Reinforces role clarity. | Keep short; avoid feeling like rules exam. |
| `v2_q007_old_tool` | Strong visual recognition. | Source image and fact-check. |
| `v2_q009_ad_fragment` | Good image/table discussion. | Rights/source approval required. |
| `v2_q012_service_signal` | Supports Diplomacy behavior. | Rewrite as social-reading question. |
| `v2_q015_origin_story` | Main quiz material. | Write strong options. |
| `v2_q016_food_closeup` | Good bar-energy visual. | Source image; avoid tiny detail. |
| `v2_q017_manual_audio_mood` | Good manual audio moment. | Confirm source and fallback. |
| `v2_q019_object_reveal` | Strong staged reveal slot. | Pair prompt and reveal image. |
| `v2_q021_pattern_trap` | Good visual trap if readable. | Test far-table readability. |
| `v2_q023_court_truth` | Court-safe core. | Write low-ambiguity prompt. |
| `v2_q026_court_food_fact` | Robust Court question. | Keep non-controversial. |
| `v2_q029_final_plain` | Needed final-safe row. | Write strong decisive question. |
| `v2_q030_final_image_choice` | Strong final image if smoke-passed. | Use only after asset proof. |
| `v2_q033_duel_fast_object` | Duel-ready fast row. | Keep very short. |
| `v2_q034_duel_true_false` | Good Duel fallback. | Keep no ambiguity. |

### B. Needs Victor/local approval before final wording

| question_code | approval needed | why |
| --- | --- | --- |
| `v2_q011_map_mark` | Local/Kurgan/Sobranie reference. | Avoid wrong or forced local flavor. |
| `v2_q020_local_placeholder` | Exact local fact. | Must be true and suitable for guests. |
| `v2_q043_reserve_local` | Reserve local reference. | Same local approval needed. |
| `v2_q013_drink_shape` | Alcohol/non-alcohol tone. | Keep compatible with mixed audience and 18+ policy. |
| `v2_q025_court_gold_choice` | Game economy interpretation. | Must not imply automatic gold effects. |
| `v2_q028_court_final_argument` | Role/Court usage. | Decide if this is question or host prompt. |
| `v2_q032_final_house_choice` | Strategy/final tone. | Decide if scoring question or discussion prompt. |

### C. Needs media/asset work before XLSX can be useful

| question_code | media work | risk |
| --- | --- | --- |
| `v2_q003_table_object_closeup` | Photo/crop. | Must be easy warmup. |
| `v2_q007_old_tool` | Public-safe image. | Source/rights. |
| `v2_q009_ad_fragment` | Old ad/poster crop. | Rights/source risk. |
| `v2_q011_map_mark` | Local/map/sign image. | Local accuracy. |
| `v2_q014_hidden_detail` | Delayed clue image. | Could be too hard. |
| `v2_q016_food_closeup` | Food close-up. | Must not be gross/ambiguous. |
| `v2_q019_object_reveal` | Reveal image. | Needs exact pairing with explanation. |
| `v2_q021_pattern_trap` | Pattern image. | Readability from far tables. |
| `v2_q024_court_evidence_image` | Court evidence image. | Must not cause dispute. |
| `v2_q027_court_symbol_reveal` | Reveal symbol/image. | Needs smoke. |
| `v2_q030_final_image_choice` | Final image. | Use only if polished. |
| `v2_q035_duel_visual` | Fast duel image. | Likely cut unless very clear. |
| `v2_q039_reserve_visual` | Reserve image. | Optional. |
| `v2_q047_reserve_image_reveal` | Reserve reveal image. | Optional. |

### D. Consider cutting or moving to host script, not XLSX

These are useful ideas but may not be best as scored/imported questions:

| question_code | recommendation | reason |
| --- | --- | --- |
| `v2_q006_phone_stage` | Move to host/operator script unless rewritten. | Too operational for scored question. |
| `v2_q028_court_final_argument` | Consider manual host prompt. | May be better as Court procedure. |
| `v2_q036_host_manual_break` | Keep outside import unless needed. | Pacing moment, not a normal question. |
| `v2_q048_reserve_host_choice` | Keep outside import unless needed. | Emergency host fallback. |

## 6. Visual/image review

Current draft has 13 image candidates, which is healthy because the target is 10-12.

Recommended first visual set:

| priority | question_code | reason |
| ---: | --- | --- |
| 1 | `v2_q003_table_object_closeup` | Easy image warmup. |
| 2 | `v2_q007_old_tool` | Strong visual recognition. |
| 3 | `v2_q009_ad_fragment` | Good discussion if rights are safe. |
| 4 | `v2_q014_hidden_detail` | Adds staged-timer variety. |
| 5 | `v2_q016_food_closeup` | Fits bar/game atmosphere. |
| 6 | `v2_q019_object_reveal` | Good reveal-stage moment. |
| 7 | `v2_q021_pattern_trap` | Strong if readable. |
| 8 | `v2_q024_court_evidence_image` | Court flavor, but must be simple. |
| 9 | `v2_q027_court_symbol_reveal` | Reveal image, low clue dependency. |
| 10 | `v2_q030_final_image_choice` | Final visual if excellent. |
| 11 | `v2_q011_map_mark` | Use only after local approval. |
| 12 | `v2_q039_reserve_visual` | Reserve image. |

Likely cut or reserve:

- `v2_q035_duel_visual` unless the image is instantly obvious.
- `v2_q047_reserve_image_reveal` unless extra asset is already easy.

Image readiness rule:

- A row should not become final if the image cannot be sourced, cropped, and TV-smoke-tested.

## 7. Manual music/audio review

Current draft has 4 manual audio candidates.

Recommended live-game use:

| question_code | recommendation |
| --- | --- |
| `v2_q017_manual_audio_mood` | Keep as primary manual audio question. |
| `v2_q022_manual_audio_instrument` | Keep if source/fallback is simple. |
| `v2_q031_final_manual_audio` | Use only if final pacing needs music. |
| `v2_q042_reserve_audio_fallback` | Keep as reserve only. |

Operational rule:

- Manual audio should be host-operated outside the app.
- XLSX rows should use `media_type=none` and `tags=manual_audio`.
- Do not use runtime `media_type=audio` for this game.
- Do not include copyrighted song titles or lyrics in public-facing prompts unless source/legal plan is approved.

## 8. Court review

Court has enough material, but needs strict editorial control.

Keep Court questions:

- short;
- clear;
- low ambiguity;
- explainable by host;
- safe if TV/media fails.

Court rows to prioritize:

- `v2_q023_court_truth`
- `v2_q025_court_gold_choice`
- `v2_q026_court_food_fact`
- `v2_q028_court_final_argument` if rewritten as manual/role prompt
- `v2_q041_reserve_court_safe`

Use Court image rows only if smoke-passed:

- `v2_q024_court_evidence_image`
- `v2_q027_court_symbol_reveal`

Avoid:

- real people accusations;
- toxic public claims;
- hidden math arguments;
- questions that imply automatic gold/resource changes.

## 9. Duel review

Duel rows are correctly kept as reserve/core-flex, not a mandatory engine.

Good Duel candidates:

- `v2_q033_duel_fast_object`
- `v2_q034_duel_true_false`

Risky Duel candidate:

- `v2_q035_duel_visual`, because Duel questions must be instantly understandable.

Duel boundary:

- No Duel V2 question-before-move engine.
- No full tic-tac-toe runtime changes.
- Existing Duel V1.1 challenge/resolve/draw-replay remains the boundary.

## 10. Editorial risk register

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Too many operational/rules questions feel like training | Medium | Move some into host script or player guide. |
| Image questions depend on tiny details | High | TV readability review before import. |
| Local references are inaccurate or forced | Medium | Victor/local approval before final wording. |
| Audio source is not ready or legally unclear | High | Manual-only, source approval, text fallback. |
| Court questions become arguments | Medium | Use short factual prompts and host authority. |
| Duel question takes too long to parse | Medium | Use only fast plain rows. |
| Reserve rows accidentally imported as core | Medium | Use `tags=reserve` and separate review. |
| XLSX authoring invents answers too early | Medium | Require fact-check before `approved`. |

## 11. Recommended status updates before XLSX

Suggested draft-list status changes for authoring:

| status | rows |
| --- | --- |
| `needs_write` | Most plain/core rows after approval. |
| `needs_media` | All selected image rows until asset exists. |
| `needs_review` | Local, Court, strategy, and manual audio rows. |
| `reserve` | Reserve rows 37-48 and optional cut rows. |
| `approved` | Use only after final prompt/options/correct answer/fact check. |

Do not mark rows `approved` in XLSX until:

- final prompt exists;
- options exist if needed;
- correct answer exists;
- explanation exists;
- fact/source is checked;
- media exists if required;
- Victor/operator has approved tone and local references.

## 12. Recommended next XLSX authoring columns

Use the preparation-plan columns plus operational review helpers:

```text
section
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
round_code
tags
review_status
source_note
host_note
asset_status
```

Recommended `review_status` values:

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

## 13. Open decisions for Victor

Before XLSX writing becomes final, Victor should decide:

- Should onboarding/phone/rules ideas be scored questions or host-script material?
- Which local/Kurgan/Sobranie references are allowed?
- Should visual target be 10, 11, or 12 image questions?
- Should manual audio target be 3 or 4 moments?
- Is music part of scoring or only atmosphere?
- Should Court be quiz-heavy or drama/host-heavy?
- Should Duel get dedicated rows or only reserve rows?
- Should any alcohol/bar-culture questions avoid 18+ ambiguity entirely?
- Who owns image rights/source approval?
- Who owns playlist/device/volume check?

## 14. Next artifact recommendation

Recommended next artifact:

```text
docs/control/QUESTION_BANK_V2_XLSX_AUTHORING_SPEC.md
```

Purpose:

- Convert approved slots into exact spreadsheet rows.
- Define final columns.
- Define status workflow.
- Mark which rows are core vs reserve.
- Mark selected visual rows.
- Mark manual audio rows with `tags=manual_audio`.
- Keep import safety visible: `dry_run=true`, `clear_existing=false`, no `LIVE01`.

Do not create/import XLSX until this review is accepted.
