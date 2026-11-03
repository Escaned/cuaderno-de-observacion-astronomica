import { Select } from './ui/Select';
import { useObservatorioActivo } from '../hooks/useObservatorioActivo';

interface ObservatorioSelectorProps {
  ayuda?: boolean;
}

export function ObservatorioSelector({ ayuda = true }: ObservatorioSelectorProps) {
  const { observatorios, activo, setActivoId } = useObservatorioActivo();

  if (observatorios.length === 0) return null;

  const color = activo?.color ?? '#4d48e2';

  return (
    <div
      className="card mb-6 border-l-4"
      style={{ borderLeftColor: color }}
    >
      <div className="flex flex-col sm:flex-row sm:items-end gap-4">
        <div className="w-full sm:w-80">
          <Select
            label="Observatorio"
            value={activo?.id ?? ''}
            onChange={e => setActivoId(Number(e.target.value))}
            options={observatorios.map(o => ({
              value: o.id,
              label: o.es_predeterminado ? `${o.nombre} (predeterminado)` : o.nombre,
            }))}
          />
        </div>

        {activo && (
          <div className="flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
            <span
              className="inline-block w-4 h-4 rounded-full border border-black/10"
              style={{ backgroundColor: color }}
              aria-hidden="true"
            />
            <span>
              {activo.latitud.toFixed(4)}°, {activo.longitud.toFixed(4)}°
              {activo.altitud_msnm != null && ` — ${Math.round(activo.altitud_msnm)} m s. n. m.`}
            </span>
          </div>
        )}
      </div>

      {ayuda && (
        <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
          El color de la pantalla identifica el observatorio activo. Cambialo solo si vas a
          registrar observaciones desde otro sitio.
        </p>
      )}
    </div>
  );
}
