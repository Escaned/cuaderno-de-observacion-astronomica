@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo   Todavia no esta instalado en este equipo.
    echo.
    echo   Primero hace doble clic en:  instalar.bat
    echo.
    pause
    exit /b 1
)

if not exist "frontend\dist\index.html" (
    echo.
    echo   [AVISO] Falta la interfaz web compilada ^(frontend\dist^).
    echo           La aplicacion va a arrancar, pero el navegador no va a mostrar nada.
    echo.
)

echo.
echo ============================================================
echo   Riguel - Cuaderno de Campo Astronomico
echo ============================================================
echo.
echo   Arrancando... el navegador se va a abrir solo.
echo.
echo   Direccion:  http://localhost:8000
echo.
echo   PARA CERRAR LA APLICACION: cerra esta ventana
echo   o apreta Ctrl+C aqui dentro.
echo.
echo ------------------------------------------------------------
echo.

REM Actualiza la base antes de abrir nada: una version nueva puede cambiar el
REM esquema, y la app no arranca contra una base vieja. Se hace aca para que el
REM error se lea en esta ventana y no como una pantalla vacia en el navegador.
pushd backend
"..\.venv\Scripts\python.exe" -m alembic upgrade head
if errorlevel 1 (
    popd
    echo.
    echo   [ERROR] No pude actualizar la base de datos.
    echo           Lee el mensaje de arriba; la aplicacion no va a arrancar.
    echo.
    pause
    exit /b 1
)
popd

REM Abre el navegador en segundo plano, esperando a que el servidor responda.
REM Definiendo la variable RIGUEL_SIN_NAVEGADOR no se abre (util en pruebas automaticas).
if defined RIGUEL_SIN_NAVEGADOR goto :servidor
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0abrir-navegador.ps1"

:servidor
cd backend
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

echo.
echo   La aplicacion se detuvo.
echo.
pause
