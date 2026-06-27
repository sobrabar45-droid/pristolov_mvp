# Duel Draw Handling Checkpoint

Date: 2026-06-27
Scope: docs-only checkpoint after completed runtime patch.

## Commit recorded

- `ddb9c66` Add Duel draw handling

## Completed behavior

The Duel V1.1 draw/replay patch is implemented locally at HEAD.

Implemented behavior:

- Added duel status `needs_replay` using existing `GameDuel.status` string storage.
- Added Master action/button: `Ничья / переигровка`.
- Added dev/operator route: `POST /dev/games/{room_code}/duels/{duel_id}/draw`.
- Draw/replay state applies no winner reward, no loser penalty, and no gold transfer.
- `winner_house_id` remains empty when draw is marked.
- Winner resolution from `needs_replay` remains allowed after replay or host tie-break.
- Duplicate active same-pair/reverse-pair challenge guard includes `needs_replay`.
- Master, TV, and player room show readable replay-needed status.

## Verification already known

Bootstrap Sync Report after `ddb9c66` confirmed:

- Local repository was clean before this docs checkpoint.
- Local HEAD was `ddb9c66 Add Duel draw handling`.
- Expected latest P0 code markers were present:
  - `stage_briefing`;
  - Expedition copy guidance;
  - `open-answers`;
  - `answers_open=False`;
  - correct answer stripping before reveal;
  - TV timer 20 second clamp/default;
  - Duel `needs_replay`;
  - `/dev/games/{room_code}/duels/{duel_id}/draw`.

## Not yet verified

Still pending:

- Mutating controlled Duel smoke in `TEST_ROOM_SETUP`.
- Production HEAD/deployment status for `537670e` and `ddb9c66`.
- Manual visual smoke for Question Reveal 20 second timer.
- Manual visual smoke for Duel draw/replay flow.

## Required next task

Run bundled controlled smoke in `TEST_ROOM_SETUP` only.

Smoke bundle:

1. Stage briefing renders on Master/TV.
2. Expedition copy renders for assigned, non-assigned, and Lord/Lady states.
3. Question Reveal:
   - open question;
   - options hidden;
   - open answers;
   - timer is about 20 seconds;
   - correct answer remains hidden until reveal.
4. Duel:
   - create/accept duel if practical;
   - mark `Ничья / переигровка`;
   - verify no reward/penalty;
   - optionally resolve winner after replay/tie-break.

## Hard constraints for next task

- Do not touch LIVE01.
- Do not mutate production without explicit command.
- Do not change runtime code.
- Do not change DB schema.
- Do not change scenario JSON.
- Do not run `git pull`.
- Do not restart services.
- Do not run migrations.
- Do not run production smoke without explicit user command.

## Runtime untouched confirmation

This checkpoint is documentation only. It does not change runtime code, templates, DB schema, scenario JSON, production config, or LIVE01 state.
