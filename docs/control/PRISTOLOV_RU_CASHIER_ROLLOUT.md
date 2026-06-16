# Pristolov.ru Cashier Gold Desk Production Rollout

Date: 2026-06-16

Scope:
- Production rollout of standalone cashier Gold Desk with manual +1 mode confirmed.
- Documentation-only checkpoint task.

Target environment:
- VPS host/IP: `5.42.119.94`
- Project path: `/opt/pristolov/app`
- Service: `pristolov.service`
- Nginx config: `/etc/nginx/sites-available/pristolov`
- Nginx backup: `/etc/nginx/sites-available/pristolov.bak.20260616_141932`

Rollout changes applied in production:
- Added protected `/cashier/` location in nginx (mirroring existing `/gold/` protection behavior).
- `/cashier/gold-desk/{room_code}` available for tablet use.
- `/dev` kept internal.

Validation summary:
- `https://pristolov.ru/cashier/gold-desk/LIVE01` returned page content and worked in browser/tablet.
- Upstream token-protected smoke:
  - `cashier_with_token = 200`
- Cashier page content checks:
  - `manual_section = present`
  - `plus_one_button = present`
  - `dev_links = none`
- Manual mode smoke confirmed by user flow.
- Legacy existing flows preserved; check-amount and grant endpoints remained available through protected flow.

Implemented runtime commits included in rollout path:
- `3bc9e5f` Add standalone cashier Gold Desk screen
- `d9acc89` Add manual cashier gold grant
- `f360c49` Add cashier Gold Desk checkpoint
- `2327ac3` Document pristolov.ru cashier access plan

Rollback note:
- Restore nginx backup and reload nginx if cashier surface needs immediate rollback:
  - restore `/etc/nginx/sites-available/pristolov.bak.20260616_141932` to `/etc/nginx/sites-available/pristolov`
  - run nginx config reload.
