# DEVELOPMENT LEARNING PACK: Cashier Production Rollout

## Trigger / why this pack exists
- Block needed a safe way to run cashier gold assignment from tablets on pristolov.ru without weakening existing access control.
- Earlier paths (`/dev`) were not suitable for cashiers; we needed a dedicated, protected cashier surface.
- This pack captures the production-safe pattern used to close risk, run rollout, and avoid repeated mistakes.

## Reusable pattern
- Keep cashier flow isolated from `/dev` and any operator-only UI.
- Add dedicated route: `/cashier/gold-desk/{room_code}` with equivalent backend behavior to internal Gold Desk.
- Protect `/cashier` at both app and proxy boundary together with `/gold`.
- Keep `/cashier` and `/gold` available behind:
  - app-level route guard (`ADMIN_ROUTE_TOKEN` where configured), and
  - deployment-layer gate for tablet access (Basic/Auth or equivalent).
- Avoid custom token transport in frontend. Browser cannot send `X-Admin-Token` automatically.
- Roll out only through deployment infra changes before opening new protected external route.
- Use rollback-safe configuration changes for web server.

## What worked
- Internal and external split:
  - `/dev` remained internal/operator-only.
  - `/cashier` became separate external-facing entry for tablets.
- `app/templates/cashier_gold_desk.html` kept simple and safe:
  - no `/dev` links
  - existing check-amount flow intact
  - added manual `+1` mode for cumulative-order scenarios.
- Production nginx on VPS got explicit `/cashier/` protection and `X-Admin-Token` forwarding/injection.
- Smoke checks were explicit and passed:
  - `/cashier/gold-desk/LIVE01` accessible to authorized path
  - manual section and `+1` button visible
  - no `/dev` links shown
  - manual grants and check-amount grants both operational.

## What almost went wrong
- Assuming browser could call protected endpoints with `X-Admin-Token` without explicit proxy/header handling.
- Trying to expose `/cashier` via existing `/dev` paths instead of a dedicated route.
- Missing local recovery when server smoke got interrupted by stale ports/processes.
- Ambiguity between local Windows shell tooling and VPS shell environment during operations.
- Incomplete command flow that mixed admin patch + rollout smoke in one rushed pass.

## Safe production rollout checklist
- Confirm commit is complete in local branch.
- Commit docs/runtime scope decisions before rollout.
- Push commits intended for production.
- On VPS: update application working tree from source and build/pull expected commit.
- Apply/verify web-server changes first for any new external route.
- Restart app/service and run targeted endpoint smoke only after network/proxy checks.
- Keep `/dev` excluded from public exposure.
- Run exact path smoke from external client/device.
- Record and validate rollback path.

## VPS/nginx checklist
- Identify service/config:
  - service: `pristolov.service`
  - config: `/etc/nginx/sites-available/pristolov`
- Backup nginx file with timestamp before edits.
- Add/mirror `/cashier/` location consistently with existing `/gold/`.
- Preserve and verify auth and header forwarding settings.
- Verify syntax (`nginx -t`) before reload.
- Reload only on successful config validation.

## Codex hang recovery pattern
- If Codex/local smoke stalls:
  - stop touching runtime logic.
- Preserve current state and report:
  - dirty files
  - open ports/processes
  - temp logs existence
  - compile status
  - what smoke is done and what remains.
- Finish smoke in follow-up once environment is clean.
- Avoid destructive cleanup without confirmation.

## Shell distinction: Windows PowerShell vs VPS bash
- Local development actions:
  - run in Windows PowerShell.
  - use Windows process tooling and local ports.
- Production checks:
  - run over SSH on VPS (bash-compatible shell).
  - do not execute Linux shell commands locally in PowerShell scripts.
- Keep deployment verification and app file checks in VPS context.

## Security rules for /cashier, /gold, /dev
- `/cashier`: no public exposure without guard; protect like `/gold`.
- `/gold`: keep authenticated token-bound behavior for write APIs.
- `/dev`: never expose publicly; no operational cashier dependencies on `/dev`.
- Do not pass secrets/tokens in URL, page, JS, logs, or screenshots.
- If token forwarding is required, perform it in controlled infrastructure layer.

## Anti-patterns
- Reusing internal paths for external cashiers.
- Removing check-amount mode when adding manual +1 mode.
- Adding `/cashier` route in app without proxy/tested production boundary.
- Exposing token in query, body, frontend script, or templates.
- Pushing production changes without verified smoke path and rollback plan.

## Future reuse
- Apply the same pattern for any tablet-only internal operator action surface.
- Reuse the guarded split:
  - internal operator flows stay in `/dev`,
  - cashier/assistant workflows live under dedicated prefix,
  - production guard chain is explicit and testable.
- Reuse this pack during next feature block transitions that touch routes and deployment hardening.

