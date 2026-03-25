/**
 * status.js — Управление статусами UI (ES6 module)
 */

import { getById, setText, addClass, removeClass } from '../utils/dom.js';
import { APP_CONFIG } from '../core/config.js';
import { STATUS_TYPES } from '../core/constants.js';

/**
 * Класс для управления статусами UI
 */
export class StatusManager {
    constructor() {
        this.statusElement = null;
        this.timeoutId = null;
    }

    /**
     * Инициализация менеджера статусов
     */
    init() {
        this.statusElement = getById('status');
    }

    /**
     * Показать статус
     * @param {string} message - Сообщение
     * @param {string} type - Тип статуса (success, error, info)
     */
    show(message, type = STATUS_TYPES.INFO) {
        if (!this.statusElement) {
            this.init();
        }

        if (this.statusElement) {
            // Очистка предыдущих классов
            Object.values(STATUS_TYPES).forEach((t) => {
                removeClass(this.statusElement, `status-${t}`);
            });

            // Установка нового статуса
            setText(this.statusElement, message);
            addClass(this.statusElement, `status-${type}`);
            this.statusElement.style.display = 'block';

            // Авто-скрытие для success
            if (type === STATUS_TYPES.SUCCESS) {
                this.clearAutoHide();
                this.timeoutId = setTimeout(() => {
                    this.hide();
                }, APP_CONFIG.STATUS_DURATION.success);
            }
        }
    }

    /**
     * Скрыть статус
     */
    hide() {
        if (this.statusElement) {
            this.statusElement.style.display = 'none';
            this.clearAutoHide();
        }
    }

    /**
     * Очистить таймер авто-скрытия
     */
    clearAutoHide() {
        if (this.timeoutId) {
            clearTimeout(this.timeoutId);
            this.timeoutId = null;
        }
    }

    /**
     * Показать успех
     * @param {string} message - Сообщение
     */
    success(message) {
        this.show(message, STATUS_TYPES.SUCCESS);
    }

    /**
     * Показать ошибку
     * @param {string} message - Сообщение
     */
    error(message) {
        this.show(message, STATUS_TYPES.ERROR);
    }

    /**
     * Показать информацию
     * @param {string} message - Сообщение
     */
    info(message) {
        this.show(message, STATUS_TYPES.INFO);
    }
}

// Экспорт синглтона
export const statusManager = new StatusManager();

export default statusManager;
