# Детальный план создания одностраничного веб-приложения для генерации параметрических фундаментных болтов по ГОСТ 24379.1-2012

## 1. Архитектура сборки

### Иерархия типов и инстансов IFC

```
IfcProject (IFC4 ADD2 TC1)
└── IfcSite
    └── IfcBuilding
        └── IfcBuildingStorey
            └── IfcMechanicalFastener (сборка, тип: ANCHORBOLT)
                ├── IfcMechanicalFastener (шпилька, тип: STUD)
                ├── IfcMechanicalFastener (гайка, тип: NUT) [опционально]
                ├── IfcMechanicalFastener (шайба, тип: WASHER) [опционально]
                └── IfcMechanicalFastener (гайка, тип: NUT) [опционально]
```

### Диаграмма отношений

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           IfcProject                                    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            IfcSite                                      │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          IfcBuilding                                    │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       IfcBuildingStorey                                 │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  IfcMechanicalFastener (сборка - инстанс)                               │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ IfcMechanicalFastenerType (ANCHORBOLT - тип)                      │  │
│  │ ├─ Property Sets (Pset_*)                                          │  │
│  │ ├─ Materials (IfcMaterial)                                         │  │
│  │ └─ Representation (IfcProductDefinitionShape)                      │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ▼                                                                │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ IfcRelAggregates (сборка → компоненты)                            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ├──► IfcMechanicalFastener (шпилька - инстанс)                │
│         │    ┌───────────────────────────────────────────────────────┐  │
│         │    │ IfcMechanicalFastenerType (STUD - тип)                │  │
│         │    │ ├─ Geometry (IfcSweptDiskSolid)                        │  │
│         │    │ ├─ Property Sets (Pset_MechanicalFastenerCommon)       │  │
│         │    │ └─ Materials (IfcMaterial)                             │  │
│         │    └───────────────────────────────────────────────────────┘  │
│         │                                                                │
│         ├──► IfcMechanicalFastener (гайка - инстанс)                  │
│         │    ┌───────────────────────────────────────────────────────┐  │
│         │    │ IfcMechanicalFastenerType (NUT - тип)                 │  │
│         │    │ ├─ Geometry (IfcExtrudedAreaSolid)                     │  │
│         │    │ ├─ Property Sets (Pset_MechanicalFastenerCommon)       │  │
│         │    │ └─ Materials (IfcMaterial)                             │  │
│         │    └───────────────────────────────────────────────────────┘  │
│         │                                                                │
│         └──► IfcMechanicalFastener (шайба - инстанс)                  │
│              ┌───────────────────────────────────────────────────────┐  │
│              │ IfcMechanicalFastenerType (WASHER - тип)              │  │
│              │ ├─ Geometry (IfcExtrudedAreaSolid)                     │  │
│              │ ├─ Property Sets (Pset_MechanicalFastenerCommon)       │  │
│              │ └─ Materials (IfcMaterial)                             │  │
│              └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  IfcRelDefinesByType (инстансы → типы)                                  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2. Структура проекта

```
anchor_bolt_ifc_generator/
├── index.html                              # Главная страница приложения
├── css/
│   ├── main.css                            # Основные стили интерфейса
│   ├── form.css                            # Стили формы ввода параметров
│   ├── viewer.css                          # Стили 3D-визуализатора
│   └── properties.css                      # Стили панели свойств
├── js/
│   ├── main.js                             # Главный скрипт приложения
│   ├── ui/
│   │   ├── form_handler.js                 # Обработка формы ввода
│   │   ├── properties_panel.js             # Управление панелью свойств
│   │   └── download_handler.js             # Обработка скачивания файлов
│   ├── ifc/
│   │   ├── ifc_generator.js                # Генерация IFC через Pyodide
│   │   ├── ifc_validator.js                # Валидация IFC-файла
│   │   └── ifc_exporter.js                 # Экспорт в файл
│   ├── viewer/
│   │   ├── threejs_setup.js                # Инициализация Three.js
│   │   ├── geometry_converter.js           # Конвертация геометрии IFC в меш
│   │   ├── interaction_handler.js          # Обработка взаимодействия с 3D
│   │   └── element_selector.js             # Выбор элементов в 3D
│   └── utils/
│       ├── data_validator.js               # Валидация входных данных
│       └── event_bus.js                    # Система событий приложения
├── python/
│   ├── ifc_model_builder.py                # Основной модуль генерации IFC
│   ├── ifc_types/
│   │   ├── anchor_bolt_type.py             # Тип сборки (ANCHORBOLT)
│   │   ├── stud_type.py                    # Тип шпильки (STUD)
│   │   ├── nut_type.py                     # Тип гайки (NUT)
│   │   └── washer_type.py                  # Тип шайбы (WASHER)
│   ├── ifc_instances/
│   │   ├── anchor_bolt_instance.py         # Инстанс сборки
│   │   ├── stud_instance.py                # Инстанс шпильки
│   │   ├── nut_instance.py                 # Инстанс гайки
│   │   └── washer_instance.py              # Инстанс шайбы
│   ├── ifc_relations/
│   │   ├── rel_defines_by_type.py          # Отношения типов и инстансов
│   │   ├── rel_aggregates.py               # Агрегация элементов
│   │   └── rel_connects_elements.py        # Соединения элементов
│   ├── ifc_geometry/
│   │   ├── swept_disk_solid_builder.py     # Построение геометрии шпильки
│   │   ├── extruded_area_solid_builder.py  # Построение геометрии гаек/шайб
│   │   └── composite_curve_builder.py      # Построение составных кривых
│   ├── ifc_properties/
│   │   ├── pset_mechanical_fastener.py     # Property Sets для крепежа
│   │   ├── pset_anchor_bolt.py             # Property Sets для анкерных болтов
│   │   └── pset_manufacturer_info.py       # Property Sets производителя
│   └── data/
│       ├── gost_24379_1_2012.py            # Параметры по ГОСТ 24379.1-2012
│       └── gost_19281_2014.py              # Материалы по ГОСТ 19281-2014
├── data/
│   ├── gost_24379_1_2012.json              # Справочник параметров ГОСТ
│   ├── gost_19281_2014.json                # Справочник материалов
│   └── default_parameters.json             # Параметры по умолчанию
├── assets/
│   ├── icons/
│   │   ├── bolt.svg
│   │   ├── nut.svg
│   │   ├── washer.svg
│   │   ├── download.svg
│   │   └── refresh.svg
│   └── templates/
│       └── ifc_header_template.txt         # Шаблон заголовка IFC-файла
├── pyodide/
│   ├── pyodide.js                          # Pyodide runtime
│   ├── pyodide-lock.json                   # Зависимости Pyodide
│   └── requirements.txt                    # Python зависимости
└── docs/
    ├── architecture.md                     # Архитектура приложения
    ├── ifc_specification.md                # Спецификация IFC
    └── gost_reference.md                   # Справочник ГОСТ
```

## 3. Спецификация IfcMechanicalFastenerType

### Таблица атрибутов типов и их назначение

