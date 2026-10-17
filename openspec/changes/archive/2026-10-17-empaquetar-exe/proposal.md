# Proposal: Ship a Windows executable so users do not need Python

## Intent

Every install failure so far has come from the user's Python, not from the application. The tool
requires 3.12 or 3.13 and fails outright on 3.14, where pip tries to compile `pydantic-core` from
source and needs Rust. Even when it works, the user has to install Python, tick *Add python.exe to
PATH*, run `instalar.bat` and wait.

Ship a folder the user unzips and double-clicks. No Python, no pip, no `.venv`, no Rust.

## Scope

### In Scope

- `desktop.py`: a frozen entry point that resolves writable data next to the executable, brings the
  database up to date (schema **and** seed data), starts the server in-process, opens the browser,
  and shuts down cleanly.
- Frozen-aware resource resolution so the bundled frontend is found under `sys._MEIPASS` instead of
  being derived from `__file__`.
- A PyInstaller spec (one-dir, console window) bundling `frontend/dist`, the Alembic migrations and
  the default logo.
- First-run import of an existing `backend\riguel.db` from a script-based install, because both
  distributions will coexist.
- Extend `empaquetar.ps1` to build **and verify** the executable folder, keeping the current
  script-zip path working.
- Rewrite `INSTALL.md` for the executable and add the build steps to `DESARROLLO.md`.

### Out of Scope

- **Code signing.** An unsigned executable triggers SmartScreen ("unknown publisher"). Documented as
  a known limitation; Nuitka is the fallback if false positives get out of hand.
- **A tray icon or a windowless build.** v1 keeps the console window, which the users already know
  how to close from `arrancar.bat`.
- **Supporting Python 3.14 in the source install.** Separate change; it needs `fastapi >= 0.118.1`
  and `pydantic >= 2.12`, plus a full regression pass.
- **Removing `instalar.bat` / `arrancar.bat`.** They stay as the alternative distribution until the
  executable has been verified on a machine without Python.

## Capabilities

### New Capabilities

- `desktop-launcher`: the frozen entry point. Owns the data directory, first-run bootstrap,
  migrations, port selection, browser opening and shutdown.

### Modified Capabilities

- `frontend-serving`: the built UI MUST be located relative to the bundle when frozen, not relative
  to `__file__`.
