# 📋 Phase 4: Устранение циклических зависимостей

**Длительность:** 1 неделя  
**Приоритет:** 🟡 Средний  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 4 убедитесь, что выполнены Phase 0-3:**

- [ ] Pre-commit hooks работают (Phase 0)
- [ ] Критические исправления выполнены (Phase 1)
- [ ] Модули разделены (Phase 2)
- [ ] RepresentationMaps добавлены (Phase 3)
- [ ] Все 107 тестов проходят
- [ ] Изменения Phase 1-3 закоммичены

**Если предыдущие фазы не выполнены:**
1. Откройте `refactoring/PHASE_1_TODO.md`, `refactoring/PHASE_2_TODO.md`, `refactoring/PHASE_3_TODO.md`
2. Выполните все задачи предыдущих фаз
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Устранение потенциальных циклических зависимостей между модулями через введение Protocol интерфейсов и dependency injection.

### Цели:
- ✅ Создать Protocol интерфейсы для основных классов
- ✅ Устранить циклические зависимости
- ✅ Улучшить тестируемость кода
- ✅ Сохранить прохождение всех тестов

---

## 📝 Задачи

### 4.1. Создание Protocol интерфейсов

**Файл:** `python/protocols.py`  
**Длительность:** 1 день

#### 4.1.1. Содержимое файла

```python
"""
protocols.py — Protocol интерфейсы для dependency injection

Согласно PEP 544:
- Protocol определяет структурный подтип
- Позволяет использовать duck typing с проверкой типов
- Устраняет необходимость в явных интерфейсах
"""

from typing import Protocol, List, Any, Optional, Dict, Tuple, runtime_checkable


# =============================================================================
# IFC Document Protocol
# =============================================================================

@runtime_checkable
class IfcDocumentProtocol(Protocol):
    """
    Протокол для IFC документа

    Определяет минимальный интерфейс для работы с IFC файлом.
    Позволяет использовать mock объекты в тестах.
    """

    def create_entity(self, entity_type: str, *args, **kwargs) -> Any:
        """Создание IFC сущности"""
        ...

    def by_type(self, entity_type: str, include_subtypes: bool = False) -> List[Any]:
        """Получение сущностей по типу"""
        ...

    def by_id(self, id: int) -> Any:
        """Получение сущности по ID"""
        ...

    def by_guid(self, guid: str) -> Any:
        """Получение сущности по GUID"""
        ...

    def write(self, filepath: str) -> None:
        """Запись в файл"""
        ...

    def remove(self, entity: Any) -> None:
        """Удаление сущности"""
        ...

    def get_inverse(self, entity: Any) -> List[Any]:
        """Получение обратных ссылок"""
        ...

    def traverse(self, entity: Any, max_levels: int = None) -> List[Any]:
        """Обход графа сущности"""
        ...

    @property
    def schema(self) -> str:
        """Схема IFC (например, 'IFC4')"""
        ...

    def __len__(self) -> int:
        """Количество сущностей в файле"""
        ...


# =============================================================================
# Geometry Builder Protocol
# =============================================================================

@runtime_checkable
class GeometryBuilderProtocol(Protocol):
    """
    Протокол для построителя геометрии

    Определяет интерфейс для создания IFC геометрии.
    """

    def create_bent_stud_solid(
        self,
        bolt_type: str,
        diameter: int,
        length: int
    ) -> Any:
        """Создание изогнутой шпильки"""
        ...

    def create_straight_stud_solid(
        self,
        diameter: int,
        length: int
    ) -> Any:
        """Создание прямой шпильки"""
        ...

    def create_nut_solid(
        self,
        diameter: int,
        height: int
    ) -> Any:
        """Создание гайки"""
        ...

    def create_washer_solid(
        self,
        inner_d: int,
        outer_d: int,
        thickness: int
    ) -> Any:
        """Создание шайбы"""
        ...

    def deep_copy(self, entity: Any) -> Any:
        """Глубокое копирование геометрии"""
        ...

    def associate_representation(
        self,
        product_type: Any,
        shape_rep: Any,
        use_map: bool = True
    ) -> Optional[Any]:
        """Ассоциация представления с типом"""
        ...


# =============================================================================
# Material Manager Protocol
# =============================================================================

@runtime_checkable
class MaterialManagerProtocol(Protocol):
    """
    Протокол для менеджера материалов

    Определяет интерфейс для управления материалами IFC.
    """

    def create_material(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        material_key: Optional[str] = None
    ) -> Any:
        """Создание материала"""
        ...

    def get_material(self, name: str) -> Optional[Any]:
        """Получение материала"""
        ...

    def create_material_list(
        self,
        materials: List[Any],
        name: Optional[str] = None
    ) -> Any:
        """Создание списка материалов"""
        ...

    def associate_material(
        self,
        entity: Any,
        material: Any
    ) -> Any:
        """Ассоциация материала с сущностью"""
        ...

    def get_cached_materials_count(self) -> int:
        """Количество закэшированных материалов"""
        ...


# =============================================================================
# Type Factory Protocol
# =============================================================================

@runtime_checkable
class TypeFactoryProtocol(Protocol):
    """
    Протокол для фабрики типов

    Определяет интерфейс для создания и кэширования типов IFC.
    """

    def get_or_create_stud_type(
        self,
        bolt_type: str,
        diameter: int,
        length: int,
        material: str
    ) -> Any:
        """Создание/получение типа шпильки"""
        ...

    def get_or_create_nut_type(
        self,
        diameter: int,
        material: str
    ) -> Any:
        """Создание/получение типа гайки"""
        ...

    def get_or_create_washer_type(
        self,
        diameter: int,
        material: str
    ) -> Any:
        """Создание/получение типа шайбы"""
        ...

    def get_or_create_assembly_type(
        self,
        bolt_type: str,
        diameter: int,
        material: str
    ) -> Any:
        """Создание/получение типа сборки"""
        ...

    def get_cached_types_count(self) -> int:
        """Количество закэшированных типов"""
        ...


# =============================================================================
# Instance Factory Protocol
# =============================================================================

@runtime_checkable
class InstanceFactoryProtocol(Protocol):
    """
    Протокол для фабрики инстансов

    Определяет интерфейс для создания сборок болтов.
    """

    def create_bolt_assembly(
        self,
        bolt_type: str,
        diameter: int,
        length: int,
        material: str
    ) -> Dict[str, Any]:
        """Создание сборки болта"""
        ...


# =============================================================================
# Type Aliases для удобства
# =============================================================================

# Полный набор протоколов для injection
class AllProtocols(Protocol):
    """Комбинированный протокол для всех зависимостей"""

    ifc_document: IfcDocumentProtocol
    geometry_builder: GeometryBuilderProtocol
    material_manager: MaterialManagerProtocol
    type_factory: TypeFactoryProtocol
    instance_factory: InstanceFactoryProtocol
```

