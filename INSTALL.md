# Guía de instalación

**Objetivo:** tener *Riguel Cuaderno de Campo Astronómico* corriendo en tu máquina en unos 5 minutos.

Es una app local: backend **FastAPI** + frontend **React**, con base **SQLite** en un archivo (`backend/riguel.db`). No necesitás base de datos externa, ni Docker, ni servicios en la nube. Todo corre en tu computadora.

> **Camino rápido (TL;DR):** clonar → `pip install` → `alembic upgrade head` → `npm install` → `python run.py` → abrir http://localhost:5173

---

## 1. Requisitos previos

| Herramienta | Versión mínima | Verificar con |
|---|---|---|
| Python | 3.12+ | `python --version` |
| Node.js | 20+ | `node --version` |
| npm | 10+ | `npm --version` |
| Git | cualquiera | `git --version` |

Si alguno falta, instalalo antes de seguir. En Windows, Python y Node se consiguen desde python.org y nodejs.org.

---

## 2. Instalación paso a paso

### 2.1 Clonar el repositorio

```bash
git clone <URL_DEL_REPO> observaciones
cd observaciones
```

### 2.2 Backend

Entrá a la carpeta del backend y creá un entorno virtual:

```bash
cd backend
python -m venv .venv
```

Activalo según tu sistema:

| Sistema | Comando |
|---|---|
| Windows (PowerShell) | `.venv\Scripts\Activate.ps1` |
| Windows (CMD) | `.venv\Scripts\activate.bat` |
| Linux / macOS | `source .venv/bin/activate` |

Instalá las dependencias:

```bash
pip install -r requirements.txt
```

### 2.3 Crear la base de datos

```bash
alembic upgrade head
```

Esto crea las tablas y carga los **datos semilla**: el observatorio *Riguel* (Madrid) y los 6 filtros estándar (L, R, G, B, Ha, OIII). Ya podés registrar observaciones sin configurar nada más.

### 2.4 Frontend

```bash
cd ../frontend
npm install
```

### 2.5 Arrancar todo

Volvé a la raíz y ejecutá el orquestador:

```bash
cd ..
python run.py
```

Levanta los dos servidores a la vez y los baja con `Ctrl+C`.

| Servicio | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| Documentación de la API (Swagger) | http://localhost:8000/docs |

---

## 3. Arranque manual (dos terminales)

Si preferís ver los logs de cada proceso por separado:

**Terminal 1, backend:**
```bash
cd backend
python run.py
```

**Terminal 2, frontend:**
```bash
cd frontend
npm run dev
```

> 💡 Si usás el entorno virtual, **activalo antes** de correr `python run.py` desde la raíz. El orquestador reutiliza el mismo intérprete de Python, así que si no está activado el backend arrancaría sin las dependencias.

---

## 4. Verificar que quedó bien

| Check | Cómo | Resultado esperado |
|---|---|---|
| Backend vivo | http://localhost:8000/health | `{"status":"ok","service":"riguel-caderno-api"}` |
| Base migrada | `cd backend` y luego `alembic current` | `0002 (head)` |
| Datos semilla | http://localhost:8000/api/v1/filtros | 6 filtros |
| Frontend | http://localhost:5173 | Dashboard con menú lateral |

Checklist:

- [ ] `/health` responde `ok`
- [ ] `alembic current` muestra `0002`
- [ ] `/api/v1/filtros` devuelve 6 filtros
- [ ] El frontend carga el Dashboard

---

## 5. Variables de entorno (opcional)

**La app arranca sin configurar nada**: todas las variables tienen un valor por defecto razonable.

Si querés personalizar algo, copiá el archivo de ejemplo **dentro de `backend/`** (que es el directorio de trabajo del backend):

```bash
copy .env.example backend\.env     # Windows
cp .env.example backend/.env       # Linux / macOS
```

| Variable | Default | Para qué sirve |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./riguel.db` | Ubicación de la base SQLite |
| `API_HOST` | `0.0.0.0` | Interfaz donde escucha el backend |
| `API_PORT` | `8000` | Puerto del backend |
| `FRONTEND_URL` | `http://localhost:5173` | Origen permitido por CORS |
| `TIMEZONE` | `Europe/Madrid` | Zona horaria |
| `OBS_NOMBRE` | `Riguel` | Nombre del observatorio (semilla inicial) |
| `OBS_LAT` / `OBS_LON` | `40.4168` / `-3.7038` | Coordenadas del observatorio |
| `OBS_ALT` | `650.0` | Altitud en metros |
| `OBS_TZ` | `Europe/Madrid` | Zona horaria del observatorio |
| `IMAGES_DIR` | `./data/imagenes` | Carpeta de imágenes estáticas |
| `IMAGES_URL_PREFIX` | `/imagenes` | Ruta pública de las imágenes |
| `API_KEY` | (vacío) | Opcional, para exponer en LAN |

---

## 6. Ejecutar los tests

**Backend** (esperado: 22 pasan, 2 se saltean):
```bash
cd backend
pytest
```

**Frontend** (esperado: 18 pasan):
```bash
cd frontend
npm test -- --run
```

---

## 7. Problemas conocidos

| Síntoma | Causa | Solución |
|---|---|---|
| `RuntimeError: Directory './data/imagenes' does not exist` | Falta la carpeta de imágenes (solo en clones anteriores al fix del `.gitkeep`) | `mkdir data\imagenes` dentro de `backend/` (en Linux/macOS: `mkdir -p data/imagenes`) |
| `WeasyPrint could not import some external libraries` | `weasyprint` figura en `requirements.txt` pero la app **no lo usa**; en Windows necesita librerías GTK del sistema | Ignoralo, no afecta a la app. Para sacarlo del medio: `pip uninstall weasyprint` |
| `alembic: command not found` | El entorno virtual no está activado | Activá el venv (paso 2.2) |
| El frontend no trae datos | El backend está apagado o el puerto 8000 está ocupado | Verificá http://localhost:8000/health |
| `Address already in use` al arrancar | Ya hay algo en el puerto 8000 o 5173 | Cerrá el proceso previo o cambiá `API_PORT` en `.env` |

---

## 8. Siguiente paso

Abrí http://localhost:5173/observaciones/new y creá tu primera observación.

El asistente tiene 3 pasos: **datos de la noche** → **sesiones de captura** → **calibraciones**. El campo **FWHM (arcsec)** acepta valores entre **0.5 y 10.0**.
