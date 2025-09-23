import { describe, it, expect } from 'vitest';
import { buildBasePath } from './basePath';

describe('buildBasePath', () => {
    describe('Valid inputs', () => {
        it('should build base path for valid identifier', () => {
            const result = buildBasePath('INIT-123');
            expect(result).toBe('initiative.INIT-123');
        });

        it('should handle alphanumeric identifiers', () => {
            const result = buildBasePath('ABC123');
            expect(result).toBe('initiative.ABC123');
        });

        it('should handle identifiers with special characters', () => {
            const result = buildBasePath('TASK-SPECIAL_123');
            expect(result).toBe('initiative.TASK-SPECIAL_123');
        });

        it('should handle identifiers with dots', () => {
            const result = buildBasePath('INIT.123.456');
            expect(result).toBe('initiative.INIT.123.456');
        });

        it('should handle single character identifier', () => {
            const result = buildBasePath('A');
            expect(result).toBe('initiative.A');
        });

        it('should handle numeric string identifier', () => {
            const result = buildBasePath('123');
            expect(result).toBe('initiative.123');
        });

        it('should accept task identifier', () => {
            const result = buildBasePath('INIT-123', 'TASK-123');
            expect(result).toBe('initiative.INIT-123.tasks.TASK-123');
        });
    });

    describe('Invalid inputs', () => {
        it('should return empty string for empty identifier', () => {
            const result = buildBasePath('');
            expect(result).toBe('');
        });

        it('should return empty string for null identifier', () => {
            const result = buildBasePath(null as any);
            expect(result).toBe('');
        });

        it('should return empty string for undefined identifier', () => {
            const result = buildBasePath(undefined as any);
            expect(result).toBe('');
        });

        it('should return empty string for non-string identifier (number)', () => {
            const result = buildBasePath(123 as any);
            expect(result).toBe('');
        });

        it('should return empty string for non-string identifier (object)', () => {
            const result = buildBasePath({ id: 'test' } as any);
            expect(result).toBe('');
        });

        it('should return empty string for non-string identifier (array)', () => {
            const result = buildBasePath(['test'] as any);
            expect(result).toBe('');
        });

        it('should return empty string for non-string identifier (boolean)', () => {
            const result = buildBasePath(true as any);
            expect(result).toBe('');
        });
    });

    describe('Edge cases', () => {
        it('should handle identifier with only spaces', () => {
            const result = buildBasePath('   ');
            expect(result).toBe('initiative.   ');
        });

        it('should handle identifier with leading/trailing spaces', () => {
            const result = buildBasePath(' INIT-123 ');
            expect(result).toBe('initiative. INIT-123 ');
        });

        it('should handle very long identifier', () => {
            const longIdentifier = 'A'.repeat(1000);
            const result = buildBasePath(longIdentifier);
            expect(result).toBe(`initiative.${longIdentifier}`);
        });

        it('should handle identifier with newlines', () => {
            const result = buildBasePath('INIT\n123');
            expect(result).toBe('initiative.INIT\n123');
        });

        it('should handle identifier with tabs', () => {
            const result = buildBasePath('INIT\t123');
            expect(result).toBe('initiative.INIT\t123');
        });
    });
});