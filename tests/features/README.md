# IFC Gherkin Validation

Валидация IFC файлов с использованием оригинальных Gherkin-правил buildingSMART.

## 🚀 Быстрый старт

### Запуск валидации IFC файла

```bash
# Скрипт
./run_gherkin_validation.sh bolt_2.1_M20x300.ifc

# Или напрямую через behave
cd external/ifc-gherkin-rules
python -m behave --define input=/path/to/file.ifc features/rules/
```

### Запуск конкретного правила

```bash
cd external/ifc-gherkin-rules
python -m behave --define input=/path/to/file.ifc features/rules/PJS/PJS101_Project-presence.feature
```

### Запуск по категориям правил

```bash
# Только правила Project (PJS)
python -m behave --define input=file.ifc features/rules/PJS/

# Только правила Spatial (SPS)
python -m behave --define input=file.ifc features/rules/SPS/

# Исключить отключённые правила
python -m behave --define input=file.ifc --tags="-@disabled" features/rules/
```

## 📁 Структура

```
external/ifc-gherkin-rules/       # buildingSMART ifc-gherkin-rules
├── features/
│   ├── rules/                     # Оригинальные правила buildingSMART
│   │   ├── PJS/                   # Project rules
│   │   ├── SPS/                   # Spatial rules
│   │   ├── GEM/                   # Geometry rules
│   │   ├── MAT/                   # Materials rules
│   │   ├── OJT/                   # Object type rules
│   │   └── ...
│   └── steps/                     # Step definitions buildingSMART
└── ...

run_gherkin_validation.sh          # Скрипт запуска валидации
```

## 📊 Результаты валидации buildingSMART

### Пилотные тесты (5 правил)

| Правило | Категория | Статус |
|---------|-----------|--------|
| PJS101 | Project | ✅ PASS |
| SPS001 | Spatial | ✅ PASS (4 сценария) |
| GEM051 | Geometry | ✅ PASS (6 сценариев) |
| MAT000 | Materials | ✅ PASS (2 сценария) |
| OJT001 | Object Type | ✅ PASS (3 сценария) |

**Итого:** 14 сценариев прошли на `bolt_1.1_M20x800.ifc`

### Все применимые правила (92 правила)

```
✅ 85 features passed
❌ 7 features failed
⏭️  8 features skipped (отключённые тегами)

✅ 354 scenarios passed
❌ 7 scenarios failed
⏭️  11 scenarios skipped

✅ 1480 steps passed
❌ 7 steps failed
```

### Проваленные правила (7)

| Правило | Описание | Статус |
|---------|----------|--------|
| **GEM113** | Indexed poly curve arcs — colinear points | ⚠️ Требует анализа |
| **IFC102** | Deprecated entities (IFC4) | ⚠️ Требует анализа |
| **IFC105** | Resource entities not referenced | ⚠️ Требует анализа |
| **OJP001** | Relative placement for aggregated elements | ❌ Нужно исправить |
| **SPS003** | Aggregated elements containment | ⚠️ Требует анализа |
| **SPS005** | Simultaneous spatial relationships | ⚠️ Требует анализа |
| **SPS007** | Spatial containment | ⚠️ Требует анализа |

**OJP001:** Компоненты болта должны иметь относительное размещение (`PlacementRelTo`) 
указывающее на `IfcLocalPlacement` контейнера (assembly), а не абсолютное.

## 🔧 Использование

### Все правила

```bash
./run_gherkin_validation.sh your_file.ifc
```

### Отдельные категории

```bash
# Project rules
cd external/ifc-gherkin-rules && python -m behave --define input=../../your_file.ifc features/rules/PJS/

# Spatial rules  
cd external/ifc-gherkin-rules && python -m behave --define input=../../your_file.ifc features/rules/SPS/

# Geometry rules
cd external/ifc-gherkin-rules && python -m behave --define input=../../your_file.ifc features/rules/GEM/
```

## 📚 Документация buildingSMART

- [ifc-gherkin-rules README](https://github.com/buildingSMART/ifc-gherkin-rules)
- [Validation Service Docs](https://buildingsmart.github.io/validate/)
- [Rule Development Guide](https://buildingsmart.github.io/validate/2-rule-development/)
