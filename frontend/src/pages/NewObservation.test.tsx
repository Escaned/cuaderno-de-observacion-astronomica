import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { NewObservation } from './NewObservation';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
if (typeof globalThis !== 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage });
}

const mockFiltros = [
  { id: 1, nombre: 'L', descripcion: 'Luminancia', onda_central_nm: null, orden: 1, activo: true },
  { id: 2, nombre: 'Ha', descripcion: 'H-alpha', onda_central_nm: 656.3, orden: 2, activo: true },
];

const mockObservacion = {
  id: 1,
  objeto: 'M42',
  fecha_hora_utc: '2026-10-10T22:00:00Z',
  filtro_id: 1,
  fwhm: 2.5,
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

vi.mock('../hooks/useObservatorioActivo', () => ({
  useObservatorioActivo: () => ({
    observatorios: [],
    activo: null,
    isLoading: false,
    setActivoId: vi.fn(),
  }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('NewObservation', () => {
  beforeEach(() => {
    mockLocalStorage.clear.mockClear();
  });

  it('renders without crashing', () => {
    renderWithProviders(<NewObservation />);
    expect(screen.getByText('Nueva Observación')).toBeInTheDocument();
  });
});