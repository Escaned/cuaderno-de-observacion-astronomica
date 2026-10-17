# Tasks: Ship a Windows executable so users do not need Python

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~630 (unit 1 ~295, unit 2 ~335) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | Unit 1 frozen-ready app -> Unit 2 build and verify the executable |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main (two ordered commits on `main`) |

```text
Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High
```

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | The app becomes frozen-ready: path resolution, programmatic migrations, launcher | PR 1 | Base `main`. No PyInstaller involved, so `pytest` plus a source run verify it |
| 2 | Build and verification pipeline, plus the docs | PR 2 | Base `main`, or PR 1 if chained. Depends on unit 1 |

## Phase 1: Path resolution and migrations (unit 1)

- [x] 1.1 RED: `backend/tests/test_paths.py` covers `is_frozen`, `bundle_root`, `app_dir` and `writable_paths`, frozen and not
- [x] 1.2 GREEN: create `backend/app/core/paths.py`
- [x] 1.3 RED: test that `upgrade_to_head` reaches head and seeds the observatory and the 6 filters
- [x] 1.4 GREEN: create `backend/app/core/migrations.py`, Alembic configured in code, no `alembic.ini`
- [x] 1.5 Point `main.py` `FRONTEND_DIST` at `paths.bundle_root()`
- [x] 1.6 Note in `config.py` that the launcher sets `DATABASE_URL`, `IMAGES_DIR`, `API_HOST`, `API_PORT`

## Phase 2: Launcher (unit 1)

- [x] 2.1 Create `backend/app/core/launcher.py` (was `desktop.py`, see design.md # Amendments): resolve the directories and set the environment variables before importing `app.core.config`
- [x] 2.2 Create `data/imagenes`, and restore the default `logo.jpg` when it is missing
- [x] 2.3 Adopt `backend/riguel.db` into `data/` by copy, only when `data/` has none, and say so
- [x] 2.4 Run the migrations before the server; on failure report the cause and exit
- [x] 2.5 Start uvicorn in-process on loopback, probe `http://127.0.0.1:<port>/health`, open `http://localhost:<port>`
- [x] 2.6 Busy port: reuse a running instance, otherwise report the busy port and how to free it
- [x] 2.7 Confirmed: an executable moved out of its folder dies in the PyInstaller bootloader, before any Python runs. Reworded as documentation
- [x] 2.8 Verify the launcher runs from source (`python -m app.core.launcher`) and writes nothing into the repository

## Phase 3: Packaging (unit 2)

- [x] 3.1 Pin `pyinstaller==6.22.3` in `backend/requirements-dev.txt`
- [x] 3.2 Create `riguel.spec`: one-dir, console, `datas` (frontend/dist, alembic, default logo), `hiddenimports`, `excludes`, `--noupx`
- [x] 3.3 Build once by hand and iterate on missing modules until the executable boots
- [x] 3.4 `empaquetar.ps1`: add the opt-in `-ConExe` switch and the build stage
- [x] 3.5 `empaquetar.ps1`: verify the executable - health, UI, client route, API, API 404, PDF export, logo upload, clean seeded database
- [x] 3.6 Confirm a run without the switch behaves as today

## Phase 4: Documentation (unit 2)

- [x] 4.1 `INSTALL.md`: lead with the executable; SmartScreen warning; keep the folder together; how to bring data over
- [x] 4.2 `DESARROLLO.md`: build steps, why PyInstaller, and the `127.0.0.1` vs `localhost` gotcha

## Phase 5: Verification

- [x] 5.1 `pytest` from `backend/`: all green, including the new tests
- [x] 5.2 `empaquetar.ps1` with no switches: still reports `PAQUETE LISTO Y VERIFICADO`
- [x] 5.3 `empaquetar.ps1 -ConExe`: builds and verifies the executable folder from scratch
- [x] 5.4 Launch the executable with no Python on `PATH`, from a clean folder: it must serve the UI, and the port must be refused from another machine