**Критерии приёмки:**
- [ ] Все Protocol интерфейсы определены
- [ ] @runtime_checkable декоратор применён
- [ ] Type hints корректны
- [ ] Docstrings полные

---

### 4.2. Рефакторинг импортов в geometry_builder.py

**Файл:** `python/geometry_builder.py`  
**Длительность:** 2-3 часа

#### 4.2.1. Устранение зависимости от utils.py

**До:**
```python
from utils import get_ifcopenshell
from ifcopenshell.util.representation import get_context
```

**После:**
```python
# Прямой импорт ifcopenshell без ленивой загрузки
# В Pyodide ifcopenshell уже установлен через micropip
import ifcopenshell
from ifcopenshell.util.shape_builder import ShapeBuilder, V
from ifcopenshell.util.representation import get_context
from typing import Any, List, Optional
```

#### 4.2.2. Обновление класса GeometryBuilder

```python
class GeometryBuilder:
    """Построитель IFC геометрии с использованием shape_builder"""

    def __init__(self, ifc_doc: 'IfcDocumentProtocol'):
        """
        Инициализация GeometryBuilder

        Args:
            ifc_doc: IFC документ (должен поддерживать IfcDocumentProtocol)
        """
        self.ifc = ifc_doc
        self.builder = ShapeBuilder(ifc_doc)
        self._context: Optional[Any] = None
```

**Критерии приёмки:**
- [ ] Прямой импорт ifcopenshell
- [ ] Type hints для ifc_doc
- [ ] Тесты проходят

---

### 4.3. Обновление type_factory.py

**Файл:** `python/type_factory.py`  
**Длительность:** 2-3 часа

#### 4.3.1. Добавление Protocol type hints

