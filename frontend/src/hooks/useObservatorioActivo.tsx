import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import { useObservatorios } from './useObservatorios';
import type { Observatorio } from '../types';

const STORAGE_KEY = 'observatorio-activo-id';

interface ObservatorioActivoContexto {
  observatorios: Observatorio[];
  activo: Observatorio | null;
  isLoading: boolean;
  setActivoId: (id: number) => void;
}

const ObservatorioActivoContext = createContext<ObservatorioActivoContexto | undefined>(undefined);

function leerGuardado(): number | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const id = Number(raw);
    return Number.isFinite(id) ? id : null;
  } catch {
    return null;
  }
}

export function ObservatorioActivoProvider({ children }: { children: ReactNode }) {
  const { data: observatorios = [], isLoading } = useObservatorios();
  const [activoId, setActivoIdState] = useState<number | null>(leerGuardado);

  // Si el guardado ya no existe, se cae al predeterminado. Cuando la lista
  // llega por primera vez y no habia nada guardado, tambien se elige uno.
  useEffect(() => {
    if (observatorios.length === 0) return;

    const existe = observatorios.some(o => o.id === activoId);
    if (existe) return;

    const predeterminado =
      observatorios.find(o => o.es_predeterminado) ?? observatorios[0];
    setActivoIdState(predeterminado.id);
    try {
      localStorage.setItem(STORAGE_KEY, String(predeterminado.id));
    } catch {
      /* localStorage puede no estar disponible */
    }
  }, [observatorios, activoId]);

  const setActivoId = useCallback((id: number) => {
    setActivoIdState(id);
    try {
      localStorage.setItem(STORAGE_KEY, String(id));
    } catch {
      /* ignore */
    }
  }, []);

  const activo = useMemo(
    () => observatorios.find(o => o.id === activoId) ?? null,
    [observatorios, activoId],
  );

  const value = useMemo(
    () => ({ observatorios, activo, isLoading, setActivoId }),
    [observatorios, activo, isLoading, setActivoId],
  );

  return (
    <ObservatorioActivoContext.Provider value={value}>
      {children}
    </ObservatorioActivoContext.Provider>
  );
}

export function useObservatorioActivo(): ObservatorioActivoContexto {
  const contexto = useContext(ObservatorioActivoContext);
  if (!contexto) {
    throw new Error('useObservatorioActivo debe usarse dentro de ObservatorioActivoProvider');
  }
  return contexto;
}
