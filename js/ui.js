/**
 * ui.js — UI утилиты: статусы, toggle элементов, download
 */

const UI = {
    /**
     * Включение/выключение UI элементов
     * @param {boolean} enabled
     */
    toggle(enabled) {
        const selectors = ['#boltType', '#diameter', '#length', '#material'];

        selectors.forEach((selector) => {
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
     * @param {object} data — данные элемента (name, elementProperties, ifc_type)
     */
    updatePropertiesPanel(data) {
        const panel = document.getElementById('propertiesContent');
        if (!panel) return;

        if (!data) {
            panel.innerHTML = '<p class="placeholder">Выберите элемент в 3D сцене</p>';
            return;
        }

        let html = `
            <div class="property-item">
                <span class="property-key">IFC класс:</span>
                <span class="property-value">${data.ifc_type || 'N/A'}</span>
            </div>
            <div class="property-item">
                <span class="property-key">Имя:</span>
                <span class="property-value">${data.name || 'Unnamed'}</span>
            </div>
        `;

        // Отображение PropertySet
        if (
            data.elementProperties?.property_sets &&
            data.elementProperties.property_sets.length > 0
        ) {
            for (const pset of data.elementProperties.property_sets) {
                html += `<div class="pset-header">${pset.name}</div>`;
                if (pset.properties && pset.properties.length > 0) {
                    for (const prop of pset.properties) {
                        const value =
                            prop.value !== null && prop.value !== undefined ? prop.value : 'N/A';
                        html += `
                            <div class="property-item">
                                <span class="property-key">${prop.name}:</span>
                                <span class="property-value">${value}</span>
                            </div>
                        `;
                    }
                } else {
                    html += `<p class='placeholder'>Нет свойств</p>`;
                }
            }
        } else {
            html += `<p class='placeholder'>Нет PropertySet</p>`;
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
        element.setAttribute(
            'href',
            'data:text/plain;charset=utf-8,' + encodeURIComponent(ifcData)
        );
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

// ES6 export
export default UI;

// CommonJS export для обратной совместимости
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UI;
}
