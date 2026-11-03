import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AdminAsociacion } from './AdminAsociacion';

const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
if (typeof globalThis !== 'undefined') {
  Object.defineProperty(globalThis, 'localStorage', { value: mockLocalStorage });
}

const mockAsociacion = {
  id: 1,
  nombre: 'TBVG',
  logo_path: 'logo.jpg',
};

const mockObservatorio = {
  id: 1,
  nombre: 'Riguel',
  latitud: 40.4168,
  longitud: -3.7038,
  altitud_msnm: 650,
  zona_horaria: 'Europe/Madrid',
  color: '#4d48e2',
  es_predeterminado: true,
};

vi.mock('../hooks/useAsociacion', () => ({
  useAsociacion: () => ({ data: mockAsociacion, isLoading: false }),
  useUpdateAsociacion: () => ({ mutate: vi.fn(), isPending: false }),
  useUploadLogo: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteLogo: () => ({ mutate: vi.fn(), isPending: false }),
}));

vi.mock('../hooks/useObservatorios', () => ({
  useObservatorios: () => ({ data: [mockObservatorio], isLoading: false }),
  useCreateObservatorio: () => ({ mutate: vi.fn(), isPending: false }),
  useUpdateObservatorio: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteObservatorio: () => ({ mutate: vi.fn(), isPending: false }),
  useSetObservatorioPredeterminado: () => ({ mutate: vi.fn(), isPending: false }),
}));

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>,
  );
}

describe('AdminAsociacion', () => {
  beforeEach(() => {
    mockLocalStorage.clear.mockClear();
  });

  it('renders without crashing', () => {
    renderWithProviders(<AdminAsociacion />);
    expect(screen.getByText('Asociación astronómica')).toBeInTheDocument();
  });

  it('shows the current association name in the input', () => {
    renderWithProviders(<AdminAsociacion />);
    expect(screen.getByLabelText(/Nombre de la asociación astronómica/i)).toHaveValue('TBVG');
  });

  it('shows the current logo preview', () => {
    renderWithProviders(<AdminAsociacion />);
    const logo = screen.getByAltText('Logo de la asociación');
    expect(logo).toHaveAttribute('src', '/imagenes/logo.jpg');
  });

  it('has a file input restricted to JPG and PNG', () => {
    renderWithProviders(<AdminAsociacion />);
    const fileInput = document.querySelector('input[type="file"]');
    expect(fileInput).toBeInTheDocument();
    expect(fileInput).toHaveAttribute('accept', 'image/jpeg,image/png');
  });

  it('lists the observatories with their coordinates and altitude', () => {
    renderWithProviders(<AdminAsociacion />);
    expect(screen.getByText('Riguel')).toBeInTheDocument();
    expect(screen.getByText(/40\.4168°, -3\.7038°/)).toBeInTheDocument();
    expect(screen.getByText(/650 m s\. n\. m\./)).toBeInTheDocument();
    expect(screen.getByText('Predeterminado')).toBeInTheDocument();
  });

  it('offers a button to add another observatory', () => {
    renderWithProviders(<AdminAsociacion />);
    expect(screen.getByRole('button', { name: /Agregar observatorio/i })).toBeInTheDocument();
  });
});
