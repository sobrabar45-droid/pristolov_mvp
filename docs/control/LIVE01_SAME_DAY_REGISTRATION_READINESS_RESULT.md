# LIVE01 Same-Day Registration Readiness Result

Date: 2026-06-21

## Goal

Prepare `LIVE01` for same-day live registration through One QR House Creation:

- `https://pristolov.ru/delegation/start?game_code=LIVE01&entry_mode=random`

The target product flow is:

- no pre-created Houses,
- guests create Houses on site,
- total number of Houses may be less than 10,
- system supports up to 10 official Houses,
- random/blind draw starts with +1 gold,
- baseline economy remains `500 ₽ = 1 gold`.

## Local checks completed

- Local git status before docs work: clean.
- Local HEAD: `8dc00ea`.
- `python -m compileall app -q`: passed.
- Scenario file inspected:
  - `app/game_templates/scenarios/season1_mvp_live_v2.json`
  - rounds: 10
  - embedded scenario questions: 13
- Court/question draft inspected:
  - `docs/control/LIVE01_QUESTION_REPLACEMENT_CANDIDATES_DRAFT.md`
  - includes parsed `stage_court_battle_45.patched.xlsx`
  - contains 45 clean Court question candidates in the draft/audit layer.

## Production/VPS access result

Codex could not execute the VPS reset directly.

- `ssh root@5.42.119.94 ...` through the default shell returned a local wrapper-like failure.
- `C:\Windows\System32\OpenSSH\ssh.exe ...` reached SSH but failed authentication:
  - `Permission denied (publickey,password).`

No production reset was executed from Codex.
No production DB mutation was performed from Codex.

## Pre-reset production state

Expected current state from the prior role-complete rehearsal result:

- `LIVE01` contains rehearsal fixture data.
- Rehearsal data may include:
  - test Houses,
  - test Players,
  - test Roles,
  - gold transactions,
  - deals,
  - active phases,
  - expedition/map state.

Production counts were not refreshed by Codex because VPS SSH authentication failed.

## Manual VPS command block for cleanup and smoke

Run this manually on the VPS as `root`.

Do not paste token values back into Codex output.

```bash
cd /opt/pristolov/app
set -e

echo "== preflight =="
git status --short
git rev-parse --short HEAD
python -m compileall app -q
systemctl is-active pristolov

echo "== load admin token, do not print =="
TOKEN="$(grep '^ADMIN_ROUTE_TOKEN=' /etc/pristolov/pristolov.env | cut -d= -f2-)"
test -n "$TOKEN" && echo "token_set=yes"

echo "== pre-reset counts =="
python - <<'PY'
from app.database import SessionLocal
from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.game_deal import GameDeal
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.game_expedition import GameExpedition
from app.models.game_map_visit import GameMapVisit
from app.models.game_map_state import GameMapState

db = SessionLocal()
try:
    game = db.query(Game).filter(Game.room_code == "LIVE01").first()
    print("game_exists=", bool(game), sep="")
    if game:
        house_ids = [h.id for h in db.query(House).filter(House.game_id == game.id).all()]
        print("houses=", len(house_ids), sep="")
        print("players=", db.query(Player).filter(Player.house_id.in_(house_ids)).count() if house_ids else 0, sep="")
        print("deals=", db.query(GameDeal).filter(GameDeal.game_id == game.id).count(), sep="")
        print("gold_transactions=", db.query(HouseGoldTransaction).filter(HouseGoldTransaction.game_id == game.id).count(), sep="")
        print("expeditions=", db.query(GameExpedition).filter(GameExpedition.game_id == game.id).count(), sep="")
        print("map_visits=", db.query(GameMapVisit).filter(GameMapVisit.game_id == game.id).count(), sep="")
        print("map_states=", db.query(GameMapState).filter(GameMapState.game_id == game.id).count(), sep="")
finally:
    db.close()
PY

echo "== reset runtime =="
curl -sS -X POST -H "X-Admin-Token: $TOKEN" \
  http://127.0.0.1:8000/dev/games/LIVE01/reset-runtime
echo

echo "== reset delegations =="
curl -sS -H "X-Admin-Token: $TOKEN" \
  http://127.0.0.1:8000/dev/reset-delegations/LIVE01 \
  | python -c "import sys; data=sys.stdin.read(); print('reset_delegations_html_len=' + str(len(data))); print('LIVE01_in_response=' + str('LIVE01' in data))"

echo "== post-reset counts =="
python - <<'PY'
from app.database import SessionLocal
from app.models.game import Game
from app.models.house import House
from app.models.player import Player
from app.models.game_deal import GameDeal
from app.models.house_gold_transaction import HouseGoldTransaction
from app.models.game_expedition import GameExpedition
from app.models.game_map_visit import GameMapVisit
from app.models.game_map_state import GameMapState

db = SessionLocal()
try:
    game = db.query(Game).filter(Game.room_code == "LIVE01").first()
    print("game_exists=", bool(game), sep="")
    if game:
        house_ids = [h.id for h in db.query(House).filter(House.game_id == game.id).all()]
        print("houses=", len(house_ids), sep="")
        print("players=", db.query(Player).filter(Player.house_id.in_(house_ids)).count() if house_ids else 0, sep="")
        print("deals=", db.query(GameDeal).filter(GameDeal.game_id == game.id).count(), sep="")
        print("gold_transactions=", db.query(HouseGoldTransaction).filter(HouseGoldTransaction.game_id == game.id).count(), sep="")
        print("expeditions=", db.query(GameExpedition).filter(GameExpedition.game_id == game.id).count(), sep="")
        print("map_visits=", db.query(GameMapVisit).filter(GameMapVisit.game_id == game.id).count(), sep="")
        print("map_states=", db.query(GameMapState).filter(GameMapState.game_id == game.id).count(), sep="")
finally:
    db.close()
PY

echo "== protected surface smoke =="
for path in \
  /dev/master-screen/LIVE01 \
  /dev/tv-mode/LIVE01 \
  /cashier/gold-desk/LIVE01 \
  /dev/treasurer-shop/LIVE01
do
  code="$(curl -sS -o /tmp/pristolov_smoke.html -w '%{http_code}' -H "X-Admin-Token: $TOKEN" "http://127.0.0.1:8000$path")"
  echo "$path=$code"
done

echo "== one qr smoke =="
curl -sS "http://127.0.0.1:8000/delegation/start?game_code=LIVE01&entry_mode=random" > /tmp/pristolov_one_qr.html
grep -q 'LIVE01' /tmp/pristolov_one_qr.html && echo "one_qr_live01=present"
grep -q 'Жребий даёт +1 золото' /tmp/pristolov_one_qr.html && echo "one_qr_bonus_copy=present"
grep -q 'Создать Дом' /tmp/pristolov_one_qr.html && echo "one_qr_create_house=present"
grep -q 'entry_mode_random' /tmp/pristolov_one_qr.html && echo "one_qr_random_input=present"
```

