# Riguel Cuaderno de Campo Astronomico

Aplicacion web local para el grupo Riguel de astronomia. Registra, gestiona y exporta observaciones astronomicas con metadatos completos de fotografia (sesiones de exposicion, frames de calibracion).

## Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy (async), SQLite, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, TanStack Query
- **Base de datos**: SQLite (archivo local `riguel.db`)

## Requisitos

- Python 3.12+
- Node.js 20+
- npm 10+

## Inicio rapido

### Opcion 1: Orquestador (recomendado)

```bash
python run.py
```

Levanta ambos servidores:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

### Opcion 2: Manual

**Backend:**
```bash
cd backend
pip install -r requirements.txt
python run.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Documentacion API

Una vez levantado el backend, la documentacion interactiva esta disponible en:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Estructura del proyecto

```
observaciones/
├── backend/
│   ├── app/
│   │   ├── api/v1/         # Routers REST
│   │   ├── core/           # Config, database, security
│   │   ├── crud/           # Operaciones CRUD
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   └── services/       # CSV/PDF generators
│   ├── alembic/            # Migraciones
│   ├── tests/              # Tests pytest
│   ├── run.py              # Entry point backend
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # UI components + wizard
│   │   ├── hooks/          # TanStack Query hooks
│   │   ├── pages/          # Dashboard, List, Detail, Admin
│   │   ├── services/       # API client (axios)
│   │   ├── types/          # TypeScript interfaces
│   │   └── utils/          # Date/format helpers
│   ├── package.json
│   └── vite.config.ts
├── data/imagenes/          # Imagenes estaticas
├── run.py                  # Orquestador root
└── README.md
```

## Funcionalidades

- **Dashboard**: Resumen de observaciones, estadisticas, observaciones recientes
- **Observaciones**: Lista con busqueda y filtros, creacion con wizard de 3 pasos
- **Wizard**: Datos de noche -> Sesiones de captura -> Calibraciones
- **Detalle**: Vista completa con edicion, duplicado y exportacion
- **Exportacion**: CSV (tabla individual o ZIP con todas), PDF (informe noche o campana)
- **Admin filtros**: Gestion de catalogo de filtros con reordenamiento drag-drop
- **Dark mode**: Tema oscuro/claro con persistencia en localStorage

## Testing

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

## Variables de entorno

Ver `.env.example` para la lista completa de variables configurables.

## Licencia

Uso interno - Grupo Riguel de Astronomia
"# Astronomic_book" 
