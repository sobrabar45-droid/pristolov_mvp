# Question Bank V2: first text-only dry-run scope

Purpose: define the first safest dry-run scope for Question Bank V2 without running import or changing the workbook.

Victor decision: first dry-run should use text-only rows only. Exclude all visual rows, reserve rows, and cut rows.

Sources:

- `docs/question_bank_v2/question_bank_v2_authoring_draft.xlsx`
- `docs/question_bank_v2/QUESTION_BANK_V2_CONTROLLED_DRY_RUN_PLAN.md`
- `docs/question_bank_v2/QUESTION_BANK_V2_IMPORT_READINESS_AUDIT.md`

## 1. Scope summary

| Group | Count | Slots |
| --- | ---: | --- |
| Text-only dry-run scope | 21 | 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 35 |
| Visual active rows excluded from first dry-run | 9 | 2, 6, 16, 30, 31, 32, 33, 34, 36 |
| Reserve rows excluded | 13 | 29, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48 |
| Cut rows excluded | 5 | 1, 10, 12, 17, 28 |

Safety gates remain closed:

- `safe_to_import` values: `['no']`
- `import_status` values: `['not_ready']`
- no import executed;
- no DB mutation;
- no production;
- no LIVE01;
- no media copy.

## 2. Text-only rows selected for first dry-run

| Slot | Code | Round | Type | Prompt | Correct answer draft | Status |
| ---: | --- | --- | --- | --- | --- | --- |
| 3 | `v2_edited_q003` | `v2_warmup_oath` | `plain_text` | В Польше Винни-Пуха называют Кубусь Пухатек | правда | `needs_review` |
| 4 | `v2_edited_q004` | `v2_warmup_oath` | `plain_text` | Курица проглатывает камешки, чтобы восполнить в организме недостающие минералы | ложь | `needs_review` |
| 5 | `v2_edited_q005` | `v2_warmup_oath` | `plain_text` | Матросы французского флота работали в условиях низких потолков на палубах кораблей. Помпоны на головных уборах служили для чистки потолков. | ложь | `needs_review` |
| 7 | `v2_edited_q007` | `v2_warmup_oath` | `plain_text` | На персидском языке дворец называют сараем | правда | `needs_review` |
| 8 | `v2_edited_q008` | `v2_warmup_oath` | `plain_text` | У игры «Монополия» есть специальная горячая линия для урегулирования семейных конфликтов из-за споров о покупке недвижимости и траты денег? | правда | `needs_review` |
| 9 | `v2_edited_q009` | `v2_warmup_oath` | `plain_text` | Астероиды падают на Землю в среднем каждые 2 недели | правда | `needs_review` |
| 11 | `v2_edited_q011` | `v2_warmup_oath` | `plain_text` | Законодательство США допускало отправку детей по почте | правда | `needs_review` |
| 13 | `v2_edited_q013` | `v2_warmup_oath` | `plain_text` | В фирменной пицце «Собрание» содержится перец халапеньо | правда | `needs_review` |
| 14 | `v2_edited_q014` | `v2_warmup_oath` | `plain_text` | Samsung тестирует смартфоны на прочность с помощью робота в форме ягодиц | правда | `needs_review` |
| 15 | `v2_edited_q015` | `v2_warmup_oath` | `plain_text` | Маленький кармашек в джинсах предназначен для хранения презерватива. | ложь | `needs_review` |
| 18 | `v2_edited_q018` | `v2_warmup_oath` | `plain_text` | Черепахи могут дышать попой! | правда | `needs_review` |
| 19 | `v2_edited_q019` | `v2_warmup_oath` | `plain_text` | Самолетный черный ящик имеет оранжевый цвет | правда | `needs_review` |
| 20 | `v2_edited_q020` | `v2_warmup_oath` | `plain_text` | У туристов есть традиция оставлять друг другу записки между плит в пирамиде Хеопса | ложь | `needs_review` |
| 21 | `v2_edited_q021` | `v2_stories_tricks` | `plain_text` | В кинофильме «Операция Ы» Трус, Бывалый и Балбес выступают в роли последователей известного русского хирурга Николая Пирогова. Как называется медицинское средство, которое они используют? | хлороформ | `needs_review` |
| 22 | `v2_edited_q022` | `v2_signs_objects` | `plain_text` | Предприниматель Хироки Тэраи открыл необычный дворец для церемоний. Какие события там отмечали? | разводы | `needs_review` |
| 23 | `v2_edited_q023` | `v2_stories_tricks` | `plain_text` | Иоанна Хмелевская считала, если дама перешагнула отметку 90, мужчина вправе кое-чего себе позволить не делать. В чем измеряется это самое 90? | килограммы | `needs_source_check` |
| 24 | `v2_edited_q024` | `v2_signs_objects` | `plain_text` | Однажды Джон Шепард-Барон кое-куда опоздал и не смог сделать важную для него вещь. После этого он изобрел это: | банкомат | `needs_review` |
| 25 | `v2_edited_q025` | `v2_stories_tricks` | `plain_text` | Представим, что вы живете в Дании, вам исполнилось 25 лет, и тут родня начинает посыпать вас корицей. Что это значит? | нет второй половинки | `needs_review` |
| 26 | `v2_edited_q026` | `v2_signs_objects` | `plain_text` | Какое из этих блюд названо по имени повара? | салат Цезарь | `needs_review` |
| 27 | `v2_edited_q027` | `v2_stories_tricks` | `plain_text` | У кого из этих животных самый длинный язык? | муравьед | `needs_review` |
| 35 | `v2_edited_q035` | `v2_stories_tricks` | `plain_text` | Эта вещь что-то напоминает. Туда можно залить воду. Что это? | фен | `needs_source_check` |

