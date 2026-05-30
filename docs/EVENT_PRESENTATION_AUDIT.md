# Event Presentation Audit

Project: `D:\Projects\pristolov_mvp`  
Date: 2026-05-31  
Scope: Master/TV presentation of gameplay events after Master Whisper V1.

## Purpose

Master Whisper V1 is mechanically complete:

- `quiet_support`
- `crown_tax`
- `break_alliance`

This audit checks whether important runtime consequences are visible to the host and to the room, and identifies the smallest safe polish patch before adding new mechanics.

## Current Event Sources

| Source | Backend contract | Stored in | Current visual surfaces |
|---|---|---|---|
| Last Whisper actions | `last_whisper.events`, `last_whisper.latest_event` | active `GamePhase.payload["whisper_actions"]` | Master Last Whisper scene, TV Last Whisper scene |
| Active alliances | `alliances` | `GameDeal` where `status == "alliance_active"` and `offer.type == "alliance"` | Master deal/alliance state, TV diplomacy activity |
| Broken alliances | `broken_alliances_recent` | `GameDeal` where `status in {"alliance_broken", "alliance_betrayed"}` | TV diplomacy activity, raw Master state |
| Deals | Master `deals`; TV `deals.pending/countered/recent_closed` | `GameDeal` | Master deals list, TV diplomacy feed |
| Duels | `duels` block | `GameDuel` | Master duels list/operator panel, TV activity/feeds depending scene |
| Expeditions/map outcomes | `expeditions`, `map_events.public_recent` | `GameExpedition`, `GameMapVisit` | TV map/expedition activity, Master event feed partially |
| Host round questions | `active_host_round`, `current_question` | host round/runtime question models | Master runtime panel, TV question scene |
| Master event feed | `event_feed` | derived in `master_state_service.py` | Master sidebar only |

## Master Visibility Table

| Event type | Exposed to Master? | Visually emphasized? | Current path | Notes |
|---|---:|---:|---|---|
| Last Whisper latest event | yes | medium | `renderLastWhisperScene()` reads `state.last_whisper.events/latest_event` | Visible only inside Last Whisper scene. Not included in general Master `event_feed`. |
| Quiet Support influence gain | yes | medium | Last Whisper event log | Text appears; resource delta is not promoted outside the scene. |
| Crown Tax influence loss/tie | yes | medium | Last Whisper event log | Text appears; no global alert. |
| Break Alliance | yes | medium | Last Whisper event log; `broken_alliances_recent` in state | Master state has broken alliances, but Master UI does not give them a clear global event card. |
| Active deals | yes | low/medium | `renderDeals()` and `event_feed` | Deals list exists; offer rendering is basic. |
| Deal accepted/rejected/cancelled | partial | low | `deals` list | Master `event_feed` focuses pending/countered deals and does not strongly announce closed deals. |
| Duels | yes | high | duel operator panel, `renderDuels()`, `event_feed` | Duel challenge/resolution is one of the stronger Master surfaces. |
| Gold/resource transfer | partial | low | deals/resources state | Resource consequences are visible indirectly through house resources, not as a strong event. |
| Expedition results | yes | medium | `event_feed`, expedition blocks | Exists, but not a shared event language with diplomacy/Whisper. |
| Court/Final | yes | high | separate dedicated scenes/panels | Out of scope for this polish. |

## TV Visibility Table

| Event type | Exposed to TV? | Visually emphasized? | Current path | Notes |
|---|---:|---:|---|---|
| Last Whisper latest event | yes | high during Last Whisper scene | `renderLastWhisperActivity()` reads `state.last_whisper.latest_event.tv_text` | Good scene-level visibility while the scene is active. |
| Quiet Support | yes | high only during Last Whisper scene | latest event text | Not shown in the general recent-events feed. |
| Crown Tax | yes | high only during Last Whisper scene | latest event text | Not shown in the general recent-events feed. |
| Break Alliance | yes | high during Last Whisper scene; medium in diplomacy activity | latest event text + `broken_alliances_recent` | It can disappear from focus after scene changes unless diplomacy activity is on screen. |
| Active alliances | yes | medium | `renderDiplomacyActivity()` | Uses alliance block. |
| Broken alliances | yes | medium | `renderDiplomacyActivity()` | Uses `broken_alliances_recent`; good but not unified with event feed. |
| Deals | yes | medium | `dealsFeed`, `renderDiplomacyActivity()` | Pending/countered are visible; closed deals are fallback only. |
| Duels | yes | medium/high | activity layer and feed blocks | Depends on active scene/slide. |
| Gold/resource consequences | partial | low | resource rankings and house cards | No "resource changed" event feed on TV. |
| Map/expedition events | yes | medium | `map_events.public_recent`, expedition activity | State exists; visual emphasis depends on active slide/scene. |

