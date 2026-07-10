# Edited DOCX Source Audit

Source folder: `docs/question_bank_v2/source_docs/`

Source DOCX found: `Вопросы на игру Пристолов Редакиция.docx`

This audit extracts and classifies Victor-edited question candidates before editing the XLSX.

## Outputs

- `edited_docx_question_extraction.md` - extracted question candidates with options/answers/media notes.
- `edited_docx_v2_mapping.md` - suggested V2 round/type/action mapping.
- `edited_docx_media_needs.md` - media notes and source image file mapping.

## Extraction summary

- Sections detected: ПРАВДА ИЛИ ПИЗДЁЖ?, ВАРИАНТЫ ОТВЕТОВ:, ВОПРОСЫ БЕЗ ВАРИАНТОВ:
- Extracted question candidates: 55
- Media-linked question candidates: 17
- Source image files in folder: 22

## Safety

- No import.
- No DB mutation.
- No runtime changes.
- No production.
- No LIVE01.
- No `clear_existing=true`.
- No media copying.
- No XLSX edits.

## Limitations

- Classification is heuristic and needs Victor/content review.
- Facts and answers were not independently verified.
- Similarity to previously used LIVE01 questions relies on Victor-edited source claim; no DB/LIVE comparison was run.
- Media file rights/source status is unknown until separately checked.
