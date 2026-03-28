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
     * На маленьких экранах - свернуто, на больших - развернуто
     */
    setInitialState() {
        const isSmallScreen = window.innerWidth <= this.smallScreenThreshold;

        if (isSmallScreen) {
            this.panel.classList.add('collapsed');
        } else {
            this.panel.classList.remove('collapsed');
        }
    }

    /**
     * Переключение состояния
     */
    toggle() {
        this.panel.classList.toggle('collapsed');
    }

    /**
     * Обработка изменения размера окна
     */
    handleResize() {
        const isSmallScreen = window.innerWidth <= this.smallScreenThreshold;

        // При изменении размера экрана не меняем состояние,
        // если пользователь явно не свернул/развернул
        // Но если перешли порог - применяем состояние по умолчанию
        if (isSmallScreen && !this.panel.classList.contains('collapsed')) {
            // На маленьком экране по умолчанию свернуто
            // но не сворачиваем автоматически, если пользователь развернул
        }
    }

    /**
     * Развернуть панель
     */
    expand() {
        this.panel.classList.remove('collapsed');
    }

    /**
     * Свернуть панель
     */
    collapse() {
        this.panel.classList.add('collapsed');
    }
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new PropertiesPanelToggler();
});

// ES6 export
export default PropertiesPanelToggler;
