# Physical House/role markers audit and V1 design

Date: 2026-06-27

## 1. Purpose

This document turns rehearsal feedback into a practical V1 physical marker system for PRISTOLOV.

Physical markers are needed because the digital screens and printed rules are not enough during a noisy live game:

- players must instantly understand which House is which;
- the host must see who is sitting where;
- active roles must be visible without asking every table;
- Diplomacy, Duels, Expedition, Court, and host instructions move faster when Houses and roles are physically readable;
- far tables need large, high-contrast signs rather than small text on phones.

V1 goal: simple, printable, reusable-enough markers that improve live orientation without changing runtime logic.

## 2. Current problem from rehearsal

Observed issues:

- players did not always understand who belonged to which House;
- roles were not visible enough to the host, other players, or sometimes the House itself;
- it was unclear who the Diplomat was during negotiation windows;
- far tables were hard to read;
- the host needed a faster seating/role map;
- printed rules help before the game, but they do not solve live-room visibility;
- when the host calls a role, the room should visually know who needs to move or answer.

Design implication:

- House identity should be visible from across the room;
- role identity should be visible at least at the table and to the host;
- special movement roles should be extra easy to spot;
- the system must work for fewer than 10 Houses and up to 10 Houses.

## 3. V1 marker system

Minimal practical set:

1. House table marker
   - one large table tent or vertical card per House;
   - visible House name, short label, color, and icon;
   - readable from 3-5 meters.

2. Role badge/card for each player
   - visible role name;
   - 2-3 short duties;
   - can be badge, lanyard insert, sticker, or folded mini-card.

3. Host seating map
   - one A4/A3 operator sheet;
   - table number, House, roles, optional player names, notes;
   - not a replacement for the system state.

4. Optional color wristband/ribbon
   - House-color ribbon or sticker for quick visual grouping;
   - useful when players move during Diplomacy or breaks.

5. Optional small role card
   - placed near player or handed to player;
   - should not be a full manual;
   - only role name, when important, and what to do if confused.

Recommended V1 package:

- House table tents: required.
- Role badges/cards: required.
- Host seating map: required.
- Wristbands/ribbons: optional but useful.
- Full designed merch: not V1.

## 4. House table markers

Use official House names only.

| House | Short table label | Icon idea | Color idea | Table marker format | Visibility requirement |
|---|---|---|---|---|---|
| Дом Волка | Волк | wolf silhouette / paw | deep gray + cold blue | A5 folded tent or A4 vertical stand | House name readable from far tables |
| Дом Башни | Башня | tower / fortress | stone gray + brass | A5 folded tent or A4 vertical stand | strong block letters, high contrast |
| Дом Солнца | Солнце | sun disk / rays | gold + warm orange | A5 folded tent or A4 vertical stand | bright but not low-contrast yellow text |
| Дом Меча | Меч | crossed sword / blade | steel + red accent | A5 folded tent or A4 vertical stand | icon large enough for quick recognition |
| Дом Свитка | Свиток | scroll / parchment | parchment beige + ink brown | A5 folded tent or A4 vertical stand | avoid pale-on-white print |
| Дом Печати | Печать | seal stamp / wax seal | burgundy + cream | A5 folded tent or A4 vertical stand | visible seal icon, large House name |
| Дом Ключа | Ключ | key | dark green + gold | A5 folded tent or A4 vertical stand | key icon should be simple, not ornate |
| Дом Огня | Огонь | flame | black + orange/red | A5 folded tent or A4 vertical stand | strong contrast for dim bar light |
| Дом Ворона | Ворон | raven / feather | black + violet/blue accent | A5 folded tent or A4 vertical stand | do not use black text on dark background |
| Дом Чаши | Чаша | cup / chalice | wine red + silver | A5 folded tent or A4 vertical stand | cup icon and name both visible |

Table marker content:

- large House name;
- short label;
- icon;
- optional table number;
- optional QR/link only if it does not clutter the sign.

Do not put long rules on House table markers.

## 5. Role markers

Role markers should answer two questions quickly:

- who is this player in the House;
- when does this role matter.

| Role | Visible label | Marker says | Who must recognize it | Recommended physical format |
|---|---|---|---|---|
| Лорд / Леди Дома | Лорд / Леди | “Решает за Дом. Экспедиции, дуэли, ключевые выборы.” | host, whole House, other Houses during disputes | lanyard badge or large chest sticker; optional table mini-stand |
| Мастер над золотом | Золото | “Следит за золотом и заявками. Расходы только после подтверждения.” | host, cashier, House | badge/card plus optional gold-color sticker |
| Дипломат | Дипломат | “Ищет союзы и договорённости. В переговоры выходит первым.” | host, other Houses, all Diplomats | extra-visible badge/lanyard; optional ribbon for movement |
| Мастер над шёпотом | Шёпот | “Действует в Последний Шёпот. Следит за тайным моментом.” | host and House; visibility policy needs decision | badge/card; can be visible or semi-private depending on host choice |
| Мейстер | Мейстер | “Помогает думать, помнить факты и держать темп.” | House, host when calling question support | badge/card or table-side card |
| Соратник Дома | Соратник | “Поддерживает обсуждение и помогает ролям Дома.” | House and host | simple badge/card/sticker |

