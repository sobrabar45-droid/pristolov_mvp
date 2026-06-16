# Last Whisper TV Copy Rollout

## Commit

- `8d91c85` — Shorten Last Whisper TV copy

## Date

- 2026-06-16

## Scope

- Changed only:
  - `app/templates/tv_mode_tv_state.html`
- Replaced clipped Last Whisper TV subtitle:
  - from: `Дома собирают последние слухи и готовятся к финальному объявлению.`
  - to: `Интриги перед финалом`
- Gameplay logic unchanged:
  - Last Whisper mechanics untouched
  - phase counters untouched (including `Последний Шёпот • Готово 0/1 Домов`)

## Rollout status

- Production rollout was completed on pristolov.ru.
- Template change propagated to production.
- `compileall` passed during rollout checks.
- `pristolov` service restarted after deployment.
- TV page smoke/visual check completed and confirmed: copy now fits and no clipping reported.
- User confirmed visual acceptance.

## Safety notes

- No Court/Final/template runtime behavior changes were introduced.
- No Treasurer Shop / Gold Desk / player_room / cashier scope changes.
- No new runtime logic or data behavior introduced.
- No DEVELOPMENT_LEARNING_PACK was created for this rollout; existing production rollout pattern was reused.
