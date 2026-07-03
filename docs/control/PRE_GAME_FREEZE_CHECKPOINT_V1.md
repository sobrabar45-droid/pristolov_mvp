# Pre-Game Freeze Checkpoint V1

## 1. Purpose

This is a pre-game freeze checkpoint.

The goal is to avoid destabilizing the project before the live game.

Only safety checks, protected-access browser smoke by protocol, print preparation, and host/operator read-through work should continue unless Victor explicitly approves runtime changes.

If a change is interesting but not required for game-day safety, it waits until after the game.

## 2. Current clean state

- Latest local commit: `8d48266 Add post-game feedback sheet v1`.
- Working tree expected: clean.
- Production deploy checkpoint exists.
- Production browser smoke protocol exists.
- Live operator checklist exists.
- Host game pack exists.
- Post-game feedback sheet exists.
- Diplomacy + Whisper manual pack exists.

Relevant recent preparation commits:

- `052b689 Add live operator checklist v2`
- `723cdb0 Add production browser smoke protocol`
- `ab52ecb Add host game pack v1`
- `8d48266 Add post-game feedback sheet v1`

## 3. Ready for game

Ready components:

- Master/TV/player runtime baseline after post-rehearsal cleanup.
- Question Reveal answer visibility fix.
- Duel draw/replay handling.
- Harchevnya approved shelf.
- Harchevnya 18+ unlock.
- Manual Harchevnya replacement policy.
- Player one-page rules.
- Physical House/role markers.
- Printable layout source pack.
- Diplomacy + Whisper manual pack.
- Diplomacy / Дипломат and Мастер над шёпотом manual materials.
- Host/operator documents.
- Post-game feedback sheet.

## 4. Documents to use before game

```text
docs/control/LIVE_OPERATOR_CHECKLIST_V2.md
```

Use before and during the game for operator setup, screen checks, stage checks, failure handling, and quick operator reminders.

```text
docs/control/PRODUCTION_BROWSER_SMOKE_PROTOCOL_NON_LIVE.md
```

Use only for protected-access production browser smoke in a non-LIVE room. Do not mutate production live state.

```text
docs/control/HOST_GAME_PACK_V1.md
```

Use for host speech, role explanations, stage transitions, emergency wording, and closing speech.

```text
docs/control/POST_GAME_FEEDBACK_SHEET_V1.md
```

Use after the game to collect facts before deciding on the next development block.

```text
docs/print_pack_v1/diplomacy_whisper_v1/
```

Use if Diplomacy + Whisper V1 is tested manually. Print/read through before game; do not assume runtime support for Whisper charges.

## 5. Allowed actions before game

Allowed:

- Print materials.
- Read-through with host/operator.
- Production browser smoke only by protocol.
- Use non-LIVE room only for production smoke.
- No mutating action unless explicitly approved.
- Check protected access.
- Prepare devices, chargers, Wi-Fi, HDMI, browser tabs, and backup devices.
- Collect missing operational notes.
- Confirm who is host, operator, and final decision-maker for incidents.

## 6. Forbidden actions before game without explicit Victor approval

Forbidden without explicit Victor approval:

- Do not touch `LIVE01`.
- Do not deploy.
- Do not run migrations.
- Do not restart production.
- Do not mutate production rooms.
- Do not confirm Harchevnya purchases during smoke.
- Do not force-close real questions.
- Do not resolve real duels.
- Do not advance real stages.
- Do not introduce new runtime mechanics.
- Do not digitalize Diplomacy + Whisper before manual test feedback.
- Do not change DB schema.
- Do not change scenario JSON.
- Do not make broad UI rewrites.

## 7. Known remaining tails

### Technical / rollout

- Production browser smoke with protected access still may need to be run.
- Smoke requires a non-LIVE room.
- Protected access blocks plain curl for `/dev` and `/cashier`.
- No mutating production Harchevnya smoke has been run.
- Production smoke must not touch `LIVE01`.

### Product / gameplay

- Diplomacy + Whisper should be tested manually before code.
- House identity/perks decision is deferred.
- Duel V2 is deferred.
- Inter-House attack/defense is deferred.
- Full resources/metaverse return is deferred.

## 8. Stop rule

Strong stop rule:

If a proposed change is not required for game-day safety or a confirmed `P0` / `P1` blocker, do not do it before the game.

The pre-game state is now more valuable than another speculative improvement.

## 9. Emergency exception rule

Runtime changes before the game are allowed only if all are true:

- confirmed `P0` / `P1` blocker;
- Victor explicitly approves;
- change is narrow;
- rollback path is clear;
- verification is defined before patching;
- checkpoint is created after.

If any item is missing, do not patch before the game.

## 10. Post-game next step

After the game:

- Fill `docs/control/POST_GAME_FEEDBACK_SHEET_V1.md`.
- Create a post-game checkpoint.
- Prioritize `P0` / `P1` only.
- Separate technical bugs from gameplay confusion and host/operator mistakes.
- Decide whether Diplomacy + Whisper remains manual or gets runtime planning.
- Do not expand mechanics until core confusion is reviewed.

## 11. One-screen freeze summary

Current state:

- Local readiness checkpoint is at `8d48266 Add post-game feedback sheet v1`.
- Runtime stabilization and key post-rehearsal fixes are already complete.
- Host/operator/feedback documents are ready.

Use these docs:

- `LIVE_OPERATOR_CHECKLIST_V2.md`
- `PRODUCTION_BROWSER_SMOKE_PROTOCOL_NON_LIVE.md`
- `HOST_GAME_PACK_V1.md`
- `POST_GAME_FEEDBACK_SHEET_V1.md`
- `docs/print_pack_v1/diplomacy_whisper_v1/`

Allowed:

- Print.
- Read through.
- Prepare devices.
- Check protected access.
- Run production browser smoke only by protocol and only non-LIVE.

Forbidden without Victor approval:

- Touch `LIVE01`.
- Deploy.
- Restart.
- Run migrations.
- Mutate production rooms.
- Confirm purchases during smoke.
- Force-close questions.
- Resolve duels.
- Advance stages.
- Add new mechanics.

Next after game:

- Fill feedback sheet.
- Create post-game checkpoint.
- Fix `P0` / `P1` only before expanding gameplay.
