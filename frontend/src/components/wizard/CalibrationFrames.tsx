import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import type { SesionCapturaCreate, TipoCalibracion } from '../../types';

interface CalibrationFramesProps {
  sesiones: SesionCapturaCreate[];
  filtros: { id: number; nombre: string }[];
  onChange: (sesiones: SesionCapturaCreate[]) => void;
}

const CALIBRATION_TYPES: { value: TipoCalibracion; label: string }[] = [
  { value: 'dark', label: 'Dark' },
  { value: 'flat', label: 'Flat' },
  { value: 'bias', label: 'Bias' },
  { value: 'darkflat', label: 'Dark-Flat' },
];

export function CalibrationFrames({ sesiones, filtros, onChange }: CalibrationFramesProps) {
  const updateCalibracion = (
    sesionIdx: number,
    calIdx: number,
    field: string,
    value: unknown
  ) => {
    const updated = [...sesiones];
    const sesion = { ...updated[sesionIdx] };
    const cals = [...sesion.calibraciones];
    cals[calIdx] = { ...cals[calIdx], [field]: value };
    sesion.calibraciones = cals;
    updated[sesionIdx] = sesion;
    onChange(updated);
  };

  const addCalibracion = (sesionIdx: number) => {
    const updated = [...sesiones];
    const sesion = { ...updated[sesionIdx] };
    sesion.calibraciones = [
      ...sesion.calibraciones,
      { tipo: 'dark', count: 0, tiempo_exposicion_seg: null, temperatura: null, filtro_id: null, notas: null },
    ];
    updated[sesionIdx] = sesion;
    onChange(updated);
  };

  const removeCalibracion = (sesionIdx: number, calIdx: number) => {
    const updated = [...sesiones];
    const sesion = { ...updated[sesionIdx] };
    sesion.calibraciones = sesion.calibraciones.filter((_, i) => i !== calIdx);
    updated[sesionIdx] = sesion;
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Calibraciones</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Configura los frames de calibración para cada sesión de captura.
      </p>

      {sesiones.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-4">
          Primero añade una sesión de captura.
        </p>
      )}

      {sesiones.map((sesion, sesionIdx) => (
        <div key={sesionIdx} className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg space-y-3">
          <div className="flex justify-between items-center">
            <span className="font-medium text-sm">
              Sesión {sesionIdx + 1} — {filtros.find(f => f.id === sesion.filtro_id)?.nombre ?? 'Sin filtro'}
            </span>
            <Button type="button" variant="secondary" onClick={() => addCalibracion(sesionIdx)}>
              + Calibración
            </Button>
          </div>

          {sesion.calibraciones.length === 0 && (
            <p className="text-xs text-gray-500 dark:text-gray-400">Sin calibraciones</p>
          )}

          {sesion.calibraciones.map((cal, calIdx) => (
            <div key={calIdx} className="grid grid-cols-2 md:grid-cols-5 gap-2 items-end p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
              <Select
                label="Tipo"
                value={cal.tipo}
                onChange={e => updateCalibracion(sesionIdx, calIdx, 'tipo', e.target.value)}
                options={CALIBRATION_TYPES.map(t => ({ value: t.value, label: t.label }))}
              />
              <Input
                label="Cantidad"
                type="number"
                min="0"
                value={cal.count}
                onChange={e => updateCalibracion(sesionIdx, calIdx, 'count', Number(e.target.value))}
              />
              <Input
                label="Exposición (s)"
                type="number"
                value={cal.tiempo_exposicion_seg ?? ''}
                onChange={e =>
                  updateCalibracion(sesionIdx, calIdx, 'tiempo_exposicion_seg', e.target.value ? Number(e.target.value) : null)
                }
              />
              <Input
                label="Temp. (°C)"
                type="number"
                step="0.1"
                value={cal.temperatura ?? ''}
                onChange={e =>
                  updateCalibracion(sesionIdx, calIdx, 'temperatura', e.target.value ? Number(e.target.value) : null)
                }
              />
              <div className="flex items-end">
                <button
                  type="button"
                  onClick={() => removeCalibracion(sesionIdx, calIdx)}
                  className="text-red-500 hover:text-red-700 text-sm px-2 py-2"
                >
                  ✕
                </button>
              </div>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}