# -*- mode: python ; coding: utf-8 -*-
"""Definicion de PyInstaller para el ejecutable de Windows.

Una carpeta y no un solo archivo. Un build de un-archivo descomprime todo el
paquete en un directorio temporal en CADA arranque: cuesta segundos de inicio y
le da a los antivirus bastante mas de que sospechar. Es una carpeta, se copia
entera y listo.

Todo lo que la aplicacion lee en tiempo de ejecucion esta en `datas`, en la
misma posicion relativa que tiene en el repositorio, porque el codigo lo busca a
traves de `app.core.paths.bundle_root()`:

    frontend/dist           la interfaz web compilada
    backend/alembic         las migraciones, que corren al arrancar
    backend/data/imagenes   el logo que el lanzador restaura si no hay ninguno

`alembic.ini` NO va a proposito: las migraciones se manejan desde el codigo, que
arma la configuracion de Alembic sola. Empaquetarlo seria empaquetar un archivo
que nadie lee.

Las rutas se arman desde SPECPATH, la carpeta que contiene este archivo, para que
el build salga igual sin importar desde donde se lo invoque.
"""
from pathlib import Path

ROOT = Path(SPECPATH)

datas = [
    (str(ROOT / "frontend" / "dist"), "frontend/dist"),
    (str(ROOT / "backend" / "alembic"), "backend/alembic"),
    (str(ROOT / "backend" / "data" / "imagenes" / "logo.jpg"), "backend/data/imagenes"),
]

hiddenimports = [
    # SQLAlchemy elige el dialecto asincrono de SQLite por nombre en tiempo de
    # ejecucion, asi que un analisis estatico no lo ve.
    "aiosqlite",
    "sqlalchemy.dialects.sqlite.aiosqlite",
    # Los archivos de migracion se leen del disco y se ejecutan: sus imports
    # ("from alembic import op") no aparecen en ningun analisis de este proyecto.
    "alembic.op",
]

excludes = [
    # Nada de esto hace falta para ejecutar la aplicacion.
    "tkinter",
    "pytest",
    "mypy",
    "PyInstaller",
]

a = Analysis(
    [str(ROOT / "backend" / "app" / "core" / "launcher.py")],
    pathex=[str(ROOT / "backend")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Riguel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    # Sin compresion UPX: es una de las causas clasicas de que Windows Defender
    # marque un ejecutable recien hecho como sospechoso, y el ahorro de tamano no
    # paga el problema.
    upx=False,
    console=True,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="Riguel",
)
