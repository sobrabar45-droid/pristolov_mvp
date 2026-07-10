# Question Bank V2: remaining Victor decisions

Источник: `docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx`, sheet `Вопросы для редактуры`.

Цель: показать только 5 строк, где правильный ответ ещё не заполнен и нужно решение Виктора. XLSX не изменялся.

## Summary

| Metric | Count | Rows |
| --- | ---: | --- |
| Total unresolved rows | 5 | 1, 7, 8, 29, 37 |
| Need fact answer | 4 | 1, 7, 8, 37 |
| Need media/video decision | 1 | 29 |
| Need source check | 4 | 7, 8, 29, 37 |

## Rows for Victor

### Row 1: `v2_edited_q001`

- Editor row / slot: `1`
- Round / block: `v2_warmup_oath`
- Question type: `plain_text`
- Difficulty: `easy`
- Status / next action: `needs_review` / Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 6. Аудит action=keep. answer_type=true_false. risk_flags=needs_media. Медиа требуется подобрать/проверить; в app/static не копировалось.
- Current answer field: `(пусто)`
- Answer status: `НЕТ — заполнить/проверить`
- Media ref: `v2_edited_potato_monument`
- Selected image filename: `none`
- Image status: `needs_mapping`
- Reveal timing: `with_question`
- Reserve: `нет`
- Import allowed: `НЕТ (no, not_ready)`

Question text:

```text
В белорусской столице Минске установлен памятник картошке.
```

Answer options:

- A: правда
- B: ложь

Host note / comments:

```text
Host note: Медиа из source_docs: проверить файл в source_docs.
```

Why Victor is needed: Нужно подтвердить факт/правда-ложь: в строке нет достаточной заметки с ответом.

### Row 7: `v2_edited_q007`

- Editor row / slot: `7`
- Round / block: `v2_warmup_oath`
- Question type: `plain_text`
- Difficulty: `easy`
- Status / next action: `needs_review` / Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 12. Аудит action=keep. answer_type=true_false.
- Current answer field: `(пусто)`
- Answer status: `НЕТ — заполнить/проверить`
- Media ref: `none`
- Selected image filename: `none`
- Image status: `нет`
- Reveal timing: `none`
- Reserve: `нет`
- Import allowed: `НЕТ (no, not_ready)`

Question text:

```text
На персидском языке дворец называют сараем
```

Answer options:

- A: правда
- B: ложь

Host note / comments:

```text
(empty)
```

Why Victor is needed: Нужно подтвердить факт/правда-ложь и источник: ответ не был явно указан в текущих заметках.

### Row 8: `v2_edited_q008`

- Editor row / slot: `8`
- Round / block: `v2_warmup_oath`
- Question type: `plain_text`
- Difficulty: `easy`
- Status / next action: `needs_review` / Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 13. Аудит action=keep. answer_type=true_false.
- Current answer field: `(пусто)`
- Answer status: `НЕТ — заполнить/проверить`
- Media ref: `none`
- Selected image filename: `none`
- Image status: `нет`
- Reveal timing: `none`
- Reserve: `нет`
- Import allowed: `НЕТ (no, not_ready)`

Question text:

```text
У игры «Монополия» есть специальная горячая линия для урегулирования семейных конфликтов из-за споров о покупке недвижимости и траты денег?
```

Answer options:

- A: правда
- B: ложь

Host note / comments:

```text
(empty)
```

Why Victor is needed: Нужно подтвердить факт/правда-ложь и источник: формулировка звучит как спорный факт.

### Row 29: `v2_edited_q029`

- Editor row / slot: `29`
- Round / block: `v2_signs_objects`
- Question type: `image_clue`
- Difficulty: `medium`
- Status / next action: `needs_video_check` / Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 14. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Медиа требуется подобрать/проверить; в app/static не копировалось. Решение Виктора: Кеша из Блудного попугая пока не финализировать; нужен точный кадр/видео.
- Current answer field: `(пусто)`
- Answer status: `НЕТ — заполнить/проверить`
- Media ref: `v2_edited_parrot_cage`
- Selected image filename: `none`
- Image status: `needs_mapping`
- Reveal timing: `with_question`
- Reserve: `да`
- Import allowed: `НЕТ (no, not_ready)`

Question text:

```text
Благодаря чему Кеша из мультфильма «Блудный попугай» смог выбраться из клетки?
```

Answer options:

- A: пила
- B: взрывное устройство
- C: карате
- D: просто отодвинул затвор

Host note / comments:

```text
Host note: (Тут нужна картинка на ответ или видео)
Медиа из source_docs: проверить файл в source_docs.
```

Why Victor is needed: Нужно решение по видео/медиа и правильному варианту: строка зависит от визуального материала.

### Row 37: `v2_edited_q037`

- Editor row / slot: `37`
- Round / block: `v2_reserve`
- Question type: `plain_text`
- Difficulty: `medium`
- Status / next action: `needs_source_check` / Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 22. Аудит action=rewrite. answer_type=multiple_choice. Решение Виктора: предмет гигиены через армию — reserve/source_check.
- Current answer field: `(пусто)`
- Answer status: `НЕТ — заполнить/проверить`
- Media ref: `none`
- Selected image filename: `none`
- Image status: `нет`
- Reveal timing: `none`
- Reserve: `да`
- Import allowed: `НЕТ (no, not_ready)`

Question text:

```text
Какой предмет гигиены был централизованно введен через армию?
```

Answer options:

- A: бритва
- B: зубная щетка
- C: ушные палочки
- D: расческа

Host note / comments:

```text
Host note: Резервная строка: использовать только после редакторского отбора.
```

Why Victor is needed: Нужно подтвердить правильный вариант и источник: строка отмечена как требующая source check.

## Safety note

- This is a read-only extraction from the workbook.
- No XLSX edits were made.
- No import, DB mutation, production action, LIVE01 touch, media copy, migration, deploy, or `clear_existing` was performed.
- Workbook safety remains governed by `safe_to_import=no` and `import_status=not_ready`.
