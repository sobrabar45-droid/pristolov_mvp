# Question Bank V2 Draft List

## 1. Purpose

This document is a human-readable draft list for the next commercial `приСтолов` question bank.

It is not an XLSX file yet. It is not final wording. It does not contain final answer options or final correct answers.

Use this draft to approve:

- game structure;
- topic balance;
- round placement;
- visual/image workload;
- manual music/audio workload;
- Court and Duel readiness;
- reserve coverage before XLSX authoring or import.

No import is performed from this document. No database mutation is intended.

## 2. Draft list rules

Planning targets:

- 48 authored candidate slots.
- 36 expected core/flex playable slots.
- 10-12 reserve slots.
- Visual target: 10-12 image questions.
- Manual music/audio target: 3-4 moments.
- No runtime audio dependency.
- No import from this draft.
- No `LIVE01` touch.

Status values:

- `idea` - rough concept only.
- `needs_write` - concept approved enough to write final prompt/options.
- `needs_media` - needs image/audio/source work.
- `needs_review` - needs Victor/editorial check.
- `approved` - ready to move into XLSX draft after final wording.
- `reserve` - backup/tie/fallback slot.

Draft conventions:

- `visual_needed=yes` means an image should be planned with `media_type=image` later.
- `media_ref_draft` is a proposed slug only, not a final filename.
- `manual_audio=yes` means host/operator plays audio outside the app.
- `manual_audio=yes` should later become `tags=manual_audio`, not runtime `media_type=audio`.
- Final answer options and final correct answers are intentionally not included here.

## 3. Question draft table

