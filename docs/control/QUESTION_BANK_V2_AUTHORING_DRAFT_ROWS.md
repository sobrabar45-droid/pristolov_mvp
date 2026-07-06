# Question Bank V2 Authoring Draft Rows

## 1. Purpose

This document is a Markdown preview of the future `questions` XLSX sheet for Question Bank V2.

It is close to spreadsheet rows, but it is still human-readable Markdown.

It is not an XLSX file. It is not an import file. It does not contain final answer options or final correct answers.

Use this document to review row shape, section mapping, round codes, media flags, reserve/core markers, and safety statuses before creating `question_bank_v2_authoring_draft.xlsx`.

## 2. Safety scope

This draft does not perform or authorize:

- question import;
- DB mutation;
- production action;
- `LIVE01` action;
- migrations;
- `clear_existing=true`;
- runtime audio;
- deployment.

All rows currently have:

```text
safe_to_import=no
```

Manual audio rows use:

```text
media_type=none
tags=manual_audio
```

Image rows use draft `media_ref` values only. Assets are not yet copied, approved, or smoke-tested.

## 3. Column preview

The future XLSX `questions` sheet should use these columns:

```text
slot
section
round_code
question_code
question_type
question_draft
media_type
media_ref
difficulty
tags
review_status
asset_status
is_core
is_reserve
needs_victor
safe_to_import
host_note
```

This preview intentionally omits final columns for `option_a`, `option_b`, `option_c`, `option_d`, `correct_answer`, and `explanation` because those must be written and fact-checked later in the actual authoring pass.

## 4. Authoring draft rows

