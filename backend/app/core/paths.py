"""Where the application reads its resources and writes its state.

Frozen and running from source differ in both, and this module is the only place
that asks. Everywhere else calls these helpers and stops caring.

The distinction matters because a PyInstaller bundle unpacks into a temporary
directory that is wiped when the process exits. Resources are safe there, since
they are a read-only copy of what shipped. The database and the uploaded images
are not, so they live next to the executable instead.
"""
import sys
from pathlib import Path
from typing import NamedTuple

# backend/app/core/paths.py -> core -> app -> backend -> repository root
_REPOSITORY_ROOT = 3


class WritablePaths(NamedTuple):
    """The two things the user is told to back up."""

    database: Path
    images: Path


def is_frozen() -> bool:
    """True when running from a PyInstaller bundle rather than from a checkout."""
    return bool(getattr(sys, "frozen", False))


def _repository_root() -> Path:
    """Where this file lives when the application was not packaged."""
    return Path(__file__).resolve().parents[_REPOSITORY_ROOT]


def bundle_root() -> Path:
    """Read-only resources that ship with the application.

    Inside a bundle the frontend, the migrations and the default logo are unpacked
    into a temporary directory. From source they sit in the repository.
    """
    if is_frozen():
        # PyInstaller points _MEIPASS at the unpack directory. Without it we are
        # running from a build that extracted its files next to the executable,
        # which is the closest equivalent.
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return _repository_root()


def app_dir() -> Path:
    """Directory the application belongs to, frozen or not.

    Frozen that is where the executable sits, so the user has one folder to keep
    together. From source it is `backend/`, which keeps the database landing where
    `arrancar.bat` and the migration commands already expect it.
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return _repository_root() / "backend"


def writable_paths() -> WritablePaths:
    """The database and the uploaded images.

    Frozen, both live together in `data` next to the executable: a single folder
    the instructions can point at, and the user can copy somewhere else as a
    backup. From source the historical layout is kept instead - the database at the
    backend root and the images under `data/imagenes` - because every existing
    checkout, script and test already points there and moving it would buy nothing.
    """
    directory = app_dir()
    if is_frozen():
        return WritablePaths(directory / "data" / "riguel.db", directory / "data" / "imagenes")
    return WritablePaths(directory / "riguel.db", directory / "data" / "imagenes")
