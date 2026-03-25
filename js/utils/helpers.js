/**
 * helpers.js — Вспомогательные функции (ES6 module)
 */

/**
 * Форматировать число с разделителями
 * @param {number} num - Число
 * @returns {string}
 */
export function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
}

/**
 * Округлить число до знаков
 * @param {number} num - Число
 * @param {number} decimals - Количество знаков
 * @returns {number}
 */
export function roundTo(num, decimals = 2) {
    const factor = Math.pow(10, decimals);
    return Math.round(num * factor) / factor;
}

/**
 * Проверить, что значение не null/undefined
 * @param {*} value - Значение
 * @returns {boolean}
 */
export function isDefined(value) {
    return value !== null && value !== undefined;
}

/**
 * Проверить, что значение пустое
 * @param {*} value - Значение
 * @returns {boolean}
 */
export function isEmpty(value) {
    if (Array.isArray(value)) {
        return value.length === 0;
    }
    if (value !== null && typeof value === 'object') {
        return Object.keys(value).length === 0;
    }
    return !value;
}

/**
 * Глубоко клонировать объект
 * @param {Object} obj - Объект
 * @returns {Object}
 */
export function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Получить текущую дату в формате ISO
 * @returns {string}
 */
export function getISODate() {
    return new Date().toISOString();
}

/**
 * Sleep функция
 * @param {number} ms - Миллисекунды
 * @returns {Promise}
 */
export function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Debounce функция
 * @param {Function} func - Функция
 * @param {number} wait - Время ожидания
 * @returns {Function}
 */
export function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle функция
 * @param {Function} func - Функция
 * @param {number} limit - Лимит
 * @returns {Function}
 */
export function throttle(func, limit) {
    let inThrottle;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => (inThrottle = false), limit);
        }
    };
}

export default {
    formatNumber,
    roundTo,
    isDefined,
    isEmpty,
    deepClone,
    getISODate,
    sleep,
    debounce,
    throttle
};
