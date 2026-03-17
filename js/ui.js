/**
 * ui.js — UI утилиты: статусы, toggle элементов, download
 */

const UI = {
    /**
     * Включение/выключение UI элементов
     * @param {boolean} enabled
     */
    toggle(enabled) {
        const selectors = [
            '#boltType', '#diameter', '#length', '#material'
        ];

        selectors.forEach(selector => {
            const element = document.querySelector(selector);
            if (element) {
                element.disabled = !enabled;
            }
        });

        const form = document.getElementById('boltForm');
        if (form) {
            form.classList.toggle('disabled', !enabled);
        }
    },

    /**
     * Показ сообщения о статусе
     * @param {string} message
     * @param {'success'|'error'|'info'} type
     * @param {number} duration — время показа в мс (0 = бессрочно)
     */
    showStatus(message, type = 'info', duration = 0) {
        const statusEl = document.getElementById('statusMessage');
        if (!statusEl) return;

        statusEl.textContent = message;
        statusEl.className = `status-message show ${type}`;

        if (duration > 0) {
            setTimeout(() => {
                statusEl.classList.remove('show');
            }, duration);
        }
    },

    /**
     * Скрытие сообщения о статусе
     */
    hideStatus() {
        const statusEl = document.getElementById('statusMessage');
        if (statusEl) {
            statusEl.classList.remove('show');
        }
    },

    /**
     * Обновление панели свойств
     * @param {object} meshItem — выбранный mesh-объект или данные сборки
     */
    updatePropertiesPanel(meshItem) {
        const panel = document.getElementById('propertiesContent');
        if (!panel) return;

        // Если есть данные о сборке, отображаем их
        if (meshItem && meshItem.assemblyInfo) {
            const info = meshItem.assemblyInfo;
            const boltTypeNames = {
                '1.1': 'Тип 1. Исполнение 1',
                '1.2': 'Тип 1. Исполнение 2',
                '2.1': 'Тип 2. Исполнение 1',
                '5': 'Тип 5'
            };
            
            panel.innerHTML = `
                <div class="property-item">
                    <span class="property-key">Имя:</span>
                    <span class="property-value">${meshItem.name}</span>
                </div>
                <div class="property-item">
                    <span class="property-key">Тип болта:</span>
                    <span class="property-value">${boltTypeNames[info.bolt_type] || info.bolt_type}</span>
                </div>
                <div class="property-item">
                    <span class="property-key">Диаметр:</span>
                    <span class="property-value">М${info.diameter}</span>
                </div>
                <div class="property-item">
                    <span class="property-key">Длина:</span>
                    <span class="property-value">${info.length} мм</span>
                </div>
                <div class="property-item">
                    <span class="property-key">Материал:</span>
                    <span class="property-value">${info.material}</span>
                </div>
            `;
            return;
        }

        if (!meshItem) {
            panel.innerHTML = '<p class="placeholder">Выберите элемент в 3D сцене</p>';
            return;
        }

        let html = `
            <div class="property-item">
                <span class="property-key">Имя:</span>
                <span class="property-value">${meshItem.name}</span>
            </div>
            <div class="property-item">
                <span class="property-key">ID:</span>
                <span class="property-value">${meshItem.id}</span>
            </div>
        `;

        if (meshItem.metadata) {
            Object.entries(meshItem.metadata).forEach(([key, value]) => {
                html += `
                    <div class="property-item">
                        <span class="property-key">${key}:</span>
                        <span class="property-value">${value}</span>
                    </div>
                `;
            });
        }

        panel.innerHTML = html;
    },

    /**
     * Download IFC файла
     * @param {string} ifcData — IFC содержимое
     * @param {string} filename — имя файла
     */
    downloadFile(ifcData, filename) {
        if (!ifcData) return;

        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(ifcData));
        element.setAttribute('download', filename);
        element.style.display = 'none';

        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    },

    /**
     * Генерация имени файла для болта
     * @param {object} params — параметры болта
     * @returns {string}
     */
    generateFilename(params) {
        return `bolt_${params.bolt_type}_M${params.diameter}x${params.length}.ifc`;
    },

    /**
     * Включение/выключение кнопки download
     * @param {boolean} enabled
     */
    toggleDownloadButton(enabled) {
        const btn = document.getElementById('downloadBtn');
        if (btn) {
            btn.disabled = !enabled;
        }
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UI;
}
