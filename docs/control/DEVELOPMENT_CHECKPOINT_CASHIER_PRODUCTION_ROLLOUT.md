# Development Block Checkpoint: Cashier Production Rollout

Scope:
- Cashier production rollout block is closed and documented.
- Includes Treasurer Shop V1/V1.1 and Master/TV Treasurer Shop visibility work that fed into the same release path.

Closed commits:
- `3bc9e5f` Add standalone cashier Gold Desk screen
- `d9acc89` Add manual cashier gold grant
- `f360c49` Add cashier Gold Desk checkpoint
- `2327ac3` Document pristolov.ru cashier access plan
- `ed72f16` Document cashier production rollout
- `e341900` Improve Whisper Master player messaging
- `d5ed6d6` Add Whisper Master V1.1 checkpoint
- `50d2a01` Add Treasurer Shop V1.1 checkpoint
- `2832eaa` Add Treasurer Shop V1.1 bar shelf items
- `153d319` Select Treasurer Shop V1.1 bar shelf candidates
- `c78c9c9` Document Treasurer Shop bar shelf prices

Production state:
- Host/IP: `5.42.119.94`
- Project path: `/opt/pristolov/app`
- Service: `pristolov.service`
- Nginx config: `/etc/nginx/sites-available/pristolov`
- Nginx backup: `/etc/nginx/sites-available/pristolov.bak.20260616_141932`
- Production confirms `/cashier/gold-desk/LIVE01` access for authorized sessions.
- `/cashier/` is protected at proxy and app-level (`/dev` and `/gold` remain guarded similarly).

What is safe to show now:
- Standalone cashier Gold Desk at `/cashier/gold-desk/{room_code}`.
- Check-amount grant flow and manual `+1` flow.
- No cashier links to `/dev`, master/TV, or scenario-director surfaces.

What remains deferred:
- Additional runtime product expansions and role/polish tasks beyond this block.
- New runtime patches pending explicit candidate lock and audit review in `DEVELOPMENT_LEARNING_PACK`.

Do not touch:
- Court/Final flow code and templates.
- Player room or Treasurer Shop behavior outside documented scope.
- Gold core formulas/architecture.
- `/dev` route exposure or proxy policy changes already defined for production rollout.

Next step:
- `DEVELOPMENT_LEARNING_PACK` (docs/audit-only) for this block before any next runtime contour.
