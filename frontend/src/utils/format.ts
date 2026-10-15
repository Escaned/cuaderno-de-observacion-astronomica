export function formatFwhm(fwhm: number): string {
  return `${fwhm.toFixed(1)}"`;
}

export function formatDuration(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  if (hours > 0) {
    return `${hours}h ${minutes.toString().padStart(2, '0')}m`;
  }
  return `${minutes}m`;
}

export function formatNumber(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return '—';
  return value.toFixed(decimals);
}

export function formatTemperature(temp: number | null | undefined): string {
  if (temp === null || temp === undefined) return '—';
  return `${temp.toFixed(1)}°C`;
}