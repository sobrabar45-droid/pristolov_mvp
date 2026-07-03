# Live Operator Checklist V2

## 1. Purpose

This checklist helps the host/operator run the next live game after the post-rehearsal cleanup, Harchevnya 18+ rollout, and Diplomacy + Whisper V1 print-pack updates.

It is practical, not theoretical:

- what to open before guests arrive;
- what to check during each stage;
- what not to touch during live play;
- how to handle common failures calmly;
- what to record after the game before the next development block.

## 2. Absolute safety rules

- Do not touch `LIVE01` without explicit Victor approval.
- Do not run migrations before the game.
- Do not deploy during the game.
- Do not restart production during the game unless there is a critical failure and Victor approves.
- Do not run mutating smoke on the production live room.
- Do not confirm test purchases in a live room.
- Harchevnya replacements are manual only.
- 18+ positions require staff/bar confirmation.
- The game screen does not replace real-world age/legal checks.
- Host/operator is final authority for Diplomacy + Whisper V1.
- Whisper effects are manual and host-confirmed; no automatic theft, penalty, deal break, or hidden irreversible effect.

## 3. Before guests arrive

Checklist:

- Confirm production site opens.
- Confirm operator has correct protected access.
- Confirm Master screen opens.
- Confirm TV screen opens.
- Confirm one Player screen opens.
- Confirm cashier/gold desk opens if Harchevnya is used.
- Confirm print materials are ready:
  - player one-page rules;
  - House table markers;
  - role cards/badges;
  - Diplomacy + Whisper cards;
  - host resolution sheets.
- Confirm chargers, power, Wi-Fi, and backup devices are ready.
- Confirm browser tabs are pinned or clearly named.
- Confirm TV/browser zoom is readable from far tables.
- Confirm host and technical operator know who makes final calls during incidents.

## 4. Required browser tabs

Open and label these before guests arrive:

- Master screen.
- TV screen.
- Cashier/gold desk, if Harchevnya is used.
- Dev/admin screen only if required and authorized.
- At least one test Player screen.
- Production logs/status only for technical operator, not for host.

Do not leave sensitive admin screens visible to players.

## 5. Non-LIVE smoke before game

Use a non-LIVE room only if available and explicitly approved.

Checklist:

- Do not mutate `LIVE01`.
- Check Master screen loads.
- Check TV screen loads.
- Check one Player screen loads.
- Check Harchevnya block is visible for `Мастер над золотом`.
- Check 18+ items are hidden by default.
- Check `Показать позиции 18+` reveals 18+ items.
- Check 18+ warning copy is readable.
- Check cashier 18+ warning if cashier screen is accessible.
- Do not confirm purchases unless explicitly approved.
- Do not alter real game state.

If no safe non-LIVE room is available, skip mutating smoke and run only visual/read-only checks.

## 6. Start of game checklist

Before the first active stage:

- Room/code prepared.
- Houses assigned.
- House table markers placed.
- Roles explained.
- Player QR/links distributed.
- Master/TV synchronized.
- First stage announcement visible.
- Host explains:
  - gold;
  - roles;
  - individual phones;
  - Harchevnya;
  - Diplomacy;
  - Мастер над шёпотом;
  - no automatic Whisper penalties;
  - what to do if a phone freezes.

Host opening reminder:

> If your screen freezes, do not register again. Refresh once, then show the screen to the host/operator.

## 7. During game: stage checks

### Intro / warmup

Operator checks:

- TV shows stage announcement.
- Master shows current stage briefing.
- Players understand House and role.
- QR/player access is stable.

Common failure:

- A player is in the wrong House or has no role.

First action:

- Ask the player to show their screen; do not create duplicate registration without operator decision.

### Question reveal

Operator checks:

- Question-only stage appears first.
- Answer options are hidden before host opens answers.
- Timer starts only after answers open.
- Correct answer is hidden before reveal.
- Correct answer appears on Master/TV after reveal.

Common failure:

- Host thinks answer did not reveal.

First action:

- Check whether the question was force-closed/revealed, then refresh TV/Master once.

### Expedition / map

Operator checks:

- Lord / Lady understands who is assigned.
- Assigned players see direction choice.
- Non-assigned players know they can discuss but not vote.
- Stalled players are identified early.

Common failure:

- Assigned player does not see destination choice.

First action:

- Ask the player to refresh once or show the screen to host/operator.

### Diplomacy / free play

Operator checks:

- Diplomats know they can move/negotiate.
- Deal cards are available.
- Host confirms official deals if needed.
- TV/Master announcements do not promise automatic enforcement.

Common failure:

- Players argue that a deal must automatically apply.

First action:

- Host clarifies: V1 deals are political promises; effects are manual/host-interpreted.

### Harchevnya

Operator checks:

- `Мастер над золотом` can see the request block.
- Non-18+ items are visible.
- 18+ items are hidden until checkbox unlock.
- Cashier queue receives requests.
- Gold is charged only after cashier/bar confirmation.

Common failure:

- Player thinks request already spent gold.

First action:

- Explain: request is pending until cashier/bar confirms.

### Duel

Operator checks:

- Duel challenge/acceptance state is clear.
- Master can resolve winner.
- If offline game ends in draw, Master can mark `Ничья / переигровка`.
- Draw/replay does not apply winner reward.

Common failure:

- Duel stalls after a draw.

First action:

- Mark draw/replay and either replay manually or move on by host decision.

### Court

Operator checks:

- Court stage announcement is visible.
- Houses know who speaks/participates.
- Any promised Court support is treated as political promise unless host manually rules otherwise.

Common failure:

- Players expect hidden automatic Court bonus from a deal.

First action:

- Host clarifies manual V1: no automatic Court modifier from deal cards.

