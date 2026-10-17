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

    # logo_path arrives in 0003 and fwhm in 0002, so a missing one means we stopped early.
    assert "logo_path" in observatorio_columns
    assert "fwhm" in observacion_columns


def test_upgrade_to_head_does_not_duplicate_the_seed(tmp_path):
    database = tmp_path / "riguel.db"

    migrations.upgrade_to_head(_database_url(database))
    migrations.upgrade_to_head(_database_url(database))

    assert _query(database, "SELECT COUNT(*) FROM filtros") == [(6,)]
    assert _query(database, "SELECT COUNT(*) FROM observatorio") == [(1,)]


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
