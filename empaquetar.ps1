<#
    empaquetar.ps1
    Genera el ZIP de distribucion de "Riguel - Cuaderno de Campo Astronomico".

    Uso:
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -SoloEmpaquetar

    Que hace:
      1. Compila el frontend (npm run build)
      2. Copia el proyecto a una carpeta temporal, dejando afuera todo lo de desarrollo
      3. Genera el ZIP
      4. Lo descomprime en una carpeta limpia, corre instalar.bat y comprueba
         que la aplicacion levante y responda. Si eso falla, el ZIP no sirve.

    El paso 4 es el importante: es la unica forma de detectar que una dependencia
    falte o que algo se rompa solo al instalar desde cero.
#>

param(
    [switch]$SoloEmpaquetar
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

function Escribir-Paso($texto) {
    Write-Host ''
    Write-Host "== $texto" -ForegroundColor Cyan
}
function Escribir-Ok($texto)   { Write-Host "   OK   $texto" -ForegroundColor Green }
function Escribir-Fallo($texto){ Write-Host "   FALLO  $texto" -ForegroundColor Red }
function Escribir-Aviso($texto){ Write-Host "   !    $texto" -ForegroundColor Yellow }

# ---------------------------------------------------------------------------
# 0. Comprobaciones previas
# ---------------------------------------------------------------------------
Escribir-Paso '0/4  Comprobando el entorno'

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw 'No encontre npm. Para generar el paquete hace falta Node.js 20 o superior.'
}
Escribir-Ok 'npm disponible'

if (-not (Test-Path (Join-Path $raiz 'instalar.bat')) -or -not (Test-Path (Join-Path $raiz 'arrancar.bat'))) {
    throw 'Faltan instalar.bat o arrancar.bat en la raiz del proyecto.'
}
Escribir-Ok 'scripts de instalacion presentes'

$ocupado = Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue
if ($ocupado) {
    throw "El puerto $puerto esta ocupado. Cerra la aplicacion antes de empaquetar (la verificacion necesita ese puerto)."
}
Escribir-Ok "puerto $puerto libre"

# ---------------------------------------------------------------------------
# 1. Compilar el frontend
# ---------------------------------------------------------------------------
Escribir-Paso '1/4  Compilando el frontend'

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
Escribir-Paso '2/4  Armando el paquete'

if (Test-Path $tmpBase) { Remove-Item $tmpBase -Recurse -Force }
New-Item -ItemType Directory -Path $stage -Force | Out-Null

$dirsExcluidos  = @('node_modules', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache')
# *.zip tambien se excluye: el ZIP de salida se genera en la raiz del proyecto y, si
# no se filtra, robocopy lo mete dentro del paquete nuevo (robocopy no lee .gitignore).
$archExcluidos  = @('riguel.db', '*.pyc', '*.pyo', '*.tsbuildinfo', '*.log', '*.zip')

robocopy $raiz $stage /E /XD @dirsExcluidos /XF @archExcluidos /NFL /NDL /NJH /NJS /NP | Out-Null
if ($LASTEXITCODE -ge 8) { throw "robocopy fallo (codigo $LASTEXITCODE)." }

# Fotos subidas por el usuario: no viajan (solo el logo por defecto y el .gitkeep).
$dirImagenes = Join-Path $stage 'backend\data\imagenes'
if (Test-Path $dirImagenes) {
    $sobran = Get-ChildItem $dirImagenes -File -Force | Where-Object { $_.Name -notin @('logo.jpg', '.gitkeep') }
    foreach ($f in $sobran) { Remove-Item $f.FullName -Force }
    if ($sobran) { Escribir-Aviso "saque $($sobran.Count) imagen(es) subida(s) por el usuario" }
}
Escribir-Ok 'copiado sin node_modules, .venv, base de datos ni fotos propias'

# ---------------------------------------------------------------------------
# 3. Generar el ZIP
# ---------------------------------------------------------------------------
Escribir-Paso '3/4  Generando el ZIP'

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

if ($SoloEmpaquetar) {
    Write-Host ''
    Write-Host 'Listo (sin verificar).' -ForegroundColor Green
    return
}

# ---------------------------------------------------------------------------
# 4. Verificar en una carpeta limpia
# ---------------------------------------------------------------------------
Escribir-Paso '4/4  Probando el paquete desde cero'

Expand-Archive -Path $zipDestino -DestinationPath $prueba -Force
$appDir = Join-Path $prueba $nombre
if (-not (Test-Path (Join-Path $appDir 'instalar.bat'))) {
    throw "El ZIP no contiene la estructura esperada (falta instalar.bat dentro de $nombre)."
}

# El ZIP no debe traer nada de desarrollo.
foreach ($prohibido in @('frontend\node_modules', '.venv', 'backend\riguel.db')) {
    if (Test-Path (Join-Path $appDir $prohibido)) {
        throw "El ZIP contiene $prohibido y no deberia."
    }
}
if (-not (Test-Path (Join-Path $appDir 'frontend\dist\index.html'))) {
    throw 'El ZIP no incluye el frontend compilado: no funcionaria sin Node.'
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
    foreach ($ruta in @('/', '/admin/asociacion', '/observaciones/123', '/api/v1/observatorio', '/imagenes/logo.jpg')) {
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
    $datos = Invoke-RestMethod "$base/api/v1/observatorio" -TimeoutSec 20
    if ($datos.logo_path -ne 'logo.jpg') { throw "El logo por defecto no es logo.jpg (es '$($datos.logo_path)')." }
    Escribir-Ok 'base de datos limpia y logo por defecto en su lugar'

} finally {
    Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    if ($proc) { Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue }
    Remove-Item Env:\RIGUEL_SIN_NAVEGADOR -ErrorAction SilentlyContinue
    # Esperar a que el puerto quede libre de verdad antes de seguir.
    for ($i = 0; $i -lt 20; $i++) {
        if (-not (Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue)) { break }
        Start-Sleep -Milliseconds 500
    }
}

Remove-Item $prueba -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item $tmpBase -Recurse -Force -ErrorAction SilentlyContinue

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
Write-Host ''
