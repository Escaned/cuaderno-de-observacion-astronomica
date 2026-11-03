import { describe, it, expect } from 'vitest';
import { hexToRgba } from './color';

describe('hexToRgba', () => {
  it('converts a six-digit hex color', () => {
    expect(hexToRgba('#4d48e2', 0.5)).toBe('rgba(77, 72, 226, 0.5)');
  });

  it('expands a three-digit hex color', () => {
    expect(hexToRgba('#0f0', 0.2)).toBe('rgba(0, 255, 0, 0.2)');
  });

  it('falls back to the app color on invalid input', () => {
    expect(hexToRgba('no-es-un-color', 0.1)).toBe('rgba(77, 72, 226, 0.1)');
  });
});
