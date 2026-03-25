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

| Тип | Форма     | Диаметры | Длины    |
| --- | --------- | -------- | -------- |
| 1.1 | Изогнутый | М12–М48  | 300–1400 |
| 1.2 | Изогнутый | М12–М48  | 300–1000 |
| 2.1 | Прямой    | М16–М48  | 500–1250 |
| 5   | Прямой    | М12–М48  | 300–1000 |

**Примечание:** Исполнение определяется автоматически по типу болта (1.1 → исполнение 1, 1.2 → исполнение 2, и т.д.).

### Состав сборки (автоматически)

- **Типы 1.1, 1.2, 5**: шпилька + верхняя шайба + 2 верхних гайки
- **Тип 2.1**: шпилька + верхняя шайба + 2 верхних гайки + 2 нижних гайки

---

## Архитектура

### Структура проекта

```
ANCHOR-BOLT-GENERATOR/
├── js/                     # JavaScript модули (ES6 modules)
├── python/                 # Python модули (Pyodide)
│   ├── data/               # Пакет: данные ГОСТ
│   └── services/           # Пакет: сервисы
├── tests/                  # Автотесты (pytest + Jest)
├── docs/                   # Документация
└── .qwen/                  # AI контекст (ARCHITECTURE.md, TESTING.md)
```

### Технологический стек

| Компонент      | Версия                        | Назначение                         |
| -------------- | ----------------------------- | ---------------------------------- |
| Frontend       | HTML5, CSS3, Vanilla JS (ES6) | Браузерный UI                      |
| 3D-движок      | Three.js r128                 | WebGL-визуализация                 |
| Python-среда   | Pyodide 0.26.0                | Python WebAssembly                 |
| IFC-библиотека | IfcOpenShell 0.8.4            | Создание/конвертация IFC           |
| IFC-стандарт   | IFC4 ADD2 TC1                 | BIM-стандарт                       |
| Материалы      | ГОСТ 19281-2014, ГОСТ 535-88  | Марки стали (09Г2С, ВСт3пс2, 10Г2) |
| Тестирование   | pytest, Jest, Behave          | Python + JavaScript + Gherkin      |

### Архитектура приложения

**Клиент-серверная архитектура в браузере:**

```
┌─────────────────────────────────────────────────────────────┐
│                     Браузер (Client)                        │
├─────────────────────────────────────────────────────────────┤
│  JavaScript слой (UI, валидация, Three.js)                  │
├─────────────────────────────────────────────────────────────┤
│  Python слой (Pyodide): IFC генерация, геометрия            │
└─────────────────────────────────────────────────────────────┘
```

**IFC-иерархия:** IfcProject → IfcSite → IfcBuilding → IfcBuildingStorey → IfcMechanicalFastener (Сборка)

**Ключевые решения:**

- Единый источник истины: геометрия строится в IFC → конвертируется в mesh Three.js
- RepresentationMaps + IfcMappedItem: переиспользование геометрии типов
- Динамическое кэширование: оптимизация размера IFC
- DI-контейнер: управление зависимостями Python-модулей

**Поток данных:** Ввод → Валидация → TypeFactory (кэш) → InstanceFactory → GeometryBuilder → GeometryConverter → Viewer

→ Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md), [docs/arch-docs/](docs/arch-docs/)

---

## Тестирование

### Статистика тестов

- **Python:** 276 тестов (pytest)
- **JavaScript:** 38 тестов (Jest)
- **Gherkin:** 100+ правил (buildingSMART)
- **Покрытие:** 82% (Python), 70% (JavaScript)

### Уровни тестирования

| Уровень       | Инструмент       | Описание                           |
| ------------- | ---------------- | ---------------------------------- |
| Unit-тесты    | pytest           | Python модули                      |
| Unit-тесты    | Jest             | JavaScript модули                  |
| Валидация IFC | Behave (Gherkin) | Проверка по правилам buildingSMART |

→ Подробнее: [TESTING.md](TESTING.md), [docs/tests-docs/](docs/tests-docs/)

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

- [ARCHITECTURE.md](ARCHITECTURE.md) — Архитектура проекта
- [TESTING.md](TESTING.md) — TDD Workflow
- [docs/arch-docs/](docs/arch-docs/) — Детализация архитектуры
- [docs/tests-docs/](docs/tests-docs/) — Детализация тестирования
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
