import { useMutation } from '@tanstack/react-query';
import { exportCSV, exportPDFNoche, exportPDFCampana } from '../services/api';

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function useExportCSV() {
  return useMutation({
    mutationFn: (params: { tabla: string; fecha_desde?: string; fecha_hasta?: string; filtro_id?: number }) =>
      exportCSV(params).then(blob => {
        const filename = `export_${params.tabla}_${new Date().toISOString().slice(0, 10)}.zip`;
        downloadBlob(blob, filename);
      }),
  });
}

export function useExportPDFNoche() {
  return useMutation({
    mutationFn: (fecha: string) =>
      exportPDFNoche(fecha).then(blob => {
        downloadBlob(blob, `informe_noche_${fecha}.pdf`);
      }),
  });
}

export function useExportPDFCampana() {
  return useMutation({
    mutationFn: ({ fechaDesde, fechaHasta }: { fechaDesde: string; fechaHasta: string }) =>
      exportPDFCampana(fechaDesde, fechaHasta).then(blob => {
        downloadBlob(blob, `informe_campana_${fechaDesde}_${fechaHasta}.pdf`);
      }),
  });
}