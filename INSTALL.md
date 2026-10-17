# Riguel — Cuaderno de Campo Astronómico

Aplicación para registrar y consultar las observaciones del grupo, con informes en PDF.

Funciona **en tu propia computadora**: no necesita internet, ni cuenta, ni servidor externo. Tus datos
quedan en tu disco.

---

## Lo que necesitás

| | |
|---|---|
| **Sistema** | Windows 10 u 11 |
| **Python** | **3.12 o 3.13** — [descargar](https://www.python.org/downloads/windows/) |
| **Navegador** | Chrome, Edge, Firefox o cualquier otro |

Eso es todo. **No hace falta Node.js, ni Docker, ni instalar una base de datos.**

> ⚠️ **Necesitás 3.12 o 3.13. Con 3.14 la instalación falla.** No es un capricho: una de las
> dependencias viene compilada distinto para cada versión de Python, y todavía no hay versión
> compilada para 3.14.
>
> Si ya tenés 3.14 instalado no hace falta desinstalarlo: instalá 3.13 al lado y listo.

> ⚠️ Al instalar Python, marcá la casilla **Add python.exe to PATH** en la primera pantalla del
> instalador. Si no lo hacés, después el instalador de la aplicación no va a encontrar Python.

Si preferís la línea de comandos, en Windows también sirve:

```powershell
winget install -e --id Python.Python.3.13
```

---

## Instalación (2 pasos)

### Paso 1 — Instalar

Descomprimí el ZIP donde quieras (por ejemplo en `Documentos`) y hacé **doble clic en `instalar.bat`**.

Se abre una ventana negra que va mostrando el progreso. Tarda **un par de minutos** la primera vez,
porque descarga las dependencias. Cuando termine vas a ver:

```
============================================================
  INSTALACION COMPLETA
============================================================
```

> ⚠️ **Descomprimí el ZIP antes de usarlo.** Si hacés doble clic adentro del ZIP comprimido, o desde
> una carpeta temporal, la instalación puede fallar.

### Paso 2 — Usar

Hacé **doble clic en `arrancar.bat`**. Se abre el navegador solo, en:

**http://localhost:8000**

Si el navegador no se abre, escribí esa dirección a mano.

---

## Uso diario

| Quiero… | Cómo |
|---|---|
| Abrir la aplicación | Doble clic en `arrancar.bat` |
| Cerrarla | Cerrá la **ventana negra** (o `Ctrl+C` adentro) |
| Cambiar el nombre o el logo del grupo | Menú lateral → **Asociación** |
| Descargar un informe | Pantalla **Exportar** |
| Registrarlo todo de nuevo | No hace falta: los datos quedan guardados entre sesiones |

La aplicación **no se instala como servicio**: se abre cuando la arrancás y se cierra cuando cerrás
la ventana. Nada queda corriendo de fondo.

**Tu primera observación:** hacé clic en *Nueva observación* y seguí el asistente de 3 pasos
(**datos de la noche** → **sesiones de captura** → **calibraciones**). La mayoría de los campos se
completan solos con valores razonables.

---

## Dónde están tus datos (importante)

Todo vive dentro de la carpeta de la aplicación:

| Qué | Dónde |
|---|---|
| Observaciones, filtros, configuración | `backend\riguel.db` |
| Fotos y el logo | `backend\data\imagenes\` |

**Para hacer una copia de seguridad alcanza con copiar esos dos.** Guardalos juntos y vas a poder
restaurar todo en cualquier momento: pegalos de vuelta en su lugar y listo.

> El archivo `riguel.db` es la base de datos completa. Si lo borrás, la próxima vez que arranques se
> crea una nueva y **vacía**.

---

## Si algo no funciona

| Qué pasa | Qué hacer |
|---|---|
| **`instalar.bat` dice que no encuentra Python** | Instalá Python desde [python.org](https://www.python.org/downloads/windows/) marcando *Add python.exe to PATH*. Después cerrá la ventana y volvé a ejecutar `instalar.bat` |
| **`instalar.bat` dice que tu Python no sirve para esta aplicación** | Hace falta 3.12 o 3.13. Si tenés 3.14, instalá la 3.13 al lado (no hace falta desinstalar nada): `winget install -e --id Python.Python.3.13` |
| **Mientras instala las dependencias aparece `Preparing metadata (pyproject.toml)`, `maturin` o `Rust`** | El Python de tu equipo no sirve para esta aplicación (casi siempre es 3.14). Instalá 3.13 y después **borrá la carpeta `.venv`** que está junto a `instalar.bat`, y volvé a ejecutarlo. El paso de borrar `.venv` no es opcional: si queda, se reutiliza el entorno viejo y el error se repite |
| **Dice `El entorno que habia es de Python ... y ahora uso ...`** | No es un error: `instalar.bat` se dio cuenta de que cambiaste de versión de Python, borró el entorno viejo y lo armó de nuevo |
| **La ventana negra se cierra al instante** | Ejecutá `instalar.bat` desde una terminal para leer el error: abrí *Símbolo del sistema*, entrá a la carpeta con `cd` y escribí `instalar.bat` |
| **"Address already in use"** al arrancar | Ya hay algo usando el puerto 8000 (a veces, una aplicación anterior que quedó abierta). Cerrá la ventana negra que hayas dejado abierta y volvé a intentar |
| **El navegador abre pero la página está en blanco** | Esperá unos segundos y recargá (`F5`). Si sigue, arrancá de nuevo con `arrancar.bat` |
| **La instalación se corta por la mitad** | Casi siempre es internet. Volvé a ejecutar `instalar.bat`: retoma lo que ya había bajado |
| **Quiero empezar de cero** | Borrá `backend\riguel.db` y ejecutá `instalar.bat` otra vez |

Si nada de esto lo resuelve, pasale a quien te dio el programa **el texto completo de la ventana
negra**. Ahí está el motivo.

---

## Para varios equipos de la red (opcional)

Por defecto la aplicación solo es accesible **desde tu propia computadora**. Para que otras personas
de la red entren desde sus máquinas, hay que escuchar en toda la red.

Editá `arrancar.bat` con el Bloc de notas y cambiá esta línea:

```bat
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

por:

```bat
"..\.venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Después los demás entran con `http://TU-IP-LOCAL:8000` (por ejemplo `http://192.168.1.50:8000`).
Vas a tener que permitir el paso en el Firewall de Windows la primera vez.

> ⚠️ Al hacer esto, la aplicación **queda sin contraseña** para cualquiera que esté en la misma red.
> No lo hagas en una red pública o compartida.

---

## Documentación técnica

Si necesitás modificar el código, compilar el frontend o correr los tests, mirá
[`DESARROLLO.md`](DESARROLLO.md).
