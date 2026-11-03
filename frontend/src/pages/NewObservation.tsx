import { useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useFilters } from '../hooks/useFilters';
import { useCreateObservacion, useObservacion, useUpdateObservacion } from '../hooks/useObservations';
import { useObservatorioActivo } from '../hooks/useObservatorioActivo';
import { ObservatorioSelector } from '../components/ObservatorioSelector';
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
  const { activo, setActivoId } = useObservatorioActivo();
  const createMutation = useCreateObservacion();
  const updateMutation = useUpdateObservacion();

  // Al editar, la pantalla muestra el observatorio al que pertenece la
  // observacion (con su color), no el que estuviera seleccionado antes.
  useEffect(() => {
    if (editMode && observacion?.observatorio_id != null) {
      setActivoId(observacion.observatorio_id);
    }
  }, [editMode, observacion?.observatorio_id, setActivoId]);

  if (filtrosLoading || (editMode && obsLoading)) return <Loader />;

  const initialData = editMode && observacion
    ? {
        objeto: observacion.objeto,
        fechaHoraUtc: observacion.fecha_hora_utc,
        filtroId: observacion.filtro_id ?? '',
        fwhm: observacion.fwhm,
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

  const observatorioId =
    (editMode ? observacion?.observatorio_id : undefined) ?? activo?.id ?? null;

  const handleSubmit = (data: ObservacionCreate) => {
    const payload: ObservacionCreate = { ...data, observatorio_id: observatorioId };
    if (editMode && id) {
      updateMutation.mutate(
        { id: Number(id), data: payload },
        { onSuccess: () => navigate(`/observaciones/${id}`) }
      );
    } else {
      createMutation.mutate(payload, {
        onSuccess: newObs => navigate(`/observaciones/${newObs.id}`),
      });
    }
  };

  return (
    <div>
      <ObservatorioSelector />

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
