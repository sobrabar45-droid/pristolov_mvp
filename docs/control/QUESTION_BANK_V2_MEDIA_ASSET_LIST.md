# Question Bank V2 Media Asset List

## 1. Purpose

This file tracks image/media/manual-audio assets needed for Question Bank V2.

It is not media storage. It does not create files. It does not place files into the app. It does not create an XLSX file.

Use this document to prepare future XLSX/media work by defining:

- planned `media_ref` values;
- target filenames;
- expected image type;
- source strategy;
- source/rights status;
- asset readiness status;
- reveal timing;
- manual audio notes and fallback rules.

This is a planning artifact before authoring/import work.

## 2. Safety status

Current safety state:

- no media files created;
- no images copied into the app;
- no XLSX created;
- no import;
- no DB mutation;
- no production action;
- no `LIVE01` action;
- no unlicensed audio upload;
- no runtime audio dependency;
- no `clear_existing=true`;
- no deployment.

## 3. Image asset rules

Future app media folder, if/when assets are approved and copied:

```text
app/static/questions_media
```

Future served URL pattern:

```text
/static/questions_media/<filename>
```

Image rules:

- Use slug-friendly filenames.
- Prefer Latin/ASCII filenames.
- Avoid spaces, quotes, punctuation, parentheses, and mixed Cyrillic filenames.
- Prefer these extensions:
  - `.jpg`
  - `.png`
  - `.webp`
- Use reasonable size/compression for TV/browser loading.
- Each image needs source/rights status before use.
- Each image must be checked on TV or TV-like display before game.
- Do not rely on tiny text or details that far tables cannot read.
- Every image question needs a plain fallback or replacement row.

## 4. Naming convention

Preferred rule:

```text
media_ref and filename base should match where possible.
```

Examples:

| Use | media_ref | target filename |
| --- | --- | --- |
| generic visual | `v2_visual_001` | `v2_visual_001.png` |
| food/drink | `v2_food_001` | `v2_food_001.jpg` |
| map/detail | `v2_map_001` | `v2_map_001.webp` |
| logo/symbol | `v2_symbol_001` | `v2_symbol_001.png` |
| table/bar scene | `v2_table_001` | `v2_table_001.jpg` |

Question-linked convention for this bank:

```text
media_ref:       v2_q003_table_object_closeup
target filename: v2_q003_table_object_closeup.jpg
```

If a different extension is selected, keep the same base name.

## 5. Image asset table

Status values:

```text
missing
needs_generate
needs_photo
needs_source_check
needs_crop
ready_candidate
blocked
```

Source strategies:

```text
generate
photo_own
licensed
public_domain_check
venue_photo
manual_placeholder
```