| Атрибут | Тип данных | Обязательность | Назначение | Пример значения |
|---------|------------|----------------|------------|-----------------|
| **GlobalId** | IfcGloballyUniqueId | Обязательный | Уникальный идентификатор | "2xV4$yBcH0qO8nqPE$FO5z" |
| **OwnerHistory** | IfcOwnerHistory | Обязательный | История владения | Создается автоматически |
| **Name** | IfcLabel | Обязательный | Имя элемента | "Болт 1.1.М20 х 800 09Г2С ГОСТ 24379.1-2012" |
| **Description** | IfcText | Опциональный | Описание элемента | "Фундаментный болт по ГОСТ 24379.1-2012" |
| **ApplicableOccurrence** | IfcIdentifier | Опциональный | Применимое вхождение | "Болт фундаментный" |
| **HasPropertySets** | SET [0:?] OF IfcPropertySetDefinition | Опциональный | Наборы свойств | Ссылки на Pset_* |
| **RepresentationMaps** | LIST [0:?] OF IfcRepresentationMap | Опциональный | Карты представлений | Геометрия типа |
| **Tag** | IfcIdentifier | Опциональный | Тег элемента | "BOLT-001" |
| **ElementType** | IfcLabel | Обязательный | Тип элемента | "STUD", "NUT", "WASHER" |
| **PredefinedType** | IfcMechanicalFastenerTypeEnum | Обязательный | Предопределенный тип | "ANCHORBOLT", "USERDEFINED" |

### Спецификация для каждого типа элемента

#### IfcMechanicalFastenerType (STUD - шпилька)

| Атрибут | Значение | Примечание |
|---------|----------|------------|
| ElementType | "STUD" | Строковый идентификатор |
| PredefinedType | "USERDEFINED" | Пользовательский тип |
| NominalDiameter | REAL | Диаметр резьбы (мм) |
| NominalLength | REAL | Номинальная длина (мм) |
| ThreadLength | REAL | Длина резьбовой части (мм) |
| Geometry | IfcSweptDiskSolid | Единое тело с осевой линией |

#### IfcMechanicalFastenerType (NUT - гайка)

| Атрибут | Значение | Примечание |
|---------|----------|------------|
| ElementType | "NUT" | Строковый идентификатор |
| PredefinedType | "USERDEFINED" | Пользовательский тип |
| NominalDiameter | REAL | Диаметр резьбы (мм) |
| Height | REAL | Высота гайки (мм) |
| WidthAcrossFlats | REAL | Размер под ключ (мм) |
| Geometry | IfcExtrudedAreaSolid | Выдавленное тело с профилем |

#### IfcMechanicalFastenerType (WASHER - шайба)

| Атрибут | Значение | Примечание |
|---------|----------|------------|
| ElementType | "WASHER" | Строковый идентификатор |
| PredefinedType | "USERDEFINED" | Пользовательский тип |
| NominalDiameter | REAL | Диаметр отверстия (мм) |
| Thickness | REAL | Толщина шайбы (мм) |
| OuterDiameter | REAL | Внешний диаметр (мм) |
| Geometry | IfcExtrudedAreaSolid | Выдавленное тело с профилем |

#### IfcMechanicalFastenerType (ANCHORBOLT - сборка)

| Атрибут | Значение | Примечание |
|---------|----------|------------|
| ElementType | "ANCHORBOLT" | Строковый идентификатор |
| PredefinedType | "ANCHORBOLT" | Предопределенный тип анкерного болта |
| NominalDiameter | REAL | Диаметр резьбы (мм) |
| NominalLength | REAL | Номинальная длина (мм) |
| AnchorBoltLength | REAL | Общая длина болта (мм) |
| AnchorBoltThreadLength | REAL | Длина резьбовой части (мм) |
| Geometry | None | Геометрия определяется компонентами |

## 4. Создание типов элементов

### Этап типизации (выполняется один раз при инициализации)

#### 4.1 Построение осевой линии для шпильки

**Алгоритм построения осевой линии:**

1. **Определение параметров:**
   - Диаметр резьбы (d)
   - Общая длина шпильки (L)
   - Радиус изгиба (R) - зависит от типа болта
   - Тип болта (1.1, 1.2, 2.1, 5)

2. **Расчет точек осевой линии:**
   - Начальная точка: (0, 0, 0)
   - Точка начала изгиба: (0, 0, R)
   - Центр дуги изгиба: (R, 0, R)
   - Точка конца изгиба: (R, 0, 0)
   - Конечная точка: (R, 0, L - R)

3. **Создание сегментов кривой:**
   - **IfcLine** - прямолинейный сегмент от начальной точки до начала изгиба
   - **IfcCircularArcSegment3D** - дугообразный сегмент для изгиба
   - **IfcLine** - прямолинейный сегмент от конца изгиба до конечной точки

4. **Сборка составной кривой:**
   - Создание объекта **IfcCompositeCurve**
   - Установка атрибута **SelfIntersect = FALSE**
   - Добавление всех сегментов в правильном порядке

#### 4.2 Тип шпильки (IfcMechanicalFastenerType, ElementType "STUD")

**Структура создания типа шпильки:**

1. **Создание геометрии:**
   - Построение осевой линии через **IfcCompositeCurve**
   - Создание профиля **IfcCircleProfileDef** с радиусом = диаметр/2
   - Создание тела **IfcSweptDiskSolid** с осевой линией и профилем

2. **Создание типа:**
   - Создание объекта **IfcMechanicalFastenerType**
   - Установка атрибутов: Name, Description, ElementType="STUD", PredefinedType="USERDEFINED"
   - Присвоение геометрии через **IfcProductDefinitionShape**

3. **Создание материалов:**
   - Создание объекта **IfcMaterial** с параметрами по ГОСТ 19281-2014
   - Связывание материала с типом через **IfcRelAssociatesMaterial**

4. **Создание Property Sets:**
   - **Pset_MechanicalFastenerCommon**:
     - NominalDiameter
     - NominalLength
     - ThreadLength
     - ThreadPitch
   - Связывание PSets с типом через **IfcRelDefinesByProperties**

#### 4.3 Профили для гаек и шайб

**Алгоритм создания профиля гайки:**

1. **Внешний контур (шестиугольник):**
   - Расчет 6 вершин правильного шестиугольника
   - Создание объекта **IfcPolyline** с вершинами
   - Вершины рассчитываются по формуле: (R*cos(θ), R*sin(θ), 0)

2. **Внутреннее отверстие:**
   - Создание объекта **IfcCircleProfileDef**
   - Радиус = диаметр резьбы / 2 + зазор

3. **Профиль с отверстиями:**
   - Создание объекта **IfcArbitraryProfileDefWithVoids**
   - Установка **OuterCurve** = IfcPolyline
   - Установка **InnerCurves** = [IfcCircleProfileDef]

**Алгоритм создания профиля шайбы:**

1. **Внешний контур (круг):**
   - Создание объекта **IfcCircleProfileDef**
   - Радиус = внешний диаметр шайбы / 2

2. **Внутреннее отверстие:**
   - Создание объекта **IfcCircleProfileDef**
   - Радиус = диаметр резьбы / 2 + зазор

3. **Профиль с отверстиями:**
   - Создание объекта **IfcArbitraryProfileDefWithVoids**
   - Установка **OuterCurve** = внешний круг
   - Установка **InnerCurves** = [внутренний круг]

#### 4.4 Тип гаек (IfcMechanicalFastenerType, ElementType "NUT")

**Структура создания типа гайки:**

1. **Создание геометрии:**
   - Создание профиля через **IfcArbitraryProfileDefWithVoids**
   - Создание выдавленного тела **IfcExtrudedAreaSolid**
   - Установка направления выдавливания = (0, 0, 1)
   - Установка глубины выдавливания = высота гайки

2. **Создание типа:**
   - Создание объекта **IfcMechanicalFastenerType**
   - Установка атрибутов: Name, Description, ElementType="NUT", PredefinedType="USERDEFINED"

3. **Создание материалов и свойств:**
   - Аналогично типу шпильки

#### 4.5 Тип шайб (IfcMechanicalFastenerType, ElementType "WASHER")

**Структура создания типа шайбы:**

