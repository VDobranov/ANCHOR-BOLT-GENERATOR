# ANCHOR-BOLT-GENERATOR — Контекст проекта

## Обзор проекта

**Генератор анкерных болтов** — браузерное приложение для создания фундаментных болтов по **ГОСТ 24379.1-2012** с экспортом в **IFC4 ADD2 TC1** и **3D-визуализацией** через Three.js.

### Основные возможности
- ✅ Создание анкерных болтов по ГОСТ 24379.1-2012
- ✅ 3D-визуализация в браузере через Three.js (ортографическая камера)
- ✅ Экспорт в IFC (Industry Foundation Classes) для BIM-процессов
- ✅ Работа полностью в браузере (Python через Pyodide WebAssembly)
- ✅ Динамическое кэширование типов для оптимизации размера IFC
- ✅ Полная валидация параметров по ГОСТ
- ✅ Автоматическое определение состава сборки по типу болта
- ✅ Конвертация геометрии через `ifcopenshell.geom` (единый источник истины)
- ✅ Валидация IFC согласно спецификации (MappedRepresentation)

### Поддерживаемые типы болтов

| Тип | Форма | Диаметры | Длины |
|-----|-------|----------|-------|
| 1.1 | Изогнутый | М12–М48 | 300–1400 |
| 1.2 | Изогнутый | М12–М48 | 300–1000 |
| 2.1 | Прямой | М16–М48 | 500–1250 |
| 5 | Прямой | М12–М48 | 300–1000 |

**Примечание:** Исполнение определяется автоматически по типу болта (1.1 → исполнение 1, 1.2 → исполнение 2, и т.д.).

### Состав сборки (автоматически)
- **Типы 1.1, 1.2, 5**: шпилька + верхняя шайба + 2 верхних гайки
- **Тип 2.1**: шпилька + верхняя шайба + 2 верхних гайки + 2 нижних гайки

---

## Структура проекта (после рефакторинга 2026)

```
ANCHOR-BOLT-GENERATOR/
├── index.html              # Главная HTML-страница (русский UI)
├── style.css               # Стили приложения
├── README.md               # Пользовательская документация (русский)
├── .qwen/QWEN.md           # Контекст для AI-ассистентов (этот файл)
├── .nojekyll               # Отключение Jekyll для GitHub Pages
├── .pre-commit-config.yaml # Pre-commit hooks (black, isort, flake8, mypy)
├── .flake8                 # Конфигурация flake8
├── pytest.ini              # Конфигурация pytest
├── package.json            # Node.js зависимости (Jest)
├── LICENSE                 # Лицензия MIT
│
├── js/                     # JavaScript модули (ES6 modules)
│   ├── config.js           # Константы приложения, URL, значения по умолчанию
│   ├── main.js             # Оркестрация приложения, инициализация
│   ├── ifcBridge.js        # Мост JS ↔ Python (Pyodide), загрузка модулей
│   ├── core/
│   │   ├── config.js       # APP_CONFIG (ES6 module)
│   │   └── constants.js    # BOLT_TYPES, MATERIALS, AVAILABLE_DIAMETERS
│   ├── ui/
│   │   └── status.js       # StatusManager: управление статусами UI
│   ├── services/
│   │   └── validationService.js  # ValidationService: валидация параметров
│   ├── utils/
│   │   ├── dom.js          # DOM утилиты (getById, querySelector, etc.)
│   │   └── helpers.js      # Вспомогательные функции (debounce, formatNumber)
│   └── tests/              # Jest тесты
│       ├── constants.test.js
│       ├── helpers.test.js
│       └── validationService.test.js
│
├── python/                 # Python модули (Pyodide среда)
│   ├── main.py             # IFCDocumentManager: менеджер документов (не Singleton!)
│   ├── document_manager.py # IFCDocumentManager: управление множественными IFC документами
│   ├── container.py        # DIContainer: Dependency Injection контейнер
│   ├── protocols.py        # Protocol интерфейсы (PEP 544) для DI
│   ├── utils.py            # Централизованный импорт ifcopenshell
│   ├── validate_utils.py   # Утилиты валидации IFC (validate_ifc_file)
│   ├── gost_data.py        # Wrapper для обратной совместимости
│   ├── material_manager.py # Менеджер материалов IFC
│   ├── type_factory.py     # TypeFactory: кэширование типов с RepresentationMaps
│   ├── instance_factory.py # InstanceFactory: создание инстансов с IfcMappedItem
│   ├── geometry_builder.py # Геометрия IFC: кривые, профили, выдавливание
│   ├── geometry_converter.py # Конвертация IFC → mesh Three.js
│   └── ifc_generator.py    # Экспорт IFC, валидация документа
│   │
│   ├── data/               # Пакет: данные ГОСТ
│   │   ├── __init__.py     # Экспорт API
│   │   ├── bolt_dimensions.py      # BOLT_DIM_DATA: размеры болтов
│   │   ├── fastener_dimensions.py  # NUT_DIM_DATA, WASHER_DIM_DATA
│   │   ├── materials.py            # MATERIALS: свойства материалов
│   │   └── validation.py           # AVAILABLE_LENGTHS, validate_parameters
│   │
│   └── services/           # Пакет: сервисы
│       ├── __init__.py     # Экспорт API
│       └── dimension_service.py    # DimensionService: размеры болтов
│
├── tests/                  # Автотесты (pytest + Jest)
│   ├── conftest.py         # Фикстуры и Mock классы (MockIfcEntity, MockIfcDoc)
│   ├── workflow.md         # TDD Workflow документация
│   ├── test_main.py
│   ├── test_document_manager.py
│   ├── test_container.py
│   ├── test_gost_data.py
│   ├── test_material_manager.py
│   ├── test_type_factory.py
│   ├── test_instance_factory.py
│   ├── test_geometry_builder.py
│   ├── test_dimension_service.py
│   ├── test_utils.py
│   └── test_validate_utils.py
│
├── docs/
│
├── data/
│   └── dim.csv             # Исходные данные размеров болтов
│
├── wheels/
│   └── ifcopenshell-*.whl  # IfcOpenShell wheel для Pyodide
│
├── assets/
│   ├── favicon.svg
│   └── icons/
│
└── .vscode/
    └── settings.json       # Настройки линтера и автодополнения
```

