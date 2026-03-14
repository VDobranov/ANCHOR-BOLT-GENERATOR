# 📋 Phase 5: Улучшение архитектуры

**Длительность:** 2 недели  
**Приоритет:** 🟡 Средний  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 5 убедитесь, что выполнены Phase 0-4:**

- [ ] Pre-commit hooks работают (Phase 0)
- [ ] Критические исправления выполнены (Phase 1)
- [ ] Модули разделены (Phase 2)
- [ ] RepresentationMaps добавлены (Phase 3)
- [ ] Protocol интерфейсы созданы (Phase 4)
- [ ] Все 107 тестов проходят
- [ ] Изменения Phase 1-4 закоммичены

**Если предыдущие фазы не выполнены:**
1. Откройте файлы `refactoring/PHASE_1_TODO.md` — `refactoring/PHASE_4_TODO.md`
2. Выполните все задачи предыдущих фаз
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Улучшение архитектуры проекта через устранение Singleton паттерна, разделение слоёв ответственности и создание менеджера документов.

### Цели:
- ✅ Удалить Singleton из main.py
- ✅ Создать IFCDocumentManager для управления документами
- ✅ Вынести бизнес-логику в отдельный слой
- ✅ Сохранить прохождение всех тестов

---

## 📝 Задачи

### 5.1. Удаление Singleton паттерна

**Файл:** `python/main.py`  
**Длительность:** 2-3 дня  
**Сложность:** Высокая

#### 5.1.1. Текущее состояние (ДО)

```python
class IFCDocument:
    """Класс для управления IFC документом"""

    _instance = None  # Singleton - глобальное состояние

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.file = None
        self.material_manager = None
        self._initialized = True
```

**Проблемы:**
- Singleton создаёт глобальное состояние
- Тесты влияют друг на друга
- Невозможно создать несколько документов
- Сложно тестировать изолированно

#### 5.1.2. Целевое состояние (ПОСЛЕ)

