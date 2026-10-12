import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import type { SesionCapturaCreate } from '../../types';

interface CaptureSessionsProps {
  sesiones: SesionCapturaCreate[];
  filtros: { id: number; nombre: string }[];
  errors: Record<string, string>;
  onChange: (sesiones: SesionCapturaCreate[]) => void;
}

export function CaptureSessions({ sesiones, filtros, errors, onChange }: CaptureSessionsProps) {
  const addSesion = () => {
    onChange([
      ...sesiones,
      {
        filtro_id: filtros[0]?.id ?? 0,
        tiempo_exposicion_seg: 300,
        num_subs: 10,
        binning: 1,
        temp_sensor: null,
        calibraciones: [],
      },
    ]);
  };

  const removeSesion = (index: number) => {
    onChange(sesiones.filter((_, i) => i !== index));
  };

  const updateSesion = (index: number, field: string, value: unknown) => {
    const updated = [...sesiones];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold">Sesiones de Captura</h3>
        <Button type="button" variant="secondary" onClick={addSesion}>
          + Añadir sesión
        </Button>
      </div>

      {errors.sesiones && <p className="text-red-500 text-sm">{errors.sesiones}</p>}

      {sesiones.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-4">
          No hay sesiones de captura. Añade al menos una.
        </p>
      )}

      {sesiones.map((sesion, idx) => (
        <div key={idx} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-3">
          <div className="flex justify-between items-center">
            <span className="font-medium text-sm">Sesión {idx + 1}</span>
            <button
              type="button"
              onClick={() => removeSesion(idx)}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              Eliminar
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Select
              label="Filtro *"
              value={sesion.filtro_id}
              onChange={e => updateSesion(idx, 'filtro_id', Number(e.target.value))}
              options={filtros.map(f => ({ value: f.id, label: f.nombre }))}
            />
            <Input
              label="Exposición (s) *"
              type="number"
              min="1"
              value={sesion.tiempo_exposicion_seg}
              onChange={e => updateSesion(idx, 'tiempo_exposicion_seg', Number(e.target.value))}
            />
            <Input
              label="Número de tomas *"
              type="number"
              min="1"
              value={sesion.num_subs}
              onChange={e => updateSesion(idx, 'num_subs', Number(e.target.value))}
            />
            <Select
              label="Binning"
              value={sesion.binning}
              onChange={e => updateSesion(idx, 'binning', Number(e.target.value))}
              options={[
                { value: 1, label: '1x1' },
                { value: 2, label: '2x2' },
              ]}
            />
            <Input
              label="Temp. sensor (°C)"
              type="number"
              step="0.1"
              value={sesion.temp_sensor ?? ''}
              onChange={e => updateSesion(idx, 'temp_sensor', e.target.value ? Number(e.target.value) : null)}
            />
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Tiempo total: {((sesion.tiempo_exposicion_seg * sesion.num_subs) / 60).toFixed(1)} min
          </p>
        </div>
      ))}
    </div>
  );
}