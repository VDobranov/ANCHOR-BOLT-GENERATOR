/**
 * Тесты для config.js
 */

import { APP_CONFIG } from '../core/config.js';

describe('config.js', () => {
    describe('APP_CONFIG', () => {
        test('должен быть заморожен (Object.freeze)', () => {
            expect(Object.isFrozen(APP_CONFIG)).toBe(true);
        });

        test('должен содержать PYODIDE_VERSION', () => {
            expect(APP_CONFIG.PYODIDE_VERSION).toBe('0.26.0');
        });

        test('должен содержать PYODIDE_URL', () => {
            expect(APP_CONFIG.PYODIDE_URL).toBe(
                'https://cdn.jsdelivr.net/pyodide/dev/full/pyodide.js'
            );
        });

        test('должен содержать THREE_JS_URL', () => {
            expect(APP_CONFIG.THREE_JS_URL).toBe(
                'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
            );
        });

        test('должен содержать IFCOPENSHELL_WHEEL_URL', () => {
            expect(APP_CONFIG.IFCOPENSHELL_WHEEL_URL).toContain('ifcopenshell');
            expect(APP_CONFIG.IFCOPENSHELL_WHEEL_URL).toContain('.whl');
        });

        test('должен содержать PYTHON_MODULES массив', () => {
            expect(Array.isArray(APP_CONFIG.PYTHON_MODULES)).toBe(true);
            expect(APP_CONFIG.PYTHON_MODULES.length).toBeGreaterThan(0);
            expect(APP_CONFIG.PYTHON_MODULES).toContain('python/main.py');
        });

        test('должен содержать PYODIDE_LOAD_TIMEOUT', () => {
            expect(APP_CONFIG.PYODIDE_LOAD_TIMEOUT).toBe(30000);
        });

        test('должен содержать STATUS_DURATION', () => {
            expect(APP_CONFIG.STATUS_DURATION).toEqual({
                success: 3000,
                error: 5000,
                info: 0
            });
        });

        test('должен содержать DEFAULT_BOLT_PARAMS', () => {
            expect(APP_CONFIG.DEFAULT_BOLT_PARAMS).toEqual({
                bolt_type: '1.1',
                diameter: 20,
                length: 800,
                material: '09Г2С'
            });
        });

        test('должен содержать COMPONENT_COLORS', () => {
            expect(APP_CONFIG.COMPONENT_COLORS).toEqual({
                STUD: 0x8b8b8b,
                WASHER: 0xa9a9a9,
                NUT: 0x696969,
                ANCHORBOLT: 0x4f4f4f
            });
        });

        test('не должен позволять изменять свойства', () => {
            // В строгом режиме это бросит ошибку
            'use strict';
            expect(() => {
                APP_CONFIG.NEW_PROPERTY = 'test';
            }).toThrow();
        });

        test('должен позволять изменять вложенные объекты (Object.freeze не глубокий)', () => {
            // Object.freeze не глубокий - вложенные объекты можно изменять
            // Это известное ограничение JavaScript
            expect(() => {
                APP_CONFIG.STATUS_DURATION.newStatus = 1000;
            }).not.toThrow();
        });
    });
});