```python
"""
main.py — Менеджер IFC документов

Управление множественными IFC документами:
- Каждый документ имеет уникальный ID
- Документы изолированы друг от друга
- Поддержка тестирования через временные документы
"""

from typing import Dict, Optional, Any
import ifcopenshell
import numpy as np
from material_manager import MaterialManager


class IFCDocumentManager:
    """
    Менеджер IFC документов с поддержкой множественных документов

    Пример использования:
        manager = IFCDocumentManager()
        doc = manager.create_document('my-bolt', schema='IFC4')
        # ... работа с документом
        manager.delete_document('my-bolt')
    """

    def __init__(self):
        """Инициализация менеджера"""
        self._documents: Dict[str, ifcopenshell.file] = {}
        self._material_managers: Dict[str, MaterialManager] = {}
        self._current_id: Optional[str] = None

    def create_document(
        self,
        doc_id: str,
        schema: str = 'IFC4'
    ) -> ifcopenshell.file:
        """
        Создание нового IFC документа

        Args:
            doc_id: Уникальный идентификатор документа
            schema: IFC схема (по умолчанию 'IFC4')

        Returns:
            IFC документ (ifcopenshell.file)
        """
        if doc_id in self._documents:
            raise ValueError(f"Документ '{doc_id}' уже существует")

        doc = self._initialize_document(schema)
        self._documents[doc_id] = doc
        self._current_id = doc_id

        return doc

    def _initialize_document(self, schema: str) -> ifcopenshell.file:
        """
        Инициализация нового IFC документа

        Создаёт базовую структуру:
        - IfcOwnerHistory (#1)
        - IfcProject
        - IfcSite
        - IfcBuilding
        - IfcBuildingStorey

        Args:
            schema: IFC схема

        Returns:
            Инициализированный IFC документ
        """
        import time
        import tempfile
        import os

        timestamp = int(time.time())

        spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','{time.strftime('%Y-%m-%dT%H:%M:%S')}',(''),(''),'IfcOpenShell 0.8.4','IfcOpenShell 0.8.4','');
FILE_SCHEMA(('{schema}'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#6,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG','ABG',$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCORGANIZATION('ABG','ABG',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','Anchor Bolt Generator','ABG');
ENDSEC;
END-ISO-10303-21;
"""

        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as tmp:
            tmp.write(spf_content)
            tmp_path = tmp.name

        doc = ifcopenshell.open(tmp_path)
        os.unlink(tmp_path)

        # Сохраняем ссылку на OwnerHistory
        doc.owner_history = doc.by_id(1)

        # Создаём базовую структуру
        self._create_base_structure(doc)

        # Создаём менеджер материалов
        self._material_managers[str(id(doc))] = MaterialManager(doc)

        return doc

    def _create_base_structure(self, doc: ifcopenshell.file):
        """Создание базовой IFC структуры: Project/Site/Building/Storey"""
        f = doc
        import ifcopenshell.util.element

        # Project
        project = f.create_entity('IfcProject',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            Name='Anchor Bolt Generator',
            Description='Generated anchor bolts with IFC4 ADD2 TC1'
        )

        # Site
        site = f.create_entity('IfcSite',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            Name='Default Site'
        )

        # Building
        building = f.create_entity('IfcBuilding',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            Name='Default Building'
        )

        # Storey
        storey = f.create_entity('IfcBuildingStorey',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            Name='Storey 1',
            Elevation=0.0
        )

        # Иерархия
        f.create_entity('IfcRelAggregates',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=project,
            RelatedObjects=[site]
        )
        f.create_entity('IfcRelAggregates',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=site,
            RelatedObjects=[building]
        )
        f.create_entity('IfcRelAggregates',
            GlobalId=ifcopenshell.util.element.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=building,
            RelatedObjects=[storey]
        )

        # Units and contexts
        from ifc_generator import IFCGenerator
        gen = IFCGenerator(f)
        gen.setup_units_and_contexts()

    def get_document(self, doc_id: Optional[str] = None) -> ifcopenshell.file:
        """
        Получение IFC документа

        Args:
            doc_id: Идентификатор документа (опционально, используется текущий)

        Returns:
            IFC документ

        Raises:
            ValueError: Если документ не найден
        """
        doc_id = doc_id or self._current_id
        if doc_id is None:
            raise ValueError("Документ не выбран и нет текущего документа")
        if doc_id not in self._documents:
            raise ValueError(f"Документ '{doc_id}' не найден")
        return self._documents[doc_id]

    def get_material_manager(
        self,
        doc_id: Optional[str] = None
    ) -> MaterialManager:
        """
        Получение менеджера материалов для документа

        Args:
            doc_id: Идентификатор документа

        Returns:
            MaterialManager для документа
        """
        doc_id = doc_id or self._current_id
        if doc_id is None:
            raise ValueError("Документ не выбран")
        key = str(id(self._documents[doc_id]))
        return self._material_managers.get(key)

    def reset_document(self, doc_id: Optional[str] = None) -> ifcopenshell.file:
        """
        Сброс документа: удаление болтов, сохранение структуры

        Args:
            doc_id: Идентификатор документа

        Returns:
            Сброшенный IFC документ
        """
        doc = self.get_document(doc_id)

        # Сохраняем базовые структуры
        projects = doc.by_type('IfcProject')
        sites = doc.by_type('IfcSite')
        buildings = doc.by_type('IfcBuilding')
        storeys = doc.by_type('IfcBuildingStorey')

        # Сохраняем имена материалов
        material_names = []
        mat_mgr = self.get_material_manager(doc_id)
        if mat_mgr:
            material_names = list(mat_mgr.materials_cache.keys())

        # Удаляем болты и связанные сущности
        self._delete_fasteners_and_relations(doc)

        # Пересоздаём базовую структуру
        self._create_base_structure(doc)

        # Восстанавливаем material_manager
        self._material_managers[str(id(doc))] = MaterialManager(doc)

        return doc

    def _delete_fasteners_and_relations(self, doc: ifcopenshell.file):
        """Удаление болтов и связанных сущностей"""
        import ifcopenshell.util.element

        # Типы сущностей для удаления
        entity_types = [
            'IfcMechanicalFastener',
            'IfcMechanicalFastenerType',
            'IfcRelDefinesByType',
            'IfcRelAggregates',
            'IfcRelConnectsElements',
            'IfcRelContainedInSpatialStructure',
            'IfcRelAssociatesMaterial',
            'IfcMaterialList'
        ]

        # Удаляем сущности
        for entity_type in entity_types:
            for entity in doc.by_type(entity_type):
                try:
                    doc.remove(entity)
                except Exception:
                    pass  # Игнорируем ошибки удаления

    def delete_document(self, doc_id: str) -> None:
        """
        Удаление документа

        Args:
            doc_id: Идентификатор документа
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
            if str(id(doc_id)) in self._material_managers:
                del self._material_managers[str(id(doc_id))]
            if self._current_id == doc_id:
                self._current_id = None

    def list_documents(self) -> list[str]:
        """
        Получение списка идентификаторов документов

        Returns:
            Список ID документов
        """
        return list(self._documents.keys())

    def reset(self):
        """Сброс менеджера: удаление всех документов"""
        self._documents.clear()
        self._material_managers.clear()
        self._current_id = None


# =============================================================================
# Фабричные функции для обратной совместимости
# =============================================================================

# Глобальный менеджер (для обратной совместимости)
_doc_manager: Optional[IFCDocumentManager] = None


def get_document_manager() -> IFCDocumentManager:
    """
    Получение менеджера документов

    Returns:
        IFCDocumentManager экземпляр
    """
    global _doc_manager
    if _doc_manager is None:
        _doc_manager = IFCDocumentManager()
    return _doc_manager


def initialize_base_document() -> ifcopenshell.file:
    """Инициализация базового документа"""
    manager = get_document_manager()
    return manager.create_document('default')


def get_ifc_document() -> ifcopenshell.file:
    """Получение текущего IFC документа"""
    manager = get_document_manager()
    return manager.get_document()


def reset_ifc_document() -> ifcopenshell.file:
    """Сброс IFC документа и создание нового"""
    manager = get_document_manager()
    doc = manager.get_document()
    if doc is None:
        return manager.create_document('default')
    return manager.reset_document()


def get_material_manager() -> MaterialManager:
    """Получение менеджера материалов"""
    manager = get_document_manager()
    return manager.get_material_manager()
```

