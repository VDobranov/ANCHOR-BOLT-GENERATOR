/**
 * Тесты для constants.js
 */

import { BOLT_TYPES, MATERIALS, AVAILABLE_DIAMETERS, STATUS_TYPES } from '../core/constants.js';

describe('constants', () => {
    describe('BOLT_TYPES', () => {
        test('должен содержать все типы болтов', () => {
            expect(BOLT_TYPES['1.1']).toBeDefined();
            expect(BOLT_TYPES['1.2']).toBeDefined();
            expect(BOLT_TYPES['2.1']).toBeDefined();
            expect(BOLT_TYPES['5']).toBeDefined();
        });

        test('должен быть заморожен (Object.freeze)', () => {
            expect(Object.isFrozen(BOLT_TYPES)).toBe(true);
        });
    });

    describe('MATERIALS', () => {
        test('должен содержать все материалы', () => {
            expect(MATERIALS['09Г2С']).toBeDefined();
            expect(MATERIALS['ВСт3пс2']).toBeDefined();
            expect(MATERIALS['10Г2']).toBeDefined();
        });

        test('должен быть заморожен (Object.freeze)', () => {
            expect(Object.isFrozen(MATERIALS)).toBe(true);
        });
    });

    describe('AVAILABLE_DIAMETERS', () => {
        test('должен содержать правильные диаметры', () => {
            expect(AVAILABLE_DIAMETERS).toEqual([12, 16, 20, 24, 30, 36, 42, 48]);
        });

        test('должен быть заморожен (Object.freeze)', () => {
            expect(Object.isFrozen(AVAILABLE_DIAMETERS)).toBe(true);
        });
    });

    describe('STATUS_TYPES', () => {
        test('должен содержать все типы статусов', () => {
            expect(STATUS_TYPES.SUCCESS).toBe('success');
            expect(STATUS_TYPES.ERROR).toBe('error');
            expect(STATUS_TYPES.INFO).toBe('info');
        });

        test('должен быть заморожен (Object.freeze)', () => {
            expect(Object.isFrozen(STATUS_TYPES)).toBe(true);
        });
    });
});
