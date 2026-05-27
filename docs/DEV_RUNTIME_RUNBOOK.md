# Dev Runtime Runbook

## Goal

Start one fresh dev runtime from the project `venv` before smoke or rehearsal.

Do not run multiple uvicorn instances for the same project on port `8000`.

For smoke or rehearsal, prefer stable no-reload mode.

## Safe launcher

Use:

```powershell
cd D:\Projects\pristolov_mvp
.\scripts\start_dev_server.ps1 -NoReload
```

The launcher does this:

1. Confirms that the current directory is the project root.
2. Confirms that `.\venv\Scripts\python.exe` exists.
3. Checks which PID listens on port `8000`.
4. Prints the PID, executable path, and command line for the listener.
5. Stops only a listener that looks like the project python/uvicorn runtime.
6. Refuses to stop anything automatically if the process path or command line is ambiguous.
7. Normalizes Windows environment variables before launch so the child process gets one canonical `Path` entry instead of conflicting `Path` / `PATH` keys.
8. Starts a stable runtime by default for rehearsal, without `--reload`.
9. Supports optional reload mode only for active development.
10. Rotates the current `tmp\uvicorn_8000_stdout.log` and `tmp\uvicorn_8000_stderr.log` on every fresh launch by truncating them and writing a new launcher header for the current runtime.
11. Writes `tmp\uvicorn_8000_runtime.json` with the current launch metadata:
   - `started_at`
   - `port`
   - `bind_host`
   - `mode`
   - `project_root`
   - `venv_python`
   - `stdout_log`
   - `stderr_log`
   - `launcher_version`
   - `started_by`
   - `pid` when it can be confirmed
12. If command line attribution is missing, it can still trust the current runtime only when multiple signals agree:
   - there is exactly one python listener on `8000`;
   - the live master screen answers with the expected project UI markers;
   - the current marker/log points to the same project root and port;
   - PID match is a strong signal when available;
   - if PID is missing, the launcher still requires matching log or recent access-log evidence and no conflicting marker evidence.

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Why not kill all Python processes

Do not use broad process cleanup for rehearsal prep.

Reasons:

- other local Python jobs may be unrelated;
- a stale listener on `8000` must be identified, not guessed;
- broad kills make runtime diagnosis harder;
- the project already had mixed global Python and `venv` symptoms, so precise targeting matters.

## Before every smoke or rehearsal

1. Check git state:

```powershell
git status --short
```

Expected result: clean working tree.

2. Start the launcher from the project root:

```powershell
cd D:\Projects\pristolov_mvp
.\scripts\start_dev_server.ps1 -NoReload
```

If you change code while running in stable no-reload mode, restart the launcher before the next smoke.

3. Verify fresh UI on the runtime:

- open `http://127.0.0.1:8000/dev/master-screen/LIVE01`
- confirm the page shows:
  - `Вход игроков`
  - `Сбросить комнату для репетиции`

4. Reset `LIVE01` before rehearsal:

- `POST /dev/games/LIVE01/reset-runtime`
- `GET /dev/reset-delegations/LIVE01`

5. Verify clean room state:

- `houses_count = 0`
- `players_count = 0`
- `active_phases = []`
- `active_host_round = null`
- `current_question = null`
- `next_round = stage_intro`

## If the launcher refuses to stop port 8000

That is a safety feature.

Do not force broad cleanup immediately.

Instead:

1. inspect the printed PID and command line;
2. confirm whether it is really the project runtime;
3. stop only that specific process manually;
4. rerun the launcher.

Arbitrary `python.exe` listeners are still not stopped automatically just because they use port `8000`.
The launcher only trusts them when project evidence converges.

## Trusted runtime marker and logs

The launcher now maintains:

- `tmp\uvicorn_8000_runtime.json`
- `tmp\uvicorn_8000_stdout.log`
- `tmp\uvicorn_8000_stderr.log`

Why this matters:

- old append-logs can make trusted attribution ambiguous;
- Windows may hide the command line for the active `python.exe`;
- the marker gives the launcher a fresh record of the current project runtime without making that marker the only trust signal.

The launcher still refuses auto-stop when the signals conflict, for example:

- marker says one PID, but another PID listens on `8000`;
- marker/log points to another port or project root;
- master screen does not answer with the expected project UI;
- more than one listener is present on `8000`.

## LAN / phone access

Default local smoke:

```powershell
.\scripts\start_dev_server.ps1 -NoReload
```

This binds to `127.0.0.1`.

For phone or LAN rehearsal, use:

```powershell
.\scripts\start_dev_server.ps1 -NoReload -BindHost 0.0.0.0
```

Use `0.0.0.0` only when you really need another device on the network to connect.

## Reload mode

Use reload mode only during active template or route development:

```powershell
.\scripts\start_dev_server.ps1 -Reload
```

Do not use reload mode as the rehearsal default on this Windows machine.

## Dry run

To inspect the current listener and safe stop plan without stopping or starting anything:

```powershell
.\scripts\start_dev_server.ps1 -NoLaunch
```
