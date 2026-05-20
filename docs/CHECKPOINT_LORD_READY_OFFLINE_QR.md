# Checkpoint — Lord Dashboard / House Ready / Offline QR

Дата фиксации: 2026-05-13

## Что уже работает

- `Lord Dashboard` работает как отдельный экран Дома.
- Лорд больше не застревает в `delegation setup`.
- Экран Дома открывается по маршруту:
  - `/house/{invite_code}`
- На экране Дома видны:
  - название Дома
  - состав
  - роли
  - золото
  - влияние
  - текущий этап
  - invite link для позднего входа

## House Ready

- `House Ready` хранится в БД.
- Persisted поле:
  - `houses.is_ready`
- Лорд может:
  - отметить Дом как готовый
  - снять готовность
- `master-state` и `tv-state` получают readiness-данные.

## Master / TV

- `master` видит готовность Домов.
- `TV` видит прогресс готовности Домов.
- На уровне state доступны:
  - `summary.houses_ready_count`
  - `summary.houses_not_ready_count`
  - `readiness.ready_count`
  - `readiness.not_ready_count`
  - `readiness.ready_houses`
  - `readiness.not_ready_houses`

## Offline QR Invite Flow

- QR больше не зависит от внешнего сервиса.
- QR генерируется локально через маршрут:
  - `/house/{invite_code}/join-qr.svg`
- QR кодирует join link вида:
  - `/delegation/join?game_code=LIVE01&invite_code=...`
- Текстовая ссылка входа остаётся как fallback.

## Late Join

- `late join` работает.
- Игрок может открыть ссылку или QR и попасть на:
  - `/delegation/join?game_code=LIVE01&invite_code=...`
- `game_code` и `invite_code` подставляются автоматически.

## Состояние LIVE01 после smoke

- `LIVE01` после smoke очищен.
- Проверено:
  - `houses = 0`
  - `players = 0`
  - `active_phases = []`
  - `court_runtime = null`
  - `next_round = stage_intro`

## Следующий шаг

- Следующий практический шаг:
  - `gold economy / manual gold add`
