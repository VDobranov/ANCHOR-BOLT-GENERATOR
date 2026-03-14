# 📋 Phase 1: Критические исправления

**Длительность:** 2-3 дня  
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 1 убедитесь, что выполнена Phase 0:**

- [ ] Pre-commit hooks настроены (`pre-commit --version` работает)
- [ ] Все 107 тестов проходят (`pytest tests/ -v` → 107 passed)
- [ ] Покрытие зафиксировано (файлы в `refactoring/coverage_before_*`)
- [ ] Ветка для рефакторинга создана

**Если Phase 0 не выполнена:**
1. Откройте `refactoring/PHASE_0_TODO.md`
2. Выполните все задачи Phase 0
3. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Критические исправления, которые необходимо выполнить в первую очередь для улучшения архитектуры и производительности.

### Цели:
- ✅ Удалить workaround для импорта shape_builder
- ✅ Заменить ручное дублирование геометрии на `builder.deep_copy()`
- ✅ Оптимизировать экспорт через memory buffer
- ✅ Сохранить прохождение всех 107 тестов

---

## 📝 Задачи

### 1.1. Удаление workaround для shape_builder

**Файл:** `python/geometry_builder.py`  
**Сложность:** Низкая  
**Риск:** Минимальный  
**Время:** 1-2 часа

#### 1.1.1. Текущее состояние (ДО)

```python
# Workaround для циклического импорта VectorType (IfcOpenShell #7562):
# Создаём mock VectorType перед импортом shape_builder
import sys
import types
from typing import Any

if 'ifcopenshell.util.shape_builder' not in sys.modules:
    _mock_sb = types.ModuleType('ifcopenshell.util.shape_builder')
    _mock_sb.VectorType = Any
    _mock_sb.V = lambda *coords: [float(c) for c in coords]
    sys.modules['ifcopenshell.util.shape_builder'] = _mock_sb

from utils import get_ifcopenshell
from ifcopenshell.util.representation import get_context

# Удаляем mock и импортируем реальный модуль
del sys.modules['ifcopenshell.util.shape_builder']
from ifcopenshell.util.shape_builder import ShapeBuilder

# Экспортируем V для использования в других модулях
V = lambda *coords: [float(c) for c in coords]
```

**Проблемы:**
- Хрупкая конструкция с mock модулем
- Создание и удаление модуля в sys.modules
- Потенциальные проблемы при обновлении ifcopenshell

#### 1.1.2. Целевое состояние (ПОСЛЕ)

```python
"""
geometry_builder.py — Построение IFC геометрии
Использует ifcopenshell.util.shape_builder для стандартного API

Согласно документации IfcOpenShell:
- ShapeBuilder предоставляет стандартное API для построения геометрии
- V — функция для создания векторов координат
"""

import math
from typing import Any, List, Tuple, Optional

from ifcopenshell.util.shape_builder import ShapeBuilder, V
from ifcopenshell.util.representation import get_context


class GeometryBuilder:
    """Построитель IFC геометрии с использованием shape_builder"""

    def __init__(self, ifc_doc):
        """
        Инициализация GeometryBuilder

        Args:
            ifc_doc: IFC документ (ifcopenshell.file)
        """
        self.ifc = ifc_doc
        self.builder = ShapeBuilder(ifc_doc)
        self._context = None
```

#### 1.1.3. Шаги выполнения

```bash
# 1. Открыть файл для редактирования
code python/geometry_builder.py

# 2. Заменить первые 30 строк на новый код
# Удалить строки 1-28 (workaround код)
# Вставить новый импорт

# 3. Запустить тесты
pytest tests/test_geometry_builder.py -v

# 4. Проверить все тесты
pytest tests/ -v --tb=short
```

#### 1.1.4. Проверка в браузере

```bash
# 1. Запустить локальный сервер
python3 -m http.server 8000

# 2. Открыть http://localhost:8000
# 3. Сгенерировать болт каждого типа (1.1, 1.2, 2.1, 5)
# 4. Проверить, что 3D модель отображается
# 5. Скачать IFC файл, проверить валидатором
```

**Критерии приёмки:**
- [ ] Workaround код удалён
- [ ] Прямой импорт `from ifcopenshell.util.shape_builder import ShapeBuilder, V`
- [ ] Все 15 тестов geometry_builder проходят
- [ ] Все 107 тестов проходят
- [ ] Генерация в браузере работает

---

