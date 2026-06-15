# DECISIONS

## Архитектурные решения
- Использовать существующий gold runtime (`spend_gold_for_action` или эквивалентный gold-сервис), без ручного списания.
- Реализация V1/ V1.1 выполнена только как runtime patch без изменения архитектуры.
- Отдельный экран Мастера золота для покупок, без полноценного каталога/админ-системы.
- Держать влияние и победу незатронутыми для барных покупок.

## Роутинг
- Экран Treasurer Shop: `GET /dev/treasurer-shop/{room_code}`.
- Экшен endpoint: `POST /player/treasurer-shop/{player_id}/purchase`.
- Защита: покупки разрешены только role `treasurer`.

## Игровые решения
- `set_bar` и `giraffe` списывают золото и создают атмосферные/социальные события.
- Добавлены V1.1 барные SKU:
  - `author_tea` — 3 gold.
  - `lemonade_02` — 2 gold.
  - `sobranie_pizza` — 6 gold.
  - `anna_pavlova` — 2 gold.
- V1.1 SKU отмечены как bar/social-only:
  - влияние не меняется
  - дипломатия не меняется
  - нет Court/Final эффекта.
- `gift_to_ally`:
  - требует target_house_id;
  - проверяет существование и принадлежность дома к той же игре;
  - требует активный союз (`GameDeal` alliance);
  - после успешной покупки меняет influence на +1 для обоих домов.

## События
- События покупок должны идти в Master/TV:
  - type: `treasurer_shop`
  - source: `treasurer_shop.purchase`.

## Нежелательные изменения
- Не добавлять новые модели/таблицы.
- Не менять core gold архитектуру.
- Не менять Court/Final.
- Не менять diplomacy core.
- Не делать commit в рамках этого шага.
