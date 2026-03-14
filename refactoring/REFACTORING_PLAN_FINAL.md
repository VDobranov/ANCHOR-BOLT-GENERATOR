# 📋 План рефакторинга ANCHOR-BOLT-GENERATOR

**Версия:** 3.0 (Объединённая)  
**Обновлено:** с учётом документации IfcOpenShell и полного анализа кода

---

## 🔍 Анализ текущего состояния проекта

### Общее описание
Проект представляет собой генератор фундаментных болтов по ГОСТ 24379.1-2012 с:
- ✅ Веб-интерфейсом на Three.js
- ✅ Python-бэкендом на Pyodide (WebAssembly)
- ✅ Экспортом в IFC4 ADD2 TC1 формат
- ✅ **107 passing тестами**

### Архитектура
```
┌─────────────────────────────────────────────────────────────┐
│                    Браузер (Client)                          │
├─────────────────────────────────────────────────────────────┤
│  JavaScript Layer:                                          │
│  - viewer.js (Three.js 3D)                                  │
│  - form.js (управление формой)                              │
│  - ifcBridge.js (мост к Python)                             │
│  - main.js (оркестрация)                                    │
│  - ui.js, init.js, config.js                                │
├─────────────────────────────────────────────────────────────┤
│  Pyodide (Python WASM):                                     │
│  - main.py (IFC документ)                                   │
│  - instance_factory.py (создание болтов)                    │
│  - type_factory.py (кэширование типов)                      │
│  - geometry_builder.py (IFC геометрия)                      │
│  - material_manager.py (материалы)                          │
│  - gost_data.py (ГОСТ справочники)                          │
│  - ifc_generator.py (экспорт IFC)                           │
│  - geometry_converter.py (конвертация в mesh)               │
│  - validate_utils.py (утилиты валидации)                    │
│  - utils.py (общие утилиты)                                 │
└─────────────────────────────────────────────────────────────┘
```

### Структура тестов
```
tests/
├── conftest.py              # Фикстуры и конфигурация pytest
├── test_utils.py            # Тесты utils.py (3 теста)
├── test_gost_data.py        # Тесты gost_data.py (36 тестов)
├── test_geometry_builder.py # Тесты geometry_builder.py (15 тестов)
├── test_type_factory.py     # Тесты type_factory.py (17 тестов)
├── test_instance_factory.py # Тесты instance_factory.py (14 тестов)
├── test_material_manager.py # Тесты material_manager.py (12 тестов)
├── test_main.py             # Тесты main.py (10 тестов)
└── validate_utils.py        # Утилиты валидации
```

---

## 🚨 Выявленные проблемы

### 1. **Архитектурные проблемы**

#### 1.1. Нарушение Single Responsibility Principle

**`gost_data.py` (1100+ строк):**
- Содержит данные (справочники): `BOLT_DIM_DATA`, `NUT_DIM_DATA`, `WASHER_DIM_DATA`
- Функции валидации: `validate_parameters()`
- Функции-геттеры для размеров: `get_bolt_hook_length()`, `get_thread_length()`, ...
- Константы материалов: `MATERIALS`
- **Решение**: Разделить на 4-5 модулей

**`instance_factory.py` (450+ строк):**
- Создание сборок болтов
- Дублирование геометрии (`_duplicate_geometric_items` — 150+ строк)
- Конвертация в mesh (`_generate_mesh_data`)
- Создание отношений IFC
- **Решение**: Вынести дублирование и конвертацию в отдельные модули

**`main.py` (350+ строк):**
- Singleton паттерн (`IFCDocument._instance`)
- Создание базовой структуры IFC
- Сброс документа (дублирование кода инициализации)
- **Решение**: Рефакторинг в менеджер документов

#### 1.2. Циклические зависимости

```python
# geometry_builder.py
from utils import get_ifcopenshell

# utils.py (ленивый импорт)
_ifcopenshell_cache = None
def get_ifcopenshell():
    global _ifcopenshell_cache
    ...

# main.py → type_factory.py → geometry_builder.py → utils.py
```

**Проблема**: Потенциальная циклическая зависимость при расширении

#### 1.3. Глобальное состояние

- Singleton в `main.py` (`IFCDocument._instance`)
- Глобальный кэш `_ifcopenshell_cache` в `utils.py`
- **Проблема**: Тесты могут влиять друг на друга, сложно тестировать изолированно

#### 1.4. Workaround для ifcopenshell

```python
# geometry_builder.py: mock VectorType перед импортом
if 'ifcopenshell.util.shape_builder' not in sys.modules:
    _mock_sb = types.ModuleType('ifcopenshell.util.shape_builder')
    _mock_sb.VectorType = Any
    sys.modules['ifcopenshell.util.shape_builder'] = _mock_sb
```

**Проблема**: 
- Хрупкая конструкция, может сломаться при обновлении ifcopenshell
- Создан в 2024 для обхода проблемы импорта в Pyodide
- **По документации IfcOpenShell**: `VectorType` — это псевдоним типа, не требует mock

---

### 2. **Проблемы кода**

#### 2.1. DRY (Don't Repeat Yourself)

**Дублирование создания OwnerHistory:**
```python
# main.py (reset method и initialize method)
timestamp = int(time.time())
spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','{time.strftime('%Y-%m-%dT%H:%M:%S')}',(''),(''),'IfcOpenShell 0.8.4','IfcOpenShell 0.8.4','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#6,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG','ABG',$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCORGANIZATION('ABG','ABG',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','Anchor Bolt Generator','ABG');
ENDSEC;
END-ISO-10303-21;
"""
```

