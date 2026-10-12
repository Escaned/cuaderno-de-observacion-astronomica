## Verification Report

**Change**: riguel-cuaderno-astronomico
**Phase**: 2 — Backend API & Export
**Mode**: Standard (not Strict TDD)
**Date**: 2026-10-12

---

### Completeness

| Metric | Value |
|--------|-------|
| Schemas defined | 6 files (observatorio, filtro, observacion, sesion_captura, calibracion, export) |
| CRUD modules | 5 files (observatorio, filtro, observacion, sesion_captura, calibracion) |
| API routers | 4 files (observatorio, filtros, observaciones, export) |
| Services | 2 files (csv_generator, pdf_generator) |
| Test files | 3 files (test_api, test_models, test_database) |

---

### Build & Tests Execution

**Build**: N/A (Python project, no build step)

**Tests**: 17 passed / 4 failed / 0 skipped

**Failed tests**:
1. `test_filtros_duplicate_nombre_fails` — assert 400 == 201 (duplicate name check fails)
2. `test_observaciones_crud` — `InvalidRequestError: 'Observacion.sesiones_captura' does not support object population`
3. `test_observaciones_filter_by_filtro` — same `InvalidRequestError`
4. `test_observaciones_filter_by_date_range` — same `InvalidRequestError`

**Coverage**: Not measured (no coverage tool configured)

---

### Spec Compliance Matrix

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Observatorio singleton | GET returns/create config | `test_api.py > test_observatorio_get_create` | PASS |
| Observatorio singleton | PUT updates fields | `test_api.py > test_observatorio_update` | PASS |
| Filtros CRUD | Full CRUD cycle | `test_api.py > test_filtros_crud` | PASS |
| Filtros CRUD | Duplicate name rejected | `test_api.py > test_filtros_duplicate_nombre_fails` | FAIL |
| Observaciones CRUD | Create with nested data | `test_api.py > test_observaciones_crud` | FAIL |
| Observaciones CRUD | Read all | (covered by above) | FAIL |
| Observaciones CRUD | Read detail | (covered by above) | FAIL |
| Observaciones CRUD | Update | (covered by above) | FAIL |
| Observaciones CRUD | Duplicate | (covered by above) | FAIL |
| Observaciones CRUD | Delete | (covered by above) | FAIL |
| Observaciones filtering | Filter by filtro_id | `test_api.py > test_observaciones_filter_by_filtro` | FAIL |
| Observaciones filtering | Filter by date range | `test_api.py > test_observaciones_filter_by_date_range` | FAIL |
| Export CSV | Single table export | `test_api.py > test_export_csv_single_table` | PASS |
| Export CSV | All tables ZIP | `test_api.py > test_export_csv_all_zip` | PASS |
| Health | Health check | `test_api.py > test_health_check` | PASS |
| Models | Singleton constraint | `test_models.py > test_observatorio_singleton` | PASS |
| Models | Filtro CRUD | `test_models.py > test_filtro_crud` | PASS |
| Models | Filtro unique nombre | `test_models.py > test_filtro_unique_nombre` | PASS |
| Models | Seeing constraint | `test_models.py > test_observacion_with_seeing_constraint` | PASS |
| Models | Seeing out of range | `test_models.py > test_observacion_seeing_out_of_range_fails` | PASS |
| Models | SesionCaptura relationship | `test_models.py > test_sesion_captura_relationship` | PASS |
| Models | Calibracion types | `test_models.py > test_calibracion_types` | PASS |
| Models | Cascade delete observacion | `test_models.py > test_cascade_delete_observacion_removes_sesiones` | PASS |
| Models | Cascade delete sesion | `test_models.py > test_cascade_delete_sesion_removes_calibracion` | PASS |
| Database | Init creates tables | `test_database.py > test_init_db_creates_tables` | PASS |
| Database | Get session | `test_database.py > test_get_session_yields_session` | PASS |