1. **Создание геометрии:**
   - Создание профиля через **IfcArbitraryProfileDefWithVoids**
   - Создание выдавленного тела **IfcExtrudedAreaSolid**
   - Установка направления выдавливания = (0, 0, 1)
   - Установка глубины выдавливания = толщина шайбы

2. **Создание типа:**
   - Создание объекта **IfcMechanicalFastenerType**
   - Установка атрибутов: Name, Description, ElementType="WASHER", PredefinedType="USERDEFINED"

3. **Создание материалов и свойств:**
   - Аналогично типу шпильки

#### 4.6 Тип сборки (IfcMechanicalFastenerType, PredefinedType "ANCHORBOLT")

**Структура создания типа сборки:**

1. **Создание типа:**
   - Создание объекта **IfcMechanicalFastenerType**
   - Установка атрибутов: Name, Description, ElementType="ANCHORBOLT", PredefinedType="ANCHORBOLT"

2. **Создание расширенных Property Sets:**
   - **Pset_MechanicalFastenerCommon**:
     - NominalDiameter
     - NominalLength
   - **Pset_ElementComponentCommon**:
     - CorrosionTreatment = "GALVANISED"
     - DeliveryType = "LOOSE"
     - Status = "NEW"
   - **Pset_ManufacturerTypeInformation**:
     - AssemblyPlace = "SITE"
     - ModelLabel = Name типа
     - OperationalDocument = "ГОСТ 24379.1-2012"
   - **Pset_MechanicalFastenerAnchorBolt**:
     - AnchorBoltLength
     - AnchorBoltDiameter
     - AnchorBoltThreadLength
     - AnchorBoltProtrusionLength

3. **Создание материалов:**
   - Аналогично другим типам

## 5. Генерация инстансов элементов

### Этап генерации (выполняется для каждого болта)

#### 5.1 Инстанс шпильки (IfcMechanicalFastener)

**Процесс создания инстанса шпильки:**

1. **Создание размещения в пространстве:**
   - Создание объекта **IfcAxis2Placement3D**
   - Установка **Location** = (0, 0, 0)
   - Установка **Axis** = (0, 0, 1)
   - Установка **RefDirection** = (1, 0, 0)

2. **Создание объекта размещения:**
   - Создание объекта **IfcLocalPlacement**
   - Связывание с родительским размещением (IfcBuildingStorey)

3. **Создание инстанса:**
   - Создание объекта **IfcMechanicalFastener**
   - Установка атрибутов: Name, Description, ObjectType="STUD"
   - Установка **ObjectPlacement** = IfcLocalPlacement

4. **Связывание с типом:**
   - Создание объекта **IfcRelDefinesByType**
   - Установка **RelatedObjects** = [инстанс шпильки]
   - Установка **RelatingType** = тип шпильки (IfcMechanicalFastenerType)

#### 5.2 Инстансы гаек (IfcMechanicalFastener)

**Процесс создания инстансов гаек:**

1. **Определение позиций гаек:**
   - Расчет координат размещения по оси шпильки
   - Учет высоты гаек и зазоров

2. **Создание размещения для каждой гайки:**
   - Аналогично инстансу шпильки
   - Установка **Location** = (x, y, z) для каждой гайки

3. **Создание инстансов:**
   - Создание объектов **IfcMechanicalFastener** для каждой гайки
   - Установка атрибутов: Name, Description, ObjectType="NUT"

4. **Связывание с типом:**
   - Создание объектов **IfcRelDefinesByType** для каждой гайки
   - Связывание с типом гайки

#### 5.3 Инстансы шайб (IfcMechanicalFastener)

**Процесс создания инстансов шайб:**

1. **Определение позиций шайб:**
   - Расчет координат размещения по оси шпильки
   - Учет толщины шайб и зазоров

2. **Создание размещения для каждой шайбы:**
   - Аналогично инстансу шпильки
   - Установка **Location** = (x, y, z) для каждой шайбы

3. **Создание инстансов:**
   - Создание объектов **IfcMechanicalFastener** для каждой шайбы
   - Установка атрибутов: Name, Description, ObjectType="WASHER"

4. **Связывание с типом:**
   - Создание объектов **IfcRelDefinesByType** для каждой шайбы
   - Связывание с типом шайбы

#### 5.4 Главный инстанс сборки (IfcMechanicalFastener)

**Процесс создания главного инстанса сборки:**

1. **Создание размещения сборки:**
   - Создание объекта **IfcLocalPlacement** для сборки
   - Связывание с родительским размещением (IfcBuildingStorey)

2. **Создание инстанса сборки:**
   - Создание объекта **IfcMechanicalFastener**
   - Установка атрибутов: Name, Description, ObjectType="ANCHORBOLT"
   - Установка **ObjectPlacement** = IfcLocalPlacement сборки

3. **Связывание с типом:**
   - Создание объекта **IfcRelDefinesByType**
   - Установка **RelatedObjects** = [инстанс сборки]
   - Установка **RelatingType** = тип сборки (IfcMechanicalFastenerType)

4. **Создание агрегации компонентов:**
   - Создание объекта **IfcRelAggregates**
   - Установка **RelatingObject** = инстанс сборки
   - Установка **RelatedObjects** = [инстанс шпильки, инстансы гаек, инстансы шайб]

## 6. Отношения между инстансами

### Типы отношений и их назначение

#### 6.1 IfcRelDefinesByType (инстансы → типы)

**Назначение:** Связывание инстансов с их типами для наследования геометрии и свойств

**Структура:**
- **GlobalId** - уникальный идентификатор отношения
- **OwnerHistory** - история владения
- **RelatedObjects** - список инстансов (массив)
- **RelatingType** - ссылка на тип (один объект)

**Примеры использования:**
- Связывание инстанса шпильки с типом шпильки
- Связывание инстансов гаек с типом гайки
- Связывание инстансов шайб с типом шайбы
- Связывание инстанса сборки с типом сборки

#### 6.2 IfcRelAggregates (главный → компоненты)

**Назначение:** Определение иерархии агрегации между сборкой и ее компонентами

**Структура:**
- **GlobalId** - уникальный идентификатор отношения
- **OwnerHistory** - история владения
- **RelatingObject** - родительский объект (сборка)
- **RelatedObjects** - дочерние объекты (компоненты)

**Пример использования:**
- Сборка (болт) → [шпилька, гайка1, шайба1, гайка2]

#### 6.3 IfcRelConnectsElements (связи между элементами)

**Назначение:** Определение физических соединений между элементами

**Структура:**
- **GlobalId** - уникальный идентификатор отношения
- **OwnerHistory** - история владения
- **ConnectionGeometry** - геометрия соединения (опционально)
- **RelatingElement** - первый элемент соединения
- **RelatedElement** - второй элемент соединения

**Примеры использования:**
- Шпилька ↔ Гайка1 (резьбовое соединение)
- Гайка1 ↔ Шайба1 (контактное соединение)
- Шайба1 ↔ Гайка2 (контактное соединение)

#### 6.4 IfcRelAssociatesMaterial (типы → материалы)

**Назначение:** Связывание типов с материалами

**Структура:**
- **GlobalId** - уникальный идентификатор отношения
- **OwnerHistory** - история владения
- **RelatedObjects** - список типов
- **RelatingMaterial** - материал

**Пример использования:**
- Тип шпильки, тип гайки, тип шайбы → Материал "09Г2С"

#### 6.5 IfcRelDefinesByProperties (типы/инстансы → свойства)

**Назначение:** Связывание объектов с наборами свойств (Property Sets)