### 1.2. Замена ручного дублирования на builder.deep_copy()

**Файл:** `python/instance_factory.py`  
**Сложность:** Низкая  
**Риск:** Низкий  
**Время:** 2-3 часа

#### 1.2.1. Текущее состояние (ДО)

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
    """Дублирование кривой"""
    if curve.is_a() == 'IfcCompositeCurve':
        segments = [self._duplicate_curve_segment(s) for s in curve.Segments]
        return self.ifc.create_entity('IfcCompositeCurve',
            Segments=segments, SelfIntersect=curve.SelfIntersect
        )
    elif curve.is_a() == 'IfcPolyline':
        points = [self.ifc.create_entity('IfcCartesianPoint', Coordinates=p.Coordinates)
                 for p in curve.Points]
        return self.ifc.create_entity('IfcPolyline', Points=points)
    return curve

def _duplicate_curve_segment(self, segment):
    """Дублирование сегмента кривой"""
    return self.ifc.create_entity('IfcCompositeCurveSegment',
        Transition=segment.Transition,
        SameSense=segment.SameSense,
        ParentCurve=self._duplicate_curve(segment.ParentCurve)
    )

def _duplicate_placement(self, placement):
    """Дублирование размещения"""
    if placement.is_a() == 'IfcAxis2Placement3D':
        return self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint',
                Coordinates=placement.Location.Coordinates
            ),
            Axis=self._duplicate_direction(placement.Axis) if placement.Axis else None,
            RefDirection=self._duplicate_direction(placement.RefDirection) if placement.RefDirection else None
        )
    return placement

def _duplicate_direction(self, direction):
    """Дублирование направления"""
    return self.ifc.create_entity('IfcDirection',
        DirectionRatios=direction.DirectionRatios
    )

def _duplicate_profile(self, profile):
    """Дублирование профиля"""
    return profile  # Упрощённо возвращаем оригинал
```

**Проблемы:**
- ~150 строк сложного кода
- Поддержка всех типов сущностей вручную
- Дублирование логики в каждом методе
- Сложно тестировать

#### 1.2.2. Целевое состояние (ПОСЛЕ)

```python
"""
instance_factory.py — Создание инстансов болтов и сборок
"""

from typing import Dict, Any, List, Literal
from ifcopenshell.util.shape_builder import ShapeBuilder

from utils import get_ifcopenshell
from type_factory import TypeFactory
from gost_data import (
    validate_parameters,
    get_nut_dimensions,
    get_washer_dimensions,
    get_material_name
)
from material_manager import MaterialManager


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(self, ifc_doc, type_factory=None):
        """
        Инициализация InstanceFactory

        Args:
            ifc_doc: IFC документ
            type_factory: TypeFactory для создания типов (опционально)
        """
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)

    def _duplicate_geometric_items(self, items):
        """
        Дублирование геометрических элементов через ShapeBuilder.deep_copy()

        Согласно документации IfcOpenShell:
        - deep_copy() создаёт полную копию геометрии со всеми зависимостями
        - Поддерживает все типы сущностей IFC
        - Значительно проще и надёжнее ручного дублирования

        Args:
            items: Список IFC сущностей для дублирования

        Returns:
            Список скопированных сущностей
        """
        builder = ShapeBuilder(self.ifc)
        return [builder.deep_copy(item) for item in items]
```

#### 1.2.3. Шаги выполнения

```bash
# 1. Открыть файл для редактирования
code python/instance_factory.py

# 2. Добавить импорт в начало файла
# from ifcopenshell.util.shape_builder import ShapeBuilder

# 3. Найти метод _duplicate_geometric_items (строки ~290-310)

# 4. Заменить метод на новую реализацию (3 строки вместо ~150)

# 5. Удалить методы:
#    - _duplicate_curve (строки ~312-325)
#    - _duplicate_curve_segment (строки ~327-335)
#    - _duplicate_placement (строки ~337-350)
#    - _duplicate_direction (строки ~352-357)
#    - _duplicate_profile (строки ~359-362)

# 6. Запустить тесты
pytest tests/test_instance_factory.py -v

# 7. Проверить все тесты
pytest tests/ -v --tb=short
```

#### 1.2.4. Проверка функциональности

```bash
# 1. Запустить тест на валидацию IFC
pytest tests/test_instance_factory.py::TestGenerateBoltAssembly::test_generate_bolt_assembly_validates_ifc -v

