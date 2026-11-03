import axios from 'axios';
import type {
  Asociacion,
  Observatorio,
  ObservatorioCreate,
  Filtro,
  Observacion,
  ObservacionListItem,
  ObservacionCreate,
} from '../types';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Asociacion
export const getAsociacion = () => api.get<Asociacion>('/asociacion').then(r => r.data);
export const updateAsociacion = (data: Partial<Asociacion>) =>
  api.put<Asociacion>('/asociacion', data).then(r => r.data);
export const uploadLogo = (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  return api
    .post<Asociacion>('/asociacion/logo', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then(r => r.data);
};
export const deleteLogo = () =>
  api.delete<Asociacion>('/asociacion/logo').then(r => r.data);

// Observatorios
export const getObservatorios = () =>
  api.get<Observatorio[]>('/observatorios').then(r => r.data);
export const createObservatorio = (data: ObservatorioCreate) =>
  api.post<Observatorio>('/observatorios', data).then(r => r.data);
export const updateObservatorio = (id: number, data: Partial<ObservatorioCreate>) =>
  api.put<Observatorio>(`/observatorios/${id}`, data).then(r => r.data);
export const deleteObservatorio = (id: number) => api.delete(`/observatorios/${id}`);
export const setObservatorioPredeterminado = (id: number) =>
  api.post<Observatorio>(`/observatorios/${id}/predeterminado`).then(r => r.data);

// Filtros
export const getFiltros = (activoOnly = false) =>
  api.get<Filtro[]>('/filtros', { params: { activo_only: activoOnly } }).then(r => r.data);
export const createFiltro = (data: Partial<Filtro>) =>
  api.post<Filtro>('/filtros', data).then(r => r.data);
export const updateFiltro = (id: number, data: Partial<Filtro>) =>
  api.put<Filtro>(`/filtros/${id}`, data).then(r => r.data);
export const deleteFiltro = (id: number) => api.delete(`/filtros/${id}`);
export const reorderFiltros = (reorders: { filtro_id: number; orden: number }[]) =>
  api.post<Filtro[]>('/filtros/reorder', reorders).then(r => r.data);

// Observaciones
export const getObservacionesStats = () =>
  api.get<{ total_exposicion_seg: number }>('/observaciones/stats').then(r => r.data);
export const getObservaciones = (params?: {
  skip?: number;
  limit?: number;
  filtro_id?: number;
  observatorio_id?: number;
  fecha_desde?: string;
  fecha_hasta?: string;
  objeto?: string;
}) => api.get<ObservacionListItem[]>('/observaciones', { params }).then(r => r.data);
export const getObservacion = (id: number) =>
  api.get<Observacion>(`/observaciones/${id}`).then(r => r.data);
export const createObservacion = (data: ObservacionCreate) =>
  api.post<Observacion>('/observaciones', data).then(r => r.data);
export const updateObservacion = (id: number, data: Partial<ObservacionCreate>) =>
  api.put<Observacion>(`/observaciones/${id}`, data).then(r => r.data);
export const duplicateObservacion = (id: number) =>
  api.post<Observacion>(`/observaciones/${id}/duplicate`).then(r => r.data);
export const deleteObservacion = (id: number) => api.delete(`/observaciones/${id}`);

// Export
export const exportCSV = (params: { tabla: string; fecha_desde?: string; fecha_hasta?: string; filtro_id?: number }) =>
  api.get('/export/csv', { params, responseType: 'blob' }).then(r => r.data);
export const exportPDFNoche = (fecha: string) =>
  api.get('/export/pdf/noche', { params: { fecha }, responseType: 'blob' }).then(r => r.data);
export const exportPDFCampana = (fechaDesde: string, fechaHasta: string) =>
  api.get('/export/pdf/campana', { params: { fecha_desde: fechaDesde, fecha_hasta: fechaHasta }, responseType: 'blob' }).then(r => r.data);

export default api;