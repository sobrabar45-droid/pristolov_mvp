# Treasurer Shop V1.2 Request Flow

## Current state (V1 / V1.1)

- Operator-mediated shop entry remains: `/dev/treasurer-shop/{room_code}`.
- Runtime supports direct house spending actions in `V1.1`:
  - `author_tea` — 3 gold
  - `lemonade_02` — 2 gold
  - `sobranie_pizza` — 6 gold
  - `anna_pavlova` — 2 gold
- Player room currently shows no shop actions/buttons.
- Treasurer role does not yet have direct shop browse + request flow.
- Cashier flow is currently independent through `/cashier/gold-desk/{room_code}`.
- Alcohol-named items are intentionally deferred.

## Desired V1.2 player flow

1. Treasurer / Master of Gold sees a player_room entry:
   - Label: `Харчевня / Магазин`.
2. Player opens shop UI and browses available non-alcohol shelves.
3. Player selects desired items and submits a request, not a direct spend.
4. Gold is not deducted at request time.
5. Request is delivered to cashier queue with house and selected items.
6. Cashier confirms request with button: `Заказ принят`.
7. Gold is deducted at cashier confirmation time.

## 18+ checkbox concept

- Add an 18+ acknowledgment control in shop UI.
- If unchecked, show only safe-shelf subset (non-alcohol).
- If checked, allow full assortment (future scope; currently alcohol items still deferred).
- Keep this UI-level and explicit; avoid silent unlocking.

## Safe shelf vs full shelf

- V1.2 default for live visibility: safe shelf only.
- Full shelf remains hidden behind 18+ path and still governed by runtime policy.
- Alcohol/legal review remains a separate prerequisite before adding alcohol to any public player-facing shop path.

## Cashier queue and operator visibility

- Cashier queue entry must include:
  - House name
  - Item label
  - Price / cost
  - Timestamp (optional but useful)
  - Current request status
- Existing cashier gold desk should emphasize who ordered what before confirmation.

## Master / TV visibility

- Master/TV should display a readable event only when order is confirmed (not when requested).
- Suggested event text patterns:
  - `Дом {actor} отправил заказ в Харьчевню / Магазин.`
  - `По приказу Харьчевни/кассы: «{item_label}» выдан за {gold_cost} золота.`
- Exact phrasing to be finalized in V1.2 runtime draft.

## Risk log

- Age-gating risk:
  - Unclear consent semantics and UX clarity around the 18+ flow.
- Accidental request risk:
  - duplicate taps, accidental item multipliers, stale queue entries.
- Duplicate request risk:
  - same house + same items may be submitted repeatedly if no idempotency model exists.
- Storage/status risk:
  - request lifecycle state must be explicit (`requested`, `confirmed`, `denied`, `expired`), which is not yet in current model.
- Cashier abuse/false approval risk:
  - requires explicit cashier confirmation control and traceable events.

## Open technical question

- Where to store pending shop requests?
  - Dedicated request table (recommended) with house_id, item_code, qty, status, created_by, confirmed_by.
  - Or embedded state in existing room/house action history (less visible, harder to scale).
  - Decision required before any runtime implementation.

## Implementation strategy V1.2

- Selected storage for V1.2 first batch: `GameDeal` (existing model), not a new table.
- Player request records use:
  - `offer.type` = `treasurer_shop_request`
  - strict `offer_code`/`item_code` payload inside offer JSON
  - statuses: `pending` (created by player), `accepted_waiting_treasurer` (awaiting cashier confirmation), `completed` (cashier confirmed and gold spent), `treasurer_rejected` (cashier rejected), optional `declined` path if target-stage rejection remains.
- Gold ledger rule:
  - no gold movement on request creation or treasury acceptance stage.
  - `HouseGoldTransaction` is created only when cashier confirmation executes transfer/spend.
- Strict filtering is required so shop records never mix with diplomacy/resource deals:
  - all `GameDeal` queries for V1.2 flow include `offer.type == treasurer_shop_request`.
  - generic deal queues/streams exclude this type unless explicitly needed.
- Source of truth for request payload:
  - `offer` stores ordered items with `action_code`, `item_label`, `cost_gold`, quantity if needed.
  - status transition stays minimal and explicit.

- Scope guardrails for this patch:
  - safe shelf only: `author_tea`, `lemonade_02`, `sobranie_pizza`, `anna_pavlova`.
  - defer 18+ expansion and all alcohol items.
  - defer dedicated `ShopRequest` model and advanced cleanup/expiry lifecycle.

- TV/Master visibility:
  - readable event on confirmed spend only.
  - no user-visible event while request is still pending.

## V1.2 runtime guardrails (for later patch)

- Do not spend gold on browse or pre-confirm actions.
- Spend only at cashier confirmation.
- Keep Treasury Shop runtime mechanics unchanged until this flow is approved.
- Keep `/dev`/Cashier/Gold Desk separation as-is; no player-room direct gold mutation on this path.

## Proposed next step

- Run an audit-only implementation strategy session in `docs` and `NEXT_CODEX_TASK`.
- Decision in `NEXT_CODEX_TASK` should stay Codex 5.3 first (decision/flow), then Codex 5.5 for minimal runtime candidate after storage model and storage lifecycle are approved.

## Commit/trace

- Current doc task follow-on to existing flow, current HEAD: `ff6b110`.
