/**
 * config.js — Константы и конфигурация приложения
 */

const APP_CONFIG = {
    // Pyodide
    PYODIDE_VERSION: '0.26.0',
    PYODIDE_URL: 'https://cdn.jsdelivr.net/pyodide/dev/full/pyodide.js',

    // Three.js
    THREE_JS_URL: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',

    // ifcopenshell wheel
    IFCOPENSHELL_WHEEL_URL: 'https://raw.githubusercontent.com/vdobranov/anchor-bolt-generator/main/wheels/ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl',

    // Python модули для загрузки
    PYTHON_MODULES: [
        'python/main.py',
        'python/instance_factory.py',
        'python/type_factory.py',
        'python/gost_data.py',
        'python/geometry_builder.py',
        'python/ifc_generator.py',
        'python/geometry_converter.py',
        'python/utils.py'
    ],

    // Таймауты
    PYODIDE_LOAD_TIMEOUT: 30000,

    // UI
    STATUS_DURATION: {
        success: 3000,
        error: 5000,
        info: 0
    },

    // Параметры болта по умолчанию
    DEFAULT_BOLT_PARAMS: {
        bolt_type: '1.1',
        execution: 1,
        diameter: 20,
        length: 800,
        material: '09Г2С'
    },

    // Цвета компонентов
    COMPONENT_COLORS: {
        STUD: 0x8B8B8B,
        WASHER: 0xA9A9A9,
        NUT: 0x696969,
        ANCHORBOLT: 0x4F4F4F
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APP_CONFIG;
}
