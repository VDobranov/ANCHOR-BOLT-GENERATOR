/**
 * init.js - Application initialization after Pyodide loads
 * This script waits for Pyodide to be fully loaded before initializing the app
 */

// Wait for Pyodide to be available globally
async function waitForPyodide(timeout = 30000) {
    const startTime = Date.now();

    while (typeof loadPyodide === 'undefined') {
        if (Date.now() - startTime > timeout) {
            throw new Error(`Pyodide failed to load within ${timeout}ms`);
        }
        await new Promise(resolve => setTimeout(resolve, 100));
    }
}

// Initialize app after DOM and Pyodide are ready
async function initializeApp() {
    try {
        // Ensure Pyodide is loaded
        await waitForPyodide();
        console.log('✓ Pyodide is available');

        // Now initialize the IFC Bridge and the rest of the app
        bridge = await initializeIFCBridge();
        console.log('✓ IFC Bridge initialized');

        // Setup form listeners
        setupFormListeners();

        showStatus('Приложение готово к работе', 'success', 3000);
    } catch (error) {
        showStatus(`Ошибка инициализации: ${error.message}`, 'error', 0);
        console.error('Initialization error:', error);
    }
}

// Start initialization when DOM is ready
document.addEventListener('DOMContentLoaded', async () => {
    showStatus('Инициализация приложения...', 'info');

    try {
        // Initialize 3D viewer (doesn't depend on Pyodide)
        const canvas = document.getElementById('canvas3D');
        viewer = new IFCViewer(canvas);
        console.log('✓ 3D Viewer initialized');

        // Then wait for Pyodide and initialize the rest
        await initializeApp();
    } catch (error) {
        showStatus(`Ошибка инициализации: ${error.message}`, 'error', 0);
        console.error(error);
    }
});
