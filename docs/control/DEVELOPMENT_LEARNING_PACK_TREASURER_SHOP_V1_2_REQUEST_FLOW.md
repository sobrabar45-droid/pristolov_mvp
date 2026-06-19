# DEVELOPMENT_LEARNING_PACK_TREASURER_SHOP_V1_2_REQUEST_FLOW

## Trigger / why this pack exists

- Treasurer Shop V1.2 moved from V1.1-style operator flow to a player-to-cashier request flow.
- Required safer and traceable behavior for on-site play:
  - player can place request from role panel
  - cashier confirms manually
  - gold and ledger update only after confirmation
- Needed explicit rules for no-spend-at-request and event timing.

## Reusable pattern: request -> queue -> confirm -> ledger/event

1. Player action creates a pending business request.
2. Operator/cashier dashboard shows request metadata and status.
3. Operator confirmation triggers final business action (gold spend + event + ledger).
4. Request transitions to completed on success; stays pending on failure cases.

This pattern is reusable for low-risk approvals where immediate execution is not desired.

## Why GameDeal was reused

- Existing `GameDeal` already had:
  - game scope
  - house/player associations
  - status lifecycle
  - offer payload storage
- Reuse avoids introducing a new table during V1.2 and keeps rollout minimal.
- Request filtering by `offer.type == "treasurer_shop_request"` cleanly separates finance requests from diplomacy deals.

## Why HouseGoldTransaction must remain final ledger only

- `HouseGoldTransaction` is the final, immutable financial ledger.
- Writing to it at request creation would break “request pending” semantics and false-trigger accounting.
- Keeping ledger writes only on confirmation preserves auditability and makes insufficient-gold rollback explicit.

## Staged patching pattern used

1. Patch 1 — request queue without spend
   - Added treasurer UI request section and safe shelf posting.
   - Created pending `GameDeal` with `status = pending`, `offer.type = treasurer_shop_request`.
   - Cashier queue display added.
2. Checkpoint
   - Documented scope and smoke criteria before moving forward.
3. Patch 2 — confirmation and spend
   - Added cashier confirm endpoint and “Заказ принят”.
-  Guarded gold spend through existing gold flow.
- Completed request updates and event emission through existing pathways.
4. Checkpoint
5. Production rollout
   - Deployed via standard ff-only sequence to VPS, service restart, and production smoke checks.

## Smoke principles (must prove)

- Request creation does not spend gold:
  - house balance unchanged, no new `HouseGoldTransaction`.
- Confirmation is the only point of spend:
  - balance decreases exactly by cost, transaction added once.
- Insufficient gold behavior:
  - confirmation returns `ok=false`
  - request remains pending
  - no transaction created
- Event visibility:
  - Master/TV event appears only after confirmation, not on request creation.

## UI rules

- No `/dev` links in player cashier paths introduced for this flow.
- Safe shelf only in V1.2:
  - `author_tea`, `lemonade_02`, `sobranie_pizza`, `anna_pavlova`.
- Cashier queue row must show:
  - House
  - item
  - cost
  - status

## Security/product constraints

- Alcohol/full shelf remains intentionally deferred.
- `18+` expanded shelf deferred.
- No new model/table introduced in V1.2 baseline.
- Keep role/route protections as existing cashier/operator model.
- Cashier flow must continue to use existing +1/check-amount capabilities unchanged.

## Codex hang/recovery notes

- If browser/dev-server smoke blocks, capture:
  - status snapshot first
  - exact incomplete smoke steps
  - process/log cleanup state
- Continue with status-only reporting and resume smoke in separate step.
- Keep all work bounded to docs once runtime is already complete.

## Anti-patterns

- Writing `HouseGoldTransaction` on request creation.
- Mixing treasury request data into diplomacy `offer.type`.
- Leaving legacy operator-only request state not visible in cashier queue.
- Exposing confirmation in `/player_room` instead of cashier-only interface.

## Future reuse candidates

- Any feature requiring delayed execution with human approval.
- Any flow needing pending/confirmed state before mutation.
- Product approvals where UX should prevent accidental spend until operator acceptance.
