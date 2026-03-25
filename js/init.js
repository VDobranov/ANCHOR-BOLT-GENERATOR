/**
 * init.js — Точка входа приложения
 * Загружается последним, запускает инициализацию
 */

import UI from './ui.js';

document.addEventListener('DOMContentLoaded', () => {
    UI.toggle(false);
    UI.showStatus('Инициализация приложения...', 'info');
});
