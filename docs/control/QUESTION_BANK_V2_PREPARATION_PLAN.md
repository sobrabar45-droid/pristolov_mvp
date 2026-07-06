# Question Bank V2 Preparation Plan

## 1. Purpose

This plan prepares the next commercial `приСтолов` question bank and game session without importing or mutating anything yet.

The next commercial game is planned in about 9 days. Player feedback asks for more media-rich moments:

- visual questions;
- image-based questions;
- music-related questions;
- moments with musical/audio accompaniment;
- fewer plain-text-only stretches.

Current technical reality:

- Image questions are the safest media path.
- Audio/music can be represented as metadata, but runtime audio rendering is not reliable enough for the next game without a separate patch.
- Music/audio should be host-operated manually for this game unless a narrow audio patch is approved, implemented, and smoke-tested separately.

## 2. Current system summary

Question data is stored and executed through:

- `RoundTemplate`
- `RoundQuestionTemplate`
- `GameHostRound`
- `GameHostRoundQuestion`
- `GameAssignment`

Important question template fields:

- `prompt`
- `ui_template`
- `answer_mode`
- `content_json`
- `reward_json`
- `fail_effect_json`

Import endpoints exist under protected/operator routes:

- `POST /dev/questions/import`
- `POST /dev/questions/prepare-media`

Supported import formats:

- `.docx`
- `.xlsx`

Import safety defaults:

- `dry_run=true` by default.
- `dry_run=false` writes/imports questions.
- `clear_existing=true` can delete existing related question/runtime rows.
- Default target round: `imported_warmup_test`.

## 3. Recommended V2 question-bank shape

Target a balanced bank that gives the evening rhythm and visual variety.

Suggested first target:

| Block | Count | Notes |
| --- | ---: | --- |
| Fast true/false | 8-12 | Short, energetic, easy warmup. |
| Multiple choice | 12-18 | Main quiz material. |
| Image questions | 8-12 | Strongest V2 improvement; test every asset. |
| Open/free text | 4-6 | Host-controlled, use sparingly. |
| Music/manual audio moments | 3-5 | Host plays audio outside app. |
| Court/final reserve | 4-8 | Clean, reliable, no fragile media dependency. |

Minimum viable target before import:

- 30-40 total usable questions.
- At least 8 visual/image questions.
- At least 3 music/audio moments prepared manually.
- At least 5 reserve plain questions in case media fails.

## 4. Recommended round/content plan

Suggested flow for next commercial game:

1. Opening warmup
   - Mostly true/false and simple multiple choice.
   - 1 image question maximum.
   - Goal: get players comfortable.

2. Main question block 1
   - Multiple choice plus 2-3 image questions.
   - Keep media as clue when the image is required to answer.

3. Social/diplomacy window
   - No fragile app media dependency.
   - Host can use music bed manually if desired.

4. Main question block 2
   - More visual questions.
   - Include 1-2 music/manual audio moments.

5. Duel/Court/final
   - Prefer robust questions.
   - Use images only if already verified on TV.
   - Avoid untested audio runtime.

## 5. XLSX-first import recommendation

Use `.xlsx` as the primary source for V2.

Reason:

- One question per row.
- Explicit columns for `media_type` and `media_ref`.
- Easier review before import.
- Less formatting ambiguity than DOCX.

Expected sheet name:

```text
questions
```

