# Development Learning Pack: Public Homepage V1

## 1. Block summary

The public homepage block is closed.

System-level outcome:

- The public homepage `/` was previously wired but effectively empty.
- V1/V2 homepage prototypes were useful exploration but were not the accepted direction.
- V3 image-first homepage direction was accepted as the practical visual direction.
- `/` was implemented through the existing isolated `app/templates/index.html` root template.
- `/join` was restyled so the first public entry flow no longer looked like an old unstyled form.
- The hero image was deployed as a static asset.
- Production deploy and read-only smoke succeeded.
- A follow-up audit confirmed that service/operator routes must not be exposed directly from the public homepage before the next live game.

The block stayed narrow: no `LIVE01`, DB, migrations, Master/TV/Player/Cashier gameplay logic, route logic, or scenario mechanics were changed.

## 2. Final state

Latest production UI commit:

- `be04f4c Polish public homepage and join page`

Deploy checkpoint:

- `e52a734 Add public homepage deploy checkpoint`

Service routes audit checkpoint:

- `871edf4 Add homepage service routes audit checkpoint`

Production state recorded:

- `/` works.
- `/join` works.
- Static hero image works.
- Public contacts are real:
  - `553-553`
  - `8 912 835-35-53`
  - `vk.ru/pristolov45`
  - `@sobranie_kgn`

## 3. Reusable pattern: freeze-safe public UI exception

Pattern:

- A pre-game freeze can allow narrow public UI work if it does not touch game runtime.
- Audit first.
- Prefer changing an existing isolated template if the route is already wired.
- Add a static asset only if needed.
- Avoid route edits.
- Avoid DB/schema changes.
- Avoid migrations.
- Avoid game templates and runtime screens.
- Run local read-only smoke before commit.
- Deploy with GET-only smoke.

Good example from this block:

- `/` already rendered `app/templates/index.html`.
- The template was empty.
- Static files were already mounted from top-level `static/`.
- The safe implementation slice was only:
  - `app/templates/index.html`
  - `static/homepage/hero_council_room.png`

## 4. Reusable pattern: prototype before runtime

Pattern:

- Start with a concept doc.
- Create a content pack.
- Build standalone HTML prototypes outside runtime.
- Reject weak prototype directions without committing them into runtime.
- Commit only the accepted prototype direction.
- Keep prototypes separate from app templates until implementation is approved.
- After approval, implement the narrowest runtime slice.

Specific lessons:

- CSS-only prototype work is fast, but can easily drift into generic premium/admin/dashboard visuals.
- Image-first hero direction improved first impression and made the page feel less like an internal tool.
- Final runtime should use the image as atmosphere/background, not as a disconnected square/card if the goal is a public landing page.
- A polished homepage is not enough if `/join` still looks old; the first click must feel like the same product.

## 5. Reusable pattern: public vs protected surfaces

Pattern:

- Public homepage should not expose service/operator routes directly.
- `/dev`, `/gold`, and `/cashier` are protected by `ADMIN_ROUTE_TOKEN` / `X-Admin-Token` when configured.
- Public `<a>` links cannot send `X-Admin-Token`.
- Direct public links to protected routes create bad UX or security expectations.
- Protected/operator navigation should become a separate protected hub later.

Decision from this block:

- Do not add direct public buttons to Game Master, TV mode, cashier, scenario admin, question import, or gold/operator tools before the game.

## 6. Reusable pattern: deploy safety

Successful deploy pattern:

1. Push local commit to origin first.
2. On production, use `git pull --ff-only origin main`.
3. Run compile check.
4. Restart `pristolov.service` only after successful pull and compile.
5. Confirm service status is `active`.
6. Run read-only smoke:
   - `GET /`
   - `GET /join`
   - static hero image
7. Run content marker check.
8. Run forbidden marker check.
9. Do not run mutating smoke.

This worked for the public homepage block because the change was template/static-only and did not require migrations or data changes.

## 7. Reusable pattern: unexpected file guard

Incident captured:

- Unexpected `app/dependencies.py` appeared before homepage smoke.
- Smoke was stopped.
- Diff was inspected.
- The change was outside approved homepage scope.
- Only `app/dependencies.py` was reverted.
- Homepage smoke continued afterward.

Lesson:

- If an unexpected runtime file appears, stop before verification, commit, or deploy.
- Inspect the diff.
- Revert or intentionally split the change.
- Never hide unrelated runtime changes inside a public UI patch.

## 8. Specific decisions made

Decisions:

- Public brand spelling: `приСтолов`.
- `/` is the public marketing/game entry page.
- `/join` is the public room-code entry page.
- `Войти в игру` leads to `/join`.
- Service/operator links are not exposed before the game.
- Question import is not public.
- Future operator hub should be protected.

## 9. What not to repeat

Do not repeat:

- Do not leave public homepage empty.
- Do not use placeholder contacts on production.
- Do not make the hero image a small square/card if it is meant as atmosphere.
- Do not deploy a polished homepage if `/join` still looks old.
- Do not add public buttons to `/dev`, `/cashier`, or `questions/import`.
- Do not mix docs/prototypes/runtime changes in one uncontrolled commit.
- Do not use `git add .`.

## 10. Future follow-up candidates

Possible future tasks:

- Protected Operator Start Hub V1 design.
- Question import/admin workflow documentation.
- Public homepage visual refinement after real phone review.
- Favicon / OG image / social preview.
- Proper contact/legal/footer pass.
- Production non-LIVE browser smoke before game.
- Post-game feedback checkpoint.

## 11. Codex control notes

Recommended future Codex instructions:

- Inspect before editing.
- List expected changed files before touching files.
- Never stage unrelated files.
- Require local smoke for public UI.
- Require deploy smoke for production.
- Cite expected non-actions in IF-reports.
- Stop on unexpected runtime diffs.
- Keep public/protected route boundaries explicit.
- Prefer narrow commits over bundled mixed-scope commits.

## 12. NEXT_CODEX_TASK suggestion

`docs/control/NEXT_CODEX_TASK.md` was not updated in this task.

Suggested next task wording if it is updated later:

```text
Current recommended next step:
Stay in pre-game safety mode. Do not start new runtime mechanics before the live game. Allowed work: print/read-through, phone visual check for `/` and `/join`, protected non-LIVE production browser smoke by protocol, and post-game feedback collection.
```
