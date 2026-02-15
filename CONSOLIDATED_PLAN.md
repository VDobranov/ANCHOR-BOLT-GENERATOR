## **CONSOLIDATED_PLAN.md** 

Я создам для вас **консолидированный план**, слив лучшие аспекты всех трёх и разрешив противоречия. Вот структура:

### **0. Обзор решений противоречий**

| Противоречие | Решение | Отвечающий подход |
|---|---|---|
| **Типизация типов IFC** | Динамическое кэширование `get_or_create_type()` по параметрам (diameter, length, bolt_type, material) | DeepSeek/Claude + разрешение Qwen |
| **Структура Python модулей** | 9-модульная архитектура (type_factory, instance_factory, geometry_utils, pset_manager, material_manager, gost_data) | DeepSeek |
| **Структура JavaScript** | 3 основных файла (main.js, viewer.js, ifcBridge.js) | DeepSeek |
| **IFC версия** | IFC4 ADD2 TC1 (российский стандарт) | Все согласованы |

---

### **1. АРХИТЕКТУРА ПРИЛОЖЕНИЯ**

#### **1.1 Иерархия типов и инстансов IFC (окончательная)**

```
IfcProject (IFC4 ADD2 TC1)
└── IfcSite
    └── IfcBuilding
        └── IfcBuildingStorey
            └── IfcMechanicalFastener (Assembly: ANCHORBOLT)
                ├── IfcMechanicalFastener (Stud: USERDEFINED)
                ├── IfcMechanicalFastener (Nut #1: USERDEFINED) [опц.]
                ├── IfcMechanicalFastener (Washer #1: USERDEFINED) [опц.]
                ├── IfcMechanicalFastener (Nut #2: USERDEFINED) [опц.]
                └── IfcMechanicalFastener (Washer #2: USERDEFINED) [опц.]
```

**Ключевая особенность**: Типы (`IfcMechanicalFastenerType`) создаются **динамически и кэшируются** на основе уникальной комбинации `(bolt_type, execution, diameter, length, material)`. Таким образом, тип для болта М20×800 из стали 09Г2С создаётся один раз, а затем переиспользуется.

#### **1.2 Типо-инстансная модель (взаимодействие)**

- **Типы** содержат: полную геометрию, Property Sets, материалы
- **Инстансы** содержат: размещение в пространстве, ссылки на типы через `IfcRelDefinesByType`
- **Сборка** агрегирует все компоненты через `IfcRelAggregates`
- **Соединяющие отношения** между компонентами через `IfcRelConnectsElements`

---

### **2. СТРУКТУРА ПРОЕКТА (окончательная)**

```
anchor-bolt-generator/
│
├── index.html                  # Главная страница
├── style.css                   # Основные стили
│
├── js/                         # JavaScript слой (3 модуля)
│   ├── main.js                 # Оркестрация: форма, события, Pyodide
│   ├── viewer.js               # 3D визуализация (Three.js)
│   └── ifcBridge.js            # Communication layer (JS ↔ Python)
│
├── python/                     # Python слой (9 модулей)
│   ├── main.py                 # Точка входа Pyodide
│   ├── type_factory.py         # Создание и кэширование типов (get_or_create_*)
│   ├── instance_factory.py     # Создание инстансов и размещений
│   ├── ifc_generator.py        # Генерация IFC-файла (экспорт)
│   ├── geometry_builder.py     # Построение геометрии (IfcCompositeCurve, IfcExtrudedAreaSolid, профили)
│   ├── pset_manager.py         # Управление Property Sets (Pset_MechanicalFastenerCommon и др.)
│   ├── material_manager.py     # Создание и привязка IfcMaterial
│   ├── gost_data.py            # Справочники ГОСТ (параметры, валидация)
│   └── requirements.txt        # Зависимости Python
│
├── data/                       # JSON справочники (опционально, для быстрой загрузки)
│   ├── gost_24379_1_2012.json  # Параметры болтов по ГОСТ
│   └── gost_19281_2014.json    # Материалы
│
├── assets/
│   ├── icons/                  # SVG иконки
│   └── three.min.js            # Three.js библиотека (или CDN)
│
└── README.md
```

**Примечание**: Python модули загружаются один раз при инициализации Pyodide. JavaScript модули загружаются при старте приложения в браузере.

---

### **3. ДВУХЭТАПНАЯ АРХИТЕКТУРА ИНИЦИАЛИЗАЦИИ**

