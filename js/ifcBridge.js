/**
 * ifcBridge.js - Communication layer between JavaScript and Python
 */

class IFCBridge {
    constructor(pyodide) {
        this.pyodide = pyodide;
        this.ifc_main = null;
        this.currentIFCData = null;
    }

    async initialize() {
        try {
            // First, load Python modules into Pyodide's virtual filesystem
            if (typeof showStatus !== 'undefined') {
                showStatus('Загрузка Python модулей в виртуальную файловую систему...', 'info');
            }
            await loadPythonModules(this.pyodide);
            if (typeof showStatus !== 'undefined') {
                showStatus('Python модули загружены в виртуальную файловую систему', 'info');
            }

            // Then import and initialize them
            if (typeof showStatus !== 'undefined') {
                showStatus('Импорт и инициализация Python модулей...', 'info');
            }
            
            // First, verify ifcopenshell is available before initializing
            if (typeof showStatus !== 'undefined') {
                showStatus('Проверка доступности ifcopenshell...', 'info');
            }
            await this.pyodide.runPythonAsync(`
                import sys
                sys.path.insert(0, '/python')
                
                # Verify ifcopenshell is available
                try:
                    import ifcopenshell
                    print(f'✓ ifcopenshell available: {ifcopenshell}')
                except ImportError as e:
                    print(f'✗ ifcopenshell NOT available: {e}')
                    raise RuntimeError('ifcopenshell not available after micropip installation')
                
                # Import main module
                import main as ifc_main
                
                # Check if ifcopenshell is available via main module
                if not ifc_main.is_ifcopenshell_available():
                    raise RuntimeError('ifcopenshell not available in main module')
                
                print('✓ ifcopenshell verified, initializing base document...')
                ifc_main.initialize_base_document()
                print('✓ Base document initialized successfully')
            `);

            this.ifc_main = this.pyodide.globals.get('ifc_main');
            console.log('✓ Python modules initialized');
            if (typeof showStatus !== 'undefined') {
                showStatus('Python модули успешно инициализированы', 'info');
            }
            return true;
        } catch (error) {
            console.error('Failed to initialize Python modules:', error);
            if (typeof showStatus !== 'undefined') {
                showStatus(`Ошибка инициализации: ${error.message}`, 'error');
            }
            throw error;
        }
    }

    async generateBolt(params) {
        try {
            // Convert JavaScript booleans to Python booleans in JSON
            const paramsJson = JSON.stringify(params)
                .replace(/false/g, 'False')
                .replace(/true/g, 'True');

            const result = await this.pyodide.runPythonAsync(`
                from instance_factory import generate_bolt_assembly
                import json

                params = ${paramsJson}

                ifc_str, mesh_data = generate_bolt_assembly(params)

                # Return tuple: (ifc_string, mesh_dict)
                (ifc_str, mesh_data)
            `);

            // result is a Python tuple converted to JS
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
            const result = await this.pyodide.runPythonAsync(`
                from instance_factory import get_element_properties
                get_element_properties('${elementId}')
            `);

            return result;
        } catch (error) {
            console.error('Error getting element properties:', error);
            return {};
        }
    }
}

// Global instance
let ifcBridge = null;

async function initializeIFCBridge() {
    try {
        if (typeof showStatus !== 'undefined') {
            showStatus('Создание IFC Bridge...', 'info');
        }
        ifcBridge = new IFCBridge(pyodide);
        if (typeof showStatus !== 'undefined') {
            showStatus('Загрузка Python модулей...', 'info');
        }
        await ifcBridge.initialize();
        if (typeof showStatus !== 'undefined') {
            showStatus('Python модули загружены', 'info');
        }
        return ifcBridge;
    } catch (error) {
        console.error('Bridge initialization failed:', error);
        throw error;
    }
}
