# Production smoke protocol before live game

## Context

- Pre-live readiness audit is closed in `9bc6639`.
- Codex-first smoke rhythm is active from `8f9da8e`.
- Target production:
  - VPS: `root@5.42.119.94`
  - app path: `/opt/pristolov/app`
  - service: `pristolov.service`
  - upstream: `http://127.0.0.1:8000`
  - public domain: `https://pristolov.ru`
  - room: `LIVE01`

## Local checks completed

- `git status --short`: clean at the start of this protocol task.
- `python -m compileall app -q`: passed.
- Local source/docs inspected:
  - `docs/control/PRE_LIVE_READINESS_AUDIT_AFTER_TREASURER_SHOP_V1_2.md`
  - `docs/control/CODEX_FIRST_SMOKE_RHYTHM.md`
  - `docs/control/NEXT_CODEX_TASK.md`
  - `app/routes/player.py`
  - `app/routes/cashier.py`
  - `app/routes/dev.py`
  - `app/templates/player_room.html`
  - `app/templates/cashier_gold_desk.html`
  - `app/templates/master_screen.html`
  - `app/templates/tv_mode_tv_state.html`
- Source surface checks confirmed:
  - cashier route exists: `/cashier/gold-desk/{room_code}`
  - cashier confirm endpoint exists: `/cashier/treasurer-shop/requests/{request_id}/confirm`
  - operator pages exist: `/dev/master-screen/{room_code}`, `/dev/tv-mode/{room_code}`, `/dev/gold-desk/{room_code}`, `/dev/treasurer-shop/{room_code}`
  - player Treasurer Shop request endpoint exists: `/player/treasurer-shop/request/{player_id}`
  - Last Whisper endpoint exists: `/player/last-whisper/action/{player_id}`
  - player phase label source includes fixed `Последний Шёпот`

## SSH/VPS checks status

- VPS checks are pending external execution.
- Codex environment SSH is not reliable for this task: `ssh root@5.42.119.94 "echo ok"` hung/failed in the Codex tool path.
- Do not treat missing VPS smoke as application failure. Treat it as an execution-environment limitation.
- Next step: run the command block below manually on the VPS or from a trusted terminal, then paste the output back into Codex.

## Manual VPS command block

Run this on the VPS as `root` from a normal terminal session. It intentionally does not print `ADMIN_ROUTE_TOKEN`.

```bash
set -euo pipefail
cd /opt/pristolov/app

echo "== git =="
git status --short
git rev-parse --short HEAD
git log --oneline -n 5

echo "== compileall =="
python -m compileall app -q
echo "compileall=passed"

echo "== service =="
systemctl is-active pristolov.service
systemctl status pristolov.service --no-pager | sed -n '1,12p'

echo "== recent logs =="
journalctl -u pristolov.service -n 80 --no-pager | grep -E "Traceback|ERROR|Exception" || true

echo "== env presence =="
test -f /etc/pristolov/pristolov.env && echo "env_file=present" || echo "env_file=missing"
grep -q '^ADMIN_ROUTE_TOKEN=' /etc/pristolov/pristolov.env && echo "ADMIN_ROUTE_TOKEN=SET" || echo "ADMIN_ROUTE_TOKEN=MISSING"

set +x
TOKEN="$(grep '^ADMIN_ROUTE_TOKEN=' /etc/pristolov/pristolov.env | cut -d= -f2-)"

echo "== protected endpoints with upstream token =="
for path in \
  /cashier/gold-desk/LIVE01 \
  /dev/master-screen/LIVE01 \
  /dev/tv-mode/LIVE01 \
  /dev/gold-desk/LIVE01 \
  /dev/treasurer-shop/LIVE01
do
  code="$(curl -sS -o /tmp/pristolov_smoke_page.html -w '%{http_code}' -H "X-Admin-Token: ${TOKEN}" "http://127.0.0.1:8000${path}")"
  echo "${path}=${code}"
done

echo "== cashier html content =="
curl -sS -H "X-Admin-Token: ${TOKEN}" "http://127.0.0.1:8000/cashier/gold-desk/LIVE01" > /tmp/pristolov_cashier.html
grep -q 'Ручное начисление' /tmp/pristolov_cashier.html && echo "manual_section=present" || echo "manual_section=missing"
grep -q '+1 золото' /tmp/pristolov_cashier.html && echo "plus_one_button=present" || echo "plus_one_button=missing"
grep -q 'Сумма чека' /tmp/pristolov_cashier.html && echo "check_amount=present" || echo "check_amount=missing"
grep -q 'Заказ принят' /tmp/pristolov_cashier.html && echo "accept_button=present" || echo "accept_button=missing"
grep -q 'Ожидает подтверждения' /tmp/pristolov_cashier.html && echo "shop_queue_status=present" || echo "shop_queue_status=missing"
grep -q '/dev' /tmp/pristolov_cashier.html && echo "cashier_dev_links=FOUND" || echo "cashier_dev_links=none"

echo "== player template static checks =="
grep -q '/dev' app/templates/player_room.html && echo "player_template_dev_links=FOUND" || echo "player_template_dev_links=none"
grep -q 'Последний Шёпот' app/routes/player.py && echo "phase_label_source=fixed" || echo "phase_label_source=check_needed"

echo "== db role inventory, redacted =="
python - <<'PY'
from collections import Counter
from app.database import SessionLocal
from app.models.game import Game
from app.models.player import Player

db = SessionLocal()
try:
    game = db.query(Game).filter(Game.room_code == "LIVE01").first()
    if not game:
        print("game=missing")
    else:
        players = db.query(Player).filter(Player.game_id == game.id).all()
        role_counts = Counter((p.role.code if p.role else "no_role") for p in players)
        print(f"game=present id={game.id}")
        print(f"players_count={len(players)}")
        for role_code, count in sorted(role_counts.items()):
            print(f"role_count {role_code}={count}")
        target_roles = ["treasurer", "lord_lady", "diplomat", "whisper_master", "maester", "house_sworn"]
        for role_code in target_roles:
            print(f"role_present {role_code}={role_counts.get(role_code, 0) > 0}")
finally:
    db.close()
PY

echo "== public protection spot checks =="
for path in /cashier/gold-desk/LIVE01 /dev/master-screen/LIVE01 /gold/houses/1/grant
do
  code="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:8000${path}" || true)"
  echo "upstream_without_token ${path}=${code}"
done
```

