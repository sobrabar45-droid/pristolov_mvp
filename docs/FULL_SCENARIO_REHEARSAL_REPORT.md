# Full Scenario Rehearsal Report

## Контекст

- Сценарий: `season1_mvp_live_v2`
- Dev room: `IRON01`
- Цель: полный боевой runtime-прогон от старта до terminal state

## Реальная последовательность `season1_mvp_live_v2`

1. `stage_intro`
2. `stage_truth_lie_opening`
3. `stage_four_options`
4. `stage_map_entry`
5. `stage_diplomacy_1`
6. `stage_crest`
7. `stage_free_play`
8. `stage_duels`
9. `stage_court`
10. `stage_final_show`
11. `terminal state`

## Что подтверждено

- `system stages` открываются как `phase`, а не как обычные quiz rounds.
- `host rounds` идут через существующий `host_round` pipeline.
- Переход `court -> final_show` работает.
- Переход `final_show -> terminal` работает.
- Terminal state после полного прогона чистый.

## Найденный и исправленный баг

### Симптом

После `host-continue` на `stage_final_show` сам `host_round` завершался, но `GamePhase` с `phase_type="host_round"` оставалась активной.

### Последствие

- `master` и `TV` продолжали видеть stale `host_round` envelope.
- Director уже доходил до terminal state, но UI-контур ещё держал активную phase-оболочку.

### Исправление

Исправление внесено в:

- [D:\Projects\pristolov_mvp\app\routes\dev.py](D:/Projects/pristolov_mvp/app/routes/dev.py)

Логика:

- после `host_continue` закрывать `host_round` phase,
- если больше не осталось `active` / `completed_waiting_host` rounds.

## Рискованные переходы

- `stage_duels -> stage_court`
- `court_finished -> stage_final_show`
- `stage_final_show -> terminal`

## Итоговый terminal state director

- `current_round = null`
- `next_round = null`
- `last_completed_round = stage_final_show`
- `active_host_round = null`
- `active_system_stage_phase = null`
- `can_start_next = false`
- `can_advance = false`
- `scenario_finished = true`

## Итоговый master / tv state

- `active_phases = []`
- `active_host_round = null`
- `current_question = null`
- `court_runtime = null`

## Скрины

- [master_full_rehearsal_final_active.png](D:/Projects/pristolov_mvp/tmp/gui_smoke/master_full_rehearsal_final_active.png)
- [tv_full_rehearsal_final_active.png](D:/Projects/pristolov_mvp/tmp/gui_smoke/tv_full_rehearsal_final_active.png)
- [master_full_rehearsal_terminal_clean.png](D:/Projects/pristolov_mvp/tmp/gui_smoke/master_full_rehearsal_terminal_clean.png)
- [tv_full_rehearsal_terminal_clean.png](D:/Projects/pristolov_mvp/tmp/gui_smoke/tv_full_rehearsal_terminal_clean.png)

## Итог

- `season1_mvp_live_v2` считается `runtime-smoke` пройденным.
- Полный сценарный контур подтверждён от старта до terminal state.
