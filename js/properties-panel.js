/**
 * properties-panel.js — Управление сворачиванием/разворачиванием панели свойств
 */

class PropertiesPanelToggler {
    constructor() {
        this.panel = document.getElementById('propertiesPanel');
        this.toggleButton = document.getElementById('propertiesToggle');
        this.smallScreenThreshold = 1024;

        if (this.panel && this.toggleButton) {
            this.init();
        }
    }

    init() {
        // Установка начального состояния в зависимости от размера экрана
        this.setInitialState();

        // Обработчик клика
        this.toggleButton.addEventListener('click', () => this.toggle());

        // Обработчик изменения размера окна
        window.addEventListener('resize', () => this.handleResize());
    }

    /**
     * Установка начального состояния
     * На маленьких экранах - свернуто (по CSS), на больших - развернуто
     */
    setInitialState() {
        const isSmallScreen = window.innerWidth <= this.smallScreenThreshold;

        if (isSmallScreen) {
            // На маленьких экранах по умолчанию свёрнуто (CSS)
            this.panel.classList.remove('expanded');
        } else {
            // На больших экранах развёрнуто
            this.panel.classList.add('expanded');
        }
    }

    /**
     * Переключение состояния
     */
    toggle() {
        this.panel.classList.toggle('expanded');
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        const isSmallScreen = window.innerWidth <= this.smallScreenThreshold;

        // При изменении размера экрана применяем состояние по умолчанию
        if (isSmallScreen) {
            this.panel.classList.remove('expanded');
        } else {
            this.panel.classList.add('expanded');
        }
    }

    /**
     * Развернуть панель
     */
    expand() {
        this.panel.classList.add('expanded');
    }

    /**
     * Свернуть панель
     */
    collapse() {
        this.panel.classList.remove('expanded');
    }
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new PropertiesPanelToggler();
});

// ES6 export
export default PropertiesPanelToggler;