Recommended columns:

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
```

Recommended `question_type` values:

```text
true_false
single_choice
free_text
```

Recommended `media_type` values for this game:

```text
image
none
```

Avoid using `audio` as runtime media for this game unless separately approved and tested.

## 6. Image/media naming convention

Use stable, simple, slug-friendly `media_ref` values.

Recommended convention:

```text
v2_001_kodak
v2_002_old_map
v2_003_button_hook
v2_004_time_seller
```

Recommended image filenames in `app/static/questions_media`:

```text
v2_001_kodak.jpg
v2_002_old_map.png
v2_003_button_hook.jpg
v2_004_time_seller.webp
```

Rules:

- Prefer Latin lowercase filenames.
- Use underscores, not spaces.
- Avoid punctuation, quotes, parentheses, and mixed Cyrillic filenames for new V2 assets.
- Prefer `.jpg`, `.png`, or `.webp`.
- Keep file sizes reasonable for TV/browser loading.
- Keep a spreadsheet column with exact `media_ref`.

## 7. Image question authoring rules

For each image question, decide one of these modes manually in the question notes:

- `clue`: image must be visible with the question.
- `reveal`: image appears after answer/reveal.
- `decorate`: image adds atmosphere but is not required.

Current runtime has image reveal logic, but all image questions must be smoke-tested on TV.

Authoring checklist:

- The question text clearly tells players if they should look at the image.
- The correct answer does not depend on tiny unreadable details.
- The image works on a large TV from far tables.
- The image is not legally/copyright sensitive for public use.
- The file exists under `app/static/questions_media`.
- The `media_ref` matches the slug/filename convention.

## 8. Music/audio plan for this game

For the next game, treat music/audio as host-operated manual moments.

Do not rely on runtime audio playback unless a separate audio patch is approved and tested.

Recommended manual flow:

1. Add a question row with `media_type=none`.
2. In `tags` or host notes, mark it as `manual_audio`.
3. Prepare an external playlist/audio folder for the host.
4. Host plays the track from a known device/source.
5. TV/app shows the text question only.
6. Host stops audio manually after the answer window.

Manual audio checklist:

- File/source ready before the game.
- Volume checked on venue speakers.
- Track start point known.
- Backup text-only version exists.
- Legal/staff decision on public playback is handled outside app.

## 9. Safe preparation workflow

Recommended sequence:

1. Draft the question bank in XLSX.
2. Collect image assets separately.
3. Rename images using the V2 naming convention.
4. Place candidate images under `app/static/questions_media` only in a controlled patch/task.
5. Run question import dry-run only:
   - `dry_run=true`
   - `clear_existing=false`
   - explicit `target_round_code`
6. Run media prepare dry-run only:
   - `dry_run=true`
   - inspect missing/ambiguous matches
7. Review preview output manually.
8. Fix source XLSX/media filenames.
9. Repeat dry-run until clean.
10. Only then run a controlled import into a non-LIVE test round/room.
11. Smoke on Master/TV/player in a non-LIVE room.
12. Only after approval, decide whether to prepare production/non-LIVE or live setup.

## 10. Import safety rules

Hard safety rules:

- Do not import into `LIVE01` without explicit approval.
- Do not use `clear_existing=true` without a written target and rollback plan.
- Do not import directly from a messy DOCX into production.
- Do not skip dry-run.
- Do not expose import UI publicly.
- Do not add homepage links to `/dev/questions/import`.
- Do not run imports during the live game.

Safe defaults:

```text
dry_run=true
clear_existing=false
target_round_code=v2_commercial_test_round
```

## 11. New game/session preparation flow

Before creating a commercial session:

1. Choose new room code.
2. Confirm it is not `LIVE01`.
3. Confirm scenario code.
4. Dry-run room setup if using helper/script.
5. Confirm helper compatibility with current DB schema before real creation.
6. Create or prepare room only after dry-run review.
7. Apply scenario only to the target non-LIVE room.
8. Open registration only after operator confirms URLs.

Known caution:

- `scripts/setup_room_mvp.py` exists and has a dry-run path.
- Earlier local smoke found a local schema/model mismatch around `games.status` for real helper insertion.
- Before using it for real setup, run dry-run and confirm current production/local schema expectations.

## 12. Non-LIVE smoke checklist

After import and room setup, smoke only in non-LIVE room:

- Master page opens.
- TV page opens.
- Player entry opens.
- First plain question opens.
- Options hidden before answer-open stage.
- Options visible after answer-open stage.
- Correct answer hidden before reveal.
- Correct answer visible after reveal on Master/TV.
- One image clue question displays image on TV.
- One deferred/reveal image question behaves as expected.
- Missing image produces no broken fatal UI.
- Manual audio question is playable by host outside app.
- No production live room is mutated.

## 13. What should be manual vs imported

Manual:

- final editorial review;
- image selection/cropping/compression;
- copyright/source approval;
- music/audio playback;
- host notes and timing;
- deciding if image is clue/reveal/decorative;
- final go/no-go before production.

Imported:

- structured question rows;
- options/correct answers/explanations;
- `media_type=image` metadata;
- `media_ref` metadata;
- target test round questions.

## 14. Risk register

| Risk | Severity | Mitigation |
| --- | --- | --- |
| `clear_existing=true` deletes needed rows | High | Keep false unless explicit approved replacement. |
| Import into wrong room/round | High | Use explicit target round and non-LIVE room. |
| Audio does not render | High | Manual host playback only. |
| Image filenames do not match slug | Medium | Use Latin slug convention and dry-run media prep. |
| Image too small for far tables | Medium | TV visual check before game. |
| DOCX parser misreads formatting | Medium | Prefer XLSX for V2. |
| Media copyright concern | Medium | Human review before use. |
| Runtime patch too close to game | Medium | Avoid new audio/runtime mechanics before game. |

## 15. Recommended next tasks

Recommended next sequence:

1. Create V2 question XLSX draft.
2. Create V2 image asset list with filenames and source/rights notes.
3. Create manual music/audio playlist plan for host.
4. Run import dry-run against local/non-LIVE only.
5. Run media prepare dry-run.
6. Create non-LIVE test room/session plan.
7. Smoke imported questions in non-LIVE room.
8. Only then decide whether any runtime patch is necessary.

Do not start with runtime/audio patching unless Victor explicitly makes audio playback a P0 requirement.