**Дублирование создания сущностей:**
```python
# type_factory.py - создание материалов
mat_name = get_material_name(material)
mat = self.material_manager.create_material(mat_name, category='Steel', material_key=material)
self.material_manager.associate_material(stud_type, mat)

# instance_factory.py - тот же код
mat_name = get_material_name(material)
mat = self.material_manager.get_material(mat_name)
if mat:
    self.material_manager.associate_material(assembly, mat)
```

#### 2.2. Длинные методы

**`create_bolt_assembly` (250+ строк):**
- Смешивает создание компонентов, отношений, mesh данных
- Сложно тестировать отдельные аспекты
- **Решение**: Разбить на подметоды с понятными названиями

#### 2.3. Магические числа

```python
# gost_data.py
MASS_INDICES = {
    '1.1': 5,  # Почему 5?
    '1.2': 6,
    '2.1': 7,
    '5': 8
}

# instance_factory.py
z_pos = washer_thickness / 2  # Почему /2?
z_pos = length - washer_thickness / 2 - nut_height / 2  # Сложная формула
```

#### 2.4. Необработанные исключения

```python
# geometry_converter.py
try:
    import ifcopenshell.geom
    return ifcopenshell.geom
except ImportError:
    return None  # Просто игнорируем

# instance_factory.py
except Exception as e:
    print(f"Warning: Could not convert element {element.GlobalId}: {e}")
    return None
```

---

### 3. **Проблемы тестирования**

#### 3.1. Mock объекты в тестах

**Проблема**: 5 копий одного и того же mock класса

```python
# test_instance_factory.py, test_geometry_builder.py, test_type_factory.py,
# test_material_manager.py, test_main.py
class MockIfcEntity:
    """Дублируется в каждом тестовом файле"""
    def __init__(self, entity_type, *args, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        if entity_type == 'IfcMechanicalFastenerType':
            if not hasattr(self, 'RepresentationMaps'):
                self.RepresentationMaps = None

    def is_a(self):
        return self._entity_type

    def __getattr__(self, name):
        return self._kwargs.get(name)

    @property
    def dim(self):
        if '3D' in self._entity_type:
            return 3
        if '2D' in self._entity_type:
            return 2
        return 2
```

#### 3.2. Интеграционные тесты требуют ifcopenshell

```python
# test_instance_factory.py::TestGenerateBoltAssembly
def test_generate_bolt_assembly_validates_ifc(self):
    # Требует реальный ifcopenshell
    # Пропускается если недоступен
    try:
        result = generate_bolt_assembly(params)
        # ...
    except Exception:
        pytest.skip("ifcopenshell недоступен")
```

#### 3.3. Отсутствие тестов для JavaScript

- viewer.js, form.js, ifcBridge.js, ui.js не тестируются
- **Риск**: Регрессии в UI, сложно рефакторить

---

### 4. **Проблемы производительности**

#### 4.1. Дублирование геометрии

```python
# instance_factory.py
def _duplicate_geometric_items(self, items):
    # Для КАЖДОГО болта дублируется вся геометрия
    # Даже если типы закэшированы в type_factory
    
    # 150+ строк ручного копирования для каждого типа сущности
    duplicated = []
    for item in items:
        if item.is_a() == 'IfcSweptDiskSolid':
            directrix = self._duplicate_curve(item.Directrix)
            duplicated.append(self.ifc.create_entity('IfcSweptDiskSolid',
                Directrix=directrix, Radius=item.Radius
            ))
        elif item.is_a() == 'IfcExtrudedAreaSolid':
            # ... ещё 50+ строк
```

**Проблема**:
- 150+ строк сложного кода
- Поддержка всех типов сущностей вручную
- **По документации IfcOpenShell**: есть `builder.deep_copy(entity)`

#### 4.2. Экспорт через временный файл

```python
# instance_factory.py::generate_bolt_assembly
with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
    temp_path = f.name
ifc_doc.write(temp_path)
with open(temp_path, 'r') as f:
    ifc_str = f.read()
os.unlink(temp_path)
```

**Проблема**: 
- Дисковый I/O (медленно)
- Создание/удаление файлов
- **По документации IfcOpenShell**: `write()` поддерживает file-like объекты

---

### 5. **Проблемы документации и типизации**

#### 5.1. Отсутствие type hints

```python
# gost_data.py
def get_bolt_mass(diameter, length, bolt_type):  # Без типов
    ...

# Должно быть:
def get_bolt_mass(diameter: int, length: int, bolt_type: BoltType) -> float | None:
```

#### 5.2. Недостаточные docstrings

```python
# geometry_builder.py
def _calculate_tangent_point(center_x, center_z, diameter, point_x, point_z):
    """Находит точку касания окружности из внешней точки."""
    # Нет описания args, returns, exceptions
```

#### 5.3. Отсутствие документации API

- Нет Sphinx документации
- Нет примеров использования
- **Решение**: Генерация документации из type hints и docstrings

---

### 6. **Проблемы IFC-специфичные**

#### 6.1. Отсутствие RepresentationMaps

**Текущий подход:**
```python
# type_factory.py
stud_type = self.ifc.create_entity('IfcMechanicalFastenerType', ...)
shape_rep = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
self.builder.associate_representation(stud_type, shape_rep)
```

**Проблема**:
- Геометрия создаётся заново для каждого типа
- Нет переиспользования через RepresentationMap
- **По документации IFC4**: `RepresentationMaps` позволяет переиспользовать геометрию

#### 6.2. Ручное создание отношений вместо ifcopenshell.api

**Текущий код:**
```python
self.ifc.create_entity('IfcRelAggregates',
    GlobalId=ifc.guid.new(),
    OwnerHistory=owner_history,
    RelatingObject=assembly,
    RelatedObjects=components
)
```

**Примечание**: Текущий подход корректен, но `ifcopenshell.api.run()` помечен как устаревший.

---

## 📐 План рефакторинга

### **Фаза 0: Подготовка (1-2 дня)**

