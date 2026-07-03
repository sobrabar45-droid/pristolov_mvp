# Production Browser Smoke Protocol: Non-LIVE Rooms

## 1. Purpose

This protocol is for browser-based production smoke checks with protected/authorized access.

It is non-LIVE only.

It checks visibility and basic UI behavior:

- public page availability;
- Master / TV / Player page rendering;
- Harchevnya 18+ visibility behavior;
- cashier/gold desk visibility if authorized;
- readable Cyrillic and usable layout.

It must not mutate real game state unless Victor explicitly approves the exact action, room, and purpose.

## 2. Absolute safety rules

- Do not touch `LIVE01` without explicit Victor approval.
- Do not use a live production room.
- Do not confirm Harchevnya purchases.
- Do not spend real House gold.
- Do not resolve real duels.
- Do not close real questions.
- Do not advance real stages.
- Do not run migrations.
- Do not deploy.
- Do not restart production.
- Do not use `/dev` actions on a real live room.
- If unsure whether a room is safe, stop.

## 3. Preconditions

Checklist:

- Protected browser access is available.
- A non-LIVE production room exists, or Victor explicitly creates/approves one.
- Operator knows which room code is safe.
- Current production service is active.
- Browser tabs can be opened for Master, TV, Player, and cashier/gold desk.
- No guests are actively using the test room.
- Technical operator understands which actions are read-only and which actions mutate state.

If any precondition is missing, label the attempt `BLOCKED_PROTECTED_ACCESS` or `BLOCKED_NO_NON_LIVE_ROOM`.

## 4. Browser tabs to open

Use placeholders unless the operator already has the exact protected links:

```text
<PRODUCTION_BASE_URL>
<NON_LIVE_ROOM_CODE>
<TEST_PLAYER_LINK>
```

Open:

- public/home page;
- Master screen for `<NON_LIVE_ROOM_CODE>`;
- TV screen for `<NON_LIVE_ROOM_CODE>`;
- Player room for `<TEST_PLAYER_LINK>`;
- cashier/gold desk for `<NON_LIVE_ROOM_CODE>`, if available and authorized;
- optional production status/log view only for technical operator.

Do not expose protected/admin screens to guests.

## 5. Smoke checklist: read-only / visual

Check:

- public page opens;
- Master page loads;
- TV page loads;
- Player page loads;
- screens show the same room/stage;
- no visible 500/error page;
- no mojibake / broken Cyrillic;
- mobile-width player page is readable;
- desktop-width Master/TV pages are readable;
- browser console has no obvious blocking errors, if operator knows how to check.

Do not click actions that mutate state.

## 6. Harchevnya visual smoke

Check visibility only:

- Harchevnya block is visible to the correct role/player, if available.
- Non-18+ approved shelf is visible.
- 18+ items are hidden by default.
- `Показать позиции 18+` checkbox is visible.
- After checking it, 18+ items appear.
- Player copy says staff/bar confirmation is required.
- Player copy does not promise automatic replacement.
- No purchase confirmation is submitted.
- Cashier/gold desk shows 18+ warning if a pre-existing safe pending request exists.
- If no pending request exists, do not create one unless Victor explicitly approves.

Expected 18+ rule:

- Game UI can reveal 18+ positions after checkbox.
- Staff/bar still makes the real-world service decision.
- Gold is charged only after cashier/bar confirmation.
- Replacement is manual only.

## 7. Question Reveal visual smoke

Read-only if possible:

- current question screen renders;
- staged reveal copy is understandable;
- options are not shown before the proper stage if a question is currently in question-only mode;
- after actual gameplay reveal, answer should be visible on Master/TV.

Do not force-close a question.

Do not mutate real question state.

## 8. Duel draw visual smoke

Read-only if possible:

- existing duel status renders clearly;
- draw/replay status displays as replay needed if such state exists;
- Master/TV wording is understandable.

Do not create a real duel.

Do not accept, resolve, or mark draw on a real duel in this protocol.

## 9. Diplomacy + Whisper manual materials check

Production runtime is not required for the manual Diplomacy + Whisper V1 pack.

Check only:

- operator has printed materials;
- host understands manual-only;
- each House can receive 3 Whisper charges if the mechanic is used;
- no one expects runtime support for Whisper charges;
- no automatic penalties are promised;
- host is ready to approve, reject, or rephrase actions.

## 10. Stop conditions

Stop immediately if:

- room appears to be `LIVE01`;
- real guests/players are active in the room;
- any action would spend gold;
- any action would close a question;
- any action would advance a stage;
- any action would resolve a duel;
- any action would confirm a purchase;
- protected access is unclear;
- operator is unsure whether the room is safe;
- any 500/error page appears;
- browser shows the wrong room code;
- the test would require `/dev` mutation on a live room.

When stopped, record the result as `STOPPED_SAFETY_RISK` or the most specific blocked/fail label.

## 11. Evidence to record

Record:

- date/time;
- operator;
- production base URL used, if allowed internally;
- room code checked;
- protected access confirmed yes/no;
- pages opened;
- visible result for Master/TV/Player;
- Harchevnya 18+ visibility result;
- cashier warning result if checked;
- errors observed;
- screenshots, optional;
- whether any state mutation happened. Expected: no.

Screenshots should not be committed unless explicitly requested.

## 12. Result labels

Use one label:

- `PASS_READ_ONLY` — all planned read-only checks passed and no mutation happened.
- `PASS_WITH_LIMITATIONS` — core pages worked, but some optional checks could not be completed safely.
- `BLOCKED_PROTECTED_ACCESS` — protected access was unavailable or unclear.
- `BLOCKED_NO_NON_LIVE_ROOM` — no safe non-LIVE room was available.
- `FAIL_UI_ERROR` — page rendered 500/error/broken UI in a safe check.
- `STOPPED_SAFETY_RISK` — check was stopped because continuing could touch live state or mutate unsafe data.

## 13. Required report format

```text
Production Browser Smoke Report

Date/time:
Operator:
Production base:
Room code:
Protected access confirmed: yes/no
LIVE01 touched: no
Mutating actions performed: no

Public page:
Master:
TV:
Player:
Cashier/gold desk:
Harchevnya non-18+:
Harchevnya 18+ hidden by default:
Harchevnya 18+ visible after checkbox:
Question reveal visual:
Duel draw visual:
Diplomacy/Whisper print materials:

Errors:
Screenshots:
Final verdict:
Next action:
```