Role marker copy style:

- 1 large role name;
- 1 short duty line;
- 1 “when needed” hint;
- no hidden mechanics;
- no backend words;
- no long lore.

Extra visibility recommendations:

- Дипломат should be very visible during negotiation windows.
- Лорд / Леди should be visible at all times.
- Мастер над золотом should be easy for cashier/operator to identify.
- Мастер над шёпотом may be visible for usability, but secrecy is an open product decision.

## 6. Host seating map

Host-facing sheet format:

| Table | House | Лорд / Леди | Мастер над золотом | Дипломат | Мастер над шёпотом | Мейстер | Соратники | Notes |
|---|---|---|---|---|---|---|---|---|
| 1 |  |  |  |  |  |  |  |  |
| 2 |  |  |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  |  |
| 4 |  |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |
| 6 |  |  |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  |  |
| 8 |  |  |  |  |  |  |  |  |
| 9 |  |  |  |  |  |  |  |  |
| 10 |  |  |  |  |  |  |  |  |

Rules for the seating map:

- use it for orientation, not as the source of truth for gold/influence;
- do not manually duplicate current gold/influence unless the operator explicitly needs an emergency paper backup;
- update role names only when a real role change happens;
- keep player names optional to reduce setup pressure.

Recommended physical format:

- A3 clipboard for host if available;
- A4 is acceptable if fewer Houses;
- thick marker/pen, not tiny handwriting;
- one spare blank sheet.

## 7. Print/production recommendations

House table markers:

- 10 House markers maximum set;
- A5 folded tent minimum;
- A4 vertical stand preferred for far tables;
- font: 48-72 pt for House name if A4, 32-48 pt if A5;
- matte lamination or thick paper to survive bar tables;
- color + icon + name, not color alone.

Role markers:

- capacity target: 100 players;
- practical starter pack:
  - 10 Лорд / Леди badges;
  - 10 Мастер над золотом badges;
  - 10 Дипломат badges;
  - 10 Мастер над шёпотом badges;
  - 10 Мейстер badges;
  - 50 Соратник Дома badges/cards;
  - 10-20 blank spare role cards.

Wristbands/ribbons:

- optional House-color ribbon/sticker set;
- useful for moving players and Diplomacy;
- should match table marker colors.

Production style:

- large text beats beautiful detail;
- high contrast beats lore texture;
- reusable laminated House markers are worth it;
- disposable role stickers are acceptable for V1;
- avoid tiny icons as the only identifier.

## 8. What not to do in V1

Do not spend V1 effort on:

- expensive merch;
- metal pins, custom coins, premium lanyards, or complex costumes;
- complex lore cards;
- public House bonuses/perks;
- QR-only identification;
- changing digital role logic;
- changing runtime code;
- changing House assignment mechanics;
- making markers depend on exact final roster before guests arrive.

Do not turn the marker system into a second rules manual.

## 9. Operator flow

Before registration:

- place blank table numbers or reserved House marker slots;
- prepare all 10 House table markers nearby;
- prepare role badge/card stacks;
- prepare host seating map.

After House creation / House assignment:

- place the selected House marker on that table;
- write table number on host seating map;
- give Лорд / Леди the most visible marker first.

After role assignment:

- issue role badges/cards;
- confirm each role aloud at the table;
- ask Дипломат and Лорд / Леди to raise hands once so host can locate them;
- mark key roles on host seating map if needed.

Suggested host phrase:

“Теперь каждый Дом должен быть виден в зале. На столе стоит ваш Дом, а роли должны быть у игроков на виду. Если ведущий зовёт роль, смотрим на карточку и действуем.”

If someone loses a marker:

- issue a blank spare card/sticker;
- write role name with thick marker;
- update host seating map only if the role actually changed.

During game:

- call roles by exact names;
- use markers to find Diplomats during Diplomacy;
- use markers to find Лорд / Леди during Duels, Court, Expedition, and final decisions;
- do not ask players to identify themselves repeatedly if the marker already solves it.

## 10. Open questions

- Exact final House colors: should they match future visual identity or stay pragmatic for print contrast?
- Icon source: custom icons, simple generated icons, or text-only V1?
- Should roles be visible to everyone or only to host/House?
- Should Дипломат be extra visible with a special ribbon or lanyard?
- Should Мастер над шёпотом be hidden/secret or visible for usability?
- Should role cards be reusable laminated cards or disposable stickers?
- Should House markers include table number, QR, or only House identity?
- Should one “active role now” sign exist near TV/host?

## 11. Next recommended task

Recommended next task: first print pack draft for player rules + markers.

Why:

- the one-page player guide is drafted;
- this document defines the physical marker system;
- the next useful step is to produce printable artifacts rather than another abstract plan;
- a print pack can include:
  - one-page player guide;
  - 10 House table markers;
  - 6 role card/badge templates;
  - host seating map.

Alternative next task: Harchevnya / 18+ / availability audit, if the next live event needs bar/menu mechanics before print production.

Do not produce print assets before reviewing this marker design.
