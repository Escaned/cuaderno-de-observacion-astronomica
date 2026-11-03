import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAsociacion, updateAsociacion, uploadLogo, deleteLogo } from '../services/api';

export function useAsociacion() {
  return useQuery({
    queryKey: ['asociacion'],
    queryFn: getAsociacion,
  });
}

export function useUpdateAsociacion() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) => updateAsociacion(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['asociacion'] }),
  });
}

export function useUploadLogo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadLogo(file),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['asociacion'] }),
  });
}

export function useDeleteLogo() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => deleteLogo(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['asociacion'] }),
  });
}