| slot | section | round_code | question_code | question_type | question_draft | media_type | media_ref | difficulty | tags | review_status | asset_status | is_core | is_reserve | needs_victor | safe_to_import | host_note |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | warmup | `v2_warmup_oath` | `v2_q001_oath_table` | `true_false` | Fast opener about why a House should listen to host instructions and role signals before acting. | none |  | easy | warmup | needs_write | none | yes | no | no | no | Convert into concise true/false. |
| 2 | warmup | `v2_warmup_oath` | `v2_q002_gold_rhythm` | `single_choice` | Simple question about when gold matters during requests, House choices, and table strategy. | none |  | easy | economy | needs_write | none | yes | no | no | no | Reinforce gold without changing economy rules. |
| 3 | warmup | `v2_warmup_oath` | `v2_q003_table_object_closeup` | `single_choice` | Players identify a familiar table or bar object from a close-up image. | image | `v2_q003_table_object_closeup` | easy | image_clue,needs_image | needs_media | planned | yes | no | no | no | First low-stakes image; must be readable from far tables. |
| 4 | warmup | `v2_warmup_oath` | `v2_q004_house_roles` | `single_choice` | Question asks which House role is best suited to negotiate with another House. | none |  | easy | role_prompt | needs_write | none | yes | no | no | no | Keep playful; avoid feeling like a rules test. |
| 5 | warmup | `v2_warmup_oath` | `v2_q005_food_myth` | `single_choice` | Light food misconception question with a surprising but safe explanation. | none |  | easy | food | idea | none | yes | no | no | no | Needs concrete fact later. |
| 6 | warmup | `v2_warmup_oath` | `v2_q006_phone_stage` | `single_choice` | Question about what to do when phone, TV, and host timing feel out of sync. | none |  | easy | needs_host_note | needs_victor | none | yes | no | yes | no | Consider moving to host script instead of scored question. |
| 7 | main_1 | `v2_signs_objects` | `v2_q007_old_tool` | `single_choice` | Players identify what old tool or object was used for. | image | `v2_q007_old_tool` | medium | image_clue,needs_image | needs_media | planned | yes | no | no | no | Strong visual recognition slot; source/rights check needed. |
| 8 | main_1 | `v2_signs_objects` | `v2_q008_menu_symbol` | `single_choice` | Question about meaning of a common menu, bar, or service symbol. | none |  | easy | food,bar_culture | idea | none | yes | no | no | no | Can use venue-inspired but not false brand claim. |
| 9 | main_1 | `v2_signs_objects` | `v2_q009_ad_fragment` | `single_choice` | Players infer product category from a cropped old-style advertisement or poster fragment. | image | `v2_q009_ad_fragment` | medium | image_clue,needs_image,needs_fact_check | needs_media | planned | yes | no | no | no | Rights/source risk; do not finalize without approval. |
| 10 | main_1 | `v2_signs_objects` | `v2_q010_false_friend_object` | `single_choice` | Object whose name or purpose is often mistaken; players choose real use. | none |  | medium | object_trivia | needs_write | none | yes | no | no | no | Could become image if asset appears. |
| 11 | main_1 | `v2_signs_objects` | `v2_q011_map_mark` | `single_choice` | Local map/sign/orientation clue question, pending exact Kurgan/Sobranie reference. | image | `v2_q011_map_mark` | medium | image_clue,local_reference,needs_victor,needs_image | needs_victor | planned | yes | no | yes | no | Needs Victor/local approval before wording. |
| 12 | main_1 | `v2_signs_objects` | `v2_q012_service_signal` | `single_choice` | Social-reading question: what table behavior signals a House is ready to negotiate. | none |  | easy | diplomacy | needs_write | none | yes | no | no | no | Supports Diplomacy without adding mechanics. |
| 13 | main_1 | `v2_signs_objects` | `v2_q013_drink_shape` | `single_choice` | Question about how glass/serving shape can change perception of a drink. | none |  | medium | bar_culture,needs_victor | needs_victor | none | yes | no | yes | no | Keep non-alcohol or 18+ safe. |
| 14 | main_1 | `v2_signs_objects` | `v2_q014_hidden_detail` | `single_choice` | Delayed image clue where players infer answer from a broad visual detail. | image | `v2_q014_hidden_detail` | hard | image_after_timer,needs_image | needs_media | planned | yes | no | no | no | Avoid tiny details; TV readability required. |
| 15 | main_2 | `v2_stories_tricks` | `v2_q015_origin_story` | `single_choice` | Players choose the most plausible origin story of a common object or ritual. | none |  | medium | history,needs_fact_check | needs_write | none | yes | no | no | no | Needs strong options and fact check. |
| 16 | main_2 | `v2_stories_tricks` | `v2_q016_food_closeup` | `single_choice` | Food texture or ingredient close-up; players infer dish/category. | image | `v2_q016_food_closeup` | medium | image_clue,needs_image | needs_media | planned | yes | no | no | no | Good bar-energy visual; avoid gross ambiguity. |
| 17 | main_2 | `v2_stories_tricks` | `v2_q017_manual_audio_mood` | `single_choice` | Host plays short manual audio; players identify mood, era, or context. | none |  | medium | manual_audio,needs_host_note,needs_victor | needs_victor | planned | yes | no | yes | no | Manual/offline only; source/legal/fallback required. |
| 18 | main_2 | `v2_stories_tricks` | `v2_q018_social_bluff` | `single_choice` | Strategy/social question about which negotiation move most likely signals a bluff. | none |  | medium | diplomacy | idea | none | yes | no | no | no | Keep playful, not accusatory. |
| 19 | main_2 | `v2_stories_tricks` | `v2_q019_object_reveal` | `single_choice` | Text-first question; reveal image explains unexpected object or fact after answer. | image | `v2_q019_object_reveal` | medium | image_reveal,needs_image | needs_media | planned | yes | no | no | no | Strong staged reveal candidate. |
| 20 | main_2 | `v2_stories_tricks` | `v2_q020_local_placeholder` | `single_choice` | Local/Kurgan-flavored fact question pending exact approved reference. | none |  | medium | local_reference,needs_victor,needs_fact_check | needs_victor | none | yes | no | yes | no | Needs local truth check before wording. |
| 21 | main_2 | `v2_stories_tricks` | `v2_q021_pattern_trap` | `single_choice` | Pattern/arrangement image; players identify what changed or what it is used for. | image | `v2_q021_pattern_trap` | hard | image_clue,needs_image | needs_media | planned | yes | no | no | no | Must be visible from far tables. |
| 22 | main_2 | `v2_stories_tricks` | `v2_q022_manual_audio_instrument` | `single_choice` | Host plays/describes a short sound; players identify instrument family or setting. | none |  | medium | manual_audio,needs_host_note,needs_victor | needs_victor | planned | yes | no | yes | no | Manual/offline only; text fallback required. |
| 23 | court | `v2_court_trial` | `v2_q023_court_truth` | `single_choice` | Short Court-safe factual question that can settle public tension cleanly. | none |  | medium | court_safe,needs_fact_check | needs_fact_check | none | yes | no | no | no | Keep low ambiguity. |
| 24 | court | `v2_court_trial` | `v2_q024_court_evidence_image` | `single_choice` | Image presented as Court evidence; players infer what it most likely proves. | image | `v2_q024_court_evidence_image` | medium | court_safe,image_clue,needs_image | needs_media | planned | yes | no | no | no | Use only if simple and TV-smoked. |
| 25 | court | `v2_court_trial` | `v2_q025_court_gold_choice` | `single_choice` | Court strategy question about safe House decision when gold is limited. | none |  | medium | court_safe,economy,needs_victor | needs_victor | none | yes | no | yes | no | Must not imply automatic gold/resource mutation. |
| 26 | court | `v2_court_trial` | `v2_q026_court_food_fact` | `single_choice` | Short non-controversial food/bar fact suitable for Court. | none |  | easy | court_safe,food,needs_fact_check | needs_fact_check | none | yes | no | no | no | Avoid alcohol/legal ambiguity. |
| 27 | court | `v2_court_trial` | `v2_q027_court_symbol_reveal` | `single_choice` | Court question where reveal image explains why the answer was true. | image | `v2_q027_court_symbol_reveal` | medium | court_safe,image_reveal,needs_image | needs_media | planned | yes | no | no | no | Reveal image, not clue-critical. |
| 28 | court | `v2_court_trial` | `v2_q028_court_final_argument` | `free_text` | Role/Court prompt about who should speak for a House in a public dispute. | none |  | easy | court_safe,role_prompt,needs_victor | needs_victor | none | yes | no | yes | no | Consider manual host prompt instead of import. |
| 29 | final | `v2_final_word` | `v2_q029_final_plain` | `single_choice` | Clear final-round general culture question with low ambiguity. | none |  | medium | final_safe,needs_fact_check | needs_write | none | yes | no | no | no | Needs strong explanation. |
| 30 | final | `v2_final_word` | `v2_q030_final_image_choice` | `single_choice` | Fully tested final image clue for decisive tension. | image | `v2_q030_final_image_choice` | hard | final_safe,image_clue,needs_image | needs_media | planned | yes | no | no | no | Use only if excellent and smoke-passed. |
| 31 | final | `v2_final_word` | `v2_q031_final_manual_audio` | `single_choice` | Optional final manual audio/mood clue with text fallback. | none |  | medium | final_safe,manual_audio,needs_victor,needs_host_note | needs_victor | planned | yes | no | yes | no | Optional; no runtime audio. |
| 32 | final | `v2_final_word` | `v2_q032_final_house_choice` | `free_text` | Strategic final prompt about risk vs safe points for a House. | none |  | medium | final_safe,role_prompt,needs_victor | needs_victor | none | yes | no | yes | no | Decide if scored question or host discussion. |
| 33 | duel | `v2_reserve` | `v2_q033_duel_fast_object` | `single_choice` | Very short duel-ready question about identifying familiar object or fact. | none |  | easy | duel_ready | needs_write | none | yes | no | no | no | Keep extremely short. |
| 34 | duel | `v2_reserve` | `v2_q034_duel_true_false` | `true_false` | Fast true/false Duel question with immediate understandable answer. | none |  | easy | duel_ready | needs_write | none | yes | no | no | no | No ambiguity. |
| 35 | duel | `v2_reserve` | `v2_q035_duel_visual` | `single_choice` | Optional image-based Duel question if the image is instantly readable. | image | `v2_q035_duel_visual` | medium | duel_ready,image_clue,needs_image | needs_media | planned | yes | no | no | no | Likely cut unless very clear. |
| 36 | host_manual | `v2_reserve` | `v2_q036_host_manual_break` | `free_text` | Host manual pacing moment for tie, pause, or table reset. | none |  | easy | host_manual,needs_host_note,needs_victor | needs_victor | none | yes | no | yes | no | Probably not imported. |
| 37 | reserve | `v2_reserve` | `v2_q037_reserve_plain_food` | `single_choice` | Plain reserve food/drink culture question with no media dependency. | none |  | easy | reserve,food | reserve | none | no | yes | no | no | Backup if media fails. |
| 38 | reserve | `v2_reserve` | `v2_q038_reserve_history` | `single_choice` | Strange everyday-history reserve question. | none |  | medium | reserve,needs_fact_check | reserve | none | no | yes | no | no | Needs fact check before use. |
| 39 | reserve | `v2_reserve` | `v2_q039_reserve_visual` | `single_choice` | Backup image clue if another visual question is rejected. | image | `v2_q039_reserve_visual` | medium | reserve,image_clue,needs_image | reserve | planned | no | yes | no | no | Optional reserve asset. |
| 40 | reserve | `v2_reserve` | `v2_q040_reserve_social` | `single_choice` | Reserve question about negotiation/social behavior with no personal accusation. | none |  | medium | reserve,diplomacy | reserve | none | no | yes | no | no | Supports Diplomacy vibe. |
| 41 | reserve | `v2_reserve` | `v2_q041_reserve_court_safe` | `single_choice` | Court-safe reserve question for tie or disputed moment. | none |  | easy | reserve,court_safe | reserve | none | no | yes | no | no | Robust fallback. |
| 42 | reserve | `v2_reserve` | `v2_q042_reserve_audio_fallback` | `single_choice` | Backup manual audio moment with text-only fallback. | none |  | easy | reserve,manual_audio,needs_victor,needs_host_note | reserve | planned | no | yes | yes | no | Use only if source/device/fallback are ready. |
| 43 | reserve | `v2_reserve` | `v2_q043_reserve_local` | `single_choice` | Reserve local/Kurgan/Sobranie placeholder pending approval. | none |  | medium | reserve,local_reference,needs_victor | reserve | none | no | yes | yes | no | Do not finalize without local check. |
| 44 | reserve | `v2_reserve` | `v2_q044_reserve_object` | `single_choice` | Reserve object trivia without image dependency. | none |  | medium | reserve,object_trivia | reserve | none | no | yes | no | no | Can become image later if needed. |
| 45 | reserve | `v2_reserve` | `v2_q045_reserve_final_safe` | `single_choice` | Clean final/tie reserve question with no media and no ambiguity. | none |  | hard | reserve,final_safe | reserve | none | no | yes | no | no | For final backup. |
| 46 | reserve | `v2_reserve` | `v2_q046_reserve_role` | `single_choice` | Reserve role-understanding question for player clarity. | none |  | easy | reserve,role_prompt | reserve | none | no | yes | no | no | Useful if table confusion appears. |
| 47 | reserve | `v2_reserve` | `v2_q047_reserve_image_reveal` | `single_choice` | Backup reveal image explaining a surprising answer after reveal. | image | `v2_q047_reserve_image_reveal` | medium | reserve,image_reveal,needs_image | reserve | planned | no | yes | no | no | Use only if asset is easy and ready. |
| 48 | host_manual | `v2_reserve` | `v2_q048_reserve_host_choice` | `free_text` | Host-choice emergency pacing, tie, or failed-media replacement moment. | none |  | easy | reserve,host_manual,needs_host_note | reserve | none | no | yes | yes | no | Manual only; likely not imported. |