| slot | round_code | question_code | question_type | theme | draft_prompt_idea | visual_needed | media_ref_draft | manual_audio | difficulty | status | notes |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `v2_warmup_oath` | `v2_q001_oath_table` | `plain_text` | opening / table culture | Quick true/false about why teams should listen to both host and House roles before acting. | no |  | no | easy | needs_write | Warmup confidence question; no trick. |
| 2 | `v2_warmup_oath` | `v2_q002_gold_rhythm` | `plain_text` | gold / economy | Simple multiple-choice idea about when gold matters: requests, choices, and House decisions. | no |  | no | easy | needs_write | Reinforces game economy without backend terms. |
| 3 | `v2_warmup_oath` | `v2_q003_table_object_closeup` | `image_clue` | bar object / visual trap | Show a close-up of a familiar table/bar object and ask what it is from the wider context. | yes | `v2_q003_table_object_closeup` | no | easy | needs_media | First low-stakes image; must be readable on TV. |
| 4 | `v2_warmup_oath` | `v2_q004_house_roles` | `role_prompt` | roles | Ask which role is best suited to negotiate with another House. | no |  | no | easy | needs_write | Reinforces `Дипломат`. |
| 5 | `v2_warmup_oath` | `v2_q005_food_myth` | `plain_text` | food myth | Light bar-food misconception question with a surprising but safe answer. | no |  | no | easy | idea | Avoid obscure nutrition dispute. |
| 6 | `v2_warmup_oath` | `v2_q006_phone_stage` | `plain_text` | player behavior | Quick question about what players should do when phone and TV disagree: follow host / refresh calmly. | no |  | no | easy | needs_review | Useful onboarding, maybe too operational. |
| 7 | `v2_signs_objects` | `v2_q007_old_tool` | `image_clue` | old object | Show an old tool/object and ask what everyday task it helped solve. | yes | `v2_q007_old_tool` | no | medium | needs_media | Strong visual recognition slot. |
| 8 | `v2_signs_objects` | `v2_q008_menu_symbol` | `plain_text` | signs / symbols | Ask about meaning of a common menu/bar symbol or marking. | no |  | no | easy | idea | Could use local menu inspiration, not exact brand claim. |
| 9 | `v2_signs_objects` | `v2_q009_ad_fragment` | `image_clue` | old advertisement | Show a cropped old-style ad/poster fragment and ask what product category it likely sells. | yes | `v2_q009_ad_fragment` | no | medium | needs_media | Rights/source check required. |
| 10 | `v2_signs_objects` | `v2_q010_false_friend_object` | `plain_text` | visual thinking | A question about an object whose name/purpose is often mistaken. | no |  | no | medium | needs_write | Can become image later if asset found. |
| 11 | `v2_signs_objects` | `v2_q011_map_mark` | `image_clue` | map / local placeholder | Show a simple map/sign fragment and ask what clue helps orient people. | yes | `v2_q011_map_mark` | no | medium | needs_media | Kurgan/Sobranie placeholder; approve local reference. |
| 12 | `v2_signs_objects` | `v2_q012_service_signal` | `plain_text` | social reading | Ask what behavior at a table most clearly signals a House is ready to negotiate. | no |  | no | easy | needs_review | Supports Diplomacy. |
| 13 | `v2_signs_objects` | `v2_q013_drink_shape` | `plain_text` | drink culture | Ask why a glass or serving shape might change perception of a drink. | no |  | no | medium | idea | Keep non-alcohol version possible. |
| 14 | `v2_signs_objects` | `v2_q014_hidden_detail` | `image_after_timer` | visual trap | Show an image only after timer/open stage or as a delayed clue; ask players to infer from a broad detail. | yes | `v2_q014_hidden_detail` | no | hard | needs_media | Must not rely on tiny text. |
| 15 | `v2_stories_tricks` | `v2_q015_origin_story` | `plain_text` | strange history | Ask which origin story of a common object/ritual is most plausible. | no |  | no | medium | needs_write | General culture slot. |
| 16 | `v2_stories_tricks` | `v2_q016_food_closeup` | `image_clue` | food visual | Show close-up of food texture/ingredient and ask what dish/category it suggests. | yes | `v2_q016_food_closeup` | no | medium | needs_media | Good bar-energy image. |
| 17 | `v2_stories_tricks` | `v2_q017_manual_audio_mood` | `manual_audio` | music mood | Host plays a short instrumental/mood fragment; players identify era/mood/context from choices. | no |  | yes | medium | needs_review | No song names or lyrics in draft; source/legal TBD. |
| 18 | `v2_stories_tricks` | `v2_q018_social_bluff` | `plain_text` | strategy / social reading | Ask which negotiation move is most likely a bluff in a House game context. | no |  | no | medium | idea | Supports table talk. |
| 19 | `v2_stories_tricks` | `v2_q019_object_reveal` | `image_reveal` | reveal moment | Ask text-first, then reveal image after answer to explain the unexpected object/fact. | yes | `v2_q019_object_reveal` | no | medium | needs_media | Good staged reveal candidate. |
| 20 | `v2_stories_tricks` | `v2_q020_local_placeholder` | `plain_text` | local / Kurgan placeholder | A local/Kurgan-flavored fact question with generic placeholder until Victor approves exact reference. | no |  | no | medium | needs_review | Needs local truth check. |
| 21 | `v2_stories_tricks` | `v2_q021_pattern_trap` | `image_clue` | visual pattern | Show a pattern/arrangement and ask what changed or what it is used for. | yes | `v2_q021_pattern_trap` | no | hard | needs_media | Make visible from far tables. |
| 22 | `v2_stories_tricks` | `v2_q022_manual_audio_instrument` | `music_knowledge` | music / instrument | Host plays or describes a short sound; players identify instrument family or performance setting. | no |  | yes | medium | needs_review | Manual/offline only; fallback text needed. |
| 23 | `v2_court_trial` | `v2_q023_court_truth` | `court_question` | Court / public argument | Short Court-safe question with clear answer that can settle a public tension moment. | no |  | no | medium | needs_write | Keep robust and unambiguous. |
| 24 | `v2_court_trial` | `v2_q024_court_evidence_image` | `image_clue` | Court evidence | Show an image as "evidence" and ask what it most likely proves. | yes | `v2_q024_court_evidence_image` | no | medium | needs_media | Only if TV-smoked. |
| 25 | `v2_court_trial` | `v2_q025_court_gold_choice` | `court_question` | gold / ethics | Ask which House decision is strategically safest when gold is limited. | no |  | no | medium | needs_review | No actual gold mutation from question. |
| 26 | `v2_court_trial` | `v2_q026_court_food_fact` | `court_question` | food/drink fact | Short, non-controversial food/bar fact suitable for audience judgement. | no |  | no | easy | needs_write | Avoid alcohol/legal ambiguity. |
| 27 | `v2_court_trial` | `v2_q027_court_symbol_reveal` | `image_reveal` | symbol reveal | Court question where reveal image explains why the answer was true. | yes | `v2_q027_court_symbol_reveal` | no | medium | needs_media | Reveal image, not clue-critical. |
| 28 | `v2_court_trial` | `v2_q028_court_final_argument` | `role_prompt` | roles / Court | Ask which role should speak for a House in a public dispute and why. | no |  | no | easy | needs_review | Maybe host-judged/free-text. |
| 29 | `v2_final_word` | `v2_q029_final_plain` | `plain_text` | final / general culture | Clear final-round question with low ambiguity and strong explanation. | no |  | no | medium | needs_write | No fragile media. |
| 30 | `v2_final_word` | `v2_q030_final_image_choice` | `image_clue` | final visual | One fully tested image clue suitable for final tension. | yes | `v2_q030_final_image_choice` | no | hard | needs_media | Use only if smoke-passed. |
| 31 | `v2_final_word` | `v2_q031_final_manual_audio` | `manual_audio` | final music mood | Host plays a short final atmosphere/audio clue; text fallback asks about mood/context. | no |  | yes | medium | needs_review | Optional; must have no runtime dependency. |
| 32 | `v2_final_word` | `v2_q032_final_house_choice` | `role_prompt` | final strategy | Ask a decisive social/strategic question about choosing risk vs safe points. | no |  | no | medium | idea | Could be host-led. |
| 33 | `v2_reserve` | `v2_q033_duel_fast_object` | `duel_question` | Duel / fast object | Very short duel-ready question about identifying a familiar object or fact. | no |  | no | easy | needs_write | Core-flex Duel slot. |
| 34 | `v2_reserve` | `v2_q034_duel_true_false` | `duel_question` | Duel / true-false | Fast true/false duel question with immediate understandable answer. | no |  | no | easy | needs_write | Core-flex Duel slot. |
| 35 | `v2_reserve` | `v2_q035_duel_visual` | `duel_question` | Duel visual | Optional image-based duel question if asset is readable instantly. | yes | `v2_q035_duel_visual` | no | medium | needs_media | Core-flex only if image smoke passes. |
| 36 | `v2_reserve` | `v2_q036_host_manual_break` | `host_manual_moment` | host / pacing | Host manual moment for tie, pause, or table reset; no final answer needed yet. | no |  | no | easy | needs_review | Core-flex pacing slot, not import-first. |
| 37 | `v2_reserve` | `v2_q037_reserve_plain_food` | `plain_text` | reserve food | Plain reserve question about food/drink culture with no media dependency. | no |  | no | easy | reserve | Backup if media fails. |
| 38 | `v2_reserve` | `v2_q038_reserve_history` | `plain_text` | reserve history | Strange everyday-history reserve question. | no |  | no | medium | reserve | Needs fact check later. |
| 39 | `v2_reserve` | `v2_q039_reserve_visual` | `image_clue` | reserve visual | Backup image clue if another image is rejected. | yes | `v2_q039_reserve_visual` | no | medium | reserve | Asset optional. |
| 40 | `v2_reserve` | `v2_q040_reserve_social` | `plain_text` | reserve social reading | Reserve question about negotiation/social behavior, no personal accusations. | no |  | no | medium | reserve | Supports Diplomacy vibe. |
| 41 | `v2_reserve` | `v2_q041_reserve_court_safe` | `court_question` | reserve Court | Court-safe short question for tie or disputed moment. | no |  | no | easy | reserve | Robust fallback. |
| 42 | `v2_reserve` | `v2_q042_reserve_audio_fallback` | `manual_audio` | reserve music | Backup manual audio moment with text-only fallback if speakers fail. | no |  | yes | easy | reserve | Legal/source TBD. |
| 43 | `v2_reserve` | `v2_q043_reserve_local` | `plain_text` | local placeholder | Reserve local/Kurgan/Sobranie placeholder pending approval. | no |  | no | medium | reserve | Do not finalize without Victor/local check. |
| 44 | `v2_reserve` | `v2_q044_reserve_object` | `plain_text` | object trivia | Reserve object trivia without image dependency. | no |  | no | medium | reserve | Can become image if needed. |
| 45 | `v2_reserve` | `v2_q045_reserve_final_safe` | `plain_text` | final reserve | Clean final/tie question, no media, no ambiguity. | no |  | no | hard | reserve | For final backup. |
| 46 | `v2_reserve` | `v2_q046_reserve_role` | `role_prompt` | roles | Reserve role-understanding question for player clarity. | no |  | no | easy | reserve | Useful if table confusion appears. |
| 47 | `v2_reserve` | `v2_q047_reserve_image_reveal` | `image_reveal` | reserve reveal | Backup reveal image explaining a surprising answer after timer/reveal. | yes | `v2_q047_reserve_image_reveal` | no | medium | reserve | Use only if asset ready. |
| 48 | `v2_reserve` | `v2_q048_reserve_host_choice` | `host_manual_moment` | host fallback | Host-choice reserve moment for emergency pacing, tie, or failed media replacement. | no |  | no | easy | reserve | Manual only; may not become XLSX row. |

