<#
    empaquetar.ps1
    Genera el ZIP de distribucion de "Riguel - Cuaderno de Campo Astronomico".

    Uso:
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -SoloEmpaquetar
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -ConExe
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -SoloEmpaquetar -ConExe
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -ConExe -Publicar

    Que hace:
      1. Compila el frontend (npm run build)
      2. Copia el proyecto a una carpeta temporal, dejando afuera todo lo de desarrollo
      3. Genera el ZIP
      4. Lo descomprime en una carpeta limpia, corre instalar.bat y comprueba
         que la aplicacion levante y responda. Despues simula una ACTUALIZACION:
         reemplaza la base por una de la version anterior y verifica que la
         migracion la repare, guarde una copia y no pierda ni una observacion.
      5. (solo con -ConExe) Construye el ejecutable con PyInstaller y lo prueba
         entero: en una carpeta limpia, con una base de datos de por medio y
         reiniciandolo, para comprobar que lo que guarda sobrevive. Incluye el
         mismo caso de actualizacion sobre data\riguel.db.
      6. (solo con -Publicar) Crea el release en GitHub con los ZIP ya verificados.

    Los pasos 4 y 5 son los importantes: son la unica forma de detectar que una
    dependencia falte o que algo se rompa solo al instalar desde cero. El paso 5
    comprueba ademas cosas que SOLO pueden fallar una vez empaquetado, como que la
    interfaz compilada se encuentre adentro del paquete.

    -SoloEmpaquetar saltea el paso 4. Combinado con -ConExe saltea la instalacion
    completa y va derecho al ejecutable, que es lo comodo mientras se lo esta
    ajustando.

    -Publicar sube el resultado a GitHub Releases y NO se puede combinar con
    -SoloEmpaquetar: un paquete sin verificar no se publica. Antes de tocar la red
    comprueba que la version de frontend/package.json y la de backend/app/main.py
    coincidan, que el arbol este limpio, que HEAD sea origin/main y que el tag no
    exista. El release se crea recien cuando TODAS las verificaciones pasaron, y
    despues lo baja de vuelta para comparar el SHA256. Con un repositorio privado
    avisa que la URL publica pide sesion de GitHub: el release sirve para quien
    tenga acceso al repo, no para repartir el link a cualquiera.
#>

param(
    [switch]$SoloEmpaquetar,
    [switch]$ConExe,
    [switch]$Publicar
)

$ErrorActionPreference = 'Stop'

$raiz = if ($PSScriptRoot) { $PSScriptRoot } else { (Get-Location).Path }
Set-Location $raiz

$nombre     = 'Riguel-Cuaderno-astronomico'
$zipDestino = Join-Path $raiz "$nombre.zip"

$tmpBase = Join-Path $env:TEMP 'riguel-pack'
$stage   = Join-Path $tmpBase $nombre
$prueba  = Join-Path $tmpBase 'prueba-desde-cero'

$puerto = 8000

# Cuantos pasos va a anunciar el script, para que la numeracion no mienta segun
# los interruptores que se hayan usado. Sin ninguno son 4, como siempre.
$pasos = 3
if (-not $SoloEmpaquetar) { $pasos++ }
if ($ConExe)              { $pasos++ }
if ($Publicar)            { $pasos++ }
# El ejecutable va antes de publicar, y con -SoloEmpaquetar la verificacion del ZIP
# no existe, asi que su numero baja para que la cuenta no salte de 3 a 5.
$pasoExe = if ($SoloEmpaquetar) { 4 } else { 5 }
$pasoPublicar = $pasos

# Carpeta donde queda el ejecutable listo para repartir. Puede que se pise a si
# misma entre corridas, asi que se limpia antes de construir.
$distExe = Join-Path $raiz 'dist'

function Escribir-Paso($texto) {
    Write-Host ''
    Write-Host "== $texto" -ForegroundColor Cyan
}
function Escribir-Ok($texto)   { Write-Host "   OK   $texto" -ForegroundColor Green }
function Escribir-Fallo($texto){ Write-Host "   FALLO  $texto" -ForegroundColor Red }
function Escribir-Aviso($texto){ Write-Host "   !    $texto" -ForegroundColor Yellow }

# Sockets que estan ESCUCHANDO en un puerto.
#
# No sirve filtrar con -State Listen: en algunas maquinas el proveedor CIM
# devuelve el estado vacio y la consulta no encuentra nada, aunque haya un
# servidor escuchando y los pedidos HTTP respondan. Un socket en escucha se
# reconoce porque no tiene puerto remoto (RemotePort 0); los de cliente, si.
function Get-Escuchando($p) {
    @(Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue |
        Where-Object { $_.RemotePort -eq 0 })
}

# Baja el servidor aunque haya quedado como hijo de cmd.exe. `taskkill` se llama a
# traves de cmd para que PowerShell no convierta su "no se encontro el proceso" en
# un error cuando el servidor ya se cayo solo.
function Stop-Aplicacion($proceso) {
    Get-Escuchando $puerto |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    if ($proceso) { cmd /c "taskkill /PID $($proceso.Id) /T /F >nul 2>&1" }
    for ($i = 0; $i -lt 20; $i++) {
        if (-not (Get-Escuchando $puerto)) { break }
        Start-Sleep -Milliseconds 500
    }
}

# Arma una base como la dejaba la version anterior: en 0003, con la tabla
# `asociacion` que creaba create_all y con una observacion cargada. Es el estado en
# el que una actualizacion puede romper, y el unico que importa de verdad: la
# persona ya tiene sus datos adentro.
#
# Usa el python y la carpeta de migraciones que le pasen, para servir tanto al
# paquete recien instalado como al ejecutable.
function New-BaseVersionAnterior($pythonExe, $alembicDir, $dbPath) {
    # Se parte de cero a proposito: lo que se simula es una instalacion anterior, no
    # una base que se actualiza dos veces.
    foreach ($sobra in @($dbPath, "$dbPath-wal", "$dbPath-shm")) {
        if (Test-Path $sobra) { Remove-Item $sobra -Force }
    }
    $script = Join-Path $env:TEMP "riguel-base-vieja-$([guid]::NewGuid().ToString('N')).py"
    @'
import os, sqlite3, sys
from alembic import command
from alembic.config import Config

alembic_dir, database = sys.argv[1], sys.argv[2]
# `alembic/env.py` importa `app`, y eso solo funciona si `backend/` esta en el path.
sys.path.insert(0, os.path.dirname(alembic_dir))

config = Config()
config.set_main_option("script_location", alembic_dir)
config.set_main_option("sqlalchemy.url", "sqlite+aiosqlite:///" + database.replace("\\", "/"))
command.upgrade(config, "0003")

conexion = sqlite3.connect(database)
conexion.execute(
    "CREATE TABLE asociacion ("
    " id INTEGER NOT NULL,"
    " nombre VARCHAR(100) NOT NULL DEFAULT 'Riguel',"
    " logo_path VARCHAR(255),"
    " CONSTRAINT ck_asociacion_singleton CHECK (id = 1),"
    " PRIMARY KEY (id))"
)
conexion.execute(
    "INSERT INTO asociacion (id, nombre, logo_path) "
    "VALUES (1, 'Nombre de la actualizacion', 'logo.jpg')"
)
conexion.execute(
    "INSERT INTO observaciones (objeto, fecha_hora_utc, fwhm) "
    "VALUES ('M31', '2026-02-01 22:00:00', 2.2)"
)
conexion.commit()
conexion.close()
'@ | Set-Content -Path $script -Encoding ASCII
    & $pythonExe $script $alembicDir $dbPath
    $codigo = $LASTEXITCODE
    Remove-Item $script -Force -ErrorAction SilentlyContinue
    if ($codigo -ne 0) { throw 'No pude armar la base de la version anterior.' }
}

