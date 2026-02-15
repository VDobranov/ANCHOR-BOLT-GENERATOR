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

        // Load ifcopenshell wheel file
        console.log('  Loading ifcopenshell wheel...');
        const wheelFilename = 'ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl';
        const wheelUrl = 'wheels/' + wheelFilename;
        try {
            const response = await fetch(wheelUrl);
            if (!response.ok) {
                throw new Error(`Failed to fetch wheel: ${response.status}`);
            }
            const wheelData = await response.arrayBuffer();
            FS.writeFile('/wheels/' + wheelFilename, new Uint8Array(wheelData));
            console.log('  ✓ ifcopenshell wheel loaded');
        } catch (error) {
            console.error('Failed to load ifcopenshell wheel:', error);
            throw error;
        }

        // Load micropip package first
        console.log('  Loading micropip...');
        await pyodide.loadPackage('micropip');
        console.log('  ✓ micropip loaded');

        // Install ifcopenshell using micropip
        console.log('  Installing ifcopenshell...');
        await pyodide.runPythonAsync(`
            import micropip
            await micropip.install('file:///wheels/${wheelFilename}')
        `);
        console.log('  ✓ ifcopenshell installed');

        // Load each Python file
        const cacheBuster = '?v=' + Date.now(); // Prevent browser caching
        for (const filePath of PYTHON_MODULES) {
            const fileName = filePath.split('/').pop();

            try {
                console.log(`  Loading ${fileName}...`);

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
            } catch (error) {
                console.error(`Failed to load ${fileName}:`, error);
                throw error;
            }
        }

        console.log('✓ All Python modules loaded');
    } catch (error) {
        console.error('Error loading Python modules:', error);
        throw new Error(`Failed to load Python modules: ${error.message}`);
    }
}
