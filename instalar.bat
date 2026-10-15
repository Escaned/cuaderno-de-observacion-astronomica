@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================
echo   Riguel - Cuaderno de Campo Astronomico
echo   INSTALACION
echo ============================================================
echo.

REM ---------------------------------------------------------------
REM  1. Buscar Python
REM ---------------------------------------------------------------
echo [1/5] Buscando Python...

set "PYCMD="
py -3 --version >nul 2>&1
if not errorlevel 1 set "PYCMD=py -3"

if not defined PYCMD (
    python --version >nul 2>&1
    if not errorlevel 1 set "PYCMD=python"
)

if not defined PYCMD (
    echo.
    echo   [ERROR] No encontre Python en este equipo.
    echo.
    echo   Descargalo de:  https://www.python.org/downloads/windows/
    echo.
    echo   MUY IMPORTANTE: al instalar, marca la casilla que dice
    echo   Add python.exe to PATH antes de continuar.
    echo.
    echo   Si tenes winget, podes instalarlo con este comando:
    echo       winget install -e --id Python.Python.3.12
    echo.
    goto :error
)

for /f "delims=" %%v in ('%PYCMD% --version 2^>^&1') do set "PYVER=%%v"
echo       Encontrado: !PYVER!

%PYCMD% -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)"
if errorlevel 1 (
    echo.
    echo   [ERROR] Tu Python es mas viejo que 3.12 y la aplicacion no funciona con esa version.
    echo   Instala una version nueva desde https://www.python.org/downloads/windows/
    echo.
    goto :error
)

REM ---------------------------------------------------------------
REM  2. Entorno virtual
REM ---------------------------------------------------------------
echo.
echo [2/5] Creando el entorno virtual (carpeta .venv)...
if exist ".venv\Scripts\python.exe" (
    echo       Ya existe, lo reutilizo.
) else (
    %PYCMD% -m venv .venv
    if errorlevel 1 (
        echo.
        echo   [ERROR] No pude crear el entorno virtual.
        echo.
        goto :error
    )
    echo       Creado.
)

REM ---------------------------------------------------------------
REM  3. Dependencias
REM ---------------------------------------------------------------
echo.
echo [3/5] Instalando dependencias (puede tardar un par de minutos)...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo.
    echo   [ERROR] No pude actualizar pip. Revisa tu conexion a internet.
    echo.
    goto :error
)

".venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"
if errorlevel 1 (
    echo.
    echo   [ERROR] No pude instalar las dependencias. Revisa tu conexion a internet.
    echo.
    goto :error
)

REM ---------------------------------------------------------------
REM  4. Base de datos
REM ---------------------------------------------------------------
echo.
echo [4/5] Preparando la base de datos...
pushd backend
"..\.venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    popd
    echo.
    echo   [ERROR] No pude preparar la base de datos.
    echo.
    goto :error
)
popd

REM ---------------------------------------------------------------
REM  5. Comprobacion final
REM ---------------------------------------------------------------
echo.
echo [5/5] Comprobando que todo este en su lugar...
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, sqlalchemy, reportlab; print('       Dependencias OK')"
if errorlevel 1 (
    echo.
    echo   [ERROR] Falta alguna dependencia.
    echo.
    goto :error
)

if exist "frontend\dist\index.html" (
    echo       Interfaz web OK
) else (
    echo.
    echo   [AVISO] No encuentro la interfaz web compilada en frontend\dist
    echo           El paquete deberia incluirla. Si falta, avisale a quien te lo dio.
    echo.
)

echo.
echo ============================================================
echo   INSTALACION COMPLETA
echo ============================================================
echo.
echo   Para usar la aplicacion, hace doble clic en:
echo.
echo       arrancar.bat
echo.
echo   Se va a abrir el navegador solo en http://localhost:8000
echo.
pause
exit /b 0

:error
echo.
echo ============================================================
echo   LA INSTALACION FALLO
echo ============================================================
echo.
echo   Lee el mensaje de arriba para saber que paso.
echo   Si no sabes como seguir, pasa el texto completo de esta
echo   ventana a quien te paso el programa.
echo.
pause
exit /b 1
