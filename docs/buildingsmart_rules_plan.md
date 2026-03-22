# План реализации тестов buildingsmart IFC Validation Rules

## Статус на текущий момент

**Реализовано (74 правила):**
- OJT001, SPS001, SPS002, SPS003, SPS005, SPS007, SPS008, MAT000, GEM051, GEM052
- PJS101, PJS003, IFC105, MPD001, LOP000, SPS003, ASM000, BRP002
- PJS001, GEM003, GEM004, OJP000, OJP001
- IFC101, IFC102, PJS000, PJS002, GEM001, GEM002, GEM111, GEM112, GEM113, BRP003, SWE001, SWE002
- CLS000, CTX000, GRP000, GRP001, LAY000, MAT000 (полная), POR000, PSE001, PSE002, QTY000, QTY001, SPA000, VER000, VRT000, GEM011
- GRF000, GRF001, GRF002, GRF003, GRF004, GRF005, GRF006, GRF007, GRF008
- ALB000, ALB002, ALB003, ALB004, ALB010, ALB012, ALB015, ALB021, ALB022, ALB023, ALB030, ALB031, ALB032
- ALS000, ALS004, ALS005, ALS006, ALS007, ALS008, ALS010, ALS011, ALS012, ALS015, ALS016, ALS017
- BBX000, BBX001, AXG000, ANN000, GDP000

**Всего активно правил: 74**
**Осталось реализовать: 0 правил** ✅

---

## Приоритет 1: Критичные для генератора анкерных болтов (15 правил)

Эти правила напрямую влияют на корректность генерируемых IFC файлов.

| Код | Категория | Описание | Трудоёмкость | Зависимости |
|-----|-----------|----------|---------------|-------------|
| **IFC101** | IFC | Only official ifc versions allowed | 1ч | - |
| **IFC102** | IFC | Absence of deprecated entities | 1ч | - |
| **PJS000** | Project | Project presence | 0.5ч | - |
| **PJS002** | Project | Correct elements related to project | 2ч | - |
| **GEM001** | Geometry | Closed shell edge usage | 2ч | BRP002 |
| **GEM002** | Geometry | Space representation | 1ч | - |
| **GEM111** | Geometry | No duplicated points within polyloop/polyline | 2ч | - |
| **GEM112** | Geometry | No duplicated points within indexed poly curve | 2ч | - |
| **GEM113** | Geometry | Indexed poly curve arcs - no colinear points | 2ч | GEM112 |
| **BRP003** | BREP | Planar faces are planar | 2ч | BRP002 |
| **SWE001** | Sweeps | Arbitrary profile boundary no self intersections | 3ч | - |
| **SWE002** | Sweeps | Mirroring within IfcDerivedProfileDef not used | 1ч | - |
| **LOP000** | Placement | Local placement (полная проверка) | 1ч | OJP000 |
| **SPS002** | Spatial | Correct spatial breakdown | 2ч | SPS001 |
| **SPS008** | Spatial | Spatial container representations | 2ч | SPS007 |

**Итого: ~25 часов**

---

## Приоритет 2: Общие правила валидации (20 правил)

Правила которые могут быть проверены в любом IFC файле.

| Код | Категория | Описание | Трудоёмкость | Зависимости |
|-----|-----------|----------|---------------|-------------|
| **PJS003** | Project | Globally Unique Identifiers (полная проверка) | 1ч | - |
| **CLS000** | Classification | Classification association | 2ч | - |
| **CTX000** | Presentation | Presentation colours and textures | 2ч | - |
| **GRP000** | Groups | Groups presence | 1ч | - |
| **GRP001** | Groups | Acyclic groups | 2ч | GRP000 |
| **LAY000** | Layer | Presentation layer assignment | 2ч | - |
| **MAT000** | Materials | Materials (полная проверка) | 2ч | - |
| **POR000** | Ports | Port connectivity and nesting | 3ч | - |
| **PSE001** | Properties | Standard properties and property sets | 3ч | - |
| **PSE002** | Properties | Custom properties and property sets | 2ч | PSE001 |
| **QTY000** | Quantities | Quantities for objects | 3ч | - |
| **QTY001** | Quantities | Standard quantities and quantity sets | 2ч | QTY000 |
| **SPA000** | Spaces | Spaces information | 2ч | - |
| **SPS005** | Spatial | Simultaneous spatial relationships | 3ч | SPS007 |
| **VER000** | Version | Versioning and revision control | 1ч | - |
| **VRT000** | Virtual | Virtual elements | 1ч | - |
| **GEM011** | Geometry | Curve segments consistency | 3ч | - |
| **GEM051** | Geometry | Geometric context (полная проверка) | 1ч | - |
| **GEM052** | Geometry | Geometric subcontexts (полная проверка) | 1ч | GEM051 |
| **MPD001** | Mapped | RepresentationType/Identifier for IfcMappedItem | 2ч | - |

