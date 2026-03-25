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
    IFCOPENSHELL_WHEEL_URL:
        'https://raw.githubusercontent.com/vdobranov/anchor-bolt-generator/main/wheels/ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl',

    // Python модули для загрузки
    PYTHON_MODULES: [
        'python/main.py',
        'python/document_manager.py',
        'python/protocols.py',
        'python/container.py',
        'python/material_manager.py',
        'python/instance_factory.py',
        'python/type_factory.py',
        'python/gost_data.py',
        'python/geometry_builder.py',
        'python/ifc_generator.py',
        'python/geometry_converter.py',
        'python/utils.py',
        'python/validate_utils.py',
        'python/data/__init__.py',
        'python/data/bolt_dimensions.py',
        'python/data/fastener_dimensions.py',
        'python/data/materials.py',
        'python/data/validation.py',
        'python/services/__init__.py',
        'python/services/dimension_service.py'
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
        diameter: 20,
        length: 800,
        material: '09Г2С'
    },

    // Цвета компонентов
    COMPONENT_COLORS: {
        STUD: 0x8b8b8b,
        WASHER: 0xa9a9a9,
        NUT: 0x696969,
        ANCHORBOLT: 0x4f4f4f
    }
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APP_CONFIG;
}