## Expected results

- `git status --short` should be clean.
- `git rev-parse --short HEAD` should be at or after the latest deployed PRISTOLOV_CORE commit.
- `compileall=passed`.
- `systemctl is-active pristolov.service` should print `active`.
- Recent logs should not show fresh `Traceback`.
- Protected endpoint smoke with `X-Admin-Token` should return `200` for:
  - `/cashier/gold-desk/LIVE01`
  - `/dev/master-screen/LIVE01`
  - `/dev/tv-mode/LIVE01`
  - `/dev/gold-desk/LIVE01`
  - `/dev/treasurer-shop/LIVE01`
- Cashier HTML checks should show:
  - `manual_section=present`
  - `plus_one_button=present`
  - `check_amount=present`
  - `accept_button=present`
  - `shop_queue_status=present`
  - `cashier_dev_links=none`
- Player template check should show:
  - `player_template_dev_links=none`
  - `phase_label_source=fixed`
- DB inventory should show `game=present` and role counts without player tokens.

## Controlled E2E candidates

- Safe on LIVE01 without mutation:
  - service status
  - compileall
  - protected endpoint GETs
  - HTML content checks
  - DB role inventory
- Mutating actions require explicit go-ahead or disposable test room:
  - Treasurer Shop request creation
  - cashier confirmation (`Заказ принят`)
  - manual `+1 золото`
  - check amount grant
  - Last Whisper actions
  - diplomacy/lord actions

## Go / No-Go logic

- GO:
  - service active
  - compileall passes
  - all protected endpoint GETs return `200` with token
  - no fresh traceback in recent logs
  - cashier HTML content is present
  - no `/dev` links in cashier/player surfaces
  - role inventory confirms required live roles exist
- Conditional GO:
  - non-mutating checks are green, but controlled E2E is deferred to final supervised acceptance
  - one non-critical role is absent but not needed for the live session
- No-Go:
  - service inactive
  - compileall fails
  - protected target pages do not return `200` with token
  - cashier page leaks `/dev`
  - player phase label source regresses
  - fresh traceback appears during smoke

## How to paste results back

Paste the complete command output back into Codex, with no token values. The command block above redacts the token by design. Codex should then create/update a smoke result doc and produce the final go/no-go recommendation.

## Final manual acceptance

Manual browser/phone acceptance is final-only after the command block is green:

- open one real player room link
- open cashier page
- open Master screen
- open TV screen
- visually confirm text/layout is readable on the target devices
