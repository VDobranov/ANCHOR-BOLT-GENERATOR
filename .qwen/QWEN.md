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

### Поддерживаемые типы болтов

| Тип | Форма | Диаметры | Длины |
|-----|-------|----------|-------|
| 1.1 | Изогнутый | М12–М48 | 300–1400 |
| 1.2 | Изогнутый | М12–М48 | 300–1000 |
| 2.1 | Прямой | М16–М48 | 500–1250 |
| 5 | Футорка | М12–М48 | 300–1000 |

**Примечание:** Исполнение определяется автоматически по типу болта (1.1 → исполнение 1, 1.2 → исполнение 2, и т.д.).

### Состав сборки (автоматически)
- **Типы 1.1, 1.2, 5**: шпилька + верхняя шайба + 2 верхних гайки
- **Тип 2.1**: шпилька + верхняя шайба + 2 верхних гайки + 2 нижних гайки

---

## Структура проекта

```
ANCHOR-BOLT-GENERATOR/
├── index.html              # Главная HTML-страница (русский UI)
├── style.css               # Стили приложения
├── README.md               # Пользовательская документация (русский)
├── .qwen/QWEN.md           # Контекст для AI-ассистентов (этот файл)
├── LICENSE                 # Лицензия MIT
│
├── js/                     # JavaScript модули (7 файлов)
│   ├── config.js           # Константы приложения, URL, значения по умолчанию
│   ├── ui.js               # UI-утилиты (статусы, переключение, скачивание)
│   ├── form.js             # Класс BoltForm: обработка формы, валидация
│   ├── viewer.js           # Класс IFCViewer: сцена Three.js, меши
│   ├── ifcBridge.js        # Класс IFCBridge: мост JS ↔ Python (Pyodide)
│   ├── main.js             # Оркестрация приложения, инициализация
│   └── init.js             # Точка входа
│
├── python/                 # Python модули (10 файлов, среда Pyodide)
│   ├── main.py             # Singleton IFCDocument, базовая структура
│   ├── utils.py            # Централизованный импорт ifcopenshell
│   ├── gost_data.py        # Справочники ГОСТ, валидация, таблицы размеров
│   ├── material_manager.py # Менеджер материалов IFC (IfcMaterial, IfcRelAssociatesMaterial)
│   ├── type_factory.py     # TypeFactory: кэширование IfcMechanicalFastenerType
│   ├── instance_factory.py # InstanceFactory: создание инстансов, сборок
│   ├── geometry_builder.py # Геометрия IFC через shape_builder: кривые, профили, выдавливание
│   ├── geometry_converter.py # Конвертация IFC → mesh Three.js через ifcopenshell.geom
│   ├── ifc_generator.py    # Экспорт IFC, валидация документа
│   └── validate_utils.py   # Утилиты валидации IFC (для Pyodide)
│
├── tests/                  # Автотесты (pytest)
│   ├── test_main.py
│   ├── test_gost_data.py
│   ├── test_material_manager.py
│   ├── test_type_factory.py
│   ├── test_instance_factory.py
│   ├── test_geometry_builder.py
│   ├── test_utils.py
│   └── validate_utils.py   # Утилиты валидации для тестов
│
├── data/
│   └── dim.csv             # Исходные данные размеров болтов
│
├── wheels/
│   └── ifcopenshell-0.8.4+158fe92-cp313-cp313-pyodide_2025_0_wasm32.whl
│
├── assets/
│   ├── favicon.svg
│   └── icons/
│
├── ai/                     # Документация архитектуры от AI
│   ├── CONSOLIDATED_PLAN.md
│   ├── IMPLEMENTATION_SUMMARY.md
│   ├── PLAN_claude.md
│   ├── PLAN_deepseek.md
│   ├── PLAN_qwen.md
│   ├── entry_prompt.md
│   └── Qwen_session_*.md   # Резюме сессий
│
├── .vscode/
│   └── settings.json       # Настройки линтера и автодополнения
│
└── .gitignore
```

