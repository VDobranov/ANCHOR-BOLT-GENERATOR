/**
 * init.js - Application initialization after Pyodide loads
 * This script waits for Pyodide to be available globally
 */

// Global variable to store pyodide instance
let pyodide = null;

// Wait for Pyodide to be available globally
async function waitForPyodide(timeout = 30000) {
    const startTime = Date.now();
    if (typeof showStatus !== 'undefined') {
        showStatus('Ожидание загрузки Pyodide...', 'info');
    }

    while (typeof loadPyodide === 'undefined') {
        if (Date.now() - startTime > timeout) {
            throw new Error(`Pyodide failed to load within ${timeout}ms`);
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
    
    if (typeof showStatus !== 'undefined') {
        showStatus('Pyodide доступен', 'info');
    }
}

// Initialize app after DOM and Pyodide are ready
async function initializeApp() {
    try {
        // Ensure Pyodide is loaded
        if (typeof showStatus !== 'undefined') {
            showStatus('Загрузка Pyodide runtime...', 'info');
        }
        pyodide = await loadPyodide();
        console.log('✓ Pyodide is available');
        if (typeof showStatus !== 'undefined') {
            showStatus('Pyodide runtime загружен', 'info');
        }

        // Now initialize the IFC Bridge and the rest of the app
        if (typeof showStatus !== 'undefined') {
            showStatus('Инициализация IFC Bridge...', 'info');
        }
        bridge = await initializeIFCBridge();
        console.log('✓ IFC Bridge initialized');
        if (typeof showStatus !== 'undefined') {
            showStatus('IFC Bridge инициализирован', 'info');
        }

        // Setup form listeners
        if (typeof showStatus !== 'undefined') {
            showStatus('Настройка обработчиков событий...', 'info');
        }
        setupFormListeners();
        if (typeof showStatus !== 'undefined') {
            showStatus('Обработчики событий настроены', 'info');
        }

        // Generate default bolt automatically
        if (typeof showStatus !== 'undefined') {
            showStatus('Генерация болта по умолчанию...', 'info');
        }
        await generateDefaultBolt();
        if (typeof showStatus !== 'undefined') {
            showStatus('Болт по умолчанию сгенерирован', 'info');
        }

        // Enable UI after successful initialization
        toggleUI(true);
        if (typeof showStatus !== 'undefined') {
            showStatus('Приложение готово к работе', 'success', 3000);
        }
    } catch (error) {
        if (typeof showStatus !== 'undefined') {
            showStatus(`Ошибка инициализации: ${error.message}`, 'error', 0);
        }
        console.error('Initialization error:', error);
    }
}

// Start initialization when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    // Disable UI and show initialization message
    toggleUI(false);
    showStatus('Инициализация приложения...', 'info');

    try {
        // Initialize 3D viewer (doesn't depend on Pyodide)
        const canvas = document.getElementById('canvas3D');
        viewer = new IFCViewer(canvas);
        console.log('✓ 3D Viewer initialized');
        showStatus('Инициализация 3D визуализации...', 'info');

        // Then wait for Pyodide and initialize the rest
        await initializeApp();
    } catch (error) {
        showStatus(`Ошибка инициализации: ${error.message}`, 'error', 0);
        console.error(error);
    }
});