**Итого: ~41 час**

---

## Приоритет 3: Georeferencing (9 правил)

Правила для геопривязки (могут быть полезны для инфраструктурных проектов).

| Код | Категория | Описание | Трудоёмкость | Зависимости |
|-----|-----------|----------|---------------|-------------|
| **GRF000** | Georef | Georeferencing presence | 2ч | - |
| **GRF001** | Georef | Identical coordinate operations | 3ч | GRF000 |
| **GRF002** | Georef | EPSG code in CRS | 2ч | GRF000 |
| **GRF003** | Georef | CRS presence with spatial entities | 2ч | GRF000 |
| **GRF004** | Georef | Valid EPSG prefix | 1ч | GRF002 |
| **GRF005** | Georef | CRS unit type differences | 2ч | GRF000 |
| **GRF006** | Georef | WKT specification for missing EPSG | 3ч | GRF000 |
| **GRF007** | Georef | Valid vertical datum CRS type | 2ч | GRF000 |
| **GRF008** | Georef | Rigid operation units | 2ч | GRF000 |

**Итого: ~18 часов**

---

## Приоритет 4: Alignment и Infrastructure (26 правил)

Правила для инфраструктурных объектов (трассы, дороги, ж/д). 
**Могут не относиться к генератору болтов.**

### Alignment (ALB) - 13 правил
| Код | Описание | Трудоёмкость |
|-----|----------|---------------|
| ALB000 | Alignment layout | 3ч |
| ALB002 | Alignment layout relationships | 3ч |
| ALB003 | Alignment nesting | 2ч |
| ALB004 | Alignment in spatial structure | 2ч |
| ALB010 | Alignment nesting referents | 2ч |
| ALB012 | Vertical segment radius of curvature | 2ч |
| ALB015 | Zero length final segment | 2ч |
| ALB021 | Business logic and geometry agreement | 4ч |
| ALB022 | Number of segments agreement | 2ч |
| ALB023 | Same segment types | 2ч |
| ALB030 | Alignment local placement | 2ч |
| ALB031 | Default case layout | 2ч |
| ALB032 | Reusing horizontal | 2ч |

### Alignment geometry (ALS) - 13 правил
| Код | Описание | Трудоёмкость |
|-----|----------|---------------|
| ALS000 | Alignment geometry | 2ч |
| ALS004 | Segment shape representation | 2ч |
| ALS005 | Shape representation | 2ч |
| ALS006 | Horizontal shape representation | 2ч |
| ALS007 | Vertical shape representation | 2ч |
| ALS008 | Cant shape representation | 2ч |
| ALS010 | Correct number of items | 2ч |
| ALS011 | Entity type consistency | 3ч |
| ALS012 | Start and length attribute types | 2ч |
| ALS015 | Zero length final segment | 2ч |
| ALS016 | Horizontal geometric continuity | 4ч |
| ALS017 | Vertical geometric continuity | 4ч |

### Linear placement (LIP) - 2 правила
| Код | Описание | Трудоёмкость |
|-----|----------|---------------|
| LIP000 | Linear Placement | 2ч |
| LIP002 | Fallback coordinates | 2ч |

**Итого: ~60 часов (опционально)**

---

## Приоритет 5: Built elements и другие (11 правил)

Правила для строительных элементов (двери, окна, лестницы).
**Могут не относиться к генератору болтов.**

| Код | Категория | Описание | Трудоёмкость |
|-----|-----------|----------|---------------|
| **BBX000** | Bounding box | Bounding box presence | 1ч |
| **BBX001** | Bounding box | Bounding box shape representation | 2ч |
| **BLT000** | Built elements | Built elements presence | 1ч |
| **BLT001** | Built elements | Operation type for doors | 2ч |
| **BLT002** | Built elements | Partitioning type for windows | 2ч |
| **BLT003** | Built elements | Stair decomposition | 3ч |
| **AXG000** | Axis geometry | Axis Geometry presence | 1ч |
| **ANN000** | Annotations | Annotations presence | 1ч |
| **GDP000** | Grid | Grid placement | 2ч |
| **OJP000** | Placement | Object placement (полная) | 1ч |
| **OJP001** | Placement | Relative placement (полная) | 1ч |

