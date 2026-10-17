# Riguel — Cuaderno de Campo Astronómico

Aplicación para registrar y consultar las observaciones del grupo, con informes en PDF.

Funciona **en tu propia computadora**: no necesita internet, ni cuenta, ni servidor externo. Tus datos
quedan en tu disco.

---

## Lo que necesitás

| | |
|---|---|
| **Sistema** | Windows 10 u 11 |
| **Navegador** | Chrome, Edge, Firefox o cualquier otro |

Eso es todo. **No hace falta instalar Python, ni Node.js, ni nada.** El programa ya viene listo para
usar.

---

## Instalación (2 pasos)

### Paso 1 — Descomprimir

Descomprimí el ZIP donde quieras (por ejemplo en `Documentos`). Adentro vas a encontrar una carpeta
`Riguel` con dos cosas:

```
Riguel\
  Riguel.exe        <- el programa
  _internal\        <- lo que el programa necesita para funcionar
```

> ⚠️ **La carpeta se usa entera.** `Riguel.exe` solo no funciona: necesita la carpeta `_internal` que
> está al lado. Si lo sacás de ahí, o si lo mandás solo por correo o WhatsApp, no arranca.
>
> Para moverlo de una computadora a otra, copiá **la carpeta `Riguel` completa**.

> ⚠️ **Descomprimí el ZIP antes de usarlo.** Si hacés doble clic adentro del ZIP comprimido, o desde
> una carpeta temporal, los datos se pueden perder.

### Paso 2 — Doble clic en `Riguel.exe`

Se abre una ventana negra con el progreso y, unos segundos después, tu navegador en:

**http://localhost:8000**

Si el navegador no se abre, escribí esa dirección a mano.

> ⚠️ **La primera vez, Windows puede avisarte que "Windows protegió tu PC".** Es normal y tiene
> explicación: el programa no está firmado digitalmente (firmarlo sale plata) y Windows desconfía de
> cualquier ejecutable nuevo que baje de internet.
>
> Para continuar: clic en **Más información** y después en **Ejecutar de todas formas**. Se pregunta
> una sola vez.

La ventana negra es el motor de la aplicación. **Mientras esté abierta, la aplicación funciona.** Si
la cerrás, se cierra la aplicación.

---

## Uso diario

| Quiero… | Cómo |
|---|---|
| Abrir la aplicación | Doble clic en `Riguel.exe` |
| Cerrarla | Cerrá la **ventana negra** |
| Tenerla a mano | Clic derecho en `Riguel.exe` → *Anclar a la barra de tareas* |
| Cambiar el nombre o el logo del grupo | Menú lateral → **Asociación** |
| Descargar un informe | Pantalla **Exportar** |
| Registrarlo todo de nuevo | No hace falta: los datos quedan guardados entre sesiones |

La aplicación **no se instala como servicio**: se abre cuando la arrancás y se cierra cuando cerrás la
ventana. Nada queda corriendo de fondo.

**Tu primera observación:** hacé clic en *Nueva observación* y seguí el asistente de 3 pasos
(**datos de la noche** → **sesiones de captura** → **calibraciones**). La mayoría de los campos se
completan solos con valores razonables.

---

## Dónde están tus datos (importante)

Todo vive en la carpeta `data`, adentro de la carpeta de la aplicación:

| Qué | Dónde |
|---|---|
| Observaciones, filtros, configuración | `data\riguel.db` |
| Fotos y el logo | `data\imagenes\` |

**Para hacer una copia de seguridad alcanza con copiar esos dos.** Guardalos juntos y vas a poder
restaurar todo en cualquier momento: pegalos de vuelta en su lugar y listo.

> El archivo `riguel.db` es la base de datos completa. Si lo borrás, la próxima vez que arranques se
> crea una nueva y **vacía**.

---

## Si venías de la versión anterior (la de `instalar.bat`)

Tus observaciones **no se pierden**. La versión nueva las adopta sola:

1. Copiá a un lugar seguro tu carpeta `backend\riguel.db` — es tu base con todo lo que cargaste.
2. En la carpeta nueva, creá una carpeta llamada `backend` y pegá ahí ese `riguel.db`.
3. Abrí `Riguel.exe`. La ventana negra te va a avisar que encontró la base anterior y la copió.
   El archivo viejo queda donde estaba, no se toca.
4. **Las fotos y el logo que hayas subido** sí hay que copiarlos a mano: pasalos de
   `backend\data\imagenes\` a `data\imagenes\`. El logo por defecto se repone solo.

---

## Si algo no funciona

| Qué pasa | Qué hacer |
|---|---|
| **Windows avisa que "protegió tu PC"** | *Más información* → *Ejecutar de todas formas*. Explicado arriba |
| **Dice `Failed to load Python DLL`** | Sacaste `Riguel.exe` de su carpeta. Volvelo a poner junto a la carpeta `_internal` |
| **Dice que el puerto 8000 está ocupado** | Ya hay otra copia abierta o algún programa usando ese puerto. Cerrá la otra ventana negra y volvé a intentar |
| **El navegador abre pero la página está en blanco** | Esperá unos segundos y recargá (`F5`). Si sigue, cerrá la ventana negra y abrí de nuevo |
| **La ventana negra se cierra al instante** | Sacale una foto al texto que llegó a mostrar: ahí está el motivo |
| **Quiero empezar de cero** | Con la aplicación cerrada, borrá `data\riguel.db` y volvé a abrirla |
| **Quiero guardar una copia de todo** | Copiá `data\riguel.db` y `data\imagenes\` a un pendrive. Ver *Dónde están tus datos* |

Si nada de esto lo resuelve, pasale a quien te dio el programa **el texto completo de la ventana
negra**. Ahí está el motivo.

---

## Para varios equipos de la red (opcional)

El ejecutable escucha **solo en tu computadora**: nadie de la red puede entrar, ni siquiera para mirar.
Es a propósito, para que tus observaciones no queden a la vista de cualquiera en una red compartida o
pública.

Si el grupo necesita que varias personas entren desde sus propias máquinas, eso se puede hacer con la
**otra forma de distribución** (la que se instala con `instalar.bat`), que lo permite si lo pedís a
propósito. Pedile a quien te dio el programa esa versión.

---

## Documentación técnica

Si necesitás modificar el código, compilar el frontend, construir el ejecutable o correr los tests,
mirá [`DESARROLLO.md`](DESARROLLO.md).