## 4. Visual slots summary

Target: 10-12 image questions.

Current draft visual slots: 13 candidate image slots. This intentionally gives 1-3 replaceable image candidates before final XLSX selection.

| question_code | expected image type | media_ref_draft | asset status |
| --- | --- | --- | --- |
| `v2_q003_oath_table` | familiar table/bar object close-up | `v2_q003_table_object_closeup` | planned |
| `v2_q007_old_tool` | old tool/object | `v2_q007_old_tool` | planned |
| `v2_q009_ad_fragment` | old advertisement/poster crop | `v2_q009_ad_fragment` | planned; rights/source check needed |
| `v2_q011_map_mark` | map/sign/local orientation fragment | `v2_q011_map_mark` | planned; local approval needed |
| `v2_q014_hidden_detail` | delayed visual clue / broad hidden detail | `v2_q014_hidden_detail` | planned |
| `v2_q016_food_closeup` | food texture/ingredient close-up | `v2_q016_food_closeup` | planned |
| `v2_q019_object_reveal` | reveal image after answer | `v2_q019_object_reveal` | planned |
| `v2_q021_pattern_trap` | visible pattern/arrangement | `v2_q021_pattern_trap` | planned |
| `v2_q024_court_evidence_image` | Court evidence image | `v2_q024_court_evidence_image` | planned; smoke required |
| `v2_q027_court_symbol_reveal` | Court reveal symbol/image | `v2_q027_court_symbol_reveal` | planned; smoke required |
| `v2_q030_final_image_choice` | final image clue | `v2_q030_final_image_choice` | planned; use only if smoke-passed |
| `v2_q035_duel_visual` | fast duel visual | `v2_q035_duel_visual` | optional; may cut |
| `v2_q039_reserve_visual` | reserve image clue | `v2_q039_reserve_visual` | reserve |
| `v2_q047_reserve_image_reveal` | reserve reveal image | `v2_q047_reserve_image_reveal` | reserve |

