# 📋 Phase 7: Улучшение тестов

**Длительность:** 1 неделя  
**Приоритет:** 🟡 Средний  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 7 убедитесь, что выполнены Phase 0-6:**

- [ ] Pre-commit hooks работают (Phase 0)
- [ ] Критические исправления выполнены (Phase 1)
- [ ] Модули разделены (Phase 2)
- [ ] RepresentationMaps добавлены (Phase 3)
- [ ] Protocol интерфейсы созданы (Phase 4)
- [ ] Singleton удалён, архитектура улучшена (Phase 5)
- [ ] Type hints добавлены (Phase 6)
- [ ] Все 107 тестов проходят
- [ ] Изменения Phase 1-6 закоммичены

**Если предыдущие фазы не выполнены:**
1. Откройте файлы `refactoring/PHASE_1_TODO.md` — `refactoring/PHASE_6_TODO.md`
2. Выполните все задачи предыдущих фаз
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Улучшение тестовой инфраструктуры через централизацию mock объектов, добавление фикстур и интеграционных тестов.

### Цели:
- ✅ Переместить все Mock объекты в conftest.py
- ✅ Создать универсальные фикстуры для тестов
- ✅ Добавить интеграционные тесты
- ✅ Увеличить покрытие до 90%+

---

## 📝 Задачи

### 7.1. Централизация Mock объектов

**Файл:** `tests/conftest.py`  
**Длительность:** 1-2 дня  
**Сложность:** Средняя

#### 7.1.1. Текущее состояние (проблема)

Mock класс `MockIfcEntity` дублируется в 5 файлах:
- `tests/test_instance_factory.py`
- `tests/test_geometry_builder.py`
- `tests/test_type_factory.py`
- `tests/test_material_manager.py`
- `tests/test_main.py`

#### 7.1.2. Целевое состояние conftest.py

