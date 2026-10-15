import { describe, it, expect } from 'vitest';
import { formatDate, formatTime, formatDateTime, toISODate, formatUTCtoMadrid } from './date';

describe('formatUTCtoMadrid', () => {
  it('formats ISO date to Madrid time', () => {
    // 2026-10-09T22:00:00Z in Madrid (CEST, UTC+2) = 2026-10-10 00:00
    expect(formatUTCtoMadrid('2026-10-09T22:00:00Z')).toBe('10/10/2026 00:00');
  });
});

describe('formatDate', () => {
  it('formats ISO date to dd/MM/yyyy (Madrid timezone)', () => {
    // 2026-10-09T22:00:00Z in Madrid = 2026-10-10
    expect(formatDate('2026-10-09T22:00:00Z')).toBe('10/10/2026');
  });
});

describe('formatTime', () => {
  it('formats ISO date to HH:mm (Madrid timezone)', () => {
    // 2026-10-09T22:30:00Z in Madrid = 00:30
    expect(formatTime('2026-10-09T22:30:00Z')).toBe('00:30');
  });
});

describe('formatDateTime', () => {
  it('formats ISO date to dd/MM/yyyy HH:mm (Madrid timezone)', () => {
    // 2026-10-09T22:30:00Z in Madrid = 10/10/2026 00:30
    expect(formatDateTime('2026-10-09T22:30:00Z')).toBe('10/10/2026 00:30');
  });
});

describe('toISODate', () => {
  it('converts Date to ISO string', () => {
    const d = new Date(2026, 9, 10, 0, 0, 0); // Oct 10, 2026 00:00 local
    expect(toISODate(d)).toContain('2026-10-10');
  });
});