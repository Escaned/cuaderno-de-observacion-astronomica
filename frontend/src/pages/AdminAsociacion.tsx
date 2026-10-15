import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  useObservatorio,
  useUpdateObservatorio,
  useUploadLogo,
  useDeleteLogo,
} from '../hooks/useObservatorio';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Loader } from '../components/ui/Loader';

const MAX_LOGO_BYTES = 2 * 1024 * 1024;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png'];

function errorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

export function AdminAsociacion() {
  const { data: observatorio, isLoading } = useObservatorio();
  const updateMutation = useUpdateObservatorio();
  const uploadMutation = useUploadLogo();
  const deleteMutation = useDeleteLogo();

  const [nombre, setNombre] = useState('');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (observatorio) setNombre(observatorio.nombre);
  }, [observatorio]);

  if (isLoading) return <Loader />;

  const logoUrl = observatorio?.logo_path ? `/imagenes/${observatorio.logo_path}` : null;

  const handleSaveName = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaved(false);

    if (!nombre.trim()) {
      setError('El nombre de la asociación no puede estar vacío.');
      return;
    }

    updateMutation.mutate(
      { nombre: nombre.trim() },
      {
        onSuccess: () => {
          setSaved(true);
          setTimeout(() => setSaved(false), 2500);
        },
        onError: err => setError(errorMessage(err, 'No se pudo guardar el nombre.')),
      },
    );
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError('Formato no soportado. Usá JPG o PNG.');
      resetFileInput();
      return;
    }

    if (file.size > MAX_LOGO_BYTES) {
      setError('El logo no puede superar los 2 MB.');
      resetFileInput();
      return;
    }

    uploadMutation.mutate(file, {
      onSuccess: () => resetFileInput(),
      onError: err => {
        setError(errorMessage(err, 'No se pudo subir el logo.'));
        resetFileInput();
      },
    });
  };

  const resetFileInput = () => {
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleDeleteLogo = () => {
    setError(null);
    if (confirm('¿Quitar el logo de la asociación?')) {
      deleteMutation.mutate(undefined, {
        onError: err => setError(errorMessage(err, 'No se pudo quitar el logo.')),
      });
    }
  };

  const isBusy = uploadMutation.isPending || deleteMutation.isPending;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Asociación astronómica</h1>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-red-50 dark:bg-red-900/30 text-red-700 dark:text-red-300 text-sm">
          {error}
        </div>
      )}

      <div className="card mb-6">
        <h2 className="text-lg font-semibold mb-4">Nombre</h2>
        <form onSubmit={handleSaveName} className="space-y-4 max-w-md">
          <Input
            label="Nombre de la asociación astronómica"
            value={nombre}
            onChange={e => setNombre(e.target.value)}
            maxLength={100}
            placeholder="Ej. Asociación Astronómica Riguel"
          />
          <div className="flex items-center gap-3">
            <Button type="submit" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'Guardando...' : 'Guardar'}
            </Button>
            {saved && <span className="text-sm text-green-600 dark:text-green-400">Guardado ✓</span>}
          </div>
        </form>
        <p className="mt-3 text-xs text-gray-500 dark:text-gray-400">
          Este nombre aparece en la barra lateral y en las cabeceras de los informes en PDF.
        </p>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Logo</h2>

        <div className="flex flex-col sm:flex-row gap-6 items-start">
          <div className="w-40 h-40 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex items-center justify-center overflow-hidden shrink-0">
            {logoUrl ? (
              <img src={logoUrl} alt="Logo de la asociación" className="max-w-full max-h-full object-contain" />
            ) : (
              <span className="text-xs text-gray-400 text-center px-3">Sin logo</span>
            )}
          </div>

          <div className="flex-1 space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300">
                Elegir archivo (JPG o PNG, máx. 2 MB)
              </label>
              <input
                ref={fileRef}
                type="file"
                accept="image/jpeg,image/png"
                onChange={handleFileChange}
                disabled={isBusy}
                className="block w-full text-sm text-gray-600 dark:text-gray-400 file:mr-3 file:px-4 file:py-2 file:rounded-lg file:border-0 file:bg-space-600 file:text-white hover:file:bg-space-700 file:cursor-pointer disabled:opacity-50"
              />
            </div>

            <div className="flex items-center gap-3">
              {uploadMutation.isPending && (
                <span className="text-sm text-gray-500 dark:text-gray-400">Subiendo...</span>
              )}
              {logoUrl && (
                <Button variant="danger" onClick={handleDeleteLogo} disabled={isBusy}>
                  Quitar logo
                </Button>
              )}
            </div>

            <p className="text-xs text-gray-500 dark:text-gray-400">
              El logo aparece en la barra lateral, en la pestaña del navegador y en las cabeceras de los informes en PDF.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
