# Pre-live production smoke result

## Context

- Protocol: [PRODUCTION_SMOKE_PROTOCOL_PRE_LIVE.md](D:\Projects\pristolov_mvp\docs\control\PRODUCTION_SMOKE_PROTOCOL_PRE_LIVE.md)
- Command execution: manual VPS block was run by user outside Codex.
- Protocol commit: `d46c820`.

## VPS smoke result summary

- `git`
  - `head` = `a5e9cae`
  - `git status --short` count = `0`
- service
  - `pristolov.service` = `active`
- compile
  - `python -m compileall app -q` = `OK`
- token
  - token set = `yes`
  - token length = `64`

## Protected endpoint results (127.0.0.1:8000 with X-Admin-Token)

- `/cashier/gold-desk/LIVE01` = `200`
- `/dev/master-screen/LIVE01` = `200`
- `/dev/tv-mode/LIVE01` = `200`
- `/dev/gold-desk/LIVE01` = `200`
- `/dev/treasurer-shop/LIVE01` = `200`

## Cashier / player UI checks

- `manual_grant=present`
- `plus_one=present`
- `check_amount=present`
- `shop_queue=present`
- `accept_button=present`
- `cashier_dev_links=none`
- `phase_label_source=OK`
- `player_dev_links=none`

## DB inventory (redacted)

- game: `LIVE01`
- players_total: `2`
- houses_total: `1`
- role counts:
  - `role_lord_lady=1`
  - `role_maester=1`
- role presence:
  - `has_treasurer=no`
  - `has_lord_lady=yes`
  - `has_diplomat=no`
  - `has_whisper_master=no`
  - `has_maester=yes`
  - `has_house_sworn=no`

## Go/no-go decision

- **Conditional GO** for surfaces and production readiness
  - infrastructure, protected routes, and cashier/player static checks are green
- **No-Go** for complete role/action runtime E2E
  - live role inventory does not include `treasurer`, `diplomat`, `whisper_master`, or `house_sworn`
  - critical action flows cannot be fully validated without those roles

## Recommendation

- Next step: create/fill a controlled test room with required roles (or rotate LIVE01 test state) and run role/action E2E smoke.
- Keep manual-only final acceptance for:
  - one real player room link
  - cashier page
  - Master screen
  - TV page

