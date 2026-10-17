"""Where the backend looks for the built frontend.

This is the one path that fails silently when it is wrong: the application still
starts, the API still answers, and the user just gets a blank page or a 404. It is
also the path that used to be derived from the source file's position, which means
nothing inside a packaged build.

The tests reload the module because the location is resolved once, at import time.
"""
import importlib
import sys

from app import main
from app.core import paths


def test_frontend_dist_is_inside_the_bundle_when_frozen(monkeypatch, tmp_path):
    executable = tmp_path / "Riguel.exe"
    executable.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setattr(sys, "executable", str(executable), raising=False)

    try:
        frozen_main = importlib.reload(main)

        assert frozen_main.FRONTEND_DIST == tmp_path / "frontend" / "dist"
    finally:
        # Undo the fake freeze before restoring, so the reload sees a normal
        # checkout again and no other test inherits the packaged location.
        monkeypatch.undo()
        importlib.reload(main)


def test_frontend_dist_from_source_is_the_built_frontend_in_the_repository(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert main.FRONTEND_DIST == paths.bundle_root() / "frontend" / "dist"
