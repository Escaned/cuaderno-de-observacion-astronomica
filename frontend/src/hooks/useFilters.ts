import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getFiltros, createFiltro, updateFiltro, deleteFiltro, reorderFiltros } from '../services/api';
import type { Filtro } from '../types';

export function useFilters(activoOnly = false) {
  return useQuery({
    queryKey: ['filtros', activoOnly],
    queryFn: () => getFiltros(activoOnly),
  });
}

export function useCreateFilter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Partial<Filtro>) => createFiltro(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['filtros'] }),
  });
}

export function useUpdateFilter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Filtro> }) => updateFiltro(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['filtros'] }),
  });
}

export function useDeleteFilter() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteFiltro(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['filtros'] }),
  });
}

export function useReorderFilters() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reorders: { filtro_id: number; orden: number }[]) => reorderFiltros(reorders),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['filtros'] }),
  });
}