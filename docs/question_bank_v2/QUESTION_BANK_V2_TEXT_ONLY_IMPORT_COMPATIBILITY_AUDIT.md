# Question Bank V2: text-only import compatibility audit

Scope: read-only compatibility audit between the filtered text-only XLSX candidate and the current `/dev/questions/import` importer code.

Candidate XLSX:

```text
docs/question_bank_v2/question_bank_v2_text_only_dry_run_candidate.xlsx
```

## 1. Import endpoint

The XLSX question import endpoint is:

```text
POST /dev/questions/import
```

Defined in:

```text
app/routes/dev.py
```

Important endpoint parameters:

- `dry_run`, default Form value: `true`;
- `target_round_code`, default: `imported_warmup_test`;
- `true_false_limit`, default: `5`;
- `single_choice_limit`, default: `5`;
- `free_text_limit`, default: `3`;
- `media_limit`, default: `0`;
- `prefer_media`, default: `false`;
- `clear_existing`, default: `false`.

## 2. Parser/function

XLSX is parsed by:

```text
app/services/question_import_service.py
parse_questions_xlsx(file_path)
build_questions_import_preview(file_path)
normalize_imported_question(raw_question)
select_questions_by_limits(...)
```

## 3. Sheet expectations

The parser requires a worksheet named exactly:

```text
questions
```

Candidate workbook sheets:

- `README`
- `questions`
- `review_status`
- `excluded_rows`
- `scope_21_rows`

Compatibility result: `questions` sheet exists, so sheet-level lookup passes.

## 4. Column expectations

The parser reads these exact header names from the `questions` sheet:

| Column | Used for | Present in candidate? |
| --- | --- | --- |
| `section` | section/type inference | no |
| `question_type` | question type | yes |
| `question` | prompt text | no |
| `option_a` | answer option A | no |
| `option_b` | answer option B | no |
| `option_c` | answer option C | no |
| `option_d` | answer option D | no |
| `correct_answer` | correct answer | no |
| `explanation` | explanation/host note | no |
| `media_type` | media type | yes |
| `media_ref` | media ref | yes |
| `difficulty` | difficulty | yes |
| `role_code` | role code | no |
| `round_code` | round code | yes |
| `tags` | tags | yes |

Candidate currently has authoring columns such as:

- `question_code`
- `prompt_draft`
- `option_a_draft`
- `option_b_draft`
- `option_c_draft`
- `option_d_draft`
- `correct_answer_draft`
- `import_status`
- `safe_to_import`

## 5. Candidate parser result

Read-only parser check result:

```text
PARSED_COUNT 21
PREVIEW_COUNT 21
SECTIONS {'true_false': 0, 'single_choice': 0, 'free_text': 0}
ERROR_COUNT 21
TYPE_COUNTS {'plain_text': 21}
EMPTY_PROMPT_COUNT 21
EMPTY_ANSWER_COUNT 21
```

The parser can open the workbook and reads 21 rows, but all 21 parsed rows have errors because importer-facing prompt/answer columns are missing.

First parsed item shape observed:

```text
{'question_code': 'import_plain_text_001', 'type': 'plain_text', 'prompt': '', 'correct_answer': '', 'options': [], 'has_errors': True, 'errors': ['Не заполнен текст вопроса', 'Не указан правильный ответ'], 'media_type': 'none', 'media_ref': '', 'round_code': 'v2_warmup_oath'}
```

## 6. Important compatibility finding

The current candidate XLSX is a valid authoring/scope artifact, but it is not import-compatible yet.

Reason: importer expects importer-facing columns:

```text
question, correct_answer, option_a, option_b, option_c, option_d, explanation
```

The candidate currently uses authoring-facing columns:

```text
prompt_draft, correct_answer_draft, option_a_draft, option_b_draft, option_c_draft, option_d_draft, host_note
```

Also, importer selection counts only these question types:

```text
true_false, single_choice, free_text
```

The candidate currently has `question_type=plain_text` for all 21 rows, so default `preview_selected` logic would not select them as true_false/single_choice/free_text questions.

## 7. `safe_to_import=no` and `import_status=not_ready` behavior

Current importer code does not read or enforce `safe_to_import` or `import_status`.

Therefore:

- these fields do not cause rows to be skipped;
- these fields do not protect the file at runtime if someone sends it to the import endpoint;
- they are useful authoring/safety metadata, but not importer guards.

Because the current candidate has missing importer-facing columns, the practical failure mode is not safe skipping. It is parsing 21 erroneous rows with empty prompt/correct answer and unsupported type classification.

## 8. Required changes before any dry-run request

Before a safe local dry-run request can be attempted, create a separate import-compatible candidate XLSX, not by mutating the authoring workbook in place.

Required conversion:

| Current authoring column | Importer column |
| --- | --- |
| `prompt_draft` | `question` |
| `correct_answer_draft` | `correct_answer` |
| `option_a_draft` | `option_a` |
| `option_b_draft` | `option_b` |
| `option_c_draft` | `option_c` |
| `option_d_draft` | `option_d` |
| `host_note` / `notes` | `explanation` |
| `question_code` | currently ignored by parser; optional only unless importer is changed |

Required type normalization:

- rows with `правда/ложь` options should become `question_type=true_false`;
- rows with answer options should become `question_type=single_choice`;
- rows with no answer options should become `question_type=free_text`;
- do not use `plain_text` for importer dry-run.

Required dry-run constraints remain:

- `dry_run=true`;
- `clear_existing=false`;
- local/non-LIVE only;
- no production;
- no `LIVE01`;
- no media copy;
- no DB mutation.

## 9. Recommendation

Do not run `/dev/questions/import` with the current text-only candidate XLSX.

Recommended next task: create a separate import-compatible text-only dry-run XLSX with importer-facing columns and normalized question types, while keeping it local/non-imported until a new compatibility check passes.

## 10. Read-only confirmation

- Candidate workbook unchanged by this audit: `True`
- No import was run.
- No DB mutation happened.
- No production action happened.
- No `LIVE01` touch happened.
- No media copy happened.
- No runtime/template/route changes happened.
- No deploy/migration/restart happened.
- No `clear_existing` was used.
