/**
 * dom.js — DOM утилиты (ES6 module)
 */

/**
 * Получить элемент по ID
 * @param {string} id - ID элемента
 * @returns {HTMLElement|null}
 */
export function getById(id) {
    return document.getElementById(id);
}

/**
 * Получить элементы по query selector
 * @param {string} selector - Селектор
 * @returns {NodeList}
 */
export function querySelectorAll(selector) {
    return document.querySelectorAll(selector);
}

/**
 * Получить элемент по query selector
 * @param {string} selector - Селектор
 * @returns {HTMLElement|null}
 */
export function querySelector(selector) {
    return document.querySelector(selector);
}

/**
 * Добавить класс элементу
 * @param {HTMLElement} element - Элемент
 * @param {string} className - Имя класса
 */
export function addClass(element, className) {
    if (element) {
        element.classList.add(className);
    }
}

/**
 * Удалить класс у элемента
 * @param {HTMLElement} element - Элемент
 * @param {string} className - Имя класса
 */
export function removeClass(element, className) {
    if (element) {
        element.classList.remove(className);
    }
}

/**
 * Переключить класс у элемента
 * @param {HTMLElement} element - Элемент
 * @param {string} className - Имя класса
 */
export function toggleClass(element, className) {
    if (element) {
        element.classList.toggle(className);
    }
}

/**
 * Установить текст элемента
 * @param {HTMLElement} element - Элемент
 * @param {string} text - Текст
 */
export function setText(element, text) {
    if (element) {
        element.textContent = text;
    }
}

/**
 * Установить HTML элемента
 * @param {HTMLElement} element - Элемент
 * @param {string} html - HTML
 */
export function setHTML(element, html) {
    if (element) {
        element.innerHTML = html;
    }
}

/**
 * Добавить обработчик события
 * @param {HTMLElement} element - Элемент
 * @param {string} event - Событие
 * @param {Function} handler - Обработчик
 * @param {Object} options - Опции
 */
export function addEventListener(element, event, handler, options = {}) {
    if (element) {
        element.addEventListener(event, handler, options);
    }
}

/**
 * Удалить обработчик события
 * @param {HTMLElement} element - Элемент
 * @param {string} event - Событие
 * @param {Function} handler - Обработчик
 */
export function removeEventListener(element, event, handler) {
    if (element) {
        element.removeEventListener(event, handler);
    }
}

export default {
    getById,
    querySelectorAll,
    querySelector,
    addClass,
    removeClass,
    toggleClass,
    setText,
    setHTML,
    addEventListener,
    removeEventListener
};
