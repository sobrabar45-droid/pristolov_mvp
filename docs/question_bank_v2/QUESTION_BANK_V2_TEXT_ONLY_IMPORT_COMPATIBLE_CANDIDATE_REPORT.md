# Question Bank V2: import-compatible text-only candidate report

Purpose: document the separate importer-facing XLSX created from the 21-row text-only scope. This task did not run import or mutate any DB.

## 1. Created artifact

```text
docs/question_bank_v2/question_bank_v2_text_only_import_compatible_candidate.xlsx
```

Source artifact:

```text
docs\question_bank_v2\question_bank_v2_text_only_dry_run_candidate.xlsx
```

## 2. Selected rows

- selected slot count: `21`
- selected slots: `[3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 35]`
- visual rows excluded;
- reserve/cut rows excluded;
- media fields are `none` / empty.

## 3. Importer-facing schema

The `questions` sheet now uses importer-facing columns:

```text
section, question_type, question, option_a, option_b, option_c, option_d, correct_answer, explanation, media_type, media_ref, difficulty, role_code, round_code, tags
```

Trace/safety columns appended after importer columns:

```text
source_slot, source_question_code, safe_to_import, import_status
```

## 4. Type normalization

Types were normalized for importer compatibility:

- `single_choice`: `8`
- `true_false`: `13`

Rules used:

- `правда/ложь` option rows -> `true_false`;
- rows with answer options -> `single_choice`;
- rows with no answer options -> `free_text`;
- no `plain_text` remains.

## 5. Parser compatibility verification

Read-only parser verification against current importer code:

```text
PARSED_COUNT 21
PREVIEW_COUNT 21
SECTIONS {'true_false': 13, 'single_choice': 8, 'free_text': 0}
ERROR_COUNT 0
TYPE_COUNTS {'single_choice': 8, 'true_false': 13}
EMPTY_PROMPT_CODES []
EMPTY_ANSWER_CODES []
MEDIA_REFS_NONEMPTY []
```

Compatibility result: parser opens the XLSX and all 21 rows parse without validation errors.

## 6. Safety status

- No import was run.
- No DB mutation happened.
- No production action happened.
- No `LIVE01` touch happened.
- No media copy happened.
- No runtime/template/route changes happened.
- No deploy/migration/restart happened.
- No `clear_existing` was used.
- Source candidate unchanged: `True`.

Important: `safe_to_import` and `import_status` remain metadata only. Current importer does not enforce them. Future dry-run still requires explicit approval and must use `dry_run=true` plus `clear_existing=false`.

## 7. Next recommended step

Run a separate read-only/local dry-run command planning task, or explicitly approve a local non-LIVE dry-run using this import-compatible candidate. Do not run against production or `LIVE01`.