```python
"""
conftest.py — Конфигурация и фикстуры для pytest тестов

Централизованное хранилище:
- Mock классов
- Фикстур для общих объектов
- Конфигурации тестов
"""

import sys
import os
from typing import Any, Dict, List, Optional

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pytest


# =============================================================================
# Mock классы
# =============================================================================

class MockIfcEntity:
    """
    Mock для IFC сущности

    Используется в тестах для имитации поведения ifcopenshell сущностей.
    Поддерживает основные атрибуты и методы IFC entity.

    Attributes:
        _entity_type: Тип сущности (например, 'IfcMechanicalFastenerType')
        _kwargs: Атрибуты сущности
    """

    def __init__(self, entity_type: str, *args, **kwargs):
        """
        Инициализация Mock сущности

        Args:
            entity_type: Тип сущности
            *args: Позиционные аргументы
            **kwargs: Именованные атрибуты сущности
        """
        self._entity_type = entity_type
        self._kwargs = kwargs

        # Обработка positional аргументов
        for i, arg in enumerate(args):
            setattr(self, f'arg{i}', arg)

        # Установка атрибутов
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Установка RepresentationMaps по умолчанию для типов
        if entity_type == 'IfcMechanicalFastenerType':
            if not hasattr(self, 'RepresentationMaps'):
                self.RepresentationMaps = None

    def is_a(self) -> str:
        """Получение типа сущности"""
        return self._entity_type

    def __getattr__(self, name: str) -> Any:
        """Получение атрибута"""
        return self._kwargs.get(name)

    def __setattr__(self, name: str, value: Any):
        """Установка атрибута"""
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._kwargs[name] = value
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        """Строковое представление"""
        return f"MockIfcEntity({self._entity_type})"

    @property
    def dim(self) -> int:
        """
        Определение размерности для кривых и точек

        Returns:
            2 для 2D, 3 для 3D
        """
        if '3D' in self._entity_type:
            return 3
        if '2D' in self._entity_type:
            return 2
        if self._entity_type == 'IfcIndexedPolyCurve':
            points = self._kwargs.get('Points')
            if points and hasattr(points, 'dim'):
                return points.dim
            return 3
        if self._entity_type in ['IfcCircle', 'IfcPolyline', 'IfcCompositeCurve']:
            return 2
        return 2


class MockIfcDoc:
    """
    Mock для IFC документа

    Используется в тестах для имитации поведения ifcopenshell.file.
    Поддерживает создание сущностей, поиск по типу и ID.

    Attributes:
        entities: Список всех созданных сущностей
        _by_type: Кэш сущностей по типу
        schema: IFC схема (по умолчанию 'IFC4')
    """

    def __init__(self):
        """Инициализация Mock документа"""
        self.entities: List[MockIfcEntity] = []
        self._by_type: Dict[str, List[MockIfcEntity]] = {}
        self.schema = "IFC4"
        self.owner_history = None

    def create_entity(self, entity_type: str, *args, **kwargs) -> MockIfcEntity:
        """
        Создание IFC сущности

        Args:
            entity_type: Тип сущности
            *args: Позиционные аргументы
            **kwargs: Именованные атрибуты

        Returns:
            Созданная Mock сущность
        """
        # Поддержка IfcReal и IfcText для PropertySets
        if entity_type == 'IfcReal':
            value = args[0] if args else kwargs.get('Value', 0.0)
            entity = MockIfcEntity(entity_type, Value=value)
        elif entity_type == 'IfcText':
            value = args[0] if args else kwargs.get('Value', '')
            entity = MockIfcEntity(entity_type, Value=value)
        elif entity_type in ['IfcLineIndex', 'IfcArcIndex'] and args:
            entity = MockIfcEntity(entity_type, Indices=args[0])
        else:
            entity = MockIfcEntity(entity_type, *args, **kwargs)

        self.entities.append(entity)

        # Кэширование по типу
        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)

        return entity

    def __getattr__(self, name: str):
        """
        Динамическая поддержка методов типа createIfcIndexedPolyCurve

        Args:
            name: Имя метода

        Returns:
            Функция для создания сущности
        """
        if name.startswith('create'):
            entity_type = name[6:]

            def create_method(*args, **kwargs):
                return self.create_entity(entity_type, *args, **kwargs)

            return create_method

        raise AttributeError(f"'MockIfcDoc' object has no attribute '{name}'")

    def by_type(self, entity_type: str) -> List[MockIfcEntity]:
        """
        Получение сущностей по типу

        Args:
            entity_type: Тип сущности

        Returns:
            Список сущностей данного типа
        """
        return self._by_type.get(entity_type, [])

    def by_id(self, id: int) -> MockIfcEntity:
        """
        Получение сущности по ID

        Args:
            id: ID сущности

        Returns:
            Сущность с данным ID
        """
        if 0 < id <= len(self.entities):
            return self.entities[id - 1]
        raise IndexError(f"Entity with id {id} not found")

    def by_guid(self, guid: str) -> Optional[MockIfcEntity]:
        """
        Получение сущности по GUID

        Args:
            guid: GUID сущности

        Returns:
            Сущность с данным GUID или None
        """
        for entity in self.entities:
            if entity._kwargs.get('GlobalId') == guid:
                return entity
        return None

    def remove(self, entity: MockIfcEntity) -> None:
        """
        Удаление сущности

        Args:
            entity: Сущность для удаления
        """
        if entity in self.entities:
            self.entities.remove(entity)
            entity_type = entity._entity_type
            if entity_type in self._by_type:
                self._by_type[entity_type].remove(entity)

    def get_inverse(self, entity: MockIfcEntity) -> List[MockIfcEntity]:
        """
        Получение обратных ссылок на сущность

        Args:
            entity: Сущность

        Returns:
            Список сущностей, ссылающихся на данную
        """
        # Упрощённая реализация для тестов
        return []

    def traverse(self, entity: MockIfcEntity, max_levels: int = None) -> List[MockIfcEntity]:
        """
        Обход графа сущности

        Args:
            entity: Сущность для обхода
            max_levels: Максимальная глубина обхода

        Returns:
            Список всех связанных сущностей
        """
        # Упрощённая реализация для тестов
        return []

    def write(self, filepath: str) -> None:
        """
        Запись в файл (заглушка для тестов)

        Args:
            filepath: Путь к файлу
        """
        pass

    def __len__(self) -> int:
        """Количество сущностей в документе"""
        return len(self.entities)

    def __iter__(self):
        """Итерация по сущностям"""
        return iter(self.entities)


# =============================================================================
# Фикстуры
# =============================================================================

@pytest.fixture
def mock_ifc_entity():
    """
    Фабрика для создания MockIfcEntity

    Example:
        def test_something(mock_ifc_entity):
            entity = mock_ifc_entity('IfcWall', Name='Test')
    """
    return MockIfcEntity


@pytest.fixture
def mock_ifc_doc():
    """
    Mock для IFC документа

    Example:
        def test_something(mock_ifc_doc):
            entity = mock_ifc_doc.create_entity('IfcWall', Name='Test')
    """
    return MockIfcDoc()


@pytest.fixture
def geometry_builder(mock_ifc_doc):
    """
    GeometryBuilder с mock документом

    Example:
        def test_something(geometry_builder):
            result = geometry_builder.create_line([0, 0, 0], [10, 10, 10])
    """
    from geometry_builder import GeometryBuilder
    return GeometryBuilder(mock_ifc_doc)


@pytest.fixture
def type_factory(mock_ifc_doc):
    """
    TypeFactory с mock документом

    Example:
        def test_something(type_factory):
            stud_type = type_factory.get_or_create_stud_type(...)
    """
    from type_factory import TypeFactory
    return TypeFactory(mock_ifc_doc)


@pytest.fixture
def instance_factory(mock_ifc_doc):
    """
    InstanceFactory с mock документом

    Example:
        def test_something(instance_factory):
            result = instance_factory.create_bolt_assembly(...)
    """
    from instance_factory import InstanceFactory
    return InstanceFactory(mock_ifc_doc)


@pytest.fixture
def material_manager(mock_ifc_doc):
    """
    MaterialManager с mock документом

    Example:
        def test_something(material_manager):
            material = material_manager.create_material(...)
    """
    from material_manager import MaterialManager
    return MaterialManager(mock_ifc_doc)


@pytest.fixture(scope='session')
def python_path():
    """Возвращает путь к python модулям"""
    return os.path.join(os.path.dirname(__file__), '..', 'python')


@pytest.fixture(scope='function')
def valid_bolt_params():
    """
    Параметры валидного болта по умолчанию

    Example:
        def test_something(valid_bolt_params):
            result = generate_bolt_assembly(valid_bolt_params)
    """
    return {
        'bolt_type': '1.1',
        'diameter': 20,
        'length': 800,
        'material': '09Г2С'
    }


@pytest.fixture(scope='function')
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ['1.1', '1.2', '2.1', '5']


@pytest.fixture(scope='function')
def all_diameters():
    """Все доступные диаметры"""
    return [12, 16, 20, 24, 30, 36, 42, 48]


@pytest.fixture(scope='function')
def all_materials():
    """Все доступные материалы"""
    return ['09Г2С', 'ВСт3пс2', '10Г2']
```

