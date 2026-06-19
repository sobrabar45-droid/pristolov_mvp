# Player Room role UX audit after Treasurer Shop V1.2

## Scope and inspected files
- `app/templates/player_room.html`
- `app/routes/player.py`
- `app/models/role.py`
- `app/models/` role- or deal-related helpers used by player room
- `docs/control/NEXT_CODEX_TASK.md`
- `docs/control/DEVELOPMENT_LEARNING_PACK_TREASURER_SHOP_V1_2_REQUEST_FLOW.md`

## Role UX matrix

| Role code | Visible sections | Available buttons/actions | Active when | Backend endpoint(s) | Effect/resource | Copy quality | Liveliness |
|---|---|---|---|---|---|---|---|
| `lord_lady` | Role card, “Что делать сейчас”, Expedition block, Duels block, Alliances block, common action cards | Create expedition, choose route, resolve expedition, create duel, accept/decline duel, break alliance peaceful/betrayal | Expedition: active in `map/free_play`; Duels/resolve: duels phase; Alliance only if alliances exist | `/player/expedition/create/{player_id}`, `/player/expedition/{expedition_id}/choose-location/{player_id}`, `/player/expedition/{expedition_id}/resolve/{player_id}`, `/player/duels/challenge/{player_id}`, `/player/duels/accept/{player_id}/{duel_id}`, `/player/duels/refuse/{player_id}/{duel_id}`, `/player/alliances/break/{player_id}` | Expedition/duel/alliance state changes and role bonus mechanics | Good: role purpose clear, guidance text is readable | **Strongest** |
| `diplomat` | Role card, “Что делать сейчас”, Expedition block (hidden/disabled), Deal block | Create/answer/reject deals | Active during `diplomacy/free_play`; block shown with disabled text outside phase | `/player/deals/create/{player_id}`, `/player/deals/respond/{player_id}` | Creates `GameDeal`, handles accept/reject lifecycle | Good with clear phase note and form guidance | Strong/active |
| `maester` | Role card + “Что делать сейчас” + generic active-assignments flow | No direct role-specific actions in `player_room` today | No role-specific endpoints exposed in this screen | No role-specific endpoint from `player_room` | None in room UX today | Copy says future tasks may appear; currently placeholder-like | Weak |
| `treasurer` | Role card, “Что делать сейчас”, Expedition block (if phase), Deal block (“Подтверждение сделок”), Treasurer Shop block (“Харчевня / Магазин”) | Create treasurer request (`author_tea`, `lemonade_02`, `sobranie_pizza`, `anna_pavlova`); confirm/reject pending diplomatic deals | Shopper buttons visible any time role has not-role-specific lock; last whisper/deal sections depend on phase | `/player/treasurer-shop/request/{player_id}`; `/player/deals/treasurer-confirm/{player_id}` | Request creation: creates pending `GameDeal` (`type=treasurer_shop_request`, no spend). Confirmation: spends gold and writes `HouseGoldTransaction` | Clear: explicit “Золото спишется после подтверждения кассиром” | **Strong** |
| `whisper_master` | Role card, “Что делать сейчас”, Last Whisp block | One of: `quiet_support`, `crown_tax`, `break_alliance`, with disabled placeholders for unavailable/no-op branches | Last whisper phase only (`last_whisper` phase), one action per house enforced by state checks | `/player/last-whisper/action/{player_id}` | Targeted influence/Alliance/leader effects with explicit no-op handling | Mostly clear; no placeholder-like phrases in player room; additional clarity around no-op currently appears in result/help text | Medium |
| `house_sworn` | Role card, “Что делать сейчас” only | No role-specific player-room actions; may participate in expedition route voting if selected in expedition role list | Expedition phase: may appear in expedition role voting path | `player_room` does not call dedicated endpoint by role | None | Copy is generic and thin | Weak |
| `None / unassigned` | Role card “not assigned” message, assignment/phase info only | No action controls | No role yet | None | None | Clear | Empty until role assigned |

## Other role-like codes found
- Also present in role definitions and expedition role options: `lord_lady`, `diplomat`, `maester`, `treasurer`, `whisper_master`, `house_sworn`.
- No additional active player-room role code branches found in current template beyond these.

## Audit checks
- At least one meaningful action:
  - yes: `lord_lady`, `diplomat`, `treasurer`, `whisper_master`
  - partial/none: `maester`, `house_sworn`, unassigned
- Inactive/locked states:
  - For role-gated sections, when not allowed, block is hidden or shows explicit phase/ownership message.
  - Last whisper shows explicit gating and “button visibility only for role”.
- Button visibility:
  - Generally role- and phase-gated (server/JS both enforce gating).
  - No cross-role action leakage observed.
- Placeholder/placeholder-like text:
  - only `maester` block is intentionally future-facing; this is functional placeholder text.
- `/dev` links:
  - No `/dev` links in `player_room` UI; only role/screen links.
- Duplicate/confusing sections:
  - No major duplicates; repeated “house resource” and “active assignments” are intentional global sections.
- Phase gating clarity:
  - Mostly explicit; e.g. diplomacy window text in deal/deals create path, last whisper gate text, duel/exploration phase checks.
- Error readability:
  - Non-technical and concise for most actions; additional consistency can improve whisper/tree edge cases and hidden failure causes.

## Post-V1.2 role strength
- Strongest role: `lord_lady`
- Weakest roles: `house_sworn` and `maester` (no dedicated mechanical actions in player room)

## Urgent improvements
- Most urgent UX text polish: `maester` and `house_sworn` (make their intended contribution/next step explicit when no active action is available).
- Role needing real mechanic next: `house_sworn`/обычный участник (light-touch meaningful task so role feels active before late game).

## Recommended next contour
- **A) text/UX polish only** (focus on `maester` and `house_sworn` copy and one-time “no action” state clarity, while preserving live mechanics).
