# Question Bank V2 Blueprint

## 1. Purpose

This blueprint turns the V2 preparation plan into an actual game/question-bank structure for the next commercial `приСтолов` game.

It is not an import file and does not mutate runtime state.

The goal is to define before authoring XLSX/import assets:

- round structure;
- target question counts;
- visual/image moments;
- manual music/audio moments;
- Duel/Court placement;
- reserve questions;
- media asset list format;
- safe import and smoke boundaries.

Hard decisions inherited from the preparation plan:

- Use XLSX-first authoring.
- Image questions are the safest runtime media path.
- Runtime audio is not reliable enough for the next game.
- Music/audio moments are manual/offline through host/operator.
- Import must start with dry-run.
- Do not touch `LIVE01`.
- Do not use destructive `clear_existing=true` unless explicitly approved with rollback.

## 2. Target game shape

Recommended target length:

- 2.0-2.5 hours including onboarding, breaks, diplomacy, Harchevnya, Duel/Court, and final.

Recommended question bank size:

- Core playable set: 36 questions.
- Reserve set: 10-12 questions.
- Total authored candidates: 48 questions.

Recommended media target:

- Image questions: 10-12.
- Manual audio/music moments: 3-4.
- Plain robust reserve questions: at least 8.

Design principle:

- Every media moment must have a plain fallback.
- No critical stage should depend on untested audio or missing image assets.

## 3. Round plan overview

| Stage | Purpose | Questions | Media | Notes |
| --- | --- | ---: | --- | --- |
| Intro / onboarding | Explain Houses, roles, phones | 0 | Optional music bed manual | Host script, no app dependency. |
| Warmup: Oath of the Table | Fast start, easy confidence | 6 | 1 image max | Mostly true/false. |
| Main Round 1: Signs and Objects | Visual/table energy | 8 | 3 images | Strong image-clue questions. |
| Social / Diplomacy window | Movement, deals, Harchevnya | 0 | Manual background music | No runtime question dependency. |
| Main Round 2: Stories and Tricks | Strong quiz core | 8 | 3 images, 1 manual audio | One host-played music/audio question. |
| Duel window | Duel challenge/resolve moment | 0-2 reserve | Manual only | Use existing Duel V1.1 draw/replay handling. |
| Court: Trial of Houses | Public tension | 6 | 1-2 images | Keep mostly robust. |
| Final: Last Word of the Houses | Decisive finish | 4 | 1 image or none | Avoid fragile media. |
| Reserve | Backup / tie / tech fallback | 10-12 | 2 images max | Plain-first fallback bank. |

Core runtime question target:

- Warmup: 6
- Main Round 1: 8
- Main Round 2: 8
- Court: 6
- Final: 4
- Reserve: 10-12

## 4. XLSX round code blueprint

Use one XLSX file with sheet name:

```text
questions
```

Recommended `round_code` values:

| Round code | Human name | Count | Notes |
| --- | --- | ---: | --- |
| `v2_warmup_oath` | Разминка: Клятва стола | 6 | True/false and simple choice. |
| `v2_signs_objects` | Знаки и предметы | 8 | Visual clue-heavy block. |
| `v2_stories_tricks` | Истории и уловки | 8 | Mixed quiz with one manual audio. |
| `v2_court_trial` | Суд Домов | 6 | Court-ready robust questions. |
| `v2_final_word` | Последнее слово Домов | 4 | Final decisive questions. |
| `v2_reserve` | Резерв ведущего | 10-12 | Backup, tie, tech fallback. |

Recommended import test target before final scenario mapping:

```text
v2_commercial_test_round
```

Do not import directly into live scenario rounds until dry-run preview and non-LIVE smoke pass.

## 5. Question type distribution

Target distribution for 48 authored candidates:

| Type | Target count | Purpose |
| --- | ---: | --- |
| `true_false` | 12 | Fast, table-wide energy. |
| `single_choice` | 26 | Main reliable gameplay. |
| `free_text` | 10 | Host-led, Court/final/reserve. |