### Final

Operator checks:

- TV shows final stage.
- Host controls pace.
- Phones remain useful but do not distract from final.
- Any Last Whisper / final-window action is host-controlled.

Common failure:

- Players keep negotiating when final focus is needed.

First action:

- Host announces final lock-in and redirects attention to TV/table.

## 8. Harchevnya operator checklist

- Player request does not instantly spend gold.
- Cashier/bar confirms before gold is charged.
- 18+ warning must be visible for alcohol positions.
- Staff/bar confirms availability and legality.
- Staff may refuse service regardless of game gold.
- No automatic replacement.
- No automatic refund/substitution.
- If unavailable, replacement is manual only through staff/host/cashier.
- House/player must agree to replacement.
- Record any unavailable item or confusing request for post-game feedback.

## 9. Diplomacy + Whisper manual checklist

- Give each House 3 Whisper charges.
- Дипломат receives/understands deal cards.
- Мастер над шёпотом receives/understands action cards.
- Host uses resolution sheet.
- Host approves, rejects, or rephrases every Whisper action.
- No automatic theft.
- No automatic penalty.
- No automatic deal break.
- No hidden irreversible effects.
- Avoid repeated targeting or harassment of one House.
- Record which cards were used.
- After game, mark which cards created useful drama and which confused players.

## 10. Failure handling

### Player phone frozen

Check first:

- Is the player on Wi-Fi/mobile internet?
- Does refresh work?
- Is the player using the correct link/token?

Do not:

- Create a new registration immediately.
- Tell the player to spam buttons.

Escalate if:

- Refresh fails twice or several players report the same issue.

### Player does not see current stage

Check first:

- Player has correct room/player token.
- Player refreshed once.
- Master/TV agree on stage.

Do not:

- Reset room.
- Change phase manually without host/operator agreement.

Escalate if:

- Many players are out of sync.

### TV not updated

Check first:

- Browser refresh.
- Network/HDMI/TV display.
- Master state is moving.

Do not:

- Restart production during game unless Victor approves.

Escalate if:

- TV and Master both stop updating.

### Master not updated

Check first:

- Protected access/session.
- Browser refresh.
- Service/site still opens.

Do not:

- Deploy or pull code.
- Run migrations.

Escalate if:

- Master remains unavailable after refresh and site check.

### Harchevnya not visible

Check first:

- Player role is `Мастер над золотом`.
- Player is in correct House/room.
- Player refreshed once.

Do not:

- Create duplicate player without operator decision.

Escalate if:

- Correct role still cannot see Harchevnya.

### 18+ checkbox not working

Check first:

- Player is on `Мастер над золотом` screen.
- Browser refresh.
- Checkbox is actually checked.

Do not:

- Promise alcohol manually through game UI if screen is unclear.

Escalate if:

- 18+ items remain inaccessible and bar wants to use them.

### Question answer not revealed

Check first:

- Was answers stage opened?
- Was question force-closed/revealed?
- Master/TV refreshed once.

Do not:

- Reveal answer verbally before host decides.

Escalate if:

- Master/TV state does not expose reveal after close.

### Duel ends in draw

Check first:

- Is Master on duel state?
- Use draw/replay action.

Do not:

- Pick fake winner just because the UI needs resolution.

Escalate if:

- Draw/replay button is unavailable.

### Cashier cannot confirm

Check first:

- Cashier page protected access.
- Request still pending.
- House has enough gold.
- Staff/bar approves availability.

Do not:

- Serve item through game if cashier/bar cannot confirm and gold state matters.

Escalate if:

- Multiple pending requests cannot be handled.

### Wi-Fi problem

Check first:

- Is it one phone or many?
- Mobile data fallback.
- Router/access point status.

Do not:

- Blame players or ask everyone to re-register.

Escalate if:

- Multiple Houses lose access.

### Host is confused

Check first:

- Stage announcement.
- Host quick script.
- Operator checklist.

Do not:

- Improvise new mechanics that change balance.

Escalate if:

- A rule decision affects scoring, gold, duel result, or 18+ service.

## 11. Post-game checklist

- Do not immediately start coding fixes during emotions.
- Collect feedback while memories are fresh.
- Record technical issues:
  - phone freezes;
  - TV/Master sync;
  - Harchevnya requests;
  - cashier confirmation;
  - question reveal;
  - duel draw/replay;
  - Expedition stalls.
- Record confusing rules:
  - Diplomacy;
  - Whisper charges;
  - Harchevnya 18+;
  - gold;
  - Court;
  - Duel.
- Record unused mechanics.
- Record strongest moments.
- Record Harchevnya usage.
- Record Diplomacy/Whisper usage.
- Record Duel/Court issues.
- Create post-game checkpoint before the next development block.

## 12. Quick print version

1. Open production site.
2. Open Master screen.
3. Open TV screen.
4. Open cashier/gold desk if Harchevnya is used.
5. Open one Player screen.
6. Confirm protected access works.
7. Do not touch `LIVE01` without Victor approval.
8. Do not deploy, migrate, or restart during game unless critical and approved.
9. Place House markers.
10. Hand out/prepare role cards.
11. Prepare player rules and Diplomacy + Whisper cards.
12. Confirm first stage announcement appears.
13. Explain phones, gold, roles, Harchevnya, Diplomacy, Whisper.
14. Harchevnya requests spend gold only after cashier/bar confirmation.
15. 18+ items require staff/bar confirmation.
16. Replacements are manual only.
17. Give each House 3 Whisper charges.
18. Whisper effects are host-confirmed; no automatic penalties.
19. If screen freezes: refresh once, then show operator.
20. After game: collect feedback and create checkpoint before coding.
