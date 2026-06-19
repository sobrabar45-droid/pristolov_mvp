# Next contour selection after support-role UX polish

## Audit context

Recent work is stable and user-visible surfaces are production-ready:

- Cashier + standalone Gold Desk flow deployed.
- Treasurer Shop V1.2 request/confirmation flow deployed.
- Support-role UX polish rolled out.
- Codex-first smoke rhythm is adopted in repo control docs (`8f9da8e`).

No runtime patch is requested in this step.

## Candidate contours

| Candidate | Value before live | Risk | Scope size | Runtime patch needed | Codex-first verify? |
|---|---|---|---|---|---|
| A. Pre-live full smoke / readiness audit | High — validates complete live path across player, cashier, Master/TV, phases, and Gold/requests | Low-medium (exposure of gaps) | Small (docs + endpoint checks; smoke script plan) | No | Yes (routes, status checks, curl/API checks, no destructive actions) |
| B. Treasurer Shop V1.3 (`request` history/status actions: reject/cancel) | Medium — user-facing operational convenience | Medium (ledger/state contract changes) | Medium | Yes | Partial (needs new states and UI checks) |
| C. Player Room role mechanics expansion for `maester`/`house_sworn` | Low-medium (engagement improvement) | Medium-high (design-risk and balance impact) | Large | Yes | Mostly no (requires gameplay scenario checks) |
| D. Master/TV event clarity polish | Medium — reduces operator confusion during game | Low-medium | Small-medium | Yes (template/wording) | Yes (text + rendering checks; visual QA final only) |
| E. Mojibake cleanup pass | Medium | Low | Small | Possibly (if any runtime/template artifacts remain) | Yes (rg + targeted compile/smoke for affected routes) |

## Recommended next contour

- **Selected: A — Pre-live full smoke / readiness audit**

### Why A is selected

- It gives highest immediate live value: one checklist validates all operational surfaces together.
- It aligns with current rule: Codex-first automated checks first, manual visual checks only for final acceptance.
- It is audit-only and low-risk because it does not change gameplay contracts.

### Why others are deferred now

- **B** and **C** introduce state/API/UI changes and should follow a separate runtime-planned block.
- **D** is useful, but its impact is narrower and can be included in/after a full readiness pass.
- **E** should be done as a scoped cleanup when concrete new corruption is confirmed in remaining surfaces.

## Next exact task

- Run pre-live readiness audit across:
  - player_room role/phase behavior,
  - cashier queue + confirmation path,
  - Master/TV visibility,
  - gold endpoints and status gates.
- Record results in runtime readiness artifacts before any next patch.