Target distribution for 36 core questions:

| Type | Target count |
| --- | ---: |
| `true_false` | 8 |
| `single_choice` | 22 |
| `free_text` | 6 |

Authoring rule:

- Every `single_choice` question should have 4 options unless there is a strong reason not to.
- Every question must have `correct_answer` and `explanation`.
- Free-text answers must be short enough for host judgement.

## 6. Visual/image question plan

Target 10-12 image questions.

Image usage categories:

| Usage | Count | Runtime expectation |
| --- | ---: | --- |
| clue | 6-8 | Image visible with question. |
| reveal | 2-3 | Image appears after answer/reveal. |
| decorate | 1-2 | Atmosphere only, not needed to answer. |

Recommended placement:

| Round | Image count | Usage |
| --- | ---: | --- |
| `v2_warmup_oath` | 1 | clue or decorate |
| `v2_signs_objects` | 3-4 | clue-heavy |
| `v2_stories_tricks` | 3 | clue/reveal mix |
| `v2_court_trial` | 1-2 | robust, readable |
| `v2_final_word` | 0-1 | only if fully tested |
| `v2_reserve` | 1-2 | fallback optional |

Image quality rules:

- Must be readable from far tables.
- No tiny text unless the question is about the broad image, not details.
- Use high-contrast images.
- Crop before importing.
- Compress enough for browser/TV loading.
- Avoid copyrighted or questionable public media without approval.

## 7. Manual music/audio moment plan

Runtime audio is not part of V2 unless separately patched and tested.

Use 3-4 manual audio/music moments:

| Moment | Placement | App data | Host action |
| --- | --- | --- | --- |
| Opening ambience | Intro | No question row needed | Host starts background music. |
| Guess by sound/music | `v2_stories_tricks` | `media_type=none`, `tags=manual_audio` | Host plays track manually. |
| Diplomacy bed | Social window | No question row needed | Low-volume music during deals. |
| Final tension | Final | Optional no-media question | Host controls music manually. |

Manual audio rules:

- Keep a playlist/folder outside app.
- Host knows exact file and start point.
- Venue volume checked before guests arrive.
- Every audio question has text fallback.
- Do not put `media_type=audio` in the XLSX for runtime unless audio patch is approved.

## 8. Candidate question themes

Use themes that work for bar guests and team discussion.

Recommended theme buckets:

1. Strange everyday history
   - inventions;
   - old objects;
   - rituals;
   - food/drink trivia.

2. Visual recognition
   - object close-ups;
   - old advertisements;
   - unusual tools;
   - maps/signs/symbols.

3. Human behavior and myths
   - common misconceptions;
   - social habits;
   - surprising facts.

4. Music/manual audio
   - recognize era/style/instrument;
   - identify mood/source/context;
   - compare two short fragments manually.

5. Court/final-worthy questions
   - clear answer;
   - low ambiguity;
   - easy for audience to accept.

Avoid:

- overlong text;
- obscure expert-only facts;
- answers that rely on spelling disputes;
- copyrighted media without approval;
- jokes that become personal insults;
- image questions with unreadable detail.

## 9. XLSX row blueprint

Each row should use these fields:

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

Recommended values:

- `section`: human grouping, e.g. `warmup`, `main`, `court`, `final`, `reserve`.
- `question_type`: `true_false`, `single_choice`, or `free_text`.
- `media_type`: `image` or `none` for this game.
- `media_ref`: slug-style key for image questions; blank for no media.
- `difficulty`: `easy`, `medium`, `hard`.
- `role_code`: usually blank or `maester` unless a role-specific question is intended.
- `round_code`: one of the V2 round codes.
- `tags`: use comma-separated operational tags.

Useful `tags`:

```text
image_clue
image_reveal
image_decorate
manual_audio
court_safe
final_safe
reserve
needs_fact_check
needs_image
needs_host_note
```

## 10. Media asset list blueprint