**Структура:**
- **GlobalId** - уникальный идентификатор отношения
- **OwnerHistory** - история владения
- **RelatedObjects** - список объектов (типы или инстансы)
- **RelatingPropertyDefinition** - Property Set

**Примеры использования:**
- Тип шпильки → Pset_MechanicalFastenerCommon
- Тип сборки → Pset_MechanicalFastenerAnchorBolt
- Инстанс сборки → Переопределенные свойства (опционально)

## 7. Интеграция с интерфейсом

### Структура вызова из JavaScript

#### 7.1 Инициализация Pyodide

**Последовательность инициализации:**

1. **Загрузка Pyodide runtime:**
   ```javascript
   // Загрузка Pyodide из CDN
   async function loadPyodideRuntime() {
       const pyodide = await loadPyodide({
           indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/"
       });
       
       // Установка зависимостей
       await pyodide.loadPackage(["micropip"]);
       await pyodide.runPythonAsync(`
           import micropip
           await micropip.install('ifcopenshell')
       `);
       
       return pyodide;
   }
   ```

2. **Загрузка Python модулей:**
   ```javascript
   async function loadPythonModules(pyodide) {
       // Загрузка модулей из папки python/
       await pyodide.runPythonAsync(`
           import sys
           sys.path.append('/python')
           
           from ifc_model_builder import IFCModelBuilder
           from data.gost_24379_1_2012 import GOSTParameters
       `);
   }
   ```

#### 7.2 Передача параметров болта

**Структура объекта параметров:**

```javascript
const boltParameters = {
    // Основные параметры
    type: "1",                    // Тип болта: "1", "2", "5"
    execution: "1",               // Исполнение: "1", "2"
    diameter: 20,                 // Диаметр резьбы (мм)
    length: 800,                  // Общая длина (мм)
    
    // Материал
    material: "09Г2С",            // Марка стали по ГОСТ 19281-2014
    
    // Дополнительные компоненты
    hasAdditionalNut: true,       // Наличие дополнительной гайки
    hasWasher: true,              // Наличие шайбы
    
    // Расширенные параметры (опционально)
    threadLength: 150,            // Длина резьбовой части (мм)
    bendRadius: 50,               // Радиус изгиба (мм)
    
    // Настройки экспорта
    includeProperties: true,      // Включать свойства в модель
    validateModel: true           // Валидировать модель перед экспортом
};
```

#### 7.3 Вызов генерации модели

**Основной метод генерации:**

```javascript
async function generateIFCModel(pyodide, parameters) {
    try {
        // Вызов Python функции через Pyodide
        const result = await pyodide.runPythonAsync(`
            # Создание билдера модели
            builder = IFCModelBuilder()
            
            # Установка параметров
            builder.set_parameters(${JSON.stringify(parameters)})
            
            # Генерация модели
            ifc_model = builder.generate_model()
            
            # Валидация модели
            is_valid = builder.validate_model()
            
            # Экспорт в бинарные данные
            ifc_data = builder.export_to_bytes()
            
            # Возврат результата
            {
                "success": True,
                "ifc_data": ifc_data,
                "validation": is_valid,
                "element_count": builder.get_element_count(),
                "file_size": len(ifc_data)
            }
        `);
        
        return result;
    } catch (error) {
        console.error("Ошибка генерации IFC модели:", error);
        throw error;
    }
}
```

#### 7.4 Обработка результатов

**Обработка сгенерированной модели:**

```javascript
async function handleIFCGenerationResult(result) {
    if (result.success) {
        // Создание Blob из бинарных данных
        const blob = new Blob([result.ifc_data], { 
            type: 'application/ifc' 
        });
        
        // Обновление статистики
        updateStatistics({
            elementCount: result.element_count,
            fileSize: result.file_size,
            isValid: result.validation
        });
        
        // Предпросмотр 3D модели
        await preview3DModel(blob);
        
        // Предложение скачать файл
        offerDownload(blob);
    } else {
        showError("Ошибка генерации модели");
    }
}
```

## 8. Визуализация

### Архитектура 3D-предпросмотра

#### 8.1 Инициализация Three.js сцены

**Структура сцены:**

```javascript
class IFCCanvasViewer {
    constructor(containerElement) {
        this.container = containerElement;
        
        // Создание сцены
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // Создание камеры
        this.camera = new THREE.PerspectiveCamera(
            45, 
            containerElement.clientWidth / containerElement.clientHeight,
            0.1, 
            10000
        );
        this.camera.position.set(500, 500, 500);
        
        // Создание рендерера
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(
            containerElement.clientWidth, 
            containerElement.clientHeight
        );
        this.renderer.setPixelRatio(window.devicePixelRatio);
        
        // Добавление рендерера в контейнер
        containerElement.appendChild(this.renderer.domElement);
        
        // Создание контроллера орбит
        this.controls = new THREE.OrbitControls(
            this.camera, 
            this.renderer.domElement
        );
        this.controls.enableDamping = true;
        
        // Создание сетки и осей
        this.createGrid();
        this.createAxes();
        
        // Запуск анимации
        this.animate();
    }
    
    createGrid() {
        // Создание сетки для ориентации
    }
    
    createAxes() {
        // Создание осей координат
    }
    
    animate() {
        // Цикл анимации
        requestAnimationFrame(() => this.animate());
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}
```

#### 8.2 Конвертация геометрии IFC в меш

**Метод конвертации:**

```javascript
class IFCGeometryConverter {
    constructor(pyodide) {
        this.pyodide = pyodide;
    }
    
    async convertIFCToMesh(ifcData) {
        try {
            // Вызов Python функции для конвертации
            const geometryData = await this.pyodide.runPythonAsync(`
                import ifcopenshell
                import ifcopenshell.geom
                
                # Загрузка IFC модели
                ifc_file = ifcopenshell.file.from_string(ifc_data.decode('utf-8'))
                
                # Настройка параметров геометрии
                settings = ifcopenshell.geom.settings()
                settings.set(settings.USE_WORLD_COORDS, True)
                settings.set(settings.SEW_SHELLS, True)
                
                # Извлечение геометрии для всех элементов
                geometry_elements = []
                
                for element in ifc_file.by_type("IfcMechanicalFastener"):
                    try:
                        shape = ifcopenshell.geom.create_shape(settings, element)
                        
                        # Извлечение вершин и граней
                        verts = shape.geometry.verts
                        faces = shape.geometry.faces
                        
                        # Форматирование данных для Three.js
                        geometry_data = {
                            "element_id": element.GlobalId,
                            "element_type": element.ObjectType,
                            "vertices": list(verts),
                            "faces": list(faces),
                            "transformation": list(shape.transformation.matrix.data)
                        }
                        
                        geometry_elements.append(geometry_data)
                    except Exception as e:
                        print(f"Ошибка обработки элемента {element.GlobalId}: {e}")
                
                geometry_elements
            `);
            
            return geometryData;
        } catch (error) {
            console.error("Ошибка конвертации геометрии:", error);
            throw error;
        }
    }
}
```

#### 8.3 Создание мешей Three.js

**Процесс создания визуальных объектов:**

