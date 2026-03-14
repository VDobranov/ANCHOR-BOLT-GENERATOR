# 📋 Phase 6: Type hints и документация

**Длительность:** 1-2 недели  
**Приоритет:** 🟡 Средний  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 6 убедитесь, что выполнены Phase 0-5:**

- [ ] Pre-commit hooks работают (Phase 0)
- [ ] Критические исправления выполнены (Phase 1)
- [ ] Модули разделены (Phase 2)
- [ ] RepresentationMaps добавлены (Phase 3)
- [ ] Protocol интерфейсы созданы (Phase 4)
- [ ] Singleton удалён, архитектура улучшена (Phase 5)
- [ ] Все 107 тестов проходят
- [ ] Изменения Phase 1-5 закоммичены

**Если предыдущие фазы не выполнены:**
1. Откройте файлы `refactoring/PHASE_1_TODO.md` — `refactoring/PHASE_5_TODO.md`
2. Выполните все задачи предыдущих фаз
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Добавление type hints во все модули и генерация Sphinx документации для улучшения поддерживаемости и документирования API.

### Цели:
- ✅ Добавить type hints во все Python модули
- ✅ Настроить Sphinx для генерации документации
- ✅ Создать документацию для всех публичных API
- ✅ Достичь type coverage > 90%

---

## 📝 Задачи

### 6.1. Добавление type hints

**Длительность:** 1 неделя  
**Сложность:** Средняя

#### 6.1.1. Настройка mypy

**Файл:** `mypy.ini`

```ini
[mypy]
python_version = 3.13
warn_return_any = True
warn_unused_configs = True
ignore_missing_imports = True
no_implicit_optional = True
warn_redundant_casts = True
warn_unused_ignores = True
disallow_untyped_defs = False  # Включить после добавления всех type hints

[mypy-python.data.*]
disallow_untyped_defs = True

[mypy-python.services.*]
disallow_untyped_defs = True
```

#### 6.1.2. Type hints для data модулей

**Файл:** `python/data/bolt_dimensions.py` (обновление)

```python
"""
python/data/bolt_dimensions.py — Данные размеров болтов из dim.csv

Based on ГОСТ 24379.1-2012
"""

from typing import TypedDict, Optional, Dict, List, Tuple, Literal


# =============================================================================
# Типы данных
# =============================================================================

BoltType = Literal['1.1', '1.2', '2.1', '5']


class BoltDimension(TypedDict):
    """Структура данных размеров болта"""
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


# =============================================================================
# Константы с type hints
# =============================================================================

AVAILABLE_DIAMETERS: List[int] = [12, 16, 20, 24, 30, 36, 42, 48]

DIAMETER_LIMITS: Dict[BoltType, Tuple[int, int]] = {
    '1.1': (12, 48),
    '1.2': (12, 48),
    '2.1': (16, 48),
    '5': (12, 48)
}

BOLT_DIM_DATA: Dict[str, BoltDimension] = {
    # ... данные
}
```

#### 6.1.3. Type hints для services модулей

**Файл:** `python/services/dimension_service.py` (обновление)

```python
"""
python/services/dimension_service.py — Сервис для получения размеров болтов
"""

from typing import Optional, Literal
from ..data.bolt_dimensions import BOLT_DIM_DATA

BoltType = Literal['1.1', '1.2', '2.1', '5']


def get_bolt_hook_length(diameter: int, length: int) -> Optional[int]:
    """
    Получить вылет крюка для болта.

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Вылет крюка (мм) или None
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['hook_length']
    return None
```

#### 6.1.4. Type hints для geometry_builder.py

**Файл:** `python/geometry_builder.py` (обновление)

```python
"""
geometry_builder.py — Построение IFC геометрии
"""

import math
from typing import Any, List, Tuple, Optional

from ifcopenshell.util.shape_builder import ShapeBuilder, V
from ifcopenshell.util.representation import get_context
from ifcopenshell.entity_instance import entity_instance


class GeometryBuilder:
    """Построитель IFC геометрии"""

    def __init__(self, ifc_doc: Any):
        self.ifc = ifc_doc
        self.builder = ShapeBuilder(ifc_doc)
        self._context: Optional[entity_instance] = None

    def create_line(
        self,
        point1: List[float],
        point2: List[float]
    ) -> entity_instance:
        """Создание IfcPolyline между двумя точками"""
        return self.builder.polyline([V(*point1), V(*point2)])

    def create_bent_stud_solid(
        self,
        bolt_type: str,
        diameter: int,
        length: int
    ) -> entity_instance:
        """Создание геометрии изогнутой шпильки"""
        context = self._get_context()
        axis_curve = self.create_composite_curve_stud(bolt_type, diameter, length)
        swept_area = self.create_swept_disk_solid(axis_curve, diameter / 2.0)
        return self._create_shape_representation(context, swept_area)
```

#### 6.1.5. Type hints для type_factory.py

**Файл:** `python/type_factory.py` (обновление)