# 2. Проверить в браузере
# - Сгенерировать болты всех типов
# - Скачать IFC файл
# - Проверить валидатором (онлайн или локально)
```

**Критерии приёмки:**
- [ ] Метод `_duplicate_geometric_items` использует `builder.deep_copy()`
- [ ] Методы `_duplicate_*` удалены
- [ ] Все 14 тестов instance_factory проходят
- [ ] Все 107 тестов проходят
- [ ] IFC файл валиден

---

### 1.3. Экспорт в memory buffer

**Файл:** `python/instance_factory.py`  
**Сложность:** Низкая  
**Риск:** Низкий  
**Время:** 1-2 часа

#### 1.3.1. Текущее состояние (ДО)

```python
def generate_bolt_assembly(params):
    """
    Главная функция для генерации болта

    Args:
        params: dict с параметрами болта

    Returns:
        (ifc_string, mesh_data)
    """
    from main import reset_ifc_document

    # Сброс документа: удаление предыдущих болтов
    ifc_doc = reset_ifc_document()

    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(
        bolt_type=params['bolt_type'],
        diameter=params['diameter'],
        length=params['length'],
        material=params['material']
    )

    # Экспорт в строку через временный файл
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

**Проблемы:**
- Дисковый I/O (медленно)
- Создание и удаление временных файлов
- Потенциальные проблемы с правами доступа
- Не работает в некоторых средах (WebAssembly)

#### 1.3.2. Целевое состояние (ПОСЛЕ)

```python
import io
from typing import Dict, Any, Tuple

from instance_factory import InstanceFactory
from main import reset_ifc_document


def generate_bolt_assembly(params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Главная функция для генерации болта

    Args:
        params: dict с параметрами болта:
            - bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
            - diameter: Диаметр (мм)
            - length: Длина (мм)
            - material: Материал ('09Г2С', 'ВСт3пс2', '10Г2')

    Returns:
        Кортеж (ifc_string, mesh_data):
            - ifc_string: IFC файл в виде строки
            - mesh_data: Данные для 3D визуализации
    """
    # Сброс документа: удаление предыдущих болтов
    ifc_doc = reset_ifc_document()

    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(
        bolt_type=params['bolt_type'],
        diameter=params['diameter'],
        length=params['length'],
        material=params['material']
    )

    # Экспорт в memory buffer (быстрее и надёжнее)
    buffer = io.StringIO()
    ifc_doc.write(buffer)
    ifc_str = buffer.getvalue()

    return (ifc_str, result['mesh_data'])
```

#### 1.3.3. Шаги выполнения

```bash
# 1. Открыть файл для редактирования
code python/instance_factory.py

# 2. Добавить импорт io в начало файла
# import io

# 3. Найти функцию generate_bolt_assembly (строки ~370-400)

# 4. Заменить экспорт через tempfile на export в io.StringIO()

# 5. Добавить type hints для функции

# 6. Запустить тесты
pytest tests/test_instance_factory.py -v

# 7. Проверить все тесты
pytest tests/ -v --tb=short
```

#### 1.3.4. Тест производительности

```python
# test_export_performance.py
import time
import io
import tempfile
import os


def test_memory_buffer_export_speed():
    """Тест скорости экспорта в memory buffer"""
    from main import reset_ifc_document
    from instance_factory import InstanceFactory

    ifc_doc = reset_ifc_document()
    factory = InstanceFactory(ifc_doc)

    params = {
        'bolt_type': '1.1',
        'diameter': 20,
        'length': 800,
        'material': '09Г2С'
    }

    result = factory.create_bolt_assembly(**params)

    # Memory buffer
    start = time.time()
    for _ in range(100):
        buffer = io.StringIO()
        ifc_doc.write(buffer)
        ifc_str = buffer.getvalue()
    memory_time = time.time() - start

    # Temp file
    start = time.time()
    for _ in range(100):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
            temp_path = f.name
        ifc_doc.write(temp_path)
        with open(temp_path, 'r') as f:
            ifc_str = f.read()
        os.unlink(temp_path)
    file_time = time.time() - start

    print(f"Memory buffer: {memory_time:.3f}s")
    print(f"Temp file: {file_time:.3f}s")
    print(f"Speedup: {file_time / memory_time:.2f}x")

    # Ожидаем: memory buffer быстрее в 2-3 раза
    assert memory_time < file_time
```