#### **Этап 1: Инициализация при загрузке (один раз)**
1. Загрузка Pyodide runtime в браузер (~50-80 MB)
2. Импорт Python модулей
3. **Создание базового Project/Site/Building/StoreyStructure** (пустая IFC модель)
4. Инициализация словаря для кэширования типов: `types_cache = {}`

#### **Этап 2: Генерация при каждом запросе пользователя**
1. Пользователь заполняет форму (тип, диаметр, длина, материал, количество гаек/шайб)
2. JavaScript вызывает Python функцию с параметрами
3. Python:
   - Валидирует параметры через `gost_data.py`
   - Получает или создаёт типы (тип шпильки, гайки, шайбы, сборки) через `type_factory`
   - Создаёт инстансы через `instance_factory`
   - Генерирует IFC и mesh-метаинформацию
4. JavaScript рендерит 3D и обновляет UI

---

### **4. УПРАВЛЕНИЕ ТИПАМИ (Кэширование)**

```python
# type_factory.py - псевдокод структуры

class TypeFactory:
    def __init__(self):
        self.types_cache = {}  # { (bolt_type, d, l, material): type_object }
    
    def get_or_create_stud_type(self, bolt_type, execution, diameter, length, material):
        key = ('stud', bolt_type, execution, diameter, length, material)
        if key not in self.types_cache:
            # Построить геометрию (IfcCompositeCurve + IfcSweptDiskSolid)
            # Создать IfcMechanicalFastenerType
            # Добавить Property Sets
            # Привязать материал
            self.types_cache[key] = new_type
        return self.types_cache[key]
    
    def get_or_create_nut_type(self, diameter, material):
        # Гайка зависит только от диаметра (высота, размер под ключ – из ГОСТ)
        key = ('nut', diameter, material)
        # ...
    
    def get_or_create_washer_type(self, diameter, material):
        # Шайба зависит только от диаметра
        key = ('washer', diameter, material)
        # ...
    
    def get_or_create_assembly_type(self, bolt_type, diameter, material):
        # Сборка зависит от типа болта и диаметра
        key = ('assembly', bolt_type, diameter, material)
        # ...
```

**Преимущество**: Если пользователь дважды создаст болт M20×800, тип создаётся один раз.

---

### **5. СПЕЦИФИКАЦИЯ IFCMECHANICALFASTENERTYPE (ОКОНЧАТЕЛЬНАЯ)**

| Элемент | PredefinedType | ElementType | Геометрия | Key PSets |
|---------|----------------|-------------|-----------|-----------|
| **Шпилька** | USERDEFINED | "STUD" | `IfcSweptDiskSolid` (IfcCompositeCurve + круглый профиль) | Pset_MechanicalFastenerCommon (NominalDiameter, NominalLength, ThreadLength) |
| **Гайка** | USERDEFINED | "NUT" | `IfcExtrudedAreaSolid` (шестиугольник с отверстием) | Pset_MechanicalFastenerCommon (NominalDiameter, Height) |
| **Шайба** | USERDEFINED | "WASHER" | `IfcExtrudedAreaSolid` (кольцо) | Pset_MechanicalFastenerCommon (NominalDiameter, OuterDiameter, Thickness) |
| **Сборка** | ANCHORBOLT | (опц. "ANCHORBOLT") | Отсутствует (представление определяется компонентами) | Pset_MechanicalFastenerCommon, Pset_ElementComponentCommon, Pset_ManufacturerTypeInformation |

Все типы привязаны к `IfcMaterial` ("09Г2С", "10Г2", и т.д.) через `IfcRelAssociatesMaterial`.

---

### **6. ГЕНЕРАЦИЯ ГЕОМЕТРИИ (geometry_builder.py)**

#### **6.1 Осевая линия шпильки (IfcCompositeCurve)**

**Для изогнутых болтов (тип 1.1):**
1. `IfcLine` - нижний прямой участок (от точки (0,0,0) до (0,0,R))
2. `IfcCircularArcSegment3D` - дугообразный участок (радиус R, центр (R,0,R))
3. `IfcLine` - верхний прямой участок (от (R,0,0) до (R,0,L-R))

**Для прямых болтов (тип 2.1, 5):**
- Один `IfcLine` от (0,0,0) до (0,0,L)