# Lo que hay adentro de una base, en JSON, para comprobarlo despues de actualizar.
function Get-EstadoBase($pythonExe, $dbPath) {
    $script = Join-Path $env:TEMP "riguel-revisar-base-$([guid]::NewGuid().ToString('N')).py"
    @'
import json, sqlite3, sys

conexion = sqlite3.connect(sys.argv[1])
tablas = {fila[0] for fila in conexion.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}

def uno(sql):
    try:
        fila = conexion.execute(sql).fetchone()
        return fila[0] if fila else None
    except sqlite3.Error:
        return None

print(json.dumps({
    "revision": uno("SELECT version_num FROM alembic_version"),
    "asociacion": uno("SELECT nombre FROM asociacion WHERE id = 1"),
    "observaciones": uno("SELECT COUNT(*) FROM observaciones"),
    "tabla_apartada": "asociacion_previa" in tablas,
}))
conexion.close()
'@ | Set-Content -Path $script -Encoding ASCII
    $salida = (& $pythonExe $script $dbPath | Out-String).Trim()
    $codigo = $LASTEXITCODE
    Remove-Item $script -Force -ErrorAction SilentlyContinue
    if ($codigo -ne 0) { throw "No pude leer la base ${dbPath}: $salida" }
    return $salida | ConvertFrom-Json
}

# ---------------------------------------------------------------------------
# 0. Comprobaciones previas
# ---------------------------------------------------------------------------
Escribir-Paso "0/$pasos  Comprobando el entorno"

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'No encontre npm. Para generar el paquete hace falta Node.js 20 o superior.'
}
Escribir-Ok 'npm disponible'

if (-not (Test-Path (Join-Path $raiz 'instalar.bat')) -or -not (Test-Path (Join-Path $raiz 'arrancar.bat'))) {
    throw 'Faltan instalar.bat o arrancar.bat en la raiz del proyecto.'
}
Escribir-Ok 'scripts de instalacion presentes'

$ocupado = Get-Escuchando $puerto
if ($ocupado) {
    throw "El puerto $puerto esta ocupado. Cerra la aplicacion antes de empaquetar (la verificacion necesita ese puerto)."
}
Escribir-Ok "puerto $puerto libre"

