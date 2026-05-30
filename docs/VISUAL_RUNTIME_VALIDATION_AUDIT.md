# Visual Runtime Validation Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Scope: browser-visible Master, TV, and player runtime surfaces after MVP runtime stabilization.

## Purpose

The MVP runtime now has command-level smoke coverage for the main V1 contours. This audit defines what still needs browser-visible validation before a live game.

The question is not whether JSON state mutates correctly. The question is whether the host, TV room, and players can actually see important consequences clearly enough during a public run.

## Files Inspected

- `docs/RUNTIME_STABILITY_VALIDATION_PASS.md`
- `docs/CHECKPOINT_MVP_RUNTIME_STABILIZATION.md`
- `docs/EVENT_PRESENTATION_AUDIT.md`
- `docs/ROLE_ACTION_REGISTRY_V1.yaml`
- `docs/ROLE_ACTION_REGISTRY_V1_README.md`
- `app/routes/dev.py`
- `app/routes/delegation.py`
- `app/services/master_state_service.py`
- `app/templates/master_screen.html`
- `app/templates/tv_mode_tv_state.html`
- `app/templates/tv_screen.html`
- `app/templates/player_room.html`
- `scripts/smoke_last_whisper_quiet_support.py`
- `scripts/smoke_last_whisper_crown_tax.py`
- `scripts/smoke_last_whisper_break_alliance.py`
- `scripts/smoke_recent_events_contract.py`
- `scripts/smoke_player_duel_lifecycle.py`
- `scripts/smoke_assignment_reward_loop.py`
- `scripts/smoke_treasurer_resource_deal.py`
- `scripts/smoke_expedition_lifecycle.py`
- `scripts/smoke_court_lifecycle.py`

## Production-Relevant Screens

| Surface | Live URL pattern | Template | Purpose | Validation status |
|---|---|---|---|---|
| Master operator screen | `/dev/master-screen/{room_code}` | `app/templates/master_screen.html` | Host controls, scene state, Court controls, Last Whisper, event feed | command-state covered, browser visibility still open |
| TV room screen | `/dev/tv-mode/{room_code}` | `app/templates/tv_mode_tv_state.html` | Public room display, current scene, rankings, deals, events | state contract covered, room-visible prominence still open |
| Player room | `/house/{invite_code}/player/{player_id}` | `app/templates/player_room.html` | Role actions, assignments, duels, deals, expeditions, Last Whisper controls | command-route covered, browser/mobile clarity still open |
| Lord dashboard / onboarding | house invite dashboard routes in `app/routes/delegation.py` | `app/templates/lord_dashboard.html` | House lobby, invite distribution, role assignment | must be visually checked for live onboarding |
| Master/TV JSON state | `/dev/game-master/{room_code}/state`, `/dev/game-master/{room_code}/tv-state` | service-derived JSON | Source for Master/TV screens and smoke scripts | covered by command smokes, not a visual surface |

## Legacy / Avoid Surfaces

| Surface | Reason to avoid for live |
|---|---|
| `/dev/tv-screen/{room_code}` / `app/templates/tv_screen.html` | Older TV template. It still contains legacy mojibake in visible strings, including the HTML title. Use only as a fallback/debug page, not as the production TV screen. |
| Raw JSON state endpoints | Useful for smoke and diagnostics, but they do not prove CSS visibility, readable layout, or room-visible event prominence. |
| Unscoped dev/operator endpoints | Some dev routes mutate runtime state and are not intended as operator-facing live controls unless explicitly named in the runbook. |

## Current Visual State

### Master

Master screen is the strongest operator surface. It has dedicated scene rendering for Last Whisper, Court, Final, host rounds, duels, diplomacy, and scenario director controls.

Important observation: `master_screen.html` renders `event_feed`, while `master_state_service.py` now also exposes `recent_events`. Browser validation should confirm whether the host can see critical consequences in the actual screen without opening raw JSON.

### TV

`tv_mode_tv_state.html` is the production TV candidate. It fetches `/dev/game-master/{room_code}/tv-state` and renders:

- scene-specific activity;
- leader/resources panels;
- deals feed;
- `eventsFeed` from `data.events`, `data.recent_events`, or `data.tv_summary.recent_events`;
- Court activity when Court runtime is active.

Important observation: the backend now exposes `recent_events`, and this template already consumes it. The remaining risk is visual prominence, not data availability.

### Player

`player_room.html` is the production player surface. It renders Last Whisper information, role-gated Last Whisper controls, duel controls, deal controls, expedition controls, assignment answer flow, and player-facing feedback.

Important observation: command smokes prove the routes, but browser validation must verify that controls are only visible to the right role and that resulting feedback is understandable on a real device.

## Event Visual Checklist

