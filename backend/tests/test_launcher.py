"""The entry point of the packaged application.

Most of the launcher is process work - start a server, open a browser - and is not
worth unit testing here. The parts that decide *where* things go and *which* URL to
use are, because getting them wrong produces exactly the two confusing failures
this change exists to prevent: a browser that never opens because it was pointed at
an address the server does not answer on, and an install that writes its database
into whatever directory the user happened to start it from.
"""
from httpx import ASGITransport, AsyncClient
import pytest

from app.core import launcher, paths


def _writable(tmp_path) -> paths.WritablePaths:
    return paths.WritablePaths(tmp_path / "riguel.db", tmp_path / "imagenes")


def test_environment_points_the_application_at_this_folder_and_this_port(tmp_path):
    environment = launcher.environment(_writable(tmp_path), port=8000)

    assert environment["DATABASE_URL"] == (
        f"sqlite+aiosqlite:///{(tmp_path / 'riguel.db').as_posix()}"
    )
    assert environment["IMAGES_DIR"] == str(tmp_path / "imagenes")
    assert environment["API_PORT"] == "8000"


def test_environment_makes_the_database_absolute(tmp_path):
    environment = launcher.environment(_writable(tmp_path), port=8000)

    # The settings default is `sqlite+aiosqlite:///./riguel.db`: relative to the
    # working directory, which is what made the database's location depend on where
    # the process was started from.
    assert "./riguel.db" not in environment["DATABASE_URL"]
    assert tmp_path.as_posix() in environment["DATABASE_URL"]


def test_environment_binds_to_loopback_only(tmp_path):
    environment = launcher.environment(_writable(tmp_path), port=8000)

    # The settings default is 0.0.0.0, which would serve the user's observations to
    # everyone sharing their network.
    assert environment["API_HOST"] == "127.0.0.1"


def test_environment_honours_the_requested_port(tmp_path):
    environment = launcher.environment(_writable(tmp_path), port=8123)

    assert environment["API_PORT"] == "8123"


def test_probes_the_server_over_ipv4_and_opens_localhost():
    # Two different hosts for the same port on purpose. On Windows `localhost`
    # resolves to ::1 first, the server only listens on IPv4, and a probe against
    # localhost waits out the IPv6 timeout before falling back - which looks exactly
    # like a server that never comes up. Browsers try both, so they are fine.
    assert launcher.health_url(8000) == "http://127.0.0.1:8000/health"
    assert launcher.browser_url(8000) == "http://localhost:8000"
    assert launcher.health_url(8123) == "http://127.0.0.1:8123/health"
    assert launcher.browser_url(8123) == "http://localhost:8123"


def test_port_defaults_to_8000_when_nothing_says_otherwise(monkeypatch):
    monkeypatch.delenv("RIGUEL_PUERTO", raising=False)

    assert launcher.configured_port() == 8000


def test_port_can_be_overridden(monkeypatch):
    monkeypatch.setenv("RIGUEL_PUERTO", "8123")

    assert launcher.configured_port() == 8123


def test_a_nonsense_port_falls_back_instead_of_crashing(monkeypatch):
    monkeypatch.setenv("RIGUEL_PUERTO", "ocho mil")

    assert launcher.configured_port() == 8000


def test_adopts_a_legacy_database_and_leaves_the_original_untouched(tmp_path):
    legacy = tmp_path / "backend" / "riguel.db"
    legacy.parent.mkdir()
    legacy.write_bytes(b"observaciones de antes")
    target = tmp_path / "data" / "riguel.db"

    adopted = launcher.adopt_legacy_database(legacy, target)

    assert adopted is True
    assert target.read_bytes() == b"observaciones de antes"
    assert legacy.read_bytes() == b"observaciones de antes"


def test_never_overwrites_a_database_that_is_already_in_use(tmp_path):
    legacy = tmp_path / "backend" / "riguel.db"
    legacy.parent.mkdir()
    legacy.write_bytes(b"la vieja")
    target = tmp_path / "data" / "riguel.db"
    target.parent.mkdir()
    target.write_bytes(b"la que se esta usando")

    adopted = launcher.adopt_legacy_database(legacy, target)

    assert adopted is False
    assert target.read_bytes() == b"la que se esta usando"


def test_does_nothing_when_there_is_no_legacy_database(tmp_path):
    target = tmp_path / "data" / "riguel.db"

    adopted = launcher.adopt_legacy_database(tmp_path / "backend" / "riguel.db", target)

    assert adopted is False
    assert not target.exists()


def test_installs_the_default_logo_when_there_is_none(tmp_path):
    bundled = tmp_path / "bundled-logo.jpg"
    bundled.write_bytes(b"jpeg por defecto")
    images = tmp_path / "imagenes"
    images.mkdir()

    installed = launcher.install_default_logo(bundled, images / "logo.jpg")

    assert installed is True
    assert (images / "logo.jpg").read_bytes() == b"jpeg por defecto"


def test_does_not_replace_the_logo_the_association_already_chose(tmp_path):
    bundled = tmp_path / "bundled-logo.jpg"
    bundled.write_bytes(b"jpeg por defecto")
    images = tmp_path / "imagenes"
    images.mkdir()
    (images / "logo.jpg").write_bytes(b"el logo de la asociacion")

    installed = launcher.install_default_logo(bundled, images / "logo.jpg")

    assert installed is False
    assert (images / "logo.jpg").read_bytes() == b"el logo de la asociacion"


def test_recognises_the_application_answering_on_the_port():
    assert launcher.is_this_application({"status": "ok", "service": "riguel-cuaderno-api"}) is True


def test_does_not_mistake_another_program_for_the_application():
    assert launcher.is_this_application({"status": "ok", "service": "otra-cosa"}) is False
    assert launcher.is_this_application({"detail": "Not Found"}) is False
    assert launcher.is_this_application(None) is False


@pytest.mark.asyncio
async def test_recognises_the_payload_the_application_actually_serves():
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = (await client.get("/health")).json()

    # Pins the constant against the real endpoint: if /health starts reporting a
    # different service name, the launcher would stop recognising its own server and
    # would offer to start a second one on top of it.
    assert launcher.is_this_application(payload) is True
