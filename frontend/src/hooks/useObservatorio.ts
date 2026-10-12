import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getObservatorio, updateObservatorio } from '../services/api';

export function useObservatorio() {
  return useQuery({
    queryKey: ['observatorio'],
    queryFn: getObservatorio,
  });
}

export function useUpdateObservatorio() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateObservatorio(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observatorio'] }),
  });
}