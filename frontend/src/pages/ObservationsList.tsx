import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useObservations, useDeleteObservacion } from '../hooks/useObservations';
import { useFilters } from '../hooks/useFilters';
import { useObservatorioActivo } from '../hooks/useObservatorioActivo';
import { ObservatorioSelector } from '../components/ObservatorioSelector';
import { formatUTCtoMadrid } from '../utils/date';
import { formatFwhm } from '../utils/format';
import { Loader } from '../components/ui/Loader';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Select } from '../components/ui/Select';

export function ObservationsList() {
  const [search, setSearch] = useState('');
  const [filtroId, setFiltroId] = useState<number | ''>('');
  const { observatorios, activo } = useObservatorioActivo();

  const { data: observations, isLoading } = useObservations({
    objeto: search || undefined,
    filtro_id: filtroId || undefined,
    observatorio_id: activo?.id,
  });
  const { data: filtros } = useFilters();
  const deleteMutation = useDeleteObservacion();

  if (isLoading) return <Loader />;

  const nombreObservatorio = (id: number | null) =>
    (id != null && observatorios.find(o => o.id === id)?.nombre) || '—';

  return (
    <div>
      <ObservatorioSelector />

      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Observaciones</h1>
          {activo && (
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Mostrando las de <span className="font-medium">{activo.nombre}</span>
            </p>
          )}
        </div>
        <Link to="/observaciones/new">
          <Button>Nueva observación</Button>
        </Link>
      </div>

      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <Input
            placeholder="Buscar por objeto..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <div className="w-48">
          <Select
            value={filtroId}
            onChange={e => setFiltroId(e.target.value ? Number(e.target.value) : '')}
            options={[
              { value: '', label: 'Todos los filtros' },
              ...(filtros?.map(f => ({ value: f.id, label: f.nombre })) ?? []),
            ]}
          />
        </div>
      </div>

      {observations && observations.length > 0 ? (
        <div className="card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="text-left py-3 px-4">Objeto</th>
                <th className="text-left py-3 px-4">Fecha (Madrid)</th>
                <th className="text-left py-3 px-4">Observatorio</th>
                <th className="text-left py-3 px-4">FWHM</th>
                <th className="text-left py-3 px-4">Filtro</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {observations.map(obs => (
                <tr key={obs.id} className="border-b border-gray-100 dark:border-gray-800">
                  <td className="py-3 px-4">
                    <Link to={`/observaciones/${obs.id}`} className="text-space-600 dark:text-space-400 hover:underline font-medium">
                      {obs.objeto}
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {formatUTCtoMadrid(obs.fecha_hora_utc)}
                  </td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {nombreObservatorio(obs.observatorio_id)}
                  </td>
                  <td className="py-3 px-4">{formatFwhm(obs.fwhm)}</td>
                  <td className="py-3 px-4 text-gray-600 dark:text-gray-400">
                    {filtros?.find(f => f.id === obs.filtro_id)?.nombre ?? '—'}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={() => deleteMutation.mutate(obs.id)}
                      className="text-red-500 hover:text-red-700 text-xs"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card text-center text-gray-500 dark:text-gray-400">
          No hay observaciones
        </div>
      )}
    </div>
  );
}
