import { useParams, useNavigate, Link } from 'react-router-dom';
import { useObservacion, useDeleteObservacion } from '../hooks/useObservations';
import { useObservatorioActivo } from '../hooks/useObservatorioActivo';
import { useExportPDFNoche, useExportCSV } from '../hooks/useExport';
import { formatUTCtoMadrid } from '../utils/date';
import { formatFwhm, formatDuration, formatTemperature } from '../utils/format';
import { Button } from '../components/ui/Button';
import { Loader } from '../components/ui/Loader';

export function ObservationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { data: obs, isLoading } = useObservacion(id ? Number(id) : 0);
  const deleteMutation = useDeleteObservacion();
  const { observatorios } = useObservatorioActivo();
  
  const exportPDFMutation = useExportPDFNoche();
  const exportCSVMutation = useExportCSV();

  if (isLoading) return <Loader />;
  if (!obs) return <div className="card">Observación no encontrada</div>;

  const totalExposure = obs.sesiones_captura.reduce((acc, s) => acc + (s.tiempo_exposicion_seg * s.num_subs), 0);
  const observatorio = observatorios.find(o => o.id === obs.observatorio_id);

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold">{obs.objeto}</h1>
          <p className="text-gray-500 dark:text-gray-400">{formatUTCtoMadrid(obs.fecha_hora_utc)}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/observaciones/${obs.id}/edit`}>
            <Button variant="secondary">Editar</Button>
          </Link>
          <Link to={`/observaciones/new?duplicate=true&id=${obs.id}`}>
            <Button variant="secondary">Duplicar</Button>
          </Link>
          <Button
            variant="danger"
            onClick={() => {
              if (confirm('¿Eliminar esta observación?')) {
                deleteMutation.mutate(obs.id, { onSuccess: () => navigate('/observaciones') });
              }
            }}
          >
            Eliminar
          </Button>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Datos Generales</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Observatorio</span>
            <p className="flex items-center gap-2">
              {observatorio && (
                <span
                  className="inline-block w-3 h-3 rounded-full border border-black/10"
                  style={{ backgroundColor: observatorio.color }}
                  aria-hidden="true"
                />
              )}
              {observatorio?.nombre ?? '—'}
            </p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">FWHM</span>
            <p>{formatFwhm(obs.fwhm)}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Temperatura</span>
            <p>{formatTemperature(obs.temperatura)}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Humedad</span>
            <p>{obs.humedad ?? '—'}%</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Viento</span>
            <p>{obs.viento_kph ? `${obs.viento_kph} km/h ${obs.direccion_viento ?? ''}` : '—'}</p>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Tiempo total</span>
            <p>{formatDuration(totalExposure)}</p>
          </div>
        </div>
        {obs.descripcion && (
          <div className="mt-4">
            <span className="text-gray-500 dark:text-gray-400 text-sm">Descripción</span>
            <p className="mt-1">{obs.descripcion}</p>
          </div>
        )}
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Sesiones de Captura ({obs.sesiones_captura.length})</h2>
        <div className="space-y-4">
          {obs.sesiones_captura.map(sesion => (
            <div key={sesion.id} className="p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="flex justify-between items-center mb-2">
                <span className="font-medium">Filtro: {sesion.filtro_id}</span>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {sesion.tiempo_exposicion_seg}s × {sesion.num_subs} = {formatDuration(sesion.tiempo_exposicion_seg * sesion.num_subs)}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 dark:text-gray-400">
                <span>Binning: {sesion.binning}x{sesion.binning}</span>
                <span>Temp: {sesion.temp_sensor ?? '—'}°C</span>
              </div>
              {sesion.calibraciones.length > 0 && (
                <div className="mt-2 text-xs">
                  <span className="text-gray-500 dark:text-gray-400">Calibraciones: </span>
                  {sesion.calibraciones.map(c => `${c.tipo} (${c.count})`).join(', ')}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          variant="secondary"
          onClick={() => exportPDFMutation.mutate(obs.fecha_hora_utc)}
          disabled={exportPDFMutation.isPending}
        >
          Exportar PDF noche
        </Button>
        <Button
          variant="secondary"
          onClick={() => exportCSVMutation.mutate({ tabla: 'observaciones' })}
          disabled={exportCSVMutation.isPending}
        >
          Exportar CSV
        </Button>
      </div>
    </div>
  );
}