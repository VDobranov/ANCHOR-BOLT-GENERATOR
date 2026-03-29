/**
 * ifcBridge.js — Коммуникация между JavaScript и Python (Pyodide)
 */

import UI from './ui.js';

class IFCBridge {
    constructor(pyodide) {
        this.pyodide = pyodide;
        this.ifc_main = null;
        this.currentIFCData = null;
    }

    /**
     * Конвертация Proxy-объекта Pyodide в обычный JavaScript объект
     * Рекурсивно обрабатывает вложенные объекты и массивы
     * @param {any} obj - Pyodide Proxy или обычный JS объект
     * @returns {any} - Конвертированный JavaScript объект
     */
    convertPyodideObject(obj) {
        if (!obj) return obj;

        // Если это Pyodide Proxy с методом toJs
        if (obj && typeof obj === 'object' && typeof obj.toJs === 'function') {
            try {
                const jsObj = obj.toJs({ depth: 1 });
                // Рекурсивно обрабатываем вложенные объекты
                if (Array.isArray(jsObj)) {
                    return jsObj.map((item) => this.convertPyodideObject(item));
                } else if (typeof jsObj === 'object' && jsObj !== null) {
                    const result = {};
                    for (const [key, value] of Object.entries(jsObj)) {
                        result[key] = this.convertPyodideObject(value);
                    }
                    return result;
                }
                return jsObj;
            } catch (e) {
                // Если toJs не сработал, пробуем напрямую
                return this.convertProxyDirectly(obj);
            }
        }

        // Если это обычный объект, рекурсивно обрабатываем
        if (Array.isArray(obj)) {
            return obj.map((item) => this.convertPyodideObject(item));
        } else if (typeof obj === 'object' && obj !== null) {
            const result = {};
            for (const [key, value] of Object.entries(obj)) {
                result[key] = this.convertPyodideObject(value);
            }
            return result;
        }

        return obj;
    }

    /**
     * Прямое извлечение данных из Proxy-объекта
     * @param {Proxy} proxy - Pyodide Proxy объект
     * @returns {object} - JavaScript объект
     */
    convertProxyDirectly(proxy) {
        const result = {};
        try {
            // Для dict: получаем ключи через Python
            if (proxy && typeof proxy.keys === 'function') {
                const keys = proxy.keys();
                for (const key of keys) {
                    result[key] = this.convertPyodideObject(proxy.get(key));
                }
            }
        } catch (e) {
            console.warn('Failed to convert proxy directly:', e);
        }
        return result;
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
            print('  Installing shapely...')
            await micropip.install('shapely')
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

        // Создание директорий для пакетов
        try {
            FS.mkdir('/python/data');
        } catch (e) {
            if (e.code !== 'EEXIST') throw e;
        }
        try {
            FS.mkdir('/python/services');
        } catch (e) {
            if (e.code !== 'EEXIST') throw e;
        }

        // Получаем базовый URL (для GitHub Pages)
        const baseUrl = window.location.pathname;
        const baseDir = baseUrl.substring(0, baseUrl.lastIndexOf('/') + 1);

        for (const filePath of APP_CONFIG.PYTHON_MODULES) {
            const fileName = filePath.split('/').pop();
            // Используем абсолютный путь от корня сайта
            const fullPath = baseDir + filePath + cacheBuster;

            console.log(`Loading: ${fullPath}`);
            const response = await fetch(fullPath);
            if (!response.ok) {
                console.error(
                    `Failed to fetch ${fullPath}: ${response.status} ${response.statusText}`
                );
                throw new Error(`Failed to fetch ${filePath}`);
            }
            const content = await response.text();

            // Определяем путь для файла
            let targetPath;
            if (filePath.includes('/data/')) {
                targetPath = `/python/data/${fileName}`;
            } else if (filePath.includes('/services/')) {
                targetPath = `/python/services/${fileName}`;
            } else {
                targetPath = `/python/${fileName}`;
            }

            FS.writeFile(targetPath, content);
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

            # Проверяем shapely
            try:
                import shapely
                print(f'✓ shapely доступен: {shapely.__version__ if hasattr(shapely, "__version__") else "unknown"}')
            except ImportError as e:
                print(f'⚠ shapely не доступен: {e}')
        `);
    }

    async initializeBaseDocument() {
        await this.pyodide.runPythonAsync(`
            import sys
            sys.path.insert(0, '/python')
            import main as ifc_main

            ifc_main.initialize_base_document()
            print('✓ Базовый документ инициализирован')
        `);
    }

    async generateBolt(params, exportSettings) {
        try {
            const paramsJson = JSON.stringify(params)
                .replace(/false/g, 'False')
                .replace(/true/g, 'True');

            // Настройки экспорта по умолчанию
            const settings = exportSettings || {
                assembly_class: 'IfcMechanicalFastener',
                assembly_mode: 'separate',
                geometry_type: 'solid'
            };

            // Класс для сборки доступен только при режиме "Вроссыпь"
            const assemblyClass =
                settings.assembly_mode === 'separate'
                    ? settings.assembly_class
                    : 'IfcMechanicalFastener';

            const settingsJson = JSON.stringify({
                ...settings,
                assembly_class: assemblyClass
            })
                .replace(/false/g, 'False')
                .replace(/true/g, 'True');

            const result = await this.pyodide.runPythonAsync(`
                from instance_factory import generate_bolt_assembly
                params = ${paramsJson}
                settings = ${settingsJson}
                ifc_str, mesh_data = generate_bolt_assembly(
                    params,
                    settings.get('assembly_class', 'IfcMechanicalFastener'),
                    settings.get('assembly_mode', 'separate'),
                    settings.get('geometry_type', 'solid'),
                    settings.get('add_standard_pset', True)
                )
                (ifc_str, mesh_data)
            `);

            this.currentIFCData = result[0];

            // Конвертация Proxy объектов Pyodide в JavaScript объекты
            const meshData = this.convertPyodideObject(result[1]);

            return {
                ifcData: result[0],
                meshData: meshData,
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

    /**
     * Получение PropertySet элемента по GlobalId
     * @param {string} globalId - GlobalId элемента
     * @returns {Promise<object|null>} - Данные о свойствах или null
     */
    async getElementProperties(globalId) {
        try {
            const result = await this.pyodide.runPythonAsync(`
                from ifc_generator import IFCGenerator
                from main import get_ifc_document

                ifc_doc = get_ifc_document()
                generator = IFCGenerator(ifc_doc)
                props = generator.get_element_properties('${globalId}')
                props
            `);

            // Конвертация Proxy объектов Pyodide в JavaScript объекты
            return this.convertPyodideObject(result);
        } catch (error) {
            console.error('Error getting element properties:', error);
            return null;
        }
    }
}

let ifcBridge = null;

async function initializeIFCBridge(pyodide) {
    ifcBridge = new IFCBridge(pyodide);
    await ifcBridge.initialize();
    window.ifcBridge = ifcBridge; // Экспорт в window для доступа из других модулей
    return ifcBridge;
}

// ES6 exports
export { IFCBridge, initializeIFCBridge };

// CommonJS export для обратной совместимости
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { IFCBridge, initializeIFCBridge };
}
