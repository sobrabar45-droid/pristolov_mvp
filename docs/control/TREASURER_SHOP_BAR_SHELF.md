# Treasurer Shop Bar Shelf (V1.1 candidate)

**Status:** Product decision only. No runtime changes have been implemented yet.

## Current V1 runtime baseline

- V1 is operator-mediated and accessed at:
  - `/dev/treasurer-shop/{room_code}`
- Player-room purchase buttons are intentionally absent in V1.
- The current V1 runtime menu still maps to existing actions:
  - `set_bar`
  - `giraffe`
  - `gift_to_ally`

## Proposed Bar Shelf product menu (V1.1 candidate)

- `3` gold — `авторский чай`
- `7` gold — `шампанское премиум премьер`
- `7` gold — `сет настоек`
- `10` gold — `Жираф пива Шихан`
- `2` gold — `лимонад 0.2`
- `6` gold — `пицца Собрание`
- `10` gold — `любой пивной сет (1, 2, 3, 4)`
- `2` gold — `десерт Анна Павлова`
- `7` gold — `сет тапасов`

## V1.1 readiness notes (decision-only)

- This is a **V1.1 candidate only** and is **not implemented in runtime** yet.
- Treasurer Shop remains operator-mediated until a later runtime task explicitly approves player-facing changes.
- The next runtime patch must include deterministic mapping from each product label to a stable `action_code`.
- The next runtime patch must explicitly decide which items only trigger bar/social events and which, if any, also modify influence.
- Public/legal wording should be reviewed separately before using any alcohol names in public-facing materials.

## V1.1 runtime candidate selection

First safe runtime batch (non-alcohol, bar/social only):

- `author_tea` — 3 gold — bar/social only
- `lemonade_02` — 2 gold — bar/social only
- `sobranie_pizza` — 6 gold — bar/social only
- `anna_pavlova` — 2 gold — bar/social only

Deferred to later runtime candidate (pending wording/legal/public-display decision):

- `champagne_premier`
- `tincture_set`
- `shihan_beer_giraffe`
- `beer_set_any`

Control note:

- `gift_to_ally` remains a political/social action and is not a normal bar shelf SKU.

## Out of scope (this doc)

- Do not replace the current Treasurer Shop V1 runtime menu yet.
- Do not add purchase buttons to `player_room` in this phase.
