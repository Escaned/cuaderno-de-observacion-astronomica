"""Where the application reads its resources and writes its state.

A frozen build and a checkout differ in both, and `app.core.paths` is the single
place that decides. These tests pin the decision for both cases so the rest of the
code can stop asking where things are.
"""
import sys

from app.core import paths


def _make_it_look_frozen(monkeypatch, tmp_path):
    """Pretend the process is a packaged executable sitting in `tmp_path`."""
    executable = tmp_path / "Riguel.exe"
    executable.write_bytes(b"")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable), raising=False)
    return executable


def test_is_frozen_is_false_when_running_from_source(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    assert paths.is_frozen() is False


def test_is_frozen_is_true_when_the_interpreter_is_frozen(monkeypatch, tmp_path):
    _make_it_look_frozen(monkeypatch, tmp_path)

    assert paths.is_frozen() is True


def test_bundle_root_from_source_is_the_repository_root(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    # Asserting on a file that only exists in the repository proves we did not
    # merely return the directory this test file lives in.
    assert (paths.bundle_root() / "backend" / "app" / "core" / "paths.py").is_file()


def test_bundle_root_frozen_is_the_unpacked_bundle(monkeypatch, tmp_path):
    _make_it_look_frozen(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)

    assert paths.bundle_root() == tmp_path / "bundle"


def test_bundle_root_frozen_without_a_bundle_falls_back_to_the_executable(monkeypatch, tmp_path):
    executable = _make_it_look_frozen(monkeypatch, tmp_path)
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)

    assert paths.bundle_root() == executable.parent


def test_app_dir_from_source_is_the_backend_directory(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    # The migrations and the development scripts live in backend/, not in the root.
    assert (paths.app_dir() / "alembic" / "env.py").is_file()


def test_app_dir_frozen_is_the_directory_of_the_executable(monkeypatch, tmp_path):
    executable = _make_it_look_frozen(monkeypatch, tmp_path)

    assert paths.app_dir() == executable.parent


def test_writable_paths_from_source_keep_the_historical_layout(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)

    writable = paths.writable_paths()

    assert writable.database == paths.bundle_root() / "backend" / "riguel.db"
    assert writable.images == paths.bundle_root() / "backend" / "data" / "imagenes"


def test_writable_paths_frozen_keep_everything_in_data_next_to_the_executable(monkeypatch, tmp_path):
    _make_it_look_frozen(monkeypatch, tmp_path)

    writable = paths.writable_paths()

    assert writable.database == tmp_path / "data" / "riguel.db"
    assert writable.images == tmp_path / "data" / "imagenes"
