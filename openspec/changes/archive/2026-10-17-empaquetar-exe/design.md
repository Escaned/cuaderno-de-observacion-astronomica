# Design: Ship a Windows executable so users do not need Python

## Technical Approach

Add a launcher plus a build definition. The application changes in two places: how the built frontend is
located, and where writable paths come from. One new module, `backend/app/core/paths.py`, answers both at
import time. `backend/app/core/migrations.py` drives Alembic in code, so nothing needs an `alembic.ini`.
The rest is packaging.

## Architecture Decisions

| # | Decision | Choice | Rejected | Rationale |
|---|---|---|---|---|
| 1 | Package format | PyInstaller one-dir, console window | one-file; tray icon | Instant start instead of unpacking on every launch; no new dependency |
| 2 | Writable state | `data/` next to the executable | `sys._MEIPASS`; `%LOCALAPPDATA%` | `_MEIPASS` is a temp dir wiped on exit; `%LOCALAPPDATA%` hides the files users are told to back up |
| 3 | Paths into settings | Environment variables set **before** `app.core.config` is imported | `os.chdir()`; editing the defaults; shipping a `.env` | Keeps the development defaults untouched; `os.chdir` turns `./data/imagenes` into `data/data/imagenes` |
| 4 | Database bootstrap | Programmatic `alembic upgrade head` | `create_all`; shipping `alembic.ini` | `0001_initial.py` carries the seed and `create_all` seeds nothing; an `.ini` reintroduces a CWD-relative path |
| 5 | Built frontend | Inside the bundle, at `_MEIPASS/frontend/dist` | A folder next to the executable | One artifact instead of two |
| 6 | Bind address | `API_HOST=127.0.0.1` set explicitly | The `0.0.0.0` default | The default listens on every interface, exposing the user's observations to the whole LAN. `arrancar.bat` already binds to loopback |
| 7 | Probe vs open | Poll `127.0.0.1`, open `localhost` | `localhost` for both | Documented gotcha in `abrir-navegador.ps1`: `localhost` resolves to `::1` first and the server only speaks IPv4, so every probe eats the IPv6 timeout |
| 8 | Busy port | If `/health` answers as Riguel, open the browser and exit; otherwise report and stop | Silently picking another port | A URL that changes per launch breaks bookmarks; a clear message beats silent redirection |
| 9 | Legacy database | Copy `backend/riguel.db` into `data/`, never move | Move; ignore it | Losing observations is unacceptable; a copy is reversible |

Decision 7 is the likeliest source of a "hangs 30 seconds" bug report; both the launcher and the packaging
check must use it.

## Data Flow

    Riguel.exe
      |
      +- paths.app_dir()     -> <exe dir>/data      writable
      +- paths.bundle_root() -> sys._MEIPASS        read-only resources
      |
      +- set DATABASE_URL, IMAGES_DIR, API_HOST=127.0.0.1, API_PORT before the import
      +- create data/imagenes; restore logo.jpg if missing
      +- adopt backend/riguel.db -> data/riguel.db   copy, only if data/ has none
      +- migrations.upgrade_to_head()                fails loud, no server started
      +- import app.main; start uvicorn in-process, no reload
      +- poll http://127.0.0.1:<port>/health until 200
      +- open http://localhost:<port>  unless RIGUEL_SIN_NAVEGADOR

    main.py:  FRONTEND_DIST = paths.bundle_root() / "frontend" / "dist"

## File Changes

| File | Action | Description |
|---|---|---|
| `backend/app/core/launcher.py` | Create | Packaged entry point: paths, bootstrap, migrations, server, browser |
| `riguel.spec` | Create | PyInstaller one-dir definition: `datas`, `hiddenimports`, `excludes`, `--noupx` |
| `backend/app/core/paths.py` | Create | `is_frozen()`, `bundle_root()`, `app_dir()` |
| `backend/app/core/migrations.py` | Create | `upgrade_to_head()`, Alembic configured in code |
| `backend/tests/test_paths.py` | Create | Unit tests for the three helpers, frozen and not frozen |
| `backend/app/main.py` | Modify | `FRONTEND_DIST` from `paths.bundle_root()` |
| `backend/app/core/config.py` | Modify | Document that the launcher sets the paths when frozen |
| `backend/alembic/env.py` | Modify | Only fall back to the settings for the URL when the caller set none |
| `backend/requirements-dev.txt` | Modify | Pin `pyinstaller==6.22.3` |
| `empaquetar.ps1` | Modify | Opt-in `-ConExe` stage: build and verify the executable folder |
| `INSTALL.md` | Modify | Rewritten around the executable; SmartScreen note; data migration |
| `DESARROLLO.md` | Modify | Build steps and why PyInstaller |

No `.gitignore` change is needed: `dist/`, `build/` and `*.db` are already ignored, and `*.spec` stays
tracked. `abrir-navegador.ps1` is untouched; the launcher covers the frozen path natively.

Amended during apply, rationale in the apply-progress record: the entry point is
`backend/app/core/launcher.py`, not a root-level `desktop.py`, and `env.py` changes so the caller's
database URL wins.

## Interfaces / Contracts

```python
# backend/app/core/paths.py
def is_frozen() -> bool: ...   # getattr(sys, "frozen", False)
def bundle_root() -> Path: ... # sys._MEIPASS when frozen, else the repository root
def app_dir() -> Path: ...     # the executable's directory when frozen, else <repo>/backend
def writable_paths() -> WritablePaths: ...  # the database and the images, per mode

# backend/app/core/migrations.py
def upgrade_to_head(database_url: str, script_location: Path) -> None: ...
```

Set by the launcher before `app.core.config` is imported: `DATABASE_URL`, `IMAGES_DIR`, `API_HOST`,
`API_PORT`. Development sets none and keeps today's defaults. `case_sensitive=False` lets the uppercase
names match the lowercase fields, and environment variables outrank the `.env` file.

## Testing Strategy

| Layer | What | How |
|---|---|---|
| Unit | The three helpers decide correctly frozen vs not | `test_paths.py`, test-first, with `monkeypatch` on `sys.frozen`, `sys._MEIPASS` and `sys.executable` |
| Integration | Nothing regressed: settings defaults, static mount, SPA fallback, API 404s | `pytest` from `backend/` (27 passed, 2 skipped) |
| E2E | The packaged artifact boots, serves UI and API, keeps 404s, exports a PDF, uploads a logo, seeds a clean database | `empaquetar.ps1 -ConExe`, in a clean folder, with `RIGUEL_SIN_NAVEGADOR` set |

## Migration / Rollout

No user data migration is required: the artifact is additive and the legacy copy covers the switch. The
executable stays opt-in until verified on a machine without Python, and only then does `INSTALL.md` lead
with it.

## Open Questions

- [ ] `-ConExe` as a switch on `empaquetar.ps1`, or its own script? (Proposed: a switch, so the frontend build and the port check are not duplicated.)
- [ ] Nuitka stays the fallback; the trigger is Defender flagging it in the field, untestable from here.
