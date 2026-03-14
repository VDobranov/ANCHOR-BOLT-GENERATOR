/**
 * validationService.js — Валидация параметров болтов (ES6 module)
 */

import { AVAILABLE_DIAMETERS, BOLT_TYPES, MATERIALS } from '../core/constants.js';

/**
 * Класс для валидации параметров болтов
 */
export class ValidationService {
    /**
     * Валидировать тип болта
     * @param {string} boltType - Тип болта
     * @returns {{valid: boolean, error: string|null}}
     */
    static validateBoltType(boltType) {
        if (!boltType) {
            return { valid: false, error: 'Тип болта не указан' };
        }

        if (!BOLT_TYPES[boltType]) {
            return { valid: false, error: `Неподдерживаемый тип болта: ${boltType}` };
        }

        return { valid: true, error: null };
    }

    /**
     * Валидировать диаметр болта
     * @param {number} diameter - Диаметр
     * @returns {{valid: boolean, error: string|null}}
     */
    static validateDiameter(diameter) {
        if (!diameter) {
            return { valid: false, error: 'Диаметр не указан' };
        }

        const numDiameter = Number(diameter);
        if (isNaN(numDiameter)) {
            return { valid: false, error: 'Диаметр должен быть числом' };
        }

        if (!AVAILABLE_DIAMETERS.includes(numDiameter)) {
            return { valid: false, error: `Диаметр должен быть одним из: ${AVAILABLE_DIAMETERS.join(', ')}` };
        }

        return { valid: true, error: null };
    }

    /**
     * Валидировать длину болта
     * @param {number} length - Длина
     * @returns {{valid: boolean, error: string|null}}
     */
    static validateLength(length) {
        if (!length) {
            return { valid: false, error: 'Длина не указана' };
        }

        const numLength = Number(length);
        if (isNaN(numLength)) {
            return { valid: false, error: 'Длина должна быть числом' };
        }

        if (numLength < 100 || numLength > 2000) {
            return { valid: false, error: 'Длина должна быть от 100 до 2000 мм' };
        }

        return { valid: true, error: null };
    }

    /**
     * Валидировать материал
     * @param {string} material - Материал
     * @returns {{valid: boolean, error: string|null}}
     */
    static validateMaterial(material) {
        if (!material) {
            return { valid: false, error: 'Материал не указан' };
        }

        if (!MATERIALS[material]) {
            return { valid: false, error: `Неподдерживаемый материал: ${material}` };
        }

        return { valid: true, error: null };
    }

    /**
     * Валидировать все параметры болта
     * @param {Object} params - Параметры болта
     * @returns {{valid: boolean, errors: Array<string>}}
     */
    static validateBoltParams(params) {
        const errors = [];

        const typeResult = this.validateBoltType(params.bolt_type);
        if (!typeResult.valid) errors.push(typeResult.error);

        const diameterResult = this.validateDiameter(params.diameter);
        if (!diameterResult.valid) errors.push(diameterResult.error);

        const lengthResult = this.validateLength(params.length);
        if (!lengthResult.valid) errors.push(lengthResult.error);

        const materialResult = this.validateMaterial(params.material);
        if (!materialResult.valid) errors.push(materialResult.error);

        return {
            valid: errors.length === 0,
            errors
        };
    }
}

export default ValidationService;
