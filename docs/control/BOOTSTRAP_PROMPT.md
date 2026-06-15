# BOOTSTRAP_PROMPT

## Goal
Treasurer Shop V1/V1.1 migration checkpoint handoff (runtime already completed).

## Initial context
- `Gold Desk` exists (checkpoint `2537910`).
- Treasurer Shop закрыт по V1.1 (`50d2a01`), runtime уже в репозитории.
- Следующий шаг: audit-only выбор следующего узкого кандидата.

## Exact bootstrap checklist
1. `git status --short`.
2. If tree dirty — stop.
3. Read control docs in order:
   - `docs/control/CURRENT_STATE.md`
   - `docs/control/DECISIONS.md`
   - `docs/control/OPEN_TASKS.md`
   - `docs/control/CHANGELOG.md`
   - `docs/control/CHECKPOINT_TREASURER_SHOP_V1_1.md` (если отсутствует — создать из этого prompt).
   - `docs/control/NEXT_CODEX_TASK.md`
4. Verify no runtime/template edits are required in this migration checkpoint task.
5. Review commit history for required closure commits (listed in CHECKPOINT).

## Runtime requirements for next steps
- Do not change runtime code in this handoff step.
- Keep operator-mediated flow unchanged: `/dev/treasurer-shop/{room_code}` only.
- Keep `player_room` без purchase buttons.
- Keep bar/social-only behavior for V1.1:
  - `author_tea`, `lemonade_02`, `sobranie_pizza`, `anna_pavlova`.
- Keep alcohol/legal-deferred items deferred:
  - `champagne_premier`, `tincture_set`, `shihan_beer_giraffe`, `beer_set_any`.

## Required output
- Добавить / обновить контрольные документы для миграции.
- Не вносить runtime/runtime-template изменения.
- Сформировать commit:
  - `Add Treasurer Shop V1.1 migration checkpoint`.
