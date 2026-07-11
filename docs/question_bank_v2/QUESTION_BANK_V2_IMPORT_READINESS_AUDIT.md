# Question Bank V2: import-readiness audit

Источник: `docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx`.

Аудит read-only: workbook открыт только для чтения, изменения в XLSX не выполнялись, import не запускался.

## 1. Executive summary

| Check | Result |
| --- | ---: |
| Active editor rows | 43 |
| Active non-reserve rows | 30 |
| Reserve rows in active editor sheet | 13 |
| Rows with complete question + answer | 42 |
| Blocking unresolved non-reserve rows | 0 |
| Reserve unresolved rows | 1 |
| Visual rows | 17 |
| Visual rows with media_ref | 17 |
| Visual rows missing media_ref | 0 |
| Conservative dry-run planning candidates | 27 |

Safety gates:

- `safe_to_import` values: `['no']`
- `import_status` values: `['not_ready']`
- rows with changed/import-ready safety values: `0`

## 2. Active vs reserve rows

| Group | Count | Slots |
| --- | ---: | --- |
| Active non-reserve | 30 | 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36 |
| Reserve | 13 | 29, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48 |
| Technical cut rows | 5 | 1, 10, 12, 17, 28 |

## 3. Question and answer completeness

| Group | Count | Slots |
| --- | ---: | --- |
| Complete question + answer | 42 | 2, 3, 4, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48 |
| Blocking unresolved non-reserve | 0 | none |
| Reserve unresolved | 1 | 29 |

## 4. Visual/media rows

| Slot | Code | Reserve | media_ref | Selected file | Image status | Reveal timing |
| ---: | --- | --- | --- | --- | --- | --- |
| 2 | `v2_edited_q002` | нет | `v2_edited_playing_card_money` | `none` | `needs_mapping` | `with_question` |
| 6 | `v2_edited_q006` | нет | `v2_edited_backrub` | `v2_edited_backrub.jpg` | `source_available_unverified` | `after_answer` |
| 16 | `v2_edited_q016` | нет | `v2_edited_banany` | `v2_edited_banany.jfif` | `needs_crop_or_replace` | `with_question` |
| 29 | `v2_edited_q029` | да | `v2_edited_parrot_cage` | `none` | `needs_mapping` | `with_question` |
| 30 | `v2_edited_q030` | нет | `v2_edited_knocker_up` | `v2_edited_knocker_up.jpeg` | `source_available_unverified` | `with_question` |
| 31 | `v2_edited_q031` | нет | `v2_edited_beauty_contest` | `v2_edited_beauty_contest.png` | `needs_replacement` | `with_question` |
| 32 | `v2_edited_q032` | нет | `v2_edited_two_penny_hangover` | `v2_edited_two_penny_hangover.jpg` | `source_available_unverified` | `with_question` |
| 33 | `v2_edited_q033` | нет | `v2_edited_bear_back` | `v2_edited_bear_back.png` | `needs_source_check` | `with_question` |
| 34 | `v2_edited_q034` | нет | `v2_edited_vinaigrette_box` | `v2_edited_vinaigrette_box.jpg` | `source_available_unverified` | `with_question` |
| 36 | `v2_edited_q036` | нет | `v2_edited_buttonhook` | `v2_edited_buttonhook.jpg` | `source_available_unverified` | `with_question` |
| 40 | `v2_edited_q040` | да | `v2_edited_time_salad` | `none` | `needs_mapping` | `with_question` |
| 41 | `v2_edited_q041` | да | `v2_edited_kodak_2` | `v2_edited_kodak_2.jpg` | `source_available_unverified` | `with_question` |
| 42 | `v2_edited_q042` | да | `v2_edited_microwave` | `v2_edited_microwave.jpg` | `source_available_unverified` | `with_question` |
| 43 | `v2_edited_q043` | да | `v2_edited_dishwasher` | `v2_edited_dishwasher.jfif` | `source_available_unverified` | `with_question` |
| 44 | `v2_edited_q044` | да | `v2_edited_ratcatcher_2` | `v2_edited_ratcatcher_2.jfif` | `source_available_unverified` | `with_question` |
| 45 | `v2_edited_q045` | да | `v2_edited_time_seller` | `v2_edited_time_seller.jpg` | `source_available_unverified` | `with_question` |
| 48 | `v2_edited_q048` | да | `v2_edited_card_kings` | `v2_edited_card_kings.jpg` | `needs_clean_source` | `with_question` |

## 5. Visual rows needing source/replacement/crop/check