---

## Технологический стек

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| **Frontend** | HTML5, CSS3, Vanilla JS (ES6 modules) | Браузерный UI |
| **3D-движок** | Three.js r128 | WebGL-визуализация |
| **Python-среда** | Pyodide 0.26.0 | Python WebAssembly |
| **IFC-библиотека** | IfcOpenShell 0.8.4 | Создание/конвертация IFC |
| **IFC-стандарт** | IFC4 ADD2 TC1 | Российский BIM-стандарт |
| **Материалы** | ГОСТ 19281-2014, ГОСТ 535-88 | Марки стали |
| **Тестирование** | pytest 9.0+, Jest 29+ | Python + JavaScript тесты |
| **CI/CD** | pre-commit, GitHub Actions | Автоматические проверки |

### Доступные материалы
- **09Г2С** (ГОСТ 19281-2014) — σ_в = 490 МПа, низколегированная сталь
- **ВСт3пс2** (ГОСТ 535-88) — σ_в = 345 МПа, углеродистая конструкционная сталь
- **10Г2** (ГОСТ 19281-2014) — σ_в = 490 МПа, низколегированная сталь

---

## Сборка и запуск

### Локальная разработка
```bash
# Запустить HTTP-сервер (Python 3)
python3 -m http.server 8000

# Открыть в браузере
# http://localhost:8000
```

### Установка зависимостей
```bash
# Python зависимости (для тестов)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Pre-commit hooks
pre-commit install

# JavaScript зависимости (для тестов)
npm install
```

### Запуск тестов
```bash
# Python тесты
pytest tests/ -v

# Python тесты с покрытием
pytest tests/ --cov=python --cov-report=term-missing

# JavaScript тесты
npm test

# JavaScript тесты с покрытием
npm run test:coverage

# Все тесты
pytest tests/ -v && npm test
```

### Pre-commit проверки
```bash
# Запуск всех проверок
pre-commit run --all-files

# Проверки: black, isort, flake8, mypy
```

### Сборка не требуется
Приложение работает напрямую в браузере. Pyodide загружает Python-модули динамически во время выполнения.

### Двухэтапная инициализация

