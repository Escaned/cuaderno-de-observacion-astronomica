"""Bring the database up to date, from code instead of the `alembic` command.

The packaged application has no `alembic.ini` and no working directory to resolve
one from, so everything the command line would read from that file is passed in
explicitly. `alembic upgrade head` keeps working unchanged for development, but it
skips the two safety nets that live here: a copy of the database before any schema
change and the repair of the half-migrated databases described below. That is why
`instalar.bat` and `arrancar.bat` run this module instead of the command.
"""
import shutil
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text

from app.core import paths

# Nombre con el que se aparta la tabla `asociacion` que creaba `create_all` antes de
# que existiera la migracion 0004. No es una tabla del modelo: si queda con este
# nombre es porque una actualizacion se corto a la mitad.
_ORPHAN_TABLE = "asociacion_previa"

# Cuantas copias de la base se conservan antes de actualizarla. La mas vieja se borra:
# el objetivo es poder volver atras si una actualizacion sale mal, no guardar historia.
_BACKUPS_TO_KEEP = 5

_SQLITE_PREFIXES = ("sqlite+aiosqlite:///", "sqlite:///")


def script_location() -> Path:
    """The directory holding the migration scripts."""
    return paths.bundle_root() / "backend" / "alembic"


def _config(database_url: str) -> Config:
    config = Config()
    config.set_main_option("script_location", str(script_location()))
    # Alembic reads the URL through configparser, where a per cent sign starts an
    # interpolation. Escaping it keeps URLs that legitimately contain one, such as
    # a password, from failing with a confusing error.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    return config


def _database_path(database_url: str) -> Path | None:
    """The file behind a SQLite URL, or None when it is not a SQLite database."""
    for prefix in _SQLITE_PREFIXES:
        if database_url.startswith(prefix):
            return Path(database_url[len(prefix):]).resolve()
    return None


def _sync_engine(database_url: str):
    """A plain engine, for the schema checks Alembic does not do for us."""
    if _database_path(database_url) is None:
        return None
    return create_engine(database_url.replace("+aiosqlite", ""), future=True)


def _current_revision(engine) -> str | None:
    if "alembic_version" not in inspect(engine).get_table_names():
        return None
    with engine.connect() as connection:
        return connection.execute(text("SELECT version_num FROM alembic_version")).scalar()


def _backup_before_migrating(database_url: str, config: Config) -> Path | None:
    """Copy the database file before a migration touches it.

    An update must never be the reason observations disappear. Copied next to the
    database, with the date in the name, so it is found without reading anything.
    Only when there is a pending migration: a normal start copies nothing.
    """
    database = _database_path(database_url)
    if database is None or not database.is_file():
        return None

    engine = _sync_engine(database_url)
    try:
        current = _current_revision(engine)
    finally:
        engine.dispose()

    if current == ScriptDirectory.from_config(config).get_current_head():
        return None

    destino = database.with_name(
        f"{database.name}.antes-de-actualizar-{datetime.now():%Y%m%d-%H%M%S}.db"
    )
    shutil.copy2(database, destino)

    # Una base chica por version nueva; con el tope, la carpeta no crece sin control.
    respaldos = sorted(database.parent.glob(f"{database.name}.antes-de-actualizar-*.db"))
    for viejo in respaldos[:-_BACKUPS_TO_KEEP]:
        viejo.unlink(missing_ok=True)

    return destino


def _park_orphan_asociacion(database_url: str) -> bool:
    """Move away the `asociacion` table that `create_all` left behind.

    Before migration 0004 there was no `asociacion` table: `init_db` created it with
    `create_all`, which never adds a column to an existing table. So a database could
    end up with `asociacion` created but `observatorio` still in the old shape, and
    then 0004 failed with "table asociacion already exists". The table is not
    garbage: the screen was already in use, so it can hold the name and the logo the
    person saved. It gets another name for the duration of the migration and is put
    back afterwards.
    """
    engine = _sync_engine(database_url)
    if engine is None:
        return False
    try:
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        if "asociacion" not in tables or "observatorio" not in tables:
            return False
        columnas = {column["name"] for column in inspector.get_columns("observatorio")}
        if "color" in columnas:
            return False  # ya esta en 0004 o mas adelante

        with engine.begin() as connection:
            if _ORPHAN_TABLE in tables:
                # Un intento anterior ya la habia apartado: esa copia es la que tiene
                # los datos, la que esta con el nombre normal nacio vacia.
                connection.execute(text('DROP TABLE "asociacion"'))
                return False
            connection.execute(
                text(f'ALTER TABLE "asociacion" RENAME TO "{_ORPHAN_TABLE}"')
            )
        return True
    finally:
        engine.dispose()


def _restore_parked_asociacion(database_url: str) -> bool:
    """Put the name and logo saved before the migration into the new `asociacion`."""
    engine = _sync_engine(database_url)
    if engine is None:
        return False
    try:
        tables = set(inspect(engine).get_table_names())
        if _ORPHAN_TABLE not in tables or "asociacion" not in tables:
            # Sin la tabla nueva no hay donde restaurar: se deja como este para que
            # no se pierda nada y se pueda mirar a mano.
            return False

        with engine.begin() as connection:
            guardada = connection.execute(
                text(f'SELECT nombre, logo_path FROM "{_ORPHAN_TABLE}" WHERE id = 1')
            ).first()
            if guardada is not None and (guardada[0] or guardada[1]):
                connection.execute(
                    text(
                        'UPDATE "asociacion" '
                        "SET nombre = COALESCE(:nombre, nombre), "
                        "logo_path = COALESCE(:logo, logo_path) "
                        "WHERE id = 1"
                    ),
                    {"nombre": guardada[0], "logo": guardada[1]},
                )
            connection.execute(text(f'DROP TABLE "{_ORPHAN_TABLE}"'))
        return True
    finally:
        engine.dispose()


def upgrade_to(database_url: str, revision: str) -> None:
    """Apply migrations up to `revision`.

    Used by `upgrade_to_head` and by the tests, which need a database of an earlier
    version to check that an update keeps what was already stored.
    """
    command.upgrade(_config(database_url), revision)


def upgrade_to_head(database_url: str) -> None:
    """Apply every pending migration, keeping whatever the database already has.

    Creating the tables is not enough: the observatory and the six standard filters
    are inserted by the migrations, so a fresh install that skips them starts with
    nothing to record an observation against.
    """
    config = _config(database_url)

    copia = _backup_before_migrating(database_url, config)
    if copia is not None:
        print(f"  Copia de seguridad de la base antes de actualizarla: {copia}")

    if _park_orphan_asociacion(database_url):
        print("  Aparte la tabla 'asociacion' que habia dejado una version anterior.")

    command.upgrade(config, "head")

    if _restore_parked_asociacion(database_url):
        print("  Restaure el nombre y el logo de la asociacion que ya estaban guardados.")


def main() -> None:
    """Update the database of the current settings: `python -m app.core.migrations`."""
    # Imported here so `python -m app.core.migrations` works from `backend/` without
    # reading a `.env` that a caller may be overriding with environment variables.
    from app.core.config import settings

    upgrade_to_head(settings.database_url)


if __name__ == "__main__":
    main()