| Slot | Code | media_ref | Image status | Next action |
| ---: | --- | --- | --- | --- |
| 2 | `v2_edited_q002` | `v2_edited_playing_card_money` | `needs_mapping` | Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 7. Аудит action=keep. answer_type=true_false. risk_flags=needs_media. Медиа требуется подобрать/проверить; в app/static не копировалось. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 6 | `v2_edited_q006` | `v2_edited_backrub` | `source_available_unverified` | Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 11. Аудит action=keep. answer_type=true_false. risk_flags=needs_media, brand_fact_check. Исходный asset есть в docs/question_bank_v2/source_docs/BackRub.jpg; не скопирован в app/static. Решение Виктора: BackRub.jpg использовать как reveal/support image для вопроса про Google BackRub. |
| 16 | `v2_edited_q016` | `v2_edited_banany` | `needs_crop_or_replace` | Источник: edited DOCX, раздел "ПРАВДА ИЛИ ПИЗДЁЖ?", № 21. Аудит action=keep. answer_type=true_false. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Бананы.jfif; не скопирован в app/static. Решение Виктора: вопрос про бананы оставить как есть; картинку Бананы.jfif нужно кропнуть или заменить из-за чёрных полей. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 29 | `v2_edited_q029` | `v2_edited_parrot_cage` | `needs_mapping` | не блокирует подготовку; можно вернуться после проверки кадра/видео |
| 30 | `v2_edited_q030` | `v2_edited_knocker_up` | `source_available_unverified` | Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 15. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/15. женщина будит жителей.jpeg; не скопирован в app/static. Решение Виктора: женщина будит жителей — использовать как визуальный вопрос. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 31 | `v2_edited_q031` | `v2_edited_beauty_contest` | `needs_replacement` | Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 16. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/16. конкурс красоты.png; не скопирован в app/static. Решение Виктора: конкурс красоты/лодыжки оставить только после замены картинки на чистый источник; текущая выглядит обработанной. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 32 | `v2_edited_q032` | `v2_edited_two_penny_hangover` | `source_available_unverified` | Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 17. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/17. Двухпенсовый подвес.jpg; не скопирован в app/static. Решение Виктора: двухпенсовый подвес / люди спят на верёвках — использовать как визуальный вопрос. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 33 | `v2_edited_q033` | `v2_edited_bear_back` | `needs_source_check` | Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 18. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/18. Медведь).png; не скопирован в app/static. Решение Виктора: медведь лечит спину — оставить, но нужен source check. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 34 | `v2_edited_q034` | `v2_edited_vinaigrette_box` | `source_available_unverified` | Источник: edited DOCX, раздел "ВАРИАНТЫ ОТВЕТОВ:", № 19. Аудит action=needs_media. answer_type=multiple_choice. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/19. Уксусница.jpg; не скопирован в app/static. Решение Виктора: уксусница / коробочка с резким запахом — использовать как визуальный/object question. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 40 | `v2_edited_q040` | `v2_edited_time_salad` | `needs_mapping` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 2. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Время.png; не скопирован в app/static. |
| 41 | `v2_edited_q041` | `v2_edited_kodak_2` | `source_available_unverified` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 4. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Кодак-2.jpg; не скопирован в app/static. Решение Виктора: Kodak-2 использовать как основной визуал; Kodak-1 не основной. |
| 42 | `v2_edited_q042` | `v2_edited_microwave` | `source_available_unverified` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 5. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Микроволновка.jpg; не скопирован в app/static. Решение Виктора: микроволновка / растаявшая конфета — использовать как визуальный вопрос. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 43 | `v2_edited_q043` | `v2_edited_dishwasher` | `source_available_unverified` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 6. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Посудомойка.jfif; не скопирован в app/static. Решение Виктора: Жозефина Кокрейн / посудомоечная машина — использовать как визуальный вопрос. |
| 44 | `v2_edited_q044` | `v2_edited_ratcatcher_2` | `source_available_unverified` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 7. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Крысолов-2.jfif; не скопирован в app/static. |
| 45 | `v2_edited_q045` | `v2_edited_time_seller` | `source_available_unverified` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 8. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Продавщица времени.jpg; не скопирован в app/static. Решение Виктора: выбрать лучший вариант между Время.jpg и Продавщица времени.jpg после просмотра. | Правильный ответ заполнен из существующей заметки/вариантов; всё ещё нужен редакторский review. |
| 48 | `v2_edited_q048` | `v2_edited_card_kings` | `needs_clean_source` | Источник: edited DOCX, раздел "ВОПРОСЫ БЕЗ ВАРИАНТОВ:", № 12. Аудит action=needs_media. answer_type=open_answer. risk_flags=needs_media. Исходный asset есть в docs/question_bank_v2/source_docs/Короли-карты.jpg; не скопирован в app/static. Решение Виктора: Короли-карты.jpg требует clean source; текущий файл похож на изображение с источником/водяным знаком. |