**Этап 1: Загрузка приложения (один раз)**
1. Загрузка Pyodide (~80 МБ)
2. Установка зависимостей: `typing_extensions` → `numpy` → `shapely` → `ifcopenshell`
3. Проверка доступности `ifcopenshell.geom`
4. Загрузка Python-модулей в виртуальную файловую систему (с учётом структуры data/ и services/)
5. Создание базовой IFC-структуры (Проект → Участок → Здание → Этаж)

**Этап 2: Генерация болта (каждый запрос)**
1. Валидация параметров через `ValidationService` (JS) и `gost_data.py` (Python)
2. Получение/создание типов с кэшированием и RepresentationMaps (TypeFactory)
3. Создание инстансов с IfcMappedItem (InstanceFactory)
4. Конвертация IFC-геометрии в mesh через `ifcopenshell.geom.create_shape()`
5. Обновление 3D-сцены

---

## Архитектура (после рефакторинга)

### IFC-иерархия
```
IfcProject
└── IfcSite
    └── IfcBuilding
        └── IfcBuildingStorey
            └── IfcMechanicalFastener (Сборка: ANCHORBOLT)
                ├── IfcMechanicalFastener (Шпилька: USERDEFINED)
                ├── IfcMechanicalFastener (Гайка #1: USERDEFINED) [опц.]
                ├── IfcMechanicalFastener (Шайба #1: USERDEFINED) [опц.]
                ├── IfcMechanicalFastener (Гайка #2: USERDEFINED) [опц.]
                └── IfcMechanicalFastener (Шайба #2: USERDEFINED) [опц.]
```

### Ответственность модулей

#### JavaScript-слой (ES6 modules)
| Модуль | Ответственность |
|--------|-----------------|
| `js/core/config.js` | APP_CONFIG: URL wheel-пакетов, PYTHON_MODULES, значения по умолчанию |
| `js/core/constants.js` | BOLT_TYPES, MATERIALS, AVAILABLE_DIAMETERS, STATUS_TYPES |
| `js/ui/status.js` | StatusManager: управление статусами UI (show, hide, success, error) |
| `js/services/validationService.js` | ValidationService: валидация параметров болта |
| `js/utils/dom.js` | DOM утилиты: getById, querySelector, addClass, setText, etc. |
| `js/utils/helpers.js` | Helpers: formatNumber, roundTo, debounce, throttle, sleep |
| `js/ifcBridge.js` | IFCBridge: загрузка Pyodide, настройка ifcopenshell, загрузка модулей |
| `js/main.js` | Оркестрация: инициализация, координация модулей |

#### Python-слой
| Модуль | Ответственность |
|--------|-----------------|
| `main.py` | IFCDocumentManager (не Singleton!): менеджер документов, API для обратной совместимости |
| `document_manager.py` | IFCDocumentManager: управление множественными IFC документами |
| `container.py` | DIContainer: Dependency Injection контейнер |
| `protocols.py` | Protocol интерфейсы (PEP 544): IfcDocumentProtocol, GeometryBuilderProtocol, etc. |
| `utils.py` | Централизованный импорт `ifcopenshell` (`get_ifcopenshell`) |
| `validate_utils.py` | Утилиты валидации IFC: `validate_ifc_file()`, `assert_valid_ifc()` |
| `gost_data.py` | Wrapper для обратной совместимости (делегирование в data.*) |
| `material_manager.py` | Менеджер материалов: создание `IfcMaterial`, `IfcMaterialList`, `IfcRelAssociatesMaterial` |
| `type_factory.py` | `TypeFactory`: кэширование `IfcMechanicalFastenerType` с использованием **RepresentationMaps** |
| `instance_factory.py` | `InstanceFactory`: создание инстансов с **IfcMappedItem** (для переиспользования геометрии) |
| `geometry_builder.py` | Построение IFC-геометрии: `IfcSweptDiskSolid`, `IfcExtrudedAreaSolid`, кривые, профили |
| `geometry_converter.py` | Конвертация IFC → mesh Three.js через `ifcopenshell.geom.create_shape()` |
| `ifc_generator.py` | Экспорт IFC-файла, валидация документа |
| | |
| `data/__init__.py` | Экспорт API: `get_bolt_dimensions`, `get_nut_dimensions`, `get_washer_dimensions`, `validate_parameters` |
| `data/bolt_dimensions.py` | `BOLT_DIM_DATA`: размеры болтов из dim.csv |
| `data/fastener_dimensions.py` | `NUT_DIM_DATA`, `WASHER_DIM_DATA`: размеры гаек и шайб |
| `data/materials.py` | `MATERIALS`: свойства материалов (σ_в, ГОСТ, плотность) |
| `data/validation.py` | `AVAILABLE_LENGTHS`, `validate_parameters`: валидация по ГОСТ |
| `services/dimension_service.py` | `DimensionService`: сервис для получения размеров болтов |