Final XLSX should select about 10-12 from these, after source/rights, readability, and TV smoke review.

## 5. Manual music/audio slots summary

Target: 3-4 manual/offline music/audio moments.

Current draft manual audio slots: 4.

| question_code | host action | fallback if audio fails | legal/source status placeholder |
| --- | --- | --- | --- |
| `v2_q017_manual_audio_mood` | Host plays a short instrumental/mood fragment outside the app. | Use text-only mood/context question. | `NEEDS_SOURCE_APPROVAL` |
| `v2_q022_manual_audio_instrument` | Host plays or describes a sound/instrument moment manually. | Read a text description and ask instrument-family question. | `NEEDS_SOURCE_APPROVAL` |
| `v2_q031_final_manual_audio` | Host plays final atmosphere/audio clue manually. | Use final text question only. | `NEEDS_SOURCE_APPROVAL` |
| `v2_q042_reserve_audio_fallback` | Host uses backup manual audio only if earlier moment fails or extra time exists. | Skip and use plain reserve question. | `NEEDS_SOURCE_APPROVAL` |

Rules:

- No runtime audio dependency.
- Do not use copyrighted song names or lyrics in the question draft.
- Host/operator owns playback device, volume check, and fallback.
- Later XLSX should use `media_type=none` and `tags=manual_audio` for scoring/manual notes.

