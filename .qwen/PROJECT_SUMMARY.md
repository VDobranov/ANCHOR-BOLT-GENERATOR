The user wants me to create a comprehensive project summary in markdown format based on the conversation history. Let me analyze the key information:

1. **Project**: Anchor Bolt Generator according to GOST 24379.1-2012 with IFC4 ADD2 TC1 export
2. **Tech Stack**: Python/Pyodide, Three.js r128, IfcOpenShell 0.8.4
3. **Recent Work**: 
   - Refactoring on 11.03.2026 - removed 11 unused functions, -199 lines
   - Documentation updates (README.md, QWEN.md)
   - Currently implementing material management system for IFC compliance

4. **Current Task**: Implementing material_manager.py for proper IFC4 material associations

Let me create a comprehensive summary.# Project Summary

## Overall Goal
Разработка браузерного генератора анкерных болтов по ГОСТ 24379.1-2012 с экспортом в IFC4 ADD2 TC1 и 3D-визуализацией через Three.js, работающего полностью в браузере через Pyodide.

## Key Knowledge

### Технологический стек
- **Frontend**: HTML5, CSS3, Vanilla JS (7 модулей: config, ui, form, viewer, ifcBridge, main, init)
- **3D-движок**: Three.js r128
- **Python-среда**: Pyodide 0.26.0 (Python 3.13 WebAssembly)
- **IFC-библиотека**: IfcOpenShell 0.8.4
- **IFC-стандарт**: IFC4 ADD2 TC1 (российский BIM-стандарт)

### Архитектура проекта
```
python/ (7 модулей):
  - main.py: Singleton IFCDocument
  - utils.py: Централизованный импорт ifcopenshell
  - gost_data.py: Справочники ГОСТ, валидация
  - type_factory.py: Кэширование IfcMechanicalFastenerType
  - instance_factory.py: Создание инстансов и сборок
  - geometry_builder.py: Построение IFC-геометрии
  - geometry_converter.py: Конвертация IFC → Three.js mesh
  - material_manager.py: Менеджер материалов IFC (новый)

js/ (7 модулей):
  - config.js, ui.js, form.js, viewer.js, ifcBridge.js, main.js, init.js
```

### Поддерживаемые типы болтов
| Тип | Форма | Диаметры | Длины | Исполнение |
|-----|-------|----------|-------|------------|
| 1.1 | Изогнутый | М12–М48 | 300–1400 | авто (1) |
| 1.2 | Изогнутый | М12–М48 | 300–1000 | авто (2) |
| 2.1 | Прямой | М16–М48 | 500–1250 | авто (1) |
| 5 | Футорка | М12–М48 | 300–1000 | авто (1) |

**Состав сборки**:
- Типы 1.1, 1.2, 5: шпилька + шайба + 2 гайки
- Тип 2.1: шпилька + шайба + 2 верхних гайки + 2 нижних гайки

### Материалы (ГОСТ)
- **09Г2С** (ГОСТ 19281-2014) — σ_в = 490 МПа
- **ВСт3пс2** (ГОСТ 535-88) — σ_в = 345 МПа
- **10Г2** (ГОСТ 19281-2014) — σ_в = 490 МПа

**Формат имён IFC**: `"09Г2С ГОСТ 19281-2014"`

### Ключевые решения архитектуры
- Геометрия строится **один раз** в IFC через `type_factory.py` (IfcSweptDiskSolid, IfcExtrudedAreaSolid)
- Конвертация в mesh для Three.js через `ifcopenshell.geom.create_shape()` (единый источник истины)
- Кэширование типов по ключу: `(тип, диаметр, длина, исполнение, материал)`
- Параметр `execution` удалён (коммит 6adba9b) — определяется автоматически по типу
- BOLT_TYPES: `set` вместо `dict`

### Тестирование
- **Статус**: 76 passed, 1 skipped
- **Фреймворк**: pytest
- **Команда**: `pytest` или `python -m pytest`

