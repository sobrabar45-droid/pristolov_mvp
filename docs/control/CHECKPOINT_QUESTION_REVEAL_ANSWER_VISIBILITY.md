# Question Reveal answer visibility checkpoint

Date: 2026-06-27

## Commit

Runtime fix:

- `197f3c1` Fix question reveal answer visibility

## Problem

After `POST /dev/host-rounds/{host_round_id}/force-close-question`, the runtime question correctly moved to `status="resolved"` and raw DB question content still contained `correct_answer`.

However, Master/TV state did not expose the resolved question after close/reveal. As a result, the TV reveal renderer had no `current_question.content.correct_answer` to display.

## Root cause

The sanitizer was not the main problem.

Existing sanitizer behavior in `app/services/master_state_service.py` already allowed full question content when `is_reveal=True`:

- before reveal: remove `correct_answer`, `answer`, and `explanation`;
- before `open-answers`: also remove answer options;
- after reveal: return safe content as-is.

The actual issue was state selection:

- Master state selected only active `GameHostRoundQuestion` records;
- TV state selected only active `GameHostRoundQuestion` records;
- once the question became `resolved`, it was dropped from `current_question` entirely.

## Fix

Changed only:

- `app/services/master_state_service.py`

Added helper:

- `_select_current_or_reveal_runtime_question(...)`

Behavior after the fix:

- prefer active runtime question;
- if no active question exists, select the latest `resolved` / `closed` question for the active host round;
- pass the selected question into existing `_build_runtime_question_payload(...)`;
- keep existing sanitizer as the only answer-visibility gate.

## Verification

Focused compile passed:

```text
python -m py_compile app\services\master_state_service.py
```

Targeted local smoke in `TEST_ROOM_SETUP` passed.

Before open answers:

```text
Master/TV reveal_stage=question
options hidden
correct_answer hidden
```

After open answers:

```text
Master/TV reveal_stage=options
options visible
started_at set
correct_answer hidden
```

After force-close/reveal:

```text
runtime_question.status=resolved
Master/TV reveal_stage=reveal
content.correct_answer visible
options visible
```

Anti-google regression check:

```text
correct_answer hidden before reveal
options hidden before open answers
correct_answer not exposed merely because answers_open=true
correct_answer exposed only after runtime question status resolved
```

## Scope notes

- Player state was not changed.
- Player phone answer reveal remains a product decision, not part of this fix.
- Templates were not changed.
- Routes were not changed.
- Scenario JSON was not changed.
- DB schema was not changed.
- `LIVE01` was not touched.
- Production was not touched.
- Local `TEST_ROOM_SETUP` still contains accumulated smoke artifacts.
- Production HEAD/deployment status remains unverified.

## Remaining decisions

1. Decide whether player phones should also show correct answer after reveal.
2. Decide when to deploy and smoke `197f3c1` in production.
3. Decide whether local `TEST_ROOM_SETUP` should be cleaned, archived, or kept as a smoke fixture.

## Recommended next product step

Recommended next product contour: player rules / printed one-page guide.

Reason:

- the latest technical P0 flow is now locally verified;
- Harchevnya and physical markers are useful, but players still need a clear one-page contract for what to do at the table;
- a printed guide can reduce host interruptions without more runtime risk.

Do not start that product task from this checkpoint.
