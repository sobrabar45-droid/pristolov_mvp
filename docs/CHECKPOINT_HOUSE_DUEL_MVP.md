# Checkpoint — House Duel MVP

Дата фиксации: 2026-05-14

## Что реализовано
- House vs House duel MVP реализован через существующую систему `GameDuel`
- новые модели и таблицы не создавались

## Переиспользованные routes
- `POST /dev/games/{room_code}/duels/challenge`
- `POST /dev/games/{room_code}/duels/{duel_id}/accept`
- `POST /dev/games/{room_code}/duels/{duel_id}/refuse`
- `POST /dev/games/{room_code}/duels/{duel_id}/resolve`

## Переиспользованный gold ledger
- `HouseGoldTransaction`
- `resolve_pvp_gold(...)`

## Динамическая ставка
- ставка теперь динамическая
- ставка по умолчанию: `3`
- custom stake поддержан
- формула выигрыша:
  - `prize = stake * 2 - 1`
  - `system commission = 1`

## Пример для stake 3
- проигравший: `-3`
- победитель: `-3 +5`
- net результат победителя: `+2`

## Operator UI на master-screen
- compact блок `Дуэль Домов`
- `challenger select`
- `target select`
- `stake input`
- `create challenge`
- `accept / refuse`
- `resolve winner`

## State / TV
- `master-state` отдаёт дуэль и обновлённое золото
- `tv-state` отдаёт дуэль и обновлённое золото
- `TV` обновляется через обычный polling

## Safety
- same-house duel блокируется в UI
- insufficient gold отклоняется backend
- overspend не создаёт отрицательный баланс
- cleanup `LIVE01` теперь удаляет `HouseGoldTransaction` и `GameHouseTower` до удаления `House`

## Проверка на LIVE01
- открыта duel phase
- создана дуэль
- дуэль принята
- дуэль разрешена
- `master-state` обновился
- `tv-state` обновился
- балансы золота обновились
- кейс insufficient gold отклонён
- same-house UI guard присутствует
