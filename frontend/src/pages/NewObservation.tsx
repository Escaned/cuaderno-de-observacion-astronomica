import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useFilters } from '../hooks/useFilters';
import { useCreateObservacion, useObservacion, useUpdateObservacion } from '../hooks/useObservations';
import { WizardLayout } from '../components/wizard/WizardLayout';
import { Loader } from '../components/ui/Loader';
import type { ObservacionCreate } from '../types';

export function NewObservation() {
  const navigate = useNavigate();
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const duplicate = searchParams.get('duplicate') === 'true';
  const editMode = !!id;

  const { data: filtros, isLoading: filtrosLoading } = useFilters(true);
  const { data: observacion, isLoading: obsLoading } = useObservacion(id ? Number(id) : 0);
  const createMutation = useCreateObservacion();
  const updateMutation = useUpdateObservacion();

  if (filtrosLoading || (editMode && obsLoading)) return <Loader />;

  const initialData = editMode && observacion
    ? {
        objeto: observacion.objeto,
        fechaHoraUtc: observacion.fecha_hora_utc,
        filtroId: observacion.filtro_id ?? '',
        seeing: observacion.seeing,
        temperatura: observacion.temperatura,
        humedad: observacion.humedad,
        vientoKph: observacion.viento_kph,
        direccionViento: observacion.direccion_viento,
        descripcion: observacion.descripcion,
        imagenes: observacion.imagenes,
        sesiones_captura: observacion.sesiones_captura.map(s => ({
          filtro_id: s.filtro_id,
          tiempo_exposicion_seg: s.tiempo_exposicion_seg,
          num_subs: s.num_subs,
          binning: s.binning,
          temp_sensor: s.temp_sensor,
          calibraciones: s.calibraciones.map(c => ({
            tipo: c.tipo,
            count: c.count,
            tiempo_exposicion_seg: c.tiempo_exposicion_seg,
            temperatura: c.temperatura,
            filtro_id: c.filtro_id,
            notas: c.notas,
          })),
        })),
      }
    : undefined;

  const handleSubmit = (data: ObservacionCreate) => {
    if (editMode && id) {
      updateMutation.mutate(
        { id: Number(id), data },
        { onSuccess: () => navigate(`/observaciones/${id}`) }
      );
    } else {
      createMutation.mutate(data, {
        onSuccess: newObs => navigate(`/observaciones/${newObs.id}`),
      });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">
        {editMode ? 'Editar Observación' : duplicate ? 'Duplicar Observación' : 'Nueva Observación'}
      </h1>
      <WizardLayout
        initialData={initialData}
        filtros={filtros ?? []}
        onSubmit={handleSubmit}
        onCancel={() => navigate(-1)}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
      />
    </div>
  );
}