**Алгоритм:**
```python
def create_composite_curve(bolt_type, diameter, length):
    segments = []
    if has_bend(bolt_type):
        radius = calculate_bend_radius(bolt_type, diameter)  # из ГОСТ
        # Добавить сегменты...
        segments.append(IfcCompositeCurveSegment(..., IfcLine(...)))
        segments.append(IfcCompositeCurveSegment(..., IfcCircularArcSegment3D(...)))
        segments.append(IfcCompositeCurveSegment(..., IfcLine(...)))
    else:
        segments.append(IfcCompositeCurveSegment(..., IfcLine(...)))
    
    return IfcCompositeCurve(segments, SelfIntersect=False)
```

#### **6.2 Профили для гаек и шайб (IfcArbitraryProfileDefWithVoids)**

**Гайка (шестиугольник):**
- Внешний контур: 6 вершин правильного шестиугольника (размер под ключ S из ГОСТ)
- Внутреннее отверстие: круг с радиусом = диаметр резьбы / 2 + зазор

**Шайба (кольцо):**
- Внешний контур: круг с радиусом = наружный диаметр / 2
- Внутреннее отверстие: круг с радиусом = диаметр резьбы / 2 + зазор

---

### **7. ПРОЦЕСС ГЕНЕРАЦИИ ИНСТАНСОВ (instance_factory.py)**

**Входные параметры:**
```json
{
  "bolt_type": "1.1",
  "execution": 1,
  "diameter": 20,
  "length": 800,
  "material": "09Г2С",
  "has_bottom_nut": true,
  "has_top_nut": true,
  "has_washers": true
}
```

**Процесс:**

1. **Получить типы:**
   ```python
   stud_type = type_factory.get_or_create_stud_type(bolt_type, exec, d, l, material)
   nut_type = type_factory.get_or_create_nut_type(d, material)
   washer_type = type_factory.get_or_create_washer_type(d, material)
   assembly_type = type_factory.get_or_create_assembly_type(bolt_type, d, material)
   ```

2. **Создать инстансы с размещением:**
   - `stud_instance` → размещение (0,0,0) с осью Z вдоль болта
   - `washer_bottom_instance` → (0, 0, 0) - на нижнем торце
   - `nut_bottom_instance` → (0, 0, washer_thickness) - над нижней шайбой
   - `washer_top_instance` → (0, 0, length - washer_thickness)
   - `nut_top_instance` → (0, 0, length - washer_thickness - nut_height)

3. **Создать отношения:**
   - `IfcRelDefinesByType` для каждого инстанса
   - `IfcRelAggregates` (сборка → компоненты)
   - `IfcRelConnectsElements` (шпилька ↔ гайки/шайбы)

4. **Вернуть:**
   - IFC-строка (для экспорта)
   - Mesh-метаинформация (вершины, индексы, цвета для Three.js)

---

### **8. ОТНОШЕНИЯ МЕЖДУ ЭЛЕМЕНТАМИ (окончательная таблица)**

| Тип отношения | Применение | Пример |
|---|---|---|
| `IfcRelDefinesByType` | Каждый инстанс → его тип | stud_instance → stud_type |
| `IfcRelAggregates` | Сборка → компоненты | assembly_instance → [stud, nut_bottom, washer_bottom, nut_top, washer_top] |
| `IfcRelConnectsElements` | Физические соединения | stud ↔ nut_bottom, nut_bottom ↔ washer_bottom |
| `IfcRelAssociatesMaterial` | Типы → материал | [stud_type, nut_type, washer_type] → Material("09Г2С") |
| `IfcRelDefinesByProperties` | Типы/инстансы → PSets | stud_type → Pset_MechanicalFastenerCommon |

---

### **9. ИНТЕГРАЦИЯ с БРАУЗЕРОМ (JS/Python мост)**

#### **9.1 Инициализация (первый раз)**

```javascript
// main.js

async function initializeApp() {
    let pyodide = await loadPyodide();
    
    // Загрузить Python модули
    await pyodide.loadPackage(['ifcopenshell']);  // если нужно
    await pyodide.runPythonAsync(`
        import main as ifc_main
        ifc_main.initialize_base_document()  # Создать пустой Project/Site/Building/StoreyStructure
    `);
    
    setupThreeJS();
    setupFormListeners();
}
```

#### **9.2 Генерация при запросе**

