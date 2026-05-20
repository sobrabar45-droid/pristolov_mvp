# Checkpoint — Manual Gold Control

Дата фиксации: 2026-05-13

## Что реализовано

- На `master-screen` реализован ручной контроль золота Дома.
- Доступны кнопки начисления:
  - `+1`
  - `+2`
  - `+3`
- Доступны кнопки списания:
  - `-1`
  - `-2`
  - `-3`

## Используемые backend routes

- `POST /gold/houses/{house_id}/grant`
- `POST /gold/houses/{house_id}/spend`

## Какие данные меняются

- `houses.resource_gold`
- `house_gold_transactions`

## State / UI

- `master-state` отражает обновлённое золото Дома.
- `tv-state` отражает обновлённое золото Дома.
- `TV` получает обновление через обычный polling.

## Защита от overspend

- При попытке списать больше золота, чем есть у Дома:
  - backend возвращает `409`
  - UI показывает понятный alert на русском языке
- Отрицательный баланс не допускается.

## Cleanup

- `reset-delegations` теперь удаляет `HouseGoldTransaction` до удаления Домов.
- Это нужно, чтобы ручные gold-транзакции не ломали очистку live-комнаты.

## Результат smoke для LIVE01

- Начисление золота работает.
- Списание золота работает.
- Защита от overspend работает.
- Cleanup после smoke снова работает корректно.

## Итог

- Manual gold control для live-оператора считается зафиксированным checkpoint.
