# Question Bank V2 Authoring Draft

## Что это

`question_bank_v2_authoring_draft.xlsx` — первый локальный редакторский XLSX-черновик для следующей коммерческой игры `приСтолов`.

Файл нужен для Виктора и контент-редактуры: смотреть структуру, идеи вопросов, медиа-флаги, резерв, ручное аудио и статусы готовности.

Это только authoring draft. Файл не import-ready.

## Статус безопасности

- Нет DB mutation.
- Нет production action.
- Нет LIVE01 touch.
- Import не запускался.
- Migrations не запускались.
- Медиафайлы не создавались и не копировались в `app/static/questions_media`.
- Все строки вопросов имеют `safe_to_import=no`.
- Все строки вопросов имеют `import_status=not_ready`.
- `clear_existing=true` запрещён без отдельного явного разрешения и rollback-плана.

## Листы workbook

1. `questions` — 48 редакторских строк-кандидатов.
2. `media_assets` — 13 планируемых визуальных/image кандидатов.
3. `manual_audio` — 4 ручных/offline аудиомомента для ведущего.
4. `review_status` — 48 строк для отслеживания проверки.

## Правило по ручному аудио

Manual audio работает только вручную: host-operated/offline.

Приложение не должно проигрывать аудио. В строках ручного аудио стоит `media_type=none`, в tags есть `manual_audio`, и перед живой игрой нужен текстовый fallback.

## Правило по изображениям

Картинки ещё требуют asset/source checks.

Ни один image asset не считается существующим или финально готовым. Для визуальных вопросов нужно отдельно проверить источник/права, совпадение filename и `media_ref`, открытие локально и читаемость на ТВ.

## Правило импорта

Import возможен только после review и отдельного dry-run approval.

Безопасные будущие значения:

```text
dry-run first
clear_existing=false
target_round_code=v2_commercial_test_round
no LIVE01
```

## Следующие шаги

1. Victor/content review.
2. Заполнить финальные prompts/options/correct answers.
3. Выбрать финальные 10-12 image rows.
4. Подготовить media assets.
5. Перевести строки в `ready_for_dry_run` только после проверки.
6. Запускать dry-run import только после явного разрешения.
