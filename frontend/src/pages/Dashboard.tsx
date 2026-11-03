import { useObservations, useObservacionesStats } from '../hooks/useObservations';
import { useAsociacion } from '../hooks/useAsociacion';
import { useObservatorios } from '../hooks/useObservatorios';
import { formatUTCtoMadrid } from '../utils/date';
import { formatFwhm, formatDuration } from '../utils/format';
import { Loader } from '../components/ui/Loader';

function formatearCoordenadas(observatorio: { latitud: number; longitud: number }): string {
  return `${observatorio.latitud.toFixed(4)}°, ${observatorio.longitud.toFixed(4)}°`;
}

export function Dashboard() {
  const { data: observations, isLoading } = useObservations({ limit: 5 });
  const { data: stats } = useObservacionesStats();
  const { data: asociacion } = useAsociacion();
  const { data: observatorios } = useObservatorios();

  if (isLoading) return <Loader />;

  const totalObs = observations?.length ?? 0;
  const totalExposicion = stats?.total_exposicion_seg ?? 0;
  const nombreAsociacion = asociacion?.nombre || 'Riguel';

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">{nombreAsociacion}</h1>

      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Observatorios</h2>
        {observatorios && observatorios.length > 0 ? (
          <ul className="space-y-3">
            {observatorios.map(observatorio => (
              <li
                key={observatorio.id}
                className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border-l-4"
                style={{ borderLeftColor: observatorio.color }}
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{observatorio.nombre}</span>
                    {observatorio.es_predeterminado && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-space-100 dark:bg-space-900 text-space-700 dark:text-space-300">
                        Predeterminado
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {formatearCoordenadas(observatorio)}
                    {observatorio.altitud_msnm != null &&
                      ` — ${Math.round(observatorio.altitud_msnm)} m s. n. m.`}
                  </p>
                </div>
                <span
                  className="inline-block w-4 h-4 rounded-full border border-black/10 self-start sm:self-center"
                  style={{ backgroundColor: observatorio.color }}
                  aria-hidden="true"
                />
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">
            Todavía no hay observatorios. Agregalos en{' '}
            <span className="font-medium">Asociación</span>.
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="card text-center">
          <div className="text-3xl font-bold text-space-600 dark:text-space-400">{totalObs}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Observaciones recientes</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-space-600 dark:text-space-400">{formatDuration(totalExposicion)}</div>
          <div className="text-sm text-gray-500 dark:text-gray-400">Tiempo total exposición</div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Observaciones recientes</h2>
        {observations && observations.length > 0 ? (
          <div className="space-y-3">
            {observations.map(obs => (
              <div key={obs.id} className="flex justify-between items-center p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50">
                <div>
                  <span className="font-medium">{obs.objeto}</span>
                  <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                    {formatUTCtoMadrid(obs.fecha_hora_utc)}
                  </span>
                </div>
                <span className="text-sm">{formatFwhm(obs.fwhm)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No hay observaciones registradas</p>
        )}
      </div>
    </div>
  );
}
