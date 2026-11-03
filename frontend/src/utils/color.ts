/** Convierte un color #rrggbb en rgba() para poder darle transparencia. */
export function hexToRgba(hex: string, alpha: number): string {
  const limpio = hex.replace('#', '').trim();
  const completo =
    limpio.length === 3
      ? limpio
          .split('')
          .map(c => c + c)
          .join('')
      : limpio;

  if (!/^[0-9a-fA-F]{6}$/.test(completo)) {
    return `rgba(77, 72, 226, ${alpha})`;
  }

  const r = parseInt(completo.slice(0, 2), 16);
  const g = parseInt(completo.slice(2, 4), 16);
  const b = parseInt(completo.slice(4, 6), 16);
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
