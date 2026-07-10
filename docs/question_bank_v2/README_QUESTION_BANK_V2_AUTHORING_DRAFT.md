# Question Bank V2 Authoring Draft

## Что это

`question_bank_v2_authoring_draft.xlsx` — локальный редакторский XLSX-черновик для следующей коммерческой игры `приСтолов`.

Файл нужен Виктору и контент-редактору, чтобы спокойно проверить вопросы, варианты ответов, правильные ответы, картинки, ручные музыкальные моменты, заметки ведущего и статусы готовности.

Это только authoring draft. Файл не import-ready.

## Что изменено для удобства редактуры

В workbook добавлены русские человекочитаемые вкладки:

1. `Редактору` — короткая инструкция: где писать, что проверять, чего не делать.
2. `Вопросы для редактуры` — основная рабочая таблица для Виктора: текст вопроса, варианты, правильный ответ, картинка, музыка, заметка ведущему, статус и комментарий редактора.
3. `Статусы RU` — расшифровка технических статусов простым языком.

Технические листы сохранены:

1. `questions` — импортная структура, пока не готовая к импорту.
2. `media_assets` — source-картинки и будущие media_ref.
3. `manual_audio` — ручные/offline аудиомоменты.
4. `review_status` — статусы проверки.

## Как редактировать

Работать лучше с листом `Вопросы для редактуры`.

Редактор может править или комментировать:

- текст вопроса;
- варианты A/B/C/D;
- черновик правильного ответа;
- необходимость картинки;
- заметку ведущему;
- сложность;
- статус редактуры;
- комментарии редактора.

После редакторского прохода Codex может отдельной задачей перенести утверждённые правки обратно в технические поля и подготовить dry-run план.

## Статус безопасности

- Нет import.
- Нет DB mutation.
- Нет production action.
- Нет LIVE01 touch.
- Migrations не запускались.
- Медиафайлы не копировались в `app/static/questions_media`.
- Все строки вопросов имеют `safe_to_import=no`.
- Все строки вопросов имеют `import_status=not_ready`.
- `clear_existing=true` запрещён без отдельного явного разрешения и rollback-плана.

## Правило по изображениям

Изображения пока являются source materials.

Перед использованием в игре нужно отдельно проверить:

- источник и права;
- соответствие `media_ref` и будущего filename;
- читаемость на ТВ;
- момент показа;
- fallback, если картинка не откроется.

## Правило по ручному аудио

Manual audio работает только вручную: host-operated/offline.

Приложение не должно проигрывать аудио. Для каждого музыкального момента нужен fallback словами.

## Обновление от edited DOCX source

Workbook populated from `docs/question_bank_v2/source_docs/Вопросы на игру Пристолов Редакиция.docx` through the committed edited DOCX source audit.

- Source audit reference: commit `4d15bce Add edited DOCX question source audit`.
- Source materials reference: commit `98c1e5d Add question bank v2 source materials`.
- XLSX update reference: commit `511b363 Update question bank v2 XLSX from edited DOCX`.
- `questions` contains Russian candidate prompts/options/answer drafts where the source explicitly provided them.
- All rows remain authoring-only: `safe_to_import=no` and `import_status=not_ready`.
- no import; no DB mutation; no production action; no LIVE01 touch.
- Images remain source materials only under `docs/question_bank_v2/source_docs/`.
- `media_assets.source_rights_status=needs_check` for source image candidates.
- Manual audio remains host-operated/offline only; no runtime audio dependency was added.

## Следующие шаги

1. Victor/content review on `Вопросы для редактуры`.
2. Проверить факты и правильные ответы.
3. Выбрать финальные 10-12 image questions.
4. Проверить source rights и TV readability для картинок.
5. Подготовить отдельную задачу на dry-run import только после явного approval.
6. Не использовать LIVE01.

## Обновление fact-check/media от Виктора

Применены редакторские решения Виктора по fact-check и визуальным материалам.

Что обновлено в workbook:

- спорные вопросы помечены `cut`;
- утверждённые вопросы оставлены в редакторском статусе `needs_review`;
- визуальные вопросы размечены через `needs_media`, `needs_source_check`, `needs_replacement`, `needs_crop_or_replace`, `needs_clean_source` или `needs_video_check`;
- обновлены draft правильных ответов для утверждённых multiple-choice вопросов;
- обновлены `media_ref`, `asset_status`, `reveal_timing` и заметки по source-картинкам;
- лист `Вопросы для редактуры` синхронизирован с техническими листами;
- лист `Статусы RU` дополнен новыми редакторскими статусами.

Safety сохраняется:

- все строки остаются `safe_to_import=no`;
- все строки остаются `import_status=not_ready`;
- no import;
- no DB mutation;
- no production action;
- no LIVE01 touch;
- no media copy to `app/static/questions_media`;
- no runtime/template/route changes.

## Рабочая таблица после fact-check/media решений

Workbook cleaned up for practical content work:

- main sheet `Вопросы для редактуры` now contains only active/non-cut questions;
- questions removed by Victor are moved to separate sheet `Убрано`;
- active editor sheet now shows answer completeness, selected image file/target, image status, reveal timing, and next action as visible columns;
- selected visual files are tied to question rows through `media_ref` and target filename/status columns;
- unresolved answers are explicitly marked as `НЕТ — заполнить/проверить` instead of being hidden in technical notes;
- technical sheets are preserved for traceability, but workbook remains authoring-only.

Counts after cleanup:

- active editor rows: 44;
- removed/cut rows: 4;
- all technical question rows still have `safe_to_import=no`;
- all technical question rows still have `import_status=not_ready`.

Safety remains unchanged: no import, no DB mutation, no production action, no LIVE01 touch, no media copy to `app/static/questions_media`, no runtime/template/route changes.