#### 7.1.3. Обновление тестовых файлов

**Пример для `tests/test_geometry_builder.py`:**

**До:**
```python
class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type, *args, **kwargs):
        # ... дублирование кода

class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        # ... дублирование кода

class TestGeometryBuilderInit:
    def test_geometry_builder_init(self):
        mock_ifc = MockIfcDoc()
        # ...
```

**После:**
```python
"""
Тесты для geometry_builder.py - построение IFC геометрии
"""
import pytest


class TestGeometryBuilderInit:
    """Тесты инициализации GeometryBuilder"""

    def test_geometry_builder_init(self, mock_ifc_doc):
        """GeometryBuilder должен инициализироваться с ifc_doc"""
        from geometry_builder import GeometryBuilder

        builder = GeometryBuilder(mock_ifc_doc)

        assert builder.ifc is mock_ifc_doc
        assert builder._context is None
```

**Критерии приёмки:**
- [ ] MockIfcEntity в conftest.py
- [ ] MockIfcDoc в conftest.py
- [ ] Фикстуры для основных классов
- [ ] Дублирование удалено из всех тестовых файлов
- [ ] Все тесты проходят

---

### 7.2. Добавление интеграционных тестов

**Файл:** `tests/test_integration.py`  
**Длительность:** 2-3 дня  
**Сложность:** Средняя

#### 7.2.1. Содержимое файла