| Event contour | Master should visibly show | TV should visibly show | Player should visibly show |
|---|---|---|---|
| Last Whisper: `quiet_support` | House/action log and `+1 influence` consequence | readable event text in Last Whisper and/or recent events | Whisper Master sees action used; target/other players see info-state if refreshed |
| Last Whisper: `crown_tax` | honest success/tie/zero-delta text | same readable Russian event text | Whisper Master sees action used and repeat blocked |
| Last Whisper: `break_alliance` | selected alliance broken, event text, active alliance removed | broken alliance event and no stale active alliance | Whisper Master sees action used; alliance selector disappears/updates after action |
| Duel resolved/refused | duel status and host resolution result | duel result/refusal visible as room event | Lord/Lady sees challenge/accept/refuse status; regular players do not get control surface |
| Assignment reward | active question/result and House influence/resource change | question/result or standings reflect reward | answering player sees correctness and payoff, including `+1 influence` where applicable |
| Treasurer resource deal | deal status and resource transfer | deal event/resource movement visible or inferable | Treasurer sees confirmation result and cannot double-confirm |
| Expedition resolved | expedition status/result/reward | map/expedition event or recent activity visible | expedition party sees completed result and repeat completion blocked |
| Court finished | `court_finished`, final Court state, no stale active pair | Court finished/result scene | players should not see stale unanswered Court prompts |
| `recent_events` contract | important consequences visible without JSON inspection | high-value events visible in `eventsFeed` | not necessarily global, but player-specific feedback must remain clear |

## Automatable Browser Checks Later

These can be automated with browser tooling after the manual audit path is stable:

1. Open `/dev/master-screen/LIVE01`, `/dev/tv-mode/LIVE01`, and at least one `/house/{invite_code}/player/{player_id}` URL.
2. Trigger existing smoke paths or their setup helpers.
3. Assert expected Russian event text appears in the DOM.
4. Assert event text does not contain replacement characters like `U+FFFD` or obvious mojibake fragments.
5. Assert important blocks are not hidden by CSS (`display: none`, zero size, off-screen placement).
6. Capture screenshots after each major event for operator review.
7. Verify state calls are read-only by comparing scenario/current phase before and after browser refreshes.

## Human Visual Review Required

These are judgment calls and should not be replaced by JSON checks:

- TV event text is readable from room distance.
- Master screen makes the next operator action obvious under time pressure.
- Player controls are understandable on the intended phone/tablet size.
- Last Whisper and Court scenes feel like live moments, not hidden admin state.
- The operator can tell which screen is correct without choosing a legacy route by accident.
- Onboarding/Lord dashboard links and QR flow are usable for real players.

## Minimal Visual Validation Script Before Live

Use this as the pre-game manual/browser validation script:

1. Start trusted no-reload runtime on `http://127.0.0.1:8000`.
2. Reset/prepare `LIVE01` with the current V1 scenario and seeded Houses.
3. Open Master at `http://127.0.0.1:8000/dev/master-screen/LIVE01`.
4. Open TV at `http://127.0.0.1:8000/dev/tv-mode/LIVE01`.
5. Open player rooms through real invite/player URLs from the seeded game, including at least Lord/Lady, Treasurer, Master Whisper, and a regular role.
6. Run or reproduce these contours one by one:
   - Last Whisper `quiet_support`;
   - Last Whisper `crown_tax`;
   - Last Whisper `break_alliance`;
   - duel challenge/accept/refuse/resolve;
   - assignment answer reward;
   - treasurer deal confirmation;
   - expedition resolve;
   - Court lifecycle to `court_finished`.
7. After each contour, visually confirm Master, TV, and relevant player pages show the consequence without inspecting JSON.
8. Take screenshots of Master and TV after each major event.
9. Stop before Final/Terminal unless a separate Final/Terminal validation pass is explicitly running.

## No-Go Visual Risks

Do not proceed to public live game if any of these are true:

- Operator or room is using `/dev/tv-screen/{room_code}` instead of `/dev/tv-mode/{room_code}`.
- A stabilized gameplay consequence appears in JSON but not on Master/TV DOM.
- Last Whisper event text is unreadable, mojibake, or too small/hidden on TV.
- `recent_events` exists in state but is not visibly rendered on TV.
- Master shows stale Court pair/question after Court is finished.
- Player screen exposes action controls to the wrong role.
- Player completes an action but sees no understandable feedback.
- Assignment reward changes influence but player/room cannot understand the payoff.
- Duel/Court/Last Whisper scenes are not legible from the intended live distance.
- Onboarding/Lord dashboard cannot reliably get players to their room.

## Recommended Next Step

Recommended next contour:

```text
Browser-visible validation pass for Master/TV/player surfaces
```

Keep it validation-first. Do not add new mechanics during that pass.

Suggested implementation order:

1. Manual browser validation using the script above.
2. Capture screenshots and note no-go findings.
3. If the screens are visually weak but state is correct, do a template-only polish patch.
4. After the manual pass is stable, add browser automation for DOM text and screenshot checks.

## Audit Judgment

The backend state contract is ready enough for visual validation.

The production risk is now mostly screen selection and visual trust: the room must open the correct TV surface, the host must see consequences without digging, and players must receive role-specific feedback that matches the runtime truth.
