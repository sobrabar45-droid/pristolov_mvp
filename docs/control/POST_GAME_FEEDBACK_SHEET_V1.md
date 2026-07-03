# Post-Game Feedback Sheet V1

## 1. Purpose

Use this sheet immediately after a live game.

Do not start coding fixes during emotions. First collect facts, then decide.

Separate:

- technical bugs;
- gameplay confusion;
- host/operator mistakes;
- print/material problems;
- production/access issues;
- strong moments worth preserving.

The goal is not to blame anyone. The goal is to decide what must be fixed before the next live game.

## 2. Fast host/operator debrief

Fill this first.

```text
Date:
Room code:
Number of Houses:
Approximate number of players:
Game duration:
Environment: production / local / other
Host:
Operator:
Final winning House:

Overall verdict:
[ ] strong
[ ] playable with issues
[ ] unstable
[ ] failed

One-sentence summary:
```

## 3. Technical issues log

Severity guide:

- `P0` — stopped or seriously broke live game flow.
- `P1` — visible issue with workaround; should fix before next game if repeated.
- `P2` — minor issue, confusing but not blocking.

| Time/stage | Screen affected: Master / TV / Player / Cashier / Other | What happened | Severity: P0 / P1 / P2 | Workaround used | Needs code fix: yes/no/unknown | Evidence: screenshot/log/link |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

Prompts:

- Phones frozen?
- Stage not updating?
- TV delay?
- Master delay?
- Player link problem?
- Harchevnya issue?
- 18+ checkbox issue?
- Question reveal issue?
- Duel/draw issue?
- Cashier/gold issue?
- Wi-Fi issue?
- Protected access issue?

## 4. Gameplay understanding

Check quickly.

| Question | Yes | No | Mixed | Notes |
| --- | --- | --- | --- | --- |
| Did players understand this is not just a quiz? | [ ] | [ ] | [ ] | |
| Did players understand Houses? | [ ] | [ ] | [ ] | |
| Did players understand roles? | [ ] | [ ] | [ ] | |
| Did players understand gold? | [ ] | [ ] | [ ] | |
| Did players understand Harchevnya? | [ ] | [ ] | [ ] | |
| Did players understand Diplomacy? | [ ] | [ ] | [ ] | |
| Did players understand Мастер над шёпотом? | [ ] | [ ] | [ ] | |
| Did players understand Court? | [ ] | [ ] | [ ] | |

What required repeated explanation?

```text

```

## 5. Stage-by-stage feedback

### Intro

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Warmup / questions

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Expedition / map

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Diplomacy / free play

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Harchevnya

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Duel

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Court

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

### Final

- Worked well:
- Confusing:
- Too long / too short:
- Technical issue:
- Keep / change / remove:

## 6. Role feedback

| Role | Was role useful? | Did player know what to do? | Did role affect the game? | Needs clearer card/script/runtime? |
| --- | --- | --- | --- | --- |
| Лорд / Леди Дома | | | | |
| Дипломат | | | | |
| Мастер над золотом | | | | |
| Мастер над шёпотом | | | | |
| Мейстер | | | | |
| Other House members | | | | |

Notes:

```text

```

## 7. Harchevnya feedback

| Question | Yes | No | Unknown | Notes |
| --- | --- | --- | --- | --- |
| Did any House open Harchevnya? | [ ] | [ ] | [ ] | |
| Did any House request items? | [ ] | [ ] | [ ] | |
| Did players understand request vs confirmation? | [ ] | [ ] | [ ] | |
| Were 18+ items hidden by default? | [ ] | [ ] | [ ] | |
| Did checkbox reveal 18+ items clearly? | [ ] | [ ] | [ ] | |
| Did staff/bar confirmation work? | [ ] | [ ] | [ ] | |
| Were any items unavailable? | [ ] | [ ] | [ ] | |
| Were manual replacements clear? | [ ] | [ ] | [ ] | |
| Any disputes about gold? | [ ] | [ ] | [ ] | |

Unavailable items / replacement notes:

```text

```

## 8. Diplomacy + Whisper feedback

| Question | Yes | No | Unknown | Notes |
| --- | --- | --- | --- | --- |
| Did Diplomats negotiate? | [ ] | [ ] | [ ] | |
| Did Houses use deal cards? | [ ] | [ ] | [ ] | |
| Did Мастер над шёпотом use charges? | [ ] | [ ] | [ ] | |
| Did players understand host confirmation? | [ ] | [ ] | [ ] | |
| Any toxic/overheated moments? | [ ] | [ ] | [ ] | |
| Did it create useful intrigue? | [ ] | [ ] | [ ] | |
| Should this remain manual? | [ ] | [ ] | [ ] | |
| Should this move toward runtime support? | [ ] | [ ] | [ ] | |

Cards used:

- [ ] Разведка
- [ ] Слух
- [ ] Тень сделки

Best Diplomacy / Whisper moment:

```text

```

Biggest Diplomacy / Whisper confusion:

```text

```

## 9. Player mini-survey

Give this to players or ask verbally. Keep it short.

1. What was the clearest part?

```text

```

2. What was the most confusing part?

```text

```

3. Which role/mechanic felt most useful?

```text

```

4. Did you use Harchevnya?

```text
yes / no
```

5. Did you use Diplomacy or Whisper?

```text
yes / no
```

6. Would you play again?

```text
yes / no / maybe
```

7. One thing to improve.

```text

```

## 10. Prioritization after game

| Issue | Category: technical / gameplay / host script / print materials / operations | Severity: P0 / P1 / P2 | Frequency: one House / several Houses / everyone | Proposed next action | Owner | Deadline |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |
| | | | | | | |

Rules:

- Fix only `P0` / `P1` before the next live game.
- Do not expand mechanics until core confusion is resolved.
- Do not digitalize Diplomacy + Whisper before at least one manual test result is reviewed.
- Do not turn one loud complaint into a feature without checking frequency.
- Keep strong moments; do not optimize all drama away.

## 11. Post-game checkpoint prompt

Ready to copy:

```text
Create a post-game checkpoint summarizing technical issues, gameplay feedback, Harchevnya usage, Diplomacy/Whisper usage, decisions, and next priorities. Docs only. Do not change runtime.
```

## 12. One-page quick version

### 10 host/operator questions

1. Did production/screens stay stable?
2. Did players understand this is not just a quiz?
3. Which stage caused the most confusion?
4. Which stage created the strongest moment?
5. Did roles feel useful?
6. Did Harchevnya work and stay clear?
7. Did 18+ confirmation stay safe?
8. Did Diplomacy create real negotiation?
9. Did Мастер над шёпотом create useful intrigue?
10. What must be fixed before the next game?

### 7 player questions

1. Clearest part:
2. Most confusing part:
3. Most useful role/mechanic:
4. Used Harchevnya: yes / no
5. Used Diplomacy or Whisper: yes / no
6. Would play again: yes / no / maybe
7. One thing to improve:

### Top 5 issues table

| # | Issue | Category | P0/P1/P2 | Frequency | Next action |
| --- | --- | --- | --- | --- | --- |
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |
