# Post-rehearsal feedback cleanup and deploy checkpoint

Date: 2026-06-29
Scope: docs-only savepoint after the post-general-rehearsal cleanup block and Harchevnya 18+ production deploy.

## 1. Summary

The post-general-rehearsal feedback cleanup pass is closed enough to move forward.

The project now has a materially stronger V1 foundation across:

- player-screen stability;
- stage clarity;
- Expedition guidance;
- question reveal and anti-google flow;
- Duel draw/replay handling;
- player-facing rules and print materials;
- Harchevnya approved shelf, 18+ unlock, and cashier warning flow;
- production deployment of the latest Harchevnya 18+ runtime patch.

This does not mean all product work is complete. It means the major cleanup pass after rehearsal has a stable checkpoint and the next work should be deliberate: first finish protected production browser smoke if needed, then move to the next meaningful gameplay design contour.

## 2. Current production state

Latest relevant production deployment:

- `origin/main` was pushed to `b3f6ed1 Add Harchevnya 18 rollout readiness report`.
- Production pulled to `b3f6ed1` with fast-forward deploy.
- Compile passed for:
  - `app/routes/player.py`
  - `app/routes/cashier.py`
  - `app/services/master_state_service.py`
- `pristolov.service` was restarted.
- Service status after restart: `active`.
- Startup logs were clean:
  - `Application startup complete`
  - `Uvicorn running on http://127.0.0.1:8000`
- Public `GET /` returned `200`.
- Plain unauthenticated `/dev/...` and `/cashier/...` curl checks returned `403 Forbidden`, consistent with protected access.
- `HEAD /` returned `405 Method Not Allowed`, but `GET /` returned `200`, so this was not treated as service failure.

Production non-actions during the deploy/checkpoint contour:

- `LIVE01` was not touched.
- Migrations were not run.
- DB schema was not changed.
- No production DB mutation smoke was run.
- No mutating Harchevnya production request smoke was run.

Protected routes require proper protected access for meaningful browser smoke.

## 3. Closed feedback items

### Technical stability

Closed or checkpointed:

- Player polling/load stabilization.
- Removal/throttling of excessive polling writes.
- Real player endpoint load probe helper.
- Player endpoint optimization for 100-client target.
- Level 1 combined passive load probe and checkpoint.
- Room setup / loader foundation audit and helper smoke.

### Player clarity

Closed or checkpointed:

- Stage Announcement / Round Briefing UX.
- Player one-page rules audit and V1 draft.
- Physical House/role markers audit and V1 design.
- First print pack for player rules + markers.
- Printable layout source pack.

### Question flow

Closed or checkpointed:

- Question timer/reveal audit.
- Staged Question Reveal V1:
  - question-only stage;
  - options + timer stage;
  - explicit answer reveal stage.
- Answer timer tuned to 20 seconds.
- Master/TV correct-answer visibility after reveal fixed.
- Local controlled smoke/checkpoints for staged reveal.

### Expedition flow

Closed or checkpointed:

- Expedition UX current-state audit.
- Expedition copy and stalled/disconnected guidance.
- Hidden formula remains unrevealed to players.
- Repeated Expedition discovery mechanic preserved.

### Duel flow

Closed or checkpointed:

- Duel / tic-tac-toe current-state audit.
- Duel draw/replay handling.
- `needs_replay` status.
- Master action for draw/replay.
- No reward/penalty on draw.
- Winner resolution after replay preserved.

### Harchevnya / shop flow

Closed or checkpointed:

- Harchevnya / 18+ / availability audit.
- Victor-approved shelf and manual-only replacement policy.
- 18+ unlock UI/copy design.
- Harchevnya 18+ runtime patch:
  - non-18+ default shelf;
  - 18+ items hidden by default;
  - `Показать позиции 18+` unlock;
  - alcohol items marked `18+`;
  - cashier 18+ warning;
  - gold charged only after cashier/bar confirmation;
  - replacement remains manual-only.
- Local mutating smoke in `TEST_ROOM_SETUP`.
- Local visual/browser smoke for player Harchevnya and cashier queue.
- Production deploy readiness report.
- Production deploy checkpoint.

### Print / physical materials

Closed or checkpointed:

- One-page player rules draft.
- Physical House/role markers design.
- Print pack for player rules and markers.
- Printable Markdown layout source pack.

## 4. Remaining tails

### Technical rollout tail

Remaining:

- Production browser smoke with proper protected access is still not done.
- Non-LIVE production room smoke depends on available protected access and/or an approved non-LIVE room.
- No mutating production Harchevnya request smoke has been run.
- Local `TEST_ROOM_SETUP` contains smoke artifacts from previous local tests.
- Protected `/dev/...` and `/cashier/...` routes cannot be meaningfully checked by plain unauthenticated curl.

### Product / gameplay tail

Remaining from general rehearsal feedback and subsequent design discussions:

- Diplomacy still needs a stronger gameplay purpose after Crest/herb removal.
- `Мастер над шёпотом` still needs design for charges / подлянки during the game.
- House identity/perks decision remains open:
  - cosmetic only;
  - or small, controlled bonuses.
- Duel V2 with question-before-move is deferred.
- Inter-House attack/defense layer is deferred.
- Full metaverse/resources return is deferred.
- Harchevnya 18+ legal/staff responsibility remains operational and must not be treated as solved by UI.

## 5. Recommended next step

Recommended order:

1. Run production browser smoke with proper protected access, non-LIVE only.
2. If no safe non-LIVE production room exists, explicitly decide whether to create/prepare one.
3. After protected production smoke is green or intentionally deferred, move to a product design pass for:
   - Diplomacy;
   - `Мастер над шёпотом`.

The next meaningful gameplay breakthrough is likely not another technical cleanup. It is making Diplomacy and `Мастер над шёпотом` feel purposeful, politically sharp, and easy to understand during live play.

## 6. Hard constraints going forward

- Do not touch `LIVE01` without explicit approval.
- Do not mutate production for smoke without explicit approval.
- Do not add new mechanics before the next design pass.
- Do not add automatic Harchevnya replacement/refund/substitution logic.
- Keep 18+ staff/legal confirmation language.
- Keep gold charging after cashier/bar confirmation.
- Maintain checkpoint discipline after runtime changes and production deploys.
- Prefer non-LIVE rooms for production smoke.
- Keep V1 individual player phones as the current product direction unless a separate V2 decision is made.
