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
set "PYVER="
set "OTROVER="

REM Se prueba de la version mas nueva soportada a la mas vieja, en ese orden:
REM el lanzador "py" elige la ultima que encuentre, y si alguien tiene 3.14
REM instalado "py -3" devuelve 3.14, que todavia no sirve.
REM La 3.14 no sirve porque pydantic 2.8 trae pydantic-core 2.20.1, que esta
REM escrito en Rust y solo publica ruedas hasta 3.13: en 3.14 pip intentaria
REM compilarlo y la instalacion fallaria pidiendo Rust.
for %%C in ("py -3.13" "py -3.12" "python" "py -3") do (
    if not defined PYCMD (
        %%~C --version >nul 2>&1
        if not errorlevel 1 (
            set "VERDEESTE="
            for /f "delims=" %%v in ('%%~C --version 2^>nul') do set "VERDEESTE=%%v"
            if not defined OTROVER set "OTROVER=!VERDEESTE!"
            %%~C -c "import sys; sys.exit(0 if (3,12) <= sys.version_info[:2] < (3,14) else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYCMD=%%~C"
                set "PYVER=!VERDEESTE!"
            )
        )
    )
)

if not defined PYCMD (
    if not defined OTROVER goto :sin_python
    goto :python_malo
)

echo       Encontrado: !PYVER!

REM ---------------------------------------------------------------
REM  2. Entorno virtual
REM ---------------------------------------------------------------
echo.
echo [2/5] Preparando el entorno virtual (carpeta .venv)...

REM Un .venv creado con otra version de Python no se puede reutilizar, y ademas
REM es la causa de un fallo que confunde mucho: se instala Python 3.13, se vuelve
REM a ejecutar instalar.bat y vuelve a fallar, porque el .venv viejo (hecho con
REM 3.14, por ejemplo) se reutilizaba en silencio.
REM
REM Las dos rutas van sin comillas a proposito: dentro de un "for /f" un comando
REM que empieza con comilla doble se parsea distinto. Son relativas y sin espacios.
REM Si el python del .venv existiera pero no respondiera, VENVVER quedaria vacio
REM y tampoco coincidiria, que es justo lo que buscamos: recrearlo.
if exist ".venv\Scripts\python.exe" (
    set "VENVVER="
    set "ELEGIDOVER="
    for /f "delims=" %%v in ('.venv\Scripts\python.exe -c "import sys;print(sys.version_info[0],sys.version_info[1])" 2^>nul') do set "VENVVER=%%v"
    for /f "delims=" %%v in ('%PYCMD% -c "import sys;print(sys.version_info[0],sys.version_info[1])" 2^>nul') do set "ELEGIDOVER=%%v"

    if not "!VENVVER!"=="!ELEGIDOVER!" (
        echo       El entorno que habia es de Python !VENVVER! y ahora uso !ELEGIDOVER!.
        echo       Lo borro y lo creo de nuevo.
        rmdir /s /q ".venv"
    )
)

if exist ".venv\Scripts\python.exe" (
    echo       Ya existe y es de la version correcta, lo reutilizo.
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
    echo   [ERROR] No pude instalar las dependencias.
    echo.
    echo           Puede ser que no tengas internet, o que tu Python no sea
    echo           compatible: hace falta 3.12 o 3.13.
    echo.
    echo           Mira el texto de arriba. Si aparece "pyproject.toml",
    echo           "maturin" o "Rust", es lo segundo: instala Python 3.13,
    echo           borra la carpeta .venv y volve a ejecutar instalar.bat.
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

:sin_python
echo.
echo   [ERROR] No encontre Python en este equipo.
echo.
echo   Descargalo de:  https://www.python.org/downloads/windows/
echo.
echo   MUY IMPORTANTE: al instalar, marca la casilla que dice
echo   Add python.exe to PATH antes de continuar.
echo.
echo   Si tenes winget, podes instalarlo con este comando:
echo       winget install -e --id Python.Python.3.13
echo.
goto :error

:python_malo
echo.
echo   [ERROR] Tu Python es !OTROVER! y la aplicacion todavia no funciona con esa version.
echo.
echo   Hace falta Python 3.12 o 3.13. La 3.14 todavia no esta soportada,
echo   porque una de las dependencias se tendria que compilar y no viene lista
echo   para esa version.
echo.
echo   Instala la 3.13 y despues volve a ejecutar instalar.bat:
echo       https://www.python.org/downloads/windows/
echo   o, si tenes winget:
echo       winget install -e --id Python.Python.3.13
echo.
echo   OJO: antes de volver a ejecutarlo, BORRA la carpeta .venv que esta
echo   aqui al lado. Si no la borras se reutiliza el entorno viejo y el
echo   error se repite.
echo.
goto :error

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
