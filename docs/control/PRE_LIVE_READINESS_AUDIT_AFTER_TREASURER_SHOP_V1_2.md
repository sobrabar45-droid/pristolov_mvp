# Pre-live readiness audit after Treasurer Shop V1.2

## Context
- Selected contour: `A` in `NEXT_CONTOUR_SELECTION_AFTER_SUPPORT_ROLES_UX.md` (`42efc36`).
- Codex-first smoke rhythm is active (`8f9da8e`).
- Audit scope: player room, cashier, Master, TV, gold, and role action surfaces.

## Commit context
- `42efc36` Select next contour: pre-live readiness audit.
- Relevant live runtime work in this release stream:
  - `8f9da8e` Codex-first smoke rhythm
  - `53c7cf4`, `8524ef0`, `a5e9cae` support roles UX / phase label fix
  - `dc9c17a`, `0a03967`, `4aa61c3`, `59e7539`, `fff8e7f` Treasurer Shop V1.2 request-confirmation stream

## Automated checks performed
- `git status --short` before audit: clean.
- `git log --oneline -n 10`: showed the above context.
- `python -m compileall app -q`: passed.
- `rg` route/template checks:
  - no `/dev` links in `app/templates/player_room.html` and `app/templates/cashier_gold_desk.html`.
  - no mojibake in inspected templates (player_room/cashier/master/tv).
  - no placeholder/placeholder-like markers in `player_room.html` (`TODO`, `placeholder`, `заглуш`, `позже`, `coming soon`).
- route presence checks (from source scan):
  - `player.py`: `/treasurer-shop/request/{player_id}`, `/last-whisper/action/{player_id}`, expedition/duel/lord actions are still present.
  - `cashier.py`: `/cashier/gold-desk/{room_code}`, `/cashier/treasurer-shop/requests/{request_id}/confirm`.
  - `dev.py`: `/dev/master-screen/{room_code}`, `/dev/tv-mode/{room_code}`, `/dev/treasurer-shop/{room_code}`, `/dev/gold-desk/{room_code}`.

## HTTP smoke
- Local server detected on multiple ports (`8000`, `8001`, `8010`, `8015`).
- Smoke executed against `http://127.0.0.1:8015`:
  - `GET /cashier/gold-desk/LIVE01` -> `200`
  - `GET /dev/master-screen/LIVE01` -> `200`
  - `GET /dev/tv-mode/LIVE01` -> `200`
  - `GET /dev/gold-desk/LIVE01` -> `200`
  - `GET /dev/treasurer-shop/LIVE01` -> `200`
  - `GET /player/me/LIVE01-INVALID` -> `200` (route responds)
- Cashier page content sanity checks on local page response:
  - manual mode section: present (`Ручное начисление`)
  - manual action button text: present (`+1 золото`)
  - acceptance button: present (`Заказ принят`)
  - check-amount mode presence: inferred from content (`Сумма чека`)
  - `/dev` links in cashier HTML: not present
- Production smoke on `https://pristolov.ru/...` was attempted but **network handshake failed** in this environment (connection error), so production HTTP checks were skipped.

## Readiness matrix

| Surface | Pre-live status | Evidence | Risks |
|---|---|---|---|
| Player room route surface | Partially verified | `GET /player/me/{token}` responds; templates/routes present | No live player-token smoke executed |
| Cashier Gold Desk route | Green | `GET /cashier/gold-desk/LIVE01` 200 on local | Only local verification (no prod smoke) |
| Master screen route | Green | `GET /dev/master-screen/LIVE01` 200 locally | Route may still be protected differently in prod env |
| TV mode route | Green | `GET /dev/tv-mode/LIVE01` 200 locally | Prod validation pending |
| Treasurer Shop request flow | Green | `player.py` request create endpoint + `cashier.py` confirm endpoint present | No end-to-end with real room/token in this run |
| Cashier confirmation | Green | confirm endpoint present; queue button rendered locally | No live production smoke of confirm call |
| Manual +1 | Green | UI button and endpoint call visible | Requires manual confirmation on live |
| Check-amount grant | Green | UI contains check amount flow (`Сумма чека`) and `/gold/houses/{house_id}/grant-from-check` call | No live smoke call run |
| Last Whisper actions | Green | `/last-whisper/action/{player_id}` and related state handling still present | No phase-gated live action smoke executed |
| Diplomacy endpoints | Green | `dev.py` diplomacy routes present | No live gameplay smoke for diplomacy |
| Expedition/Duel/Lord actions | Green | corresponding routes and player UI sections still present | No live smoke executed for these actions |
| `/dev` leakage in player/cashier templates | Green | `rg "/dev"` returned no matches | none |
| Phase label mojibake | Green (templates) / Partial | player/cashier/master/tv templates clean by pattern scan | Mojibake remains in some `app/routes/app/services` error strings (non-UI route text) |

## Main blockers
1. Could not verify production endpoints due transport error to `pristolov.ru` from this environment.
2. No complete live player-token smoke was performed (no player token/room-state prepared for this pass).
3. Residual mojibake strings remain in non-template backend message strings (e.g., `app/routes/player.py` error text), not currently user-facing in normal UI flow.

## Go/No-go recommendation
- **Conditional No-Go until production reachability and final smoke are completed.**
- Local readiness is **mostly Green**, but pre-live closure should include:
  - successful HTTPS smoke against pristolov.ru for cashier/master/tv/player flows,
  - phase action smoke in a safe test room,
  - validation of `dev`/`cashier`/`gold` protection behavior in live environment.
- Next recommended task: run `docs/control/PRE_LIVE_SMOKE_EXECUTION_PROTOCOL.md` end-to-end against the target game room and document final go/no-go outcome before deploying/going live.