---

## Технологический стек

| Компонент | Версия | Назначение |
|-----------|--------|------------|
| **Frontend** | HTML5, CSS3, Vanilla JS | Браузерный UI |
| **3D-движок** | Three.js r128 | WebGL-визуализация |
| **Python-среда** | Pyodide 0.26.0 | Python WebAssembly |
| **IFC-библиотека** | IfcOpenShell 0.8.4 | Создание/конвертация IFC |
| **IFC-стандарт** | IFC4 ADD2 TC1 | Российский BIM-стандарт |
| **Материалы** | ГОСТ 19281-2014, ГОСТ 535-88 | Марки стали |

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

### Сборка не требуется
Приложение работает напрямую в браузере. Pyodide загружает Python-модули динамически во время выполнения.

### Двухэтапная инициализация

**Этап 1: Загрузка приложения (один раз)**
1. Загрузка Pyodide (~80 МБ)
2. Установка зависимостей: `typing_extensions` → `numpy` → `shapely` → `ifcopenshell`
3. Проверка доступности `ifcopenshell.geom`
4. Загрузка Python-модулей в виртуальную файловую систему
5. Создание базовой IFC-структуры (Проект → Участок → Здание → Этаж)

**Этап 2: Генерация болта (каждый запрос)**
1. Валидация параметров через `gost_data.py`
2. Получение/создание типов с кэшированием (TypeFactory)
3. Создание инстансов с размещениями (InstanceFactory)
4. Конвертация IFC-геометрии в mesh через `ifcopenshell.geom.create_shape()`
5. Обновление 3D-сцены

---

## Архитектура

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

#### JavaScript-слой
| Модуль | Ответственность |
|--------|-----------------|
| `config.js` | Константы: URL wheel-пакетов, список Python-модулей, значения по умолчанию |
| `ui.js` | UI-утилиты: статусные сообщения, переключение элементов, скачивание |
| `form.js` | Класс `BoltForm`: обработка формы, валидация, debouncing |
| `viewer.js` | Класс `IFCViewer`: сцена Three.js, камера, меши, взаимодействие |
| `ifcBridge.js` | Класс `IFCBridge`: загрузка Pyodide, настройка ifcopenshell, вызовы Python |
| `main.js` | Оркестрация: инициализация, координация модулей |
| `init.js` | Точка входа приложения |

#### Python-слой
| Модуль | Ответственность |
|--------|-----------------|
| `main.py` | Singleton `IFCDocument`: жизненный цикл IFC-файла, базовая структура |
| `utils.py` | Централизованный импорт `ifcopenshell` (`get_ifcopenshell`) |
| `material_manager.py` | Менеджер материалов: создание `IfcMaterial`, `IfcMaterialList`, `IfcRelAssociatesMaterial` |
| `gost_data.py` | Словари ГОСТ, валидация параметров, таблицы размеров |
| `type_factory.py` | `TypeFactory`: кэширование `IfcMechanicalFastenerType` по ключу `(тип, диаметр, длина, исполнение, материал)` |
| `instance_factory.py` | `InstanceFactory`: создание инстансов, размещений, агрегаций, данных mesh через `ifcopenshell.geom` |
| `geometry_builder.py` | Построение IFC-геометрии через ifcopenshell.util.shape_builder: `IfcSweptDiskSolid`, `IfcExtrudedAreaSolid`, кривые, профили |
| `geometry_converter.py` | Конвертация IFC → mesh Three.js через `ifcopenshell.geom.create_shape()` |
| `ifc_generator.py` | Экспорт IFC-файла, валидация документа |
| `validate_utils.py` | Утилиты валидации IFC: `validate_ifc_file()`, `assert_valid_ifc()` |