```javascript
// main.js

async function generateBolt() {
    const params = {
        bolt_type: document.getElementById('boltType').value,
        execution: parseInt(document.getElementById('execution').value),
        diameter: parseInt(document.getElementById('diameter').value),
        length: parseInt(document.getElementById('length').value),
        material: document.getElementById('material').value,
        has_bottom_nut: document.getElementById('bottomNut').checked,
        has_top_nut: document.getElementById('topNut').checked,
        has_washers: document.getElementById('washers').checked
    };
    
    const result = await pyodide.runPythonAsync(`
        from instance_factory import generate_bolt_assembly
        ifc_str, mesh_data = generate_bolt_assembly(${JSON.stringify(params)})
        (ifc_str, mesh_data)
    `);
    
    // result[0] = IFC-строка
    // result[1] = { meshes: [ { vertices: [...], indices: [...], color: 0xRRGGBB } ] }
    
    viewer.updateMeshes(result[1]);
    currentIFCData = result[0];
}
```

---

### **10. ВИЗУАЛИЗАЦИЯ (viewer.js + Three.js)**

```javascript
// viewer.js

class IFCViewer {
    constructor(canvasElement) {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ canvas: canvasElement, antialias: true });
        
        // Освещение
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.6));
        this.scene.add(new THREE.DirectionalLight(0xffffff, 0.8));
        
        this.meshes = [];
    }
    
    updateMeshes(meshData) {
        // Очистить старые меши
        this.meshes.forEach(m => this.scene.remove(m));
        this.meshes = [];
        
        // Создать новые меши
        meshData.meshes.forEach(data => {
            const geometry = new THREE.BufferGeometry();
            geometry.setAttribute('position', new THREE.BufferAttribute(new Float32Array(data.vertices), 3));
            geometry.setIndex(new THREE.BufferAttribute(new Uint32Array(data.indices), 1));
            
            const material = new THREE.MeshPhongMaterial({ color: data.color });
            const mesh = new THREE.Mesh(geometry, material);
            
            this.scene.add(mesh);
            this.meshes.push({ mesh, id: data.id });  // id для выделения
        });
        
        this.render();
    }
    
    onObjectClick(event) {
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(new THREE.Vector2(event.clientX / window.innerWidth * 2 - 1, 
                                                  -(event.clientY / window.innerHeight * 2 - 1)), 
                               this.camera);
        
        const intersects = raycaster.intersectObjects(this.meshes.map(m => m.mesh));
        if (intersects.length > 0) {
            const selected = this.meshes.find(m => m.mesh === intersects[0].object);
            this.highlightElement(selected.id);
            this.showProperties(selected.id);  // → Python для получения свойств
        }
    }
    
    render() {
        this.renderer.render(this.scene, this.camera);
    }
}
```

---

### **11. ВАЛИДАЦИЯ ДАННЫХ (gost_data.py)**

```python
# gost_data.py

BOLT_TYPES = {
    '1.1': {'execution': [1, 2], 'has_bend': True},
    '1.2': {'execution': [1, 2], 'has_bend': True},
    '2.1': {'execution': [1], 'has_bend': False},
    '5': {'execution': None, 'has_bend': False}
}

AVAILABLE_DIAMETERS = [12, 16, 20, 24, 30, 36, 42, 48, 56, 64, 72, 80, 90, 100]

AVAILABLE_LENGTHS = {
    ('1.1', 1): {
        12: [400, 500, 630, 800, 1000, 1250],
        16: [500, 630, 800, 1000, 1250, 1600],
        20: [500, 630, 800, 1000, 1250, 1600],
        # ...
    },
    ('1.1', 2): { ... },
    # ...
}

BOLT_DIMENSIONS_SPEC = {
    16: {'thread_pitch': 2.0, 'nut_height': 15, 'washer_thickness': 3, 'washer_outer_diameter': 30, 's_width': 24},
    20: {'thread_pitch': 2.5, 'nut_height': 18, 'washer_thickness': 4, 'washer_outer_diameter': 37, 's_width': 30},
    # ... по таблицам ГОСТ
}

MATERIALS = {
    '09Г2С': {'gost': '19281-2014', 'tensile_strength': 490, 'density': 7850},
    'ВСт3пс2': {'gost': '535-88', 'tensile_strength': 345, 'density': 7850},
    # ...
}

def validate_parameters(bolt_type, execution, diameter, length, material):
    """Проверить, что параметры соответствуют ГОСТ"""
    if diameter not in AVAILABLE_DIAMETERS:
        raise ValueError(f"Диаметр {diameter} не поддерживается")
    if (bolt_type, execution) not in AVAILABLE_LENGTHS:
        raise ValueError(f"Тип болта {bolt_type} исполнение {execution} не существует")
    if length not in AVAILABLE_LENGTHS.get((bolt_type, execution), {}).get(diameter, []):
        raise ValueError(f"Длина {length} недоступна для М{diameter}")
    if material not in MATERIALS:
        raise ValueError(f"Материал {material} не в справочнике")
    return True
```

