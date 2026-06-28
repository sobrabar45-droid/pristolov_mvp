# Harchevnya 18+ unlock shelf - production rollout readiness

Date: 2026-06-28
Scope: readiness report only. No deployment was performed.

## 1. Local readiness

Latest local relevant commits:

- `87ce2b1 Add Harchevnya 18 unlock checkpoint`
- `37058ed Add Harchevnya 18 unlock shelf`
- `f6cbb71 Add Harchevnya 18 unlock design`
- `8f621d6 Add Harchevnya approved shelf policy`
- `af66fd4 Add Harchevnya availability audit`

Local working tree before this report was clean.

Local runtime smoke already passed for `37058ed`:

- Victor-approved Harchevnya shelf added to request flow.
- Non-18+ items are visible by default.
- 18+ alcohol items are hidden by default.
- `Показать позиции 18+` checkbox unlocks alcohol items.
- Alcohol items are visibly marked `18+`.
- Player copy states that gold is charged only after cashier/bar confirmation.
- Replacement remains manual only.
- Cashier queue shows an 18+ warning for alcohol requests.
- Gold is charged only after cashier confirmation.
- No automatic replacement, refund, or substitution logic was added.

Local visual/browser smoke passed in `TEST_ROOM_SETUP`:

- Player page `/house/204B48/player/955` opened.
- Default non-18+ items were visible:
  - Авторский чай
  - Лимонад 0.2 л
  - Пицца Собрание
  - Анна Павлова
  - Сет тапасов
- 18+ items were hidden before unlock:
  - Шампанское Премиум премьер
  - Сет настоек
  - Жираф пива Шихан
  - любой пивной сет
- Checkbox `Показать позиции 18+` was visible.
- 18+ warning copy was readable.
- After checking the checkbox, alcohol items appeared with correct prices and `18+` marks.
- Cashier page `/cashier/gold-desk/TEST_ROOM_SETUP` opened.
- Pending 18+ request was visible.
- Cashier 18+ warning was visible.
- Confirmation button was visible.
- Desktop and phone-like mobile layout passed.
- No files changed during visual smoke.

Known local smoke artifacts in `TEST_ROOM_SETUP`:

- `player_id=955 Test Treasurer`
- `request_id=97 tapas_set completed`
- `request_id=98 tincture_set pending`
- `transaction_id=135 amount=-7`
- `house_id=282 gold changed 11 -> 4`

## 2. Production read-only status

Production read-only status was attempted but not obtained in this local shell.

Attempted read-only checks:

- production git HEAD
- production `git status --short`
- `systemctl is-active pristolov.service`

Result:

- First SSH command was quoted incorrectly for PowerShell and attempted to evaluate `systemctl` locally.
- Second SSH command returned only `off` / `exit /b 1` and did not return production data.
- No production HEAD was confirmed.
- No production service status was confirmed.
- No production dirty/untracked status was confirmed.

Production containment:

- No `git pull` was run.
- No restart was run.
- No migrations were run.
- No production smoke was run.
- No production DB mutation was performed.
- `LIVE01` was not touched.

Current production readiness conclusion:

- Local code and local smoke are ready for rollout planning.
- Production deployment readiness is not fully confirmed until production HEAD, tree status, and service status are checked with a working read-only shell command.

## 3. Rollout risks

- Production may not yet contain `37058ed` / `87ce2b1`.
- Production working tree status is currently unknown from this report.
- Production service status is currently unknown from this report.
- Production DB may not contain `TEST_ROOM_SETUP` or the same safe smoke artifacts.
- Visual smoke has not yet been run in production.
- Alcohol and 18+ service remains real-world staff responsibility.
- Game UI does not replace legal age checks or staff refusal rights.
- No POS/iiko integration exists.
- No inventory sync exists.
- Replacements remain manual only.
- There is no automatic replacement, refund, or substitution logic by design.

## 4. Safe deployment plan, not executed

Future rollout steps only:

1. Confirm production working tree and HEAD with read-only commands.
2. Confirm production service is active.
3. Confirm production HEAD does or does not contain:
   - `37058ed Add Harchevnya 18 unlock shelf`
   - `87ce2b1 Add Harchevnya 18 unlock checkpoint`
4. Pull latest only after explicit Victor approval.
5. Restart service only after explicit Victor approval.
6. Run compile check after deployment.
7. Run smoke only in `TEST_ROOM_SETUP` or another explicitly approved non-LIVE room.
8. Verify player Harchevnya default shelf, 18+ unlock, and cashier warning.
9. Confirm manual-only replacement wording remains visible.
10. Only after non-LIVE smoke passes, decide whether to enable/use the flow in a live room.

## 5. Explicit non-actions

This report did not perform:

- deployment;
- production mutation;
- production DB writes;
- production smoke;
- `LIVE01` access or mutation;
- migrations;
- production restart;
- `git pull`;
- runtime code changes;
- scenario JSON changes;
- DB schema changes.

## 6. Recommendation

Recommendation: not ready to deploy blindly.

The patch is locally ready for controlled production rollout planning, but deployment should wait until Victor explicitly approves production read-only verification and then the actual deploy/restart steps.

Recommended next action:

- Run a corrected production read-only status command from an environment with known SSH access.
- If clean and approved, schedule explicit deployment command sequence.