### Подход к геометрии
Геометрия строится **один раз** в IFC-модели через `type_factory.py` с использованием `IfcSweptDiskSolid` и `IfcExtrudedAreaSolid`, затем конвертируется в меши Three.js через `geometry_converter.py` с помощью `ifcopenshell.geom.create_shape()`. Это обеспечивает:
- Единый источник истины для геометрии
- Отсутствие дублирования кода
- Корректное соответствие 3D-вида и IFC-данных

---

## Ключевые API

### JavaScript API
```javascript
// Инициализация (автоматически при загрузке)
const bridge = await initializeIFCBridge(pyodide);

// Генерация болта
const result = await bridge.generateBolt({
    bolt_type: '1.1',
    execution: 1,
    diameter: 20,
    length: 800,
    material: '09Г2С'
});

// result.ifcData — IFC-строка для скачивания
// result.meshData — данные для 3D-визуализации
```

### Python API
```python
# Инициализация
from main import initialize_base_document, get_ifc_document
ifc_doc = initialize_base_document()

# Генерация болта
from instance_factory import generate_bolt_assembly
ifc_str, mesh_data = generate_bolt_assembly({
    'bolt_type': '1.1',
    'execution': 1,
    'diameter': 20,
    'length': 800,
    'material': '09Г2С'
})
```

---

## Конвенции разработки

### Стиль кода
- **JavaScript**: ES6+ модули, классы, async/await
- **Python**: Python 3.13 (Pyodide), type hints где уместно
- **Именование**: английский для кода, русский для UI-строк и комментариев

### Практики тестирования
- Ручное тестирование через браузерный UI
- Валидация IFC в BIM-инструментах (Revit, ArchiCAD, BonsaiBIM)
- Документирование сессий в папке `ai/`

### Руководство по внесению изменений
- Соблюдать соответствие ГОСТ для всех размеров
- Сохранять русский язык UI (пользовательский интерфейс)
- Использовать английский для кода, комментариев и документации
- Документировать архитектурные решения в папке `ai/`

---

## Известные ограничения

1. **Совместимость Pyodide** — некоторые сложные IFC-примитивы требуют упрощения
2. **Производительность** — первая загрузка Pyodide занимает 2–3 секунды
3. **Браузер** — требуется современный браузер с поддержкой WebGL
4. **Память** — большие сборки могут требовать больше памяти
5. **Диапазон диаметров** — ограничено М12–М48 (по источнику DIM.py/BlenderBIM)

---

## Форматы файлов

### Формат IFC-вывода
- **Стандарт**: IFC4 ADD2 TC1 (российский BIM-стандарт)
- **Структура**: Проект → Участок → Здание → Этаж → Крепёж
- **Сущности**: `IfcMechanicalFastener`, `IfcMechanicalFastenerType`, `IfcMaterial`, `IfcPropertySet`

### Входные данные
- **dim.csv**: таблицы размеров болтов (источник: DIM.py/BlenderBIM)
- **gost_data.py**: встроенные словари ГОСТ и правила валидации

---

## Типовые операции

### Генерация болта
1. Выберите тип болта (1.1, 1.2, 2.1 или 5)
2. Выберите диаметр (М12–М48)
3. Выберите длину (по доступным ГОСТ)
4. Выберите материал (09Г2С, ВСт3пс2 или 10Г2)
5. Болт генерируется автоматически при изменении параметров
6. Вращайте 3D-вид мышью (ЛКМ — вращение, колесо — зум, ПКМ — панорамирование)
7. Нажмите «Скачать IFC» для экспорта

### Экспорт IFC-файла
- Формат имени: `bolt_{тип}_М{диаметр}x{длина}.ifc`
- Пример: `bolt_1.1_М20x800.ifc`

---

## Применимые стандарты

- **ГОСТ 24379.1-2012** — Болты фундаментные. Конструкция и размеры
- **ГОСТ 19281-2014** — Прокат повышенной прочности. Общие технические условия
- **ГОСТ 535-88** — Сталь углеродистая обыкновенного качества
- **IFC4 ADD2 TC1** — Industry Foundation Classes 4.0.2.1

