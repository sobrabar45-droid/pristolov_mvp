# LIVE01 Question Bank Loading Audit

## Purpose

Before tomorrow's rehearsal, this audit determines how to replace LIVE01 question content safely without mutating runtime state.

## 1) Current question loading source map

- Canonical templates are loaded from:
  - `app/game_templates/scenarios/*.json` (scenario documents, e.g. `season1_mvp_live_v2.json`)
  - template helper files in `app/game_templates/season1_core_v1/*`
- Runtime scenario application is handled by `app/services/scenario_service.py`:
  - `import_scenario_logic(...)`
  - `apply_scenario_to_game_logic(...)`
  - `ensure_scenario_schema(...)`
- Host round runtime questions are created from template questions at runtime open-cycle:
  - `open-next-question` creates `GameHostRoundQuestion` from linked `RoundQuestionTemplate`
- Key tables/models:
  - `RoundQuestionTemplate` (`app/models/round_question_template.py`) — canonical question templates per round
  - `GameHostRoundQuestion` (`app/models/game_host_round_question.py`) — per-game runtime instance questions
  - `GameAssignment` (`app/models/game_assignment.py`) links runtime questions to assigned players

## 2) Are questions stored per game or reloaded every time?

- Scenario/question templates are imported into DB on scenario import.
- `GameHostRoundQuestion` rows are created during play/host-round progression, not reloaded each request directly from JSON.
- Effective flow:
  1. `season1_mvp_live_v2.json` imported into scenario/template tables
  2. Scenario applied to game (`games/{room_code}/scenario/apply`)
  3. For active host rounds, runtime questions are created in `game_host_round_questions`

## 3) DB tables touched by question runtime and reset

- Runtime/runtime-like question state:
  - `game_host_round_questions`
  - `game_assignments` (host-round question assignment references)
- Template bank:
  - `round_question_templates`
- Reset behavior (`/dev/games/{room_code}/reset-runtime`) deletes:
  - `GameAssignment`
  - `GameHostRoundQuestion`
  - host round/phase/expedition/map/deal/duel runtime tables
  - does **not** directly delete scenario template catalog (`round_question_templates`)

## 4) Scenario import paths and endpoints

From `app/routes/dev.py` and related services:
- `POST /scenarios/import` → import scenario JSON (create/replace/merge mode)
- `POST /scenarios/{scenario_code}/import-round` → import one round
- `POST /games/{room_code}/scenario/apply` → bind scenario to LIVE01 runtime
- `POST /questions/import` exists for file-backed imports with round-scoped clear options

## 5) Is reset-runtime enough for questions?

- `reset-runtime` clears selected runtime host questions and assignments, so stale selected questions are removed.
- It does **not** change scenario templates; stale future templates in bank persist unless specifically replaced/imported.

## 6) Does bootstrap/bootstrap scripts touch LIVE01 questions?

- `scripts/bootstrap_live01_vps.py` loads:
  - `SCENARIO_CODE = "season1_mvp_live_v2"`
  - imports scenario file with `import_mode = "merge"`
  - applies scenario to `LIVE01`
- It does not directly mutate LIVE01 selected question rows except through apply/reset logic.
- `scripts/rehearsal_live01_role_e2e.py` performs `reset-runtime`, `reset-delegations`, `scenario apply`, then `seed-technical-run`, which creates fresh host-round fixtures.

## 7) Current LIVE01 question risk

- LIVE01 currently remains a role-complete rehearsal fixture with prior seeded phases/events/transactions (per earlier rehearsal artifacts and reports).
- Safe assumption: runtime host question rows are stale for tomorrow unless runtime is reset and scenario is re-applied for fresh technical/real setup.

## 8) Safe question replacement options

### A) Replace questions in current scenario JSON file (`season1_mvp_live_v2.json`)
- Pros: simple, centralized versioned change.
- Cons: affects all future uses of this scenario code until template change restored.
- Steps: edit scenario JSON → import/ apply (merge preferred for controlled change).
- Best for “need tomorrow’s fresh set quickly”.

### B) Create a new scenario JSON and repoint LIVE01
- Pros: zero risk to existing tested scenario while keeping history.
- Cons: requires one-time creation + script/coordination to switch LIVE01 `scenario_code`/`scenario_id`.
- Strongly suitable for rehearsal-safe rollout and rollback.

### C) Seed host-round questions directly into DB
- Not recommended for this scope.
- Would bypass normal import/apply invariants and increase operator/db risk.

### D) Manual admin/operator selection if supported
- Not currently a standalone operator UI flow for arbitrary question-bank replacement.
- Requires runtime code changes not included in this audit.

## 9) Recommended option for tomorrow

Recommended: **B (new scenario JSON + apply to LIVE01)** for minimal collateral risk, or **A** only if team prefers speed and accepts one-file replacement under `season1_mvp_live_v2.json`.

Execution guidance:
1. Prepare new `app/game_templates/scenarios/season1_mvp_live_v2_YYYYMMDD.json` with rehearsal-safe questions.
2. Optional: keep existing as backup.
3. Import via scenario API/script and apply to a rehearsal game first.
4. Perform role-complete non-mutating checks before final live mapping.

## 10) Read-only LIVE01 question verification (no DB write)

Do not execute in this step; run from an operator-approved shell with DB access:

```bash
python - <<'PY'
from app.db.database import SessionLocal
from app.models import Game, GameHostRoundQuestion, GameHostRound, RoundQuestionTemplate

with SessionLocal() as db:
    game = db.query(Game).filter(Game.room_code == "LIVE01").first()
    if not game:
        print("LIVE01 not found")
        raise SystemExit(1)
    count_runtime = db.query(GameHostRoundQuestion).join(GameHostRound).filter(GameHostRound.game_id == game.id).count()
    count_template = db.query(RoundQuestionTemplate).count()
    print({
        "room_code": "LIVE01",
        "game_id": game.id,
        "runtime_host_questions": count_runtime,
        "question_templates": count_template,
    })
PY
```

## 11) Smoke checks to confirm active question set

- Scenario endpoint check: `GET /games/LIVE01/scenario`
- Master/TV director state: active round IDs and question pointers should reflect expected rehearsal content
- Host round question flow:
  - open-next-question returns expected prompt source titles
  - no old duplicate or unexpected sequence behavior
- Manual quick check (post-reset/apply):
  - no mixed scenario names in scenario/director payload
  - LIVE01 `game.scenario_code` set to new code
  - `game_host_round_questions` count grows after host opens question

## 12) What must not be touched now

- Do **not** run reset/rebuild in this task.
- Do **not** touch Court/Final templates or runtime.
- Do **not** mutate DB in this audit-only step.
- Do **not** export ADMIN tokens in output.

## 13) Next Codex task

- `A` — prepare LIVE01 real setup checklist only (if the team wants only immediate control artifact and operator-confirmed execution plan), then execute controlled scenario+question replacement after approval from product/host.
