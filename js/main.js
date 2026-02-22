/**
 * main.js — Оркестрация приложения
 * Координация между формой, 3D viewer и Python-мостом
 */

let viewer = null;
let bridge = null;
let form = null;
let pyodide = null;

/**
 * Инициализация приложения
 */
async function initializeApp() {
    try {
        // Инициализация 3D viewer
        const canvas = document.getElementById('canvas3D');
        viewer = new IFCViewer(canvas);
        console.log('✓ 3D Viewer инициализирован');

        // Загрузка Pyodide
        UI.showStatus('Загрузка Pyodide runtime...', 'info');
        pyodide = await loadPyodide();
        console.log('✓ Pyodide загружен');

        // Инициализация IFC Bridge
        UI.showStatus('Инициализация IFC Bridge...', 'info');
        bridge = await initializeIFCBridge(pyodide);
        console.log('✓ IFC Bridge инициализирован');

        // Инициализация формы
        form = new BoltForm({
            pyodide,
            onParamsChange: handleParamsChange
        });
        form.init();
        console.log('✓ Форма инициализирована');

        // Генерация болта по умолчанию
        UI.showStatus('Генерация болта по умолчанию...', 'info');
        await generateDefaultBolt();

        UI.showStatus('Приложение готово к работе', 'success', 3000);
        UI.toggle(true);
    } catch (error) {
        UI.showStatus(`Ошибка инициализации: ${error.message}`, 'error', 0);
        console.error('Initialization error:', error);
    }
}

/**
 * Обработчик изменения параметров формы
 */
async function handleParamsChange(params) {
    await generateBolt(params);
}

/**
 * Генерация болта с заданными параметрами
 */
async function generateBolt(params) {
    if (!bridge) {
        UI.showStatus('Ошибка: Приложение не инициализировано', 'error', 5000);
        return;
    }

    UI.toggle(false);
    UI.showStatus(`Генерирую болт: ${params.bolt_type}, М${params.diameter}x${params.length}...`, 'info');

    try {
        const result = await bridge.generateBolt(params);

        if (result.status === 'error') {
            UI.showStatus(`Ошибка: ${result.message}`, 'error', 5000);
            return;
        }

        // Обновление 3D вида
        if (result.meshData) {
            viewer.updateMeshes(result.meshData);
        }

        // Включение кнопки download
        UI.toggleDownloadButton(true);
        UI.showStatus(`Болт ${params.bolt_type}.М${params.diameter}x${params.length} сгенерирован!`, 'success', 3000);
    } catch (error) {
        UI.showStatus(`Ошибка: ${error.message}`, 'error', 5000);
        console.error(error);
    } finally {
        UI.toggle(true);
    }
}

/**
 * Генерация болта по умолчанию
 */
async function generateDefaultBolt() {
    form.setParams(APP_CONFIG.DEFAULT_BOLT_PARAMS);
    await generateBolt(APP_CONFIG.DEFAULT_BOLT_PARAMS);
}

/**
 * Download IFC файла
 */
function downloadIFCFile() {
    const ifcData = bridge.getIFCData();
    if (!ifcData) return;

    const params = form.getParams();
    const filename = UI.generateFilename(params);

    UI.downloadFile(ifcData, filename);
    UI.showStatus(`Файл ${filename} скачан`, 'success', 3000);
}

/**
 * Обработчик события выбора mesh-объекта
 */
window.addEventListener('meshSelected', (e) => {
    UI.updatePropertiesPanel(e.detail);
});

/**
 * Обработчик кнопки download
 */
document.getElementById('downloadBtn').addEventListener('click', downloadIFCFile);

// Запуск инициализации
initializeApp();

// Export для доступа из других модулей
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { initializeApp, generateBolt, downloadIFCFile };
}