## 6. Court/Duel slots summary

Court rows:

| question_code | role in bank | note |
| --- | --- | --- |
| `v2_q023_court_truth` | Core Court | Short and robust. |
| `v2_q024_court_evidence_image` | Core Court image candidate | Use only if TV-readable. |
| `v2_q025_court_gold_choice` | Core Court strategy | No automatic gold/resource mutation. |
| `v2_q026_court_food_fact` | Core Court plain fact | Low ambiguity. |
| `v2_q027_court_symbol_reveal` | Core Court reveal image candidate | Image explains answer after reveal. |
| `v2_q028_court_final_argument` | Core Court role prompt | Host may judge manually. |
| `v2_q041_reserve_court_safe` | Reserve Court | Backup/tie slot. |

Duel rows:

| question_code | role in bank | note |
| --- | --- | --- |
| `v2_q033_duel_fast_object` | Duel-ready short question | Fast to understand. |
| `v2_q034_duel_true_false` | Duel-ready true/false | Immediate answer. |
| `v2_q035_duel_visual` | Optional Duel visual | Use only if image is instantly readable. |

Court guidance:

- Court questions should be short and robust.
- Court questions should avoid fragile media unless smoke-tested.
- Court questions should not create real-person accusations or toxic claims.

Duel guidance:

- Duel questions should be fast to understand.
- Duel V1.1 remains manual challenge/resolve/draw-replay.
- No Duel V2 question-before-move engine is included in this bank.

## 7. Open approvals for Victor

Needs Victor/operator decision before XLSX authoring:

- Approve or reject the overall theme mix.
- Approve local/Kurgan placeholders.
- Approve whether direct `Собрание` references should appear in questions.
- Approve target visual count: 10, 11, or 12 image questions.
- Approve music/manual audio count: 3 or 4 moments.
- Approve whether music is scoring content or only atmosphere.
- Approve difficulty level: easier commercial flow vs harder competitive flow.
- Approve whether Court uses new rows, old bank rows, or mixed rows.
- Approve whether Duel gets dedicated question slots or only reserve slots.
- Approve who owns image/source/rights checks.
- Approve who owns host playlist/device and fallback.

## 8. Next artifact

Recommended next artifacts after this draft list is approved:

1. Create XLSX authoring draft.
   - One row per selected question.
   - Include final prompt, options, correct answer, explanation, `round_code`, `media_type`, `media_ref`, `difficulty`, and `tags`.

2. Create media asset list.
   - Include `media_ref`, filename, source, rights status, crop/compress status, and smoke status.

3. Create manual audio/playlist plan.
   - Include host action, source/device, start point, fallback, and legal/source approval placeholder.

4. Run dry-run import only after approval.
   - `dry_run=true`.
   - `clear_existing=false`.
   - Non-LIVE target only.
   - No `LIVE01`.
