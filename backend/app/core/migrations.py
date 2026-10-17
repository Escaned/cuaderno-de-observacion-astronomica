"""Bring the database up to date, from code instead of the `alembic` command.

The packaged application has no `alembic.ini` and no working directory to resolve
one from, so everything the command line would read from that file is passed in
explicitly. `alembic upgrade head` keeps working unchanged for development.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core import paths


def script_location() -> Path:
    """The directory holding the migration scripts."""
    return paths.bundle_root() / "backend" / "alembic"


def upgrade_to_head(database_url: str) -> None:
    """Apply every pending migration.

    Creating the tables is not enough: the observatory and the six standard filters
    are inserted by the migrations, so a fresh install that skips them starts with
    nothing to record an observation against.
    """
    config = Config()
    config.set_main_option("script_location", str(script_location()))
    # Alembic reads the URL through configparser, where a per cent sign starts an
    # interpolation. Escaping it keeps URLs that legitimately contain one, such as
    # a password, from failing with a confusing error.
    config.set_main_option("sqlalchemy.url", database_url.replace("%", "%%"))
    command.upgrade(config, "head")