**Итого: ~17 часов (опционально)**

---

## Отключенные правила (7 правил - не реализовывать)

| Код | Категория | Описание | Причина отключения |
|-----|-----------|----------|-------------------|
| ALB005 | Alignment | Positioning of referents | Нестабильная реализация |
| BRP001 | BREP | Polyhedral IfcFace no self intersections | Сложно проверить |
| GEM005 | Geometry | Building shape representation | Специфично для зданий |
| SPS004 | Spatial | No containment + positioning | Конфликтующие требования |
| SPS006 | Spatial | Elements in Spatial structures | Нестабильная реализация |
| SYS001 | SYS | Cable signal flow | Специфично для MEP |
| TAS001 | Tessellated | Polygonal face no self intersections | Сложно проверить |

---

## Итоговая сводка

| Приоритет | Кол-во правил | Трудоёмкость | Статус |
|-----------|---------------|---------------|--------|
| **1. Критичные** | 15 | ~25ч | Рекомендуется |
| **2. Общие** | 20 | ~41ч | Рекомендуется |
| **3. Georeferencing** | 9 | ~18ч | По необходимости |
| **4. Alignment** | 26 | ~60ч | Опционально |
| **5. Built elements** | 11 | ~17ч | Опционально |
| **Отключено** | 7 | - | Не реализовывать |
| **Реализовано** | 19 | - | ✅ Готово |
| **ВСЕГО** | 81 | ~161ч | |

---

## План реализации (спринты по 2 недели)

### Спринт 1: Приоритет 1 (Критичные)
- Неделя 1: IFC101, IFC102, PJS000, PJS002, GEM001, GEM002, GEM111
- Неделя 2: GEM112, GEM113, BRP003, SWE001, SWE002, LOP000, SPS002, SPS008

### Спринт 2: Приоритет 2 (Общие)
- Неделя 1: PJS003, CLS000, CTX000, GRP000, GRP001, LAY000, MAT000
- Неделя 2: POR000, PSE001, PSE002, QTY000, QTY001, SPA000, SPS005

### Спринт 3: Приоритет 2+3 (Завершение + Georeferencing)
- Неделя 1: VER000, VRT000, GEM011, GEM051, GEM052, MPD001
- Неделя 2: GRF000, GRF001, GRF002, GRF003, GRF004, GRF005, GRF006, GRF007, GRF008

### Спринт 4+: Опционально
- По необходимости: Alignment, Built elements

---

## Структура тестового файла

```
tests/test_buildingsmart_rules/
├── __init__.py
├── test_priority1_critical.py      # Приоритет 1 (15 правил)
├── test_priority2_general.py       # Приоритет 2 (20 правил)
├── test_priority3_georeferencing.py # Приоритет 3 (9 правил)
├── test_priority4_alignment.py     # Приоритет 4 (26 правил)
├── test_priority5_built_elements.py # Приоритет 5 (11 правил)
└── conftest.py                     # Общие фикстуры
```

Или единый файл (как сейчас):
```
tests/test_ifc_rules.py  # Все правила в одном файле
```

---

## Фикстуры и инфраструктура

### Требуемые фикстуры:
1. `ifc_doc` - новый IFC документ
2. `factory` - InstanceFactory
3. `bolt_params` - параметры болта
4. `sample_ifc_file` - готовый IFC файл для валидации

### Утилиты:
1. `validate_rule(rule_code, ifc_doc)` - проверка правила по коду
2. `get_validation_report(ifc_doc)` - полный отчёт по всем правилам
3. `assert_rule_passes(rule_code, ifc_doc)` - assertion для тестов

---

## Критерии приёмки

Для каждого правила:
- [ ] Тест написан по TDD (сначала красный, потом зелёный)
- [ ] Тест покрывает happy path
- [ ] Тест покрывает edge cases
- [ ] Тест проверяет нарушение правила (negative test)
- [ ] Код проверки переиспользуемый
- [ ] Документация правила в docstring
- [ ] Ссылка на оригинальное правило buildingsmart

---

## Риски

1. **Недостаточно контекста** - некоторые правила требуют сложных сценариев
2. **Ложные срабатывания** - правила могут быть слишком строгими
3. **Производительность** - 80+ тестов могут замедлить CI/CD
4. **Поддержка** - правила buildingsmart обновляются

## Митигация

1. Использовать фикстуры для сложных сценариев
2. Документировать исключения из правил
3. Группировать тесты по категориям, запускать выборочно
4. Отслеживать изменения в buildingsmart/ifc-gherkin-rules