#### 0.1. Настройка pre-commit hooks

**Файл**: `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.13
  
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black"]
  
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=100"]
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ["--ignore-missing-imports"]
```

```bash
pip install pre-commit black isort flake8 mypy
pre-commit install
```

#### 0.2. Проверка тестов

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate
pytest tests/ -v --tb=short
# Ожидаем: 107 passed
```

#### 0.3. Настройка CI/CD (опционально)

**Файл**: `.github/workflows/tests.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install pytest ifcopenshell numpy
      - name: Run tests
        run: |
          pytest tests/ -v --cov=python --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

---

### **Фаза 1: Критические исправления (2-3 дня)**

#### 1.1. Удаление workaround для shape_builder

**Файл**: `python/geometry_builder.py`

**Шаги**:
1. Удалить mock код (15 строк)
2. Импортировать напрямую: `from ifcopenshell.util.shape_builder import ShapeBuilder, V`
3. Запустить тесты
4. Протестировать в браузере

**Код до**:
```python
# Workaround для циклического импорта VectorType (IfcOpenShell #7562):
# Создаём mock VectorType перед импортом shape_builder
import sys
import types

if 'ifcopenshell.util.shape_builder' not in sys.modules:
    _mock_sb = types.ModuleType('ifcopenshell.util.shape_builder')
    _mock_sb.VectorType = Any
    _mock_sb.V = lambda *coords: [float(c) for c in coords]
    sys.modules['ifcopenshell.util.shape_builder'] = _mock_sb

from ifcopenshell.util.shape_builder import ShapeBuilder

# Удаляем mock и импортируем реальный модуль
del sys.modules['ifcopenshell.util.shape_builder']
from ifcopenshell.util.shape_builder import ShapeBuilder
```

**Код после**:
```python
"""
geometry_builder.py — Построение IFC геометрии
Использует ifcopenshell.util.shape_builder для стандартного API
"""

from ifcopenshell.util.shape_builder import ShapeBuilder, V
from ifcopenshell.util.representation import get_context
from typing import Any


class GeometryBuilder:
    """Построитель IFC геометрии с использованием shape_builder"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.builder = ShapeBuilder(ifc_doc)
        self._context = None
```

**Приоритет**: 🔴 Критический  
**Сложность**: Низкая  
**Риск**: Минимальный (требуется тестирование в Pyodide)

---

#### 1.2. Замена ручного дублирования на builder.deep_copy()

**Файл**: `python/instance_factory.py`

**Шаги**:
1. Импортировать ShapeBuilder
2. Заменить `_duplicate_geometric_items` на одну строку
3. Удалить `_duplicate_curve`, `_duplicate_curve_segment`, `_duplicate_placement`, `_duplicate_direction`, `_duplicate_profile`
4. Запустить тесты

**Код до**:
```python
def _duplicate_geometric_items(self, items):
    """Дублирование геометрических элементов"""
    duplicated = []
    for item in items:
        if item.is_a() == 'IfcSweptDiskSolid':
            directrix = self._duplicate_curve(item.Directrix)
            duplicated.append(self.ifc.create_entity('IfcSweptDiskSolid',
                Directrix=directrix, Radius=item.Radius
            ))
        elif item.is_a() == 'IfcExtrudedAreaSolid':
            swept_area = self._duplicate_profile(item.SweptArea)
            position = self._duplicate_placement(item.Position)
            direction = self._duplicate_direction(item.ExtrudedDirection)
            duplicated.append(self.ifc.create_entity('IfcExtrudedAreaSolid',
                SweptArea=swept_area, Position=position,
                ExtrudedDirection=direction, Depth=item.Depth
            ))
        else:
            duplicated.append(item)
    return duplicated

def _duplicate_curve(self, curve):
    if curve.is_a() == 'IfcCompositeCurve':
        segments = [self._duplicate_curve_segment(s) for s in curve.Segments]
        return self.ifc.create_entity('IfcCompositeCurve',
            Segments=segments, SelfIntersect=curve.SelfIntersect
        )
    # ... ещё 100+ строк

def _duplicate_curve_segment(self, segment):
    # ... 20 строк

def _duplicate_placement(self, placement):
    # ... 15 строк

def _duplicate_direction(self, direction):
    # ... 5 строк

def _duplicate_profile(self, profile):
    # ... 10 строк
```

**Код после**:
```python
from ifcopenshell.util.shape_builder import ShapeBuilder

class InstanceFactory:
    # ...
    
    def _duplicate_geometric_items(self, items):
        """Дублирование геометрических элементов через ShapeBuilder"""
        builder = ShapeBuilder(self.ifc)
        return [builder.deep_copy(item) for item in items]
    
    # Удалить методы:
    # - _duplicate_curve
    # - _duplicate_curve_segment
    # - _duplicate_placement
    # - _duplicate_direction
    # - _duplicate_profile
```

**Приоритет**: 🔴 Критический  
**Сложность**: Низкая  
**Экономия**: ~150 строк кода

---

#### 1.3. Экспорт в memory buffer

**Файл**: `python/instance_factory.py`

**Шаги**:
1. Импортировать `io`
2. Заменить временный файл на `io.StringIO()`
3. Запустить тесты

**Код до**:
```python
def generate_bolt_assembly(params):
    from main import reset_ifc_document
    ifc_doc = reset_ifc_document()
    
    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(**params)
    
    # Экспорт через временный файл
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        temp_path = f.name
    
    ifc_doc.write(temp_path)
    
    with open(temp_path, 'r') as f:
        ifc_str = f.read()
    
    import os
    os.unlink(temp_path)
    
    return (ifc_str, result['mesh_data'])
```

