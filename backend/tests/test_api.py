import pytest
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_observatorio_get_create(client):
    """Test GET /api/v1/observatorio returns observatorio (auto-creates from settings)."""
    resp = await client.get("/api/v1/observatorio")
    assert resp.status_code == 200
    data = resp.json()
    assert "nombre" in data
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_observatorio_update(client):
    """Test PUT /api/v1/observatorio updates fields."""
    resp = await client.put(
        "/api/v1/observatorio",
        json={"altitud_msnm": 700.0},
    )
    assert resp.status_code == 200
    assert resp.json()["altitud_msnm"] == 700.0


@pytest.mark.asyncio
async def test_filtros_crud(client):
    """Test full CRUD for filtros."""
    # Create
    resp = await client.post(
        "/api/v1/filtros",
        json={
            "nombre": "TestL",
            "descripcion": "Test Luminance",
            "onda_central_nm": None,
            "orden": 10,
            "activo": True,
        },
    )
    assert resp.status_code == 201
    filtro_id = resp.json()["id"]

    # Read all
    resp = await client.get("/api/v1/filtros")
    assert resp.status_code == 200
    assert any(f["id"] == filtro_id for f in resp.json())

    # Update
    resp = await client.put(
        f"/api/v1/filtros/{filtro_id}",
        json={"descripcion": "Updated description"},
    )
    assert resp.status_code == 200
    assert resp.json()["descripcion"] == "Updated description"

    # Delete
    resp = await client.delete(f"/api/v1/filtros/{filtro_id}")
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/api/v1/filtros/{filtro_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_filtros_duplicate_nombre_fails(client):
    """Test that duplicate filtro names are rejected."""
    import time
    body = {"nombre": f"DupTest_{int(time.time())}", "orden": 1}
    resp = await client.post("/api/v1/filtros", json=body)
    assert resp.status_code == 201

    resp2 = await client.post("/api/v1/filtros", json=body)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_observaciones_crud(client):
    """Test full CRUD for observaciones with nested data."""
    # Create
    resp = await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M42",
            "fecha_hora_utc": "2026-10-10T22:00:00Z",
            "seeing": 3,
            "temperatura": 15.0,
            "humedad": 60,
            "sesiones_captura": [
                {
                    "filtro_id": 1,
                    "tiempo_exposicion_seg": 300.0,
                    "num_subs": 20,
                    "binning": 1,
                    "calibraciones": [
                        {"tipo": "dark", "count": 10, "tiempo_exposicion_seg": 300.0},
                        {"tipo": "flat", "count": 20, "filtro_id": 1},
                        {"tipo": "bias", "count": 50},
                        {"tipo": "darkflat", "count": 15},
                    ],
                }
            ],
        },
    )
    assert resp.status_code == 201
    obs_id = resp.json()["id"]
    assert resp.json()["objeto"] == "M42"

    # Read all
    resp = await client.get("/api/v1/observaciones")
    assert resp.status_code == 200
    assert any(o["id"] == obs_id for o in resp.json())

    # Read detail
    resp = await client.get(f"/api/v1/observaciones/{obs_id}")
    assert resp.status_code == 200
    assert resp.json()["objeto"] == "M42"

    # Update
    resp = await client.put(
        f"/api/v1/observaciones/{obs_id}",
        json={"seeing": 4},
    )
    assert resp.status_code == 200
    assert resp.json()["seeing"] == 4

    # Duplicate
    resp = await client.post(f"/api/v1/observaciones/{obs_id}/duplicate")
    assert resp.status_code == 200
    assert resp.json()["objeto"] == "M42"
    assert resp.json()["id"] != obs_id

    # Delete
    resp = await client.delete(f"/api/v1/observaciones/{obs_id}")
    assert resp.status_code == 204

    # Verify deleted
    resp = await client.get(f"/api/v1/observaciones/{obs_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_observaciones_filter_by_filtro(client):
    """Test filtering observations by filtro_id."""
    # Create an observation with filtro_id=1
    resp = await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "NGC7000",
            "fecha_hora_utc": "2026-10-10T23:00:00Z",
            "seeing": 2,
            "filtro_id": 1,
            "sesiones_captura": [],
        },
    )
    assert resp.status_code == 201

    # Filter by filtro_id=1
    resp = await client.get("/api/v1/observaciones?filtro_id=1")
    assert resp.status_code == 200
    assert all(o["filtro_id"] == 1 for o in resp.json())


@pytest.mark.asyncio
async def test_observaciones_filter_by_date_range(client):
    """Test filtering observations by date range."""
    # Create observations on different dates
    await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M31",
            "fecha_hora_utc": "2026-10-05T22:00:00Z",
            "seeing": 3,
            "sesiones_captura": [],
        },
    )
    await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M33",
            "fecha_hora_utc": "2026-10-15T22:00:00Z",
            "seeing": 3,
            "sesiones_captura": [],
        },
    )

    # Filter by date range
    resp = await client.get(
        "/api/v1/observaciones?fecha_desde=2026-10-01T00:00:00Z&fecha_hasta=2026-10-10T00:00:00Z"
    )
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_export_csv_single_table(client):
    """Test CSV export for a single table."""
    resp = await client.get("/api/v1/export/csv?tabla=filtros")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_export_csv_all_zip(client):
    """Test CSV export for all tables (returns ZIP)."""
    resp = await client.get("/api/v1/export/csv?tabla=all")
    assert resp.status_code == 200
    assert "application/zip" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"