# --- Publicacion: todo lo que se puede comprobar sin tocar la red --------------
#
# Estas guardas van ANTES de compilar. Descubrir a los diez minutos de build que el
# tag ya existia, o que el arbol estaba sucio, es la forma mas cara de enterarse.
$versionApp   = $null
$tagRelease   = $null
$repoGh       = $null
$visibilidad  = $null
$commitLocal  = $null
if ($Publicar) {
    if ($SoloEmpaquetar) {
        throw '-Publicar no se puede combinar con -SoloEmpaquetar: un paquete sin verificar no se publica.'
    }
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw 'No encontre gh (GitHub CLI). Instalalo desde https://cli.github.com y volve a intentar.'
    }
    gh auth status *> $null
    if ($LASTEXITCODE -ne 0) { throw 'gh no esta autenticado. Corre: gh auth login' }
    Escribir-Ok 'gh disponible y autenticado'

    # La version es una sola: manda el package.json del frontend y main.py tiene que
    # coincidir. Si se desincronizan, el release diria una cosa y la aplicacion otra.
    $versionApp = (Get-Content (Join-Path $raiz 'frontend\package.json') -Raw | ConvertFrom-Json).version
    if (-not $versionApp -or $versionApp -notmatch '^\d+\.\d+\.\d+$') {
        throw "No pude leer una version valida de frontend/package.json ('$versionApp')."
    }
    $mainPy = Get-Content (Join-Path $raiz 'backend\app\main.py') -Raw
    if ($mainPy -notmatch 'version\s*=\s*"([^"]+)"') {
        throw 'No encontre la version de la aplicacion en backend/app/main.py.'
    }
    $versionBackend = $Matches[1]
    if ($versionBackend -ne $versionApp) {
        throw "La version no coincide: frontend/package.json dice $versionApp y backend/app/main.py dice $versionBackend."
    }
    $tagRelease = "v$versionApp"
    Escribir-Ok "version $versionApp (tag $tagRelease) consistente en frontend y backend"

    # Un ZIP armado desde un arbol sucio no corresponde a ningun commit: nadie podria
    # reconstruirlo despues. El release tiene que salir de un estado reproducible.
    $sucio = @(git status --porcelain)
    if ($sucio.Count -gt 0) {
        throw "Hay cambios sin commitear: el paquete tiene que salir de un commit limpio.`n$($sucio -join "`n")"
    }
    git fetch origin --quiet
    if ($LASTEXITCODE -ne 0) { throw 'No pude consultar origin.' }
    $rama = (git rev-parse --abbrev-ref HEAD).Trim()
    if ($rama -ne 'main') { throw "Estas en la rama '$rama': un release se publica desde main." }
    $commitLocal  = (git rev-parse HEAD).Trim()
    $commitRemoto = (git rev-parse origin/main).Trim()
    if ($commitLocal -ne $commitRemoto) {
        throw "HEAD ($commitLocal) no coincide con origin/main ($commitRemoto): hace falta push antes de publicar."
    }
    Escribir-Ok "arbol limpio y main al dia con origin ($($commitLocal.Substring(0, 7)))"

    # Reusar un tag es peor que fallar: el release anterior quedaria pisado y quien
    # ya lo descargo no tendria forma de distinguir una version de la otra.
    git rev-parse -q --verify "refs/tags/$tagRelease" *> $null
    if ($LASTEXITCODE -eq 0) {
        throw "El tag $tagRelease ya existe localmente: subi la version antes de publicar."
    }
    $tagEnOrigin = (git ls-remote --tags --refs origin "refs/tags/$tagRelease") -join ''
    if ($tagEnOrigin) {
        throw "El tag $tagRelease ya existe en origin: subi la version antes de publicar."
    }
    Escribir-Ok "el tag $tagRelease no existe ni local ni en origin"

    $repoGh = (gh repo view --json nameWithOwner --jq '.nameWithOwner' 2>$null)
    if (-not $repoGh) { throw 'No pude averiguar el repositorio de GitHub (gh repo view).' }
    $visibilidad = (gh repo view --json visibility --jq '.visibility' 2>$null)
    Escribir-Ok "repositorio de destino: $repoGh ($visibilidad)"
}

# ---------------------------------------------------------------------------
# 1. Compilar el frontend
# ---------------------------------------------------------------------------
Escribir-Paso "1/$pasos  Compilando el frontend"

Push-Location (Join-Path $raiz 'frontend')
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build fallo (codigo $LASTEXITCODE)." }
} finally {
    Pop-Location
}
if (-not (Test-Path (Join-Path $raiz 'frontend/dist/index.html'))) {
    throw 'La compilacion no genero frontend/dist/index.html.'
}
Escribir-Ok 'frontend compilado en frontend/dist'

# ---------------------------------------------------------------------------
# 2. Armar la copia limpia
# ---------------------------------------------------------------------------
Escribir-Paso "2/$pasos  Armando el paquete"

if (Test-Path $tmpBase) { Remove-Item $tmpBase -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

# robocopy NO lee .gitignore: hay que decirle todo a mano. Nada de esta lista es
# capricho, cada cosa se colo alguna vez o se colaria sola:
#   .git       el historial completo del repositorio. El repo es privado, asi que
#              esto no es desprolijidad: es mandarle el historial entero a quien
#              recibe el paquete.
#   build/dist salidas de PyInstaller. Pesan cientos de MB y ademas confunden: quien
#              recibe la version con scripts se encuentra un Riguel.exe adentro.
#   openspec   los artefactos del flujo SDD. Son para el repositorio, no para quien
#              instala el programa.
$dirsExcluidos = @(
    'node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
    '*.egg-info', '.git', '.atl', '.idea', '.vscode'
)
# Estos tres van SOLO en la raiz, y por eso llevan ruta completa: robocopy /XD compara
# por NOMBRE, asi que un '/XD dist' a secas se llevaria tambien frontend\dist, que es
# justo el compilado que el paquete necesita para funcionar sin Node.
$dirsExcluidosRaiz = @(
    (Join-Path $raiz 'build'),
    (Join-Path $raiz 'dist'),
    (Join-Path $raiz 'openspec')
)
# *.zip tambien se excluye: el ZIP de salida se genera en la raiz del proyecto y, si
# no se filtra, robocopy lo mete dentro del paquete nuevo.
$archExcluidos  = @('riguel.db', '*.pyc', '*.pyo', '*.tsbuildinfo', '*.log', '*.zip')

robocopy $raiz $stage /E /XD @dirsExcluidos @dirsExcluidosRaiz /XF @archExcluidos /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy fallo (codigo $LASTEXITCODE)." }

# Fotos subidas por el usuario: no viajan (solo el logo por defecto y el .gitkeep).
$dirImagenes = Join-Path $stage 'backend\data\imagenes'
if (Test-Path $dirImagenes) {
    $sobran = Get-ChildItem $dirImagenes -File -Force | Where-Object { $_.Name -notin @('logo.jpg', '.gitkeep') }
    foreach ($f in $sobran) { Remove-Item $f.FullName -Force }
    if ($sobran) { Escribir-Aviso "saque $($sobran.Count) imagen(es) subida(s) por el usuario" }
}
Escribir-Ok 'copiado sin .git, sin build/dist, sin openspec, sin .venv ni fotos propias'

# ---------------------------------------------------------------------------
# 3. Generar el ZIP
# ---------------------------------------------------------------------------
Escribir-Paso "3/$pasos  Generando el ZIP"

if (Test-Path $zipDestino) { Remove-Item $zipDestino -Force }

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $stage,
    $zipDestino,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)

$mb = [math]::Round((Get-Item $zipDestino).Length / 1MB, 2)
Escribir-Ok "$nombre.zip ($mb MB)"

if ($SoloEmpaquetar -and -not $ConExe) {
    Write-Host ''
    Write-Host 'Listo (sin verificar).' -ForegroundColor Green
    return
}

# ---------------------------------------------------------------------------
# 4. Verificar el ZIP en una carpeta limpia
# ---------------------------------------------------------------------------
if (-not $SoloEmpaquetar) {

Escribir-Paso "4/$pasos  Probando el paquete desde cero"

Expand-Archive -Path $zipDestino -DestinationPath $prueba -Force
$appDir = Join-Path $prueba $nombre
if (-not (Test-Path (Join-Path $appDir 'instalar.bat'))) {
    throw "El ZIP no contiene la estructura esperada (falta instalar.bat dentro de $nombre)."
}

# El ZIP no debe traer nada de desarrollo. Los cuatro ultimos NO son higiene: se
# colaron de verdad. .git viajaba desde antes de este cambio (el repo es privado, asi
# que era el historial entero saliendo de casa), y build/dist los trajo la propia
# etapa -ConExe, porque la primera corrida los dejaba en la raiz y la segunda los
# copiaba dentro del paquete. Con el control de las tres rutas de siempre, ninguno de
# esos cuatro se notaba: el ZIP pesaba 107 MB con tres copias de Riguel.exe adentro.
foreach ($prohibido in @('frontend\node_modules', '.venv', 'backend\riguel.db',
                         '.git', 'build', 'dist', 'openspec')) {
    if (Test-Path (Join-Path $appDir $prohibido)) {
        throw "El ZIP contiene $prohibido y no deberia."
    }
}
if (-not (Test-Path (Join-Path $appDir 'frontend\dist\index.html'))) {
    throw 'El ZIP no incluye el frontend compilado: no funcionaria sin Node.'
}

# Red de seguridad por tamano. Vale aclarar que este numero NO es el tamanio esperado:
# el paquete sano pesa 0,3 MB (844 KB descomprimido). El limite tiene 30x de aire para
# que un frontend que crezca no lo haga saltar con un paquete que esta bien.
# Tampoco reemplaza a la lista de arriba: .git pesaba 1 MB y este guard no lo habria
# visto jamas. Lo que encuentra es la basura grande (un build, un .venv, un
# node_modules), que es exactamente el caso que nos paso.
if ($mb -gt 10) {
    throw "El ZIP pesa $mb MB y lo normal son 0,3: algo grande se colo. Revisa las exclusiones de robocopy."
}
Escribir-Ok 'el ZIP trae el frontend compilado y nada de desarrollo'

Write-Host '   ... corriendo instalar.bat (tarda un par de minutos)'
Push-Location $appDir
try {
    cmd /c 'instalar.bat < nul' | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "instalar.bat fallo con codigo $LASTEXITCODE." }
} finally {
    Pop-Location
}
Escribir-Ok 'instalar.bat termino bien'

# Arrancar sin abrir el navegador, para que la verificacion no moleste.
#
# Ojo: las comprobaciones automaticas van contra 127.0.0.1 y no contra localhost.
# En Windows "localhost" resuelve primero a ::1 (IPv6) y el servidor escucha solo en
# IPv4, asi que Invoke-WebRequest se come el timeout del IPv6 antes de reintentar por
# IPv4. El navegador no tiene ese problema (hace "Happy Eyeballs"), y por eso al final
# se comprueba tambien la direccion con localhost, que es la que usa la persona.
$env:RIGUEL_SIN_NAVEGADOR = '1'
$proc = $null
$vivo = $false
$base = "http://127.0.0.1:$puerto"
$basePublica = "http://localhost:$puerto"

try {
    $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'arrancar.bat' `
            -WorkingDirectory $appDir -PassThru -WindowStyle Minimized

    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Milliseconds 1000
        try {
            $r = Invoke-WebRequest "$base/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $vivo = $true; break }
        } catch { }
    }
    if (-not $vivo) { throw "El servidor no respondio en 90 segundos." }
    Escribir-Ok 'arrancar.bat levanto la aplicacion'

    # La interfaz, el enrutado del cliente y la API.
    foreach ($ruta in @('/', '/admin/asociacion', '/observaciones/123', '/api/v1/asociacion', '/api/v1/observatorios', '/imagenes/logo.jpg')) {
        $r = Invoke-WebRequest "$base$ruta" -UseBasicParsing -TimeoutSec 20
        if ($r.StatusCode -ne 200) { throw "$ruta respondio $($r.StatusCode)." }
    }
    Escribir-Ok 'la interfaz, el enrutado y la API responden'

    # La direccion que va a escribir la persona tiene que servir tambien.
    $r = Invoke-WebRequest $basePublica -UseBasicParsing -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "http://localhost:$puerto respondio $($r.StatusCode)." }
    Escribir-Ok "http://localhost:$puerto tambien responde"

    # Las rutas de API inexistentes NO deben devolver la interfaz.
    # El tipo de excepcion cambia entre PowerShell 5.1 y 7, asi que en vez de atrapar
    # un tipo concreto se lee el codigo de estado de la respuesta.
    $codigo = $null
    try {
        $respuesta = Invoke-WebRequest "$base/api/v1/noexiste" -UseBasicParsing -TimeoutSec 20
        $codigo = [int]$respuesta.StatusCode
    } catch {
        if ($_.Exception.Response) { $codigo = [int]$_.Exception.Response.StatusCode }
    }
    if ($codigo -ne 404) {
        throw "/api/v1/noexiste devolvio '$codigo' y deberia devolver 404: el fallback se estaria tragando la API."
    }
    Escribir-Ok 'las rutas de API inexistentes siguen dando 404'

    # Base de datos recien creada: sin observaciones y con el logo por defecto.
    $obs = Invoke-RestMethod "$base/api/v1/observaciones" -TimeoutSec 20
    if (@($obs).Count -ne 0) { throw "La base del paquete no esta vacia: trae $(@($obs).Count) observacion(es)." }
    $datos = Invoke-RestMethod "$base/api/v1/asociacion" -TimeoutSec 20
    if ($datos.logo_path -ne 'logo.jpg') { throw "El logo por defecto no es logo.jpg (es '$($datos.logo_path)')." }
    $sitios = Invoke-RestMethod "$base/api/v1/observatorios" -TimeoutSec 20
    if (@($sitios).Count -ne 1) { throw "La base del paquete deberia traer 1 observatorio y trae $(@($sitios).Count)." }
    Escribir-Ok 'base de datos limpia, un observatorio sembrado y logo por defecto en su lugar'

    # --- Actualizacion: una instalacion que ya tiene datos ------------------
    #
    # El caso que mas caro sale si falla: la persona ya cargo sus observaciones y su
    # nombre de asociacion. Se reemplaza la base por una de la version anterior (en
    # 0003, con la tabla que dejaba create_all) y se arranca otra vez: la migracion
    # tiene que repararla, guardar una copia y no perder nada.
    Stop-Aplicacion $proc

    $baseVieja = Join-Path $appDir 'backend\riguel.db'
    $pyApp     = Join-Path $appDir '.venv\Scripts\python.exe'
    New-BaseVersionAnterior $pyApp (Join-Path $appDir 'backend\alembic') $baseVieja
    $antes = Get-EstadoBase $pyApp $baseVieja
    if ($antes.revision -ne '0003') { throw "La base de prueba deberia estar en 0003 y esta en $($antes.revision)." }

    $env:DATABASE_URL = "sqlite+aiosqlite:///$($baseVieja -replace '\\','/')"
    $proc = Start-Process -FilePath 'cmd.exe' -ArgumentList '/c', 'arrancar.bat' `
            -WorkingDirectory $appDir -PassThru -WindowStyle Minimized
    $vivo = $false
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Milliseconds 1000
        try {
            $r = Invoke-WebRequest "$base/health" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $vivo = $true; break }
        } catch { }
    }
    if (-not $vivo) { throw 'La aplicacion no arranco contra una base de la version anterior.' }

    $datos = Invoke-RestMethod "$base/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne 'Nombre de la actualizacion') {
        throw "La actualizacion perdio el nombre de la asociacion: dice '$($datos.nombre)'."
    }
    $cantObs = Invoke-RestMethod "$base/api/v1/observaciones/count" -TimeoutSec 20
    if ([int]$cantObs -ne 1) {
        throw "La actualizacion perdio observaciones: hay $cantObs y deberia haber 1."
    }
    $sitios = Invoke-RestMethod "$base/api/v1/observatorios" -TimeoutSec 20
    if (@($sitios).Count -ne 1) { throw "La actualizacion dejo $(@($sitios).Count) observatorios en vez de 1." }
    Escribir-Ok 'una base de la version anterior se actualizo sin perder observaciones ni nombre'

    Stop-Aplicacion $proc
    Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue

    $despues = Get-EstadoBase $pyApp $baseVieja
    if ($despues.revision -ne '0004') { throw "La base quedo en $($despues.revision) y deberia quedar en 0004." }
    if ($despues.tabla_apartada) { throw 'Quedo la tabla asociacion_previa: la reparacion no termino.' }
    if ([int]$despues.observaciones -ne 1) { throw 'La observacion no quedo guardada en la base.' }

    $respaldos = @(Get-ChildItem (Join-Path $appDir 'backend') -Filter 'riguel.db.antes-de-actualizar-*.db')
    if ($respaldos.Count -lt 1) { throw 'La actualizacion no dejo copia de seguridad de la base.' }
    $copia = Get-EstadoBase $pyApp $respaldos[0].FullName
    if ($copia.revision -ne '0003') {
        throw "La copia de seguridad no es la base anterior: dice $($copia.revision)."
    }
    Escribir-Ok "guardo la copia de seguridad antes de actualizar ($($respaldos[0].Name))"

} finally {
    # Arrancar.bat deja a uvicorn como hijo de cmd.exe, asi que hay que matar el
    # arbol entero: matar solo el cmd deja el servidor vivo, el ZIP de prueba no
    # se puede borrar y la proxima corrida falla al limpiar el temporal.
    Stop-Aplicacion $proc
    Remove-Item Env:\RIGUEL_SIN_NAVEGADOR -ErrorAction SilentlyContinue
}

Remove-Item $prueba -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $tmpBase -Recurse -Force -ErrorAction SilentlyContinue

} else {
    Escribir-Aviso 'salteando la verificacion del ZIP (-SoloEmpaquetar)'
}

# ---------------------------------------------------------------------------
# 5. Construir y probar el ejecutable (-ConExe)
# ---------------------------------------------------------------------------
if ($ConExe) {

$tmpExe     = Join-Path $env:TEMP 'riguel-exe'
$workExe    = Join-Path $tmpExe 'build'
$pruebaExe  = Join-Path $tmpExe 'prueba'
$logExe     = Join-Path $tmpExe 'pyinstaller.log'
$puertoExe  = 8412
$python     = Join-Path $raiz '.venv\Scripts\python.exe'
$espec      = Join-Path $raiz 'riguel.spec'
$zipExe     = Join-Path $raiz "$nombre-exe.zip"

# --- Construir -------------------------------------------------------------
Escribir-Paso "$pasoExe/$pasos  Construyendo el ejecutable"

if (-not (Test-Path $espec))  { throw 'Falta riguel.spec en la raiz del proyecto.' }
if (-not (Test-Path $python)) {
    throw 'No encontre .venv. El ejecutable se construye con el entorno de desarrollo: corre instalar.bat primero.'
}
& $python -c 'import PyInstaller' *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'PyInstaller no esta instalado en .venv. Corre: .venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt'
}

if (Test-Path $tmpExe) { Remove-Item $tmpExe -Recurse -Force }
New-Item -ItemType Directory -Path $tmpExe -Force | Out-Null
if (Test-Path $distExe) { Remove-Item $distExe -Recurse -Force }

Write-Host '   ... corriendo PyInstaller (tarda un par de minutos)'
# La salida se manda a un archivo con cmd para no tropezar con el ruido de stderr
# que PowerShell 5.1 convierte en error cuando $ErrorActionPreference es Stop.
$orden = '"{0}" -m PyInstaller "{1}" --noconfirm --distpath "{2}" --workpath "{3}" > "{4}" 2>&1' -f `
    $python, $espec, $distExe, $workExe, $logExe
