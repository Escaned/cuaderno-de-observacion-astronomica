import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Textarea } from '../ui/Textarea';

interface NightHeaderProps {
  objeto: string;
  fecha_hora_utc: string;
  filtro_id: number | '';
  seeing: number;
  temperatura: string;
  humedad: string;
  viento_kph: string;
  direccion_viento: string;
  descripcion: string;
  filtros: { id: number; nombre: string }[];
  errors: Record<string, string>;
  onChange: (field: string, value: string | number) => void;
}

export function NightHeader({
  objeto,
  fecha_hora_utc,
  filtro_id,
  seeing,
  temperatura,
  humedad,
  viento_kph,
  direccion_viento,
  descripcion,
  filtros,
  errors,
  onChange,
}: NightHeaderProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Datos de la Noche</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <Input
            label="Objeto *"
            value={objeto}
            onChange={e => onChange('objeto', e.target.value)}
            placeholder="M42, NGC7000..."
          />
          {errors.objeto && <p className="text-red-500 text-xs mt-1">{errors.objeto}</p>}
        </div>
        <div>
          <Input
            label="Fecha y hora (UTC) *"
            type="datetime-local"
            value={fecha_hora_utc}
            onChange={e => onChange('fecha_hora_utc', e.target.value)}
          />
          {errors.fecha_hora_utc && <p className="text-red-500 text-xs mt-1">{errors.fecha_hora_utc}</p>}
        </div>
        <Select
          label="Filtro"
          value={filtro_id}
          onChange={e => onChange('filtro_id', e.target.value ? Number(e.target.value) : '')}
          options={[
            { value: '', label: 'Sin filtro' },
            ...filtros.map(f => ({ value: f.id, label: f.nombre })),
          ]}
        />
        <Select
          label="Seeing *"
          value={seeing}
          onChange={e => onChange('seeing', Number(e.target.value))}
          options={[
            { value: 1, label: 'I — Malo' },
            { value: 2, label: 'II — Regular' },
            { value: 3, label: 'III — Bueno' },
            { value: 4, label: 'IV — Muy bueno' },
            { value: 5, label: 'V — Excelente' },
          ]}
        />
        <Input
          label="Temperatura (°C)"
          type="number"
          step="0.1"
          value={temperatura}
          onChange={e => onChange('temperatura', e.target.value)}
        />
        <Input
          label="Humedad (%)"
          type="number"
          min="0"
          max="100"
          value={humedad}
          onChange={e => onChange('humedad', e.target.value)}
        />
        <Input
          label="Viento (km/h)"
          type="number"
          step="0.1"
          value={viento_kph}
          onChange={e => onChange('viento_kph', e.target.value)}
        />
        <Input
          label="Dirección viento"
          value={direccion_viento}
          onChange={e => onChange('direccion_viento', e.target.value)}
          placeholder="N, NE, E, SE, S, SO, O, NO"
        />
      </div>
      <Textarea
        label="Descripción"
        value={descripcion}
        onChange={e => onChange('descripcion', e.target.value)}
        rows={3}
        placeholder="Notas sobre la noche, condiciones, etc."
      />
    </div>
  );
}