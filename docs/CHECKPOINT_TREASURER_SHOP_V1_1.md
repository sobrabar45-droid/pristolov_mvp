# Treasurer Shop V1.1 Checkpoint

Commit:
- `2832eaa` Add Treasurer Shop V1.1 bar shelf items

Scope:
- Runtime patch only for four non-alcohol bar/social-only items.
- Operator-mediated Treasurer Shop remains the V1 pathway.
- No changes to Court/Final, player_room, gold core, or data model/schema.
- No alcohol-named items added in V1.1 runtime patch.

Changed files:
- `app/routes/player.py`
- `app/templates/treasurer_shop.html`

Added bar shelf actions:
- `author_tea` — 3 gold
- `lemonade_02` — 2 gold
- `sobranie_pizza` — 6 gold
- `anna_pavlova` — 2 gold

All four items are bar/social-only (no influence, no diplomacy, no court/final effect):
- `author_tea`
- `lemonade_02`
- `sobranie_pizza`
- `anna_pavlova`

Smoke results on fresh server at `http://127.0.0.1:8001/dev/treasurer-shop/LIVE01`:
- `author_tea`: ok=true, gold 72 -> 69, influence unchanged, Master event=true, TV event=true
- `lemonade_02`: ok=true, gold 69 -> 67, influence unchanged, Master event=true, TV event=true
- `sobranie_pizza`: ok=true, gold 67 -> 61, influence unchanged, Master event=true, TV event=true
- `anna_pavlova`: ok=true, gold 61 -> 59, influence unchanged, Master event=true, TV event=true
- Note: fresh server on port 8001 was used because dev port 8000 returned stale Python import state.

Regression checks:
- `set_bar` works.
- `giraffe` works.
- `gift_to_ally` without active alliance blocked.
- `gift_to_ally` with active alliance works; actor/ally +1 influence each.
- non-treasurer blocked from purchase endpoint.

Route + visibility:
- Operator route remains `/dev/treasurer-shop/{room_code}`.
- No purchase buttons were added in `player_room`.
- `gift_to_ally` behavior left unchanged.
- Alcohol/legal wording items remain deferred: `champagne_premier`, `tincture_set`, `shihan_beer_giraffe`, `beer_set_any`.
