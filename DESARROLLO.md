# Guía de desarrollo

Documentación para **quien va a modificar el código**. Si solo querés *usar* la aplicación, mirá
[`INSTALL.md`](INSTALL.md).

- [1. Entorno](#1-entorno)
- [2. Puesta en marcha](#2-puesta-en-marcha)
- [3. Los dos modos de ejecución](#3-los-dos-modos-de-ejecución)
- [4. Tests](#4-tests)
- [5. Empaquetar para distribuir](#5-empaquetar-para-distribuir)
- [6. Problemas conocidos](#6-problemas-conocidos)

---

## 1. Entorno

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Git | cualquiera | `git --version` |

Node **solo** hace falta para desarrollar el frontend o correr los tests. Una instalación normal
(la que describe `INSTALL.md`) no lo necesita.

---

## 2. Puesta en marcha

```bash
git clone https://github.com/Escaned/cuaderno-de-observacion-astronomica.git observaciones
cd observaciones
```

### 2.1 Backend

El entorno virtual vive en la **raíz** del repo (no en `backend/`):

```bash
python -m venv .venv
```

| Sistema | Activar |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Linux / macOS | `source .venv/bin/activate` |

```bash
pip install -r backend/requirements.txt -r backend/requirements-dev.txt
```

- `requirements.txt` → lo que la aplicación necesita para **funcionar**
- `requirements-dev.txt` → tests y tipado (`pytest`, `httpx`, `mypy`)

> **Ojo con SQLAlchemy.** El paquete se declara como `sqlalchemy[asyncio]`, no `sqlalchemy`. A partir de
> la versión 2.1, `greenlet` dejó de instalarse automáticamente y sin ese extra la app no arranca:
> `The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed`.

### 2.2 Base de datos

```bash
cd backend
alembic upgrade head
```

Crea las tablas y carga los **datos semilla**: el observatorio *Riguel* y los 6 filtros estándar
(L, R, G, B, Ha, OIII).

### 2.3 Frontend

```bash
cd frontend
npm install
```

---

## 3. Los dos modos de ejecución

### Desarrollo (dos servidores)

```bash
python run.py
```

Levanta backend (`:8000`) y Vite (`:5173`) a la vez, y los baja con `Ctrl+C`.
**En desarrollo se usa http://localhost:5173**, que es donde Vite sirve la app con recarga en caliente.

### Producción (un solo servidor)

```bash
cd frontend
npm run build          # genera frontend/dist
```

A partir de ahí el backend **también sirve la interfaz web**: entrás a http://localhost:8000 y listo,
sin Node. Es el modo que usan `instalar.bat` y `arrancar.bat`.

Cómo funciona (`backend/app/main.py`):

- Si existe `frontend/dist`, se monta `/assets` como archivos estáticos.
- Una ruta *catch-all* registrada **al final** devuelve `index.html` para cualquier ruta desconocida,
  así el enrutado del lado del cliente (`/observaciones/123`, `/admin/asociacion`…) funciona al recargar.
- Las rutas que empiezan con `api/` o `imagenes/`, y las de `docs`/`redoc`/`openapi.json`/`health`,
  **no** caen en el fallback: siguen devolviendo 404 si no existen.

Como las rutas se resuelven por orden de registro, cualquier endpoint nuevo que agregues gana sobre el
fallback mientras lo registres antes. Si agregás un prefijo reservado nuevo, sumalo a `RESERVED_PREFIXES`.

> ⚠️ **`frontend/dist` puede quedar viejo.** Si tocás el frontend y abrís `:8000` vas a ver la versión
> anterior: el backend sirve lo que haya compilado en disco. En desarrollo usá `:5173`, o volvé a
> correr `npm run build`.

---

## 4. Tests

**Backend** (esperado: **27 pasan, 2 se saltean**):

```bash
cd backend
pytest
```

Los 2 saltos son tests `async def` preexistentes a los que les falta el decorador
`@pytest.mark.asyncio`.

**Frontend** (esperado: **22 pasan**):

```bash
cd frontend
npm test -- --run
```

**End-to-end en un navegador real** (con un servidor corriendo y Chrome o Edge instalados):

```bash
cd frontend
npm run e2e                      # contra http://localhost:8000
npm run e2e -- --read-only       # sin modificar datos
npm run e2e -- --headed          # con la ventana del navegador a la vista
```

Apunta a otra URL con la variable `E2E_BASE_URL` (por ejemplo `http://localhost:5173` para el modo
desarrollo). Abre un navegador headless, recorre las 5 pantallas comprobando que el logo y el nombre
carguen de verdad, hace el click-through completo de `/admin/asociacion` (guardar nombre, subir logo,
quitar logo) y **restaura el estado original** al terminar.

Es la única verificación que atrapa fallas de carga de módulos, que `npm test` y `npm run build` no
pueden ver. No necesita dependencias: usa los módulos nativos de Node (requiere Node 22 o superior) y
habla con el navegador por CDP.

---

## 5. Empaquetar para distribuir

`empaquetar.ps1` genera el ZIP que se entrega a quien va a instalar la aplicación:

```powershell
powershell -ExecutionPolicy Bypass -File empaquetar.ps1
```

Qué hace: compila el frontend, arma un ZIP limpio y **lo prueba de verdad** en una carpeta nueva
(ejecuta `instalar.bat`, verifica que el servidor responda y borra la carpeta de prueba).

Queda fuera del paquete lo que es desarrollo o estado local: `node_modules`, `.venv`,
`__pycache__`, `.pytest_cache`, `riguel.db` y las fotos que hayas subido a
`backend/data/imagenes` (se conserva el logo por defecto).

---

## 6. Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `RuntimeError: Directory './data/imagenes' does not exist` | Falta la carpeta de imágenes (solo en clones anteriores al fix del `.gitkeep`) | `mkdir data\imagenes` dentro de `backend/` (en Linux/macOS: `mkdir -p data/imagenes`) |
| `The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed` | Se instaló `sqlalchemy` en vez de `sqlalchemy[asyncio]` | `pip install "sqlalchemy[asyncio]>=2.0.31,<2.2"` |
| `alembic: command not found` | El entorno virtual no está activado | Activá el venv (paso 2.1) |
| El frontend no trae datos | El backend está apagado o el puerto 8000 está ocupado | Verificá http://localhost:8000/health |
| `Address already in use` al arrancar | Ya hay algo en el puerto 8000 o 5173 | Cerrá el proceso previo o cambiá `API_PORT` en `.env` |
| El frontend queda en **pantalla en blanco** y la consola del navegador dice `does not provide an export named ...` | El servidor de Vite quedó sirviendo una versión vieja de un módulo (file-watching poco fiable en Windows). La terminal de Vite se ve limpia y `npm run build` pasa igual | Reiniciá `npm run dev`: matá el árbol de procesos de npm/vite y levantalo de nuevo. Recargar el navegador **no** alcanza |
| Cambiaste código del backend y **no se refleja**: `/health` responde, pero un endpoint nuevo da 404 | `uvicorn --reload` dejó un worker huérfano sirviendo código viejo | Matá **todos** los procesos `python run.py` y sus hijos (`multiprocessing-fork`), y arrancá de nuevo |
| Abrís `:8000` y ves la **versión anterior de la interfaz** | `frontend/dist` quedó compilado de antes | Usá `:5173` en desarrollo, o corré `npm run build` |
| Un `.bat` "salta" instrucciones o no respeta los `goto` | El archivo quedó guardado con saltos de línea **LF** en vez de **CRLF** | Volvé a guardarlo con CRLF (`(Get-Content x.bat) -join "\`r\`n"`) |

> Los tres síntomas de "no se actualiza" (Vite, uvicorn huérfano, `dist` viejo) son la misma clase de
> problema: file-watching poco fiable en Windows. Si algo no refleja el código en disco,
> **reiniciá el servidor** antes de dudar del código. `npm run e2e` detecta el caso del frontend
> automáticamente.

---

## 7. Estructura

```
observaciones/
  instalar.bat            instalador de doble clic (usuario final)
  arrancar.bat            arranca la app y abre el navegador
  empaquetar.ps1          genera el ZIP de distribución
  run.py                  orquestador de desarrollo (dos servidores)
  backend/
    app/
      main.py             FastAPI + servicio del frontend compilado
      api/v1/             observatorio, filtros, observaciones, export
      core/config.py      settings (pydantic-settings)
      services/pdf_generator.py
    alembic/versions/     migraciones
    requirements.txt      dependencias de ejecución
    requirements-dev.txt  dependencias de desarrollo
    tests/
  frontend/
    src/                  React + TypeScript + Vite + Tailwind
    e2e/                  test de navegador real (CDP)
    dist/                 compilado (generado, no versionado)
  openspec/               propuestas y artefactos del flujo SDD
```