## Gaps

1. There is no single shared room-facing event feed.
2. Master has `event_feed`, but TV state does not expose the same `event_feed`.
3. Last Whisper events are not added to Master `event_feed`.
4. TV feed code checks `data.events`, `data.recent_events`, or `data.tv_summary.recent_events`, but current TV state does not provide those fields.
5. `last_whisper.latest_event` is visible during Last Whisper, but it is not durable as a global recent event after the scene changes.
6. Broken alliances are visible through `broken_alliances_recent`, but only in diplomacy-specific activity rendering.
7. Gold/resource changes are mostly visible as changed numbers, not as explicit event stories.
8. Some older TV text in `tv_screen.html` still contains legacy encoding noise, so polish should target `tv_mode_tv_state.html` first.

## Recommended Smallest Patch

Use the existing state contracts and add a small derived `recent_events` list in `master_state_service.py` for TV and Master presentation.

Recommended contents for `recent_events`:

1. Latest Last Whisper event, if present:
   - `type = "last_whisper"`
   - `title = action_label`
   - `text = tv_text`
   - `severity = "high"`
2. Recent broken alliances:
   - `type = "alliance_broken"`
   - `title = "Alliance broken"`
   - `text = break_text`
   - `severity = "high"`
3. Recent duel challenge/resolution/refusal:
   - reuse existing Master `event_feed` duel texts
4. Recent closed diplomacy deals:
   - use `offer_text`, from/to houses, and status

Template polish:

- TV: make `eventsFeed` read `data.recent_events` and show Last Whisper/broken alliance events before closed deals.
- TV: add a "major" visual class for `severity == "high"`.
- Master: prepend Last Whisper and broken alliance events to existing `event_feed`, or display a compact "Important events" block using the same `recent_events`.

This is a small state-contract addition plus template consumption. It does not require new models, new tables, or a new event system.

## Template-Only Option

A template-only patch is possible but weaker:

- TV could synthesize local items from `last_whisper.latest_event` and `broken_alliances_recent`.
- Master could visually lift `last_whisper.latest_event` inside `renderLastWhisperScene()`.

This avoids backend changes but duplicates event-building logic in JS and does not solve the shared-event-feed gap. The safer long-term small patch is a derived backend `recent_events` list.

## Proposed Verification

Command-level checks:

- Extend or add a focused presentation smoke that calls `/dev/game-master/LIVE01/state` and `/dev/game-master/LIVE01/tv-state` after each Last Whisper action.
- Assert `last_whisper.latest_event.tv_text` remains readable Russian.
- If `recent_events` is added, assert Master and TV expose matching top event text.
- For `break_alliance`, assert `recent_events[0]` or a high-priority item contains the break text and `broken_alliances_recent` still contains the deal.

Browser/UI checks:

- Open Master screen during Last Whisper after each action and confirm an obvious event card/log line is visible.
- Open TV mode during Last Whisper and confirm the latest event is room-visible.
- After leaving Last Whisper, confirm the latest major event is still present in a recent-events area or ticker.

Recommended commands after a future polish patch:

```powershell
python -m py_compile app/services/master_state_service.py
python scripts/smoke_last_whisper_quiet_support.py
python scripts/smoke_last_whisper_crown_tax.py
python scripts/smoke_last_whisper_break_alliance.py
```

## Risks

- Adding a backend `recent_events` list is low risk because it can be derived read-only from existing state.
- Duplicating event synthesis in templates is riskier over time because Master and TV can drift.
- Browser-visible verification is still needed because current smoke confirms state contracts, not on-screen prominence.
- Old `tv_screen.html` contains encoding noise; polish should avoid broad cleanup unless explicitly scoped.
- Resource/gold event polish can quickly become economy design if not kept to display-only derived messages.
