# Codex-First Smoke Rhythm for PRISTOLOV_CORE

## Rule

Codex runs automated checks first and treats manual visual checks as final acceptance.

## Preferred automated checks (always)

- `git status --short`
- `python -m compileall app -q`
- `rg` checks for expected routes, templates, endpoint names, and state markers
- local/VPS HTTP smoke against relevant endpoints
- safe DB/state reads when non-destructive and useful
- service and log checks after deploy (`systemctl`, `nginx -t`, endpoint status)

## Manual check policy

- Browser/phone visual confirmation is reserved for final acceptance of a finished block or rollout.
- Earlier manual visual checks are only allowed when:
  - visual behavior cannot be inferred from API/HTML/route checks,
  - user explicitly asks for it,
  - production safety requires human confirmation.

## Server start discipline

- Avoid `Start-Process` / `cmd /c start` launch patterns that can hang.
- Prefer using an already running local server for smoke checks.
- Start a server only when required, then run scripted checks first.

## Safe development closure sequence

1. runtime/template patch
2. automated smoke and endpoint checks
3. commit
4. checkpoint documentation
5. production rollout plan/result (if deployed)
6. reusable learning pack (if needed)
7. final manual acceptance
