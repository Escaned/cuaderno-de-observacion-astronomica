import { describe, it, expect } from 'vitest';
import { formatFwhm, formatDuration, formatNumber, formatTemperature } from './format';

describe('formatFwhm', () => {
  it('formats FWHM with 1 decimal and arcsec symbol', () => {
    expect(formatFwhm(2.5)).toBe('2.5"');
  });
  it('formats FWHM 1.0', () => {
    expect(formatFwhm(1.0)).toBe('1.0"');
  });
  it('formats FWHM 3.2', () => {
    expect(formatFwhm(3.2)).toBe('3.2"');
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