## 5. Visual row candidates

Image rows in this preview:

| question_code | media_ref | status | recommendation |
| --- | --- | --- | --- |
| `v2_q003_table_object_closeup` | `v2_q003_table_object_closeup` | planned | keep |
| `v2_q007_old_tool` | `v2_q007_old_tool` | planned | keep |
| `v2_q009_ad_fragment` | `v2_q009_ad_fragment` | planned | keep if rights safe |
| `v2_q011_map_mark` | `v2_q011_map_mark` | planned | use only after local approval |
| `v2_q014_hidden_detail` | `v2_q014_hidden_detail` | planned | keep if readable |
| `v2_q016_food_closeup` | `v2_q016_food_closeup` | planned | keep |
| `v2_q019_object_reveal` | `v2_q019_object_reveal` | planned | keep |
| `v2_q021_pattern_trap` | `v2_q021_pattern_trap` | planned | keep if readable |
| `v2_q024_court_evidence_image` | `v2_q024_court_evidence_image` | planned | Court smoke required |
| `v2_q027_court_symbol_reveal` | `v2_q027_court_symbol_reveal` | planned | Court smoke required |
| `v2_q030_final_image_choice` | `v2_q030_final_image_choice` | planned | use only if excellent |
| `v2_q035_duel_visual` | `v2_q035_duel_visual` | planned | likely cut/reserve |
| `v2_q039_reserve_visual` | `v2_q039_reserve_visual` | planned | reserve |
| `v2_q047_reserve_image_reveal` | `v2_q047_reserve_image_reveal` | planned | reserve |

