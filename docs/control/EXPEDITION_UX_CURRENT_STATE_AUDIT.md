# Expedition UX Current State Audit (PRISTOLOV)

## 1) Executive summary

Expedition is already implemented end-to-end in V1 and is functionally usable:
- Lord / Lady creates and configures expedition,
- participants are assigned and can vote location,
- Lord / Lady approves and resolves when all assigned players have voted,
- resolved outcomes are propagated to player, Master, TV, and events.

The main reliability concern reported in rehearsal is mixed: part of the confusion was UX clarity, but a large part also came from technical instability/disconnections during heavy player load.

Current recommendation: **small copy/clarity patch first**, not a full redesign.

## 2) Current Expedition flow as implemented

Flow is implemented in `app/routes/player.py` and `app/services/expedition_service.py`:

1. Lord / Lady starts expedition.
2. Participants are selected by role and assigned count.
3. Participants and potentially other invited roles choose destination card/location.
4. Votes are collected; when everyone assigned votes, Lord / Lady resolves.
5. Result payload is calculated and applied to game state, then surfaced as narrative in feeds.

## 3) Lord/Lady screen behavior

- Start endpoint: `POST /player/expedition/create/{player_id}` accepts:
  - `members_count`
  - optional `role_codes` filter.
- Lord / Lady can approve via existing approval action.
- Lord / Lady sees house-level expedition state in player payload:
  - `active_house_expedition`,
  - buttons for create / assign / approve / resolve.
- Resolution requires:
  - expedition status valid for resolve,
  - all assigned players voted.

## 4) Assigned player behavior

- Assigned participants are shown destination-choice controls while expedition is active.
- They can pick allowed locations shown by role filter/permissions.
- If they have no action at the moment, UI shows waiting states according to expedition phase.

## 5) Non-assigned player behavior

- Non-assigned players are not offered destination controls.
- They see neutral house waiting copy (e.g. “Дом готовит экспедицию. Ожидайте своего хода.”), and continue with other role actions.
- No direct expedition voting is shown for them unless they are part of the expedition.

## 6) Completion / result behavior

- Resolve endpoint: `POST /player/expedition/{expedition_id}/resolve/{player_id}`.
- Resolution is allowed only when the vote set is complete.
- Current result branches are surfaced as narrative:
  - “Экспедиция успешна” (success path),
  - “Экспедиция сорвалась” (failure path),
  - plus contextual reasons and reward/penalty text in player and Master/TV state.

Observed result text includes:
- “Экспедиция готова к утверждению”
- “Экспедиция утверждена”
- “Экспедиция разошлась...”
- “Экспедиция завершена”

## 7) Existing narrative/result text

- Player view uses short event-like text (success/failure framing).
- Master/TV state contains expedition lifecycle labels (`собирает состав`, `в пути`, `Экспедиция успешна`, `Экспедиция сорвалась`).
- TV displays resolved consequences in compact narrative form.
- Event feed is present and does not expose internal math.

## 8) Hidden formula exposure check

Checked user-facing templates and service-facing texts for explicit formula disclosure.

No player-facing phrasing exposing the hidden calculation internals was found in current Expedition messages.

Note: internal outcome helpers in service layer do include debug-oriented metadata, but this is backend/internal and is currently not directly presented as rules text.

## 9) Repetition support check

- Expedition creation is restricted per house-phase (`can create only one per house per phase` in service logic).
- Multiple expeditions are therefore supported across different phases (e.g. map / free_play waves), not unlimited in same phase per house.

## 10) Technical failure risks

From architecture and rehearsal notes:
- The largest freeze/stall risk is overall player-screen stability under concurrency (shared with all phone polling paths), not Expedition logic alone.
- Additional observed risk points:
  - unresolved votes and unclear waiting labels when one participant disconnects,
  - approval path depends on lord role action and all votes being present,
  - one-room, one-phase contention can amplify perceived “broken” behavior if any participant drops.
- If transport breaks during assigned flow, house often stays “in progress”, creating player confusion until refresh/stability recovers.

## 11) What is already good enough

- Server-side Expedition mechanics are present and coherent:
  - assignment → voting → approval → resolution.
- Success/failure outcome is visible on both players and shared screens.
- No hard-coded probability text is shown publicly.
- Expedition is integrated into Master/TV summary and event surfaces.
- Repeated expeditions per night are possible over multiple eligible phases.

## 12) What is missing or unclear

- UX messaging is functional but can be clearer for participants during transitions:
  - what to do while waiting,
  - why current phase is stalled before all votes,
  - what each outcome means in practical terms.
- No dedicated “retry/rejoin” helper text shown before full manual operator intervention.
- In high-stress moments, house-level pending state can look like a freeze if one assigned player is absent.
- This is likely a presentation and operational clarity gap, not a complete mechanic rewrite.

## 13) Recommendation

Suggested next control action:

**Small copy patch** in:
- shared waiting states,
- assigned-vote completeness hint,
- resolved outcome explanation (without exposing formula),
- role-appropriate fallback guidance when expedition stalls.

If copy changes do not stabilize understanding, next technical escalation should be a **technical completion patch** for connectivity/refresh and stale-state recovery.

### Minimal next task

- Audit-and-implement minimal Expedition UX copy clarifications with freeze-safe wording and role-specific action states; keep outcome text non-technical and non-formulaic.