**Код после**:
```python
import io
from instance_factory import InstanceFactory
from main import reset_ifc_document


def generate_bolt_assembly(params):
    """Главная функция для генерации болта"""
    ifc_doc = reset_ifc_document()
    
    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(**params)
    
    # Экспорт в memory buffer
    buffer = io.StringIO()
    ifc_doc.write(buffer)
    ifc_str = buffer.getvalue()
    
    return (ifc_str, result['mesh_data'])
```

**Приоритет**: 🟠 Высокий  
**Сложность**: Низкая  
**Выигрыш производительности**: 2-3x на экспорт

---

### **Фаза 2: Разделение модулей (3-4 дня)**

#### 2.1. Создание `python/data/`

**Структура**:
```
python/data/
├── __init__.py
├── bolt_dimensions.py    # BOLT_DIM_DATA, get_bolt_dimensions()
├── fastener_dimensions.py # NUT_DIM_DATA, WASHER_DIM_DATA
├── materials.py          # MATERIALS, get_material_name()
└── validation.py         # validate_parameters(), BOLT_TYPES, ...
```

**Файл**: `python/data/__init__.py`

```python
"""Модуль данных ГОСТ для анкерных болтов"""

from .bolt_dimensions import BOLT_DIM_DATA, get_bolt_dimensions
from .fastener_dimensions import NUT_DIM_DATA, WASHER_DIM_DATA
from .materials import MATERIALS, get_material_name
from .validation import (
    BOLT_TYPES,
    AVAILABLE_DIAMETERS,
    DIAMETER_LIMITS,
    AVAILABLE_LENGTHS,
    validate_parameters
)

__all__ = [
    'BOLT_DIM_DATA',
    'get_bolt_dimensions',
    'NUT_DIM_DATA',
    'WASHER_DIM_DATA',
    'MATERIALS',
    'get_material_name',
    'BOLT_TYPES',
    'AVAILABLE_DIAMETERS',
    'DIAMETER_LIMITS',
    'AVAILABLE_LENGTHS',
    'validate_parameters'
]
```

**Файл**: `python/data/bolt_dimensions.py`

```python
"""Модуль содержит данные размеров болтов из dim.csv"""

from typing import TypedDict, Optional, Dict, List

class BoltDimension(TypedDict):
    length: int
    hook_length: int
    bend_radius: int
    diameter: int
    thread_length: int
    mass_1_1: Optional[float]
    mass_1_2: Optional[float]
    mass_2_1: Optional[float]
    mass_5: Optional[float]
    l1: int
    l2: int
    l3: int
    r: int

BOLT_DIM_DATA: Dict[str, BoltDimension] = {
    "12_150": {
        "length": 150,
        "hook_length": 40,
        "bend_radius": 12,
        "diameter": 12,
        "thread_length": 80,
        "mass_1_1": None,
        "mass_1_2": None,
        "mass_2_1": None,
        "mass_5": 0.18,
        "l1": 100,
        "l2": 50,
        "l3": 25,
        "r": 8
    },
    # ... остальные данные
}

def get_bolt_dimensions(diameter: int, length: int) -> Optional[BoltDimension]:
    """Получить размеры болта по диаметру и длине"""
    key = f"{diameter}_{length}"
    return BOLT_DIM_DATA.get(key)
```

**Файл**: `python/data/materials.py`

```python
"""Модуль содержит данные о материалах по ГОСТ"""

from typing import TypedDict, Literal, Dict

class MaterialInfo(TypedDict):
    gost: str
    tensile_strength: int  # МПа
    yield_strength: int
    density: int  # кг/м³
    description: str

MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']

MATERIALS: Dict[MaterialType, MaterialInfo] = {
    '09Г2С': {
        'gost': '19281-2014',
        'tensile_strength': 490,
        'yield_strength': 390,
        'density': 7850,
        'description': 'Низколегированная сталь'
    },
    'ВСт3пс2': {
        'gost': '535-88',
        'tensile_strength': 345,
        'yield_strength': 235,
        'density': 7850,
        'description': 'Углеродистая конструкционная сталь'
    },
    '10Г2': {
        'gost': '19281-2014',
        'tensile_strength': 490,
        'yield_strength': 390,
        'density': 7850,
        'description': 'Низколегированная сталь'
    }
}

def get_material_name(material: MaterialType) -> str:
    """Форматирование имени материала для IFC
    
    Args:
        material: Тип материала (например, '09Г2С')
    
    Returns:
        Строка в формате: "09Г2С ГОСТ 19281-2014"
    """
    info = MATERIALS.get(material)
    if info:
        return f"{material} ГОСТ {info['gost']}"
    return material
```

**Файл**: `python/data/validation.py`

