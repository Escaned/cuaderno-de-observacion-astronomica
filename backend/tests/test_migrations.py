"""The migrations, driven from code instead of the `alembic` command.

The packaged application has no `alembic.ini` and no working directory to resolve
one from, so everything the command line would read from that file is passed in
explicitly. These tests describe what the database has to look like afterwards,
including the seed data that the migrations - not `create_all` - are responsible
for.
"""
import sqlite3

from app.core import migrations


def _database_url(database) -> str:
    return f"sqlite+aiosqlite:///{database.as_posix()}"


def _query(database, sql):
    connection = sqlite3.connect(database)
    try:
        return connection.execute(sql).fetchall()
    finally:
        connection.close()


def test_upgrade_to_head_creates_and_seeds_a_fresh_database(tmp_path):
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))

    assert _query(database, "SELECT nombre FROM observatorio WHERE id = 1") == [("Riguel",)]
    assert _query(database, "SELECT nombre FROM asociacion WHERE id = 1") == [("Riguel",)]
    assert [row[0] for row in _query(database, "SELECT nombre FROM filtros ORDER BY orden")] == [
        "L",
        "R",
        "G",
        "B",
        "Ha",
        "OIII",
    ]


def test_upgrade_to_head_applies_every_migration(tmp_path):
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))

    observatorio_columns = {row[1] for row in _query(database, "PRAGMA table_info(observatorio)")}
    observacion_columns = {row[1] for row in _query(database, "PRAGMA table_info(observaciones)")}

    # logo_path arrives in 0003, fwhm in 0002 and the sites in 0004, so a missing
    # one means we stopped early.
    assert "color" in observatorio_columns
    assert "es_predeterminado" in observatorio_columns
    assert "fwhm" in observacion_columns
    assert "observatorio_id" in observacion_columns

    # The first observatory is the default
    assert _query(database, "SELECT es_predeterminado FROM observatorio WHERE id = 1") == [(1,)]


def test_upgrade_to_head_does_not_duplicate_the_seed(tmp_path):
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))
    migrations.upgrade_to_head(_database_url(database))

    assert _query(database, "SELECT COUNT(*) FROM filtros") == [(6,)]
    assert _query(database, "SELECT COUNT(*) FROM observatorio") == [(1,)]
    assert _query(database, "SELECT COUNT(*) FROM asociacion") == [(1,)]


def _database_of_the_previous_version(database, nombre="Asociacion guardada", logo="logo-propio.jpg"):
    """A database stuck between versions, exactly as the previous release left it.

    `create_all` created `asociacion` on startup but never added `color` to
    `observatorio`, so migration 0004 found the table already there and failed. The
    screen was in use, so the table can hold a name and a logo worth keeping.
    """
    migrations.upgrade_to(_database_url(database), "0003")
    connection = sqlite3.connect(database)
    try:
        connection.execute(
            "CREATE TABLE asociacion ("
            " id INTEGER NOT NULL,"
            " nombre VARCHAR(100) NOT NULL DEFAULT 'Riguel',"
            " logo_path VARCHAR(255),"
            " CONSTRAINT ck_asociacion_singleton CHECK (id = 1),"
            " PRIMARY KEY (id))"
        )
        connection.execute(
            "INSERT INTO asociacion (id, nombre, logo_path) VALUES (1, ?, ?)",
            (nombre, logo),
        )
        connection.execute(
            "INSERT INTO observaciones (objeto, fecha_hora_utc, fwhm) "
            "VALUES ('M42', '2026-01-05 22:00:00', 2.4)"
        )
        connection.commit()
    finally:
        connection.close()


def test_an_update_repairs_the_table_create_all_left_and_keeps_the_data(tmp_path, capsys):
    database = tmp_path / "riguel.db"
    _database_of_the_previous_version(database)

    migrations.upgrade_to_head(_database_url(database))

    tablas = {row[0] for row in _query(database, "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert "asociacion_previa" not in tablas
    assert _query(database, "SELECT version_num FROM alembic_version") == [("0004",)]

    # Lo que la persona habia guardado gana sobre lo que siembra la migracion.
    assert _query(database, "SELECT nombre, logo_path FROM asociacion WHERE id = 1") == [
        ("Asociacion guardada", "logo-propio.jpg")
    ]
    assert _query(database, "SELECT nombre FROM observatorio WHERE id = 1") == [("Riguel",)]

    # Y las observaciones siguen ahi, ligadas al observatorio que ya existia.
    assert _query(database, "SELECT objeto, observatorio_id FROM observaciones") == [("M42", 1)]

    assert "Aparte la tabla" in capsys.readouterr().out


def test_an_update_saves_a_copy_of_the_database_before_touching_it(tmp_path):
    database = tmp_path / "riguel.db"
    _database_of_the_previous_version(database)

    migrations.upgrade_to_head(_database_url(database))

    respaldos = sorted(tmp_path.glob("riguel.db.antes-de-actualizar-*.db"))
    assert len(respaldos) == 1
    # La copia es la base tal como estaba: en 0003 y con la tabla vieja adentro, que
    # es justo lo que hace falta para volver atras si la actualizacion sale mal.
    assert _query(respaldos[0], "SELECT version_num FROM alembic_version") == [("0003",)]


def test_a_normal_start_does_not_save_a_copy(tmp_path):
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))
    migrations.upgrade_to_head(_database_url(database))

    assert not list(tmp_path.glob("riguel.db.antes-de-actualizar-*.db"))


def test_upgrade_to_head_uses_the_url_it_is_given_not_the_configured_one(tmp_path, monkeypatch):
    working_directory = tmp_path / "cwd"
    working_directory.mkdir()
    monkeypatch.chdir(working_directory)
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))

    assert _query(database, "SELECT COUNT(*) FROM filtros") == [(6,)]
    # The application settings point at ./riguel.db, relative to the working
    # directory. If the Alembic environment script overwrote the caller's URL with
    # them, the seeded database would have landed here instead of where we asked.
    assert not (working_directory / "riguel.db").exists()
