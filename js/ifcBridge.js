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
            // Import Python modules
            await this.pyodide.runPythonAsync(`
                import sys
                sys.path.insert(0, '/python')
                import main as ifc_main
                ifc_main.initialize_base_document()
            `);

            this.ifc_main = this.pyodide.globals.get('ifc_main');
            console.log('✓ Python modules initialized');
            return true;
        } catch (error) {
            console.error('Failed to initialize Python modules:', error);
            throw error;
        }
    }

    async generateBolt(params) {
        try {
            const result = await this.pyodide.runPythonAsync(`
                from instance_factory import generate_bolt_assembly
                import json

                params = ${JSON.stringify(params)}

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
        let pyodide = await loadPyodide();
        ifcBridge = new IFCBridge(pyodide);
        await ifcBridge.initialize();
        return ifcBridge;
    } catch (error) {
        console.error('Bridge initialization failed:', error);
        throw error;
    }
}