```python
"""Модуль валидации параметров болтов по ГОСТ"""

from typing import Set, Dict, List, Tuple, Literal
from .bolt_dimensions import BOLT_DIM_DATA

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']

# Типы болтов (допустимые значения)
BOLT_TYPES: Set[BoltType] = {'1.1', '1.2', '2.1', '5'}

# Доступные диаметры согласно ГОСТ (из dim.csv)
AVAILABLE_DIAMETERS: List[int] = [12, 16, 20, 24, 30, 36, 42, 48]

# Ограничения диаметров по типам болтов
DIAMETER_LIMITS: Dict[BoltType, Tuple[int, int]] = {
    '1.1': (12, 48),  # М12–М48
    '1.2': (12, 48),  # М12–М48
    '2.1': (16, 48),  # М16–М48
    '5': (12, 48)     # М12–М48
}

# Индексы масс по типам болтов
MASS_INDICES: Dict[BoltType, int] = {
    '1.1': 'mass_1_1',
    '1.2': 'mass_1_2',
    '2.1': 'mass_2_1',
    '5': 'mass_5'
}

# Доступные длины для каждой комбинации типа и диаметра
# Генерируется автоматически из BOLT_DIM_DATA на основе наличия массы
AVAILABLE_LENGTHS: Dict[Tuple[BoltType, int], List[int]] = {}

# Автогенерация AVAILABLE_LENGTHS из BOLT_DIM_DATA
for key, data in BOLT_DIM_DATA.items():
    diameter = int(key.split('_')[0])
    length = int(data['length'])
    
    for bolt_type in BOLT_TYPES:
        mass_key = MASS_INDICES[bolt_type]
        if data.get(mass_key) is not None:
            type_key = (bolt_type, diameter)
            if type_key not in AVAILABLE_LENGTHS:
                AVAILABLE_LENGTHS[type_key] = []
            if length not in AVAILABLE_LENGTHS[type_key]:
                AVAILABLE_LENGTHS[type_key].append(length)

# Сортировка длин
for type_key in AVAILABLE_LENGTHS:
    AVAILABLE_LENGTHS[type_key].sort()


def validate_parameters(
    bolt_type: BoltType,
    diameter: int,
    length: int,
    material: MaterialType
) -> bool:
    """Валидация параметров болта по ГОСТ
    
    Args:
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        material: Материал болта
    
    Raises:
        ValueError: Если параметры не валидны
    
    Returns:
        True если параметры валидны
    """
    errors = []
    
    # Validate bolt type
    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")
    
    # Validate diameter
    if diameter not in AVAILABLE_DIAMETERS:
        errors.append(f"Неподдерживаемый диаметр: М{diameter}")
    
    # Validate diameter limits for bolt type
    if bolt_type in DIAMETER_LIMITS:
        min_d, max_d = DIAMETER_LIMITS[bolt_type]
        if diameter < min_d or diameter > max_d:
            errors.append(f"Диаметр М{diameter} недоступен для типа {bolt_type}. "
                         f"Доступен диапазон: М{min_d}–М{max_d}")
    
    # Validate material
    from .materials import MATERIALS
    if material not in MATERIALS:
        errors.append(f"Неизвестный материал: {material}")
    
    # Validate length
    if bolt_type in BOLT_TYPES:
        key = (bolt_type, diameter)
        if key not in AVAILABLE_LENGTHS:
            errors.append(f"Комбинация типа {bolt_type} и диаметра М{diameter} не существует")
        elif length not in AVAILABLE_LENGTHS[key]:
            available = AVAILABLE_LENGTHS[key]
            errors.append(f"Длина {length} недоступна. Доступные длины: {available}")
        else:
            # Дополнительная проверка: масса для данного типа должна существовать
            dim_key = f"{diameter}_{length}"
            if dim_key in BOLT_DIM_DATA:
                mass_key = MASS_INDICES[bolt_type]
                if BOLT_DIM_DATA[dim_key].get(mass_key) is None:
                    errors.append(f"Болт типа {bolt_type} с параметрами М{diameter}×{length} "
                                 f"не существует (нет массы)")
    
    if errors:
        raise ValueError('\n'.join(errors))
    
    return True
```

---

#### 2.2. Создание `python/services/`

**Структура**:
```
python/services/
├── __init__.py
└── dimension_service.py  # get_bolt_hook_length(), get_thread_length(), ...
```

**Файл**: `python/services/dimension_service.py`

```python
"""Сервис для получения размеров болтов"""

from typing import Optional, Literal
from ..data.bolt_dimensions import BOLT_DIM_DATA

BoltType = Literal['1.1', '1.2', '2.1', '5']


def get_bolt_hook_length(diameter: int, length: int) -> Optional[int]:
    """Получить вылет крюка для болта данного диаметра и длины
    
    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
    
    Returns:
        Вылет крюка (мм) или None если болт не найден
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['hook_length']
    return None


def get_bolt_bend_radius(diameter: int, length: int) -> int:
    """Получить радиус загиба для болта данного диаметра и длины
    
    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
    
    Returns:
        Радиус загиба (мм), по умолчанию равен диаметру
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['bend_radius']
    return diameter  # По умолчанию


def get_thread_length(diameter: int, length: int) -> Optional[int]:
    """Получить длину резьбы для болта данного диаметра и длины
    
    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
    
    Returns:
        Длина резьбы (мм) или None если болт не найден
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['thread_length']
    return None


def get_bolt_l1(diameter: int, length: int) -> Optional[int]:
    """Получить l1 (длина верхнего участка) для болта"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l1']
    return None


def get_bolt_l2(diameter: int, length: int) -> Optional[int]:
    """Получить l2 (длина нижнего горизонтального участка) для болта"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l2']
    return None


def get_bolt_l3(diameter: int, length: int) -> Optional[int]:
    """Получить l3 (длина нижнего участка) для болта"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l3']
    return None


def get_bolt_mass(
    diameter: int,
    length: int,
    bolt_type: BoltType
) -> Optional[float]:
    """Получить массу болта данного диаметра, длины и типа
    
    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
    
    Returns:
        Масса в кг или None, если болт такого типа не существует
    """
    key = f"{diameter}_{length}"
    if key not in BOLT_DIM_DATA:
        return None
    
    data = BOLT_DIM_DATA[key]
    mass_key = f'mass_{bolt_type.replace(".", "_")}'
    return data.get(mass_key)
```

---

#### 2.3. Рефакторинг `gost_data.py`

**Шаги**:
1. Создать новые модули в `python/data/` и `python/services/`
2. Переместить данные и функции
3. Обновить импорты во всех файлах
4. Удалить `gost_data.py` (или оставить как wrapper для обратной совместимости)

**Файл**: `python/gost_data.py` (оставить как wrapper)

