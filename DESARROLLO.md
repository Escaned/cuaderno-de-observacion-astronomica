# Guía de desarrollo

Documentación para **quien va a modificar el código**. Si solo querés *usar* la aplicación, mirá
[`INSTALL.md`](INSTALL.md).

- [1. Entorno](#1-entorno)
- [2. Puesta en marcha](#2-puesta-en-marcha)
- [3. Los modos de ejecución](#3-los-modos-de-ejecución)
- [4. Tests](#4-tests)
- [5. Empaquetar para distribuir](#5-empaquetar-para-distribuir)
- [6. Problemas conocidos](#6-problemas-conocidos)

---

## 1. Entorno

| Herramienta | Versión | Verificar con |
|---|---|---|
| Python | 3.12, 3.13 o 3.14 | `py -3.13 --version` |
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
py -3.13 -m venv .venv
```

> ⚠️ **Cuidado con `python` y `py -3` a secas.** Eligen la versión más nueva del equipo, y hoy la
> soportada llega hasta 3.14. Con una versión más nueva, el `pip install` de abajo falla intentando
> compilar `pydantic-core` desde el código fuente (que pide Rust). El motivo completo está explicado
> en `backend/requirements.txt`, arriba del pin de `pydantic`. `instalar.bat` acepta 3.12, 3.13 y 3.14
> y rechaza el resto con un mensaje claro.

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
python -m app.core.migrations
```

Crea las tablas y carga los **datos semilla**: la asociación *Riguel*, un observatorio
predeterminado *Riguel* y los 6 filtros estándar (L, R, G, B, Ha, OIII).

Ese módulo es el mismo que corre la aplicación al arrancar, y es más que `alembic upgrade head`:

- **Guarda una copia** de la base antes de cualquier cambio de esquema
  (`riguel.db.antes-de-actualizar-<fecha>.db`, se conservan las últimas 5). Si la actualización sale
  mal, se restaura renombrando la copia. Un arranque sin migraciones pendientes no copia nada.
- **Repara una base a medio migrar**: la versión anterior creaba `asociacion` con `create_all` y dejaba
  `observatorio` sin `color` ni `es_predeterminado`, así que la migración 0004 fallaba con
  `table asociacion already exists`. El módulo aparta esa tabla, migra y devuelve el nombre y el logo
  que la persona tenía guardados.

`arrancar.bat`, `instalar.bat` y el lanzador del ejecutable llaman a `python -m app.core.migrations`, no
al comando de Alembic: `alembic upgrade head` sigue sirviendo para desarrollo, pero **se saltea las dos
redes de seguridad**.

> La aplicación también actualiza la base **al arrancar** (`init_db` llama al mismo módulo). Así una
> versión nueva nunca queda corriendo contra una base vieja: sin eso, `create_all` creaba las tablas que
> faltaban pero jamás agregaba una columna a una tabla existente, y la pantalla fallaba con un 500 que
> parecía un error de la interfaz.

### 2.3 Frontend

```bash
cd frontend
npm install
```

---

## 3. Los modos de ejecución

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

### El lanzador (como el ejecutable, pero desde el código)

```bash
cd backend
python -m app.core.launcher
```

Es el **mismo punto de entrada que usa el `.exe`**, así que sirve para probar los caminos del modo
congelado sin construir nada: fija las variables de entorno, prepara la carpeta de datos, corre las
migraciones y recién ahí levanta el servidor y abre el navegador. Con `RIGUEL_SIN_NAVEGADOR=1` no abre
nada, y con `RIGUEL_PUERTO=8399` escucha en otro puerto: eso es lo que usan las comprobaciones
automáticas para no chocar con una aplicación que ya esté abierta.

---

## 4. Tests

**Backend** (esperado: **64 pasan, 2 se saltean**):

```bash
cd backend
pytest
```

Los 2 saltos son tests `async def` preexistentes a los que les falta el decorador
`@pytest.mark.asyncio`.

**Frontend** (esperado: **27 pasan**):

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
quitar logo, alta/edición de un observatorio y marcarlo como predeterminado), verifica el selector y
el cambio de color en `/observaciones`, y **restaura el estado original** al terminar.

Es la única verificación que atrapa fallas de carga de módulos, que `npm test` y `npm run build` no
pueden ver. No necesita dependencias: usa los módulos nativos de Node (requiere Node 22 o superior) y
habla con el navegador por CDP.

---

## 5. Empaquetar para distribuir

Hay **dos** artefactos y `empaquetar.ps1` produce los dos. Ninguno se entrega sin haberlo probado
antes: que el build termine no alcanza.

### 5.1 El ZIP con scripts (siempre)

```powershell
powershell -ExecutionPolicy Bypass -File empaquetar.ps1
```

Compila el frontend, arma un ZIP limpio y **lo prueba de verdad** en una carpeta nueva: lo descomprime,
corre `instalar.bat`, verifica que la aplicación levante y responda, y **simula una actualización**:
reemplaza la base por una de la versión anterior (0003, con la tabla `asociacion` que dejaba
`create_all` y una observación cargada), vuelve a arrancar y comprueba que la migración la repare, que
no se pierda la observación ni el nombre de la asociación y que quede la copia de seguridad. Borra la
carpeta de prueba. El resultado es `Riguel-Cuaderno-astronomico.zip`.

Es el modo que necesita Python en la máquina de destino, y el único que permite escuchar en la red
local (ver `INSTALL.md`).

### 5.2 El ejecutable (opt-in)

```powershell
powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -ConExe
```

Agrega, después de lo anterior, la construcción con PyInstaller y su propia verificación. Además del ZIP
quedan `dist\Riguel\` y `Riguel-Cuaderno-astronomico-exe.zip`: la versión que **no necesita Python**.

`-SoloEmpaquetar -ConExe` saltea la instalación completa y va derecho al ejecutable, que es lo cómodo
mientras se lo está ajustando.

PyInstaller viene en `requirements-dev.txt`, así que hace falta el `.venv` del proyecto. A diferencia de
`pydantic-core`, publica ruedas independientes de la versión de Python: no se rompe en 3.13.

Qué se arma (`riguel.spec`): una **carpeta**, no un archivo único. Un build de un-archivo se descomprime
en un temporal en cada arranque, así que tarda más y le da a los antivirus bastante más de qué
sospechar. Adentro van la interfaz compilada (`frontend/dist`), las migraciones (`backend/alembic`) y el
logo por defecto, en la misma posición relativa que tienen en el repositorio, porque el código los busca
con `paths.bundle_root()`.

`alembic.ini` **no** se empaqueta: las migraciones se manejan desde el código, que arma la configuración
de Alembic solo. Tampoco se usa compresión UPX, que es una de las causas clásicas de que Windows
Defender marque un ejecutable recién hecho como sospechoso.

### 5.3 Qué se prueba en el ejecutable

Además de arrancarlo en una carpeta limpia, sin Python disponible, la verificación cubre lo que **solo**
puede fallar una vez empaquetado:

- que la interfaz compilada, las migraciones y el logo estén adentro del paquete;
- que la base se cree **sembrada** por las migraciones (Riguel + los 6 filtros), y no vacía;
- que se pueda crear una observación, exportar el PDF y el CSV, y subir un logo;
- que todo eso **sobreviva a un reinicio**, que es lo que distingue una carpeta de datos de un temporal;
- que adopte la base de una instalación anterior **por copia**, sin llevarse el archivo original;
- que actualice una base de la versión anterior **sin perder observaciones** ni el nombre de la
  asociación, y que deje la copia de seguridad antes de tocarla;
- que escuche **solo en loopback**.

Si cualquiera falla, la corrida termina con código distinto de cero y no anuncia un paquete válido.

### 5.4 Dónde vive el estado, desde el código y congelado

| | Desde el código | Congelado |
|---|---|---|
| Base de datos | `backend/riguel.db` | `<carpeta del .exe>\data\riguel.db` |
| Imágenes | `backend/data/imagenes/` | `<carpeta del .exe>\data\imagenes\` |

Desde el código se conserva la disposición histórica **a propósito**, para no moverle la base a nadie.
Quien decide es `backend/app/core/launcher.py`, que fija `DATABASE_URL`, `IMAGES_DIR`, `API_HOST` y
`API_PORT` **antes** de importar `app.core.config`: los settings se construyen al importarse y leen el
entorno una sola vez.

Ese mismo lanzador es el punto de entrada del ejecutable, y también se puede correr desde el repo
(`python -m app.core.launcher`, parado en `backend/`). Es la forma de probar los caminos del modo
congelado sin construir nada.

Queda fuera del paquete lo que es desarrollo o estado local: `node_modules`, `.venv`,
`__pycache__`, `.pytest_cache`, `riguel.db` y las fotos que hayas subido a
`backend/data/imagenes` (se conserva el logo por defecto).

### 5.5 Publicar el release (opt-in)

```powershell
powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -ConExe -Publicar
```

Sube los ZIP ya verificados a GitHub Releases con `gh`.

> **El repositorio es privado.** La URL de descarga
> (`https://github.com/Escaned/cuaderno-de-observacion-astronomica/releases/latest/download/...`)
> pide sesión de GitHub: sirve para quien tenga acceso al repo, no para repartir el link a
> cualquiera. Si algún día el repo pasa a público, la misma URL funciona sin cambios.

Las comprobaciones corren **antes** de compilar, que es cuando todavía son baratas:

| Comprueba | Por qué |
|---|---|
| `gh` instalado y autenticado | un fallo de login a los diez minutos de build no tiene gracia |
| Versión igual en `frontend/package.json` y `backend/app/main.py` | el tag sale de ahí (`v1.1.0`); si no coinciden, el release diría una cosa y la app otra |
| Árbol limpio | un ZIP armado desde cambios sin commitear no se puede reconstruir |
| `HEAD` igual a `origin/main` | publicar código que no está en GitHub deja un release huérfano |
| Tag inexistente, local y remoto | pisar un tag confunde a quien ya descargó la versión anterior |

El release se crea **después** de que pasaron las verificaciones de 5.1 y 5.2. Al final compara el
tamaño de cada asset publicado con el del disco, los vuelve a bajar con `gh release download` y
compara el **SHA256**: que el release exista no garantiza que el archivo se pueda recuperar entero.
La comprobación de la URL fija con un pedido anónimo solo corre si el repo es público — en uno
privado devuelve 404 aunque todo esté bien, y el script avisa en vez de fallar.

`-Publicar` no se puede combinar con `-SoloEmpaquetar`: un paquete sin verificar no se publica.

Para sacar una versión nueva: subir la versión en los dos archivos, commitear, pushear y recién
ahí correr el script con `-Publicar`.

---

## 6. Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `RuntimeError: Directory './data/imagenes' does not exist` | Falta la carpeta de imágenes (solo en clones anteriores al fix del `.gitkeep`) | `mkdir data\imagenes` dentro de `backend/` (en Linux/macOS: `mkdir -p data/imagenes`) |
| `Preparing metadata (pyproject.toml) ... error`, `maturin`, `Rust` al hacer `pip install` | Hay una versión de Python sin rueda compilada de `pydantic-core` (por ejemplo la 3.15) o un `.venv` viejo que quedó armado con ella | Usá Python 3.12, 3.13 o 3.14 (`py -3.13 -m venv .venv`) y borrá el `.venv` viejo. Si el síntoma aparece con una versión dentro del rango, el `.venv` está roto: borralo y reinstalá |
| `The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed` | Se instaló `sqlalchemy` en vez de `sqlalchemy[asyncio]` | `pip install "sqlalchemy[asyncio]>=2.0.31,<2.2"` |
| `alembic: command not found` | El entorno virtual no está activado | Activá el venv (paso 2.1) |
| El frontend no trae datos | El backend está apagado o el puerto 8000 está ocupado | Verificá http://localhost:8000/health |
| `Address already in use` al arrancar | Ya hay algo en el puerto 8000 o 5173 | Cerrá el proceso previo o cambiá `API_PORT` en `.env` |
| El frontend queda en **pantalla en blanco** y la consola del navegador dice `does not provide an export named ...` | El servidor de Vite quedó sirviendo una versión vieja de un módulo (file-watching poco fiable en Windows). La terminal de Vite se ve limpia y `npm run build` pasa igual | Reiniciá `npm run dev`: matá el árbol de procesos de npm/vite y levantalo de nuevo. Recargar el navegador **no** alcanza |
| Cambiaste código del backend y **no se refleja**: `/health` responde, pero un endpoint nuevo da 404 | `uvicorn --reload` dejó un worker huérfano sirviendo código viejo | Matá **todos** los procesos `python run.py` y sus hijos (`multiprocessing-fork`), y arrancá de nuevo |
| Abrís `:8000` y ves la **versión anterior de la interfaz** | `frontend/dist` quedó compilado de antes | Usá `:5173` en desarrollo, o corré `npm run build` |
| Al guardar la asociación responde **405 Method Not Allowed** (o "método no permitido") | La pestaña abierta antes de recompilar sigue ejecutando el bundle viejo y llama a una ruta que ya no existe (`/api/v1/observatorio`); el fallback estático responde 405 a todo lo que no sea GET | Recargá con **Ctrl+Shift+R** o cerrá y volvé a abrir la app. `index.html` se sirve con `Cache-Control: no-store` para que no vuelva a pasar |
| Al guardar un observatorio la pantalla dice **"no se puede guardar el observatorio"** y `/api/v1/observatorios` responde **500** | La base quedó a medio migrar: una versión anterior creó `asociacion` con `create_all` pero dejó `observatorio` en el esquema viejo (sin `color` ni `es_predeterminado`) | Cerrá la app y volvé a abrirla: `init_db` y `arrancar.bat` corren `alembic upgrade head`. Si la base quedó con una tabla de más, mirá el error del arranque; el detalle de la migración está en `backend/alembic/versions/0004_observatorios.py` |
| Un `.bat` "salta" instrucciones o no respeta los `goto` | El archivo quedó guardado con saltos de línea **LF** en vez de **CRLF** | Volvé a guardarlo con CRLF. Aplica a `.bat`, `.cmd` **y `.ps1`**: `.gitattributes` los clava en CRLF, y editarlos con una herramienta que escribe LF rompe la regla |
| `Failed to load Python DLL ... _internal\python313.dll` al abrir el `.exe` | El ejecutable se separó de su carpeta `_internal` | No tiene arreglo desde el código: PyInstaller corta en el *bootloader*, antes de que corra una sola línea de Python, así que ningún manejador nuestro llega a ejecutarse. La única respuesta es copiar la carpeta `Riguel` completa, y por eso `INSTALL.md` lo avisa |
| La verificación del ejecutable dice `Deberia haber 6 filtros y hay 1` | En PowerShell **5.1** `@(Invoke-RestMethod ...)` en una sola línea da 1: la llamada entrega el arreglo como **un solo objeto** en vez de enumerarlo. En PowerShell 7 lo enumera, así que el error solo aparece corriendo el script como se documenta (`powershell -File`), no a mano en `pwsh` | Asigná primero y envolvé después (`$x = Invoke-RestMethod ...; @($x).Count`), o usá un endpoint que devuelva un entero (`/count`). Ya está resuelto así en `empaquetar.ps1` |
| `No escucha en 127.0.0.1 (escucha en: )` en la verificación del ejecutable, o `uvicorn` huérfano que impide borrar el temporal y rompe la corrida siguiente | `Get-NetTCPConnection -State Listen` puede devolver el estado vacío y no encontrar el socket en algunas máquinas, y `arrancar.bat` deja al servidor como hijo de `cmd.exe`, así que matar solo el `cmd` no alcanza | Ya está resuelto en `empaquetar.ps1`: los sockets se detectan por `RemotePort 0` y el `cmd` se mata con el árbol entero (`taskkill /T`). Si te pasa con una copia vieja, cerrá los `python.exe` y borrá `%TEMP%\riguel-pack` |
| Una comprobación automática no ve la aplicación recién levantada, pero el navegador la abre sin problema | `localhost` en Windows resuelve **primero a `::1`** (IPv6) y el servidor escucha solo en IPv4. `Invoke-WebRequest` se come el timeout del IPv6 antes de reintentar; el navegador hace *Happy Eyeballs* y no sufre eso | En las comprobaciones automáticas usá siempre `http://127.0.0.1:<puerto>`. La dirección que se le muestra a la persona —y la que abre el navegador— sigue siendo `http://localhost:<puerto>` |

> Los tres síntomas de "no se actualiza" (Vite, uvicorn huérfano, `dist` viejo) son la misma clase de
> problema: file-watching poco fiable en Windows. Si algo no refleja el código en disco,
> **reiniciá el servidor** antes de dudar del código. `npm run e2e` detecta el caso del frontend
> automáticamente.

---

## 7. Estructura

```
observaciones/
  instalar.bat            instalador de doble clic (usuario final, necesita Python)
  arrancar.bat            arranca la app y abre el navegador
  abrir-navegador.ps1     espera a que el servidor responda y abre el navegador
  empaquetar.ps1          genera el ZIP y, con -ConExe, el ejecutable
  riguel.spec             receta de PyInstaller (carpeta, consola, sin UPX)
  run.py                  orquestador de desarrollo (dos servidores)
  backend/
    app/
      main.py             FastAPI + servicio del frontend compilado
      api/v1/             asociacion, observatorios, filtros, observaciones, export
      core/config.py      settings (pydantic-settings)
      core/launcher.py    punto de entrada del ejecutable
      core/paths.py       donde esta cada cosa, congelado o desde el codigo
      core/migrations.py  corre Alembic desde el codigo, sin alembic.ini
      services/pdf_generator.py
    alembic/versions/     migraciones (y la semilla)
    data/imagenes/        imagenes y logo (desde el codigo)
    tests/
    requirements.txt      dependencias de ejecucion
    requirements-dev.txt  dependencias de desarrollo
  frontend/
    src/                  React + TypeScript + Vite + Tailwind
    e2e/                  test de navegador real (CDP)
    dist/                 compilado (generado, no versionado)
  dist/                   ejecutable construido (generado, no versionado)
  openspec/               propuestas y artefactos del flujo SDD
```