---

### **12. ЭТАПЫ РАЗРАБОТКИ (проверенный и консолидированный план)**

| # | Этап | Компоненты | Зависимости | Примерно (дни) |
|---|------|-----------|------------|--------|
| 1 | **Инфраструктура** | index.html, style.css, main.js (основа), Pyodide инициализация | — | 2 |
| 2 | **GOST Справочники** | gost_data.py с полными таблицами | Этап 1 | 2 |
| 3 | **Geometry Builder** | geometry_builder.py (кривые, профили, выдавливание) | Этап 1 | 3 |
| 4 | **Type Factory** | type_factory.py с кэшированием, create_swept_disk_solid, profiles | Этап 2, 3 | 4 |
| 5 | **Materials & PSets** | material_manager.py, pset_manager.py | Этап 4 | 2 |
| 6 | **Instance Factory** | instance_factory.py, расчёт позиций, отношения | Этап 4, 5 | 3 |
| 7 | **IFC Generator** | ifc_generator.py, экспорт в строку/файл | Этап 6 | 2 |
| 8 | **IFC Bridge & Form** | ifcBridge.js, form_handler (HTML форма), валидация UI | Этап 1, 7 | 2 |
| 9 | **Three.js Viewer** | viewer.js (3D сцена, меши, выделение, Raycaster) | Этап 1 | 3 |
| 10 | **Интеграция & UI** | Полная форма, panel свойств, Download кнопка | Этап 8, 9 | 2 |
| 11 | **Тестирование & Документация** | Валидация IFC, проверка геометрии, README | Все | 2 |
| **ИТОГО** | | | | **27 дней** |

---

### **13. КЛЮЧЕВЫЕ РЕШЕНИЯ И ОБОСНОВАНИЕ**

| Решение | Альтернатива | Почему выбрано |
|---------|-------------|---------|
| **Кэширование типов** | Создание типов один раз (статические размеры) | Гибкость для любых параметров пользователя + оптимизация (один раз на уникальный набор параметров) |
| **9 модулей Python** | 5 модулей (минимально) или 20+ (максимально) | Баланс между ясностью и простотой в начале разработки |
| **3 JS файла** | 1 большой или 10+ мелких | Ясное разделение ответственности (оркестрация, визуализация, коммуникация) |
| **IFC4 ADD2 TC1** | IFC4.0.2.1 | Российский стандарт, рекомендуется для РФ рынка |
| **Двухэтапная инициализация** | Всё создавать с нуля каждый раз | Производительность (Pyodide загружается один раз, ~2-3 сек) |

---

### **14. МИНИМАЛЬНЫЙ ТЕСТОВЫЙ CASE (MVP)**

**День 1-10 (MVP):**
- Создать болт типа 1.1, М20×800, сталь 09Г2С, *без гаек/шайб*
- Экспортировать IFC файл
- Показать 3D (одна шпилька)

**День 11-20 (Version 1.0):**
- Добавить гайки и шайбы (автоматический расчёт позиций)
- Полная форма с валидацией
- Выделение элементов в 3D и панель свойств

**День 21-27 (Polish):**
- Все остальные типы и исполнения болтов
- Все диаметры и материалы
- Тесты и документация

---

### **15. ИНСТРУМЕНТЫ И ВЕРСИИ (финальные)**

| Инструмент | Версия | Назначение |
|-----------|--------|-----------|
| Python | 3.11+ | IFC логика |
| Pyodide | 0.23.0+ | Браузерный Python runtime |
| IfcOpenShell | 0.7.0+ | Работа с IFC (через pip в Pyodide) |
| Three.js | r150+ | 3D визуализация |
| IFC Standard | IFC4 ADD2 TC1 | Russian standard for BIM |
| HTML/CSS/JS | ванильные (no frameworks) | Frontend |