#### 5.1.3. Шаги выполнения

```bash
# 1. Открыть файл для редактирования
code python/main.py

# 2. Полностью переписать файл с новым кодом

# 3. Запустить тесты
pytest tests/test_main.py -v

# 4. Проверить все тесты
pytest tests/ -v --tb=short
```

**Критерии приёмки:**
- [ ] Singleton паттерн удалён
- [ ] IFCDocumentManager создан
- [ ] Поддержка множественных документов
- [ ] Фабричные функции для обратной совместимости
- [ ] Все 10 тестов main проходят
- [ ] Все 107 тестов проходят

---

### 5.2. Вынесение бизнес-логики в отдельный слой

**Длительность:** 3-4 дня  
**Сложность:** Средняя

#### 5.2.1. Создание структуры

```bash
mkdir -p python/core
touch python/core/__init__.py
touch python/core/bolt_builder.py
touch python/core/assembly_builder.py
```

#### 5.2.2. Файл `python/core/bolt_builder.py`

```python
"""
python/core/bolt_builder.py — Построение компонентов болта

Бизнес-логика построения компонентов фундаментных болтов
по ГОСТ 24379.1-2012.

Этот модуль не зависит от IFC и может тестироваться изолированно.
"""

from typing import NamedTuple, List, Optional, Literal
from dataclasses import dataclass

BoltType = Literal['1.1', '1.2', '2.1', '5']


@dataclass
class BoltComponent:
    """Базовый класс компонента болта"""
    name: str
    object_type: str
    position: tuple[float, float, float]


@dataclass
class StudComponent(BoltComponent):
    """Компонент шпильки"""
    bolt_type: BoltType
    diameter: int
    length: int
    hook_length: int
    bend_radius: int
    thread_length: int


@dataclass
class NutComponent(BoltComponent):
    """Компонент гайки"""
    diameter: int
    height: float
    s_width: int


@dataclass
class WasherComponent(BoltComponent):
    """Компонент шайбы"""
    diameter: int
    outer_diameter: int
    thickness: int


class BoltBuilder:
    """
    Построитель компонентов болта

    Определяет состав сборки для каждого типа болта:
    - Тип 1.1, 1.2, 5: шпилька + шайба + 2 гайки
    - Тип 2.1: шпилька + шайба + 4 гайки
    """

    def __init__(self):
        """Инициализация построителя"""
        self._components: List[BoltComponent] = []

    def build_assembly(
        self,
        bolt_type: BoltType,
        diameter: int,
        length: int,
        hook_length: int,
        bend_radius: int,
        thread_length: int,
        nut_height: float,
        washer_thickness: int
    ) -> List[BoltComponent]:
        """
        Построение сборки болта

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)
            length: Длина (мм)
            hook_length: Вылет крюка (мм)
            bend_radius: Радиус загиба (мм)
            thread_length: Длина резьбы (мм)
            nut_height: Высота гайки (мм)
            washer_thickness: Толщина шайбы (мм)

        Returns:
            Список компонентов сборки
        """
        self._components = []

        # Шпилька
        stud = self._create_stud(
            bolt_type=bolt_type,
            diameter=diameter,
            length=length,
            hook_length=hook_length,
            bend_radius=bend_radius,
            thread_length=thread_length
        )
        self._components.append(stud)

        # Шайба (верхняя)
        washer_top = self._create_washer_top(
            diameter=diameter,
            washer_thickness=washer_thickness
        )
        self._components.append(washer_top)

        # Гайки
        self._create_nuts(
            bolt_type=bolt_type,
            length=length,
            diameter=diameter,
            nut_height=nut_height,
            washer_thickness=washer_thickness
        )

        return self._components

    def _create_stud(
        self,
        bolt_type: BoltType,
        diameter: int,
        length: int,
        hook_length: int,
        bend_radius: int,
        thread_length: int
    ) -> StudComponent:
        """Создание компонента шпильки"""
        # Расчёт смещения для разных типов
        z_offset = 0.0
        if bolt_type == '1.1':
            z_offset = thread_length
        elif bolt_type == '1.2':
            z_offset = thread_length

        return StudComponent(
            name=f'Stud_M{diameter}x{length}',
            object_type='STUD',
            position=(0.0, 0.0, z_offset),
            bolt_type=bolt_type,
            diameter=diameter,
            length=length,
            hook_length=hook_length,
            bend_radius=bend_radius,
            thread_length=thread_length
        )

    def _create_washer_top(
        self,
        diameter: int,
        washer_thickness: int
    ) -> WasherComponent:
        """Создание верхней шайбы"""
        return WasherComponent(
            name=f'Washer_Top_M{diameter}',
            object_type='WASHER',
            position=(0.0, 0.0, washer_thickness / 2),
            diameter=diameter,
            outer_diameter=diameter + 24,  # По ГОСТ
            thickness=washer_thickness
        )

    def _create_nuts(
        self,
        bolt_type: BoltType,
        length: int,
        diameter: int,
        nut_height: float,
        washer_thickness: int
    ):
        """Создание гаек"""
        # Верхняя гайка 1
        self._components.append(NutComponent(
            name=f'Nut_Top1_M{diameter}',
            object_type='NUT',
            position=(0.0, 0.0, washer_thickness / 2),
            diameter=diameter,
            height=nut_height,
            s_width=diameter * 1.5
        ))

        # Верхняя гайка 2
        self._components.append(NutComponent(
            name=f'Nut_Top2_M{diameter}',
            object_type='NUT',
            position=(0.0, 0.0, washer_thickness + nut_height),
            diameter=diameter,
            height=nut_height,
            s_width=diameter * 1.5
        ))

        # Нижние гайки (только для типа 2.1)
        if bolt_type == '2.1':
            self._components.append(NutComponent(
                name=f'Nut_Bottom1_M{diameter}',
                object_type='NUT',
                position=(0.0, 0.0, length - washer_thickness / 2 - nut_height / 2),
                diameter=diameter,
                height=nut_height,
                s_width=diameter * 1.5
            ))

            self._components.append(NutComponent(
                name=f'Nut_Bottom2_M{diameter}',
                object_type='NUT',
                position=(0.0, 0.0, length - washer_thickness / 2 - nut_height * 1.5),
                diameter=diameter,
                height=nut_height,
                s_width=diameter * 1.5
            ))
```

