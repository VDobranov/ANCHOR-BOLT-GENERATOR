/**
 * constants.js — Константы приложения (ES6 module)
 */

export const BOLT_TYPES = Object.freeze({
    1.1: 'Тип 1.1 - С вылетом крюка и загибом',
    1.2: 'Тип 1.2 - С вылетом крюка и загибом (вариант)',
    2.1: 'Тип 2.1 - С вылетом крюка и загибом',
    5: 'Тип 5 - Прямой болт'
});

export const MATERIALS = Object.freeze({
    '09Г2С': 'Низколегированная сталь ГОСТ 19281-2014',
    ВСт3пс2: 'Углеродистая конструкционная сталь ГОСТ 535-88',
    '10Г2': 'Низколегированная сталь ГОСТ 19281-2014'
});

export const AVAILABLE_DIAMETERS = Object.freeze([12, 16, 20, 24, 30, 36, 42, 48]);

export const STATUS_TYPES = Object.freeze({
    SUCCESS: 'success',
    ERROR: 'error',
    INFO: 'info'
});

export default {
    BOLT_TYPES,
    MATERIALS,
    AVAILABLE_DIAMETERS,
    STATUS_TYPES
};
