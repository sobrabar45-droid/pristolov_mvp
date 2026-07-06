# Checkpoint: Homepage Service Routes Audit

## 1. Summary

A read-only audit was completed before adding service/operator links to the public homepage.

Decision:

- Do not add direct service/operator links to the public homepage before the next live game.
- Keep the homepage public/player-facing.
- Keep Game Master, cashier, dev tools, scenario admin, and question loading behind protected/operator workflows.

## 2. Public routes found

Public/player routes found:

- `GET /`
- `GET /join`
- `POST /join`
- `GET /game/{room_code}`
- `POST /game/{room_code}/join-house`
- `GET /player/{player_id}/role-select`
- `POST /player/{player_id}/role-select`
- `GET /game/{room_code}/roster`

## 3. Delegation/player entry routes found

Delegation and house/player entry routes found:

- `GET /delegation/start`
- `POST /delegation/start`
- `GET /delegation/join`
- `POST /delegation/join`
- `GET /house/{invite_code}`
- `GET /house/{invite_code}/player/{player_id}`

## 4. Operator/service routes found

Operator/service routes found:

- `GET /dev/game-master/{room_code}`
- `GET /dev/master-screen/{room_code}`
- `GET /dev/tv-mode/{room_code}`
- `GET /dev/tv-screen/{room_code}`
- `GET /dev/gold-desk/{room_code}`
- `GET /dev/treasurer-shop/{room_code}`
- `GET /dev/scenario-admin`
- `GET /cashier/gold-desk/{room_code}`

Related protected/mutating surfaces also exist under `/dev`, `/gold`, and `/cashier`.

## 5. Access boundary

`app/main.py` protects these prefixes when `ADMIN_ROUTE_TOKEN` is configured:

- `/dev`
- `/gold`
- `/cashier`

Required header:

- `X-Admin-Token`

Implication:

- A normal public homepage link cannot attach `X-Admin-Token`.
- Direct public links to protected service routes would likely return `403` on production.
- Even if a direct link opens locally, it does not represent production behavior when operator route protection is enabled.
- Direct links can create bad expectations for public users and operators.

## 6. Question-base loading audit

Backend question import endpoints found:

- `POST /dev/questions/import`
- `POST /dev/questions/prepare-media`

Supported import formats:

- `.docx`
- `.xlsx`

Important behavior:

- `dry_run=true` is the default for `POST /dev/questions/import`.
- `dry_run=false` writes/imports questions.
- `clear_existing=true` can delete existing related questions/runtime rows for the target round.
- Default target round: `imported_warmup_test`.

Source service files:

- `app/services/question_import_service.py`
- `app/services/media_prepare_service.py`

Question templates/docs:

- `docs/question_import_templates/`

Scenario admin relationship:

- `GET /dev/scenario-admin` exists.
- It supports scenario operations through JavaScript:
  - `GET /dev/scenarios`
  - `GET /dev/games/{room_code}/scenario`
  - `POST /dev/games/{room_code}/scenario/apply`
  - `POST /dev/scenarios/import`
  - `POST /dev/scenarios/{scenario_code}/import-round`

No dedicated public/browser upload page for question import was found during the audit.

## 7. Safe / unsafe exposure decision

Safe now:

- `/join`
- `/delegation/start` if later explicitly approved

Unsafe before the game:

- `/dev/master-screen/{room_code}`
- `/dev/game-master/{room_code}`
- `/dev/tv-mode/{room_code}`
- `/dev/scenario-admin`
- `/dev/questions/import`
- `/dev/questions/prepare-media`
- `/dev/gold-desk/{room_code}`
- `/dev/treasurer-shop/{room_code}`
- `/cashier/gold-desk/{room_code}`

Why unsafe:

- These routes are protected or operator-only.
- Many related screens contain mutating controls.
- They can affect runtime/game state.
- They may confuse public users.
- They may expose operator surfaces from a public page.
- Question import can write to the database when not in dry-run mode.
- `clear_existing=true` is potentially destructive for existing question/runtime rows.

## 8. Homepage recommendation

Keep the public homepage focused on:

- player entry;
- event/format explanation;
- organizer-facing public copy;
- safe public contacts.

Do not add direct homepage buttons for:

- Game Master;
- TV mode;
- cashier;
- gold desk;
- scenario admin;
- question upload/loading.

If needed later, add only informational copy such as:

- operator modes are available through protected organizer links;
- ask the host/operator for service access;
- protected tools are not public player entry points.

Actual service navigation should be handled by a separate protected hub, not public `/`.

## 9. Future protected operator hub concept

Future docs/design task:

- `Protected Operator Start Hub V1`

Possible route shape:

- `/dev/operator-start/{room_code}`

Possible protected hub buttons:

- Game Master;
- TV mode;
- cashier/gold desk;
- Harchevnya cashier queue;
- scenario admin;
- question loading/import tools;
- room health/status links.

This should happen only after access/control design, including how protected browser access will provide `X-Admin-Token` or another approved operator authentication path.

## 10. Final decision

Before the next live game:

- no public direct service links;
- no public question upload UI;
- no public cashier link;
- no public Game Master link;
- no homepage change needed from this audit unless Victor explicitly approves a safe informational block.

The safest current posture is:

- keep `/` public and player/organizer-facing;
- keep operator tools protected;
- use operator checklists/protected access for service navigation.