**Compliance summary**: 18/22 scenarios compliant

---

### Correctness (Static — Structural Evidence)

| Requirement | Status | Notes |
|------------|--------|-------|
| Schemas match models | PASS | All Pydantic schemas correctly mirror SQLAlchemy model fields |
| CRUD uses correct columns | PASS | All column names match model definitions |
| API routers in main.py | PASS | All 4 routers included with correct prefixes |
| REST conventions | PASS | GET/POST/PUT/DELETE follow standard patterns |
| Nested create/update | PASS | Observacion create handles nested sesiones_captura + calibraciones |
| Cascade deletes | PASS | Proper cascade configuration in models |
| Export functionality | PASS | CSV (single + ZIP) and PDF (night + campaign) implemented |

---

### Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| Async SQLAlchemy | PASS | All CRUD uses AsyncSession |
| Pydantic v2 schemas | PASS | Uses `model_config = ConfigDict(from_attributes=True)` |
| Singleton observatorio | PASS | CheckConstraint + get_or_create pattern |
| Nested observacion create | PASS | Properly handles sesiones_captura + calibraciones nesting |
| CSV export as ZIP for all tables | PASS | Implemented in csv_generator |
| PDF via weasyprint | PASS | Night and campaign reports implemented |

---

### Issues Found

**CRITICAL** (must fix before archive):

1. **`selectinload` incompatible with `lazy="dynamic"`** — `app/models/observacion.py` line 27 defines `sesiones_captura` with `lazy="dynamic"`, but `app/crud/observacion.py` lines 15 and 37 use `selectinload(Observacion.sesiones_captura)`. SQLAlchemy raises `InvalidRequestError` because dynamic relationships cannot be eagerly loaded. This breaks ALL observacion create/read/update operations.
   - **Fix**: Either change `lazy="dynamic"` to `lazy="select"` in the model, or remove `selectinload` from CRUD queries and access relationships lazily.

2. **`test_filtros_duplicate_nombre_fails` fails** — The test creates a filtro named "DupTest" and expects 201, but gets 400. The API tests use the real `riguel.db` database (not isolated), so previous test runs have already created this filtro. The test is not idempotent.
   - **Fix**: Use unique names per run, or use the temp database fixture, or clean up after test.

**WARNING** (should fix):

3. **`datetime.utcnow()` deprecation** — `app/models/observacion.py` lines 22-23 use `datetime.utcnow()` which is deprecated in Python 3.12+. Should use `datetime.now(timezone.utc)`.

4. **Duplicate schema definitions** — `SesionCapturaBase`, `CalibracionBase`, etc. are defined in both `app/schemas/observacion.py` and `app/schemas/sesion_captura.py`/`app/schemas/calibracion.py`. The `__init__.py` exports both with V2 suffixes, which is confusing.

5. **Missing dedicated routers for sesion_captura and calibracion** — CRUD functions exist but no API endpoints expose them directly. Only accessible through observaciones nesting.

6. **Test isolation issue** — API tests share the real `riguel.db` database, causing test pollution between runs. The `db_session` fixture in conftest uses a temp file but is not used by `test_api.py`.

7. **RuntimeWarning in test_database.py** — `coroutine method 'aclose' of 'get_session' was never awaited` — the test breaks out of the async generator without proper cleanup.

**SUGGESTION** (nice to have):

8. Add pagination metadata (total count) to list endpoints
9. Add input validation for `direccion_viento` values (should be like "N", "S", "E", "O", etc.)
10. Consider adding `selectinload` for `Observacion.filtro` in the list endpoint to avoid N+1 queries

---

### Verdict
**FAIL**

The `selectinload`/`lazy="dynamic"` incompatibility is a critical runtime error that breaks all observacion CRUD operations. The observaciones API is completely non-functional in its current state. The duplicate filtro test also fails due to test isolation issues. These must be fixed before the change can be considered complete.
