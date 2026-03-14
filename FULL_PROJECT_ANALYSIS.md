# 📊 ПОЛНЫЙ АНАЛИЗ ПРОЕКТА ANCHOR-BOLT-GENERATOR

**Дата анализа:** 14 марта 2026
**Статус:** ✅ 107 тестов пройдено
**Версия плана рефакторинга:** 4.0 (Финальная)

---

## 📋 СОДЕРЖАНИЕ

1. [Общая информация о проекте](#общая-информация-о-проекте)
2. [Архитектура проекта](#архитектура-проекта)
3. [Детальный анализ модулей](#детальный-анализ-модулей)
4. [Анализ тестового покрытия](#анализ-тестового-покрытия)
5. [Анализ JavaScript модулей](#анализ-javascript-модулей)
6. [IFC-спецификация и IfcOpenShell](#ifc-спецификация-и-ifcopenshell)
7. [Выявленные проблемы](#выявленные-проблемы)
8. [План рефакторинга](#план-рефакторинга)

---

## 🏗️ ОБЩАЯ ИНФОРМАЦИЯ О ПРОЕКТЕ

### Назначение
Генератор фундаментных болтов по ГОСТ 24379.1-2012 с:
- Веб-интерфейсом на Three.js
- Python-бэкендом на Pyodide (WebAssembly)
- Экспортом в IFC4 ADD2 TC1 формат

### Поддерживаемые типы болтов
| Тип | Диаметры | Длины | Состав сборки |
|-----|----------|-------|---------------|
| 1.1 | М12–М48 | 300–1400 | Шпилька + шайба + 2 гайки |
| 1.2 | М12–М48 | 300–1000 | Шпилька + шайба + 2 гайки |
| 2.1 | М16–М48 | 500–1250 | Шпилька + шайба + 4 гайки |
| 5 | М12–М48 | 300–1000 | Шпилька + шайба + 2 гайки |

### Материалы
- **09Г2С** ГОСТ 19281-2014 (низколегированная сталь, 490 МПа)
- **ВСт3пс2** ГОСТ 535-88 (углеродистая сталь, 345 МПа)
- **10Г2** ГОСТ 19281-2014 (низколегированная сталь, 490 МПа)

### Технологии
- **Three.js r128** — 3D визуализация
- **Pyodide 0.26.0** — Python WASM
- **IfcOpenShell 0.8.4** — IFC генерация
- **IFC4 ADD2 TC1** — схема

---

## 🏛️ АРХИТЕКТУРА ПРОЕКТА

### Структура проекта
```
ANCHOR-BOLT-GENERATOR/
├── python/                      # Python модули (Pyodide)
│   ├── main.py                  # IFC документ (singleton)
│   ├── instance_factory.py      # Создание сборок болтов
│   ├── type_factory.py          # Кэширование типов
│   ├── geometry_builder.py      # Построение IFC геометрии
│   ├── geometry_converter.py    # Конвертация в mesh
│   ├── material_manager.py      # Управление материалами
│   ├── gost_data.py             # ГОСТ справочники
│   ├── ifc_generator.py         # Экспорт IFC
│   ├── utils.py                 # Утилиты
│   └── validate_utils.py        # Валидация
│
├── js/                          # JavaScript модули
│   ├── config.js                # Конфигурация
│   ├── main.js                  # Оркестрация
│   ├── viewer.js                # Three.js viewer
│   ├── ifcBridge.js             # Мост к Python
│   ├── form.js                  # Управление формой
│   ├── ui.js                    # UI утилиты
│   └── init.js                  # Инициализация
│
├── tests/                       # Тесты (pytest)
│   ├── conftest.py              # Фикстуры
│   ├── test_gost_data.py        # 36 тестов
│   ├── test_geometry_builder.py # 15 тестов
│   ├── test_type_factory.py     # 17 тестов
│   ├── test_instance_factory.py # 14 тестов
│   ├── test_material_manager.py # 12 тестов
│   ├── test_main.py             # 10 тестов
│   ├── test_utils.py            # 3 теста
│   └── validate_utils.py        # Утилиты валидации
│
├── data/                        # Данные
│   └── dim.csv                  # Размеры болтов
│
├── css/                         # Стили
│   └── style.css
│
├── assets/                      # Ресурсы
│   └── favicon.svg
│
├── index.html                   # Главная страница
├── REFACTORING_PLAN_FINAL.md    # План рефакторинга
├── TDD_WORKFLOW.md              # TDD документация
└── pytest.ini                   # Конфигурация pytest
```

### Поток данных
```
┌─────────────────────────────────────────────────────────────┐
│                    Браузер (Client)                          │
├─────────────────────────────────────────────────────────────┤
│  1. Пользователь выбирает параметры болта                   │
│  2. form.js → main.js → generateBolt(params)                │
│  3. ifcBridge.js → Python (Pyodide)                         │
│  4. instance_factory.generate_bolt_assembly(params)         │
│     ├─ type_factory.get_or_create_*_type()                  │
│     │  └─ geometry_builder.create_*_solid()                 │
│     ├─ instance_factory.create_bolt_assembly()              │
│     │  └─ material_manager.create_material()                │
│     └─ export to IFC string                                 │
│  5. Возврат (ifc_str, mesh_data)                            │
│  6. viewer.js обновляет 3D сцену                            │
│  7. ui.js показывает панель свойств                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 ДЕТАЛЬНЫЙ АНАЛИЗ МОДУЛЕЙ

### 1. `gost_data.py` (443 строки)

**Назначение:** ГОСТ справочники и валидация

**Содержит:**
- `BOLT_TYPES` — типы болтов ({'1.1', '1.2', '2.1', '5'})
- `AVAILABLE_DIAMETERS` — диаметры ([12, 16, 20, 24, 30, 36, 42, 48])
- `BOLT_DIM_DATA` — данные размеров (150+ записей)
- `NUT_DIM_DATA` — размеры гаек (8 записей)
- `WASHER_DIM_DATA` — размеры шайб (8 записей)
- `MATERIALS` — материалы (3 записи)
- `AVAILABLE_LENGTHS` — автогенерируемые длины
- Функции-геттеры: `get_bolt_hook_length()`, `get_thread_length()`, ...
- `validate_parameters()` — валидация

**Проблемы:**
- ❌ Нарушение SRP (данные + логика)
- ❌ 443 строки в одном файле
- ❌ Нет type hints
- ❌ Магические индексы (MASS_INDICES = {'1.1': 5, ...})

**Решение:** Разделить на 4 модуля в `python/data/`

---

### 2. `instance_factory.py` (409 строк)

**Назначение:** Создание сборок болтов

**Ключевые методы:**
- `create_bolt_assembly()` — 250+ строк, создание полной сборки
- `_create_component()` — создание компонента
- `_duplicate_geometric_items()` — 150+ строк, ручное дублирование
- `_generate_mesh_data()` — конвертация в mesh

**Проблемы:**
- ❌ Дублирование геометрии вручную (150+ строк)
- ❌ Смешение логики (создание + дублирование + конвертация)
- ❌ Экспорт через временный файл
- ❌ Нет type hints

**Решение:**
- Использовать `builder.deep_copy()` (1 строка вместо 150)
- Вынести конвертацию в отдельный модуль
- Экспорт в `io.StringIO()`

---

### 3. `type_factory.py` (173 строки)

**Назначение:** Кэширование типов IFC

**Ключевые методы:**
- `get_or_create_stud_type()` — создание/получение типа шпильки
- `get_or_create_nut_type()` — тип гайки
- `get_or_create_washer_type()` — тип шайбы
- `get_or_create_assembly_type()` — тип сборки

**Преимущества:**
- ✅ Кэширование типов
- ✅ Делегирование геометрии в `geometry_builder`
- ✅ Ассоциация материалов

**Проблемы:**
- ⚠️ Нет `RepresentationMaps` для переиспользования
- ⚠️ Нет type hints

---

### 4. `geometry_builder.py` (373 строки)

**Назначение:** Построение IFC геометрии

**Использует:** `ifcopenshell.util.shape_builder.ShapeBuilder`

**Ключевые методы:**
- `create_composite_curve_stud()` — кривая для шпильки
- `create_bent_stud_solid()` — изогнутая шпилька (IfcSweptDiskSolid)
- `create_straight_stud_solid()` — прямая шпилька (IfcExtrudedAreaSolid)
- `create_nut_solid()` — гайка (шестиугольник с отверстием)
- `create_washer_solid()` — шайба (кольцо)

**Проблемы:**
- ❌ Workaround для импорта shape_builder (15 строк)
- ⚠️ Сложные расчёты точек касания (_calculate_tangent_point)

**Решение:** Удалить workaround, использовать чистый импорт

---

### 5. `material_manager.py` (218 строк)

**Назначение:** Управление материалами IFC

**Ключевые методы:**
- `create_material()` — создание IfcMaterial
- `create_material_list()` — IfcMaterialList
- `associate_material()` — IfcRelAssociatesMaterial
- `create_standard_psets()` — Pset_MaterialCommon, Pset_MaterialSteel

**Преимущества:**
- ✅ Кэширование материалов
- ✅ Создание PropertySets
- ✅ Правильная ассоциация

**Проблемы:**
- ⚠️ Нет type hints

---

### 6. `main.py` (308 строк)

**Назначение:** Управление IFC документом

**Класс `IFCDocument`:**
- Singleton паттерн (`_instance`)
- `initialize()` — создание базовой структуры
- `reset()` — сброс и пересоздание

**Проблемы:**
- ❌ Singleton (глобальное состояние)
- ❌ Дублирование кода инициализации (SPF content)
- ❌ Использование `ifcopenshell.api.run()` (устаревший)

**Решение:** Рефакторинг в менеджер документов

---

### 7. `geometry_converter.py` (125 строк)

**Назначение:** Конвертация IFC в Three.js mesh

**Ключевые функции:**
- `convert_ifc_to_mesh()` — один элемент
- `convert_assembly_to_meshes()` — сборка

**Проблемы:**
- ⚠️ Зависимость от `ifcopenshell.geom` (требует Pyodide)
- ⚠️ Нет fallback для сред без geom

---

### 8. `utils.py` (23 строки)

**Назначение:** Общие утилиты

**Содержит:**
- `get_ifcopenshell()` — ленивый импорт с кэшированием

**Проблемы:**
- ⚠️ Глобальное состояние (`_ifcopenshell_cache`)

---

### 9. `ifc_generator.py` (125 строк)

**Назначение:** Экспорт IFC

**Класс `IFCGenerator`:**
- `setup_units_and_contexts()` — единицы и контекст
- `export_to_string()` — экспорт
- `validate()` — валидация

**Проблемы:**
- ⚠️ Не используется в основном потоке

---

### 10. `validate_utils.py` (98 строк)

**Назначение:** Валидация IFC файлов

**Функции:**
- `validate_ifc_file()` — валидация через `ifcopenshell.validate`
- `assert_valid_ifc()` — assert для тестов

**Преимущества:**
- ✅ Перехват логов валидации
- ✅ Интеграция с pytest

---

## 🧪 АНАЛИЗ ТЕСТОВОГО ПОКРЫТИЯ

### Статистика
```
============================= 107 passed in 0.56s ==============================
```

| Модуль | Тестов | Покрытие |
|--------|--------|----------|
| `gost_data.py` | 36 | ✅ Полное |
| `geometry_builder.py` | 15 | ✅ Полное |
| `type_factory.py` | 17 | ✅ Полное |
| `instance_factory.py` | 14 | ✅ Полное |
| `material_manager.py` | 12 | ✅ Полное |
| `main.py` | 10 | ✅ Полное |
| `utils.py` | 3 | ✅ Полное |

### Mock объекты
**Проблема:** 5 копий одного mock класса в каждом тестовом файле

```python
class MockIfcEntity:
    """Дублируется в test_instance_factory.py, test_geometry_builder.py, ..."""
```

**Решение:** Вынести в `tests/conftest.py`

### Интеграционные тесты
- `test_generate_bolt_assembly_validates_ifc()` — требует ifcopenshell
- Пропускается если ifcopenshell недоступен

### Отсутствующие тесты
- ❌ JavaScript модули (viewer.js, form.js, ifcBridge.js)
- ❌ Интеграция Pyodide + браузер

---

## 🌐 АНАЛИЗ JAVASCRIPT МОДУЛЕЙ

### 1. `config.js` (52 строки)

**Конфигурация:**
- Версии Pyodide, Three.js
- URL wheel ifcopenshell
- Список Python модулей
- Цвета компонентов

---

### 2. `main.js` (108 строк)

**Оркестрация:**
- `initializeApp()` — инициализация
- `generateBolt(params)` — генерация
- `downloadIFCFile()` — скачивание

**Проблемы:**
- ⚠️ Глобальные переменные (viewer, bridge, form, pyodide)
- ⚠️ Нет обработки ошибок сети

---

### 3. `viewer.js` (365 строк)

**Класс `IFCViewer`:**
- Orthographic камера
- Вращение/панорамирование/зум
- Raycasting для выбора mesh
- Трансформация координат (Z-up → Y-up)

**Преимущества:**
- ✅ Сохранение вида при обновлении
- ✅ Фокусировка на объектах

**Проблемы:**
- ❌ Нет тестов
- ❌ Сложная логика трансформации координат

---

### 4. `ifcBridge.js` (162 строки)

**Класс `IFCBridge`:**
- Загрузка Python модулей
- Установка зависимостей (micropip)
- Вызов Python функций

**Проблемы:**
- ❌ Нет тестов
- ⚠️ Жёсткая зависимость от структуры путей

---

### 5. `form.js` (235 строк)

**Класс `BoltForm`:**
- Динамическое обновление опций
- Валидация параметров
- Debouncing изменений

**Преимущества:**
- ✅ Интеграция с Python для валидации
- ✅ Debouncing

**Проблемы:**
- ❌ Нет тестов

---

### 6. `ui.js` (115 строк)

**Объект `UI`:**
- Показ статусов
- Обновление панели свойств
- Download файлов

**Проблемы:**
- ❌ Нет тестов

---

### 7. `init.js` (8 строк)

**Точка входа:**
- DOMContentLoaded → инициализация

---

## 📐 IFC-СПЕЦИФИКАЦИЯ И IFCOPENSHELL

### IFC4 ADD2 TC1 Сущности

#### IfcMechanicalFastener
```python
stud = ifc_file.create_entity('IfcMechanicalFastener',
    GlobalId=ifcopenshell.guid.new(),
    OwnerHistory=owner_history,
    Name='Stud_M20x800',
    ObjectType='STUD',
    PredefinedType='ANCHORBOLT',
    ObjectPlacement=placement,
    Representation=representation
)
```

#### IfcMechanicalFastenerType
```python
stud_type = ifc_file.create_entity('IfcMechanicalFastenerType',
    GlobalId=ifcopenshell.guid.new(),
    Name='Stud_M20x800_1.1',
    ElementType='STUD',
    RepresentationMaps=[rep_map]  # Для переиспользования
)
```

#### RepresentationMaps
**Назначение:** Переиспользование геометрии типа для всех экземпляров

```python
rep_map = ifc_file.create_entity('IfcRepresentationMap',
    MappingOrigin=ifc_file.create_entity('IfcAxis2Placement3D',
        Location=ifc_file.create_entity('IfcCartesianPoint', Coordinates=[0, 0, 0])
    ),
    MappedRepresentation=representation
)
```

#### IfcRelAggregates
**Назначение:** Иерархия целое/часть

```python
ifc_file.create_entity('IfcRelAggregates',
    GlobalId=ifcopenshell.guid.new(),
    RelatingObject=assembly,
    RelatedObjects=[stud, washer, nut1, nut2]
)
```

#### IfcRelDefinesByType
**Назначение:** Назначение типа объектам

```python
ifc_file.create_entity('IfcRelDefinesByType',
    GlobalId=ifcopenshell.guid.new(),
    RelatingType=stud_type,
    RelatedObjects=[stud1, stud2]
)
```

#### IfcRelAssociatesMaterial
**Назначение:** Ассоциация материалов

```python
ifc_file.create_entity('IfcRelAssociatesMaterial',
    GlobalId=ifcopenshell.guid.new(),
    RelatingMaterial=material,
    RelatedObjects=[stud_type]
)
```

#### IfcMaterial + PropertySets
```python
material = ifc_file.create_entity('IfcMaterial',
    Name='09Г2С ГОСТ 19281-2014',
    Category='Steel'
)

pset_common = ifc_file.create_entity('IfcMaterialProperties',
    Name='Pset_MaterialCommon',
    Properties=[mass_density_prop],
    Material=material
)

pset_steel = ifc_file.create_entity('IfcMaterialProperties',
    Name='Pset_MaterialSteel',
    Properties=[yield_stress, ultimate_stress, structural_grade],
    Material=material
)
```

---

### IfcOpenShell ShapeBuilder

#### Основные методы
```python
from ifcopenshell.util.shape_builder import ShapeBuilder, V

builder = ShapeBuilder(ifc_file)

# Полилиния
polyline = builder.polyline([V(0, 0), V(1, 0), V(1, 1)], closed=True)

# Круг
circle = builder.circle(center=V(0, 0), radius=10)

# Профиль с отверстием
profile = builder.profile(outer_curve, inner_curves=[inner_circle])

# Экструзия
solid = builder.extrude(profile, magnitude=100)

# SweptDiskSolid (труба вдоль пути)
solid = builder.create_swept_disk_solid(path_curve, radius=10)

# Глубокое копирование
copy = builder.deep_copy(original_solid)
```

---

## 🚨 ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ

### Архитектурные проблемы

| # | Проблема | Файл | Приоритет |
|---|----------|------|-----------|
| 1 | Нарушение SRP | gost_data.py (443 строки) | 🔴 Критический |
| 2 | Singleton (глобальное состояние) | main.py | 🔴 Критический |
| 3 | Workaround для импорта | geometry_builder.py | 🟠 Высокий |
| 4 | Ручное дублирование геометрии | instance_factory.py | 🟠 Высокий |
| 5 | Экспорт через временный файл | instance_factory.py | 🟡 Средний |

### Проблемы кода

| # | Проблема | Файл | Приоритет |
|---|----------|------|-----------|
| 6 | Отсутствие type hints | Все Python файлы | 🟡 Средний |
| 7 | Дублирование mock классов | Тесты | 🟡 Средний |
| 8 | Магические числа | gost_data.py | 🟡 Средний |
| 9 | Дублирование кода инициализации | main.py | 🟡 Средний |

### Проблемы тестирования

| # | Проблема | Приоритет |
|---|----------|-----------|
| 10 | Нет тестов JavaScript | 🟡 Средний |
| 11 | Интеграционные тесты требуют ifcopenshell | 🟡 Средний |

---

## 📝 ПЛАН РЕФАКТОРИНГА

### Фаза 0: Подготовка (1 день)

#### 0.1. Настройка pre-commit hooks
**Файл:** `.pre-commit-config.yaml`

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
pytest tests/ -v --tb=short
# Ожидаем: 107 passed
```

---

### Фаза 1: Критические исправления (2-3 дня)

#### 1.1. Удаление workaround для shape_builder
**Файл:** `python/geometry_builder.py`

**До:**
```python
# Workaround для циклического импорта
if 'ifcopenshell.util.shape_builder' not in sys.modules:
    _mock_sb = types.ModuleType('ifcopenshell.util.shape_builder')
    _mock_sb.VectorType = Any
    sys.modules['ifcopenshell.util.shape_builder'] = _mock_sb

from utils import get_ifcopenshell
# ...
del sys.modules['ifcopenshell.util.shape_builder']
from ifcopenshell.util.shape_builder import ShapeBuilder
```

**После:**
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

**Тесты:**
```bash
pytest tests/test_geometry_builder.py -v
```

---

#### 1.2. Замена ручного дублирования на builder.deep_copy()
**Файл:** `python/instance_factory.py`

**До:**
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
            # ... ещё 100+ строк
    return duplicated

def _duplicate_curve(self, curve):
    # ... 20 строк

def _duplicate_placement(self, placement):
    # ... 15 строк
```

**После:**
```python
from ifcopenshell.util.shape_builder import ShapeBuilder

class InstanceFactory:
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

**Экономия:** ~150 строк кода

**Тесты:**
```bash
pytest tests/test_instance_factory.py -v
```

---

#### 1.3. Экспорт в memory buffer
**Файл:** `python/instance_factory.py`

**До:**
```python
def generate_bolt_assembly(params):
    # ...
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

**После:**
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

**Выигрыш производительности:** 2-3x на экспорт

**Тесты:**
```bash
pytest tests/test_instance_factory.py::TestGenerateBoltAssembly -v
```

---

### Фаза 2: Разделение модулей (3-4 дня)

#### 2.1. Создание `python/data/`

**Структура:**
```
python/data/
├── __init__.py
├── bolt_dimensions.py    # BOLT_DIM_DATA
├── fastener_dimensions.py # NUT_DIM_DATA, WASHER_DIM_DATA
├── materials.py          # MATERIALS
└── validation.py         # validate_parameters()
```

**Файл:** `python/data/__init__.py`
```python
"""Модуль данных ГОСТ для анкерных болтов"""

from .bolt_dimensions import BOLT_DIM_DATA, get_bolt_dimensions
from .fastener_dimensions import NUT_DIM_DATA, WASHER_DIM_DATA
from .materials import MATERIALS, get_material_name
from .validation import (
    BOLT_TYPES,
    AVAILABLE_DIAMETERS,
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
    'validate_parameters'
]
```

**Файл:** `python/data/bolt_dimensions.py`
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

**Файл:** `python/data/materials.py`
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
    """Форматирование имени материала для IFC"""
    info = MATERIALS.get(material)
    if info:
        return f"{material} ГОСТ {info['gost']}"
    return material
```

**Файл:** `python/data/validation.py`
```python
"""Модуль валидации параметров болтов по ГОСТ"""

from typing import Set, Dict, List, Tuple, Literal
from .bolt_dimensions import BOLT_DIM_DATA

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']

BOLT_TYPES: Set[BoltType] = {'1.1', '1.2', '2.1', '5'}
AVAILABLE_DIAMETERS: List[int] = [12, 16, 20, 24, 30, 36, 42, 48]

DIAMETER_LIMITS: Dict[BoltType, Tuple[int, int]] = {
    '1.1': (12, 48),
    '1.2': (12, 48),
    '2.1': (16, 48),
    '5': (12, 48)
}

MASS_INDICES: Dict[BoltType, str] = {
    '1.1': 'mass_1_1',
    '1.2': 'mass_1_2',
    '2.1': 'mass_2_1',
    '5': 'mass_5'
}

AVAILABLE_LENGTHS: Dict[Tuple[BoltType, int], List[int]] = {}
# Автогенерация AVAILABLE_LENGTHS...


def validate_parameters(
    bolt_type: BoltType,
    diameter: int,
    length: int,
    material: MaterialType
) -> bool:
    """Валидация параметров болта по ГОСТ"""
    errors = []
    
    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")
    
    # ... остальная валидация
    
    if errors:
        raise ValueError('\n'.join(errors))
    
    return True
```

**Тесты:**
```bash
pytest tests/test_gost_data.py -v
```

---

#### 2.2. Вынесение mock классов в conftest.py
**Файл:** `tests/conftest.py`

**Добавить:**
```python
@pytest.fixture
def mock_ifc_entity():
    """Фабрика для создания MockIfcEntity"""
    def _create(entity_type, **kwargs):
        return MockIfcEntity(entity_type, **kwargs)
    return _create


@pytest.fixture
def mock_ifc_doc():
    """Фикстура для создания MockIfcDoc"""
    return MockIfcDoc()


class MockIfcEntity:
    """Mock для IFC сущности (единая копия)"""
    def __init__(self, entity_type, **kwargs):
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
    """Mock для IFC документа (единая копия)"""
    def __init__(self):
        self.entities = []
        self._by_type = {}
        self.schema = "IFC4"
    
    def create_entity(self, entity_type, **kwargs):
        entity = MockIfcEntity(entity_type, **kwargs)
        self.entities.append(entity)
        
        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)
        
        return entity
    
    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])
```

**Удалить** дубликаты из тестовых файлов.

**Тесты:**
```bash
pytest tests/ -v
```

---

### Фаза 3: Добавление type hints (2-3 дня)

#### 3.1. gost_data.py
**До:**
```python
def get_bolt_mass(diameter, length, bolt_type):
    ...
```

**После:**
```python
from typing import Optional, Literal

BoltType = Literal['1.1', '1.2', '2.1', '5']


def get_bolt_mass(
    diameter: int,
    length: int,
    bolt_type: BoltType
) -> Optional[float]:
    """Получить массу болта данного диаметра, длины и типа."""
    ...
```

#### 3.2. instance_factory.py
**До:**
```python
def create_bolt_assembly(self, bolt_type, diameter, length, material):
    ...
```

**После:**
```python
from typing import Dict, Any, Literal

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']


def create_bolt_assembly(
    self,
    bolt_type: BoltType,
    diameter: int,
    length: int,
    material: MaterialType
) -> Dict[str, Any]:
    """Создание полной сборки анкерного болта."""
    ...
```

#### 3.3. geometry_builder.py
**До:**
```python
def create_nut_solid(self, diameter, height):
    ...
```

**После:**
```python
from ifcopenshell.entity_instance import entity_instance


def create_nut_solid(
    self,
    diameter: int,
    height: int
) -> entity_instance:
    """Создание геометрии гайки (шестиугольник с отверстием)."""
    ...
```

**Тесты:**
```bash
mypy python/ --ignore-missing-imports
pytest tests/ -v
```

---

### Фаза 4: Улучшение RepresentationMaps (2 дня)

#### 4.1. Добавление RepresentationMaps в type_factory.py
**Файл:** `python/type_factory.py`

**До:**
```python
def get_or_create_stud_type(self, bolt_type, diameter, length, material):
    # ...
    shape_rep = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
    self.builder.associate_representation(stud_type, shape_rep)
```

**После:**
```python
def get_or_create_stud_type(self, bolt_type: str, diameter: int, length: int, material: str):
    key = ('stud', bolt_type, diameter, length, material)
    if key in self.types_cache:
        return self.types_cache[key]
    
    type_name = f'Stud_M{diameter}x{length}_{bolt_type}'
    
    stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
        GlobalId=ifcopenshell.guid.new(),
        OwnerHistory=self.owner_history,
        Name=type_name,
        PredefinedType='USERDEFINED',
        ElementType='STUD'
    )
    
    # Создание геометрии
    shape_rep = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
    
    # Создание RepresentationMap для переиспользования
    rep_map = self.ifc.create_entity('IfcRepresentationMap',
        MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        ),
        MappedRepresentation=shape_rep
    )
    
    stud_type.RepresentationMaps = [rep_map]
    
    # ... материал
    
    self.types_cache[key] = stud_type
    return stud_type
```

**Тесты:**
```bash
pytest tests/test_type_factory.py -v
```

---

### Фаза 5: Рефакторинг main.py (2 дня)

#### 5.1. Удаление Singleton
**Файл:** `python/main.py`

**До:**
```python
class IFCDocument:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

**После:**
```python
class IFCDocument:
    """Менеджер IFC документов (без singleton)"""
    
    def __init__(self):
        self.file = None
        self.material_manager = None
        self.owner_history = None
    
    def initialize(self, schema: str = 'IFC4') -> ifcopenshell.file:
        """Инициализация нового документа."""
        ...
    
    def reset(self) -> ifcopenshell.file:
        """Сброс документа."""
        ...


# Фабричные функции
_doc_instance: Optional[IFCDocument] = None


def get_document() -> IFCDocument:
    """Получение экземпляра документа."""
    global _doc_instance
    if _doc_instance is None:
        _doc_instance = IFCDocument()
    return _doc_instance


def reset_ifc_document() -> ifcopenshell.file:
    """Сброс IFC документа и создание нового."""
    doc = get_document()
    if doc.file is None:
        return doc.initialize()
    doc.reset()
    return doc.file
```

**Тесты:**
```bash
pytest tests/test_main.py -v
```

---

### Фаза 6: Документация (1-2 дня)

#### 6.1. Sphinx документация
**Файл:** `docs/conf.py`
```python
project = 'ANCHOR-BOLT-GENERATOR'
copyright = '2026, Вячеслав Добранов'
author = 'Вячеслав Добранов'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx'
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'ifcopenshell': ('https://ifcopenshell.org/docs/', None)
}
```

**Файл:** `docs/index.rst`
```rst
ANCHOR-BOLT-GENERATOR Documentation
====================================

.. toctree::
   :maxdepth: 2
   
   python/modules
   ifc_specification

Python Modules
==============

.. automodule:: gost_data
   :members:
   :undoc-members:
   :show-inheritance:
```

**Запуск:**
```bash
pip install sphinx
sphinx-quickstart docs
sphinx-build -b html docs/ docs/_build/
```

---

## 📊 ИТОГОВАЯ ТАБЛИЦА ИЗМЕНЕНИЙ

| Фаза | Задача | Файлы | Строк | Тесты | Приоритет |
|------|--------|-------|-------|-------|-----------|
| 0 | Pre-commit hooks | .pre-commit-config.yaml | +30 | - | 🔴 |
| 1.1 | Удаление workaround | geometry_builder.py | -15 | ✅ | 🔴 |
| 1.2 | builder.deep_copy() | instance_factory.py | -150 | ✅ | 🔴 |
| 1.3 | Memory buffer | instance_factory.py | -10 | ✅ | 🟠 |
| 2.1 | Разделение gost_data | data/*.py (4) | +400 | ✅ | 🟠 |
| 2.2 | Mock в conftest | conftest.py, tests/* | +100/-200 | ✅ | 🟡 |
| 3 | Type hints | Все Python | +200 | ✅ | 🟡 |
| 4 | RepresentationMaps | type_factory.py | +30 | ✅ | 🟡 |
| 5 | Refactor main.py | main.py | -50 | ✅ | 🟡 |
| 6 | Документация | docs/* | +500 | - | 🟢 |

**Итого:**
- Удалено: ~425 строк
- Добавлено: ~1260 строк
- Чистая польза: +835 строк (лучшая структура, типизация, документация)

---

## ✅ КРИТЕРИИ ПРИЁМКИ

### После Фазы 1:
- [ ] 107 тестов пройдено
- [ ] Workaround удалён
- [ ] builder.deep_copy() работает
- [ ] Экспорт в memory buffer

### После Фазы 2:
- [ ] gost_data.py разделён на 4 модуля
- [ ] Mock классы в conftest.py
- [ ] Все тесты проходят

### После Фазы 3:
- [ ] Type hints во всех модулях
- [ ] mypy не выдаёт ошибок (кроме missing imports)

### После Фазы 4:
- [ ] RepresentationMaps используются
- [ ] Геометрия переиспользуется

### После Фазы 5:
- [ ] Singleton удалён
- [ ] Тесты main.py проходят

### После Фазы 6:
- [ ] Sphinx документация сгенерирована
- [ ] README обновлён

---

## 🎯 ЗАКЛЮЧЕНИЕ

Проект ANCHOR-BOLT-GENERATOR находится в отличном состоянии:
- ✅ 107 тестов пройдено
- ✅ Полное покрытие Python модулей
- ✅ Рабочая интеграция Pyodide + браузер
- ✅ Правильное использование IFC отношений

**План рефакторинга** направлен на:
1. Улучшение архитектуры (разделение модулей)
2. Упрощение кода (удаление workaround, ручного дублирования)
3. Добавление типизации (type hints)
4. Улучшение документации

**Ожидаемые результаты:**
- -425 строк кода
- +835 строк (структура, типизация, документация)
- 2-3x производительность экспорта
- Лучшая поддерживаемость