This preview intentionally contains more than the 10-12 target, so weak assets can be cut before XLSX finalization.

## 6. Manual audio rows

Manual audio rows in this preview:

| question_code | media_type | tags | recommendation |
| --- | --- | --- | --- |
| `v2_q017_manual_audio_mood` | `none` | `manual_audio` | primary manual audio moment |
| `v2_q022_manual_audio_instrument` | `none` | `manual_audio` | primary if source/fallback is simple |
| `v2_q031_final_manual_audio` | `none` | `manual_audio` | optional final moment |
| `v2_q042_reserve_audio_fallback` | `none` | `manual_audio` | reserve fallback |

Rules:

- no runtime audio;
- no `media_type=audio`;
- host/operator plays audio manually;
- every audio row needs text fallback;
- source/legal/device readiness must be checked later.

## 7. Rows likely not imported

These rows may remain as planning/host rows instead of imported questions:

| question_code | reason |
| --- | --- |
| `v2_q006_phone_stage` | Could be host script rather than scored question. |
| `v2_q028_court_final_argument` | Could be Court host prompt rather than imported row. |
| `v2_q036_host_manual_break` | Pacing/tie/reset moment, not normal question. |
| `v2_q048_reserve_host_choice` | Emergency host fallback, not normal question. |

Keep `safe_to_import=no` unless Victor explicitly approves converting any of these into real rows.

## 8. Next step

Recommended next step:

1. Review this Markdown row preview.
2. Decide which rows should be cut before XLSX.
3. Decide final selected image rows.
4. Decide final manual audio count.
5. Then create `question_bank_v2_authoring_draft.xlsx` as a local authoring artifact.

Do not run import after XLSX creation. The first import-related task must be dry-run only:

```text
dry_run=true
clear_existing=false
target_round_code=v2_commercial_test_round
no LIVE01
```