```javascript
class ThreeJSModelBuilder {
    constructor(scene) {
        this.scene = scene;
        this.elementMeshes = new Map();
        this.materials = this.createMaterials();
    }
    
    createMaterials() {
        return {
            stud: new THREE.MeshPhongMaterial({ 
                color: 0x8B4513, 
                specular: 0x111111,
                shininess: 30
            }),
            nut: new THREE.MeshPhongMaterial({ 
                color: 0xA9A9A9, 
                specular: 0x333333,
                shininess: 50
            }),
            washer: new THREE.MeshPhongMaterial({ 
                color: 0xD3D3D3, 
                specular: 0x222222,
                shininess: 40
            }),
            selected: new THREE.MeshPhongMaterial({ 
                color: 0xFFD700, 
                emissive: 0x444400,
                shininess: 100
            })
        };
    }
    
    createMeshFromGeometry(geometryData) {
        // Создание геометрии Three.js
        const geometry = new THREE.BufferGeometry();
        
        // Установка вершин
        const vertices = new Float32Array(geometryData.vertices);
        geometry.setAttribute('position', new THREE.BufferAttribute(vertices, 3));
        
        // Установка граней (если есть)
        if (geometryData.faces && geometryData.faces.length > 0) {
            const indices = new Uint32Array(geometryData.faces);
            geometry.setIndex(new THREE.BufferAttribute(indices, 1));
        }
        
        // Выбор материала по типу элемента
        let material;
        switch (geometryData.element_type) {
            case "STUD":
                material = this.materials.stud;
                break;
            case "NUT":
                material = this.materials.nut;
                break;
            case "WASHER":
                material = this.materials.washer;
                break;
            default:
                material = this.materials.nut;
        }
        
        // Создание меша
        const mesh = new THREE.Mesh(geometry, material);
        
        // Применение трансформации
        if (geometryData.transformation) {
            const matrix = new THREE.Matrix4();
            matrix.fromArray(geometryData.transformation);
            mesh.applyMatrix4(matrix);
        }
        
        // Добавление в сцену
        this.scene.add(mesh);
        
        // Сохранение ссылки на меш
        this.elementMeshes.set(geometryData.element_id, {
            mesh: mesh,
            type: geometryData.element_type,
            originalMaterial: material
        });
        
        return mesh;
    }
    
    selectElement(elementId) {
        // Сброс выделения всех элементов
        this.elementMeshes.forEach(element => {
            element.mesh.material = element.originalMaterial;
        });
        
        // Выделение выбранного элемента
        const selectedElement = this.elementMeshes.get(elementId);
        if (selectedElement) {
            selectedElement.mesh.material = this.materials.selected;
            return true;
        }
        
        return false;
    }
}
```

#### 8.4 Обработка выбора элементов

**Система выбора элементов:**

```javascript
class ElementSelector {
    constructor(viewer, modelBuilder, propertyPanel) {
        this.viewer = viewer;
        this.modelBuilder = modelBuilder;
        this.propertyPanel = propertyPanel;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Установка обработчика кликов
        this.viewer.renderer.domElement.addEventListener('click', 
            this.onClick.bind(this));
    }
    
    onClick(event) {
        // Расчет позиции мыши в нормализованных координатах
        this.mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        
        // Обновление луча
        this.raycaster.setFromCamera(this.mouse, this.viewer.camera);
        
        // Поиск пересечений
        const intersects = this.raycaster.intersectObjects(
            this.viewer.scene.children, 
            true
        );
        
        if (intersects.length > 0) {
            // Нахождение ближайшего пересечения
            const closestIntersection = intersects[0];
            
            // Поиск элемента по мешу
            const elementId = this.findElementIdByMesh(closestIntersection.object);
            
            if (elementId) {
                // Выделение элемента
                this.modelBuilder.selectElement(elementId);
                
                // Загрузка свойств элемента
                this.loadElementProperties(elementId);
            }
        }
    }
    
    findElementIdByMesh(mesh) {
        // Поиск элемента в мапе по мешу
        for (const [elementId, elementData] of this.modelBuilder.elementMeshes) {
            if (elementData.mesh === mesh || mesh.parent === elementData.mesh) {
                return elementId;
            }
        }
        return null;
    }
    
    async loadElementProperties(elementId) {
        // Загрузка свойств элемента через Pyodide
        const properties = await this.loadPropertiesFromIFC(elementId);
        
        // Отображение свойств в панели
        this.propertyPanel.displayProperties(properties);
    }
    
    async loadPropertiesFromIFC(elementId) {
        // Вызов Python функции для получения свойств
        return await this.pyodide.runPythonAsync(`
            # Получение элемента по GlobalId
            element = ifc_file.by_guid("${elementId}")
            
            # Извлечение свойств
            properties = {}
            
            # Базовые атрибуты
            properties["GlobalId"] = element.GlobalId
            properties["Name"] = element.Name
            properties["ObjectType"] = element.ObjectType
            
            # Property Sets
            for rel in element.IsDefinedBy:
                if rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                    pset = rel.RelatingPropertyDefinition
                    properties[pset.Name] = {}
                    
                    for prop in pset.HasProperties:
                        if prop.is_a("IfcPropertySingleValue"):
                            properties[pset.Name][prop.Name] = prop.NominalValue
            
            properties
        `);
    }
}
```

## 9. Структура данных ГОСТ

### Справочник параметров по ГОСТ 24379.1-2012

#### 9.1 Доступные типы и исполнения болтов

| Тип болта | Исполнение | Номер позиции шпильки | Описание |
|-----------|------------|----------------------|----------|
| 1 | 1 | 1 | Болт с одним изгибом, прямым концом |
| 1 | 2 | 2 | Болт с одним изгибом, загнутым концом |
| 2 | 1 | 3 | Болт с двумя изгибами |
| 5 | - | 7 | Болт прямой с коническим концом |

#### 9.2 Диапазоны диаметров резьбы

| Диаметр резьбы (мм) | Обозначение | Примечание |
|---------------------|-------------|------------|
| 12 | М12 | Минимальный диаметр |
| 16 | М16 | |
| 20 | М20 | |
| 24 | М24 | |
| 30 | М30 | |
| 36 | М36 | |
| 42 | М42 | |
| 48 | М48 | |
| 56 | М56 | |
| 64 | М64 | |
| 72 | М72 | |
| 80 | М80 | Максимальный диаметр |

#### 9.3 Стандартные длины болтов

| Диаметр (мм) | Стандартные длины (мм) |
|--------------|------------------------|
| 12-24 | 400, 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000 |
| 27-48 | 500, 600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400 |
| 52-80 | 600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600, 2800, 3000 |

#### 9.4 Параметры гаек по ГОСТ 5915-70

| Диаметр резьбы (мм) | Высота гайки (мм) | Размер под ключ (мм) | Масса (кг) |
|---------------------|-------------------|----------------------|------------|
| 12 | 10.0 | 19 | 0.015 |
| 16 | 13.0 | 24 | 0.030 |
| 20 | 16.0 | 30 | 0.055 |
| 24 | 19.0 | 36 | 0.090 |
| 30 | 22.5 | 46 | 0.160 |
| 36 | 27.0 | 55 | 0.280 |
| 42 | 31.0 | 65 | 0.450 |
| 48 | 35.0 | 75 | 0.680 |
| 56 | 40.0 | 85 | 1.050 |
| 64 | 45.0 | 95 | 1.550 |
| 72 | 50.0 | 105 | 2.200 |
| 80 | 55.0 | 115 | 3.000 |

#### 9.5 Параметры шайб по ГОСТ 24379.1-2012

| Диаметр резьбы (мм) | Внешний диаметр (мм) | Толщина (мм) | Масса (кг) |
|---------------------|----------------------|--------------|------------|
| 12 | 24 | 3.0 | 0.005 |
| 16 | 30 | 3.5 | 0.010 |
| 20 | 37 | 4.0 | 0.018 |
| 24 | 44 | 4.5 | 0.028 |
| 30 | 54 | 5.0 | 0.048 |
| 36 | 64 | 5.5 | 0.075 |
| 42 | 74 | 6.0 | 0.110 |
| 48 | 84 | 6.5 | 0.160 |
| 56 | 97 | 7.0 | 0.230 |
| 64 | 110 | 7.5 | 0.320 |
| 72 | 125 | 8.0 | 0.450 |
| 80 | 140 | 8.5 | 0.620 |

