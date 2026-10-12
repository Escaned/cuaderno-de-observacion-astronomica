import { describe, it, expect } from 'vitest';
import { formatSeeing, seeingStars, formatDuration, formatNumber, formatTemperature } from './format';

describe('formatSeeing', () => {
  it('returns correct label for seeing 1', () => {
    expect(formatSeeing(1)).toBe('I — Malo');
  });
  it('returns correct label for seeing 5', () => {
    expect(formatSeeing(5)).toBe('V — Excelente');
  });
});

describe('seeingStars', () => {
  it('returns 5 stars for seeing 3', () => {
    expect(seeingStars(3)).toBe('★★★☆☆');
  });
  it('returns all filled stars for seeing 5', () => {
    expect(seeingStars(5)).toBe('★★★★★');
  });
});

describe('formatDuration', () => {
  it('formats hours and minutes', () => {
    expect(formatDuration(3660)).toBe('1h 01m');
  });
  it('formats only minutes', () => {
    expect(formatDuration(300)).toBe('5m');
  });
});

describe('formatNumber', () => {
  it('formats with 1 decimal', () => {
    expect(formatNumber(3.14)).toBe('3.1');
  });
  it('returns dash for null', () => {
    expect(formatNumber(null)).toBe('—');
  });
});

describe('formatTemperature', () => {
  it('formats temperature', () => {
    expect(formatTemperature(-10.5)).toBe('-10.5°C');
  });
  it('returns dash for undefined', () => {
    expect(formatTemperature(undefined)).toBe('—');
  });
});