## 6. Conservative dry-run planning candidates

These rows could become dry-run candidates only after a separate explicit approval and import-prep pass. This audit does not mark them ready.

| Slot | Code | Round | Type | Visual | Status |
| ---: | --- | --- | --- | --- | --- |
| 3 | `v2_edited_q003` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 4 | `v2_edited_q004` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 5 | `v2_edited_q005` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 6 | `v2_edited_q006` | `v2_warmup_oath` | `plain_text` | yes | `needs_media` |
| 7 | `v2_edited_q007` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 8 | `v2_edited_q008` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 9 | `v2_edited_q009` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 11 | `v2_edited_q011` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 13 | `v2_edited_q013` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 14 | `v2_edited_q014` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 15 | `v2_edited_q015` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 18 | `v2_edited_q018` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 19 | `v2_edited_q019` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 20 | `v2_edited_q020` | `v2_warmup_oath` | `plain_text` | no | `needs_review` |
| 21 | `v2_edited_q021` | `v2_stories_tricks` | `plain_text` | no | `needs_review` |
| 22 | `v2_edited_q022` | `v2_signs_objects` | `plain_text` | no | `needs_review` |
| 23 | `v2_edited_q023` | `v2_stories_tricks` | `plain_text` | no | `needs_source_check` |
| 24 | `v2_edited_q024` | `v2_signs_objects` | `plain_text` | no | `needs_review` |
| 25 | `v2_edited_q025` | `v2_stories_tricks` | `plain_text` | no | `needs_review` |
| 26 | `v2_edited_q026` | `v2_signs_objects` | `plain_text` | no | `needs_review` |
| 27 | `v2_edited_q027` | `v2_stories_tricks` | `plain_text` | no | `needs_review` |
| 30 | `v2_edited_q030` | `v2_signs_objects` | `image_clue` | yes | `needs_media` |
| 32 | `v2_edited_q032` | `v2_signs_objects` | `image_clue` | yes | `needs_media` |
| 33 | `v2_edited_q033` | `v2_signs_objects` | `image_clue` | yes | `needs_source_check` |
| 34 | `v2_edited_q034` | `v2_signs_objects` | `image_clue` | yes | `needs_media` |
| 35 | `v2_edited_q035` | `v2_stories_tricks` | `plain_text` | no | `needs_source_check` |
| 36 | `v2_edited_q036` | `v2_signs_objects` | `image_clue` | yes | `needs_media` |

## 7. Rows that must remain excluded/reserve

| Slot | Code | Reason |
| ---: | --- | --- |
| 29 | `v2_edited_q029` | reserve, needs_video_check |
| 37 | `v2_edited_q037` | reserve |
| 38 | `v2_edited_q038` | reserve |
| 39 | `v2_edited_q039` | reserve |
| 40 | `v2_edited_q040` | reserve |
| 41 | `v2_edited_q041` | reserve |
| 42 | `v2_edited_q042` | reserve |
| 43 | `v2_edited_q043` | reserve |
| 44 | `v2_edited_q044` | reserve |
| 45 | `v2_edited_q045` | reserve |
| 46 | `v2_edited_q046` | reserve |
| 47 | `v2_edited_q047` | reserve |
| 48 | `v2_edited_q048` | reserve |
| 1 | `v2_edited_q001` | technical cut row |
| 10 | `v2_edited_q010` | technical cut row |
| 12 | `v2_edited_q012` | technical cut row |
| 17 | `v2_edited_q017` | technical cut row |
| 28 | `v2_edited_q028` | technical cut row |

## 8. Remaining blockers before controlled dry-run planning

- Some visual rows still need source/status/media handling before they should be considered dry-run-ready.

Required before any controlled dry-run planning:

- choose final candidate rows explicitly;
- decide which visual rows are allowed into the dry-run set;
- prepare/copy final media only in a separate approved task;
- keep reserve/cut rows excluded;
- keep `dry_run=true`;
- keep `clear_existing=false`;
- do not touch `LIVE01`;
- do not run import without explicit approval.

## 9. Read-only confirmation

- Workbook opened read-only.
- No workbook save was performed.
- No XLSX changes were made.
- No import, DB mutation, production action, LIVE01 touch, media copy, migration, deploy, or `clear_existing` was performed.