#### 5.2.3. Файл `python/core/assembly_builder.py`

```python
"""
python/core/assembly_builder.py — Построение сборок

Бизнес-логика построения сборок фундаментных болтов.
"""

from typing import Dict, Any, List
from .bolt_builder import BoltBuilder, BoltComponent


class AssemblyBuilder:
    """
    Построитель сборок болтов

    Координирует построение компонентов и создание IFC сущностей.
    """

    def __init__(self):
        """Инициализация построителя сборок"""
        self.bolt_builder = BoltBuilder()

    def build_assembly_data(
        self,
        bolt_type: str,
        diameter: int,
        length: int,
        hook_length: int,
        bend_radius: int,
        thread_length: int,
        nut_height: float,
        washer_thickness: int
    ) -> Dict[str, Any]:
        """
        Построение данных сборки

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)
            length: Длина (мм)
            hook_length: Вылет крюка (мм)
            bend_radius: Радиус загиба (мм)
            thread_length: Длина резьбы (мм)
            nut_height: Высота гайки (мм)
            washer_thickness: Толщина шайбы (мм)

        Returns:
            Dict с данными сборки
        """
        components = self.bolt_builder.build_assembly(
            bolt_type=bolt_type,
            diameter=diameter,
            length=length,
            hook_length=hook_length,
            bend_radius=bend_radius,
            thread_length=thread_length,
            nut_height=nut_height,
            washer_thickness=washer_thickness
        )

        return {
            'components': components,
            'components_count': len(components),
            'assembly_name': f'AnchorBolt_{bolt_type}_M{diameter}x{length}',
            'stud': next(c for c in components if c.object_type == 'STUD'),
            'nuts': [c for c in components if c.object_type == 'NUT'],
            'washers': [c for c in components if c.object_type == 'WASHER']
        }
```

