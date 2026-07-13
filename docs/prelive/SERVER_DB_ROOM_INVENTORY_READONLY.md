# PRISTOLOV_CORE: server DB and room inventory (read-only)

## 1. Executive summary

Verdict: `SERVER_DB_INVENTORY_PASS_PRELIVE_POSSIBLE_WITH_EXPLICIT_PLAN`.

The server inventory is sufficient to plan a controlled pre-live setup, but it does not authorize setup or import.

- `LIVE01` exists and remains forbidden.
- `TEST_ROOM_SETUP` exists and may be considered as a non-LIVE candidate only after explicit review of its current state.
- `QUESTION_DRYRUN_02` does not exist on the server.
- Question Bank V2 questions are not loaded on the server.
- A controlled server import/setup requires a separate explicit plan and approval.

## 2. Server context and method

- Server: `root@5.42.119.94`
- Application path: `/opt/pristolov/app`
- Server HEAD: `be04f4c`
- Branch: `main`
- Service: `pristolov.service`, previously confirmed active.
- DB environment source: `/etc/pristolov/pristolov.env`.
- Python: `/opt/pristolov/venv/bin/python`.
- Inventory method: read-only SQLAlchemy `SELECT` queries over the server DB.
- Secrets and environment values were not printed.

## 3. Tables and code columns discovered

Tables observed:

- `game_assignments`
- `game_deals`
- `game_duels`
- `game_expedition_members`
- `game_expeditions`
- `game_host_round_questions`
- `game_host_rounds`
- `game_house_towers`
- `game_map_states`
- `game_map_visits`
- `game_phases`
- `game_scenario_templates`
- `game_template_acts`
- `game_template_houses`
- `game_template_map_nodes`
- `game_template_roles`
- `game_template_task_pools`
- `game_template_tasks`
- `game_templates`
- `games`
- `house_gold_transactions`
- `houses`
- `players`
- `roles`
- `round_question_templates`
- `round_templates`

Code-bearing columns found:

- `game_host_rounds.round_code`
- `game_scenario_templates.code`
- `game_template_roles.code`
- `games.room_code`
- `roles.code`
- `round_templates.import_key`
- `round_templates.round_code`

The inventory did not find `game_rooms` or `game_sessions` tables.

## 4. Room inventory

- `LIVE01` exists in `games.room_code`, ID `1`.
- `TEST_ROOM_SETUP` exists in `games.room_code`, ID `2`.
- No room was created, deleted, renamed, or otherwise mutated.

`TEST_ROOM_SETUP` is the only obvious dedicated non-LIVE candidate identified by this inventory. Its existing players, houses, rounds, assignments, and current state must be reviewed again immediately before any rehearsal setup.

## 5. Question template inventory

- `round_templates` count: `12`.
- Sample/highest IDs include:
  - `12 stage_court_battle`
  - `11 stage_final_show`
  - `10 stage_last_whisper`
  - `9 stage_court`
  - `8 stage_duels`
  - `7 stage_free_play`
  - `6 stage_diplomacy_1`
  - `5 stage_map_entry`
  - `4 stage_four_options`
  - `3 stage_truth_lie_opening`
  - `2 stage_intro`
  - `1 act1_truth_lie_01`

Question Bank V2 checks:

- `QUESTION_DRYRUN_02` was not found in the server code-value search.
- `ROUND_TEMPLATE_QUESTION_DRYRUN_02_COUNT 0`.
- `QUESTION_COUNT_FOR_DRYRUN_02_COUNT 0`.
- The server does not contain the locally imported Question Bank V2 round.

## 6. Runtime inventory

- `game_host_rounds`: `8`
- `game_host_round_questions`: `26`
- `game_assignments`: `51`
- `houses`: `5`
- `players`: `25`

These counts describe existing server state only. They are not a readiness approval and were not changed by this audit.

## 7. Implications

- Deploying or updating code alone will not load the local Question Bank V2 questions into the server DB.
- If the server rehearsal uses Question Bank V2, a separate controlled server import is still required.
- `TEST_ROOM_SETUP` exists, but it is real server DB state and must not be assumed empty or disposable.
- `LIVE01` exists and must not be used for rehearsal, import, smoke, or setup.
- Any future setup must define the target room, backup/checkpoint decision, exact candidate artifact, dry-run parameters, and rollback/stop conditions before mutation.

## 8. Recommendation

Recommended next step:

- Prepare a controlled server pre-live setup/import plan only after explicit approval; or
- Keep tonight's rehearsal local and postpone server setup.

Do not run the server import based on this inventory alone.

## 9. Safety confirmation

- No import was run.
- No DB mutation occurred.
- No `LIVE01` mutation or access occurred.
- No deploy, pull, push, restart, or migration occurred.
- No server file was edited.
- No room was created or deleted.
- No media was copied.
- No secrets or tokens were printed.
