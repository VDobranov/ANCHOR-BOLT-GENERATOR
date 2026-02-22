/**
 * ifcBridge.js — Коммуникация между JavaScript и Python (Pyodide)
 */

class IFCBridge {
    constructor(pyodide) {
        this.pyodide = pyodide;
        this.ifc_main = null;
        this.currentIFCData = null;
    }

    async initialize() {
        try {
            UI.showStatus('Загрузка Python модулей...', 'info');
            await this.loadPythonModules();

            UI.showStatus('Инициализация Python модулей...', 'info');
            await this.verifyIfcOpenShell();
            await this.initializeBaseDocument();

            this.ifc_main = this.pyodide.globals.get('ifc_main');
            console.log('✓ Python модули инициализированы');
            UI.showStatus('Python модули успешно инициализированы', 'info');
            return true;
        } catch (error) {
            console.error('Ошибка инициализации Python:', error);
            UI.showStatus(`Ошибка инициализации: ${error.message}`, 'error');
            throw error;
        }
    }

    async loadPythonModules() {
        const FS = this.pyodide.FS;

        // Создание директорий
        try { FS.mkdir('/wheels'); } catch (e) { if (e.code !== 'EEXIST') throw e; }
        try { FS.mkdir('/python'); } catch (e) { if (e.code !== 'EEXIST') throw e; }

        // Загрузка micropip
        UI.showStatus('Загрузка micropip...', 'info');
        await this.pyodide.loadPackage('micropip');

        // Установка зависимостей
        UI.showStatus('Установка зависимостей...', 'info');
        await this.pyodide.runPythonAsync(`
            import micropip
            print('  Installing typing_extensions...')
            await micropip.install('typing_extensions')
            print('  Installing numpy...')
            await micropip.install('numpy')
            print('  ✓ Dependencies installed')
        `);

        // Установка ifcopenshell
        UI.showStatus('Установка ifcopenshell...', 'info');
        await this.pyodide.runPythonAsync(`
            import micropip
            print('  Installing ifcopenshell...')
            await micropip.install('${APP_CONFIG.IFCOPENSHELL_WHEEL_URL}', deps=False)
            print('  ✓ ifcopenshell installed')
        `);

        // Проверка импорта ifcopenshell
        UI.showStatus('Проверка ifcopenshell...', 'info');
        await this.pyodide.runPythonAsync(`
            try:
                import ifcopenshell
                print(f'  ✓ ifcopenshell imported: {ifcopenshell.__version__ if hasattr(ifcopenshell, "__version__") else "unknown"}')
            except ImportError as e:
                raise RuntimeError(f'ifcopenshell not importable: {e}')
        `);

        // Загрузка Python модулей
        const cacheBuster = '?v=' + Date.now();
        
        // Добавляем /python в sys.path
        await this.pyodide.runPythonAsync(`
            import sys
            if '/python' not in sys.path:
                sys.path.insert(0, '/python')
        `);
        
        for (const filePath of APP_CONFIG.PYTHON_MODULES) {
            const fileName = filePath.split('/').pop();
            const response = await fetch(filePath + cacheBuster);
            if (!response.ok) throw new Error(`Failed to fetch ${filePath}`);
            const content = await response.text();
            FS.writeFile(`/python/${fileName}`, content);
        }
    }

    async verifyIfcOpenShell() {
        await this.pyodide.runPythonAsync(`
            import sys
            sys.path.insert(0, '/python')

            # Проверяем, что ifcopenshell импортируется
            try:
                import ifcopenshell
                print(f'✓ ifcopenshell доступен: {ifcopenshell.__version__ if hasattr(ifcopenshell, "__version__") else "unknown"}')
            except ImportError as e:
                raise RuntimeError(f'ifcopenshell не доступен: {e}')

            # Проверяем ifcopenshell.geom
            try:
                import ifcopenshell.geom
                print('✓ ifcopenshell.geom доступен')
            except ImportError as e:
                print(f'⚠ ifcopenshell.geom не доступен: {e}')

            # Проверяем main.is_ifcopenshell_available()
            import main
            if not main.is_ifcopenshell_available():
                raise RuntimeError('ifcopenshell не доступен в main модуле')
        `);
    }

    async initializeBaseDocument() {
        await this.pyodide.runPythonAsync(`
            import sys
            sys.path.insert(0, '/python')
            import main as ifc_main
            
            # Проверяем доступность ifcopenshell
            if not ifc_main.is_ifcopenshell_available():
                raise RuntimeError('ifcopenshell не доступен перед инициализацией документа')
            
            ifc_main.initialize_base_document()
            print('✓ Базовый документ инициализирован')
        `);
    }

    async generateBolt(params) {
        try {
            const paramsJson = JSON.stringify(params)
                .replace(/false/g, 'False')
                .replace(/true/g, 'True');

            const result = await this.pyodide.runPythonAsync(`
                from instance_factory import generate_bolt_assembly
                params = ${paramsJson}
                ifc_str, mesh_data = generate_bolt_assembly(params)
                (ifc_str, mesh_data)
            `);

            this.currentIFCData = result[0];

            return {
                ifcData: result[0],
                meshData: result[1],
                status: 'success'
            };
        } catch (error) {
            console.error('Python error:', error);
            return {
                status: 'error',
                message: error.message
            };
        }
    }

    getIFCData() {
        return this.currentIFCData;
    }

    async getElementProperties(elementId) {
        try {
            return await this.pyodide.runPythonAsync(`
                from instance_factory import get_element_properties
                get_element_properties('${elementId}')
            `);
        } catch (error) {
            console.error('Error getting element properties:', error);
            return {};
        }
    }
}

let ifcBridge = null;

async function initializeIFCBridge(pyodide) {
    ifcBridge = new IFCBridge(pyodide);
    await ifcBridge.initialize();
    return ifcBridge;
}

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { IFCBridge, initializeIFCBridge };
}