```python
"""
gost_data.py — Обратная совместимость
Все функции перемещены в python/data/ и python/services/
"""

# Импорты для обратной совместимости
from .data.bolt_dimensions import BOLT_DIM_DATA, AVAILABLE_DIAMETERS
from .data.fastener_dimensions import NUT_DIM_DATA, WASHER_DIM_DATA
from .data.materials import MATERIALS, get_material_name
from .data.validation import (
    BOLT_TYPES,
    DIAMETER_LIMITS,
    AVAILABLE_LENGTHS,
    validate_parameters
)
from .services.dimension_service import (
    get_bolt_hook_length,
    get_bolt_bend_radius,
    get_thread_length,
    get_bolt_l1,
    get_bolt_l2,
    get_bolt_l3,
    get_bolt_mass
)

__all__ = [
    'BOLT_DIM_DATA',
    'NUT_DIM_DATA',
    'WASHER_DIM_DATA',
    'MATERIALS',
    'get_material_name',
    'BOLT_TYPES',
    'AVAILABLE_DIAMETERS',
    'DIAMETER_LIMITS',
    'AVAILABLE_LENGTHS',
    'validate_parameters',
    'get_bolt_hook_length',
    'get_bolt_bend_radius',
    'get_thread_length',
    'get_bolt_l1',
    'get_bolt_l2',
    'get_bolt_l3',
    'get_bolt_mass'
]
```

---

### **Фаза 3: Улучшение геометрии (2-3 дня)**

#### 3.1. Добавление RepresentationMaps

**Файл**: `python/type_factory.py`

**Шаги**:
1. Импортировать `get_context`
2. Создать RepresentationMap при создании типа
3. Обновить `associate_representation` для использования Map

**Код**:
```python
from ifcopenshell.util.representation import get_context
from ifcopenshell.util.shape_builder import ShapeBuilder

class TypeFactory:
    def get_or_create_stud_type(self, bolt_type, diameter, length, material):
        key = ('stud', bolt_type, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]
        
        # Создание геометрии
        if bolt_type in ['1.1', '1.2']:
            solid = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
        else:
            solid = self.builder.create_straight_stud_solid(diameter, length)
        
        # Создание представления
        body_context = get_context(self.ifc, 'Model', 'Body', 'MODEL_VIEW')
        representation = self.builder.get_representation(body_context, [solid])
        
        # Создание RepresentationMap
        rep_map = self.ifc.create_entity('IfcRepresentationMap',
            MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0, 0, 0])
            ),
            MappedRepresentation=representation
        )
        
        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=f'Stud_M{diameter}x{length}_{bolt_type}',
            PredefinedType='USERDEFINED',
            ElementType='STUD',
            RepresentationMaps=[rep_map]
        )
        
        # ... материал и кэширование
        self.types_cache[key] = stud_type
        return stud_type
```

**Приоритет**: 🟠 Высокий  
**Сложность**: Средняя  
**Выигрыш**: Меньше дублирования геометрии в IFC файле

---

### **Фаза 4: Устранение циклических зависимостей (1 неделя)**

#### 4.1. Введение интерфейсов (Protocol)

**Файл**: `python/protocols.py`

```python
"""Protocol интерфейсы для dependency injection"""

from typing import Protocol, List, Any, Optional


class IfcDocumentProtocol(Protocol):
    """Протокол для IFC документа"""
    def create_entity(self, entity_type: str, *args, **kwargs) -> Any: ...
    def by_type(self, entity_type: str) -> List[Any]: ...
    def by_id(self, id: int) -> Any: ...
    def write(self, filepath: str) -> None: ...
    def remove(self, entity: Any) -> None: ...
    def get_inverse(self, entity: Any) -> List[Any]: ...
    def traverse(self, entity: Any, max_levels: int = None) -> List[Any]: ...


class GeometryBuilderProtocol(Protocol):
    """Протокол для построителя геометрии"""
    def create_bent_stud_solid(self, bolt_type: str, diameter: int, length: int) -> Any: ...
    def create_straight_stud_solid(self, diameter: int, length: int) -> Any: ...
    def create_nut_solid(self, diameter: int, height: int) -> Any: ...
    def create_washer_solid(self, inner_d: int, outer_d: int, thickness: int) -> Any: ...
    def deep_copy(self, entity: Any) -> Any: ...


class MaterialManagerProtocol(Protocol):
    """Протокол для менеджера материалов"""
    def create_material(self, name: str, category: str = None, material_key: str = None) -> Any: ...
    def get_material(self, name: str) -> Optional[Any]: ...
    def associate_material(self, entity: Any, material: Any) -> Any: ...
```

#### 4.2. Рефакторинг импортов

**Файл**: `python/geometry_builder.py`

```python
# До
from utils import get_ifcopenshell

# После
from ifcopenshell.util.shape_builder import ShapeBuilder, V
from ifcopenshell.util.representation import get_context
```

---

### **Фаза 5: Улучшение архитектуры (2 недели)**

#### 5.1. Введение Dependency Injection

**Файл**: `python/di.py`

```python
"""Dependency Injection контейнер"""

from typing import Optional
import ifcopenshell
from .type_factory import TypeFactory
from .instance_factory import InstanceFactory
from .material_manager import MaterialManager


class Container:
    """DI контейнер для приложения"""

    def __init__(self):
        self._ifc_doc: Optional[ifcopenshell.file] = None
        self._type_factory: Optional[TypeFactory] = None
        self._instance_factory: Optional[InstanceFactory] = None
        self._material_manager: Optional[MaterialManager] = None

    @property
    def ifc_document(self) -> ifcopenshell.file:
        if self._ifc_doc is None:
            self._ifc_doc = self._create_ifc_document()
        return self._ifc_doc

    @property
    def type_factory(self) -> TypeFactory:
        if self._type_factory is None:
            self._type_factory = TypeFactory(self.ifc_document)
        return self._type_factory

    @property
    def instance_factory(self) -> InstanceFactory:
        if self._instance_factory is None:
            self._instance_factory = InstanceFactory(
                self.ifc_document,
                self.type_factory
            )
        return self._instance_factory

    @property
    def material_manager(self) -> MaterialManager:
        if self._material_manager is None:
            self._material_manager = MaterialManager(self.ifc_document)
        return self._material_manager

    def _create_ifc_document(self) -> ifcopenshell.file:
        """Создание нового IFC документа"""
        return ifcopenshell.file(schema='IFC4')

    def reset(self):
        """Сброс контейнера"""
        self._ifc_doc = None
        self._type_factory = None
        self._instance_factory = None
        self._material_manager = None
```

