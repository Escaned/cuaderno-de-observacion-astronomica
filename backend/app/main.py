from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core import paths
from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import asociacion, observatorios, filtros, observaciones, export

# The built frontend (created by `npm run build`). When it exists the backend also
# serves the web app, so a normal install needs a single server and no Node.js.
# During development it is ignored: Vite serves the app on its own port.
# Resolved through `paths` so a packaged build finds it inside the bundle: the
# location used to be derived from this file's position, which means nothing once
# the application is frozen.
FRONTEND_DIST = paths.bundle_root() / "frontend" / "dist"

# Paths that must never fall through to the SPA. They belong to the API or to the
# mounted static files, so an unknown one has to stay a plain 404 instead of
# returning index.html with a 200.
RESERVED_PREFIXES = ("api/", "imagenes/")
RESERVED_EXACT = {"docs", "redoc", "openapi.json", "health"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if FRONTEND_DIST.is_dir():
        print(f"[app] Sirviendo el frontend compilado desde {FRONTEND_DIST}")
    else:
        print("[app] Sin frontend compilado: modo desarrollo (usá Vite en :5173)")
    yield
    await close_db()


app = FastAPI(
    title="Riguel Cuaderno de Campo Astronómico",
    description="API para registro de observaciones astronómicas del grupo Riguel",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS (only relevant when the frontend runs on its own port during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for images
app.mount(
    settings.images_url_prefix,
    StaticFiles(directory=settings.images_dir),
    name="imagenes",
)

# Routers
app.include_router(asociacion.router, prefix="/api/v1/asociacion", tags=["Asociacion"])
app.include_router(observatorios.router, prefix="/api/v1/observatorios", tags=["Observatorios"])
app.include_router(filtros.router, prefix="/api/v1/filtros", tags=["Filtros"])
app.include_router(observaciones.router, prefix="/api/v1/observaciones", tags=["Observaciones"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "riguel-cuaderno-api"}


# ---------------------------------------------------------------------------
# Frontend (optional). Registered last on purpose, so every route above wins.
# ---------------------------------------------------------------------------
if FRONTEND_DIST.is_dir():
    _dist = FRONTEND_DIST.resolve()
    _assets = _dist / "assets"
    if _assets.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Serve the built app and let client-side routing handle unknown paths."""
        if full_path in RESERVED_EXACT or full_path.startswith(RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not Found")

        # A real file (favicon, logo, manifest...) is returned as-is. Anything
        # else gets index.html so React Router can resolve the route.
        candidate = (_dist / full_path).resolve()
        if full_path and candidate.is_relative_to(_dist) and candidate.is_file():
            return FileResponse(candidate)

        return FileResponse(_dist / "index.html")
