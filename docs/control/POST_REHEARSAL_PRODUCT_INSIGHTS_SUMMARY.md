# Post-Rehearsal Product Insights Summary

Date: 2026-06-23

## Core insight

The individual player-phone model is still the V1 product direction, but it must become technically boring under load. The rehearsal showed that unstable player screens damage pacing, atmosphere, and host attention more than almost any single gameplay issue.

## Product decision

- Keep individual player phones and role screens for V1.
- Do not switch to one tablet per House now.
- Keep one tablet per House as a V2 hypothesis only.
- Treat stability/scalability as the next core product contour.

## Capacity expectation

- Reproduce around 25-40 clients because rehearsal trouble appeared around 21 players.
- Design for at least 100 player clients in one room.
- Include Master, TV, cashier, Treasurer Shop/operator, and dev/operator screens on top.
- Future franchise/multi-city usage requires multiple independent rooms after single-room stability is proven.

## Operational lesson

The host cannot be the phone-support person during live play. If a player screen loses connection, the system needs either to keep showing the last useful state, recover quietly, or make the next action obvious without host intervention.

## Next product/technical contour

No gameplay expansion should be prioritized until the stability target is understood.

Immediate next step:

- collect VPS production diagnostics;
- run controlled load probes locally/staging first;
- decide whether to patch polling, DB writes, worker/process model, DB strategy, server capacity, or client degraded-mode behavior.

## Not decided yet

- Whether the main fix is app code, server config, DB architecture, or network operations.
- Whether 100+ target requires PostgreSQL/process model changes.
- Whether player screens should later move from polling to SSE/WebSocket/push.
- Whether one tablet per House becomes useful in V2 after V1 phone reliability is solved.
