/**
 * pythonLoader.js - Loads Python modules into Pyodide's virtual filesystem
 */

/**
 * List of Python modules to load (file path → module name)
 */
const PYTHON_MODULES = [
    'python/main.py',
    'python/instance_factory.py',
    'python/type_factory.py',
    'python/gost_data.py',
    'python/geometry_builder.py',
    'python/ifc_generator.py',
    'python/material_manager.py',
    'python/pset_manager.py'
];

/**
 * Load Python modules into Pyodide's virtual filesystem
 * @param {object} pyodide - Pyodide instance
 * @returns {Promise<void>}
 */
async function loadPythonModules(pyodide) {
    console.log('Loading Python modules...');

    const FS = pyodide.FS;

    try {
        // Create directories in Pyodide's virtual filesystem
        try {
            FS.mkdir('/wheels');
        } catch (e) {
            if (e.code !== 'EEXIST') throw e;
        }

        try {
            FS.mkdir('/python');
        } catch (e) {
            if (e.code !== 'EEXIST') throw e;
        }

        // Load micropip package first
        if (typeof showStatus !== 'undefined') {
            showStatus('Загрузка micropip пакета...', 'info');
        }
        console.log('  Loading micropip...');
        await pyodide.loadPackage('micropip');
        console.log('  ✓ micropip loaded');
        if (typeof showStatus !== 'undefined') {
            showStatus('micropip пакет загружен', 'info');
        }

        // Install ifcopenshell using direct wheel installation
        // This approach works around micropip's URL parsing issues with GitHub Pages subdirectories
        if (typeof showStatus !== 'undefined') {
            showStatus('Установка ifcopenshell...', 'info');
        }
        console.log('  Installing ifcopenshell...');

        // Calculate the base URL for the application (handles GitHub Pages subdirectory deployment)
        const baseUrl = window.location.origin + window.location.pathname.replace(/\/$/, '');
        const wheelFilename = 'ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl';
        const wheelFullUrl = baseUrl + '/wheels/' + wheelFilename;

        // First, try to install from Pyodide's official repository
        try {
            await pyodide.runPythonAsync(`
                import micropip
                await micropip.install('ifcopenshell', deps=False)
            `);
            console.log('  ✓ ifcopenshell installed from Pyodide repository');
            if (typeof showStatus !== 'undefined') {
                showStatus('ifcopenshell установлен (Pyodide CDN)', 'info');
            }
        } catch (error) {
            console.warn('  Failed to install from Pyodide repository, using local wheel...');

            // Fallback: Download wheel file directly and install from virtual filesystem
            try {
                console.log('  Downloading wheel from:', wheelFullUrl);

                // Fetch the wheel file directly
                const response = await fetch(wheelFullUrl);
                if (!response.ok) {
                    throw new Error(`Failed to fetch wheel: ${response.status} ${response.statusText}`);
                }
                const wheelData = await response.arrayBuffer();

                // Write to Pyodide's virtual filesystem
                FS.writeFile('/wheels/' + wheelFilename, new Uint8Array(wheelData));
                console.log('  ✓ Wheel file downloaded and written to FS');

                // Install using micropip from the local filesystem path
                // Use absolute path within Pyodide's filesystem
                await pyodide.runPythonAsync(`
                    import micropip
                    # Install from the wheel file in our virtual filesystem
                    await micropip.install('/wheels/${wheelFilename}', deps=False)
                `);

                console.log('  ✓ ifcopenshell installed from local wheel');
                if (typeof showStatus !== 'undefined') {
                    showStatus('ifcopenshell установлен (локальный файл)', 'info');
                }
            } catch (localError) {
                console.error('  Failed to install from local wheel:', localError);
                throw new Error(`Не удалось установить ifcopenshell. Проверьте, что файл существует: ${wheelFullUrl}. ${localError.message}`);
            }
        }
        console.log('  ✓ ifcopenshell installed');
        if (typeof showStatus !== 'undefined') {
            showStatus('ifcopenshell установлен', 'info');
        }

        // Load each Python file
        if (typeof showStatus !== 'undefined') {
            showStatus('Загрузка Python модулей...', 'info');
        }
        const cacheBuster = '?v=' + Date.now(); // Prevent browser caching
        for (const filePath of PYTHON_MODULES) {
            const fileName = filePath.split('/').pop();

            try {
                console.log(`  Loading ${fileName}...`);
                if (typeof showStatus !== 'undefined') {
                    showStatus(`Загрузка модуля: ${fileName}...`, 'info');
                }

                // Fetch the file content with cache busting
                const response = await fetch(filePath + cacheBuster);
                if (!response.ok) {
                    throw new Error(`Failed to fetch ${filePath}: ${response.status}`);
                }

                const content = await response.text();

                // Write to Pyodide's virtual filesystem
                const fullPath = `/python/${fileName}`;
                FS.writeFile(fullPath, content);

                console.log(`  ✓ ${fileName} loaded`);
                if (typeof showStatus !== 'undefined') {
                    showStatus(`Модуль ${fileName} загружен`, 'info');
                }
            } catch (error) {
                console.error(`Failed to load ${fileName}:`, error);
                throw error;
            }
        }

        console.log('✓ All Python modules loaded');
        if (typeof showStatus !== 'undefined') {
            showStatus('Все Python модули загружены', 'info');
        }
    } catch (error) {
        console.error('Error loading Python modules:', error);
        throw new Error(`Failed to load Python modules: ${error.message}`);
    }
}
