# Riguel Cuaderno de Campo Astronómico

Aplicación web **local** para el grupo Riguel de astronomía: registra, gestiona y exporta
observaciones con los metadatos completos de fotografía (sesiones de exposición, frames de
calibración).

Corre entera en tu computadora con SQLite como base de datos. No necesita internet, ni Docker, ni
servidores externos.

---

## Para usarla (sin tocar código)

Solo necesitás **Windows con Python 3.12, 3.13 o 3.14**: no hace falta Node.js.

El último paquete se descarga desde **[Releases](https://github.com/Escaned/cuaderno-de-observacion-astronomica/releases/latest)**:
`Riguel-Cuaderno-astronomico-exe.zip` no necesita Python (descomprimir y doble clic en `Riguel.exe`),
y `Riguel-Cuaderno-astronomico.zip` es el que se instala con los pasos de abajo.

1. Descomprimí el paquete
2. Doble clic en **`instalar.bat`**
3. Doble clic en **`arrancar.bat`** → se abre el navegador en http://localhost:8000

Guía completa, uso diario y solución de problemas: **[`INSTALL.md`](INSTALL.md)**

---

## Para desarrollar

Python 3.12, 3.13 o 3.14, Node.js 20+ y npm 10+.

```bash
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

cd backend && alembic upgrade head && cd ..
cd frontend && npm install && cd ..

python run.py          # backend :8000 + Vite :5173 (usá :5173 en desarrollo)
```

Guía completa, tests, modo producción y problemas conocidos: **[`DESARROLLO.md`](DESARROLLO.md)**

---

## Stack

| | |
|---|---|
| **Backend** | Python 3.12–3.14, FastAPI, SQLAlchemy 2 (async), SQLite, Alembic |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query |
| **PDF / CSV** | ReportLab, csv + zipfile |
| **Base de datos** | SQLite en un archivo (`backend/riguel.db`) |

---

## Dos modos de ejecución

| | Servidores | URL | Cuándo |
|---|---|---|---|
| **Producción** | 1 (FastAPI sirve la interfaz compilada) | http://localhost:8000 | Uso normal e instalación final |
| **Desarrollo** | 2 (FastAPI + Vite) | http://localhost:5173 | Programando, con recarga en caliente |

En producción, `backend/app/main.py` sirve `frontend/dist` y resuelve el enrutado del cliente con un
fallback a `index.html`, dejando intactas las rutas de `api/`, `imagenes/` y la documentación.

---

## Funcionalidades

- **Dashboard**: nombre de la asociación, observatorios con coordenadas y altitud, estadísticas y observaciones recientes
- **Observaciones**: lista con búsqueda y filtros; alta con asistente de 3 pasos
  (datos de la noche → sesiones de captura → calibraciones). El observatorio activo se elige
  arriba y tiñe la pantalla con su color para no cargar datos en el sitio equivocado
- **Detalle**: vista completa con edición, duplicado y exportación
- **Exportación**: CSV (tabla individual o ZIP con todas) y PDF (informe de noche o de campaña)
- **Filtros**: catálogo administrable con reordenamiento arrastrando
- **Asociación**: nombre del grupo y logo configurables, y varios observatorios con nombre,
  coordenadas, altitud y color; uno queda como predeterminado
- **Tema** claro/oscuro con persistencia

---

## Estructura

```
observaciones/
├── instalar.bat              instalador de doble clic (usuario final)
├── arrancar.bat              arranca la app y abre el navegador
├── abrir-navegador.ps1       espera al servidor y abre el navegador
├── empaquetar.ps1            genera y verifica el ZIP de distribución
├── run.py                    orquestador de desarrollo (dos servidores)
├── INSTALL.md                guía para quien instala
├── DESARROLLO.md             guía para quien programa
├── backend/
│   ├── app/
│   │   ├── main.py           FastAPI + servicio del frontend compilado
│   │   ├── api/v1/           routers REST (asociacion, observatorios, filtros, observaciones, export)
│   │   ├── core/             configuración, base de datos, seguridad
│   │   ├── crud/             operaciones de datos
│   │   ├── models/           modelos SQLAlchemy
│   │   ├── schemas/          esquemas Pydantic
│   │   └── services/         generadores de PDF y CSV
│   ├── alembic/versions/     migraciones
│   ├── data/imagenes/        logo por defecto y fotos subidas
│   ├── tests/                tests de pytest
│   ├── requirements.txt      dependencias de ejecución
│   └── requirements-dev.txt  dependencias de desarrollo
├── frontend/
│   ├── src/                  React + TypeScript
│   ├── e2e/                  test de navegador real (CDP, sin dependencias)
│   └── dist/                 compilado (generado, no versionado)
└── openspec/                 propuestas y artefactos del flujo SDD
```

---

## Documentación de la API

Con el backend levantado:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Variables de entorno

Todas tienen valores por defecto razonables: la aplicación arranca sin configurar nada.
Ver `.env.example` para la lista completa.

## Licencia

Uso interno — Grupo Riguel de Astronomía.