cmd /c $orden | Out-Null
if ($LASTEXITCODE -ne 0) {
    if (Test-Path $logExe) { Get-Content $logExe -Tail 30 | ForEach-Object { Write-Host "      $_" } }
    throw "PyInstaller fallo con codigo $LASTEXITCODE (log completo: $logExe)."
}

$appExe = Join-Path $distExe 'Riguel'
if (-not (Test-Path (Join-Path $appExe 'Riguel.exe'))) { throw 'PyInstaller no genero Riguel.exe.' }
$mbExe = [math]::Round(((Get-ChildItem $appExe -Recurse -File | Measure-Object -Property Length -Sum).Sum / 1MB), 1)
Escribir-Ok "ejecutable construido en dist\Riguel ($mbExe MB)"

# Lo que el codigo busca con bundle_root(). Si falta, la aplicacion igual arranca y
# la persona ve una pagina en blanco: por eso se comprueba antes de ejecutarlo.
foreach ($relativo in @(
    '_internal\frontend\dist\index.html',
    '_internal\backend\alembic\env.py',
    '_internal\backend\alembic\versions\0001_initial.py',
    '_internal\backend\data\imagenes\logo.jpg'
)) {
    if (-not (Test-Path (Join-Path $appExe $relativo))) {
        throw "Al ejecutable le falta ${relativo}: la aplicacion no funcionaria."
    }
}
Escribir-Ok 'trae adentro la interfaz compilada, las migraciones y el logo'