**Критерии приёмки:**
- [ ] BoltBuilder создан
- [ ] AssemblyBuilder создан
- [ ] Бизнес-логика отделена от IFC
- [ ] Тесты проходят

---

### 5.3. Финальная проверка фазы 5

#### 5.3.1. Запустить все тесты

```bash
pytest tests/ -v --tb=short
# Ожидаемый результат: 107 passed
```

#### 5.3.2. Проверка работы с множественными документами

```python
# test_multiple_documents.py
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
```

#### 5.3.3. Зафиксировать изменения

```bash
git add python/main.py python/core/
git commit -m "refactor(phase5): удаление Singleton и улучшение архитектуры

- IFCDocumentManager вместо Singleton
- Поддержка множественных документов
- Вынесение бизнес-логики в python/core/
- BoltBuilder и AssemblyBuilder созданы
- Фабричные функции для обратной совместимости

#refactoring #phase5"
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] Множественные документы работают
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 5

### Обязательные задачи:
- [ ] 5.1.1. Singleton удалён
- [ ] 5.1.2. IFCDocumentManager создан
- [ ] 5.1.3. Тесты проходят
- [ ] 5.2.1. Структура python/core/ создана
- [ ] 5.2.2. BoltBuilder создан
- [ ] 5.2.3. AssemblyBuilder создан
- [ ] 5.3.1. Все тесты проходят
- [ ] 5.3.2. Множественные документы работают
- [ ] 5.3.3. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Строк в main.py | ~308 | ~400 | +92 |
| Строк в core/ | 0 | ~250 | +250 |
| Singleton | 1 | 0 | -1 |
| Поддержка документов | 1 | N | +N |
| Тестов пройдено | 107 | 107 | 0 |

---

## 🚀 Следующие шаги

После завершения фазы 5:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 6**

**Ссылка на следующую фазу:** `refactoring/PHASE_6_TODO.md`

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
