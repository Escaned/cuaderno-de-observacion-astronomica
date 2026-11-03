import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
import base64
import re
import tempfile
import zlib
import os

from app.main import app
from app.core.database import Base, get_session
from app.models import Asociacion, Observatorio, Filtro, Observacion, SesionCaptura, Calibracion


# Test database URL - file-based SQLite for shared access across connections
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix='.db', prefix='test_')
os.close(_test_db_fd)
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{_test_db_path}"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=NullPool,
    connect_args={"check_same_thread": False},
)

test_async_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def test_get_session() -> AsyncSession:
    async with test_async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def test_init_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Seed asociacion
        await conn.execute(
            Asociacion.__table__.insert().values(
                id=1, nombre="Riguel", logo_path="logo.jpg"
            ).prefix_with("OR IGNORE")
        )
        # Seed observatorio predeterminado solo si la tabla esta vacia: otros
        # tests pueden haber cambiado cual es el predeterminado.
        cantidad = (await conn.exec_driver_sql("SELECT COUNT(*) FROM observatorio")).scalar_one()
        if cantidad == 0:
            await conn.execute(
                Observatorio.__table__.insert().values(
                    id=1, nombre="Riguel", latitud=40.4168, longitud=-3.7038,
                    altitud_msnm=650.0, zona_horaria="Europe/Madrid",
                    color="#4d48e2", es_predeterminado=1,
                )
            )
        # Seed filtros
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="L", descripcion="Luminancia", onda_central_nm=None, orden=1, activo=1
            ).prefix_with("OR IGNORE")
        )
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="R", descripcion="Rojo", onda_central_nm=656, orden=2, activo=1
            ).prefix_with("OR IGNORE")
        )
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="G", descripcion="Verde", onda_central_nm=540, orden=3, activo=1
            ).prefix_with("OR IGNORE")
        )
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="B", descripcion="Azul", onda_central_nm=450, orden=4, activo=1
            ).prefix_with("OR IGNORE")
        )
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="Ha", descripcion="H-alpha", onda_central_nm=656.3, orden=5, activo=1
            ).prefix_with("OR IGNORE")
        )
        await conn.execute(
            Filtro.__table__.insert().values(
                nombre="OIII", descripcion="Oxigeno III", onda_central_nm=500.7, orden=6, activo=1
            ).prefix_with("OR IGNORE")
        )


@pytest_asyncio.fixture
async def client():
    """Create a test client with in-memory database."""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from app.api.v1 import asociacion, observatorios, filtros, observaciones, export
    from contextlib import asynccontextmanager

    # Initialize database for this test
    await test_init_db()

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        yield
        await test_engine.dispose()

    test_app = FastAPI(
        title="Riguel Cuaderno de Campo Astronómico (Test)",
        description="API para registro de observaciones astronómicas del grupo Riguel",
        version="1.0.0",
        lifespan=test_lifespan,
    )

    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    test_app.include_router(asociacion.router, prefix="/api/v1/asociacion", tags=["Asociacion"])
    test_app.include_router(observatorios.router, prefix="/api/v1/observatorios", tags=["Observatorios"])
    test_app.include_router(filtros.router, prefix="/api/v1/filtros", tags=["Filtros"])
    test_app.include_router(observaciones.router, prefix="/api/v1/observaciones", tags=["Observaciones"])
    test_app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

    @test_app.get("/health")
    async def health_check():
        return {"status": "ok", "service": "riguel-cuaderno-api"}

    # Override the get_session dependency
    test_app.dependency_overrides[get_session] = test_get_session

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    test_app.dependency_overrides.clear()


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_db():
    yield
    # Clean up test database file after all tests
    if os.path.exists(_test_db_path):
        os.unlink(_test_db_path)


