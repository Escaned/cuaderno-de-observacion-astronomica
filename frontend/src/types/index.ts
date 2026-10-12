export type TipoCalibracion = 'dark' | 'flat' | 'bias' | 'darkflat';

export interface Observatorio {
  id: number;
  nombre: string;
  latitud: number;
  longitud: number;
  altitud_msnm: number | null;
  zona_horaria: string;
}

export interface Filtro {
  id: number;
  nombre: string;
  descripcion: string | null;
  onda_central_nm: number | null;
  orden: number;
  activo: boolean;
}

export interface Calibracion {
  id: number;
  sesion_captura_id: number;
  tipo: TipoCalibracion;
  count: number;
  tiempo_exposicion_seg: number | null;
  temperatura: number | null;
  filtro_id: number | null;
  notas: string | null;
}

export interface SesionCaptura {
  id: number;
  observacion_id: number;
  filtro_id: number;
  tiempo_exposicion_seg: number;
  num_subs: number;
  binning: number;
  temp_sensor: number | null;
  calibraciones: Calibracion[];
}

export interface Observacion {
  id: number;
  objeto: string;
  fecha_hora_utc: string;
  filtro_id: number | null;
  seeing: number;
  temperatura: number | null;
  humedad: number | null;
  viento_kph: number | null;
  direccion_viento: string | null;
  descripcion: string | null;
  imagenes: string | null;
  creado_en: string;
  actualizado_en: string;
  sesiones_captura: SesionCaptura[];
}

export interface ObservacionListItem {
  id: number;
  objeto: string;
  fecha_hora_utc: string;
  filtro_id: number | null;
  seeing: number;
  creado_en: string;
}

export interface ObservacionCreate {
  objeto: string;
  fecha_hora_utc: string;
  filtro_id?: number | null;
  seeing: number;
  temperatura?: number | null;
  humedad?: number | null;
  viento_kph?: number | null;
  direccion_viento?: string | null;
  descripcion?: string | null;
  imagenes?: string | null;
  sesiones_captura: SesionCapturaCreate[];
}

export interface SesionCapturaCreate {
  filtro_id: number;
  tiempo_exposicion_seg: number;
  num_subs: number;
  binning: number;
  temp_sensor?: number | null;
  calibraciones: CalibracionCreate[];
}

export interface CalibracionCreate {
  tipo: TipoCalibracion;
  count: number;
  tiempo_exposicion_seg?: number | null;
  temperatura?: number | null;
  filtro_id?: number | null;
  notas?: string | null;
}