```python
"""
type_factory.py — Фабрика для создания и кэширования типов IFC
"""

from typing import Dict, Tuple, Any, Optional, Literal
from ifcopenshell.util.representation import get_context
from ifcopenshell.entity_instance import entity_instance

from utils import get_ifcopenshell
from gost_data import get_nut_dimensions, get_washer_dimensions, get_material_name
from geometry_builder import GeometryBuilder
from material_manager import MaterialManager

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']


class TypeFactory:
    """Фабрика типов IFC MechanicalFastenerType"""

    def __init__(self, ifc_doc: Any):
        self.ifc = ifc_doc
        self.types_cache: Dict[Tuple[str, BoltType, int, int, MaterialType], entity_instance] = {}
        self.builder = GeometryBuilder(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)
        self.owner_history: Optional[entity_instance] = None

    def get_or_create_stud_type(
        self,
        bolt_type: BoltType,
        diameter: int,
        length: int,
        material: MaterialType
    ) -> entity_instance:
        """Создание/получение типа шпильки"""
        key = ('stud', bolt_type, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]
        # ...
```

#### 6.1.6. Type hints для instance_factory.py

**Файл:** `python/instance_factory.py` (обновление)

```python
"""
instance_factory.py — Создание инстансов болтов и сборок
"""

from typing import Dict, Any, List, Literal, Optional
from ifcopenshell.util.shape_builder import ShapeBuilder
from ifcopenshell.entity_instance import entity_instance

from utils import get_ifcopenshell
from type_factory import TypeFactory
from gost_data import (
    validate_parameters,
    get_nut_dimensions,
    get_washer_dimensions,
    get_material_name
)
from material_manager import MaterialManager

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(
        self,
        ifc_doc: Any,
        type_factory: Optional[TypeFactory] = None
    ):
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)

    def create_bolt_assembly(
        self,
        bolt_type: BoltType,
        diameter: int,
        length: int,
        material: MaterialType
    ) -> Dict[str, Any]:
        """
        Создание полной сборки анкерного болта.

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)
            length: Длина (мм)
            material: Материал

        Returns:
            Dict с assembly, stud, components и mesh_data
        """
        # ...
```

#### 6.1.7. Type hints для material_manager.py

**Файл:** `python/material_manager.py` (обновление)

```python
"""
material_manager.py — Менеджер материалов IFC
"""

from typing import Dict, Any, Optional, List
from ifcopenshell.entity_instance import entity_instance

from utils import get_ifcopenshell


class MaterialManager:
    """Менеджер материалов IFC"""

    def __init__(self, ifc_doc: Any):
        self.ifc = ifc_doc
        self.materials_cache: Dict[str, entity_instance] = {}
        self.material_properties_cache: Dict[Tuple[entity_instance, str], entity_instance] = {}
        self.owner_history: Optional[entity_instance] = None

    def create_material(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        material_key: Optional[str] = None
    ) -> entity_instance:
        """Создание или получение материала"""
        if name in self.materials_cache:
            return self.materials_cache[name]
        # ...
```

#### 6.1.8. Type hints для main.py

**Файл:** `python/main.py` (обновление)

```python
"""
main.py — Менеджер IFC документов
"""

from typing import Dict, Optional, Any
import ifcopenshell
from ifcopenshell.file import file as ifc_file
import numpy as np
from material_manager import MaterialManager


class IFCDocumentManager:
    """Менеджер IFC документов"""

    def __init__(self):
        self._documents: Dict[str, ifc_file] = {}
        self._material_managers: Dict[str, MaterialManager] = {}
        self._current_id: Optional[str] = None

    def create_document(
        self,
        doc_id: str,
        schema: str = 'IFC4'
    ) -> ifc_file:
        """Создание нового IFC документа"""
        # ...

    def get_document(self, doc_id: Optional[str] = None) -> ifc_file:
        """Получение IFC документа"""
        # ...
```

