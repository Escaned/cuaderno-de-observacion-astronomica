# Proposal: Seeing to FWHM (arcseconds)

## Intent
Replace the qualitative 1-5 seeing scale with quantitative FWHM measurements in arcseconds (float). This provides scientifically accurate data for astronomical observations.

## Scope

### In Scope
- Database migration: `seeing` (INTEGER 1-5) → `fwhm` (FLOAT, arcseconds)
- Backend: SQLAlchemy model, Pydantic schemas, CRUD, tests, CSV/PDF generators
- Frontend: Types, format utils, wizard components, pages, tests
- Validation: reasonable FWHM range (e.g., 0.5–10.0 arcseconds)

### Out of Scope
- Historical data conversion (1-5 → arcseconds) — requires manual review
- Image analysis integration (auto-measure FWHM from frames)

## Capabilities

### Modified Capabilities
- `observation-model`: field type/validation changes
- `observation-api`: request/response schema changes
- `observation-ui`: input/display changes

## Approach
1. Create Alembic migration adding `fwhm` column, backfill from `seeing` (rough mapping), drop `seeing`
2. Update all backend layers (model → schema → CRUD → services → tests)
3. Update all frontend layers (types → utils → components → pages → tests)
4. Update CSV/PDF exports

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `backend/alembic/versions/` | New | Migration script |
| `backend/app/models/observacion.py` | Modified | Column type, constraints |
| `backend/app/schemas/observacion.py` | Modified | Field type, validation |
| `backend/app/crud/observacion.py` | Modified | Field references |
| `backend/app/services/csv_generator.py` | Modified | Column name, formatting |
| `backend/app/services/pdf_generator.py` | Modified | Display label |
| `backend/tests/test_models.py` | Modified | Test values, assertions |
| `backend/tests/test_api.py` | Modified | Request payloads, assertions |
| `frontend/src/types/index.ts` | Modified | Type definitions |
| `frontend/src/utils/format.ts` | Modified | New FWHM formatting |
| `frontend/src/utils/format.test.ts` | Modified | Test updates |
| `frontend/src/components/wizard/NightHeader.tsx` | Modified | Input field |
| `frontend/src/components/wizard/WizardLayout.tsx` | Modified | Form state, validation |
| `frontend/src/pages/*.tsx` | Modified | Display components |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Data loss during migration | Medium | Backup DB, test migration on copy first |
| Frontend validation gaps | Medium | Add client + server validation for 0.5–10.0 range |
| Test breakage | High | Update all tests in same PR |

## Rollback Plan
- Revert migration: `alembic downgrade -1`
- Revert code changes via git
- Restore DB from backup if needed

## Dependencies
- Alembic for migration
- No external dependencies

## Success Criteria
- [ ] Migration runs cleanly on dev DB
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Wizard accepts float input (e.g., 2.3)
- [ ] Dashboard/Detail/List display FWHM with "arcsec" unit
- [ ] CSV/PDF exports show FWHM column