## 3. Visual rows excluded from first dry-run

These rows are not rejected; they are only excluded from the first text-only dry-run because they require media preparation/checks.

| Slot | Code | media_ref | Image status | Reason excluded |
| ---: | --- | --- | --- | --- |
| 2 | `v2_edited_q002` | `v2_edited_playing_card_money` | `needs_mapping` | visual/media row; not part of text-only dry-run |
| 6 | `v2_edited_q006` | `v2_edited_backrub` | `source_available_unverified` | visual/media row; not part of text-only dry-run |
| 16 | `v2_edited_q016` | `v2_edited_banany` | `needs_crop_or_replace` | visual/media row; not part of text-only dry-run |
| 30 | `v2_edited_q030` | `v2_edited_knocker_up` | `source_available_unverified` | visual/media row; not part of text-only dry-run |
| 31 | `v2_edited_q031` | `v2_edited_beauty_contest` | `needs_replacement` | visual/media row; not part of text-only dry-run |
| 32 | `v2_edited_q032` | `v2_edited_two_penny_hangover` | `source_available_unverified` | visual/media row; not part of text-only dry-run |
| 33 | `v2_edited_q033` | `v2_edited_bear_back` | `needs_source_check` | visual/media row; not part of text-only dry-run |
| 34 | `v2_edited_q034` | `v2_edited_vinaigrette_box` | `source_available_unverified` | visual/media row; not part of text-only dry-run |
| 36 | `v2_edited_q036` | `v2_edited_buttonhook` | `source_available_unverified` | visual/media row; not part of text-only dry-run |

## 4. Reserve and cut rows excluded

| Slot | Code | Exclusion reason |
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
| 1 | `v2_edited_q001` | cut |
| 10 | `v2_edited_q010` | cut |
| 12 | `v2_edited_q012` | cut |
| 17 | `v2_edited_q017` | cut |
| 28 | `v2_edited_q028` | cut |

## 5. Future dry-run command template - NOT EXECUTED

This is a planning template only. It must not be run until Victor explicitly approves a local non-LIVE dry-run and a filtered/import-prep artifact exists for the selected text-only scope.

```powershell
cd D:\Projects\pristolov_mvp

# Example only. Do not run yet.
# Use a future filtered text-only artifact, not the authoring workbook, unless a separate import-prep task confirms compatibility.
curl.exe -X POST "http://127.0.0.1:8000/dev/questions/import?room_code=NON_LIVE_ROOM&dry_run=true&clear_existing=false" ^
  -H "X-Admin-Token: <LOCAL_DEV_ADMIN_TOKEN>" ^
  -F "file=@docs/question_bank_v2/<future_text_only_import_candidate>.xlsx"
```

Required constraints:

- `dry_run=true`;
- `clear_existing=false`;
- local/non-LIVE only;
- no production;
- no LIVE01;
- no media files required for this first text-only dry-run;
- do not use reserve/cut rows;
- do not mutate the authoring workbook into import-ready state without a separate explicit task.

## 6. Next recommended step

Create a separate filtered text-only import candidate artifact for these 21 rows, still with safety review before any dry-run command is executed.

## 7. Non-actions in this task

- No workbook edits.
- No import.
- No DB mutation.
- No production action.
- No LIVE01 touch.
- No media copy.
- No runtime/template/route changes.
- No deploy/migration/restart.
- No `clear_existing`.