**Критерии приёмки:**
- [ ] Экспорт использует `io.StringIO()`
- [ ] Временные файлы не создаются
- [ ] Все 14 тестов instance_factory проходят
- [ ] Все 107 тестов проходят
- [ ] Производительность улучшилась в 2-3 раза

---

### 1.4. Финальная проверка фазы 1

#### 1.4.1. Запустить все тесты

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Все тесты
pytest tests/ -v --tb=short

# Ожидаемый результат: 107 passed
```

#### 1.4.2. Проверка в браузере

```bash
# 1. Запустить сервер
python3 -m http.server 8000

# 2. Открыть http://localhost:8000

# 3. Протестировать все типы болтов:
#    - Тип 1.1, М20x800, 09Г2С
#    - Тип 1.2, М20x800, 09Г2С
#    - Тип 2.1, М20x800, 09Г2С
#    - Тип 5, М20x800, 09Г2С

# 4. Для каждого:
#    - Проверить 3D модель
#    - Скачать IFC файл
```

#### 1.4.3. Валидация IFC файлов

```bash
# Сохранить скачанные IFC файлы
mkdir -p refactoring/test_ifc_files

# Проверить валидатором (если установлен ifcopenshell)
python3 -c "
import ifcopenshell
from validate_utils import validate_ifc_file

for filename in ['bolt_1.1_M20x800.ifc', 'bolt_2.1_M20x800.ifc']:
    ifc_doc = ifcopenshell.open(f'refactoring/test_ifc_files/{filename}')
    errors = validate_ifc_file(ifc_doc)
    if errors:
        print(f'{filename}: {len(errors)} ошибок')
    else:
        print(f'{filename}: ✓ валиден')
"
```

#### 1.4.4. Зафиксировать изменения

```bash
# Проверить статус
git status

# Посмотреть diff
git diff python/geometry_builder.py
git diff python/instance_factory.py

# Закоммитить изменения
git add python/geometry_builder.py python/instance_factory.py
git commit -m "refactor(phase1): критические исправления

- Удалён workaround для импорта shape_builder
- Заменено ручное дублирование на builder.deep_copy()
- Экспорт в memory buffer вместо временных файлов
- Удалено ~170 строк кода
- Производительность экспорта улучшена в 2-3 раза

#refactoring #phase1"
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] Все 4 типа болтов генерируются
- [ ] IFC файлы валидны
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 1

### Обязательные задачи:
- [ ] 1.1.1. Workaround код удалён
- [ ] 1.1.2. Прямой импорт ShapeBuilder, V
- [ ] 1.1.3. Все 15 тестов geometry_builder проходят
- [ ] 1.2.1. `_duplicate_geometric_items` использует `builder.deep_copy()`
- [ ] 1.2.2. Методы `_duplicate_*` удалены
- [ ] 1.2.3. Все 14 тестов instance_factory проходят
- [ ] 1.3.1. Экспорт использует `io.StringIO()`
- [ ] 1.3.2. Временные файлы не создаются
- [ ] 1.4.1. Все 107 тестов проходят
- [ ] 1.4.2. Все типы болтов генерируются в браузере
- [ ] 1.4.3. IFC файлы валидны

### Дополнительные проверки:
- [ ] Производительность экспорта улучшена
- [ ] Код отформатирован (black, isort)
- [ ] Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Строк кода (Python) | ~3500 | ~3330 | -170 (-5%) |
| Строк в geometry_builder.py | 373 | 358 | -15 |
| Строк в instance_factory.py | 409 | 239 | -170 |
| Тестов пройдено | 107 | 107 | 0 |
| Производительность экспорта | 1x | 2-3x | +200-300% |

---

## 🚀 Следующие шаги

После завершения фазы 1:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 2**

**Ссылка на следующую фазу:** `refactoring/PHASE_2_TODO.md`

---

## 📚 Приложения

### A. Полезные команды

```bash
# Быстрая проверка тестов
pytest tests/ -q

# Проверка конкретного модуля
pytest tests/test_geometry_builder.py -q
pytest tests/test_instance_factory.py -q

# Проверка стиля
black --check python/
isort --check python/

# Запуск локального сервера
python3 -m http.server 8000
```

### B. Ссылки на документацию

- [IfcOpenShell ShapeBuilder](https://ifcopenshell.org/docs/)
- [io.StringIO документация](https://docs.python.org/3/library/io.html#io.StringIO)
- [ifcopenshell.util.shape_builder](https://github.com/IfcOpenShell/IfcOpenShell)

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