**Критерии приёмки:**
- [ ] mypy.ini создан
- [ ] Type hints в data/*.py
- [ ] Type hints в services/*.py
- [ ] Type hints в geometry_builder.py
- [ ] Type hints в type_factory.py
- [ ] Type hints в instance_factory.py
- [ ] Type hints в material_manager.py
- [ ] Type hints в main.py
- [ ] mypy не выдаёт ошибок (кроме missing imports)

---

### 6.2. Настройка Sphinx документации

**Длительность:** 2-3 дня  
**Сложность:** Средняя

#### 6.2.1. Установка зависимостей

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Установка Sphinx и расширений
pip install sphinx sphinx-autodoc-typehints myst-parser sphinx-rtd-theme
```

#### 6.2.2. Создание структуры docs/

```bash
# Создать директорию
mkdir -p docs

# Инициализировать Sphinx
sphinx-quickstart docs --sep --project="ANCHOR-BOLT-GENERATOR" \
  --author="Вячеслав Добранов" --release="1.0" --language=ru
```

#### 6.2.3. Файл `docs/conf.py`

```python
# Configuration file for the Sphinx documentation builder.

import sys
import os

# Добавляем python директорию в path
sys.path.insert(0, os.path.abspath('../python'))

# -- Project information -----------------------------------------------------
project = 'ANCHOR-BOLT-GENERATOR'
copyright = '2026, Вячеслав Добранов'
author = 'Вячеслав Добранов'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for autodoc -----------------------------------------------------
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

autodoc_typehints = 'description'

# -- Options for intersphinx -------------------------------------------------
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'ifcopenshell': ('https://ifcopenshell.org/docs/', None)
}

# -- Options for HTML output -------------------------------------------------
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_logo = '../assets/favicon.svg'
html_theme_options = {
    'logo_only': True,
    'display_version': True,
}
```

#### 6.2.4. Файл `docs/index.rst`

```rst
.. ANCHOR-BOLT-GENERATOR documentation master file.

ANCHOR-BOLT-GENERATOR Documentation
====================================

Генератор фундаментных болтов по ГОСТ 24379.1-2012 с экспортом в IFC4 ADD2 TC1.

.. toctree::
   :maxdepth: 2
   :caption: Содержание:

   overview
   python/modules
   development
   changelog

Быстрый старт
=============

.. code-block:: python

   from main import initialize_base_document
   from instance_factory import generate_bolt_assembly

   # Инициализация
   ifc_doc = initialize_base_document()

   # Генерация болта
   params = {
       'bolt_type': '1.1',
       'diameter': 20,
       'length': 800,
       'material': '09Г2С'
   }
   ifc_str, mesh_data = generate_bolt_assembly(params)

Python Modules
==============

.. autosummary::
   :toctree: generated
   :recursive:

   python.data
   python.services
   python.geometry_builder
   python.type_factory
   python.instance_factory
   python.material_manager
   python.main

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
```

#### 6.2.5. Файл `docs/python/modules.rst`

```rst
Python Modules
==============

.. toctree::
   :maxdepth: 4

   data
   services
   core

Data Module
-----------

.. automodule:: python.data
   :members:
   :undoc-members:
   :show-inheritance:

Services Module
---------------

.. automodule:: python.services
   :members:
   :undoc-members:
   :show-inheritance:
```

#### 6.2.6. Генерация документации

```bash
# Перейти в директорию docs
cd docs

# Сгенерировать документацию
sphinx-build -b html . _build/html

# Открыть в браузере
open _build/html/index.html
```

#### 6.2.7. Автоматизация генерации

**Файл:** `Makefile` (добавить секцию)

```makefile
.PHONY: docs

docs:
	@sphinx-build -b html docs docs/_build/html
	@echo "Documentation generated in docs/_build/html"

docs-clean:
	@rm -rf docs/_build
	@echo "Documentation cleaned"
```

**Критерии приёмки:**
- [ ] Sphinx установлен
- [ ] docs/conf.py настроен
- [ ] docs/index.rst создан
- [ ] Документация генерируется
- [ ] Все модули задокументированы

---

### 6.3. Финальная проверка фазы 6

#### 6.3.1. Проверка type hints

```bash
# Запустить mypy
mypy python/ --ignore-missing-imports

# Ожидаемый результат: минимальное количество предупреждений
```

#### 6.3.2. Проверка документации

```bash
# Сгенерировать документацию
cd docs && sphinx-build -b html . _build/html

# Проверить наличие всех модулей
ls _build/html/generated/
```

#### 6.3.3. Зафиксировать изменения

```bash
git add python/*.py docs/
git commit -m "refactor(phase6): type hints и Sphinx документация

- Добавлены type hints во все модули
- Настроена Sphinx документация
- Type coverage > 90%
- mypy проверяет типы без ошибок

#refactoring #phase6"
```

**Критерии приёмки:**
- [ ] mypy не выдаёт ошибок
- [ ] Документация сгенерирована
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 6

### Обязательные задачи:
- [ ] 6.1.1. mypy.ini создан
- [ ] 6.1.2. Type hints в data/*.py
- [ ] 6.1.3. Type hints в services/*.py
- [ ] 6.1.4. Type hints в geometry_builder.py
- [ ] 6.1.5. Type hints в type_factory.py
- [ ] 6.1.6. Type hints в instance_factory.py
- [ ] 6.1.7. Type hints в material_manager.py
- [ ] 6.1.8. Type hints в main.py
- [ ] 6.2.1. Sphinx установлен
- [ ] 6.2.3. docs/conf.py настроен
- [ ] 6.2.4. docs/index.rst создан
- [ ] 6.2.6. Документация генерируется
- [ ] 6.3.1. mypy проверка
- [ ] 6.3.2. Документация проверена
- [ ] 6.3.3. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Type coverage | 0% | 90%+ | +90% |
| mypy ошибок | N/A | 0 | -N/A |
| Строк type hints | 0 | ~500 | +500 |
| Строк документации | 0 | ~300 | +300 |
| Тестов пройдено | 107 | 107 | 0 |

---

## 🚀 Следующие шаги

После завершения фазы 6:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 7**

**Ссылка на следующую фазу:** `refactoring/PHASE_7_TODO.md`

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