#### 5.2. Рефакторинг singleton

**Файл**: `python/main.py`

```python
# До
class IFCDocument:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

# После
class IFCDocumentManager:
    """Менеджер IFC документов с поддержкой множественных документов"""

    def __init__(self):
        self._documents: dict[str, ifcopenshell.file] = {}
        self._current_id: Optional[str] = None

    def create_document(self, doc_id: str, schema: str = 'IFC4') -> ifcopenshell.file:
        """Создание нового документа"""
        doc = self._initialize_document(schema)
        self._documents[doc_id] = doc
        self._current_id = doc_id
        return doc

    def get_document(self, doc_id: str = None) -> ifcopenshell.file:
        """Получение документа по ID или текущего"""
        doc_id = doc_id or self._current_id
        if doc_id not in self._documents:
            raise ValueError(f"Документ {doc_id} не найден")
        return self._documents[doc_id]

    def reset_document(self, doc_id: str = None) -> ifcopenshell.file:
        """Сброс документа"""
        doc_id = doc_id or self._current_id
        # Удаление болтов, сохранение структуры
        ...
```

---

### **Фаза 6: Type hints и документация (1-2 недели)**

#### 6.1. Добавление type hints

**Файл**: `python/data/bolt_dimensions.py`

```python
from typing import TypedDict, Optional, Dict, List, Literal

BoltType = Literal['1.1', '1.2', '2.1', '5']

class BoltDimension(TypedDict):
    length: int
    hook_length: int
    bend_radius: int
    diameter: int
    thread_length: int
    mass_1_1: Optional[float]
    mass_1_2: Optional[float]
    mass_2_1: Optional[float]
    mass_5: Optional[float]
    l1: int
    l2: int
    l3: int
    r: int

BOLT_DIM_DATA: Dict[str, BoltDimension] = {...}
AVAILABLE_DIAMETERS: List[int] = [12, 16, 20, 24, 30, 36, 42, 48]
DIAMETER_LIMITS: Dict[BoltType, tuple[int, int]] = {...}
AVAILABLE_LENGTHS: Dict[tuple[BoltType, int], List[int]] = {...}
```

#### 6.2. Генерация документации

```bash
# Установка
pip install sphinx sphinx-autodoc-typehints myst-parser

# Генерация
sphinx-apidoc -o docs/source python/
sphinx-build -b html docs/source docs/build
```

---

### **Фаза 7: Тесты (1 неделя)**

#### 7.1. Перемещение Mock объектов в conftest.py

**Файл**: `tests/conftest.py`

```python
"""Конфигурация и фикстуры для pytest тестов"""
import sys
import os
import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))


class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type, *args, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        if entity_type == 'IfcMechanicalFastenerType':
            if not hasattr(self, 'RepresentationMaps'):
                self.RepresentationMaps = None

    def is_a(self):
        return self._entity_type

    def __getattr__(self, name):
        return self._kwargs.get(name)

    @property
    def dim(self):
        if '3D' in self._entity_type:
            return 3
        if '2D' in self._entity_type:
            return 2
        return 2


class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities = []
        self._by_type = {}
        self.schema = "IFC4"

    def create_entity(self, entity_type, *args, **kwargs):
        entity = MockIfcEntity(entity_type, *args, **kwargs)
        self.entities.append(entity)
        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)
        return entity

    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])

    def __getattr__(self, name):
        if name.startswith('create'):
            entity_type = name[6:]
            def create_method(*args, **kwargs):
                return self.create_entity(entity_type, *args, **kwargs)
            return create_method
        raise AttributeError(f"'MockIfcDoc' object has no attribute '{name}'")


@pytest.fixture
def mock_ifc_entity():
    """Фабрика MockIfcEntity"""
    return MockIfcEntity


@pytest.fixture
def mock_ifc_doc():
    """Mock для IFC документа"""
    return MockIfcDoc()


@pytest.fixture(scope='session')
def python_path():
    """Возвращает путь к python модулям"""
    return os.path.join(os.path.dirname(__file__), '..', 'python')


@pytest.fixture(scope='function')
def valid_bolt_params():
    """Параметры валидного болта по умолчанию"""
    return {
        'bolt_type': '1.1',
        'diameter': 20,
        'length': 800,
        'material': '09Г2С'
    }


@pytest.fixture(scope='function')
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ['1.1', '1.2', '2.1', '5']


@pytest.fixture(scope='function')
def all_diameters():
    """Все доступные диаметры"""
    return [12, 16, 20, 24, 30, 36, 42, 48]


@pytest.fixture(scope='function')
def all_materials():
    """Все доступные материалы"""
    return ['09Г2С', 'ВСт3пс2', '10Г2']
```

---

### **Фаза 8: JavaScript рефакторинг (2 недели)**

#### 8.1. Модульная структура

```
js/
├── core/
│   ├── app.js          # Инициализация приложения
│   └── config.js       # Конфигурация
├── ui/
│   ├── form.js         # Управление формой
│   ├── viewer.js       # 3D viewer
│   └── status.js       # Статусы и уведомления
├── bridge/
│   ├── pyodide.js      # Pyodide загрузка
│   └── ifcBridge.js    # Python мост
└── utils/
    └── helpers.js      # Вспомогательные функции
```

