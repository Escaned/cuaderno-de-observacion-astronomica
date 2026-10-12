import { describe, it, expect } from 'vitest';
import { formatDate, formatTime, formatDateTime, toISODate } from './date';

describe('formatDate', () => {
  it('formats ISO date to dd/MM/yyyy', () => {
    expect(formatDate('2026-10-09T22:00:00Z')).toBe('09/10/2026');
  });
});

describe('formatTime', () => {
  it('formats ISO date to HH:mm', () => {
    expect(formatTime('2026-10-09T22:30:00Z')).toBe('22:30');
  });
});

describe('formatDateTime', () => {
  it('formats ISO date to dd/MM/yyyy HH:mm', () => {
    expect(formatDateTime('2026-10-09T22:30:00Z')).toBe('09/10/2026 22:30');
  });
});

describe('toISODate', () => {
  it('converts Date to ISO string', () => {
    const d = new Date(2026, 9, 9, 22, 0, 0);
    expect(toISODate(d)).toContain('2026-10-09');
  });
});