```python
"""
test_integration.py — Интеграционные тесты полного цикла

Тесты проверяют полную цепочку генерации болта:
1. Валидация параметров
2. Создание типов
3. Создание сборки
4. Экспорт в IFC
5. Валидация IFC файла
"""

import pytest
import tempfile
import os
from typing import Dict, Any


class TestFullCycleGeneration:
    """Интеграционные тесты полной генерации болта"""

    def test_generate_bolt_type_1_1(self, valid_bolt_params):
        """Генерация болта типа 1.1"""
        from instance_factory import generate_bolt_assembly

        params = {
            'bolt_type': '1.1',
            'diameter': 20,
            'length': 800,
            'material': '09Г2С'
        }

        ifc_str, mesh_data = generate_bolt_assembly(params)

        # Проверка IFC строки
        assert ifc_str.startswith('ISO-10303-21')
        assert 'IFC4' in ifc_str
        assert 'IfcMechanicalFastener' in ifc_str

        # Проверка mesh данных
        assert isinstance(mesh_data, dict)
        assert 'meshes' in mesh_data
        assert len(mesh_data['meshes']) >= 4  # stud, washer, 2 nuts

    def test_generate_bolt_type_2_1(self):
        """Генерация болта типа 2.1 (с 4 гайками)"""
        from instance_factory import generate_bolt_assembly

        params = {
            'bolt_type': '2.1',
            'diameter': 24,
            'length': 1000,
            'material': '09Г2С'
        }

        ifc_str, mesh_data = generate_bolt_assembly(params)

        # Проверка количества компонентов
        assert len(mesh_data['meshes']) >= 6  # stud, washer, 4 nuts

    def test_generate_all_bolt_types(self, all_bolt_types):
        """Генерация болтов всех типов"""
        from instance_factory import generate_bolt_assembly

        for bolt_type in all_bolt_types:
            params = {
                'bolt_type': bolt_type,
                'diameter': 20,
                'length': 800,
                'material': '09Г2С'
            }

            ifc_str, mesh_data = generate_bolt_assembly(params)

            assert ifc_str.startswith('ISO-10303-21'), f"Failed for type {bolt_type}"
            assert len(mesh_data['meshes']) >= 4, f"Failed for type {bolt_type}"

    def test_generate_all_diameters(self, all_diameters):
        """Генерация болтов всех диаметров"""
        from instance_factory import generate_bolt_assembly

        for diameter in all_diameters:
            params = {
                'bolt_type': '1.1',
                'diameter': diameter,
                'length': 800,
                'material': '09Г2С'
            }

            ifc_str, mesh_data = generate_bolt_assembly(params)

            assert ifc_str.startswith('ISO-10303-21'), f"Failed for diameter {diameter}"

    def test_generate_all_materials(self, all_materials):
        """Генерация болтов со всеми материалами"""
        from instance_factory import generate_bolt_assembly

        for material in all_materials:
            params = {
                'bolt_type': '1.1',
                'diameter': 20,
                'length': 800,
                'material': material
            }

            ifc_str, mesh_data = generate_bolt_assembly(params)

            assert ifc_str.startswith('ISO-10303-21'), f"Failed for material {material}"
            assert material in ifc_str, f"Material {material} not found in IFC"


class TestIFCFileValidation:
    """Тесты валидации IFC файлов"""

    def test_ifc_file_structure(self):
        """Проверка структуры IFC файла"""
        from instance_factory import generate_bolt_assembly
        import ifcopenshell

        params = {
            'bolt_type': '1.1',
            'diameter': 20,
            'length': 800,
            'material': '09Г2С'
        }

        ifc_str, _ = generate_bolt_assembly(params)

        # Сохраняем во временный файл
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
            f.write(ifc_str)
            temp_path = f.name

        try:
            ifc_doc = ifcopenshell.open(temp_path)

            # Проверка схемы
            assert ifc_doc.schema.startswith('IFC4')

            # Проверка OwnerHistory
            owner_history = ifc_doc.by_id(1)
            assert owner_history.is_a() == 'IfcOwnerHistory'

            # Проверка базовой структуры
            projects = ifc_doc.by_type('IfcProject')
            assert len(projects) == 1

            sites = ifc_doc.by_type('IfcSite')
            assert len(sites) == 1

            buildings = ifc_doc.by_type('IfcBuilding')
            assert len(buildings) == 1

            storeys = ifc_doc.by_type('IfcBuildingStorey')
            assert len(storeys) == 1

            # Проверка болтов
            fasteners = ifc_doc.by_type('IfcMechanicalFastener')
            assert len(fasteners) >= 4

            # Проверка типов
            fastener_types = ifc_doc.by_type('IfcMechanicalFastenerType')
            assert len(fastener_types) >= 4

            # Проверка материалов
            materials = ifc_doc.by_type('IfcMaterial')
            assert len(materials) >= 1

            # Проверка отношений
            rel_aggregates = ifc_doc.by_type('IfcRelAggregates')
            assert len(rel_aggregates) >= 1

            rel_defines = ifc_doc.by_type('IfcRelDefinesByType')
            assert len(rel_defines) >= 1

            rel_associates = ifc_doc.by_type('IfcRelAssociatesMaterial')
            assert len(rel_associates) >= 1

        finally:
            os.unlink(temp_path)

    def test_ifc_file_contains_material_properties(self):
        """Проверка наличия свойств материалов"""
        from instance_factory import generate_bolt_assembly
        import ifcopenshell

        params = {
            'bolt_type': '1.1',
            'diameter': 20,
            'length': 800,
            'material': '09Г2С'
        }

        ifc_str, _ = generate_bolt_assembly(params)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
            f.write(ifc_str)
            temp_path = f.name

        try:
            ifc_doc = ifcopenshell.open(temp_path)

            # Проверка PropertySets
            mat_props = ifc_doc.by_type('IfcMaterialProperties')
            assert len(mat_props) >= 2  # Pset_MaterialCommon и Pset_MaterialSteel

            # Проверка имён PropertySets
            pset_names = [p.Name for p in mat_props]
            assert 'Pset_MaterialCommon' in pset_names
            assert 'Pset_MaterialSteel' in pset_names

        finally:
            os.unlink(temp_path)


class TestMultipleDocuments:
    """Тесты работы с множественными документами"""

    def test_create_multiple_documents(self):
        """Создание нескольких документов"""
        from main import IFCDocumentManager

        manager = IFCDocumentManager()

        # Создание двух документов
        doc1 = manager.create_document('bolt-1')
        doc2 = manager.create_document('bolt-2')

        # Проверка изоляции
        assert doc1 is not doc2
        assert len(manager.list_documents()) == 2

        # Удаление
        manager.delete_document('bolt-1')
        assert len(manager.list_documents()) == 1

        # Очистка
        manager.reset()

    def test_reset_document(self):
        """Сброс документа"""
        from main import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document('test')

        # Создание болта
        factory = InstanceFactory(doc)
        factory.create_bolt_assembly('1.1', 20, 800, '09Г2С')

        # Проверка наличия болтов
        fasteners = doc.by_type('IfcMechanicalFastener')
        assert len(fasteners) >= 4

        # Сброс
        manager.reset_document('test')

        # Проверка удаления болтов
        fasteners = doc.by_type('IfcMechanicalFastener')
        assert len(fasteners) == 0

        # Очистка
        manager.reset()
```