#### 8.2. Добавление тестов

**Файл**: `tests/js/test_viewer.test.js`

```javascript
import { IFCViewer } from '../../js/viewer.js';

describe('IFCViewer', () => {
    let canvas;
    
    beforeEach(() => {
        canvas = document.createElement('canvas');
        canvas.width = 800;
        canvas.height = 600;
        document.body.appendChild(canvas);
    });
    
    afterEach(() => {
        document.body.removeChild(canvas);
    });
    
    test('should initialize with canvas', () => {
        const viewer = new IFCViewer(canvas);
        expect(viewer).toBeDefined();
        expect(viewer.scene).toBeDefined();
        expect(viewer.camera).toBeDefined();
        expect(viewer.renderer).toBeDefined();
    });
    
    test('should transform vertices correctly', () => {
        const viewer = new IFCViewer(canvas);
        const vertices = [0, 0, 0, 1, 1, 1];
        const transformed = viewer.transformVerticesForThreeJS(vertices);
        expect(transformed).toEqual([0, 0, 0, 1000, -1000, -1000]);
    });
});
```

---

## 📊 Метрики успеха

### До рефакторинга:
| Метрика | Значение |
|---------|----------|
| Тестов | 107 |
| Coverage | ~75% |
| Строк кода (Python) | ~3500 |
| Type coverage | 0% |
| Mock файлов | 5 |
| Критических проблем | 6 |

### После рефакторинга:
| Метрика | Цель |
|---------|------|
| Тестов | 150+ (включая JavaScript) |
| Coverage | 90%+ |
| Строк кода (Python) | ~2800 (-20%) |
| Type coverage | 90%+ |
| Mock файлов | 1 |
| Критических проблем | 0 |

---

## 📅 Дорожная карта

| Фаза | Длительность | Результат |
|------|--------------|-----------|
| **0** | 1-2 дня | Pre-commit, CI/CD, проверка тестов |
| **1** | 2-3 дня | Удаление workaround, deep_copy, memory buffer |
| **2** | 3-4 дня | Разделение gost_data.py на модули |
| **3** | 2-3 дня | RepresentationMaps для геометрии |
| **4** | 1 неделя | Protocol интерфейсы, устранение циклических зависимостей |
| **5** | 2 недели | DI контейнер, рефакторинг singleton |
| **6** | 1-2 недели | Type hints, Sphinx документация |
| **7** | 1 неделя | Mock объекты в conftest.py |
| **8** | 2 недели | JavaScript модули и тесты |

**Итого**: 10-12 недель (~2.5-3 месяца)

---

## ⚠️ Риски

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Регрессии | Средняя | Высокое | Полное покрытие тестами (107 тестов уже есть) |
| Pyodide совместимость | Средняя | Критическое | Тестирование в браузере после каждого изменения |
| Время | Высокая | Среднее | Начать с критических исправлений (Фаза 1) |
| Совместимость API | Низкая | Высокое | Поэтапный рефакторинг с wrapper для обратной совместимости |

---

## 🎯 Приоритеты

### 🔴 Критические (сделать немедленно):
1. Удалить workaround для shape_builder
2. Заменить ручное дублирование на `builder.deep_copy()`
3. Экспорт в memory buffer вместо временного файла
4. Вынести Mock объекты в `conftest.py`

### 🟠 Важные:
5. Разделить `gost_data.py` на модули
6. Добавить `RepresentationMaps` для переиспользования геометрии
7. Type hints во все модули
8. Устранить циклические зависимости

### 🟡 Желательные:
9. DI контейнер
10. Рефакторинг singleton в менеджер документов
11. Sphinx документация
12. JavaScript тесты

---

## 📝 Заключение

### Текущее состояние проекта:
- ✅ **107 passing тестов** — отличное покрытие
- ✅ **Рабочий функционал** — генерация болтов по ГОСТ
- ✅ **TDD подход** — документированный workflow
- ✅ **Понятная структура** — Python/JS разделены

### Потенциал для улучшения:
- 🔸 **Модульность** — разделение gost_data.py (1100+ строк)
- 🔸 **Типизация** — 0% type coverage
- 🔸 **Производительность** — memory buffer, deep_copy
- 🔸 **Документация** — Sphinx, type hints

### После рефакторинга код станет:
- **Проще**: -700 строк кода (-20%)
- **Быстрее**: 2-3x на экспорт
- **Надёжнее**: стандартное API IfcOpenShell
- **Поддерживаемее**: модульная структура, type hints, документация
- **Тестируемее**: единые mock объекты, JavaScript тесты

---

## 📚 Приложения

### A. IfcOpenShell документация

**Основные методы:**
- `ifcopenshell.file.create_entity()` — создание сущностей
- `ifcopenshell.file.by_type()` — поиск по типу
- `ifcopenshell.file.write()` — запись в файл (поддерживает file-like объекты)

**ShapeBuilder:**
- `polyline()` — создание IfcIndexedPolyCurve
- `circle()` — создание IfcCircle
- `profile()` — создание профиля
- `extrude()` — создание IfcExtrudedAreaSolid
- `create_swept_disk_solid()` — создание IfcSweptDiskSolid
- `deep_copy()` — глубокое копирование геометрии

### B. IFC4 Relationships

**IfcRelAggregates:**
- `RelatingObject` — целый объект (агрегат)
- `RelatedObjects` — части (SET [1:?])

**IfcRelDefinesByType:**
- `RelatingType` — определение типа
- `RelatedObjects` — объекты (SET [1:?])

**IfcRelAssociatesMaterial:**
- `RelatingMaterial` — материал
- `RelatedObjects` — элементы (SET [1:?])

### C. Pre-commit конфигурация

См. раздел 0.1.

### D. CI/CD конфигурация

См. раздел 0.3.