@pytest.mark.asyncio
async def test_asociacion_get_create(client):
    """Test GET /api/v1/asociacion returns the association (auto-creates from settings)."""
    resp = await client.get("/api/v1/asociacion")
    assert resp.status_code == 200
    data = resp.json()
    assert "nombre" in data
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_asociacion_update(client):
    """Test PUT /api/v1/asociacion updates fields."""
    resp = await client.put(
        "/api/v1/asociacion",
        json={"nombre": "Asociacion de prueba"},
    )
    assert resp.status_code == 200
    assert resp.json()["nombre"] == "Asociacion de prueba"

    # Restore the seeded name so later tests keep a predictable state
    await client.put("/api/v1/asociacion", json={"nombre": "Riguel"})


@pytest.mark.asyncio
async def test_observatorios_crud_y_predeterminado(client):
    """Create a second observatory, make it the default and list both."""
    resp = await client.post(
        "/api/v1/observatorios",
        json={
            "nombre": "Observatorio Norte",
            "latitud": 42.1,
            "longitud": -1.2,
            "altitud_msnm": 850,
            "color": "#0f766e",
        },
    )
    assert resp.status_code == 201
    nuevo_id = resp.json()["id"]
    assert resp.json()["es_predeterminado"] is False

    resp = await client.post(f"/api/v1/observatorios/{nuevo_id}/predeterminado")
    assert resp.status_code == 200
    assert resp.json()["es_predeterminado"] is True

    resp = await client.get("/api/v1/observatorios")
    assert resp.status_code == 200
    observatorios = resp.json()
    assert len(observatorios) >= 2
    assert observatorios[0]["id"] == nuevo_id
    assert sum(1 for o in observatorios if o["es_predeterminado"]) == 1

    # The last observatory cannot be deleted
    for observatorio in observatorios[1:]:
        resp = await client.delete(f"/api/v1/observatorios/{observatorio['id']}")
        assert resp.status_code == 204

    resp = await client.delete(f"/api/v1/observatorios/{nuevo_id}")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_observaciones_se_asignan_al_predeterminado(client):
    """An observation without observatorio_id lands on the default observatory."""
    resp = await client.get("/api/v1/observatorios")
    predeterminado = next(o for o in resp.json() if o["es_predeterminado"])

    resp = await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M51",
            "fecha_hora_utc": "2026-10-11T22:00:00Z",
            "fwhm": 2.2,
            "sesiones_captura": [],
        },
    )
    assert resp.status_code == 201
    assert resp.json()["observatorio_id"] == predeterminado["id"]

    resp = await client.get(f"/api/v1/observaciones?observatorio_id={predeterminado['id']}")
    assert resp.status_code == 200
    assert any(o["objeto"] == "M51" for o in resp.json())


# Minimal valid 1x1 PNG
_PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


@pytest.mark.asyncio
async def test_observatorio_logo_upload(client, tmp_path, monkeypatch):
    """Test uploading a valid PNG logo stores the file and updates logo_path."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "images_dir", str(tmp_path))

    resp = await client.post(
        "/api/v1/asociacion/logo",
        files={"file": ("logo.png", _PNG_1X1, "image/png")},
    )
    assert resp.status_code == 200
    logo_path = resp.json()["logo_path"]
    assert logo_path.startswith("logo_")
    assert logo_path.endswith(".png")
    assert (tmp_path / logo_path).is_file()


@pytest.mark.asyncio
async def test_observatorio_logo_rejects_non_image(client, tmp_path, monkeypatch):
    """Test that a file with a valid extension but non-image bytes is rejected."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "images_dir", str(tmp_path))

    resp = await client.post(
        "/api/v1/asociacion/logo",
        files={"file": ("logo.png", b"this is definitely not a png", "image/png")},
    )
    assert resp.status_code == 400
    assert not list(tmp_path.glob("logo_*"))


