import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getObservacionesStats,
  getObservaciones,
  getObservacion,
  createObservacion,
  updateObservacion,
  duplicateObservacion,
  deleteObservacion,
} from '../services/api';
import type { ObservacionCreate } from '../types';

export function useObservacionesStats() {
  return useQuery({
    queryKey: ['observaciones-stats'],
    queryFn: () => getObservacionesStats(),
  });
}

export function useObservations(params?: {
  skip?: number;
  limit?: number;
  filtro_id?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  objeto?: string;
}) {
  return useQuery({
    queryKey: ['observaciones', params],
    queryFn: () => getObservaciones(params),
  });
}

export function useObservacion(id: number) {
  return useQuery({
    queryKey: ['observacion', id],
    queryFn: () => getObservacion(id),
    enabled: !!id,
  });
}

export function useCreateObservacion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ObservacionCreate) => createObservacion(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observaciones'] }),
  });
}

export function useUpdateObservacion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<ObservacionCreate> }) =>
      updateObservacion(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observaciones'] }),
  });
}

export function useDuplicateObservacion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => duplicateObservacion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observaciones'] }),
  });
}

export function useDeleteObservacion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteObservacion(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observaciones'] }),
  });
}