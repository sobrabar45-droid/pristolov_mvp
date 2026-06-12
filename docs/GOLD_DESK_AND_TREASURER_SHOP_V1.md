# Gold Desk and Treasurer Shop V1

## Purpose

This document fixes the V1 product model for gold economy in PRISTOLOV_CORE.
It explains how gold is earned, how gold is spent, why the Treasurer role exists,
and where the line is between gameplay purchases and bar purchases.

V1 goal: make gold understandable, spendable, and socially visible without turning
bar purchases into direct pay-to-win mechanics.

## Core Loop

```text
Order -> receive gold -> spend gold -> need more gold -> order again
```

The economy should be simple enough to explain at the table:

- A House orders at the bar.
- The bar/cashier adds gold to that House.
- The Treasurer decides how to spend it.
- The House sees a reason to earn or order more.
- The room sees visible consequences when gold is spent.

## Gold Exchange

Product rule for V1:

```text
500 RUB = 1 gold
gold = floor(order_amount_rub / 500)
```

Open mismatch:

- The current codebase has gold conversion logic in `gold_service.py`.
- Current formula observed during audit: `amount_rub // 1500 * 3`.
- Product target is simpler: `floor(amount / 500)`.
- This mismatch should be resolved before public V1 if Gold Desk is enabled.

## Gold Desk V1

Gold Desk is a separate operator screen for cashier/bar use.

It should allow the bar operator to:

- Select a House.
- Enter order amount in RUB.
- See calculated gold.
- Add gold to the selected House.
- Write a `HouseGoldTransaction` log entry.
- Keep the host out of check accounting.

The host should announce the economy and narrate consequences, but should not
manually count receipts during the game.

## Treasurer Shop V1

Treasurer Shop is a player-facing block or screen for the Treasurer role.

It should allow gold to be spent in real time during the game.

Product goals:

- Make Treasurer an active role.
- Give the House a clear reason to order again.
- Turn gold from a passive counter into a decision resource.
- Create visible table moments without overloading the host.

## Two Shelves Model

### A. Gameplay Shelf

Gameplay shelf purchases can affect the game, but should remain bounded.

Candidate V1 items:

- Hint.
- Intelligence.
- Expedition boost.
- Extra action.
- Political maneuver.

These items may affect strategy, tempo, or information, but must not create an
automatic win.

### B. Bar Shelf

Bar shelf purchases are show and social pressure items.

Candidate V1 items:

- Shot set.
- Giraffe.
- Gift to another House.
- Table treat.
- Bar mini-event.

Important V1 rule:

```text
Bar shelf does not grant direct victory.
```

It gives:

- Emotion.
- Show.
- A reason to order.
- Social pressure.
- Atmosphere.

## Role Responsibilities

Cashier/bar:

- Uses Gold Desk.
- Enters order amount.
- Assigns gold to the correct House.
- Does not decide gameplay effects.

Treasurer:

- Watches House gold.
- Chooses how to spend gold.
- Operates Treasurer Shop.
- Explains proposed spending to the House.

Lord/Lady:

- Approves large or politically risky spending.
- Can overrule Treasurer if table rules require it.

Host:

- Announces the economy.
- Narrates important spending.
- Does not count checks manually.
- Does not become the Treasurer's accountant.

## V1 Recommended Spend Menu

| Cost | Item | Shelf | V1 Intent |
| ---: | --- | --- | --- |
| 1 gold | Hint | Gameplay | Small help without changing the game too much |
| 2 gold | Expedition boost | Gameplay | Make expedition decisions feel funded |
| 3 gold | Intelligence | Gameplay | Reveal useful but bounded information |
| 3 gold | Extra action | Gameplay | Create urgency and tactical choice |
| 5 gold | Political maneuver | Gameplay | High-impact but host-visible action |
| 5 gold | Bar counter set / bar event | Bar | Public show moment without direct victory |
| 10 gold | Gift to another House / giraffe / table treat | Bar | Large social gesture and table spectacle |

## Implementation Roadmap

Phase 1: document + UI explanation.

- Publish this product model.
- Add clear text in relevant UI explaining what gold is for.
- Keep mechanics unchanged.

Phase 2: Gold Desk screen.

- Add cashier/bar screen.
- Implement `500 RUB = 1 gold`.
- Add transaction log entries.
- Keep player routes public and operator routes protected.

Phase 3: Treasurer Shop UI.

- Add Treasurer-only shop surface.
- List V1 items.
- Gate purchases by available House gold.
- Show clear success/failure messages.

Phase 4: transaction logs + TV events.

- Surface gold spend events in Master/TV state.
- Make major purchases visible to the room.
- Keep event text readable and non-technical.

Phase 5: bar shelf operations.

- Add bar shelf purchase flow.
- Keep effects atmospheric and social.
- Avoid direct victory effects.

## Open Questions

- Exact V1 prices.
- Current formula mismatch: code has `amount_rub // 1500 * 3`, product wants `floor(amount / 500)`.
- Whether gold should be awarded from the full check amount or only from the delta since last entry.
- Anti-abuse rules for repeated or corrected checks.
- Who confirms bar shelf purchases.
- Which purchases appear on TV.
- Legal/advertising wording for bar-related items.
- Whether Lord/Lady approval is required for purchases above a threshold.

## What Not To Do Now

- Do not integrate POS.
- Do not create a full inventory system.
- Do not make bar purchases pay-to-win.
- Do not let bar shelf affect victory directly.
- Do not replace the existing gold transaction model before V1.
- Do not add a broad economy rewrite while the role/action registry is frozen.
