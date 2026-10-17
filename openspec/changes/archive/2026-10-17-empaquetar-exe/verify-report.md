# Verification report: empaquetar-exe

**Verdict: PASS, with warnings.** Every requirement is implemented and both artifacts were exercised
end to end. Five spec scenarios have no automated coverage, and three claims could not be tested on
this machine.

## Evidence base

| What was run | Result |
|---|---|
| `pytest` from `backend/` | 60 collected, **58 passed, 2 skipped** (baseline was 27/2) |
| `npm test -- --run` from `frontend/` | **22 passed** |
| `empaquetar.ps1` with no switches | exit 0, `PAQUETE LISTO Y VERIFICADO`, steps 0/4..4/4 |
| `empaquetar.ps1 -SoloEmpaquetar -ConExe` | exit 0, **14 of 14 executable checks green** |
| Build by hand (`pyinstaller riguel.spec`) | boots on the first attempt |
| Artifacts produced | zip 106.9 MB, `dist\Riguel\` 54.6 MB, exe zip 32.0 MB |

The 2 skips are pre-existing `async def` tests in older files with no `@pytest.mark.asyncio`. The new
`async` test in `test_launcher.py` does carry the marker and passes.

## resource-resolution - 4 requirements, 8 scenarios: all verified

| Scenario | Evidence | Verdict |
|---|---|---|
| Frozen application serves the UI | exe run: `/` 200 and `/observaciones/123` 200, served from `_internal\frontend\dist`; `test_frontend_dist_is_inside_the_bundle_when_frozen` | PASS |
| Development is unaffected | `test_frontend_dist_from_source_is_the_built_frontend_in_the_repository`; the source launcher run served the same `frontend/dist` | PASS |
| No built frontend available | implemented in `main.py` (prints "Sin frontend compilado: modo desarrollo" and starts anyway) and observed in the logs - **no test** | WARNING |
| Launched from a different working directory | in the `-ConExe` run the process inherited the repository root as its working directory and still wrote to its own `data\`; `git status` afterwards shows no stray file | PASS |
| Running from source keeps today's behaviour | `test_writable_paths_from_source_keep_the_historical_layout`; the real source run left `backend/riguel.db` byte-identical | PASS |
| Images directory absent on a cold start | clean-folder run created `data\imagenes\`, restored the logo, `/imagenes/logo.jpg` 200 | PASS |
| Static mount cannot crash the process | same run: the process stayed up; `_prepare_directories` runs before the import | PASS |
| Unknown API route | asserted in the verification: `/api/v1/noexiste` 404, not the SPA | PASS |
| Known API route | `/api/v1/observatorio` 200 with the seeded JSON | PASS |

## desktop-launcher - 8 requirements, 12 scenarios: verified except four

| Scenario | Evidence | Verdict |
|---|---|---|
| First run creates the data directory | clean-folder run: `data\riguel.db` and `data\imagenes\` existed before the server answered | PASS |
| State survives an upgrade | verified across a **restart**, not across replacing the folder with a newer build | SUGGESTION |
| Not reachable from another machine | bound to `127.0.0.1` only (asserted: no `0.0.0.0`, no `::`). No second machine was available to try | SUGGESTION |
| Fresh install is seeded | observatorio `Riguel`, `logo.jpg`, 6 filters, revision `0003`, 0 observations | PASS |
| Existing database is only updated | `test_upgrade_to_head_does_not_duplicate_the_seed`, `..._applies_every_migration` | PASS |
| Migration failure stops the launcher | implemented in `_migrate`, and nothing tests it: no test calls `run()` or `main()` | **WARNING** |
| Legacy database found | end to end: copied to `data\`, original still in place. The "says so in plain language" half is not asserted by any test | PASS / SUGGESTION |
| Both databases exist | end to end: the one in use won, the other was not overwritten | PASS |
| The application is already running | only `is_this_application`'s recognition is tested; the branch that reuses the instance is not | **WARNING** |
| The port is taken by something else | not tested | **WARNING** |
| Normal start | the IPv4 probe is tested (`test_probes_the_server_over_ipv4_and_opens_localhost`); the browser opening itself was never exercised, by design | SUGGESTION |
| Automation opt-out | used by every automated run of both artifacts | PASS |
| Unexpected failure inside the launcher | `main()` has the handler, and nothing tests it | **WARNING** |
| Executable separated from its folder | **confirmed against the real build** (`[PYI-19812:ERROR] Failed to load Python DLL`, exit -1) and reworded as documentation, because the bootloader dies before any Python runs | PASS |

## distribution - 5 requirements, 11 scenarios: verified except two

| Scenario | Evidence | Verdict |
|---|---|---|
| Default packaging run | exit 0 and `PAQUETE LISTO Y VERIFICADO`; the ZIP was installed and booted from scratch | PASS |
| Port already in use | pre-existing behaviour, untouched by this change | PASS |
| Executable build requested | `dist\Riguel\` produced; `pyinstaller==6.22.3` pinned | PASS |
| Toolchain missing | the message and the exit path exist in the script; not tested live | SUGGESTION |
| Packaged application serves the UI and the API | 6 routes asserted 200, unknown API route 404 | PASS |
| PDF export | 61 KB, `application/pdf` | PASS |
| Logo upload | stored under `data\` and still served after a restart (`logo_9535550d2db0.jpg`) | PASS |
| A failure fails the build | **observed twice for real**: the filters and the PDF failures both ended in exit 1 and no success banner | PASS |
| Clean artifact | the ZIP is asserted (`node_modules`, `.venv`, `riguel.db` absent; `frontend/dist` present). The executable folder is asserted for what it must contain, not for the absence of dev packages | SUGGESTION |
| A non-technical user reads the guide | by inspection: the executable is the only install path and nothing in it needs Python, pip, a terminal or editing a file | PASS |
| Data migration is documented | a numbered 4-step procedure, including the images folder - which the launcher does **not** adopt, verified in the code | PASS |

## Findings

### CRITICAL

None.

### WARNING (4)

All four are branches of `launcher.py` reached only through `run()` and `main()`, which the test file
does not exercise: it tests the pure functions around them. The behaviour is implemented and readable;
it is simply not proven.

1. `Migration failure stops the launcher` - spec scenario, no test.
2. `The application is already running` - spec scenario, no test.
3. `The port is taken by something else` - spec scenario, no test.
4. `Unexpected failure inside the launcher` - spec scenario, no test.

### WARNING (1, different in kind)

5. `No built frontend available` - the behaviour exists and was seen in the logs, but no test pins it.
   This one is a test gap rather than an untested branch of the launcher.

### SUGGESTION (5)

- "State survives an upgrade" was verified across a restart rather than across a folder replacement.
- Loopback-only was verified by the bind address, which is strong but not the same as trying from a
  second machine.
- The adoption message ("Encontre la base de datos de una instalacion anterior...") is not asserted.
- The browser auto-open has never been exercised end to end, because the only way to automate a run is
  to suppress it. Manually, from source, it was seen to work.
- The executable folder is not asserted to be free of development packages.

## Additions made during apply, beyond the plan

- The PDF export check creates an observation first. The endpoint legitimately refuses an empty night,
  so the check could not pass any other way, and the write path is a real risk in a frozen build.
- Two real bugs were found by the verification itself: a PowerShell 5.1 array quirk in the check code
  (documented in `DESARROLLO.md`) and the fact that the check had to use `/count` endpoints.
- Task 2.7 changed the spec instead of the code, after the real build confirmed the bootloader
  behaviour.

## Conclusion

The change does what it claims: the application runs as a Windows executable with no Python, on
loopback only, with its state next to the executable, seeded by the migrations, adopting an earlier
install's database, and the script distribution keeps working exactly as before.

The four launcher warnings are the main outstanding debt: they are exactly the paths a user hits when
something is already wrong (database locked, port busy), which is when a clear message matters most.
They are worth their own small change, since `run()` is only testable if the launcher is refactored to
take its collaborators as arguments.