#### 9.6 Материалы по ГОСТ 19281-2014

| Марка стали | Описание | Применение | Предел прочности (МПа) |
|-------------|----------|------------|------------------------|
| 09Г2С | Низколегированная конструкционная сталь | Основной материал | 490 |
| ВСт3пс2 | Углеродистая сталь обыкновенного качества | Альтернатива | 370 |
| 20Г2Р | Низколегированная сталь повышенной прочности | Для ответственных конструкций | 590 |
| 10Г2Б | Низколегированная сталь для сварных конструкций | Для сварных соединений | 510 |
| 15Г2АФД | Низколегированная сталь для мостовых конструкций | Для мостовых конструкций | 530 |

#### 9.7 Радиусы изгибов шпилек

| Тип болта | Исполнение | Радиус изгиба (мм) | Примечание |
|-----------|------------|-------------------|------------|
| 1 | 1 | 2.5×диаметр | Минимум 50 мм |
| 1 | 2 | 2.5×диаметр | Минимум 50 мм |
| 2 | 1 | 3.0×диаметр | Минимум 60 мм |
| 5 | - | Прямой (без изгиба) | Конический конец |

## 10. План реализации

### Таблица этапов с оценочными сроками

| Этап | Подэтап | Описание | Срок | Зависимости |
|------|---------|----------|------|-------------|
| **1. Подготовительный** | 1.1 | Анализ требований и спецификаций | 3 дня | - |
| | 1.2 | Создание архитектуры приложения | 2 дня | 1.1 |
| | 1.3 | Подготовка структуры проекта | 1 день | 1.2 |
| | **Итого этап 1** | | **6 дней** | |
| **2. Базовая инфраструктура** | 2.1 | Настройка HTML/CSS интерфейса | 3 дня | 1.3 |
| | 2.2 | Интеграция Pyodide runtime | 2 дня | 2.1 |
| | 2.3 | Настройка Three.js сцены | 2 дня | 2.1 |
| | 2.4 | Создание системы событий | 1 день | 2.2, 2.3 |
| | **Итого этап 2** | | **8 дней** | |
| **3. Ядро генерации IFC** | 3.1 | Создание базового IFC файла | 2 дня | 2.2 |
| | 3.2 | Реализация создания типов элементов | 4 дня | 3.1 |
| | 3.3 | Реализация создания инстансов | 3 дня | 3.2 |
| | 3.4 | Реализация отношений между элементами | 3 дня | 3.3 |
| | 3.5 | Интеграция справочников ГОСТ | 2 дня | 3.4 |
| | **Итого этап 3** | | **14 дней** | |
| **4. Геометрия элементов** | 4.1 | Реализация геометрии шпильки (IfcSweptDiskSolid) | 3 дня | 3.2 |
| | 4.2 | Реализация профилей гаек и шайб | 2 дня | 3.2 |
| | 4.3 | Реализация геометрии гаек и шайб (IfcExtrudedAreaSolid) | 2 дня | 4.2 |
| | 4.4 | Построение осевых линий для разных типов болтов | 3 дня | 4.1 |
| | **Итого этап 4** | | **10 дней** | |
| **5. Свойства и материалы** | 5.1 | Реализация стандартных Property Sets | 3 дня | 3.2 |
| | 5.2 | Реализация материалов по ГОСТ 19281-2014 | 2 дня | 3.2 |
| | 5.3 | Реализация наследования свойств | 2 дня | 5.1 |
| | 5.4 | Возможность переопределения свойств | 2 дня | 5.3 |
| | **Итого этап 5** | | **9 дней** | |
| **6. Визуализация 3D** | 6.1 | Конвертация геометрии IFC в Three.js меш | 4 дня | 4.1, 4.3 |
| | 6.2 | Реализация выбора элементов | 3 дня | 6.1 |
| | 6.3 | Отображение свойств выбранного элемента | 2 дня | 6.2, 5.1 |
| | 6.4 | Оптимизация производительности рендеринга | 3 дня | 6.1 |
| | **Итого этап 6** | | **12 дней** | |
| **7. Интерфейс пользователя** | 7.1 | Форма ввода параметров болта | 3 дня | 2.1 |
| | 7.2 | Валидация входных данных | 2 дня | 7.1 |
| | 7.3 | Панель отображения свойств | 2 дня | 6.3 |
| | 7.4 | Контролы 3D-визуализатора | 2 дня | 6.1 |
| | 7.5 | Экспорт и скачивание IFC файла | 2 дня | 3.5 |
| | **Итого этап 7** | | **11 дней** | |
| **8. Тестирование и отладка** | 8.1 | Модульное тестирование | 3 дня | 3-7 |
| | 8.2 | Интеграционное тестирование | 3 дня | 8.1 |
| | 8.3 | Тестирование визуализации | 2 дня | 6, 8.2 |
| | 8.4 | Валидация IFC файлов | 2 дня | 3, 8.2 |
| | 8.5 | Оптимизация производительности | 3 дня | 8.1-8.4 |
| | **Итого этап 8** | | **13 дней** | |
| **9. Документация** | 9.1 | Техническая документация | 3 дня | 1-8 |
| | 9.2 | Руководство пользователя | 2 дня | 7 |
| | 9.3 | Документация по ГОСТ | 2 дня | 9 |
| | **Итого этап 9** | | **7 дней** | |
| **ИТОГО** | | | **90 дней** | |

### Критические пути

1. **Основной путь:** 1 → 2 → 3 → 4 → 6 → 8 = 65 дней
2. **Параллельный путь (интерфейс):** 2 → 7 → 8 = 32 дня
3. **Параллельный путь (свойства):** 3 → 5 → 8 = 36 дней

### Риски и митигации

| Риск | Вероятность | Влияние | Митигация |
|------|-------------|---------|-----------|
| Ограничения производительности Pyodide | Средняя | Высокое | Оптимизация алгоритмов, кэширование типов |
| Сложность геометрии изогнутых болтов | Высокая | Среднее | Пошаговая реализация, тестирование |
| Валидация IFC файлов | Средняя | Высокое | Использование ifcopenshell.validate |
| Кросс-браузерная совместимость | Низкая | Среднее | Тестирование в разных браузерах |
| Размер модели для сложных болтов | Средняя | Среднее | Оптимизация геометрии, упрощение мешей |

## 11. Итоговая структура IFC-файла

### Пример фрагмента IFC-файла (формат STEP)