---

## Внешние ресурсы

- [ГОСТ 24379.1-2012 PDF](https://files.stroyinf.ru/Data2/1/4293785/4293785690.pdf)
- [Спецификация IFC4 ADD2 TC1](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/HTML/)
- [Документация Three.js](https://threejs.org/docs/)
- [Документация Pyodide](https://pyodide.org/)
- [Документация IfcOpenShell](http://ifcopenshell.org/)

---

## Контекст сессии для AI-ассистентов

При работе с этим проектом:
1. **Сохраняйте соответствие ГОСТ** — все размеры должны соответствовать ГОСТ 24379.1-2012
2. **Сохраняйте русский UI** — пользовательские строки остаются на русском
3. **Код на английском** — переменные, функции, комментарии на английском
4. **Уважайте архитектуру модулей** — 8 Python-модулей, 7 JS-модулей
5. **Используйте ifcopenshell.geom** — единый источник истины для геометрии
6. **Кэшируйте типы** — избегайте дублирования `IfcMechanicalFastenerType`
7. **Тестируйте в браузере** — изменения должны работать в среде Pyodide
8. **Проверка импортов после рефакторинга** — после любых изменений импортов или структуры модулей немедленно запускайте быструю проверку импортов на всех затронутых файлах перед продолжением работы
9. **Подтверждение архитектурных изменений** — перед внесением архитектурных изменений подтверждайте объём работ с пользователем и сначала предлагайте минимально жизнеспособный подход
10. **Отладка сложных проблем** — при отладке сложных проблем используйте агентов для параллельного исследования (например, «use an agent to explore the Pyodide import chain while another checks the geometry extraction pipeline»)
11. **Процесс рефакторинга** — перед рефакторингом составьте список всех файлов, которые будут изменены, и создайте быстрый тест импортов для каждого; запускайте эти тесты после каждой партии изменений

---

## История недавнего рефакторинга

### Переход на ifcopenshell.util.shape_builder (14.03.2026)
- Обновлён `geometry_builder.py`:
  - **Workaround для циклического импорта VectorType** (IfcOpenShell #7562)
  - Используется `ShapeBuilder` для создания геометрии:
    - `polyline()` — кривые с поддержкой дуг через `arc_points`
    - `circle()` — круглые профили
    - `profile()` — профили с отверстиями
    - `extrude()` — выдавливание профилей
    - `create_swept_disk_solid()` — заметание по кривой
    - `get_representation()` — создание представления
  - Сохранена точная математика для типов 1.1 и 1.2:
    - `_calculate_tangent_point()` — точка касания окружности
    - `_get_arc_vertex()` — вершина дуги по двум точкам и радиусу
    - `_calculate_stud_points_type_1_2()` — 6 точек для типа 1.2
  - Улучшен `_get_context()` — fallback для создания контекста вручную
- Обновлён `js/ifcBridge.js`:
  - Добавлена установка `shapely` через micropip
  - Добавлена проверка импорта `shapely`
- Обновлены тесты:
  - `tests/test_geometry_builder.py`: 13 тестов (mock ShapeBuilder)
  - `tests/test_type_factory.py`: 36 тестов (mock ShapeBuilder)
  - `tests/test_instance_factory.py`: 16 тестов (mock ShapeBuilder)
- **Итого:** удалено ~100 строк самописного кода, переведено на стандартный API
- **Тесты:** 93 passed, 1 skipped

### Точный алгоритм для типа 1.2 (11.03.2026)
- Обновлён `geometry_builder.py`:
  - Добавлен `_calculate_tangent_point()` — расчёт точки касания окружности
  - Добавлен `_get_arc_vertex()` — расчёт вершины дуги по двум точкам и радиусу
  - Добавлен `_calculate_stud_points_type_1_2()` — расчёт 6 точек для типа 1.2
  - Обновлён `create_composite_curve_stud()`:
    - Тип 1.2 использует `IfcIndexedPolyCurve` с 6 точками
    - Сегменты: `IfcLineIndex((1,2,3))`, `IfcArcIndex((3,4,5))`, `IfcLineIndex((5,6))`
    - Точная геометрия вместо аппроксимации полилинией (~12 сегментов)
- Обновлён `gost_data.py`:
  - Добавлены функции `get_bolt_l1()`, `get_bolt_l2()`, `get_bolt_l3()`
- Обновлён `instance_factory.py`:
  - IfcLocalPlacement для типа 1.2 смещён на `l0` (длина резьбы)
  - Низ резьбы находится в Z=0 (точка начала координат)
- **Итого:** добавлено ~195 строк
- **Тесты:** 95 passed, 1 skipped

### PropertySets материалов (11.03.2026)
- Обновлён `material_manager.py`:
  - Добавлен метод `create_material_properties()` — создание `IfcMaterialProperties`
  - Добавлен метод `create_standard_psets()` — создание стандартных PropertySets
  - **Pset_MaterialCommon**: `MassDensity` (плотность, кг/м³)
  - **Pset_MaterialSteel**: `YieldStress`, `UltimateStress`, `StructuralGrade` (предел текучести, предел прочности, марка стали)
  - Кэширование PropertySets по `(material, pset_name)`
- Обновлён `type_factory.py`:
  - Передаётся `material_key` в `create_material()` для создания свойств
  - Все типы болтов теперь имеют PropertySets с механическими свойствами
- Обновлены тесты:
  - `tests/test_material_manager.py`: добавлены тесты с реальным ifcopenshell (3 теста)
  - `tests/test_type_factory.py`: обновлён MockIfcDoc для поддержки IfcReal/IfcText
- **Итого:** добавлено ~100 строк
- **Тесты:** 95 passed, 1 skipped
- **Риск:** Используется документация IFC4x3 для IFC4 ADD2 TC1 (Pset имена могут отличаться)

### Материалы IFC (11.03.2026)
- Создан `material_manager.py`: управление материалами IFC
  - Класс `MaterialManager`: создание `IfcMaterial`, `IfcMaterialList`, `IfcRelAssociatesMaterial`
  - Кэширование материалов по имени
  - Ассоциация материалов с типами болтов и сборками
- Обновлён `gost_data.py`: добавлена функция `get_material_name()`
  - Формат имени: "09Г2С ГОСТ 19281-2014"
- Обновлён `type_factory.py`: интеграция с `MaterialManager`
  - Все типы болтов (шпилька, гайка, шайба) ассоциируются с материалами
  - Сборки используют `IfcMaterialList`
- Обновлён `instance_factory.py`: ассоциация материалов с assembly instances
- Обновлён `main.py`: инициализация `MaterialManager`, сохранение/восстановление при reset
- Создан `tests/test_material_manager.py`: 11 тестов
- Обновлены `tests/test_type_factory.py`: 6 тестов на ассоциацию материалов
- **Итого:** добавлено ~250 строк (новый функционал)
- **Тесты:** 93 passed, 1 skipped

### Рефакторинг (11.03.2026)
- Удалены неиспользуемые функции (11 функций):
  - `gost_data.py`: `get_bolt_type_name()`, `get_bolt_l1()`, `get_bolt_l2()`, `get_bolt_l3()`, `get_bolt_r()`, `get_bolt_all_dimensions()`, `get_material_info()`
  - `instance_factory.py`: `get_element_properties()`
  - `geometry_converter.py`: `generate_bolt_mesh_from_ifc()`
  - `ifc_generator.py`: `export_ifc_file()`
  - `utils.py`: `is_ifcopenshell_available()`
- Удалены тесты для удалённых функций (5 тестов)
- Обновлён `ifcBridge.js`: удалена проверка `is_ifcopenshell_available()` и метод `getElementProperties()`
- **Итого:** удалено 199 строк, добавлено 8 строк (чистая очистка)
- **Тесты:** 76 passed, 1 skipped

### Рефакторинг (22.02.2026)
- Удалён fallback mesh код (~340 строк) — используется только `ifcopenshell.geom`
- Удалены неиспользуемые модули: `material_manager.py`, `pset_manager.py`, `requirements.txt`
- Создан `utils.py` для централизации импорта `ifcopenshell`
- Удалено дублирование `BOLT_DIMENSIONS_SPEC` и `get_bolt_spec` в `gost_data.py`
- Обновлены `config.js` и `ui.js` (удалены несуществующие элементы)
- **Итого:** удалено ~620 строк, добавлено ~80 строк

### Рефакторинг (01.03.2026)
- Удалены неиспользуемые функции в `geometry_builder.py`:
  - `create_hexagon_profile()` — геометрия гайки создаётся в `type_factory.py`
  - `create_washer_profile()` — геометрия шайбы создаётся в `type_factory.py`
  - `create_extruded_solid()` — используется только в удалённых функциях выше
  - `create_placement()` — есть аналог в `instance_factory.py`
  - `create_stud_representation()`, `create_nut_representation()`, `create_washer_representation()` — convenience-функции не использовались
- **Итого:** удалено ~110 строк

### Рефакторинг геометрии (01.03.2026)
- Вся логика построения геометрии перемещена из `type_factory.py` в `geometry_builder.py`:
  - `_create_stud_geometry()` → `create_bent_stud_solid()`, `create_straight_stud_solid()`
  - `_create_nut_geometry()` → `create_nut_solid()`
  - `_create_washer_geometry()` → `create_washer_solid()`
  - `_get_context()` → `GeometryBuilder._get_context()`
  - `_associate_representation()` → `associate_representation()`
- `TypeFactory` теперь отвечает только за кэширование типов
- `GeometryBuilder` содержит всю логику построения IFC-геометрии
- **Итого:** `type_factory.py` сокращён со 286 до 112 строк (~174 строки перемещено)

---

## Текущий статус разработки

| Этап | Статус | Описание |
|------|--------|----------|
| 1. Инфраструктура | ✅ Готово | HTML, CSS, JS основа, Pyodide |
| 2. GOST-справочники | ✅ Готово | `gost_data.py` с полными таблицами |
| 3. Geometry Builder | ✅ Готово | Кривые и профили |
| 4. Type Factory | ✅ Готово | Кэширование типов |
| 5. Материалы и PSets | ✅ Готово | Материалы и свойства |
| 6. Instance Factory | ✅ Готово | Создание инстансов и сборок |
| 7. IFC Generator | ✅ Готово | Экспорт IFC |
| 8. Интеграция | ✅ Готово | Полная JS/Python интеграция |
| 9. Рефакторинг | ✅ Готово | Модульная архитектура |
| 10. ifcopenshell.geom | ✅ Готово | Конвертация IFC → mesh Three.js |
| 11. Геометрия сборок | ✅ Готово | Исправлена геометрия шпилек и шайб |
| 12. Очистка кода | ✅ Готово | Удаление мёртвого кода, централизация импортов |
| 13. Материалы IFC | ✅ Готово | `IfcMaterial`, `IfcRelAssociatesMaterial`, `IfcMaterialList` |
| 14. PropertySets материалов | ✅ Готово | `Pset_MaterialCommon`, `Pset_MaterialSteel` |
| 15. Точный алгоритм типа 1.2 | ✅ Готово | `IfcIndexedPolyCurve` с 6 точками, точная дуга |
| 16. Валидация IFC | ✅ Готово | `ifcopenshell.validate` с `express_rules=True`, автотесты |
| 17. Тестирование | ✅ Готово | 107 тестов, валидация структуры и геометрии |

---

## Валидация IFC

### Автоматическая валидация в тестах

Валидация проводится в автотестах (`tests/test_instance_factory.py`) после генерации болта:

```python
from instance_factory import generate_bolt_assembly
from validate_utils import validate_ifc_file

params = {'bolt_type': '1.1', 'diameter': 20, 'length': 800, 'material': '09Г2С'}
ifc_str, mesh_data = generate_bolt_assembly(params)

# Сохранение и валидация
import ifcopenshell
ifc_doc = ifcopenshell.open('/tmp/test.ifc')
errors = validate_ifc_file(ifc_doc)  # express_rules=True по умолчанию
assert errors is None, f"IFC не валиден: {errors}"
```

### Проверяемые правила

** EXPRESS правила:**
- ✅ `IfcShapeRepresentation.HasRepresentationIdentifier` — наличие обязательного атрибута
- ✅ `IfcShapeRepresentation.CorrectItemsForType` — совместимость типа представления с элементами
- ✅ `IfcProductDefinitionShape.ShapeOfProduct` — связь представления с продуктом

**Структура документа:**
- ✅ `IfcOwnerHistory` с ID #1 (ручной SPF с forward-ссылками)
- ✅ `IfcProject`, `IfcSite`, `IfcBuilding`, `IfcBuildingStorey` (по 1 каждого)
- ✅ `IfcMechanicalFastener` (4+: assembly, stud, nut, washer)
- ✅ `IfcMechanicalFastenerType` (4+)
- ✅ `IfcMaterial` (1+)
- ✅ `IfcRelAggregates`, `IfcRelDefinesByType`, `IfcRelAssociatesMaterial`

**Геометрия:**
- ✅ `IfcSweptDiskSolid` с типом `'AdvancedSweptSolid'`
- ✅ `RepresentationIdentifier='Body'` для всех представлений
- ✅ Mesh данные (4+ mesh в `mesh_data['meshes']`)

### Утилиты валидации

**python/validate_utils.py:**
```python
# Валидация с полным набором правил
errors = validate_ifc_file(ifc_doc, express_rules=True)

# Assert в тестах
assert_valid_ifc(ifc_doc, "Опциональное сообщение")
```

**tests/validate_utils.py** — копия для тестов (требования Pyodide).

### Исправленные ошибки валидации

1. **IfcOrganization требует Name** — добавлено в SPF шаблон `main.py`
2. **IfcApplication требует Version** — добавлено в SPF шаблон `main.py`
3. **IfcApplication.ApplicationDeveloper** — теперь ссылается на `IfcOrganization`, а не `IfcPerson`
4. **IfcShapeRepresentation без RepresentationIdentifier** — добавлено `'Body'` в `geometry_builder.py`
5. **IfcSweptDiskSolid не совместим с 'SweptSolid'** — изменено на `'AdvancedSweptSolid'`
6. **IfcOwnerHistory для не-root сущностей** — добавлен для `IfcMechanicalFastenerType`, `IfcRelAssociatesMaterial`

### Запуск тестов

```bash
# Все тесты с валидацией
pytest tests/

# Один тест на валидацию
pytest tests/test_instance_factory.py::TestGenerateBoltAssembly::test_generate_bolt_assembly_validates_ifc -v
```

**Результат:** 107 тестов проходят

---

## Быстрая справка

### Параметры болта по умолчанию
```javascript
{
    bolt_type: '1.1',
    execution: 1,
    diameter: 20,
    length: 800,
    material: '09Г2С'
}
```

### Доступные диаметры
М12, М16, М20, М24, М30, М36, М42, М48

### Цвета компонентов (Three.js)
- Шпилька: `0x8B8B8B` (серый)
- Шайба: `0xA9A9A9` (тёмно-серый)
- Гайка: `0x696969` (тускло-серый)
- Сборка: `0x4F4F4F` (тёмный грифель)
