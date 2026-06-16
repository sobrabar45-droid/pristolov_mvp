# Last Whisper / Master of Whisper smoke protocol (pre-live)

## Preconditions

- Use a real pre-live test session with known `room_code`.
- Confirm at least 3 Houses are present (or document if not available and adjust checks).
- Confirm exactly one verified `whisper_master` player and role token for that player.
- Confirm at least one active alliance exists if `break_alliance` will be exercised.
- Confirm there is a current influence leader (or document clearly no-leader state for `crown_tax` smoke).
- Confirm `/player/last-whisper/action/{player_id}` path is reachable in the test environment.

## Phase activation smoke

1. Open player room for the `whisper_master` and call update state.
- Confirm `active_phase_types` contains `last_whisper`.
- Confirm `lastWhisperSection` is visible.
- Confirm info text mentions one move and late-phase window.
2. For a non-Whisper role in same room:
- Confirm `lastWhisperSection` is not actionable:
  - `viewerCanAct = false`
  - no active action buttons shown
- Confirm informational state is visible instead.

## Action smoke

### `quiet_support`
- In active `last_whisper`, pick another house (not self) and submit.
- Verify API response `ok=true`.
- Verify target house influence increases by `+1`.
- Verify `last_whisper.latest_event`/recent event text appears with action label and target house.
- Verify player result message is understandable.

### `break_alliance`
- In active phase, with at least one active alliance:
  - select one active alliance.
  - submit `break_alliance`.
- Verify response `ok=true`.
- Verify selected deal moves from `alliance_active` to `alliance_broken`.
- Verify one action event is recorded in phase payload/last-whisper feed.

### `crown_tax`
- Ensure there is unique clear influence leader (single leader).
- Submit `crown_tax`.
- Verify response `ok=true`.
- Verify leader influence decreases by `-1`.
- If no leader exists, verify response contains clear explanation and no misleading success claim.

## Blocking smoke

- Outside `last_whisper` phase:
  - submit any Whisper action and expect `ok=false` with phase-related block message.
- Non-whisper role:
  - confirm submit endpoint or UI cannot perform action (`ok=false` / no buttons).
- Repeat action:
  - submit same Whisper action again from same house and expect `ok=false` with “already acted” behavior.
- `quiet_support` invalid target:
  - same house / no target selection -> expect clear blocking message.
- `break_alliance` without active alliance:
  - expect `ok=false` and message that active alliance is required / no valid deal.
- `crown_tax` no valid leader:
  - expect no-op / explanatory message and no hidden fail that appears as success.

## Visibility smoke

- On Master screen (TV/Master feed source), confirm Whisper action appears in recent events.
- On TV mode feed, confirm action appears with readable `tv_text`.
- On player room:
  - whisper player sees action result in whisper feed/result box
  - result message is understandable and not ambiguous.

## Go / No-go

Green (GO):
- `last_whisper` phase opens correctly.
- Whisper panel and controls render only for `whisper_master`.
- At least one valid action path works with correct state changes.
- Blocked states return clear player messages.
- Event surfaces (Master + TV) show one clear readable action record.

Yellow (GO WITH WATCH):
- One action missing due to session preconditions (for example, no active alliance for break_alliance).
- Minor/expected no-op messages for `crown_tax` when leader missing or no effective influence change.
- Small rendering delay requiring refresh.

Red (NO GO):
- Any action applies without phase role checks.
- Non-whisper player can execute Whisper action.
- Repeat action succeeds when it should be blocked.
- Critical event text not visible on Master/TV feeds.
- Response/UI mismatch causes ambiguity for no-op results.

## Cleanup / test restore

- If a non-destructive test action was used, record tested house/players in notes.
- If disruptive state was accidentally changed, restore test game state via game admin reset tooling or duplicate a clean practice room before live.
- Re-run key state checks after cleanup.