## Expected post-reset state

After the two reset calls:

- `houses=0`
- `players=0`
- `deals=0`
- `gold_transactions=0`
- `expeditions=0`
- `map_visits=0`
- `map_states=0`
- Master screen opens.
- TV screen opens.
- Cashier screen opens.
- One QR page opens and contains:
  - `LIVE01`,
  - random/draw option,
  - “Жребий даёт +1 золото”,
  - “Создать Дом”.

## Controlled registration smoke

Not executed by Codex because production reset could not be executed from this environment.

Recommended same-day approach:

- If time allows after manual reset, create exactly one temporary House through the One QR URL.
- Confirm:
  - starting gold is 11,
  - leader role is `lord_lady`,
  - lobby/join link exists,
  - player room opens.
- Then immediately run:
  - `POST /dev/games/LIVE01/reset-runtime`
  - `GET /dev/reset-delegations/LIVE01`
- Final state before guests arrive should be empty registration state.

If time is tight:

- Skip controlled registration mutation.
- Use non-mutating One QR HTML smoke only.
- Let first real Lord/Lady registration be the live start.

## Court/question readiness

Known local facts:

- Current scenario has 10 rounds and 13 embedded questions.
- The question audit/draft contains 45 clean Court question candidates from the patched Court bank.
- The 45-question bank is documented/audited and available as source material; this task did not import or mutate scenario/DB data.

Immediate recommendation for today:

- Use the existing scenario questions for general rounds unless an already-approved import path is executed.
- Keep the 45 clean Court questions as operator/manual Court backup if they are not imported before the game.
- Do not import question data during live setup unless the operator explicitly chooses that path and there is time for smoke.

## Go / no-go

Current Codex result:

- Infrastructure readiness from local repo: green.
- Production cleanup execution from Codex: blocked by SSH authentication.
- LIVE01 live-registration readiness: pending manual VPS cleanup command block.

Go condition before guest registration:

- Manual VPS block confirms `houses=0`, `players=0`, and no leftover runtime artifacts.
- One QR page smoke is green.
- Master/TV/Cashier protected endpoint smoke returns 200.

No-go condition:

- `LIVE01` still has rehearsal Houses/Players after cleanup attempt.
- One QR URL does not open or does not prefill `LIVE01`.
- Protected screens fail after cleanup.

## Final manual acceptance checklist

Perform only after automated/manual VPS command block is green:

- Open One QR URL on a phone.
- Confirm House creation page appears.
- Confirm `LIVE01` is visible/prefilled.
- Confirm random/draw is selected or clearly available.
- Confirm “Жребий даёт +1 золото”.
- Open Master screen.
- Open TV screen.
- Open Cashier Gold Desk.
- Keep LIVE01 empty until real guests begin registration.

## Runtime scope

No runtime code changed.
No templates changed.
No scenario JSON changed.
No DB mutation was executed by Codex.
No Court/Final logic changed.