- `database-location`: the database and uploaded images move from `backend\` to a `data\` folder next
  to the executable, and MUST still resolve correctly when running from source.
- `distribution`: a second artifact (an executable folder) produced and verified by
  `empaquetar.ps1`.
- `install-docs`: `INSTALL.md` and `DESARROLLO.md` describe the executable; the source install stays
  documented as the alternative.

## Approach

The application has five places that break when frozen. Everything else already works, which is why
this change is scoped to a launcher plus a spec file rather than a rewrite.

| # | Where | What breaks when frozen |
|---|---|---|
| 1 | `backend/app/main.py:16` | `FRONTEND_DIST` is derived from `__file__` with `parents[2]`. Inside a bundle that resolves outside the bundle, so the UI is never served. |
| 2 | `backend/app/main.py:53` | `StaticFiles(directory=settings.images_dir)` runs at import time. If the directory does not exist yet, the process dies on startup. |
| 3 | `backend/app/core/config.py:14,32,7` | `database_url`, `images_dir` and `env_file` are relative to the CWD. It works today only because `arrancar.bat` runs `cd backend`. |
| 4 | `backend/alembic/versions/0001_initial.py` | Holds the seed data (the observatory and the 6 filters). `init_db()` only does `create_all`, which creates tables but seeds nothing. |
| 5 | `backend/alembic/env.py:13` | Appends to `sys.path` and expects an `alembic.ini` next to it. Neither exists in a bundle. |

Plan:

1. Add `backend/app/core/paths.py` with two helpers: the bundle/project root (for read-only bunded
   resources) and the writable application directory (next to `sys.executable` when frozen, `backend/`
   when running from source).
2. Point `main.py` and `config.py` at those helpers. Set the data paths through environment variables
   before `app.core.config` is imported, so the relative defaults stay untouched for development.
3. Add `backend/app/core/migrations.py` that builds the Alembic `Config` in code (`script_location`
   and `sqlalchemy.url` set programmatically, no `alembic.ini`) and runs `upgrade head`.
4. Add `desktop.py`: resolve dirs, create them, restore the default logo, import a legacy database if
   one is found, migrate, start uvicorn in-process (no reload), wait for `/health`, open the browser.
5. Add `riguel.spec` with the data files, hidden imports and exclusions, and build with `--noupx`.
6. Extend `empaquetar.ps1` to also build and verify the executable folder.
7. Update the documentation.

### Rejected alternatives

- **Rely on `create_all` instead of Alembic.** Rejected: it would create an empty schema without the
  observatory or the 6 standard filters, and every existing database would lose its migration path.
- **Keep relative paths and `os.chdir()` into the data directory.** Rejected: `images_dir` is
  `./data/imagenes`, so changing the CWD makes it resolve to `data\data\imagenes`. Setting the paths
  explicitly avoids the whole class of bug.
- **PyInstaller one-file.** Rejected: it unpacks to a temp folder on every launch (2-5s) and gets
  flagged by Defender more often than one-dir.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `desktop.py` | New | Frozen entry point: paths, bootstrap, migrations, server, browser |
| `riguel.spec` | New | PyInstaller build definition (one-dir, console) |
| `backend/app/core/paths.py` | New | Bundle root vs writable app directory |
| `backend/app/core/migrations.py` | New | Runs Alembic programmatically, without `alembic.ini` |
| `backend/app/main.py` | Modified | `FRONTEND_DIST` from the paths helper |
| `backend/app/core/config.py` | Modified | Data paths derived, not CWD-relative |
| `backend/requirements-dev.txt` | Modified | Pinned PyInstaller for builds |
| `empaquetar.ps1` | Modified | New stage: build and verify the executable folder |
| `.gitignore` | Modified | Ignore build output (`build/`, `dist/`) |
| `INSTALL.md` | Modified | Rewritten around the executable |
| `DESARROLLO.md` | Modified | How to build the executable and why PyInstaller |
| `backend/tests/test_paths.py` | New | Unit tests for the path helpers (frozen and not frozen) |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Missing hidden imports at runtime (uvicorn loop/protocol `auto` modules, SQLAlchemy dialects) | High | The from-scratch verification in `empaquetar.ps1` runs the real executable and exercises the UI, the API and a PDF export |
| Windows Defender or SmartScreen flags the executable | Medium | One-dir instead of one-file, `--noupx`, documented. Nuitka is the fallback |
| Alembic fails inside the bundle (`env.py` assumes a CWD and an `.ini`) | Medium | Drive Alembic fully in code and run it before the server starts, so a failure is visible and loud |
| reportlab or pydantic-core data files missing in the bundle | Medium | Explicit PDF-export check in the packaged-artifact verification |
| User moves `Riguel.exe` out of its folder and it stops working | Medium | Documented, and the launcher MUST detect a missing `_internal` and say so in plain language |
| The executable folder is large enough to be awkward to email | Low | One-dir with exclusions; measured and reported by the build |
| Silently breaking the existing script-based install | Low | `instalar.bat`/`arrancar.bat` untouched; the source path keeps working and stays covered by tests |

## Rollback Plan

The change is additive and the source distribution is not modified in behavior, so rollback is a
plain revert:

- `desktop.py`, `riguel.spec`, `paths.py`, `migrations.py` and their tests are new files: delete them.
- The `main.py` and `config.py` edits keep the source behaviour identical; reverting the commits
  restores them exactly.
- `empaquetar.ps1` keeps producing the current script zip by default, so the already-verified
  distribution path is never at risk.
- Existing user data is untouched: the executable writes to its own `data\` folder and never modifies
  a `backend\riguel.db`.

## Dependencies

- PyInstaller 6.22.3. It publishes `py3-none-win_amd64` (version-independent, supports Python
  3.8-3.15), so unlike `pydantic-core` it cannot fail to install on our 3.13.
- `pyinstaller-hooks-contrib` 2026.8, which supplies the reportlab and SQLAlchemy hooks.
- No new runtime dependency for the application itself.

## Success Criteria

- [ ] On a Windows machine with **no Python installed**, unzipping and double-clicking `Riguel.exe`
      opens http://localhost:8000 with the application working
- [ ] First run creates the database with the observatory and the 6 standard filters seeded
- [ ] A PDF export works from the packaged executable
- [ ] Uploading a logo works, and it survives a restart
- [ ] An existing `backend\riguel.db` from a script install is picked up, not ignored
- [ ] Double-clicking a second time opens the browser on the already-running instance instead of
      failing with "Address already in use"
- [ ] `empaquetar.ps1` builds and verifies the executable folder from scratch and fails loudly if the
      packaged application does not work
- [ ] The backend test suite still reports 27 passed, 2 skipped when running from source
- [ ] `INSTALL.md` describes only the executable for end users and explains the SmartScreen warning