```python
from typing import Dict, Tuple, Any, Optional
from protocols import (
    IfcDocumentProtocol,
    GeometryBuilderProtocol,
    MaterialManagerProtocol
)


class TypeFactory:
    """Фабрика типов IFC MechanicalFastenerType"""

    def __init__(self, ifc_doc: 'IfcDocumentProtocol'):
        """
        Инициализация TypeFactory

        Args:
            ifc_doc: IFC документ
        """
        self.ifc = ifc_doc
        self.types_cache: Dict[Tuple, Any] = {}
        self.builder: GeometryBuilderProtocol = GeometryBuilder(ifc_doc)
        self.material_manager: MaterialManagerProtocol = MaterialManager(ifc_doc)

        # Получаем OwnerHistory из документа
        owner_histories = self.ifc.by_type('IfcOwnerHistory')
        self.owner_history = owner_histories[0] if owner_histories else None
```

**Критерии приёмки:**
- [ ] Protocol type hints добавлены
- [ ] Тесты проходят

---

### 4.4. Обновление instance_factory.py

**Файл:** `python/instance_factory.py`  
**Длительность:** 2-3 часа

#### 4.4.1. Добавление Protocol type hints

```python
from typing import Dict, Any, List, Optional
from protocols import (
    IfcDocumentProtocol,
    TypeFactoryProtocol,
    MaterialManagerProtocol,
    GeometryBuilderProtocol
)


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(
        self,
        ifc_doc: 'IfcDocumentProtocol',
        type_factory: Optional['TypeFactoryProtocol'] = None
    ):
        """
        Инициализация InstanceFactory

        Args:
            ifc_doc: IFC документ
            type_factory: TypeFactory для создания типов (опционально)
        """
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)
        self.material_manager: MaterialManagerProtocol = MaterialManager(ifc_doc)
```

**Критерии приёмки:**
- [ ] Protocol type hints добавлены
- [ ] Тесты проходят

---

### 4.5. Создание контейнера зависимостей (DI Container)

**Файл:** `python/di_container.py`  
**Длительность:** 1 день

#### 4.5.1. Содержимое файла

```python
"""
di_container.py — Dependency Injection контейнер

Предоставляет централизованное управление зависимостями:
- Ленивая инициализация зависимостей
- Singleton для общих зависимостей
- Поддержка тестирования через mock объекты
"""

from typing import Optional, Any
from protocols import (
    IfcDocumentProtocol,
    GeometryBuilderProtocol,
    MaterialManagerProtocol,
    TypeFactoryProtocol,
    InstanceFactoryProtocol
)


class DIContainer:
    """
    DI контейнер для приложения

    Пример использования:
        container = DIContainer()
        container.initialize_ifc_document()

        # Получение зависимостей
        factory = container.get_instance_factory()
        result = factory.create_bolt_assembly(...)
    """

    def __init__(self):
        """Инициализация контейнера"""
        self._ifc_doc: Optional[IfcDocumentProtocol] = None
        self._geometry_builder: Optional[GeometryBuilderProtocol] = None
        self._material_manager: Optional[MaterialManagerProtocol] = None
        self._type_factory: Optional[TypeFactoryProtocol] = None
        self._instance_factory: Optional[InstanceFactoryProtocol] = None

    def initialize_ifc_document(self, schema: str = 'IFC4') -> IfcDocumentProtocol:
        """
        Инициализация IFC документа

        Args:
            schema: IFC схема (по умолчанию 'IFC4')

        Returns:
            IFC документ
        """
        if self._ifc_doc is None:
            import ifcopenshell
            self._ifc_doc = ifcopenshell.file(schema=schema)

            # Создать базовую структуру
            self._create_base_structure()

        return self._ifc_doc

    def _create_base_structure(self):
        """Создание базовой IFC структуры"""
        ifc = self._ifc_doc

        # OwnerHistory
        owner_history = ifc.create_entity('IfcOwnerHistory', ...)

        # Project
        project = ifc.create_entity('IfcProject',
            OwnerHistory=owner_history,
            Name='Anchor Bolt Generator'
        )

        # Site, Building, Storey
        # ...

    def get_ifc_document(self) -> IfcDocumentProtocol:
        """Получение IFC документа"""
        if self._ifc_doc is None:
            raise RuntimeError("IFC документ не инициализирован")
        return self._ifc_doc

    def get_geometry_builder(self) -> GeometryBuilderProtocol:
        """Получение GeometryBuilder"""
        if self._geometry_builder is None:
            from geometry_builder import GeometryBuilder
            self._geometry_builder = GeometryBuilder(self.get_ifc_document())
        return self._geometry_builder

    def get_material_manager(self) -> MaterialManagerProtocol:
        """Получение MaterialManager"""
        if self._material_manager is None:
            from material_manager import MaterialManager
            self._material_manager = MaterialManager(self.get_ifc_document())
        return self._material_manager

    def get_type_factory(self) -> TypeFactoryProtocol:
        """Получение TypeFactory"""
        if self._type_factory is None:
            from type_factory import TypeFactory
            self._type_factory = TypeFactory(self.get_ifc_document())
        return self._type_factory

    def get_instance_factory(self) -> InstanceFactoryProtocol:
        """Получение InstanceFactory"""
        if self._instance_factory is None:
            from instance_factory import InstanceFactory
            self._instance_factory = InstanceFactory(
                self.get_ifc_document(),
                self.get_type_factory()
            )
        return self._instance_factory

    def reset(self):
        """Сброс контейнера"""
        self._ifc_doc = None
        self._geometry_builder = None
        self._material_manager = None
        self._type_factory = None
        self._instance_factory = None

    # Для тестирования
    def set_mock(
        self,
        protocol: type,
        mock_object: Any
    ):
        """
        Установка mock объекта для тестирования

        Args:
            protocol: Protocol тип
            mock_object: Mock объект
        """
        if protocol == IfcDocumentProtocol:
            self._ifc_doc = mock_object
        elif protocol == GeometryBuilderProtocol:
            self._geometry_builder = mock_object
        # ...
```

