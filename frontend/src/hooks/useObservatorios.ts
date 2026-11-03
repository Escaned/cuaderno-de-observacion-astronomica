import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getObservatorios,
  createObservatorio,
  updateObservatorio,
  deleteObservatorio,
  setObservatorioPredeterminado,
} from '../services/api';
import type { ObservatorioCreate } from '../types';

export function useObservatorios() {
  return useQuery({
    queryKey: ['observatorios'],
    queryFn: getObservatorios,
  });
}

function useInvalidarObservatorios() {
  const qc = useQueryClient();
  return () => {
    qc.invalidateQueries({ queryKey: ['observatorios'] });
    // Las observaciones muestran el nombre del observatorio, asi que tambien
    // hay que refrescarlas cuando cambia la lista.
    qc.invalidateQueries({ queryKey: ['observaciones'] });
  };
}

export function useCreateObservatorio() {
  const invalidar = useInvalidarObservatorios();
  return useMutation({
    mutationFn: (data: ObservatorioCreate) => createObservatorio(data),
    onSuccess: invalidar,
  });
}

export function useUpdateObservatorio() {
  const invalidar = useInvalidarObservatorios();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ObservatorioCreate> }) =>
      updateObservatorio(id, data),
    onSuccess: invalidar,
  });
}

export function useDeleteObservatorio() {
  const invalidar = useInvalidarObservatorios();
  return useMutation({
    mutationFn: (id: number) => deleteObservatorio(id),
    onSuccess: invalidar,
  });
}

export function useSetObservatorioPredeterminado() {
  const invalidar = useInvalidarObservatorios();
  return useMutation({
    mutationFn: (id: number) => setObservatorioPredeterminado(id),
    onSuccess: invalidar,
  });
}