### Подход к геометрии
Геометрия строится **один раз** в IFC-модели через `type_factory.py` с использованием `IfcSweptDiskSolid` и `IfcExtrudedAreaSolid`, затем конвертируется в меши Three.js через `geometry_converter.py` с помощью `ifcopenshell.geom.create_shape()`. Это обеспечивает:
- Единый источник истины для геометрии
- Отсутствие дублирования кода
- Корректное соответствие 3D-вида и IFC-данных
- **RepresentationMaps** для переиспользования геометрии типов
- **IfcMappedItem** для экземпляров (валидация IFC: `MappedRepresentation`)

---

## Тестирование

### Статистика тестов
- **Python:** 152 теста (pytest)
- **JavaScript:** 38 тестов (Jest)
- **Покрытие:** 82% (Python)
- **Pre-commit:** black, isort, flake8, mypy — все проходят

### Mock классы (conftest.py)
```python
from conftest import MockIfcEntity, MockIfcDoc

# MockIfcEntity: Mock для IFC сущности
# MockIfcDoc: Mock для IFC документа
```

### Фикстуры (conftest.py)
```python
@pytest.fixture(scope="function")
def mock_ifc_doc():
    """Создание Mock IFC документа"""
    return MockIfcDoc()

@pytest.fixture(scope="function")
def valid_bolt_params():
    """Параметры валидного болта по умолчанию"""
    return {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}
```

### TDD Workflow
См. `tests/workflow.md` для подробной документации по TDD процессу.

---

## GitHub Pages

### Деплой
Приложение размещено на GitHub Pages: https://vdobranov.github.io/ANCHOR-BOLT-GENERATOR/

### .nojekyll
Файл `.nojekyll` в корне отключает обработку Jekyll, что позволяет GitHub Pages корректно обслуживать файлы `__init__.py` и другие специальные файлы Python.

### Загрузка модулей
Python модули загружаются через `fetch()` с абсолютными путями от корня сайта (исправлено в `ifcBridge.js`).

---

## Ресурсы

- [TDD Workflow](tests/workflow.md) — Документация по TDD процессу
- [Sphinx документация](docs/) — API документация
- [Refactoring Plan](refactoring/README.md) — План рефакторинга (Phase 0-8)
- [pytest](https://docs.pytest.org/) — Python тестирование
- [Jest](https://jestjs.io/) — JavaScript тестирование
- [Pre-commit](https://pre-commit.com/) — Автоматические проверки

## Инструкции

After any code refactoring or bug fix, automatically update all relevant documentation files (PROJECT_SUMMARY.md, IMPLEMENTATION_SUMMARY.md, README.md, phase TODO files) before marking task complete

For Pyodide/browser projects, always verify: (1) no module-level imports before micropip installation, (2) PYTHON_MODULES includes all dependencies, (3) test in browser context not just Python

Run existing tests after any code modification that could affect tested functionality - don't assume tests will pass

Before commiting, verify: (1) no module-level ifcopenshell imports before micropip.install(), (2) all dependencies in PYTHON_MODULES, (3) test the actual browser build not just Python. List any issues found.

After every code edit, run the relevant tests for that module. If tests exist, run them immediately. If no tests exist, note this as a gap. Report test results before proceeding to the next task.

Before making any code changes, first analyze the existing test structure and identify coverage gaps. Generate comprehensive unit tests for the functions I'm about to modify, run them to establish a baseline, then implement changes while continuously running the test suite. Report any test failures immediately with suggested fixes. For this refactoring task, create tests covering: edge cases, error handling, integration points, and regression scenarios. Run all tests after each significant change and only proceed when the suite passes.