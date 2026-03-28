/**
 * resize.js — Управление изменением ширины левой панели
 */

class PanelResizer {
    constructor(handleSelector, leftPanelSelector, minWidth = 300, maxWidth = 800) {
        this.handle = document.querySelector(handleSelector);
        this.leftPanel = document.querySelector(leftPanelSelector);
        this.mainGrid = this.handle?.parentElement;
        this.minWidth = minWidth;
        this.maxWidth = maxWidth;
        this.isResizing = false;
        this.startX = 0;
        this.startWidth = 0;

        if (this.handle && this.mainGrid) {
            this.setupListeners();
        }
    }

    setupListeners() {
        this.handle.addEventListener('mousedown', (e) => this.startResize(e));
        document.addEventListener('mousemove', (e) => this.resize(e));
        document.addEventListener('mouseup', () => this.stopResize());
    }

    startResize(e) {
        this.isResizing = true;
        this.startX = e.clientX;
        this.startWidth = this.leftPanel.offsetWidth;
        this.handle.classList.add('resizing');
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'col-resize';
    }

    resize(e) {
        if (!this.isResizing) return;

        const deltaX = e.clientX - this.startX;
        let newWidth = this.startWidth + deltaX;

        // Ограничиваем ширину
        newWidth = Math.max(this.minWidth, Math.min(newWidth, this.maxWidth));

        // Обновляем grid-template-columns (меняем только первую колонку)
        this.mainGrid.style.gridTemplateColumns = `${newWidth}px 8px 1fr`;
    }

    stopResize() {
        if (this.isResizing) {
            this.isResizing = false;
            this.handle.classList.remove('resizing');
            document.body.style.userSelect = '';
            document.body.style.cursor = '';

            // Сохраняем ширину в localStorage
            const currentWidth = this.leftPanel.offsetWidth;
            localStorage.setItem('formPanelWidth', currentWidth);
        }
    }

    // Восстановление сохраненной ширины
    restoreWidth() {
        const savedWidth = localStorage.getItem('formPanelWidth');
        if (savedWidth) {
            const width = parseInt(savedWidth, 10);
            if (width >= this.minWidth && width <= this.maxWidth) {
                this.mainGrid.style.gridTemplateColumns = `${width}px 8px 1fr`;
                return;
            }
        }
        // Если нет сохраненной ширины или она некорректна - используем 450px по умолчанию
        this.mainGrid.style.gridTemplateColumns = `450px 8px 1fr`;
    }
}

// Инициализация после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    // Сброс сохраненной ширины для тестирования
    localStorage.removeItem('formPanelWidth');

    const resizer = new PanelResizer('#resizeHandle', '.form-section');
    resizer.restoreWidth();
});

// ES6 export
export default PanelResizer;
