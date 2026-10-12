import { useState, useEffect } from 'react';
import { Button } from '../ui/Button';
import { NightHeader } from './NightHeader';
import { CaptureSessions } from './CaptureSessions';
import { CalibrationFrames } from './CalibrationFrames';
import type { ObservacionCreate } from '../../types';

interface WizardLayoutProps {
  initialData?: Partial<ObservacionCreate>;
  filtros: { id: number; nombre: string }[];
  onSubmit: (data: ObservacionCreate) => void;
  onCancel: () => void;
  isSubmitting?: boolean;
}

const STEPS = ['Datos de la Noche', 'Sesiones de Captura', 'Calibraciones'];

export function WizardLayout({ initialData, filtros, onSubmit, onCancel, isSubmitting }: WizardLayoutProps) {
  const [step, setStep] = useState(0);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formData, setFormData] = useState<Record<string, unknown>>({
    objeto: initialData?.objeto ?? '',
    fecha_hora_utc: initialData?.fecha_hora_utc ?? '',
    filtro_id: initialData?.filtro_id ?? '',
    seeing: initialData?.seeing ?? 3,
    temperatura: initialData?.temperatura ?? null,
    humedad: initialData?.humedad ?? null,
    viento_kph: initialData?.viento_kph ?? null,
    direccion_viento: initialData?.direccion_viento ?? null,
    descripcion: initialData?.descripcion ?? null,
    imagenes: initialData?.imagenes ?? null,
    sesiones_captura: initialData?.sesiones_captura ?? [],
  });

  useEffect(() => {
    const saved = localStorage.getItem('wizard-draft');
    if (saved && !initialData) {
      try {
        setFormData(JSON.parse(saved));
      } catch { /* ignore */ }
    }
  }, [initialData]);

  useEffect(() => {
    if (!initialData) {
      localStorage.setItem('wizard-draft', JSON.stringify(formData));
    }
  }, [formData, initialData]);

  const handleChange = (field: string, value: unknown) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
  };

  const validateStep = (s: number): boolean => {
    const newErrors: Record<string, string> = {};
    if (s === 0) {
      if (!String(formData.objeto || '').trim()) newErrors.objeto = 'El objeto es obligatorio';
      if (!formData.fecha_hora_utc) newErrors.fecha_hora_utc = 'La fecha es obligatoria';
      if (!formData.seeing || (formData.seeing as number) < 1 || (formData.seeing as number) > 5) {
        newErrors.seeing = 'Seeing debe ser 1-5';
      }
    }
    if (s === 1) {
      const sesiones = formData.sesiones_captura as unknown[];
      if (!sesiones.length) {
        newErrors.sesiones = 'Añade al menos una sesión de captura';
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const nextStep = () => {
    if (validateStep(step)) setStep(s => Math.min(s + 1, STEPS.length - 1));
  };

  const prevStep = () => setStep(s => Math.max(s - 1, 0));

  const handleSubmit = () => {
    if (!validateStep(0) || !validateStep(1)) {
      setStep(0);
      return;
    }
    const data: ObservacionCreate = {
      objeto: formData.objeto as string,
      fecha_hora_utc: formData.fecha_hora_utc as string,
      filtro_id: (formData.filtro_id as number) || null,
      seeing: formData.seeing as number,
      temperatura: (formData.temperatura as number) ?? null,
      humedad: (formData.humedad as number) ?? null,
      viento_kph: (formData.viento_kph as number) ?? null,
      direccion_viento: (formData.direccion_viento as string) || null,
      descripcion: (formData.descripcion as string) || null,
      imagenes: (formData.imagenes as string) || null,
      sesiones_captura: formData.sesiones_captura as ObservacionCreate['sesiones_captura'],
    };
    localStorage.removeItem('wizard-draft');
    onSubmit(data);
  };

  return (
    <div className="max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((label, i) => (
          <div key={i} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                i === step
                  ? 'bg-space-600 text-white'
                  : i < step
                  ? 'bg-space-200 dark:bg-space-800 text-space-700 dark:text-space-300'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
              }`}
            >
              {i + 1}
            </div>
            <span className={`ml-2 text-sm ${i === step ? 'font-medium' : 'text-gray-500 dark:text-gray-400'}`}>
              {label}
            </span>
            {i < STEPS.length - 1 && <div className="w-8 md:w-16 h-px bg-gray-300 dark:bg-gray-600 mx-2" />}
          </div>
        ))}
      </div>

      <div className="card">
        {step === 0 && (
          <NightHeader
            objeto={String(formData.objeto || '')}
            fecha_hora_utc={String(formData.fecha_hora_utc || '')}
            filtro_id={(formData.filtro_id as number) || ''}
            seeing={Number(formData.seeing) || 3}
            temperatura={formData.temperatura?.toString() ?? ''}
            humedad={formData.humedad?.toString() ?? ''}
            viento_kph={formData.viento_kph?.toString() ?? ''}
            direccion_viento={String(formData.direccion_viento || '')}
            descripcion={String(formData.descripcion || '')}
            filtros={filtros}
            errors={errors}
            onChange={handleChange}
          />
        )}
        {step === 1 && (
          <CaptureSessions
            sesiones={(formData.sesiones_captura as import('../../types').SesionCapturaCreate[]) ?? []}
            filtros={filtros}
            errors={errors}
            onChange={sesiones => handleChange('sesiones_captura', sesiones)}
          />
        )}
        {step === 2 && (
          <CalibrationFrames
            sesiones={(formData.sesiones_captura as import('../../types').SesionCapturaCreate[]) ?? []}
            filtros={filtros}
            onChange={sesiones => handleChange('sesiones_captura', sesiones)}
          />
        )}
      </div>

      <div className="flex justify-between mt-6">
        <div>
          {step > 0 && (
            <Button type="button" variant="secondary" onClick={prevStep}>
              ← Anterior
            </Button>
          )}
        </div>
        <div className="flex gap-2">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancelar
          </Button>
          {step < STEPS.length - 1 ? (
            <Button type="button" onClick={nextStep}>
              Siguiente →
            </Button>
          ) : (
            <Button type="button" onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Guardando...' : 'Guardar observación'}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}