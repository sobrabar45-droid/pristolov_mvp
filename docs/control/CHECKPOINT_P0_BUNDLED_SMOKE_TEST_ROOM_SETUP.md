# Bundled P0 controlled smoke in TEST_ROOM_SETUP checkpoint

Date: 2026-06-27

## Summary

Bundled controlled smoke was run against the local/dev `TEST_ROOM_SETUP` room after the accumulated P0 patches:

- `5a4bf37` Add stage announcement briefing UX
- `bb99450` Improve Expedition copy guidance
- `f40059c` Add staged question reveal flow
- `537670e` Tune question answer timer
- `ddb9c66` Add Duel draw handling
- `a2b77ae` Add Duel draw handling checkpoint

Overall result: `PASS_WITH_ONE_PARTIAL`.

Verified areas:

- Stage Announcement / Round Briefing UX
- Expedition copy guidance
- Question Reveal V1 anti-google behavior and 20 second timer
- Duel draw/replay handling

Partial item:

- Post-close/reveal correct-answer visibility still needs a targeted audit/smoke.

## Preflight

```text
git status --short: clean
recent HEAD: a2b77ae Add Duel draw handling checkpoint
room code: TEST_ROOM_SETUP
```

## Room setup and safety

Smoke environment:

- local/dev DB only;
- drivername: `postgresql`;
- host: `localhost`;
- port: `5432`;
- database: `pristolov_mvp`;
- production was not touched;
- VPS/SSH was not touched;
- `LIVE01` was not touched;
- no migrations were run;
- no runtime files were edited;
- no scenario JSON was edited;
- no production config was changed.

Local setup note:

- `scripts/setup_room_mvp.py` dry-run was safe and showed it would create only `TEST_ROOM_SETUP` and apply `season1_mvp_live_v2`.
- Real helper execution failed locally because the local DB requires `games.status NOT NULL`, while the helper/model insert did not set `status`.
- A local one-off command using existing `SessionLocal`, the schema-inspection pattern from `scripts/smoke_multi_room_isolation.py`, and existing `apply_scenario_to_game_logic` inserted only `TEST_ROOM_SETUP` with `status=active`.

Final local room state:

```text
room_exists=True
game_id=8
scenario_code=season1_mvp_live_v2
scenario_id=7
houses=2
players=2
active_phases=[host_round, duel]
duels=[(22, resolved, winner_house_id=282)]
host_rounds include stage_truth_lie_opening and stage_court_battle
```

Local `TEST_ROOM_SETUP` now contains smoke artifacts and was not cleaned.

## Room availability smoke

Result: `PASS`.

All checked endpoints returned 200 via local TestClient:

```text
/delegation/start?game_code=TEST_ROOM_SETUP&entry_mode=random
/dev/master-screen/TEST_ROOM_SETUP
/dev/game-master/TEST_ROOM_SETUP/state
/dev/tv-mode/TEST_ROOM_SETUP
/dev/game-master/TEST_ROOM_SETUP/tv-state
/cashier/gold-desk/TEST_ROOM_SETUP
/dev/gold-desk/TEST_ROOM_SETUP
/dev/treasurer-shop/TEST_ROOM_SETUP
```

## Stage Announcement result

Result: `PASS`.

Evidence:

```text
master_state contains stage_briefing=true
tv_state contains stage_briefing=true
sound_cue flag present
```

Note: console JSON showed some Cyrillic mojibake, but payload keys and structure were present.

## Expedition copy result

Result: `PASS_STATIC`.

Evidence found in `app/templates/player_room.html`:

```text
Вы назначены в экспедицию
Выберите направление на своём экране. После выбора дождитесь решения Лорда / Леди.
В экспедиции участвуют назначенные игроки.
Сейчас ждём оставшихся участников.
Если игрок не видит выбор направления, попросите его обновить экран или обратиться к ведущему.
```

No direct hidden formula phrases were found in user-facing Expedition copy.

## Question Reveal + timer result

Result: `PASS_PARTIAL`.

Passed:

```text
opened normal host round: stage_truth_lie_opening
open question -> runtime_question.answers_open=false
TV before open answers: reveal_stage=question
TV before open answers: options hidden
TV before open answers: correct_answer hidden
open answers -> answers_open=true
open answers -> started_at set
TV after open answers: reveal_stage=options
TV after open answers: options visible
TV after open answers: correct_answer hidden
TV timer constants: default=20, max=20
```

Partial / follow-up needed:

```text
After force-close/reveal, checked JSON state did not expose correct_answer.
```

Interpretation:

- Anti-google behavior passed.
- Staged options passed.
- 20 second timer passed.
- Post-reveal correct-answer visibility needs targeted audit/smoke.

## Duel draw/replay result

Result: `PASS`.

Sequence completed in `TEST_ROOM_SETUP`:

```text
created duel challenge between two Houses
accepted duel
marked draw/replay
status became needs_replay
reward_applied=false
gold/influence unchanged on draw
duplicate reverse-pair challenge blocked while needs_replay
resolved winner after replay
reward/penalty applied only after winner resolution
Master/TV payloads mention duel state
```

Resource proof:

```text
Before draw:
House 282 gold=11 influence=0
House 283 gold=11 influence=0

After draw:
House 282 gold=11 influence=0
House 283 gold=11 influence=0

After winner resolution:
House 282 gold=11 influence=2
House 283 gold=10 influence=0
```

## Known warnings

- `setup_room_mvp.py` has a local schema/model mismatch: the DB requires `games.status`, but the helper/model insert does not set it.
- Question Reveal post-close correct-answer visibility remains partially unverified.
- Local `TEST_ROOM_SETUP` contains smoke artifacts and was not cleaned.
- No production smoke was run.
- Production HEAD/deployment status for latest commits remains unconfirmed.

## Recommended next task

Targeted audit/smoke for Question Reveal post-close/reveal correct-answer visibility.

Goal:

Confirm whether the correct answer is supposed to be exposed via TV/Master/player state after reveal, and if not, identify whether this is:

- expected UI-only rendering behavior;
- endpoint/state sanitizer behavior;
- missing state field;
- or a real bug.

Constraints for next task:

- audit/smoke first;
- no code changes unless bug is confirmed;
- do not touch `LIVE01`;
- do not touch production;
- prefer local `TEST_ROOM_SETUP`;
- do not reset all local rooms;
- do not change scenario JSON;
- do not change DB schema.
