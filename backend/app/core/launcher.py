"""The entry point of the packaged application.

A packaged build has no command line to pass options and no working directory to
rely on: the user double-clicks an executable. Everything the batch files do around
uvicorn - pick the interpreter, move to the right folder, open a browser - happens
here instead, written so it also works from a checkout and none of it needs a build
to be tested.

The order below is not arbitrary. The environment variables have to be written
before `app.core.config` is imported, because the settings object is built at import
time and reads them once. That is why `app.main` is imported inside `serve()` and
not at the top of this file.
"""
import json
import os
import shutil
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

from app.core import migrations, paths

# Has to match what /health reports, so the launcher can tell its own server apart
# from an unrelated program that happens to hold the port.
SERVICE_NAME = "riguel-cuaderno-api"

DEFAULT_PORT = 8000
_PORT_VARIABLE = "RIGUEL_PUERTO"
_BROWSER_VARIABLE = "RIGUEL_SIN_NAVEGADOR"
# Kept in step with abrir-navegador.ps1, which does the same job for arrancar.bat.
_STARTUP_TIMEOUT_SECONDS = 30
_PROBE_INTERVAL_SECONDS = 0.4
_PROBE_TIMEOUT_SECONDS = 1

# The logo the application falls back to, relative to the bundle.
_BUNDLED_LOGO = Path("backend") / "data" / "imagenes" / "logo.jpg"


# ---------------------------------------------------------------------------
# Decisions. Pure enough to test without starting anything.
# ---------------------------------------------------------------------------


def environment(writable: paths.WritablePaths, port: int) -> dict[str, str]:
    """The variables that pin the application to this folder and this machine."""
    return {
        # Absolute, so the database stops depending on the working directory.
        "DATABASE_URL": f"sqlite+aiosqlite:///{writable.database.as_posix()}",
        "IMAGES_DIR": str(writable.images),
        # The settings default is 0.0.0.0, which would serve the user's observations
        # to everyone on their network.
        "API_HOST": "127.0.0.1",
        "API_PORT": str(port),
    }


def health_url(port: int) -> str:
    """Where to ask whether the server is up. See `wait_until_serving`."""
    return f"http://127.0.0.1:{port}/health"


def browser_url(port: int) -> str:
    """What to open. `localhost` is fine here: browsers try IPv6 and then IPv4."""
    return f"http://localhost:{port}"


def configured_port() -> int:
    """The port to serve on, overridable so a check can step around a clash."""
    raw = os.environ.get(_PORT_VARIABLE, "").strip()
    try:
        return int(raw) if raw else DEFAULT_PORT
    except ValueError:
        print(f"  [AVISO] {_PORT_VARIABLE}={raw} no es un numero: uso {DEFAULT_PORT}.")
        return DEFAULT_PORT


def is_this_application(payload: object) -> bool:
    """Whether a /health reply came from this application."""
    return isinstance(payload, dict) and payload.get("service") == SERVICE_NAME


def adopt_legacy_database(legacy: Path, target: Path) -> bool:
    """Take over the database left by a script install.

    Copied and never moved: a move gone wrong loses observations, while a copy is
    undone by deleting one file. It only ever fills a gap.
    """
    if target.exists() or not legacy.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy, target)
    return True


def install_default_logo(bundled: Path, target: Path) -> bool:
    """Put the logo the application ships with in place, if there is none yet."""
    if target.exists() or not bundled.is_file():
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bundled, target)
    return True


# ---------------------------------------------------------------------------
# The process itself.
# ---------------------------------------------------------------------------


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(_PROBE_TIMEOUT_SECONDS)
        return probe.connect_ex(("127.0.0.1", port)) != 0


def is_this_application_running(port: int) -> bool:
    try:
        with urllib.request.urlopen(health_url(port), timeout=_PROBE_TIMEOUT_SECONDS) as reply:
            return is_this_application(json.load(reply))
    except (urllib.error.URLError, ValueError, OSError):
        return False


def wait_until_serving(port: int) -> bool:
    """Wait for the server to answer, with a ceiling so it can never hang forever.

    Probed over 127.0.0.1 on purpose. On Windows `localhost` resolves to ::1 first,
    the server listens on IPv4 only, and an attempt against localhost therefore
    waits out the IPv6 timeout before falling back - which looks exactly like a
    server that never comes up.
    """
    deadline = time.monotonic() + _STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        if is_this_application_running(port):
            return True
        time.sleep(_PROBE_INTERVAL_SECONDS)
    return False