```
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView_V2.0]'),'2;1');
FILE_NAME('AnchorBolt_1.1_M20x800.ifc','2026-02-15',(''),(''),'IFC Model Generator','IFC Model Generator','');
FILE_SCHEMA(('IFC4'));
ENDSEC;

DATA;
#1=IFCPERSON($,$,'Developer',$,$,$,$,$);
#2=IFCORGANIZATION($,'IFC Generator Team',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION($,$,'IFC Model Generator','1.0');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,$,$,1707984000);

#10=IFCPROJECT('2xV4$yBcH0qO8nqPE$FO5z',#5,'Anchor Bolt Project',$,$,$,$,(#20),#15,$);
#11=IFCDIRECTION((0.,0.,1.));
#12=IFCDIRECTION((1.,0.,0.));
#13=IFCCARTESIANPOINT((0.,0.,0.));
#14=IFCAXIS2PLACEMENT3D(#13,#11,#12);
#15=IFCUNITASSIGNMENT((#16,#17,#18,#19));
#16=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#17=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#18=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#19=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);

#20=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#14,#21);
#21=IFCAXIS2PLACEMENT3D(#13,#11,#12);

#30=IFCSITE('3aB4$yCcH1qP9nrQF$GP6a',#5,'Default Site',$,$,#31,$,$,.ELEMENT.,$,$,$,$);
#31=IFCLOCALPLACEMENT($,#14);

#40=IFCBUILDING('4bC5$zDdI2rQ0osRG$HQ7b',#5,'Default Building',$,$,#41,$,$,.ELEMENT.,$,$,$);
#41=IFCLOCALPLACEMENT(#31,#14);

#50=IFCBUILDINGSTOREY('5cD6$aEeJ3sR1ptSH$IR8c',#5,'Default Storey',$,$,#51,$,$,.ELEMENT.,0.);
#51=IFCLOCALPLACEMENT(#41,#14);

// ============ ТИПЫ ЭЛЕМЕНТОВ ============

// Тип шпильки (STUD)
#100=IFCCIRCLEPROFILEDEF(.AREA.,'Stud Profile',#13,10.);
#101=IFCCARTESIANPOINT((0.,0.,0.));
#102=IFCCARTESIANPOINT((0.,0.,50.));
#103=IFCCARTESIANPOINT((50.,0.,50.));
#104=IFCCARTESIANPOINT((50.,0.,0.));
#105=IFCCARTESIANPOINT((50.,0.,750.));
#106=IFCLINE(#101,#102);
#107=IFCCIRCULARARCSEGMENT3D(#102,#103,#104);
#108=IFCLINE(#104,#105);
#109=IFCCOMPOSITECURVE((#106,#107,#108),.F.);
#110=IFCSWEPTDISKSOLID(#109,10.,$,$,$);
#111=IFCPRODUCTDEFINITIONSHAPE($,$,(#110));

#120=IFCMATERIAL('09Г2С','Сталь 09Г2С по ГОСТ 19281-2014','STEEL');
#121=IFCMATERIALLAYER(#120,0.,$);
#122=IFCMATERIALLAYERSET((#121),$);
#123=IFCMATERIALLAYERSETUSAGE(#122,.AXIS2.,.POSITIVE.,0.,$);

#130=IFCPROPERTYSINGLEVALUE('NominalDiameter',$,IFCPOSITIVERATIOMEASURE(20.),$);
#131=IFCPROPERTYSINGLEVALUE('NominalLength',$,IFCPOSITIVERATIOMEASURE(800.),$);
#132=IFCPROPERTYSINGLEVALUE('ThreadLength',$,IFCPOSITIVERATIOMEASURE(150.),$);
#133=IFCPROPERTYSET('6dE7$bFfK4tS2quTI$JS9d',#5,'Pset_MechanicalFastenerCommon',$,(#130,#131,#132));

#140=IFCMECHANICALFASTENERTYPE('7eF8$cGgL5uT3rvUJ$LTAe',#5,'Шпилька 1.М20 х 800 09Г2С ГОСТ 24379.1-2012','Шпилька фундаментного болта','STUD',$,(#133),#111,$,.USERDEFINED.);

#150=IFCRELASSOCIATESMATERIAL('8fG9$dHhM6vU4swVK$MUBf',#5,$,$,(#140),#123);

// Тип гайки (NUT)
#200=IFCCARTESIANPOINT((10.,0.,0.));
#201=IFCCARTESIANPOINT((5.,8.66,0.));
#202=IFCCARTESIANPOINT((-5.,8.66,0.));
#203=IFCCARTESIANPOINT((-10.,0.,0.));
#204=IFCCARTESIANPOINT((-5.,-8.66,0.));
#205=IFCCARTESIANPOINT((5.,-8.66,0.));
#206=IFCCARTESIANPOINT((10.,0.,0.));
#207=IFCPOLYLINE((#200,#201,#202,#203,#204,#205,#206));
#208=IFCCIRCLEPROFILEDEF(.CURVE.,'Nut Hole',#13,8.);
#209=IFCARBITRARYPROFILEDEFWITHVOIDS(.AREA.,'Nut Profile',#207,(#208));
#210=IFCAXIS2PLACEMENT3D(#13,#11,#12);
#211=IFCEXTRUDEDAREASOLID(#209,#210,#11,16.);
#212=IFCPRODUCTDEFINITIONSHAPE($,$,(#211));

#220=IFCPROPERTYSINGLEVALUE('Height',$,IFCPOSITIVERATIOMEASURE(16.),$);
#221=IFCPROPERTYSINGLEVALUE('WidthAcrossFlats',$,IFCPOSITIVERATIOMEASURE(30.),$);
#222=IFCPROPERTYSET('9gH0$eIiN7wV5txWL$NVCg',#5,'Pset_MechanicalFastenerCommon',$,(#130,#220,#221));

#230=IFCMECHANICALFASTENERTYPE('0hI1$fJjO8xW6uyXM$OWDh',#5,'Гайка М20 ГОСТ 5915-70','Гайка фундаментного болта','NUT',$,(#222),#212,$,.USERDEFINED.);
#240=IFCRELASSOCIATESMATERIAL('1iJ2$gKkP9yX7vzYN$PXDi',#5,$,$,(#230),#123);

// Тип шайбы (WASHER)
#300=IFCCIRCLEPROFILEDEF(.AREA.,'Washer Outer',#13,18.5);
#301=IFCCIRCLEPROFILEDEF(.CURVE.,'Washer Hole',#13,11.);
#302=IFCARBITRARYPROFILEDEFWITHVOIDS(.AREA.,'Washer Profile',#300,(#301));
#303=IFCEXTRUDEDAREASOLID(#302,#210,#11,4.);
#304=IFCPRODUCTDEFINITIONSHAPE($,$,(#303));

#310=IFCPROPERTYSINGLEVALUE('Thickness',$,IFCPOSITIVERATIOMEASURE(4.),$);
#311=IFCPROPERTYSINGLEVALUE('OuterDiameter',$,IFCPOSITIVERATIOMEASURE(37.),$);
#312=IFCPROPERTYSET('2jK3$hLlQ0zY8wzZO$QYEj',#5,'Pset_MechanicalFastenerCommon',$,(#130,#310,#311));

#320=IFCMECHANICALFASTENERTYPE('3kL4$iMmR1aZ9xaAP$RZFk',#5,'Шайба М20 ГОСТ 24379.1-2012','Шайба фундаментного болта','WASHER',$,(#312),#304,$,.USERDEFINED.);
#330=IFCRELASSOCIATESMATERIAL('4lM5$jNnS2ba0ybBQ$SAGl',#5,$,$,(#320),#123);

// Тип сборки (ANCHORBOLT)
#400=IFCPROPERTYSINGLEVALUE('CorrosionTreatment',$,IFCLABEL('GALVANISED'),$);
#401=IFCPROPERTYSINGLEVALUE('DeliveryType',$,IFCLABEL('LOOSE'),$);
#402=IFCPROPERTYSINGLEVALUE('Status',$,IFCLABEL('NEW'),$);
#403=IFCPROPERTYSET('5mN6$kOoT3cb1zcCR$TBHm',#5,'Pset_ElementComponentCommon',$,(#400,#401,#402));

#410=IFCPROPERTYSINGLEVALUE('AssemblyPlace',$,IFCLABEL('SITE'),$);
#411=IFCPROPERTYSINGLEVALUE('ModelLabel',$,IFCLABEL('Болт 1.1.М20 х 800 09Г2С ГОСТ 24379.1-2012'),$);
#412=IFCPROPERTYSINGLEVALUE('OperationalDocument',$,IFCLABEL('ГОСТ 24379.1-2012'),$);
#413=IFCPROPERTYSET('6nO7$lPpU4dc2adDS$UCIn',#5,'Pset_ManufacturerTypeInformation',$,(#410,#411,#412));

#420=IFCPROPERTYSINGLEVALUE('AnchorBoltLength',$,IFCPOSITIVERATIOMEASURE(800.),$);
#421=IFCPROPERTYSINGLEVALUE('AnchorBoltDiameter',$,IFCPOSITIVERATIOMEASURE(20.),$);
#422=IFCPROPERTYSINGLEVALUE('AnchorBoltThreadLength',$,IFCPOSITIVERATIOMEASURE(150.),$);
#423=IFCPROPERTYSINGLEVALUE('AnchorBoltProtrusionLength',$,IFCPOSITIVERATIOMEASURE(150.),$);
#424=IFCPROPERTYSET('7oP8$mQqV5ed3beET$VDJo',#5,'Pset_MechanicalFastenerAnchorBolt',$,(#420,#421,#422,#423));

#430=IFCMECHANICALFASTENERTYPE('8pQ9$nRrW6fe4cfFU$WEKp',#5,'Болт 1.1.М20 х 800 09Г2С ГОСТ 24379.1-2012','Фундаментный болт по ГОСТ 24379.1-2012','ANCHORBOLT',$,(#133,#403,#413,#424),$,$,.ANCHORBOLT.);
#440=IFCRELASSOCIATESMATERIAL('9qR0$oSsX7gf5dgGV$XFLq',#5,$,$,(#430),#123);

// ============ ИНСТАНСЫ ЭЛЕМЕНТОВ ============

// Инстанс шпильки
#500=IFCLOCALPLACEMENT(#51,#14);
#501=IFCMECHANICALFASTENER('0rS1$pTtY8hg6ehHW$YGMr',#5,'Шпилька 1.М20 х 800 09Г2С ГОСТ 24379.1-2012',$,'Шпилька фундаментного болта',#500,$,$,20.,800.,'STUD');
#502=IFCRELDEFINESBYTYPE('1sT2$qUuZ9ih7fiIX$ZHNs',#5,$,$,(#501),#140);

// Инстанс гайки 1
#510=IFCLOCALPLACEMENT(#51,#14);
#511=IFCMECHANICALFASTENER('2tU3$rVvA0ji8gjJY$AIOT',#5,'Гайка М20 ГОСТ 5915-70',$,'Гайка фундаментного болта',#510,$,$,20.,$,'NUT');
#512=IFCRELDEFINESBYTYPE('3uV4$sWwB1kj9hkKZ$BJPU',#5,$,$,(#511),#230);

// Инстанс шайбы
#520=IFCLOCALPLACEMENT(#51,#14);
#521=IFCMECHANICALFASTENER('4vW5$tXxC2lk0ilLa$CKQV',#5,'Шайба М20 ГОСТ 24379.1-2012',$,'Шайба фундаментного болта',#520,$,$,20.,$,'WASHER');
#522=IFCRELDEFINESBYTYPE('5wX6$uYyD3ml1jmMb$DLRW',#5,$,$,(#521),#320);

// Инстанс гайки 2
#530=IFCLOCALPLACEMENT(#51,#14);
#531=IFCMECHANICALFASTENER('6xY7$vZzE4nm2knNc$EMSW',#5,'Гайка М20 ГОСТ 5915-70',$,'Гайка фундаментного болта',#530,$,$,20.,$,'NUT');
#532=IFCRELDEFINESBYTYPE('7yZ8$wAAf5on3loOd$FNXT',#5,$,$,(#531),#230);

// Главный инстанс сборки
#540=IFCLOCALPLACEMENT(#51,#14);
#541=IFCMECHANICALFASTENER('8zA9$xBBg6po4mpPe$GOYU',#5,'Болт 1.1.М20 х 800 09Г2С ГОСТ 24379.1-2012',$,'Фундаментный болт по ГОСТ 24379.1-2012',#540,$,$,20.,800.,'ANCHORBOLT');
#542=IFCRELDEFINESBYTYPE('9AB0$yCCh7qp5nqQf$HPZV',#5,$,$,(#541),#430);

// ============ ОТНОШЕНИЯ ============

// Агрегация компонентов
#600=IFCRELAGGREGATES('0BC1$zDDi8rq6orRg$IQAW',#5,$,$,#541,(#501,#511,#521,#531));

// Соединения элементов
#610=IFCRELCONNECTSELEMENTS('1CD2$AEjJ9sr7psSh$JRBX',#5,$,$,$,#501,#511);
#611=IFCRELCONNECTSELEMENTS('2DE3$BFkK0ts8qtTi$KSCY',#5,$,$,$,#511,#521);
#612=IFCRELCONNECTSELEMENTS('3EF4$CGlL1ut9ruUj$LTDZ',#5,$,$,$,#521,#531);

ENDSEC;
END-ISO-10303-21;
```

