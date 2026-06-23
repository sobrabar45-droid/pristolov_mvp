# Checkpoint: player polling optimization and 100-client load probe (2026-06-23)

## 1) Incident background

С начала июня live rehearsal показал падение/холодание player-room экрана при ~21 одновременных подключениях.
Открытые замеры и аудит показали, что частые GET-запросы (`/player/me/{player_token}` и `/player/me/{player_token}/assignments`) выполняли запись `last_seen_at` и генерировали избыточную нагрузку.

Продуктово подтверждено:
- V1 остаётся моделью индивидуальных телефонов;
- переход на “один планшет на Дом” откладывается как гипотеза V2;
- цель стабильности — не “дотягивание” до 25–40, а устойчивые 100+ player-клиентов в одной игровой комнате.

## 2) Capacity target

- Reproduction threshold: 25–40 одновременных players
- Target: минимум 100 players в одной комнате (10 домов × до 10 участников)
- Future target: параллельная эксплуатация нескольких комнат/городов (multi-room/multi-city)

## 3) Commits included in this checkpoint

- `08a770d` Add post-rehearsal stability and scalability audit
- `b840b0e` Reduce player polling database writes
- `967a646` Add real player endpoint load probe helper
- `4604611` Optimize player polling endpoints

## 4) Technical changes made

1. Throttled updates `last_seen_at` до редкого тикa (около 60 сек) вместо записи на каждый poll.
2. Сделан `POST /player/me/{player_token}/assignments` read-only по частому polling path.
3. Добавлен `scripts/load_probe_real_player_endpoints.py`:
   - ищет игроков текущей комнаты через `Game` + `Player.player_token`;
   - пишет пути реальных endpoint’ов (`/player/me/{token}` и `/player/me/{token}/assignments`);
   - запускает `scripts/load_probe_player_screens.py` на наборах клиентов.
4. В `/player/me/{player_token}` добавлены фазово-ролевые гейты:
   - Expedition/Дипломатия/Дуэли/Шёпот/вопросные блоки вычисляются только когда релевантны;
   - для нерелевантных контекстов возвращаются пустые структуры без тяжёлых внутренних выборок.

## 5) Production deployment status

- VPS обновлён целевыми коммитами.
- `compileall` проходит.
- сервис `pristolov` активен.
- start smoke возвращает 200.
- базовое ручное smoke для `/player/me/{token}` после `4604611` для LIVE01 было улучшено.

## 6) Load-probe methodology

- Базовая нагрузка: `load_probe_player_screens.py`
- Реальные endpoints через helper:
  - `scripts/load_probe_real_player_endpoints.py`
  - room: `LIVE01`
  - `clients`: 25, 40, 100
  - duration and interval — фиксированы в helper/запуске (по задаче — без reset, без write actions).
- Метрики: `status_counts`, `p50`, `p95`, `p99`, `errors_total`.
- Перед/после проверены одинаковые условия нагрузки и одна и та же выборка player-токенов.

## 7) Before/after comparison

| Scenario | p95 до `4604611` | p95 после `4604611` | errors | notes |
|---|---:|---:|---:|---|
| 100 real player endpoints (LIVE01) | ~1104.5 ms | 221.2 ms | 0 | 25 и 40 тоже упали: p95 75.7→30.5 и 143.6→38.0 |
| 25 real player endpoints (LIVE01) | 75.7 ms | 30.5 ms | 0 | существенно лучше headroom |
| 40 real player endpoints (LIVE01) | 143.6 ms | 38.0 ms | 0 | практически без ошибок |

## 8) Result and interpretation

- До оптимизации реальный player probe при 100 клиентах в LIVE01 имел `p95≈1104.5 ms`.
- После `4604611` `p95≈221.2 ms`, `p99≈284.0 ms`, `max≈362.3 ms`, `errors_total=0`, все ответы 200.
- Для целевых 100 клиентов это уже находится в комфортном диапазоне для V1.
- Основная ошибка freeze/dropped around 21 при первом заходе считается существенно сглаженной.

## 9) Remaining risks

- Не протестированы в одном прогона combined сценарии для игроков + Master + TV + cashier + dev/operator.
- Нет проверки в реальном режиме активных gameplay write-пиков (длительная активная фаза).
- Нет долгого длительного soak-теста (более 30–60 минут непрерывного poll).
- Multi-room/multi-city масштабирование не подтверждено.

## 10) Recommendation and next contour

- Тех-контур оптимизации player polling можно считать закрытым по V1 стабильности на целевую нагрузку 100+ клиентов в одной комнате.
- Следующий шаг до возврата к gameplay-пампа: выполнить optional combined-probe по экранным ролям (Master/TV/cashier/operator + players) на контрольном стенде, затем запускать P0 gameplay-контур:
  - объявления и этапы,
  - Expedition UX,
  - timer/reveal вопросов,
  - обработка duel tie.

