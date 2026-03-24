/**
 * Jest setup file
 * Настройка окружения для тестов
 */

/* eslint-disable no-undef */

// Mock для THREE.js
global.THREE = {
    Scene: () => ({
        background: null,
        add: () => {},
        remove: () => {}
    }),
    OrthographicCamera: () => ({
        position: { x: 0, y: 0, z: 1000 },
        up: { set: () => {} },
        lookAt: () => {},
        left: -100,
        right: 100,
        top: 100,
        bottom: -100,
        updateProjectionMatrix: () => {}
    }),
    WebGLRenderer: () => ({
        setSize: () => {},
        setPixelRatio: () => {},
        render: () => {},
        shadowMap: { enabled: false }
    }),
    AmbientLight: () => ({}),
    DirectionalLight: () => ({
        position: { set: () => {} },
        castShadow: false,
        shadow: { mapSize: { width: 0, height: 0 } }
    }),
    GridHelper: () => ({}),
    AxesHelper: () => ({}),
    Raycaster: () => ({
        setFromCamera: () => {},
        intersectObjects: () => []
    }),
    Vector3: (x = 0, y = 0, z = 0) => ({
        x,
        y,
        z,
        set: () => {},
        copy: () => {},
        length: () => 1000,
        subVectors: () => ({ length: () => 1000 })
    }),
    BufferGeometry: () => ({
        setAttribute: () => {},
        setIndex: () => {},
        computeVertexNormals: () => {},
        dispose: () => {}
    }),
    BufferAttribute: (arr) => arr,
    MeshPhongMaterial: () => ({
        dispose: () => {},
        emissive: { setHex: () => {}, intensity: 0 }
    }),
    Mesh: () => ({
        geometry: { dispose: () => {} },
        material: { dispose: () => {}, emissive: { setHex: () => {} } },
        castShadow: false,
        receiveShadow: false
    }),
    DoubleSide: 2,
    Box3: () => ({
        setFromObject: () => {},
        getCenter: (v) => v,
        getSize: () => ({ x: 100, y: 100, z: 100 }),
        expandByObject: () => {}
    })
};

// Mock для APP_CONFIG
global.APP_CONFIG = {
    PYODIDE_VERSION: '0.26.0',
    PYODIDE_URL: 'https://cdn.jsdelivr.net/pyodide/dev/full/pyodide.js',
    THREE_JS_URL: 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js',
    IFCOPENSHELL_WHEEL_URL: 'https://example.com/ifcopenshell.whl',
    PYTHON_MODULES: ['python/main.py'],
    PYODIDE_LOAD_TIMEOUT: 30000,
    STATUS_DURATION: {
        success: 3000,
        error: 5000,
        info: 0
    },
    DEFAULT_BOLT_PARAMS: {
        bolt_type: '1.1',
        diameter: 20,
        length: 800,
        material: '09Г2С'
    },
    COMPONENT_COLORS: {
        STUD: 0x8b8b8b,
        WASHER: 0xa9a9a9,
        NUT: 0x696969,
        ANCHORBOLT: 0x4f4f4f
    }
};

// Mock для UI
global.UI = {
    showStatus: () => {},
    toggle: () => {},
    toggleDownloadButton: () => {},
    downloadFile: () => {},
    hideStatus: () => {},
    updatePropertiesPanel: () => {},
    generateFilename: () => 'bolt.ifc'
};

// Mock для loadPyodide
global.loadPyodide = () =>
    Promise.resolve({
        loadPackage: () => Promise.resolve(),
        runPython: () => {},
        runPythonAsync: () => Promise.resolve(),
        FS: {
            mkdir: () => {},
            writeFile: () => {}
        },
        globals: {
            get: () => {}
        }
    });

// Mock для initializeIFCBridge
global.initializeIFCBridge = () =>
    Promise.resolve({
        initialize: () => Promise.resolve(),
        generateBolt: () => Promise.resolve({ status: 'success', meshData: {}, ifcData: 'IFC' }),
        getIFCData: () => 'IFC'
    });

// Mock для BoltForm
global.BoltForm = () => ({
    init: () => Promise.resolve(),
    getParams: () => ({ bolt_type: '1.1', diameter: 20, length: 800, material: '09Г2С' }),
    setParams: () => {}
});

// Mock для IFCExportSettings
global.IFCExportSettings = () => ({
    getSettings: () => ({
        assemblyClass: 'IfcMechanicalFastener',
        assemblyMode: 'separate',
        geometryType: 'solid'
    }),
    setSettings: () => {}
});

// Mock для IFCViewer
global.IFCViewer = () => ({
    updateMeshes: () => {},
    updateMeshesAndFocus: () => {},
    initializeCameraFocus: () => {}
});

// CustomEvent mock
global.CustomEvent = (type, detail) => ({ type, ...detail });

// window mock
global.window = {
    addEventListener: () => {},
    dispatchEvent: () => {},
    devicePixelRatio: 1
};

// document mock
global.document = {
    getElementById: () => ({
        addEventListener: () => {},
        dispatchEvent: () => {},
        value: '',
        disabled: false,
        classList: {
            add: () => {},
            remove: () => {},
            toggle: () => {},
            contains: () => false
        },
        style: { display: '' },
        textContent: '',
        innerHTML: ''
    }),
    querySelector: () => null,
    querySelectorAll: () => [],
    createElement: () => ({
        setAttribute: () => {},
        style: { display: 'none' },
        click: () => {},
        classList: {
            add: () => {},
            remove: () => {},
            toggle: () => {},
            contains: () => {}
        }
    }),
    body: {
        innerHTML: '',
        appendChild: () => {},
        removeChild: () => {},
        addEventListener: () => {}
    }
};

// requestAnimationFrame mock
global.requestAnimationFrame = (cb) => setTimeout(cb, 16);