| asset_id | question_code | round_code | media_ref | target_filename | expected_image_type | source_strategy | source_rights_status | asset_status | reveal_timing | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `asset_v2_img_001` | `v2_q003_table_object_closeup` | `v2_warmup_oath` | `v2_q003_table_object_closeup` | `v2_q003_table_object_closeup.jpg` | object close-up / table detail | `venue_photo` | `unknown` | `needs_photo` | clue | Easy first visual; must be obvious from far tables. |
| `asset_v2_img_002` | `v2_q007_old_tool` | `v2_signs_objects` | `v2_q007_old_tool` | `v2_q007_old_tool.jpg` | historical/old object | `public_domain_check` | `needs_source_check` | `needs_source_check` | clue | Strong recognition slot; use public-safe source. |
| `asset_v2_img_003` | `v2_q009_ad_fragment` | `v2_signs_objects` | `v2_q009_ad_fragment` | `v2_q009_ad_fragment.jpg` | old ad/poster fragment | `public_domain_check` | `needs_source_check` | `needs_source_check` | clue | Rights-sensitive; use only if source is safe. |
| `asset_v2_img_004` | `v2_q011_map_mark` | `v2_signs_objects` | `v2_q011_map_mark` | `v2_q011_map_mark.webp` | map/detail/local sign | `venue_photo` | `unknown` | `needs_photo` | clue | Local/Kurgan/Sobranie placeholder; requires Victor approval. |
| `asset_v2_img_005` | `v2_q014_hidden_detail` | `v2_signs_objects` | `v2_q014_hidden_detail` | `v2_q014_hidden_detail.png` | what changed / hidden detail | `generate` | `unknown` | `needs_generate` | after_timer | Must not depend on tiny visual details. |
| `asset_v2_img_006` | `v2_q016_food_closeup` | `v2_stories_tricks` | `v2_q016_food_closeup` | `v2_q016_food_closeup.jpg` | food/drink close-up | `venue_photo` | `unknown` | `needs_photo` | clue | Good bar-energy image; avoid gross ambiguity. |
| `asset_v2_img_007` | `v2_q019_object_reveal` | `v2_stories_tricks` | `v2_q019_object_reveal` | `v2_q019_object_reveal.jpg` | reveal object/explanation | `public_domain_check` | `needs_source_check` | `needs_source_check` | reveal | Image should explain answer after reveal. |
| `asset_v2_img_008` | `v2_q021_pattern_trap` | `v2_stories_tricks` | `v2_q021_pattern_trap` | `v2_q021_pattern_trap.png` | visual pattern / arrangement | `generate` | `unknown` | `needs_generate` | clue | Must be readable from far tables. |
| `asset_v2_img_009` | `v2_q024_court_evidence_image` | `v2_court_trial` | `v2_q024_court_evidence_image` | `v2_q024_court_evidence_image.jpg` | visual evidence for Court | `manual_placeholder` | `unknown` | `missing` | clue | Court image must be simple and non-controversial. |
| `asset_v2_img_010` | `v2_q027_court_symbol_reveal` | `v2_court_trial` | `v2_q027_court_symbol_reveal` | `v2_q027_court_symbol_reveal.png` | symbol/logo-style reveal | `generate` | `unknown` | `needs_generate` | reveal | Logo/symbol trap; no real brand misuse. |
| `asset_v2_img_011` | `v2_q030_final_image_choice` | `v2_final_word` | `v2_q030_final_image_choice` | `v2_q030_final_image_choice.jpg` | final visual clue | `licensed` | `needs_source_check` | `needs_source_check` | clue | Use only if polished and TV-smoke-passed. |
| `asset_v2_img_012` | `v2_q035_duel_visual` | `v2_reserve` | `v2_q035_duel_visual` | `v2_q035_duel_visual.png` | duel-safe fast visual | `generate` | `unknown` | `needs_generate` | clue | Optional; likely cut unless instantly readable. |
| `asset_v2_img_013` | `v2_q039_reserve_visual` | `v2_reserve` | `v2_q039_reserve_visual` | `v2_q039_reserve_visual.jpg` | reserve image clue | `manual_placeholder` | `unknown` | `missing` | clue | Reserve visual if another asset is rejected. |

Optional extra reserve candidate not in first 13 table:

| question_code | media_ref | note |
| --- | --- | --- |
| `v2_q047_reserve_image_reveal` | `v2_q047_reserve_image_reveal` | Keep as optional extra only if asset is easy and time allows. |

## 6. Recommended visual candidates

Likely visual categories and draft mapping:

| Category | Candidate question_code | media_ref | Notes |
| --- | --- | --- | --- |
| food/drink visual | `v2_q016_food_closeup` | `v2_q016_food_closeup` | Venue photo preferred. |
| object close-up | `v2_q003_table_object_closeup` | `v2_q003_table_object_closeup` | Warmup-safe visual. |
| logo/symbol trap | `v2_q027_court_symbol_reveal` | `v2_q027_court_symbol_reveal` | Generate or use original/simple symbol. |
| map/detail | `v2_q011_map_mark` | `v2_q011_map_mark` | Local approval required. |
| what changed image | `v2_q014_hidden_detail` | `v2_q014_hidden_detail` | After-timer reveal/clue. |
| visual evidence for Court | `v2_q024_court_evidence_image` | `v2_q024_court_evidence_image` | Must not cause argument. |
| bar/table scene | `v2_q003_table_object_closeup` | `v2_q003_table_object_closeup` | Could be own venue/table photo. |
| historical/cultural visual | `v2_q007_old_tool` | `v2_q007_old_tool` | Public-domain/source check. |
| local/Kurgan/Sobranie visual placeholder | `v2_q011_map_mark` | `v2_q011_map_mark` | `VERIFY_AGAINST_DRAFT_ROWS` after approval. |
| image after timer | `v2_q014_hidden_detail` | `v2_q014_hidden_detail` | Must not rely on tiny detail. |
| image reveal | `v2_q019_object_reveal` | `v2_q019_object_reveal` | Reveal after answer. |
| duel-safe visual reserve | `v2_q035_duel_visual` | `v2_q035_duel_visual` | Optional reserve only. |

