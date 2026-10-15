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

const mockObservatorio = {
  id: 1,
  nombre: 'TBVG',
  latitud: 40.4168,
  longitud: -3.7038,
  altitud_msnm: 650,
  zona_horaria: 'Europe/Madrid',
  logo_path: 'logo.jpg',
};

vi.mock('../hooks/useObservatorio', () => ({
  useObservatorio: () => ({ data: mockObservatorio, isLoading: false }),
  useUpdateObservatorio: () => ({ mutate: vi.fn(), isPending: false }),
  useUploadLogo: () => ({ mutate: vi.fn(), isPending: false }),
  useDeleteLogo: () => ({ mutate: vi.fn(), isPending: false }),
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
});
