# External question/media folder audit (LIVE01 materials)

## External source

- Source root: `D:\Projects\Полезности Игра пристолов\Igra_Pristolov1.0`
- Exists: yes
- Top-level entries:
  - `Игра Пристолов`
- File count inside `Игра Пристолов`: **23**
- Extension counts:
  - `.docx`: 1
  - `.jpg`: 15
  - `.jpeg`: 1
  - `.png`: 3
  - `.jfif`: 3
- Relevant question/media candidates found:
  - `Вопросы на игру Пристолов.docx` (question file)
  - 22 image/media files (jpg/jpeg/png/jfif)

## External folder relevance map

| File | Type | Looks like questions | Includes answers | Has media refs | Media exists in repo |
|---|---|---|---|---|
| `Вопросы на игру Пристолов.docx` | DOCX | yes | yes/unknown (needs parse on import) | likely via inline/adjacent references | not directly checked in-place; repo already has a similarly named import template |
| `15. женщина будит жителей.jpeg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `16. конкурс красоты.png` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `17. Двухпенсовый подвес.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `18. Медведь).png` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `19. Уксусница.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `21. Застегиватель пуговиц.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `322010b3670326e320fc8c2ff97c2478.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `BackRub.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Бананы.jfif` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Время.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Время.png` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Жозефина.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Кодак-1.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Кодак-2.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Короли-карты.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Крысолов-1.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Крысолов-2.jfif` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Микроволновка.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Посудомойка.jfif` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Продавщица времени.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Ручка.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Схема.jpg` | image | no | n/a | image candidate | exact match in `app/static/questions_media` |
| `Бананы.jfif` note: duplicate name already present in repo media folder in different case/context as expected |

## Relation to current in-repo question sources

- Scenario templates currently present:
  - `app/game_templates/scenarios/season1_full_run_v1.json` (10 rounds / 43 questions)
  - `app/game_templates/scenarios/season1_full_run_v2.json` (12 rounds / 5 questions)
  - `app/game_templates/scenarios/season1_mvp_live_v1.json` (7 rounds / 2 questions)
  - `app/game_templates/scenarios/season1_mvp_live_v2.json` (10 rounds / 13 questions)
- Question definition sources also exist in:
  - `app/game_templates/season1_core_v1/rounds.yaml`
  - `app/game_templates/season1_core_v1/round_questions.yaml`
- Existing import tooling (dev route):
  - `POST /questions/import` in `app/routes/dev.py` for DOCX/XLSX ingestion
  - `POST /questions/prepare-media` for media references/asset checks
- Existing import templates are in:
  - `docs/question_import_templates/pristolov_questions_template.docx`
  - `docs/question_import_templates/pristolov_questions_template.xlsx`
  - and related court/battle XLSX templates.

## Import strategy recommendation (no copy/move/delete yet)

### What to archive as source material only
- Preserve external folder content as immutable source pack:
  - `Igra_Pristolov1.0/Игра Пристолов/Вопросы на игру Пристолов.docx`
  - Associated media files in the same folder
- Recommended archive folder in repo for later review: `docs/source_materials/` (create only after approval).

### What can become active question bank data
- Normalize and map the DOCX questions to repository import format:
  - Use existing `POST /questions/import` dry-run flow first.
  - If accepted, write as:
    - `app/game_templates/scenarios/*.json` for concrete LIVE01 scenario assignment, **or**
    - extend/clone core templates in `app/game_templates/season1_core_v1` then generate scenario JSON.
- Do not modify runtime now; this task is an audit only.

### What media should be copied later
- External media can be staged later into `app/static/questions_media` (media runtime path already used by importer/UI).
- Current media folder already contains 33 files, including all exact-name external assets and slugified alternatives.

### What needs cleanup before import
- Normalize filenames if needed:
  - external has names like `Медведь).png` and `18. ...` which may need consistent naming/slugs for future deterministic ops.
  - `prepare-media`/import pipeline has helper logic for media matching/slugging; verify after staging.
- Verify question text encoding and inline answer formatting after dry-run parse.
- Keep question/media separation:
  - question text into scenario/question template DB
  - media assets into static media store only when reference is confirmed.

### What should not be imported now
- Court-only material, non-game technical text, and any unrelated rehearsal notes.
- No Court/final logic objects from this audit step.
- No runtime files/scripts or DB mutation before explicit operator approval.

## Suggested target placement

1. `docs/source_materials/` — source pack archive for external materials (read-only)
2. `app/game_templates/scenarios/` — applied scenario JSON once approved
3. `app/game_templates/season1_core_v1/` — template-level evolution (if moving from template-first approach)
4. `app/static/questions_media/` — media runtime assets used by importer/UI
5. `docs/control/` — this audit + decision docs

## Court vs scenario question separation (recommended)

- Keep Court questions in court/game-stage question definitions (round schema + templates).
- Keep common/round flow questions for host-led rounds inside scenario question sections.
- Do not mix legacy technical/rehearsal assets with production scenario files until explicitly rebuilt.

## Risks / blockers

- UTF-8/mojibake risk: several existing candidate docs are still encoded poorly in repo; external question text must be validated on import, not assumed safe.
- Naming mismatch risk: external media names are mixed with slugged variants (e.g. `короли_карты.jpg` vs `Короли-карты.jpg`).
- No runtime verification yet: dry-run import + manual preview required before any DB/scenario changes.
- This audit does not execute copy/move; no change can be guaranteed until import plan is explicitly executed.

## Next control action

- Current follow-up should remain **import plan review only** (audit output), no runtime patch.