### Сборка и запуск
```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Recent Actions

### Рефакторинг материалов (11.03.2026) — В ПРОЦЕССЕ
**Проблема**: Материалы не создавались в IFC файле — отсутствовали сущности `IfcMaterial` и `IfcRelAssociatesMaterial`

**Выполнено**:
1. ✅ Создан `material_manager.py` с классом `MaterialManager`:
   - Методы: `create_material()`, `get_material()`, `create_material_list()`, `associate_material()`
   - Кэширование материалов по имени
   - Поддержка `IfcMaterialList` для сборок

2. ✅ Обновлён `gost_data.py`:
   - Добавлена функция `get_material_name(material)` → `"09Г2С ГОСТ 19281-2014"`

3. ✅ Обновлён `type_factory.py`:
   - Интеграция с `MaterialManager`
   - Все типы (stud, nut, washer, assembly) теперь создают и ассоциируют материалы
   - Для assembly создаётся `IfcMaterialList`

**В работе**:
- Обновление `instance_factory.py`
- Обновление `main.py`
- Создание тестов для `material_manager.py`

### Предыдущий рефакторинг (11.03.2026) — ЗАВЕРШЁН
**Коммит**: 6adba9b "refactor: Удалить мёртвый код"
- Удалено 11 функций: `get_bolt_type_name`, `get_bolt_l1/l2/l3/r`, `get_bolt_all_dimensions`, `get_material_info`, `get_element_properties`, `generate_bolt_mesh_from_ifc`, `export_ifc_file`, `is_ifcopenshell_available`
- Удалено 5 тестов для удалённых функций
- Обновлён `ifcBridge.js`: удалена проверка `is_ifcopenshell_available` и метод `getElementProperties()`
- **Итого**: -199 строк, +8 строк

### Обновление документации (11.03.2026) — ЗАВЕРШЁН
**Коммит**: 2f4b494 "docs: Обновить README и QWEN после рефакторинга от 11.03.2026"
- Удалён параметр `execution` из примеров API
- Обновлена таблица типов болтов (убрана колонка "Исполнения")
- Добавлено примечание об автоматическом определении исполнения
- Добавлена запись о рефакторинге в историю

## Current Plan

### Рефакторинг материалов для IFC-совместимости

1. [DONE] Создать material_manager.py с классом MaterialManager
2. [DONE] Обновить gost_data.py: добавить функцию get_material_name()
3. [DONE] Обновить type_factory.py: интеграция с MaterialManager
4. [IN PROGRESS] Обновить instance_factory.py: интеграция с MaterialManager
5. [TODO] Обновить main.py: инициализация MaterialManager
6. [TODO] Создать тесты test_material_manager.py
7. [TODO] Обновить существующие тесты (test_type_factory.py, test_instance_factory.py)
8. [TODO] Интеграционное тестирование: проверить IFC файл на наличие IfcMaterial и IfcRelAssociatesMaterial
9. [TODO] Обновить документацию README.md и QWEN.md

### Критерии приёмки
- Все сущности `IfcMechanicalFastenerType` имеют ассоциации с материалами
- Материалы кэшируются (не создаются дубликаты)
- Имена материалов имеют формат: `"09Г2С ГОСТ 19281-2014"`
- IFC валидируется в BIM-приложениях без ошибок
- Тесты проходят (76 passed + новые тесты)
- Размер IFC увеличивается незначительно (<5%)

### Долгосрочные планы (из roadmap)
- [ ] Валидация IFC файлов в BIM-приложениях (Revit, ArchiCAD, BonsaiBIM)
- [ ] Добавление остальных диаметров (М56–М100)
- [ ] Пакетная генерация болтов
- [ ] Экспорт в другие форматы (STEP, STL)
- [ ] Расширенная обработка ошибок на фронтенде

---

## Summary Metadata
**Update time**: 2026-03-11T17:05:34.299Z 