**Критерии приёмки:**
- [ ] Integration тесты созданы
- [ ] Тесты полного цикла
- [ ] Тесты валидации IFC
- [ ] Тесты множественных документов
- [ ] Все тесты проходят

---

### 7.3. Финальная проверка фазы 7

#### 7.3.1. Запустить все тесты

```bash
pytest tests/ -v --tb=short
# Ожидаемый результат: 120+ passed (добавились интеграционные)
```

#### 7.3.2. Проверка покрытия

```bash
pytest tests/ -v --cov=python --cov-report=html --cov-report=term-missing

# Ожидаемый результат: coverage > 90%
```

#### 7.3.3. Зафиксировать изменения

```bash
git add tests/conftest.py tests/test_integration.py
git commit -m "refactor(phase7): централизация mock объектов и интеграционные тесты

- Mock объекты перемещены в conftest.py
- Созданы универсальные фикстуры
- Добавлены интеграционные тесты
- Покрытие увеличено до 90%+
- Удалено дублирование кода в тестах

#refactoring #phase7"
```

**Критерии приёмки:**
- [ ] Все тесты проходят
- [ ] Покрытие > 90%
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 7

### Обязательные задачи:
- [ ] 7.1.1. MockIfcEntity в conftest.py
- [ ] 7.1.2. MockIfcDoc в conftest.py
- [ ] 7.1.3. Фикстуры созданы
- [ ] 7.1.3. Дублирование удалено из тестов
- [ ] 7.2.1. Integration тесты созданы
- [ ] 7.3.1. Все тесты проходят
- [ ] 7.3.2. Покрытие > 90%
- [ ] 7.3.3. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Mock файлов | 5 | 1 | -4 |
| Строк дублирования | ~250 | 0 | -250 |
| Фикстур | 5 | 10+ | +5 |
| Интеграционных тестов | 0 | 10+ | +10 |
| Тестов пройдено | 107 | 120+ | +13+ |
| Coverage | ~75% | 90%+ | +15% |

---

## 🚀 Следующие шаги

После завершения фазы 7:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 8**

**Ссылка на следующую фазу:** `refactoring/PHASE_8_TODO.md`

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
