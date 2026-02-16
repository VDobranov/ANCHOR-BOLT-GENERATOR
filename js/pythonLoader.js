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

        // Install ifcopenshell using micropip with direct URL
        if (typeof showStatus !== 'undefined') {
            showStatus('Установка ifcopenshell...', 'info');
        }
        console.log('  Installing ifcopenshell...');

        // Use raw GitHub URL for direct installation by micropip
        const wheelUrl = 'https://raw.githubusercontent.com/vdobranov/anchor-bolt-generator/main/wheels/ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl';

        try {
            console.log('  Installing from:', wheelUrl);

            await pyodide.runPythonAsync(`
                import micropip
                print('  Starting micropip installation of dependencies...')
                
                # Install typing_extensions first (required dependency)
                print('  Installing typing_extensions...')
                await micropip.install('typing_extensions')
                print('  ✓ typing_extensions installed')
                
                # Install numpy (required by ifcopenshell)
                print('  Installing numpy...')
                await micropip.install('numpy')
                print('  ✓ numpy installed')
                
                # Now install ifcopenshell
                print('  Installing ifcopenshell...')
                await micropip.install('${wheelUrl}', deps=False)
                print('  ✓ micropip installation complete')
                
                # Verify installation by attempting import
                try:
                    import ifcopenshell
                    print(f'  ✓ ifcopenshell imported successfully (version: {ifcopenshell.__version__ if hasattr(ifcopenshell, "__version__") else "unknown"})')
                except ImportError as e:
                    print(f'  ✗ Failed to import ifcopenshell after installation: {e}')
                    raise RuntimeError(f'ifcopenshell installed but not importable: {e}')
            `);

            console.log('  ✓ ifcopenshell installed and verified');
            if (typeof showStatus !== 'undefined') {
                showStatus('ifcopenshell установлен и проверен', 'info');
            }
        } catch (error) {
            console.error('  Failed to install ifcopenshell:', error);
            throw new Error(`Не удалось установить ifcopenshell: ${error.message}`);
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
