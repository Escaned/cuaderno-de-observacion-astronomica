import { useState } from 'react';
import { useFilters, useCreateFilter, useUpdateFilter, useDeleteFilter, useReorderFilters } from '../hooks/useFilters';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Textarea } from '../components/ui/Textarea';
import { Modal } from '../components/ui/Modal';
import { Loader } from '../components/ui/Loader';
import type { Filtro } from '../types';

export function AdminFiltros() {
  const { data: filtros, isLoading } = useFilters();
  const createMutation = useCreateFilter();
  const updateMutation = useUpdateFilter();
  const deleteMutation = useDeleteFilter();
  const reorderMutation = useReorderFilters();

  const [editing, setEditing] = useState<Filtro | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [dragIdx, setDragIdx] = useState<number | null>(null);

  if (isLoading) return <Loader />;

  const handleEdit = (filtro: Filtro) => {
    setEditing(filtro);
    setIsModalOpen(true);
  };

  const handleNew = () => {
    setEditing(null);
    setIsModalOpen(true);
  };

  const handleDelete = (id: number) => {
    if (confirm('¿Eliminar este filtro?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleDragStart = (idx: number) => setDragIdx(idx);
  const handleDragOver = (e: React.DragEvent, idx: number) => {
    e.preventDefault();
    if (dragIdx === null || dragIdx === idx) return;
    const updated = [...(filtros ?? [])];
    const [moved] = updated.splice(dragIdx, 1);
    updated.splice(idx, 0, moved);
    // Update orden locally
    const reorders = updated.map((f, i) => ({ filtro_id: f.id, orden: i + 1 }));
    reorderMutation.mutate(reorders);
    setDragIdx(idx);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Administración de Filtros</h1>
        <Button onClick={handleNew}>+ Nuevo filtro</Button>
      </div>

      <div className="card">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700">
              <th className="text-left py-3 px-2 w-8"></th>
              <th className="text-left py-3 px-2">Orden</th>
              <th className="text-left py-3 px-2">Nombre</th>
              <th className="text-left py-3 px-2">Descripción</th>
              <th className="text-left py-3 px-2">λ central (nm)</th>
              <th className="text-left py-3 px-2">Activo</th>
              <th className="py-3 px-2"></th>
            </tr>
          </thead>
          <tbody>
            {filtros?.map((filtro, idx) => (
              <tr
                key={filtro.id}
                draggable
                onDragStart={() => handleDragStart(idx)}
                onDragOver={e => handleDragOver(e, idx)}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-move"
              >
                <td className="py-3 px-2 text-gray-400">⋮⋮</td>
                <td className="py-3 px-2">{filtro.orden}</td>
                <td className="py-3 px-2 font-medium">{filtro.nombre}</td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400">{filtro.descripcion ?? '—'}</td>
                <td className="py-3 px-2">{filtro.onda_central_nm ?? '—'}</td>
                <td className="py-3 px-2">
                  <button
                    onClick={() => updateMutation.mutate({ id: filtro.id, data: { activo: !filtro.activo } })}
                    className={`w-10 h-5 rounded-full transition-colors ${
                      filtro.activo ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <div
                      className={`w-4 h-4 bg-white rounded-full transition-transform ${
                        filtro.activo ? 'translate-x-5' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </td>
                <td className="py-3 px-2 text-right">
                  <button onClick={() => handleEdit(filtro)} className="text-space-600 hover:underline mr-2 text-xs">
                    Editar
                  </button>
                  <button onClick={() => handleDelete(filtro.id)} className="text-red-500 hover:text-red-700 text-xs">
                    Eliminar
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} title={editing ? 'Editar Filtro' : 'Nuevo Filtro'}>
        <FiltroForm
          initial={editing}
          onSubmit={data => {
            if (editing) {
              updateMutation.mutate({ id: editing.id, data }, { onSuccess: () => setIsModalOpen(false) });
            } else {
              createMutation.mutate(data, { onSuccess: () => setIsModalOpen(false) });
            }
          }}
          onCancel={() => setIsModalOpen(false)}
          isSubmitting={createMutation.isPending || updateMutation.isPending}
        />
      </Modal>
    </div>
  );
}

function FiltroForm({
  initial,
  onSubmit,
  onCancel,
  isSubmitting,
}: {
  initial: Filtro | null;
  onSubmit: (data: Partial<Filtro>) => void;
  onCancel: () => void;
  isSubmitting: boolean;
}) {
  const [nombre, setNombre] = useState(initial?.nombre ?? '');
  const [descripcion, setDescripcion] = useState(initial?.descripcion ?? '');
  const [ondaCentral, setOndaCentral] = useState(initial?.onda_central_nm?.toString() ?? '');
  const [orden, setOrden] = useState(initial?.orden ?? 0);
  const [activo, setActivo] = useState(initial?.activo ?? true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      nombre,
      descripcion: descripcion || null,
      onda_central_nm: ondaCentral ? Number(ondaCentral) : null,
      orden,
      activo,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <Input label="Nombre *" value={nombre} onChange={e => setNombre(e.target.value)} maxLength={20} />
      <Textarea label="Descripción" value={descripcion} onChange={e => setDescripcion(e.target.value)} rows={2} />
      <div className="grid grid-cols-2 gap-4">
        <Input label="Longitud de onda (nm)" type="number" step="0.1" value={ondaCentral} onChange={e => setOndaCentral(e.target.value)} />
        <Input label="Orden" type="number" value={orden} onChange={e => setOrden(Number(e.target.value))} />
      </div>
      <label className="flex items-center gap-2">
        <input type="checkbox" checked={activo} onChange={e => setActivo(e.target.checked)} />
        <span className="text-sm">Activo</span>
      </label>
      <div className="flex justify-end gap-2">
        <Button type="button" variant="secondary" onClick={onCancel}>Cancelar</Button>
        <Button type="submit" disabled={isSubmitting}>{isSubmitting ? 'Guardando...' : 'Guardar'}</Button>
      </div>
    </form>
  );
}