## 7. Manual audio/music asset notes

Manual audio rules:

- Do not upload audio into the app.
- Do not use runtime audio.
- Host/operator plays manually only.
- Do not use copyrighted song names or lyrics yet.
- Each audio moment needs fallback text.
- Legal/source decision belongs to Victor/operator.

| audio_id | question_code | manual_audio_ref | host_action | source_strategy | source_rights_status | fallback_if_audio_fails | status | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `audio_v2_001` | `v2_q017_manual_audio_mood` | `v2_audio_mood_001` | Host plays short instrumental/mood fragment outside app. | `manual_playlist` | `needs_victor_operator_decision` | Use text-only mood/context question. | `planned` | Primary manual audio moment. |
| `audio_v2_002` | `v2_q022_manual_audio_instrument` | `v2_audio_instrument_001` | Host plays/describes a short sound or instrument moment manually. | `manual_playlist` | `needs_victor_operator_decision` | Read text description and ask instrument-family question. | `planned` | Use only if source/fallback is simple. |
| `audio_v2_003` | `v2_q031_final_manual_audio` | `v2_audio_final_001` | Host plays final atmosphere/audio clue manually. | `manual_playlist` | `needs_victor_operator_decision` | Use final text question only. | `planned` | Optional final moment; no runtime dependency. |
| `audio_v2_004` | `v2_q042_reserve_audio_fallback` | `v2_audio_reserve_001` | Host uses backup manual audio if time/need exists. | `manual_playlist` | `needs_victor_operator_decision` | Skip and use plain reserve question. | `planned` | Reserve fallback only. |

## 8. Asset readiness gates

A visual row can move toward `ready_for_dry_run` only when:

- image exists;
- target filename matches `media_ref` base;
- source_rights_status is acceptable;
- image opens locally;
- image is readable on TV or TV-like display;
- reveal timing is known;
- host wording is ready;
- fallback row or fallback wording exists.

A manual audio row can move toward ready only when:

- host knows exactly what to play;
- source/legal status is approved by Victor/operator;
- fallback text is written;
- timing/start point is known;
- playback device is known;
- venue volume can be checked;
- no runtime audio is expected.

## 9. Media dry-run checklist

Later checklist, after separate approval:

1. Place approved images in:

```text
app/static/questions_media
```

2. Confirm expected served path:

```text
/static/questions_media/<filename>
```

3. Run question import dry-run only:

```text
dry_run=true
clear_existing=false
```

4. Run media prepare dry-run.
5. Check missing/ambiguous media.
6. Test at least one image question in a non-LIVE room.
7. Test one image reveal/deferred image behavior in a non-LIVE room.
8. Never use `LIVE01`.
9. Never use `clear_existing=true` without separate written approval and rollback plan.

## 10. Open decisions for Victor

Needs Victor/operator decision:

- Which visual concepts are worth producing?
- Are Собрание/local visuals allowed?
- Are generated images acceptable?
- Are real venue photos available?
- Who will take or generate images?
- Who approves source/rights status?
- Which 10-12 image assets are final from the 13 candidates?
- Should the Duel visual reserve be cut?
- What music/manual audio sources are acceptable?
- Who operates music during the game?
- What is the fallback if venue audio fails?

## 11. Next artifact

Recommended next artifact:

```text
docs/control/QUESTION_BANK_V2_XLSX_DRAFT_PLAN.md
```

Alternative after media-list review:

```text
question_bank_v2_authoring_draft.xlsx
```

Do not create XLSX or media files until this asset list is reviewed.
