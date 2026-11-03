from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_session
from app.crud import (
    get_or_create_asociacion,
    update_asociacion,
)
from app.schemas import AsociacionUpdate, AsociacionRead

router = APIRouter()

MAX_LOGO_BYTES = 2 * 1024 * 1024

# file suffix -> normalized extension
ALLOWED_LOGO_SUFFIXES = {".jpg": "jpg", ".jpeg": "jpg", ".png": "png"}

_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Prefix reserved for uploaded logos, so we never delete the bundled default
_UPLOAD_PREFIX = "logo_"


def _images_dir() -> Path:
    """Directory holding the static images, resolved the same way StaticFiles does."""
    return Path(settings.images_dir)


def _image_extension(data: bytes) -> str | None:
    """Return 'jpg' or 'png' when the bytes are a real JPEG/PNG, else None."""
    if data.startswith(_JPEG_MAGIC):
        return "jpg"
    if data.startswith(_PNG_MAGIC):
        return "png"
    return None


def _remove_uploaded_logos(images_dir: Path) -> None:
    """Delete previously uploaded logos. Never touches logo.jpg or .gitkeep."""
    if not images_dir.is_dir():
        return
    for old in images_dir.glob(f"{_UPLOAD_PREFIX}*"):
        if old.is_file() and old.suffix.lower() in (".jpg", ".jpeg", ".png"):
            old.unlink(missing_ok=True)


@router.get("", response_model=AsociacionRead)
async def read_asociacion(db: AsyncSession = Depends(get_session)):
    """Get the association configuration (name and logo)."""
    return await get_or_create_asociacion(db)


@router.put("", response_model=AsociacionRead)
async def update_asociacion_endpoint(
    obj_in: AsociacionUpdate, db: AsyncSession = Depends(get_session)
):
    """Update the association configuration."""
    asociacion = await get_or_create_asociacion(db)
    return await update_asociacion(db, asociacion, obj_in)


@router.post("/logo", response_model=AsociacionRead)
async def upload_asociacion_logo(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    """Upload the association logo (JPG or PNG, up to 2 MB)."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_LOGO_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato no soportado. Usá JPG o PNG.",
        )

    content = await file.read()

    if len(content) > MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=413,
            detail="El logo no puede superar los 2 MB.",
        )

    extension = _image_extension(content)
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo no es una imagen JPG o PNG válida.",
        )

    images_dir = _images_dir()
    images_dir.mkdir(parents=True, exist_ok=True)

    _remove_uploaded_logos(images_dir)

    # Unique name per upload: avoids collisions and busts the browser cache
    filename = f"{_UPLOAD_PREFIX}{uuid4().hex[:12]}.{extension}"
    (images_dir / filename).write_bytes(content)

    asociacion = await get_or_create_asociacion(db)
    return await update_asociacion(db, asociacion, AsociacionUpdate(logo_path=filename))


@router.delete("/logo", response_model=AsociacionRead)
async def delete_asociacion_logo(db: AsyncSession = Depends(get_session)):
    """Remove the association logo, leaving the association without an image."""
    asociacion = await get_or_create_asociacion(db)

    if asociacion.logo_path and Path(asociacion.logo_path).name.startswith(_UPLOAD_PREFIX):
        candidate = _images_dir() / Path(asociacion.logo_path).name
        if candidate.is_file():
            candidate.unlink(missing_ok=True)

    return await update_asociacion(db, asociacion, AsociacionUpdate(logo_path=None))