@pytest.mark.asyncio
async def test_observatorio_logo_rejects_bad_extension(client, tmp_path, monkeypatch):
    """Test that unsupported extensions (e.g. gif) are rejected."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "images_dir", str(tmp_path))

    resp = await client.post(
        "/api/v1/asociacion/logo",
        files={"file": ("logo.gif", b"GIF89a" + b"\x00" * 16, "image/gif")},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_observatorio_logo_delete(client, tmp_path, monkeypatch):
    """Test deleting the logo clears logo_path and removes the uploaded file."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "images_dir", str(tmp_path))

    up = await client.post(
        "/api/v1/asociacion/logo",
        files={"file": ("logo.png", _PNG_1X1, "image/png")},
    )
    assert up.status_code == 200
    uploaded = tmp_path / up.json()["logo_path"]
    assert uploaded.is_file()

    resp = await client.delete("/api/v1/asociacion/logo")
    assert resp.status_code == 200
    assert resp.json()["logo_path"] is None
    assert not uploaded.exists()


@pytest.mark.asyncio
async def test_night_pdf_embeds_logo(client, tmp_path, monkeypatch):
    """Test the night PDF embeds the configured logo as an image XObject."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "images_dir", str(tmp_path))

    up = await client.post(
        "/api/v1/asociacion/logo",
        files={"file": ("logo.png", _PNG_1X1, "image/png")},
    )
    assert up.status_code == 200

    await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M13",
            "fecha_hora_utc": "2026-08-20T22:00:00Z",
            "fwhm": 2.0,
            "sesiones_captura": [],
        },
    )

    resp = await client.get("/api/v1/export/pdf/noche?fecha=2026-08-20T22:00:00Z")
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")
    assert b"/Subtype /Image" in resp.content


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
            "fwhm": 2.5,
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
        json={"fwhm": 3.2},
    )
    assert resp.status_code == 200
    assert resp.json()["fwhm"] == 3.2

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
            "fwhm": 3.5,
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
            "fwhm": 2.5,
            "sesiones_captura": [],
        },
    )
    await client.post(
        "/api/v1/observaciones",
        json={
            "objeto": "M33",
            "fecha_hora_utc": "2026-10-15T22:00:00Z",
            "fwhm": 2.5,
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
    """Test CSV export for all tables (returns combined CSV)."""
    resp = await client.get("/api/v1/export/csv?tabla=all")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract visible text from a ReportLab PDF.

    ReportLab encodes content streams with /Filter [ /ASCII85Decode /FlateDecode ],
    so decode ASCII85 first, then Flate, then pull the (...) Tj string operands.
    """
    chunks = []
    for raw in re.findall(rb"stream\r?\n(.*?)endstream", pdf_bytes, re.S):
        raw = raw.strip(b"\r\n")
        if raw.startswith(b"<") or raw.endswith(b"~>"):
            try:
                raw = base64.a85decode(raw, adobe=True)
            except Exception:
                pass
        try:
            raw = zlib.decompress(raw)
        except Exception:
            pass
        for match in re.finditer(rb"\((?:[^()\\]|\\.)*\)", raw):
            text = match.group(0)[1:-1]
            text = text.replace(b"\\(", b"(").replace(b"\\)", b")").replace(b"\\\\", b"\\")
            chunks.append(text.decode("latin-1"))
    return " ".join(chunks)


@pytest.mark.asyncio
async def test_export_pdf_campana_includes_fwhm(client):
    """Test the campaign PDF shows the average FWHM per object."""
    for objeto, fecha, fwhm in [
        ("M42", "2026-09-10T22:00:00Z", 2.5),
        ("M42", "2026-09-11T22:00:00Z", 3.5),
        ("NGC7000", "2026-09-12T22:00:00Z", 1.8),
    ]:
        resp = await client.post(
            "/api/v1/observaciones",
            json={
                "objeto": objeto,
                "fecha_hora_utc": fecha,
                "fwhm": fwhm,
                "sesiones_captura": [],
            },
        )
        assert resp.status_code == 201

    resp = await client.get(
        "/api/v1/export/pdf/campana?fecha_desde=2026-09-01T00:00:00Z&fecha_hasta=2026-09-30T23:59:59Z"
    )
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]

    text = _extract_pdf_text(resp.content)
    assert "FWHM medio" in text
    assert '3.0"' in text  # mean of 2.5 and 3.5
    assert '1.8"' in text  # single observation for NGC7000
    assert "M42" in text
    assert "NGC7000" in text


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"