**Критерии приёмки:**
- [ ] DI контейнер создан
- [ ] Ленивая инициализация работает
- [ ] Поддержка mock объектов для тестов
- [ ] Тесты проходят

---

### 4.6. Обновление тестов для использования Protocol

**Файл:** `tests/conftest.py`  
**Длительность:** 2-3 часа

#### 4.6.1. Обновление MockIfcDoc

```python
from protocols import IfcDocumentProtocol


class MockIfcDoc(IfcDocumentProtocol):
    """Mock для IFC документа, реализующий IfcDocumentProtocol"""

    def __init__(self):
        self.entities = []
        self._by_type = {}
        self.schema = "IFC4"

    def create_entity(self, entity_type: str, *args, **kwargs) -> Any:
        # ... реализация

    def by_type(self, entity_type: str, include_subtypes: bool = False) -> List[Any]:
        # ... реализация

    # Остальные методы протокола
    # ...
```

**Критерии приёмки:**
- [ ] MockIfcDoc реализует IfcDocumentProtocol
- [ ] Тесты проходят

---

### 4.7. Финальная проверка фазы 4

#### 4.7.1. Запустить все тесты

```bash
pytest tests/ -v --tb=short
# Ожидаемый результат: 107 passed
```

#### 4.7.2. Проверка mypy

```bash
mypy python/ --ignore-missing-imports
# Ожидаемый результат: минимальное количество предупреждений
```

#### 4.7.3. Зафиксировать изменения

```bash
git add python/protocols.py python/di_container.py
git commit -m "refactor(phase4): Protocol интерфейсы и DI контейнер

- Созданы Protocol интерфейсы для всех основных классов
- Устранены циклические зависимости
- Добавлен DI контейнер для управления зависимостями
- Улучшена тестируемость через mock объекты

#refactoring #phase4"
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] mypy проверяет типы
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 4

### Обязательные задачи:
- [ ] 4.1.1. Protocol интерфейсы созданы
- [ ] 4.2.1. geometry_builder.py обновлён
- [ ] 4.3.1. type_factory.py обновлён
- [ ] 4.4.1. instance_factory.py обновлён
- [ ] 4.5.1. DI контейнер создан
- [ ] 4.6.1. Тесты обновлены
- [ ] 4.7.1. Все тесты проходят
- [ ] 4.7.2. mypy проверка
- [ ] 4.7.3. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Файлов | 10 | 12 | +2 |
| Строк (protocols.py) | 0 | ~200 | +200 |
| Строк (di_container.py) | 0 | ~150 | +150 |
| Циклических зависимостей | 2 | 0 | -2 |
| Тестов пройдено | 107 | 107 | 0 |

---

## 🚀 Следующие шаги

После завершения фазы 4:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 5**

**Ссылка на следующую фазу:** `refactoring/PHASE_5_TODO.md`

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
