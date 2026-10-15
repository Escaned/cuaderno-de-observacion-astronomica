import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getObservatorio, updateObservatorio, uploadLogo, deleteLogo } from '../services/api';

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

export function useUploadLogo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadLogo(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observatorio'] }),
  });
}

export function useDeleteLogo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteLogo(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['observatorio'] }),
  });
}