# --- Probar -----------------------------------------------------------------
Escribir-Paso "$pasoExe/$pasos  Probando el ejecutable desde cero"

New-Item -ItemType Directory -Path $pruebaExe -Force | Out-Null
Copy-Item $appExe -Destination $pruebaExe -Recurse
$copia     = Join-Path $pruebaExe 'Riguel'
$exe       = Join-Path $copia 'Riguel.exe'
$baseExe   = "http://127.0.0.1:$puertoExe"
$publExe   = "http://localhost:$puertoExe"
$env:RIGUEL_SIN_NAVEGADOR = '1'
$env:RIGUEL_PUERTO        = "$puertoExe"

function Iniciar-Exe($numero) {
    $ruta = Join-Path $pruebaExe "exe-out-$numero.txt"
    Start-Process -FilePath $exe -PassThru -NoNewWindow `
        -RedirectStandardOutput $ruta `
        -RedirectStandardError  (Join-Path $pruebaExe "exe-err-$numero.txt")
}

function Esperar-Exe {
    for ($i = 0; $i -lt 240; $i++) {
        try { $r = Invoke-WebRequest "$baseExe/health" -UseBasicParsing -TimeoutSec 3; if ($r.StatusCode -eq 200) { return $true } } catch { }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

function Detener-Exe($proceso) {
    Get-Escuchando $puertoExe |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    if ($proceso) { Stop-Process -Id $proceso.Id -Force -ErrorAction SilentlyContinue }
    for ($i = 0; $i -lt 20; $i++) {
        if (-not (Get-Escuchando $puertoExe)) { break }
        Start-Sleep -Milliseconds 500
    }
}

# Subida de archivos con HttpClient y no con -Form: -Form existe recien en
# PowerShell 6, y este script tiene que andar tambien en el 5.1 de Windows.
function Subir-Logo($url, $rutaArchivo) {
    Add-Type -AssemblyName System.Net.Http -ErrorAction SilentlyContinue
    $cliente = New-Object System.Net.Http.HttpClient
    try {
        $cuerpo = New-Object System.Net.Http.MultipartFormDataContent
        $bytes  = [System.IO.File]::ReadAllBytes($rutaArchivo)
        $parte  = New-Object System.Net.Http.ByteArrayContent -ArgumentList (, $bytes)
        $parte.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse('image/jpeg')
        $cuerpo.Add($parte, 'file', [System.IO.Path]::GetFileName($rutaArchivo))
        $respuesta = $cliente.PostAsync($url, $cuerpo).Result
        return [pscustomobject]@{
            Codigo = [int]$respuesta.StatusCode
            Cuerpo = $respuesta.Content.ReadAsStringAsync().Result
        }
    } finally {
        $cliente.Dispose()
    }
}

function Poner-Nombre($texto) {
    Invoke-RestMethod "$baseExe/api/v1/asociacion" -Method Put -TimeoutSec 20 `
        -ContentType 'application/json' -Body (@{ nombre = $texto } | ConvertTo-Json) | Out-Null
}

$procExe = $null
try {
    # ---- Primer arranque, carpeta limpia ----------------------------------
    $procExe = Iniciar-Exe 1
    if (-not (Esperar-Exe)) {
        $salida  = Get-Content (Join-Path $pruebaExe 'exe-out-1.txt') -ErrorAction SilentlyContinue
        $errores = Get-Content (Join-Path $pruebaExe 'exe-err-1.txt') -ErrorAction SilentlyContinue
        throw "El ejecutable no respondio en 120 segundos.`n--- salida ---`n$($salida -join "`n")`n--- errores ---`n$($errores -join "`n")"
    }
    Escribir-Ok 'arranco solo, sin Python instalado'

    foreach ($ruta in @('/', '/admin/asociacion', '/observaciones/123', '/api/v1/asociacion', '/api/v1/observatorios', '/api/v1/filtros', '/imagenes/logo.jpg')) {
        $r = Invoke-WebRequest "$baseExe$ruta" -UseBasicParsing -TimeoutSec 30
        if ($r.StatusCode -ne 200) { throw "$ruta respondio $($r.StatusCode)." }
    }
    Escribir-Ok 'la interfaz, el enrutado del cliente y la API responden'

    $r = Invoke-WebRequest $publExe -UseBasicParsing -TimeoutSec 30
    if ($r.StatusCode -ne 200) { throw "http://localhost:$puertoExe respondio $($r.StatusCode)." }
    Escribir-Ok "http://localhost:$puertoExe tambien responde"

    $codigo = $null
    try {
        $respuesta = Invoke-WebRequest "$baseExe/api/v1/noexiste" -UseBasicParsing -TimeoutSec 20
        $codigo = [int]$respuesta.StatusCode
    } catch {
        if ($_.Exception.Response) { $codigo = [int]$_.Exception.Response.StatusCode }
    }
    if ($codigo -ne 404) { throw "/api/v1/noexiste devolvio '$codigo' y deberia devolver 404." }
    Escribir-Ok 'las rutas de API inexistentes siguen dando 404'

    # Escucha SOLO en loopback. Con el default de los settings (0.0.0.0) el
    # ejecutable quedaria a la vista de cualquiera en la misma red.
    #
    # OJO: no sirve filtrar con -State Listen. En algunas maquinas el proveedor
    # CIM devuelve el estado vacio para estos sockets y la consulta no encuentra
    # nada, aunque la aplicacion este escuchando y los pedidos HTTP de arriba
    # hayan respondido 200. Se filtra por el PID del ejecutable, que es mas
    # preciso igual, y se reintenta por si la tabla tarda en reflejarlo.
    $direcciones = @()
    for ($intento = 0; $intento -lt 5 -and $direcciones.Count -eq 0; $intento++) {
        Start-Sleep -Milliseconds 500
        $direcciones = @(Get-NetTCPConnection -LocalPort $puertoExe -ErrorAction SilentlyContinue |
            Where-Object { $_.OwningProcess -eq $procExe.Id } |
            Select-Object -ExpandProperty LocalAddress -Unique)
    }
    if ($direcciones -notcontains '127.0.0.1') {
        throw "No escucha en 127.0.0.1 (escucha en: $($direcciones -join ', '))."
    }
    if ($direcciones -contains '0.0.0.0' -or $direcciones -contains '::') {
        throw "Escucha en TODAS las interfaces ($($direcciones -join ', ')): las observaciones quedarian expuestas a la red local."
    }
    Escribir-Ok "escucha solo en loopback ($($direcciones -join ', '))"

    # La semilla (asociacion + observatorio + 6 filtros) vive en las migraciones, no en
    # create_all: si el ejecutable usara create_all la base quedaria vacia y sin filtros.
    $datos = Invoke-RestMethod "$baseExe/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne 'Riguel') { throw "La asociacion deberia llamarse 'Riguel' y se llama '$($datos.nombre)'." }
    if ($datos.logo_path -ne 'logo.jpg') { throw "El logo por defecto no es logo.jpg (es '$($datos.logo_path)')." }
    $sitios = Invoke-RestMethod "$baseExe/api/v1/observatorios" -TimeoutSec 20
    if (@($sitios).Count -ne 1) { throw "Deberia haber 1 observatorio y hay $(@($sitios).Count)." }
    if ($sitios[0].nombre -ne 'Riguel') { throw "El observatorio deberia llamarse 'Riguel' y se llama '$($sitios[0].nombre)'." }
    if (-not $sitios[0].es_predeterminado) { throw 'El observatorio sembrado no quedo como predeterminado.' }
    # Los conteos van por los endpoints /count, que devuelven un entero.
    # OJO: no sirve contar la lista con @(Invoke-RestMethod ...) en una sola linea.
    # En PowerShell 5.1 esa llamada entrega el arreglo como UN objeto en vez de
    # enumerarlo, asi que @() da 1 y la comprobacion falla mintiendo. En PowerShell 7
    # funciona, o sea que el error solo aparece al correr el script como se documenta
    # (powershell -File) y no a mano en pwsh.
    $cantFiltros = Invoke-RestMethod "$baseExe/api/v1/filtros/count" -TimeoutSec 20
    if ([int]$cantFiltros -ne 6) { throw "Deberia haber 6 filtros y hay $cantFiltros." }
    # La lista completa igual se pide: es la que consume la interfaz, y traer 6
    # elementos es distinto de que el endpoint /count diga 6.
    $listaFiltros = Invoke-RestMethod "$baseExe/api/v1/filtros" -TimeoutSec 20
    if (@($listaFiltros).Count -ne 6) {
        throw "La lista de filtros trajo $(@($listaFiltros).Count) y deberian ser 6."
    }
    $cantObs = Invoke-RestMethod "$baseExe/api/v1/observaciones/count" -TimeoutSec 20
    if ([int]$cantObs -ne 0) { throw "La base del ejecutable no esta vacia: trae $cantObs observacion(es)." }
    Escribir-Ok 'base sembrada por las migraciones: Riguel, 1 observatorio, 6 filtros, ninguna observacion'

    # Crear una observacion: hace falta para poder exportar, y de paso prueba el camino
    # de ESCRITURA, que en un ejecutable es distinto del de lectura (permisos de la
    # carpeta de datos, transacciones, la base que se creo recien).
    $hoy = (Get-Date).ToString('yyyy-MM-dd')
    $nueva = Invoke-RestMethod "$baseExe/api/v1/observaciones" -Method Post -TimeoutSec 30 `
        -ContentType 'application/json' `
        -Body (@{ objeto = 'Prueba de empaquetado'; fecha_hora_utc = "${hoy}T22:00:00"; fwhm = 2.5 } | ConvertTo-Json)
    if (-not $nueva.id) { throw 'No se pudo crear una observacion.' }
    $r = Invoke-WebRequest "$baseExe/api/v1/observaciones/$($nueva.id)" -UseBasicParsing -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "La observacion recien creada no se puede leer ($($r.StatusCode))." }
    Escribir-Ok "se puede crear y leer una observacion (id $($nueva.id))"

    # Exportar. El PDF es lo que arrastra reportlab, que trae fuentes y plantillas
    # propias: es lo que mas facil se rompe al empaquetar, y no falla al arrancar sino
    # justo cuando la persona aprieta el boton.
    $pdf = Invoke-WebRequest "$baseExe/api/v1/export/pdf/noche?fecha=$hoy" -UseBasicParsing -TimeoutSec 60
    if ($pdf.StatusCode -ne 200) { throw "La exportacion a PDF respondio $($pdf.StatusCode)." }
    if ("$($pdf.Headers['Content-Type'])" -notmatch 'application/pdf') {
        throw "La exportacion no devolvio un PDF (Content-Type: $($pdf.Headers['Content-Type']))."
    }
    if ($pdf.RawContentLength -lt 1000) { throw "El PDF salio demasiado chico ($($pdf.RawContentLength) bytes)." }
    Escribir-Ok "el PDF se genera ($([math]::Round($pdf.RawContentLength/1KB)) KB)"

    $csv = Invoke-WebRequest "$baseExe/api/v1/export/csv?tabla=all" -UseBasicParsing -TimeoutSec 60
    if ($csv.StatusCode -ne 200) { throw "La exportacion a CSV respondio $($csv.StatusCode)." }
    if ($csv.Content -notmatch 'Prueba de empaquetado') {
        throw 'El CSV exportado no trae la observacion que se acaba de crear.'
    }
    Escribir-Ok 'el CSV se genera con lo que se cargo'

    # Subir un logo propio: prueba que data\imagenes es escribible de verdad.
    $logoPrueba = Join-Path $tmpExe 'logo-prueba.jpg'
    Copy-Item (Join-Path $raiz 'backend\data\imagenes\logo.jpg') $logoPrueba
    $subida = Subir-Logo "$baseExe/api/v1/asociacion/logo" $logoPrueba
    if ($subida.Codigo -ne 200) { throw "Subir el logo respondio $($subida.Codigo): $($subida.Cuerpo)" }
    $logoSubido = ($subida.Cuerpo | ConvertFrom-Json).logo_path
    if (-not $logoSubido -or $logoSubido -eq 'logo.jpg') {
        throw "El logo subido no se registro (logo_path = '$logoSubido')."
    }
    $r = Invoke-WebRequest "$baseExe/imagenes/$logoSubido" -UseBasicParsing -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "El logo subido no se sirve ($($r.StatusCode))." }
    Escribir-Ok "el logo subido se guarda y se sirve ($logoSubido)"

    # Reiniciar: lo que se guardo tiene que seguir ahi. Es lo que distingue una
    # carpeta de datos de verdad de un temporal que se borra al cerrar.
    $marca = "Riguel-prueba-$([guid]::NewGuid().ToString('N').Substring(0,8))"
    Poner-Nombre $marca
    Detener-Exe $procExe
    $procExe = Iniciar-Exe 2
    if (-not (Esperar-Exe)) { throw 'El ejecutable no volvio a arrancar.' }
    $datos = Invoke-RestMethod "$baseExe/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne $marca) { throw "El nombre de la asociacion no sobrevivio al reinicio: '$($datos.nombre)' en vez de '$marca'." }
    if ($datos.logo_path -ne $logoSubido) { throw "El logo subido no sobrevivio al reinicio (es '$($datos.logo_path)')." }
    $r = Invoke-WebRequest "$baseExe/imagenes/$logoSubido" -UseBasicParsing -TimeoutSec 20
    if ($r.StatusCode -ne 200) { throw "El logo subido no se sirve despues del reinicio ($($r.StatusCode))." }
    Escribir-Ok 'lo que guardo sobrevivio a un reinicio'

    # Adopcion: simular una instalacion anterior dejando su base en backend\, que es
    # donde la dejaria instalar.bat. El lanzador tiene que COPIARLA, no arrancar vacio.
    Detener-Exe $procExe
    $legacyDir = Join-Path $copia 'backend'
    New-Item -ItemType Directory -Path $legacyDir -Force | Out-Null
    Move-Item (Join-Path $copia 'data\riguel.db') (Join-Path $legacyDir 'riguel.db') -Force

    $procExe = Iniciar-Exe 3
    if (-not (Esperar-Exe)) { throw 'El ejecutable no arranco con una base anterior al lado.' }
    $datos = Invoke-RestMethod "$baseExe/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne $marca) {
        throw "No adopto la base anterior: la asociacion se llama '$($datos.nombre)' y la base vieja decia '$marca'."
    }
    if (-not (Test-Path (Join-Path $legacyDir 'riguel.db'))) {
        throw 'Se llevo la base anterior en vez de copiarla: el archivo original ya no esta.'
    }
    Escribir-Ok 'adopto la base de una instalacion anterior por copia, sin tocar el original'

    # Con las dos bases presentes tiene que ganar la de data\, no la anterior.
    $marcaNueva = "Riguel-nueva-$([guid]::NewGuid().ToString('N').Substring(0,8))"
    Poner-Nombre $marcaNueva
    Detener-Exe $procExe
    $procExe = Iniciar-Exe 4
    if (-not (Esperar-Exe)) { throw 'El ejecutable no arranco con las dos bases presentes.' }
    $datos = Invoke-RestMethod "$baseExe/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne $marcaNueva) {
        throw "Piso la base en uso con la anterior: dice '$($datos.nombre)' y deberia decir '$marcaNueva'."
    }
    Escribir-Ok 'con las dos bases presentes gana la que esta en uso'

    # --- Actualizacion: la base de una version anterior, ya en data\ ----------
    #
    # El ejecutable corre la misma reparacion que el paquete. Si esto falla, quien ya
    # venia usando la aplicacion se queda sin sus observaciones, que es lo peor que
    # puede pasar en una actualizacion.
    Detener-Exe $procExe
    $dbExe = Join-Path $copia 'data\riguel.db'
    New-BaseVersionAnterior $python (Join-Path $raiz 'backend\alembic') $dbExe

    $procExe = Iniciar-Exe 5
    if (-not (Esperar-Exe)) { throw 'El ejecutable no arranco contra una base de la version anterior.' }
    $datos = Invoke-RestMethod "$baseExe/api/v1/asociacion" -TimeoutSec 20
    if ($datos.nombre -ne 'Nombre de la actualizacion') {
        throw "El ejecutable perdio el nombre de la asociacion: dice '$($datos.nombre)'."
    }
    $cantObs = Invoke-RestMethod "$baseExe/api/v1/observaciones/count" -TimeoutSec 20
    if ([int]$cantObs -ne 1) {
        throw "El ejecutable perdio observaciones: hay $cantObs y deberia haber 1."
    }
    Detener-Exe $procExe

    $estado = Get-EstadoBase $python $dbExe
    if ($estado.revision -ne '0004') { throw "La base quedo en $($estado.revision) y deberia quedar en 0004." }
    if ($estado.tabla_apartada) { throw 'Quedo la tabla asociacion_previa: la reparacion no termino.' }
    $respaldosExe = @(Get-ChildItem (Join-Path $copia 'data') -Filter 'riguel.db.antes-de-actualizar-*.db')
    if ($respaldosExe.Count -lt 1) { throw 'El ejecutable no dejo copia de seguridad al actualizar.' }
    Escribir-Ok 'una base de la version anterior se actualizo sin perder nada, con copia previa'

} finally {
    Detener-Exe $procExe
    Remove-Item Env:\RIGUEL_SIN_NAVEGADOR -ErrorAction SilentlyContinue
    Remove-Item Env:\RIGUEL_PUERTO -ErrorAction SilentlyContinue
}

# --- Generar el ZIP del ejecutable -----------------------------------------
if (Test-Path $zipExe) { Remove-Item $zipExe -Force }
# Se comprime $appExe (dist\Riguel), no $distExe, para que el ZIP descomprima directo
# en una carpeta Riguel\. Comprimiendo dist\, quien abre el ZIP se topaba primero con un
# directorio llamado dist: una carpeta de build que no le dice nada y que contradice lo
# que le promete INSTALL.md, donde adentro del ZIP hay una carpeta Riguel y nada mas.
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $appExe,
    $zipExe,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $true
)
$mbZipExe = [math]::Round((Get-Item $zipExe).Length / 1MB, 2)

# Que descomprima en una sola carpeta Riguel\ es parte de lo que la guia le promete al
# usuario, asi que se comprueba leyendo el ZIP en vez de confiar en la ruta que le
# pasamos: es justo el detalle que se nos paso la primera vez.
$lector = [System.IO.Compression.ZipFile]::OpenRead($zipExe)
try {
    $raices = @($lector.Entries | ForEach-Object { ($_.FullName -replace '\\','/').Split('/')[0] } | Sort-Object -Unique)
    if ($raices.Count -ne 1 -or $raices[0] -ne 'Riguel') {
        throw "El ZIP del ejecutable descomprime en '$($raices -join ', ')' y deberia descomprimir en una sola carpeta Riguel."
    }
} finally { $lector.Dispose() }
Escribir-Ok "$nombre-exe.zip ($mbZipExe MB, descomprime en una carpeta Riguel)"

Remove-Item $tmpExe -Recurse -Force -ErrorAction SilentlyContinue

}

# ---------------------------------------------------------------------------
# 6. Publicar el release (-Publicar)
# ---------------------------------------------------------------------------
#
# Se publica recien aca, cuando los pasos 4 y 5 ya pasaron. Publicar antes de
# verificar es la forma mas facil de mandarle a la gente un ZIP roto: el release
# queda online y la persona lo descarga sin saber que nadie lo probo.
if ($Publicar) {

Escribir-Paso "$pasoPublicar/$pasos  Publicando $tagRelease en GitHub"

# Los dos paquetes: el de scripts (necesita Python) y, si se construyo, el ejecutable
# (no necesita nada). INSTALL.md documenta las dos formas, asi que el release tambien
# tiene que ofrecer las dos.
$assets = @($zipDestino)
if ($ConExe -and $zipExe -and (Test-Path $zipExe)) { $assets += $zipExe }
$nombresAssets = @($assets | ForEach-Object { (Get-Item $_).Name })

$notasPath = Join-Path $env:TEMP "riguel-release-$tagRelease.md"
$notas = @"
Riguel - Cuaderno de Campo Astronomico $versionApp

## Que trae esta version

- Varios observatorios con selector, color por sitio y uno predeterminado.
- Las actualizaciones se aplican al arrancar: la base se migra sin perder datos y se guarda una copia antes de tocarla.
- La interfaz deja de quedar cacheada con una version vieja despues de actualizar.

## Que descargar

"@
if ($nombresAssets -contains "$nombre-exe.zip") {
    $notas += "- ``$nombre-exe.zip``: no necesita Python. Descomprimir y doble clic en Riguel.exe (ver INSTALL.md).`n"
}
if ($nombresAssets -contains "$nombre.zip") {
    $notas += "- ``$nombre.zip``: necesita Python 3.12, 3.13 o 3.14. Descomprimir, doble clic en instalar.bat y despues en arrancar.bat.`n"
}
Set-Content -Path $notasPath -Value $notas -Encoding ASCII

# Las comillas van puestas a mano: los nombres no las llevan, pero las rutas si
# pueden tener espacios y cmd /c parte los argumentos por espacios sin avisar.
$listaAssets = ($assets | ForEach-Object { '"' + $_ + '"' }) -join ' '
$ordenGh = 'gh release create {0} {1} --title "{2}" --target {3} --notes-file "{4}"' -f `
    $tagRelease, $listaAssets, "Riguel Cuaderno de Campo Astronomico $versionApp", $commitLocal, $notasPath
cmd /c $ordenGh
$codigoGh = $LASTEXITCODE
Remove-Item $notasPath -Force -ErrorAction SilentlyContinue
if ($codigoGh -ne 0) { throw "gh release create fallo con codigo $codigoGh." }
Escribir-Ok "release $tagRelease creado"

# Que los archivos hayan llegado enteros. gh no falla si sube un asset truncado,
# asi que se compara el tamano publicado con el del disco.
$jsonRelease = gh release view $tagRelease --json assets,url
if ($LASTEXITCODE -ne 0) { throw "No pude leer el release $tagRelease despues de crearlo." }
$release = $jsonRelease | ConvertFrom-Json
foreach ($archivo in $assets) {
    $info = Get-Item $archivo
    $subido = $release.assets | Where-Object { $_.name -eq $info.Name }
    if (-not $subido) { throw "El release no tiene el archivo $($info.Name)." }
    if ([long]$subido.size -ne [long]$info.Length) {
        throw "El archivo $($info.Name) subio con $($subido.size) bytes y en disco pesa $($info.Length)."
    }
}
Escribir-Ok "los archivos subieron completos ($($nombresAssets -join ', '))"

# Que los archivos se puedan bajar de verdad. Se descargan con gh, que va
# autenticado: es la unica forma de comprobarlo en un repo privado, donde la URL
# publica devuelve 404 aunque el release este perfecto. Y se compara el SHA256, no
# el tamano: un archivo truncado o cambiado en el camino se detecta igual.
$carpetaDescarga = Join-Path $env:TEMP "riguel-descarga-$tagRelease"
if (Test-Path $carpetaDescarga) { Remove-Item $carpetaDescarga -Recurse -Force }
New-Item -ItemType Directory -Path $carpetaDescarga -Force | Out-Null
try {
    foreach ($archivo in $assets) {
        $info = Get-Item $archivo
        gh release download $tagRelease --pattern $info.Name --dir $carpetaDescarga --clobber
        if ($LASTEXITCODE -ne 0) { throw "No pude descargar $($info.Name) del release." }
        $bajado = Join-Path $carpetaDescarga $info.Name
        if (-not (Test-Path $bajado)) { throw "El release no entrego $($info.Name)." }
        $hashLocal  = (Get-FileHash $archivo -Algorithm SHA256).Hash
        $hashBajado = (Get-FileHash $bajado  -Algorithm SHA256).Hash
        if ($hashLocal -ne $hashBajado) {
            throw "El archivo $($info.Name) se descarga distinto de como se subio (SHA256 no coincide)."
        }
    }
} finally {
    Remove-Item $carpetaDescarga -Recurse -Force -ErrorAction SilentlyContinue
}
Escribir-Ok "los archivos se descargan enteros, con el mismo SHA256 que en disco"

# La URL fija solo se puede repartir si el repositorio es publico. En uno privado
# pide sesion de GitHub: el release sirve para quien tenga acceso al repo, no para
# mandarle el link a cualquiera. Se avisa en vez de fallar, porque el release esta bien.
if ($visibilidad -eq 'PUBLIC') {
    foreach ($nombreArchivo in $nombresAssets) {
        $urlFija = "https://github.com/$repoGh/releases/latest/download/$nombreArchivo"
        $responde = $false
        for ($intento = 0; $intento -lt 8 -and -not $responde; $intento++) {
            try {
                $r = Invoke-WebRequest $urlFija -Method Head -UseBasicParsing -TimeoutSec 30
                if ($r.StatusCode -eq 200) { $responde = $true }
            } catch { }
            if (-not $responde) { Start-Sleep -Seconds 3 }
        }
        # Algunos CDN no contestan HEAD: antes de darlo por roto se prueba una descarga.
        if (-not $responde) {
            try {
                $r = Invoke-WebRequest $urlFija -UseBasicParsing -TimeoutSec 180
                if ($r.StatusCode -eq 200) { $responde = $true }
            } catch { }
        }
        if (-not $responde) { throw "La URL fija $urlFija no responde: el release existe pero nadie podria descargarlo." }
        Escribir-Ok "descarga fija andando: $urlFija"
    }
} else {
    Escribir-Aviso "el repositorio es privado: la URL de descarga pide sesion de GitHub y solo sirve para quien tenga acceso al repo"
}

}

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  PAQUETE LISTO Y VERIFICADO' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Write-Host ''
Write-Host "  Archivo: $zipDestino"
Write-Host "  Tamanio: $mb MB"
Write-Host ''
Write-Host '  Quien lo reciba: descomprimir, doble clic en instalar.bat,'
Write-Host '  y despues doble clic en arrancar.bat.'
if ($ConExe) {
    Write-Host ''
    Write-Host '  Ejecutable (no necesita Python ni instalar nada):' -ForegroundColor Green
    Write-Host "    Carpeta: $appExe"
    Write-Host "    Archivo: $zipExe"
    Write-Host '  Quien lo reciba: descomprimir y doble clic en Riguel.exe.'
}
if ($Publicar) {
    Write-Host ''
    Write-Host "  Release $tagRelease publicado:" -ForegroundColor Green
    Write-Host "    https://github.com/$repoGh/releases/tag/$tagRelease"
    if ($visibilidad -eq 'PUBLIC') {
        Write-Host "    Descarga fija: https://github.com/$repoGh/releases/latest/download/$nombre.zip"
    } else {
        Write-Host "    Repo privado: para descargarlo hay que tener acceso al repositorio" -ForegroundColor Yellow
    }
}
Write-Host ''
