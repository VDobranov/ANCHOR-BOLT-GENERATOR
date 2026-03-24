/**
 * Тесты для validationService.js
 */

import { ValidationService } from '../services/validationService.js';

describe('ValidationService', () => {
    describe('validateBoltType', () => {
        test('должен возвращать valid=true для правильного типа болта', () => {
            expect(ValidationService.validateBoltType('1.1')).toEqual({ valid: true, error: null });
            expect(ValidationService.validateBoltType('1.2')).toEqual({ valid: true, error: null });
            expect(ValidationService.validateBoltType('2.1')).toEqual({ valid: true, error: null });
            expect(ValidationService.validateBoltType('5')).toEqual({ valid: true, error: null });
        });

        test('должен возвращать valid=false для пустого типа', () => {
            expect(ValidationService.validateBoltType('')).toEqual({
                valid: false,
                error: 'Тип болта не указан'
            });
            expect(ValidationService.validateBoltType(null)).toEqual({
                valid: false,
                error: 'Тип болта не указан'
            });
            expect(ValidationService.validateBoltType(undefined)).toEqual({
                valid: false,
                error: 'Тип болта не указан'
            });
        });

        test('должен возвращать valid=false для неподдерживаемого типа', () => {
            const result = ValidationService.validateBoltType('9.9');
            expect(result.valid).toBe(false);
            expect(result.error).toContain('Неподдерживаемый тип болта');
        });
    });

    describe('validateDiameter', () => {
        test('должен возвращать valid=true для правильного диаметра', () => {
            expect(ValidationService.validateDiameter(12)).toEqual({ valid: true, error: null });
            expect(ValidationService.validateDiameter(20)).toEqual({ valid: true, error: null });
            expect(ValidationService.validateDiameter(48)).toEqual({ valid: true, error: null });
        });

        test('должен возвращать valid=true для строкового диаметра', () => {
            expect(ValidationService.validateDiameter('12')).toEqual({ valid: true, error: null });
            expect(ValidationService.validateDiameter('20')).toEqual({ valid: true, error: null });
        });

        test('должен возвращать valid=false для пустого диаметра', () => {
            expect(ValidationService.validateDiameter('')).toEqual({
                valid: false,
                error: 'Диаметр не указан'
            });
            expect(ValidationService.validateDiameter(null)).toEqual({
                valid: false,
                error: 'Диаметр не указан'
            });
        });

        test('должен возвращать valid=false для NaN', () => {
            const result = ValidationService.validateDiameter('abc');
            expect(result.valid).toBe(false);
            expect(result.error).toContain('числом');
        });

        test('должен возвращать valid=false для диаметра вне списка', () => {
            const result = ValidationService.validateDiameter(15);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('Диаметр должен быть одним из');
        });
    });

    describe('validateLength', () => {
        test('должен возвращать valid=true для правильной длины', () => {
            expect(ValidationService.validateLength(100)).toEqual({ valid: true, error: null });
            expect(ValidationService.validateLength(800)).toEqual({ valid: true, error: null });
            expect(ValidationService.validateLength(2000)).toEqual({ valid: true, error: null });
        });

        test('должен возвращать valid=false для длины меньше 100', () => {
            const result = ValidationService.validateLength(50);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('от 100 до 2000');
        });

        test('должен возвращать valid=false для длины больше 2000', () => {
            const result = ValidationService.validateLength(3000);
            expect(result.valid).toBe(false);
            expect(result.error).toContain('от 100 до 2000');
        });

        test('должен возвращать valid=false для пустой длины', () => {
            expect(ValidationService.validateLength('')).toEqual({
                valid: false,
                error: 'Длина не указана'
            });
        });

        test('должен возвращать valid=false для длины не числом', () => {
            const result = ValidationService.validateLength('abc');
            expect(result.valid).toBe(false);
            expect(result.error).toContain('числом');
        });
    });

    describe('validateMaterial', () => {
        test('должен возвращать valid=true для правильного материала', () => {
            expect(ValidationService.validateMaterial('09Г2С')).toEqual({
                valid: true,
                error: null
            });
            expect(ValidationService.validateMaterial('ВСт3пс2')).toEqual({
                valid: true,
                error: null
            });
            expect(ValidationService.validateMaterial('10Г2')).toEqual({
                valid: true,
                error: null
            });
        });

        test('должен возвращать valid=false для пустого материала', () => {
            expect(ValidationService.validateMaterial('')).toEqual({
                valid: false,
                error: 'Материал не указан'
            });
            expect(ValidationService.validateMaterial(null)).toEqual({
                valid: false,
                error: 'Материал не указан'
            });
        });

        test('должен возвращать valid=false для неподдерживаемого материала', () => {
            const result = ValidationService.validateMaterial('Ст3');
            expect(result.valid).toBe(false);
            expect(result.error).toContain('Неподдерживаемый материал');
        });
    });

    describe('validateBoltParams', () => {
        test('должен возвращать valid=true для правильных параметров', () => {
            const params = {
                bolt_type: '1.1',
                diameter: 20,
                length: 800,
                material: '09Г2С'
            };
            const result = ValidationService.validateBoltParams(params);
            expect(result.valid).toBe(true);
            expect(result.errors).toEqual([]);
        });

        test('должен возвращать valid=false для неправильных параметров', () => {
            const params = {
                bolt_type: '9.9',
                diameter: 15,
                length: 50,
                material: 'Ст3'
            };
            const result = ValidationService.validateBoltParams(params);
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBeGreaterThan(0);
        });

        test('должен возвращать valid=false для пустых параметров', () => {
            const params = {
                bolt_type: '',
                diameter: '',
                length: '',
                material: ''
            };
            const result = ValidationService.validateBoltParams(params);
            expect(result.valid).toBe(false);
            expect(result.errors.length).toBe(4);
        });
    });
});