Create a separate asset list before placing files into `app/static/questions_media`.

Recommended columns:

```text
media_ref
filename
round_code
question_code_or_row
usage
source
rights_status
needs_crop
needs_compress
status
notes
```

Example rows:

| media_ref | filename | usage | status | notes |
| --- | --- | --- | --- | --- |
| `v2_001_kodak` | `v2_001_kodak.jpg` | clue | planned | Old camera/ad object. |
| `v2_002_button_hook` | `v2_002_button_hook.jpg` | clue | planned | Must be readable on TV. |
| `v2_003_time_seller` | `v2_003_time_seller.png` | reveal | planned | Reveal after answer. |

Status values:

```text
planned
source_found
rights_ok
edited
ready_in_static
smoke_passed
rejected
```

## 11. Court and Duel placement

Duel V1.1 exists as challenge/resolve/draw/replay flow, not a full tic-tac-toe engine.

For this game:

- Keep Duel questions/manual challenge moments simple.
- Do not add Duel V2 question-before-move runtime.
- If offline tic-tac-toe/draw happens, use existing draw/replay status.
- Have 2-3 reserve Duel/Court questions ready.

Court questions should be:

- short;
- unambiguous;
- easy to explain;
- mostly non-media;
- safe if TV/media fails.

Recommended Court set:

- 4 direct questions;
- 2 reserve/tie questions;
- at most 1-2 image questions, only if already smoke-passed.

## 12. Harchevnya/Diplomacy integration

Question bank should leave space for non-question gameplay.

Plan explicit breaks:

- one Harchevnya/social window after Warmup or Main Round 1;
- one Diplomacy/Whisper manual window before Court;
- optional short Duel window after Main Round 2.

Do not overload every minute with questions.

Host should announce:

- when players may move;
- when Diplomats may talk;
- when Harchevnya requests are appropriate;
- when phones should be checked again.

## 13. Import and smoke sequence

Do not import while authoring is still unstable.

Sequence:

1. Complete XLSX draft.
2. Complete asset list.
3. Copy/edit images only in a controlled task.
4. Run local/import dry-run:
   - `dry_run=true`
   - `clear_existing=false`
   - explicit `target_round_code`
5. Review preview.
6. Run media prepare dry-run.
7. Fix missing/ambiguous assets.
8. Import to non-LIVE test target only after approval.
9. Smoke Master/TV/player in non-LIVE room.
10. Smoke at least:
    - one plain question;
    - one image clue question;
    - one deferred/reveal image question;
    - one manual audio question as host-operated flow.

## 14. Safety boundaries

Do not do before explicit approval:

- no `LIVE01` import;
- no production DB mutation;
- no migrations;
- no public question upload UI;
- no `/dev/questions/import` public link;
- no `clear_existing=true` on important rounds;
- no runtime audio patch bundled with question authoring;
- no broad scenario rewrite;
- no deployment during the live game.

## 15. Open decisions for Victor/operator

Need human decision:

- exact date and room code for the next commercial game;
- target player count / House count;
- desired age/content tone;
- how many image-heavy questions are acceptable;
- whether music/audio is background only or part of scoring;
- whether Court should be quiz-heavy or drama-heavy;
- whether Duel is planned as a real activity or only a possible side event;
- final media rights/source approval process;
- who owns the host playlist/device.

## 16. Recommended next artifact

Next docs/content artifacts:

1. `QUESTION_BANK_V2_XLSX_DRAFT_SPEC.md`
   - exact rows to write;
   - round codes;
   - question IDs;
   - content checklist.

2. `QUESTION_BANK_V2_MEDIA_ASSET_LIST.md`
   - image/audio assets;
   - filenames;
   - source/rights status;
   - readiness status.

3. `QUESTION_BANK_V2_HOST_AUDIO_PLAYLIST_PLAN.md`
   - manual tracks;
   - timing;
   - source/device;
   - fallback instructions.

Do not create/import XLSX until the blueprint is approved.
