import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { NewObservation } from './NewObservation';

const mockFiltros = [
  { id: 1, nombre: 'L', descripcion: 'Luminancia', onda_central_nm: null, orden: 1, activo: true },
  { id: 2, nombre: 'Ha', descripcion: 'H-alpha', onda_central_nm: 656.3, orden: 2, activo: true },
];

const mockObservacion = {
  id: 1,
  objeto: 'M42',
  fecha_hora_utc: '2026-10-10T22:00:00Z',
  filtro_id: 1,
  seeing: 3,
  temperatura: 15.0,
  humedad: 60,
  viento_kph: null,
  direccion_viento: null,
  descripcion: null,
  imagenes: null,
  creado_en: '2026-10-10T22:00:00Z',
  actualizado_en: '2026-10-10T22:00:00Z',
  sesiones_captura: [],
};

vi.mock('../hooks/useFilters', () => ({
  useFilters: () => ({ data: mockFiltros, isLoading: false }),
}));

vi.mock('../hooks/useObservations', () => ({
  useObservacion: () => ({ data: mockObservacion, isLoading: false }),
  useCreateObservacion: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateObservacion: () => ({ mutate: vi.fn(), isPending: false }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/observaciones/new" element={ui} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('NewObservation', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders wizard with step 1', () => {
    renderWithProviders(<NewObservation />);
    expect(screen.getByText('Datos de la Noche')).toBeInTheDocument();
  });

  it('validates required fields on step 1', async () => {
    renderWithProviders(<NewObservation />);
    fireEvent.click(screen.getByText('Siguiente →'));
    await waitFor(() => {
      expect(screen.getByText('El objeto es obligatorio')).toBeInTheDocument();
    });
  });

  it('navigates to step 2 when valid', async () => {
    renderWithProviders(<NewObservation />);
    fireEvent.change(screen.getByPlaceholderText('M42, NGC7000...'), { target: { value: 'M42' } });
    fireEvent.change(screen.getByLabelText('Fecha y hora (UTC) *'), { target: { value: '2026-10-10T22:00' } });
    fireEvent.click(screen.getByText('Siguiente →'));
    await waitFor(() => {
      expect(screen.getByText('Sesiones de Captura')).toBeInTheDocument();
    });
  });
});