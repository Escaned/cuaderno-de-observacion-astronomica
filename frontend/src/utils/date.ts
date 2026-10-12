import { format, parseISO } from 'date-fns';
import { es } from 'date-fns/locale';
import { formatInTimeZone } from 'date-fns-tz';

const MADRID_TZ = 'Europe/Madrid';

export function formatUTCtoMadrid(dateStr: string): string {
  return formatInTimeZone(parseISO(dateStr), MADRID_TZ, 'dd/MM/yyyy HH:mm', { locale: es });
}

export function formatDate(dateStr: string): string {
  return format(parseISO(dateStr), 'dd/MM/yyyy', { locale: es });
}

export function formatTime(dateStr: string): string {
  return format(parseISO(dateStr), 'HH:mm');
}

export function formatDateTime(dateStr: string): string {
  return format(parseISO(dateStr), 'dd/MM/yyyy HH:mm', { locale: es });
}

export function toISODate(date: Date): string {
  return format(date, "yyyy-MM-dd'T'HH:mm:ss");
}

export function dateRangeToParams(fechaDesde?: Date, fechaHasta?: Date) {
  return {
    fecha_desde: fechaDesde ? toISODate(fechaDesde) : undefined,
    fecha_hasta: fechaHasta ? toISODate(fechaHasta) : undefined,
  };
}