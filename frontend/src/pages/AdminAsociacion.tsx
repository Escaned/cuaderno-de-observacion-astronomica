import { useEffect, useRef, useState } from 'react';
import axios from 'axios';
import {
  useAsociacion,
  useUpdateAsociacion,
  useUploadLogo,
  useDeleteLogo,
} from '../hooks/useAsociacion';
import {
  useObservatorios,
  useCreateObservatorio,
  useUpdateObservatorio,
  useDeleteObservatorio,
  useSetObservatorioPredeterminado,
} from '../hooks/useObservatorios';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Loader } from '../components/ui/Loader';
import type { Observatorio } from '../types';

const MAX_LOGO_BYTES = 2 * 1024 * 1024;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png'];

const COLORES = ['#4d48e2', '#0f766e', '#b45309', '#be123c', '#7e22ce', '#0369a1', '#4d7c0f'];

const FORM_VACIO = {
  nombre: '',
  latitud: '',
  longitud: '',
  altitud_msnm: '',
  color: COLORES[0],
};

function errorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const detail = (err.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') return detail;
  }
  return fallback;
}

function coordenadas(observatorio: Observatorio): string {
  return `${observatorio.latitud.toFixed(4)}°, ${observatorio.longitud.toFixed(4)}°`;
}

export function AdminAsociacion() {
  const { data: asociacion, isLoading } = useAsociacion();
  const updateMutation = useUpdateAsociacion();
  const uploadMutation = useUploadLogo();
  const deleteMutation = useDeleteLogo();

  const { data: observatorios, isLoading: observatoriosLoading } = useObservatorios();
  const crearObservatorio = useCreateObservatorio();
  const actualizarObservatorio = useUpdateObservatorio();
  const borrarObservatorio = useDeleteObservatorio();
  const marcarPredeterminado = useSetObservatorioPredeterminado();

  const [nombre, setNombre] = useState('');
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const [editingId, setEditingId] = useState<number | 'nuevo' | null>(null);
  const [form, setForm] = useState(FORM_VACIO);

  useEffect(() => {
    if (asociacion) setNombre(asociacion.nombre);
  }, [asociacion]);

  if (isLoading || observatoriosLoading) return <Loader />;

  const logoUrl = asociacion?.logo_path ? `/imagenes/${asociacion.logo_path}` : null;
  const listaObservatorios = observatorios ?? [];

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

  const abrirNuevo = () => {
    setError(null);
    setEditingId('nuevo');
    setForm(FORM_VACIO);
  };

  const abrirEditar = (observatorio: Observatorio) => {
    setError(null);
    setEditingId(observatorio.id);
    setForm({
      nombre: observatorio.nombre,
      latitud: String(observatorio.latitud),
      longitud: String(observatorio.longitud),
      altitud_msnm: observatorio.altitud_msnm != null ? String(observatorio.altitud_msnm) : '',
      color: observatorio.color,
    });
  };

  const cerrarFormulario = () => {
    setEditingId(null);
    setForm(FORM_VACIO);
  };

  const handleGuardarObservatorio = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const nombreObs = form.nombre.trim();
    const latitud = Number(form.latitud);
    const longitud = Number(form.longitud);
    const altitud = form.altitud_msnm.trim() === '' ? null : Number(form.altitud_msnm);

    if (!nombreObs) {
      setError('El nombre del observatorio no puede estar vacío.');
      return;
    }
    if (!Number.isFinite(latitud) || latitud < -90 || latitud > 90) {
      setError('La latitud debe ser un número entre -90 y 90.');
      return;
    }
    if (!Number.isFinite(longitud) || longitud < -180 || longitud > 180) {
      setError('La longitud debe ser un número entre -180 y 180.');
      return;
    }
    if (altitud != null && (!Number.isFinite(altitud) || altitud < -500 || altitud > 9000)) {
      setError('La altitud debe ser un número entre -500 y 9000 metros.');
      return;
    }

    const data = {
      nombre: nombreObs,
      latitud,
      longitud,
      altitud_msnm: altitud,
      color: form.color,
    };

    const onError = (err: unknown) =>
      setError(errorMessage(err, 'No se pudo guardar el observatorio.'));

    if (editingId === 'nuevo') {
      crearObservatorio.mutate(data, { onSuccess: cerrarFormulario, onError });
    } else if (typeof editingId === 'number') {
      actualizarObservatorio.mutate(
        { id: editingId, data },
        { onSuccess: cerrarFormulario, onError },
      );
    }
  };

  const handlePredeterminado = (observatorio: Observatorio) => {
    setError(null);
    marcarPredeterminado.mutate(observatorio.id, {
      onError: err => setError(errorMessage(err, 'No se pudo marcar como predeterminado.')),
    });
  };

  const handleBorrarObservatorio = (observatorio: Observatorio) => {
    setError(null);
    if (!confirm(`¿Eliminar el observatorio "${observatorio.nombre}"?`)) return;
    borrarObservatorio.mutate(observatorio.id, {
      onError: err => setError(errorMessage(err, 'No se pudo eliminar el observatorio.')),
    });
  };

  const isBusy = uploadMutation.isPending || deleteMutation.isPending;
  const guardandoObservatorio =
    crearObservatorio.isPending || actualizarObservatorio.isPending;

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

      <div className="card mb-6">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold">Observatorios</h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              La asociación puede tener varios. El predeterminado es el que aparece
              seleccionado en la pantalla de observaciones.
            </p>
          </div>
          <Button type="button" onClick={abrirNuevo} disabled={editingId === 'nuevo'}>
            + Agregar observatorio
          </Button>
        </div>

        {editingId !== null && (
          <form
            onSubmit={handleGuardarObservatorio}
            className="mb-5 p-4 rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/40"
          >
            <h3 className="text-sm font-semibold mb-3">
              {editingId === 'nuevo' ? 'Nuevo observatorio' : 'Editar observatorio'}
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div className="sm:col-span-2">
                <Input
                  label="Nombre"
                  value={form.nombre}
                  onChange={e => setForm(prev => ({ ...prev, nombre: e.target.value }))}
                  maxLength={100}
                  placeholder="Ej. Observatorio Norte"
                />
              </div>
              <Input
                label="Latitud"
                type="number"
                step="any"
                value={form.latitud}
                onChange={e => setForm(prev => ({ ...prev, latitud: e.target.value }))}
                placeholder="41.6789"
              />
              <Input
                label="Longitud"
                type="number"
                step="any"
                value={form.longitud}
                onChange={e => setForm(prev => ({ ...prev, longitud: e.target.value }))}
                placeholder="-0.4321"
              />
              <Input
                label="Altitud (m s. n. m.)"
                type="number"
                step="any"
                value={form.altitud_msnm}
                onChange={e => setForm(prev => ({ ...prev, altitud_msnm: e.target.value }))}
                placeholder="350"
              />
              <div>
                <label
                  htmlFor="observatorio-color"
                  className="block text-sm font-medium mb-1 text-gray-700 dark:text-gray-300"
                >
                  Color de la pantalla
                </label>
                <div className="flex items-center gap-2">
                  <input
                    id="observatorio-color"
                    type="color"
                    value={form.color}
                    onChange={e => setForm(prev => ({ ...prev, color: e.target.value }))}
                    className="h-10 w-12 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
                  />
                  <div className="flex flex-wrap gap-1">
                    {COLORES.map(color => (
                      <button
                        key={color}
                        type="button"
                        title={`Usar ${color}`}
                        onClick={() => setForm(prev => ({ ...prev, color }))}
                        className={`w-5 h-5 rounded-full border-2 ${
                          form.color.toLowerCase() === color ? 'border-gray-700 dark:border-gray-200' : 'border-transparent'
                        }`}
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 mt-4">
              <Button type="submit" disabled={guardandoObservatorio}>
                {guardandoObservatorio ? 'Guardando...' : 'Guardar observatorio'}
              </Button>
              <Button type="button" variant="secondary" onClick={cerrarFormulario}>
                Cancelar
              </Button>
            </div>
          </form>
        )}

        {listaObservatorios.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400">Todavía no hay observatorios.</p>
        ) : (
          <ul className="space-y-3">
            {listaObservatorios.map(observatorio => (
              <li
                key={observatorio.id}
                className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3 p-3 rounded-lg bg-gray-50 dark:bg-gray-700/50 border-l-4"
                style={{ borderLeftColor: observatorio.color }}
              >
                <div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium">{observatorio.nombre}</span>
                    {observatorio.es_predeterminado && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-space-100 dark:bg-space-900 text-space-700 dark:text-space-300">
                        Predeterminado
                      </span>
                    )}
                    <span
                      className="inline-block w-3 h-3 rounded-full border border-black/10"
                      style={{ backgroundColor: observatorio.color }}
                      aria-label={`Color ${observatorio.color}`}
                    />
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {coordenadas(observatorio)}
                    {observatorio.altitud_msnm != null &&
                      ` — ${Math.round(observatorio.altitud_msnm)} m s. n. m.`}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {!observatorio.es_predeterminado && (
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => handlePredeterminado(observatorio)}
                      disabled={marcarPredeterminado.isPending}
                    >
                      Hacer predeterminado
                    </Button>
                  )}
                  <Button type="button" variant="secondary" onClick={() => abrirEditar(observatorio)}>
                    Editar
                  </Button>
                  <Button
                    type="button"
                    variant="danger"
                    onClick={() => handleBorrarObservatorio(observatorio)}
                    disabled={borrarObservatorio.isPending || listaObservatorios.length <= 1}
                  >
                    Eliminar
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}
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
