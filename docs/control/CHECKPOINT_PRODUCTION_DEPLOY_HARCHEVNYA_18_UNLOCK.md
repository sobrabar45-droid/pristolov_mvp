# Production deployment checkpoint - Harchevnya 18+ unlock

Date: 2026-06-29
Scope: checkpoint only. This document records a production deployment that was already completed manually.

## 1. Summary

Production deploy completed successfully.

- Previous production HEAD: `537670e Tune question answer timer`
- Target / deployed production HEAD: `b3f6ed1 Add Harchevnya 18 rollout readiness report`
- Production branch: `main`
- Production service: `pristolov.service`
- Service status after restart: `active`

Before deploy:

- production branch was `main`
- production working tree was clean
- `pristolov.service` was active

After deploy:

- production HEAD became `b3f6ed1`
- service restarted successfully
- startup logs showed application startup and uvicorn running
- public `GET /` returned `200`

## 2. Deployed changes now on production

Production now includes the accumulated changes between previous production HEAD `537670e` and target HEAD `b3f6ed1`, including:

- Duel draw/replay handling.
- Question Reveal answer visibility fix for Master/TV state.
- Player rules and print clarity documentation.
- Physical House/role marker design and print pack docs.
- Harchevnya availability and approved shelf documentation.
- Harchevnya 18+ unlock runtime patch.
- Harchevnya 18+ rollout readiness report.

Key Harchevnya runtime behavior now deployed:

- Victor-approved shelf is represented in the player request flow.
- Non-18+ items are visible by default.
- 18+ alcohol items are hidden by default.
- `Показать позиции 18+` unlocks alcohol items.
- Alcohol items are marked `18+`.
- Cashier queue shows 18+ warning for alcohol requests.
- Gold is charged only after cashier/bar confirmation.
- Replacement remains manual only.
- No automatic replacement, refund, or substitution logic was added.

## 3. Commands/actions performed

Actions reported as performed manually:

1. Pushed `origin/main` to latest local HEAD `b3f6ed1`.
2. On production, ran fast-forward deploy:
   - `git pull --ff-only origin main`
3. Confirmed production HEAD became `b3f6ed1`.
4. Ran compile check for touched runtime files:
   - `app/routes/player.py`
   - `app/routes/cashier.py`
   - `app/services/master_state_service.py`
5. Restarted production service:
   - `systemctl restart pristolov.service`
6. Checked service status:
   - `systemctl is-active pristolov.service`
7. Checked recent service logs.
8. Checked public root endpoint:
   - `GET /`

## 4. Verification result

Verification reported after deployment:

- Compile check passed for:
  - `app/routes/player.py`
  - `app/routes/cashier.py`
  - `app/services/master_state_service.py`
- `pristolov.service` status after restart: `active`
- Logs showed:
  - `Application startup complete`
  - `Uvicorn running on http://127.0.0.1:8000`
- Public `GET /` returned `200`
- Checked logs did not show:
  - Traceback
  - ERROR
  - Exception
  - sqlite locked
  - timeout

Smoke notes:

- Plain unauthenticated curl to `/dev/...` and `/cashier/...` returned `403 Forbidden`, likely due protected access layer.
- `HEAD /` returned `405 Method Not Allowed`.
- `GET /` returned `200`, so the `HEAD /` result is not treated as service failure.

## 5. Explicit non-actions

The deployment/checks did not include:

- touching `LIVE01`;
- migrations;
- DB schema changes;
- production DB mutation by smoke;
- mutating Harchevnya request smoke on production;
- automatic replacement/refund/substitution implementation;
- POS/iiko integration;
- inventory sync.

## 6. Remaining checks

Remaining recommended checks before relying on the Harchevnya 18+ flow in live operation:

1. Browser smoke on production using proper protected access.
2. Non-LIVE room smoke if a safe non-LIVE production room exists or is explicitly created/approved.
3. Player Harchevnya visual check:
   - default non-18+ shelf visible;
   - 18+ items hidden before unlock;
   - checkbox `Показать позиции 18+` visible;
   - warning copy readable;
   - alcohol items appear after unlock with correct prices and `18+` marks.
4. Cashier Harchevnya visual check:
   - pending 18+ request shows item/cost;
   - cashier 18+ warning visible;
   - confirmation button visible.
5. Do not mutate `LIVE01` without explicit approval.
6. Do not create production Harchevnya requests without explicit approval and an approved non-LIVE room.

## 7. Risks

Known remaining risks:

- `TEST_ROOM_SETUP` may not exist on production.
- Protected access blocks plain curl smoke for `/dev/...` and `/cashier/...` routes.
- Browser smoke with proper protected access is still pending.
- Alcohol and 18+ legal/staff responsibility remains operational, not solved by the game screen.
- Game UI does not replace staff/legal age checks.
- Staff may refuse service regardless of game gold.
- Replacements remain manual only.
- No automatic replacement/refund/substitution exists by design.
- No POS/iiko integration exists.
- No inventory/availability sync exists.

## 8. Current recommendation

Production deploy is complete and basic service health is green.

Recommended next step:

- Run production browser smoke with proper protected access in a non-LIVE room only.
- If no non-LIVE room exists on production, first decide whether to create/prepare one explicitly.
- Do not mutate `LIVE01` unless Victor explicitly approves a LIVE-room smoke/action.
