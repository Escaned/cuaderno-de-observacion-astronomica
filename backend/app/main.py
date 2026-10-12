from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db, close_db
from app.api.v1 import observatorio, filtros, observaciones, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_db()


app = FastAPI(
    title="Riguel Cuaderno de Campo Astronómico",
    description="API para registro de observaciones astronómicas del grupo Riguel",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
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
app.include_router(observatorio.router, prefix="/api/v1/observatorio", tags=["Observatorio"])
app.include_router(filtros.router, prefix="/api/v1/filtros", tags=["Filtros"])
app.include_router(observaciones.router, prefix="/api/v1/observaciones", tags=["Observaciones"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "riguel-cuaderno-api"}