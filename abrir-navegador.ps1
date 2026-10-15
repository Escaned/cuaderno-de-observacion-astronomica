# Espera a que el servidor responda y recien ahi abre el navegador.
# Lo usa arrancar.bat:   powershell -File abrir-navegador.ps1
#
# Detalles que importan:
#   * Se consulta 127.0.0.1 y NO localhost. En Windows "localhost" resuelve primero
#     a ::1 (IPv6); como el servidor escucha solo en IPv4, cada intento se come el
#     timeout del IPv6 antes de caer al IPv4. Con el timeout corto eso falla siempre.
#     El navegador no sufre esto porque hace "Happy Eyeballs", asi que la direccion
#     que se abre sigue siendo localhost.
#   * La espera tiene tope. Si algo raro pasara, igual abre el navegador en vez de
#     quedarse colgado para siempre.

param(
    [int]$Puerto = 8000,
    [int]$MaxEsperaSegundos = 30
)

$url   = "http://localhost:$Puerto"
$salud = "http://127.0.0.1:$Puerto/health"
$limite = (Get-Date).AddSeconds($MaxEsperaSegundos)

while ((Get-Date) -lt $limite) {
    try {
        Invoke-WebRequest $salud -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop | Out-Null
        break
    } catch {
        Start-Sleep -Milliseconds 400
    }
}

Start-Process $url