def _pause_for_reading() -> None:
    """Keep the window open so a double-click user can read what happened.

    Skipped when there is no console to read from, and in automated runs, where
    waiting for a keypress would hang the check that started us.
    """
    if _BROWSER_VARIABLE in os.environ or not sys.stdin.isatty():
        return
    try:
        input("  Apreta Enter para cerrar...")
    except EOFError:
        pass


def _welcome(port: int) -> None:
    print()
    print("=" * 60)
    print("  Riguel - Cuaderno de Campo Astronomico")
    print("=" * 60)
    print()
    print(f"  Direccion:  {browser_url(port)}")
    print()
    print("  PARA CERRAR LA APLICACION: cerra esta ventana")
    print("  o apreta Ctrl+C aqui dentro.")
    print()
    print("-" * 60)
    print()


def _prepare_directories(writable: paths.WritablePaths) -> None:
    # The images directory has to exist before `app.main` is imported: the static
    # files mount is created at import time and refuses a directory that is not
    # there, which leaves the application dead on a cold start.
    writable.images.mkdir(parents=True, exist_ok=True)
    writable.database.parent.mkdir(parents=True, exist_ok=True)


def _take_over_a_legacy_database(writable: paths.WritablePaths) -> None:
    # Only meaningful in a packaged build, where the user has the executable in one
    # folder and a script install possibly in the next one along. From source the
    # database is already in the only place it has ever been.
    if not paths.is_frozen():
        return
    if adopt_legacy_database(paths.app_dir() / "backend" / "riguel.db", writable.database):
        print("  Encontre la base de datos de una instalacion anterior y la copie a:")
        print(f"    {writable.database}")
        print("  El archivo original quedo donde estaba, no lo toque.")
        print()


def _restore_the_default_logo(writable: paths.WritablePaths) -> None:
    if install_default_logo(paths.bundle_root() / _BUNDLED_LOGO, writable.images / "logo.jpg"):
        print("  Restaure el logo por defecto.")


def _migrate(database_url: str) -> bool:
    """Bring the database up to date, or explain why we are not starting."""
    try:
        migrations.upgrade_to_head(database_url)
    except Exception as error:  # noqa: BLE001 - any failure here has to be reported
        print()
        print("  No pude preparar la base de datos.")
        print("  No arranco el servidor para no dejarla a medio actualizar.")
        print(f"  Base de datos: {database_url}")
        print(f"  Detalle: {error}")
        print()
        _pause_for_reading()
        return False
    return True


def _serve(host: str, port: int) -> int:
    import uvicorn

    # Imported here, and not at the top of the file: importing it reads the settings
    # and mounts the static files, so the environment variables have to be in place
    # first and the images directory has to exist.
    from app.main import app

    if _BROWSER_VARIABLE not in os.environ:
        threading.Thread(
            target=lambda: wait_until_serving(port) and webbrowser.open(browser_url(port)),
            daemon=True,
        ).start()

    uvicorn.run(app, host=host, port=port, log_level="info")

    print()
    print("  La aplicacion se detuvo.")
    print()
    _pause_for_reading()
    return 0


def run() -> int:
    writable = paths.writable_paths()
    port = configured_port()

    # Checked before touching anything, so a second double-click is cheap and does
    # not create directories or migrate anything.
    if not port_is_free(port):
        if is_this_application_running(port):
            print()
            print(f"  Ya hay una copia de la aplicacion funcionando en el puerto {port}.")
            print("  Abro el navegador ahi. Para cerrarla, busca su ventana.")
            print()
            if _BROWSER_VARIABLE not in os.environ:
                webbrowser.open(browser_url(port))
            _pause_for_reading()
            return 0
        print()
        print(f"  El puerto {port} esta ocupado por otro programa.")
        print("  Cerralo y volve a intentar, o reinicia la computadora.")
        print()
        _pause_for_reading()
        return 1

    _welcome(port)

    variables = environment(writable, port)
    os.environ.update(variables)

    _prepare_directories(writable)
    _take_over_a_legacy_database(writable)
    _restore_the_default_logo(writable)

    if not _migrate(variables["DATABASE_URL"]):
        return 1

    return _serve(variables["API_HOST"], port)


def main() -> int:
    """Run the application without ever letting a traceback reach the user."""
    try:
        return run()
    except Exception as error:  # noqa: BLE001 - a traceback is noise to the user
        print()
        print("  No se pudo arrancar la aplicacion.")
        print(f"  Detalle: {error}")
        print()
        _pause_for_reading()
        return 1


if __name__ == "__main__":
    sys.exit(main())
