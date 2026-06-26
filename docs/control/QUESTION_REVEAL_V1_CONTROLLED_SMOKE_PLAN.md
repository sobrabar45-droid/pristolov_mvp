# Question Reveal V1 Controlled Smoke Plan

## 1) Purpose

Question Reveal V1 introduced a staged host-round flow:

- question-only stage,
- options + timer stage,
- explicit answer reveal stage.

This plan defines a controlled smoke test before using the change in `LIVE01`.

## 2) Why TEST_ROOM_SETUP is used

Use `TEST_ROOM_SETUP` because it already exists in production DB, has `season1_mvp_live_v2` applied, and operational screens previously returned `200`.

Do not run this smoke first on `LIVE01`.

## 3) Preconditions

- VPS is on commit `f40059c` or newer.
- `TEST_ROOM_SETUP` exists.
- Scenario `season1_mvp_live_v2` is applied.
- Master screen opens for `TEST_ROOM_SETUP`.
- TV screen opens for `TEST_ROOM_SETUP`.
- At least one test House/player may be needed so assignments can be issued and player behavior can be verified.
- Admin token is available to operator, but must not be printed in logs or docs.

## 4) Smoke Sequence

1. Open Master:
   - `/dev/master-screen/TEST_ROOM_SETUP`

2. Open TV:
   - `/dev/tv-mode/TEST_ROOM_SETUP`

3. Prepare test participant if needed:
   - create/register one test House through `/delegation/start?game_code=TEST_ROOM_SETUP&entry_mode=random`;
   - create or join one test player with the role needed by the selected host-round question;
   - do not touch `LIVE01`.

4. Start or select a host-round question sequence:
   - use Master UI, or
   - `POST /dev/host-rounds/start-series/TEST_ROOM_SETUP/{round_code}` if needed.

5. Open question:
   - Master action: `Открыть вопрос`;
   - endpoint: `POST /dev/host-rounds/{host_round_id}/open-next-question`.

6. Verify question-only state:
   - runtime question exists;
   - `answers_open=false`;
   - TV shows question text only;
   - TV does not show options;
   - TV timer is not running;
   - player screen shows question/waiting state, not answer buttons;
   - player/TV payloads do not expose `correct_answer`.

7. Open options and timer:
   - Master action: `Показать варианты / начать ответы`;
   - endpoint: `POST /dev/host-rounds/{host_round_id}/open-answers`.

8. Verify options+timer state:
   - `answers_open=true`;
   - `started_at` is set;
   - TV shows answer options;
   - TV timer starts from `started_at`;
   - player screen shows answer options/buttons;
   - player can submit answer;
   - `correct_answer` is still absent from active player/TV payloads.

9. Close/reveal:
   - Master action: `Закрыть вопрос`;
   - endpoint: `POST /dev/host-rounds/{host_round_id}/force-close-question`.

10. Verify reveal state:
   - runtime question status is no longer `active`;
   - `answers_open=false`;
   - TV shows correct answer;
   - options may show with the correct option highlighted;
   - player result can show accepted/correctness feedback according to existing rules;
   - no scoring/balance behavior changed.

## 5) Exact Endpoints / Actions to Verify

- `GET /dev/master-screen/TEST_ROOM_SETUP`
- `GET /dev/tv-mode/TEST_ROOM_SETUP`
- `GET /dev/game-master/TEST_ROOM_SETUP/state`
- `GET /dev/game-master/TEST_ROOM_SETUP/tv-state`
- `GET /dev/host-rounds/{host_round_id}/debug`
- `POST /dev/host-rounds/{host_round_id}/open-next-question`
- `POST /dev/host-rounds/{host_round_id}/open-answers`
- `POST /dev/host-rounds/{host_round_id}/force-close-question`
- `GET /player/me/{player_token}/assignments`

## 6) Expected State by Stage

| Stage | Runtime state | TV | Player |
| --- | --- | --- | --- |
| Before question | no active runtime question | waiting card | no assignment |
| Question only | `status=active`, `answers_open=false` | question text only, no timer | waiting text, no answer buttons |
| Options + timer | `status=active`, `answers_open=true`, `started_at=set` | question + options + timer | answer buttons visible |
| Reveal | `status=resolved/closed`, `answers_open=false` | correct answer visible | result/closed state |

## 7) What Must NOT Happen

- `correct_answer` must not appear in player assignments before reveal.
- `correct_answer` must not appear in TV active-question payload before reveal.
- Options must not appear before `open-answers`.
- Timer must not run before `open-answers`.
- Smoke must not create, reset, or mutate `LIVE01`.
- Smoke must not change scenario JSON, DB schema, nginx/systemd, or production config.

## 8) Rollback / Cleanup Note

- `TEST_ROOM_SETUP` may remain as a reusable test room.
- If the smoke creates a temporary test House/player in `TEST_ROOM_SETUP`, document it after smoke.
- Do not clean up by broad reset unless explicitly approved.
- Do not touch `LIVE01`.

## 9) Recommendation for Next Action

Run this controlled smoke in `TEST_ROOM_SETUP` first.

If green:

- document result;
- deploy/roll out Question Reveal V1 to production live flow if not already deployed;
- run final visual acceptance on Master/TV/player.

If not green:

- fix blocker in the smallest possible patch;
- rerun this smoke before touching `LIVE01`.