## 12. Преимущества архитектуры

### Таблица преимуществ типо-инстансного подхода

| Преимущество | Описание | Влияние на проект |
|--------------|----------|-------------------|
| **Единая точка определения** | Все параметры определяются в типах, инстансы наследуют свойства | Упрощение поддержки, снижение ошибок |
| **Снижение объема данных** | Геометрия и свойства хранятся один раз в типе, а не в каждом инстансе | Меньший размер IFC файла (до 40% экономии) |
| **Упрощенное версионирование** | Изменение типа автоматически применяется ко всем инстансам | Легкое обновление параметров |
| **Соответствие стандарту IFC** | Архитектура полностью соответствует концепции типов в IFC4 | Валидные IFC файлы, совместимость с ПО |
| **Повторное использование** | Типы могут использоваться в разных проектах и болтах | Модульность кода |
| **Оптимизация производительности** | Меньше данных для обработки при генерации и визуализации | Быстрая работа в браузере |
| **Гибкость наследования** | Возможность переопределения свойств на уровне инстансов | Поддержка специфических случаев |
| **Структурированность** | Четкая иерархия типов и инстансов | Удобство отладки и понимания кода |
| **Поддержка стандартов** | Автоматическое применение ГОСТ параметров к типам | Гарантированное соответствие нормативам |
| **Масштабируемость** | Легкое добавление новых типов болтов и компонентов | Расширяемость функционала |

### Сравнение подходов

| Критерий | Типо-инстансный подход | Подход без типов |
|----------|------------------------|------------------|
| Размер IFC файла | Меньше (оптимизирован) | Больше (дублирование) |
| Производительность | Выше (меньше данных) | Ниже |
| Поддерживаемость | Выше (единая точка) | Ниже (разбросано) |
| Соответствие IFC | Полное | Частичное |
| Гибкость | Высокая | Ограниченная |
| Сложность реализации | Средняя | Низкая |
| Масштабируемость | Высокая | Средняя |

### Рекомендации по использованию

1. **Всегда использовать типы** для всех элементов сборки
2. **Определять типы один раз** при инициализации приложения
3. **Кэшировать типы** для повторного использования
4. **Наследовать свойства** через отношения IfcRelDefinesByType
5. **Переопределять только необходимые** свойства на уровне инстансов
6. **Валидировать модель** после генерации для проверки целостности отношений

---

*План разработан в соответствии с требованиями ГОСТ 24379.1-2012 и спецификацией IFC4 ADD2 TC1. Все примеры структур и алгоритмов предназначены исключительно для планирования разработки и не содержат рабочего кода.*