import { useObservations, useObservacionesStats } from '../hooks/useObservations';
import { useObservatorio } from '../hooks/useObservatorio';
import { formatUTCtoMadrid } from '../utils/date';
import { formatFwhm, formatDuration } from '../utils/format';
import { Loader } from '../components/ui/Loader';

export function Dashboard() {
  const { data: observations, isLoading } = useObservations({ limit: 5 });
  const { data: stats } = useObservacionesStats();
  const { data: observatorio } = useObservatorio();

  if (isLoading) return <Loader />;

  const totalObs = observations?.length ?? 0;
  const totalExposicion = stats?.total_exposicion_seg ?? 0;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Grupo Astronómico Riquel Binaced - Valcarca</h1>

      {observatorio && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-2">Observatorio</h2>
          <p className="text-gray-600 dark:text-gray-400">
            Galactica — {observatorio.latitud.toFixed(4)}°, {observatorio.longitud.toFixed(4)}°
            {observatorio.altitud_msnm && ` — ${observatorio.altitud_msnm}m`}
          </p>
        </div>
      )}

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