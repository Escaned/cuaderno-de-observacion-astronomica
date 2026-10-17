<#
    empaquetar.ps1
    Genera el ZIP de distribucion de "Riguel - Cuaderno de Campo Astronomico".

    Uso:
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -SoloEmpaquetar
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -ConExe
        powershell -ExecutionPolicy Bypass -File empaquetar.ps1 -SoloEmpaquetar -ConExe

    Que hace:
      1. Compila el frontend (npm run build)
      2. Copia el proyecto a una carpeta temporal, dejando afuera todo lo de desarrollo
      3. Genera el ZIP
      4. Lo descomprime en una carpeta limpia, corre instalar.bat y comprueba
         que la aplicacion levante y responda. Si eso falla, el ZIP no sirve.
      5. (solo con -ConExe) Construye el ejecutable con PyInstaller y lo prueba
         entero: en una carpeta limpia, con una base de datos de por medio y
         reiniciandolo, para comprobar que lo que guarda sobrevive.

    Los pasos 4 y 5 son los importantes: son la unica forma de detectar que una
    dependencia falte o que algo se rompa solo al instalar desde cero. El paso 5
    comprueba ademas cosas que SOLO pueden fallar una vez empaquetado, como que la
    interfaz compilada se encuentre adentro del paquete.

    -SoloEmpaquetar saltea el paso 4. Combinado con -ConExe saltea la instalacion
    completa y va derecho al ejecutable, que es lo comodo mientras se lo esta
    ajustando.
#>

param(
    [switch]$SoloEmpaquetar,
    [switch]$ConExe
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

$ocupado = Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue
if ($ocupado) {
    throw "El puerto $puerto esta ocupado. Cerra la aplicacion antes de empaquetar (la verificacion necesita ese puerto)."
}
Escribir-Ok "puerto $puerto libre"

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
Escribir-Paso "5/$pasos  Construyendo el ejecutable"

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
Escribir-Paso "5/$pasos  Probando el ejecutable desde cero"

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
    Get-NetTCPConnection -LocalPort $puertoExe -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    if ($proceso) { Stop-Process -Id $proceso.Id -Force -ErrorAction SilentlyContinue }
    for ($i = 0; $i -lt 20; $i++) {
        if (-not (Get-NetTCPConnection -LocalPort $puertoExe -State Listen -ErrorAction SilentlyContinue)) { break }
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
    Invoke-RestMethod "$baseExe/api/v1/observatorio" -Method Put -TimeoutSec 20 `
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

    foreach ($ruta in @('/', '/admin/asociacion', '/observaciones/123', '/api/v1/observatorio', '/api/v1/filtros', '/imagenes/logo.jpg')) {
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
    $direcciones = @(Get-NetTCPConnection -LocalPort $puertoExe -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty LocalAddress -Unique)
    if ($direcciones -notcontains '127.0.0.1') {
        throw "No escucha en 127.0.0.1 (escucha en: $($direcciones -join ', '))."
    }
    if ($direcciones -contains '0.0.0.0' -or $direcciones -contains '::') {
        throw "Escucha en TODAS las interfaces ($($direcciones -join ', ')): las observaciones quedarian expuestas a la red local."
    }
    Escribir-Ok "escucha solo en loopback ($($direcciones -join ', '))"

    # La semilla (observatorio + 6 filtros) vive en las migraciones, no en create_all:
    # si el ejecutable usara create_all la base quedaria vacia y sin filtros.
    $datos = Invoke-RestMethod "$baseExe/api/v1/observatorio" -TimeoutSec 20
    if ($datos.nombre -ne 'Riguel') { throw "El observatorio deberia llamarse 'Riguel' y se llama '$($datos.nombre)'." }
    if ($datos.logo_path -ne 'logo.jpg') { throw "El logo por defecto no es logo.jpg (es '$($datos.logo_path)')." }
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
    Escribir-Ok 'base sembrada por las migraciones: Riguel, 6 filtros, ninguna observacion'

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
    $subida = Subir-Logo "$baseExe/api/v1/observatorio/logo" $logoPrueba
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
    $datos = Invoke-RestMethod "$baseExe/api/v1/observatorio" -TimeoutSec 20
    if ($datos.nombre -ne $marca) { throw "El nombre no sobrevivio al reinicio: '$($datos.nombre)' en vez de '$marca'." }
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
    $datos = Invoke-RestMethod "$baseExe/api/v1/observatorio" -TimeoutSec 20
    if ($datos.nombre -ne $marca) {
        throw "No adopto la base anterior: el observatorio se llama '$($datos.nombre)' y la base vieja decia '$marca'."
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
    $datos = Invoke-RestMethod "$baseExe/api/v1/observatorio" -TimeoutSec 20
    if ($datos.nombre -ne $marcaNueva) {
        throw "Piso la base en uso con la anterior: dice '$($datos.nombre)' y deberia decir '$marcaNueva'."
    }
    Escribir-Ok 'con las dos bases presentes gana la que esta en uso'

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
Write-Host ''
