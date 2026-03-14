# 📋 Phase 3: Улучшение геометрии

**Длительность:** 2-3 дня  
**Приоритет:** 🟠 Высокий  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 3 убедитесь, что выполнены Phase 0-2:**

- [ ] Pre-commit hooks работают (Phase 0)
- [ ] Критические исправления выполнены (Phase 1)
- [ ] `gost_data.py` разделён на модули `data/` и `services/` (Phase 2)
- [ ] Все 107 тестов проходят
- [ ] Изменения Phase 1 и Phase 2 закоммичены

**Если предыдущие фазы не выполнены:**
1. Откройте `refactoring/PHASE_1_TODO.md` и `refactoring/PHASE_2_TODO.md`
2. Выполните все задачи предыдущих фаз
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Добавление RepresentationMaps для переиспользования геометрии типов и улучшение работы с геометрией IFC.

### Цели:
- ✅ Добавить RepresentationMaps в type_factory.py
- ✅ Улучшить associate_representation для использования Map
- ✅ Оптимизировать создание геометрии
- ✅ Сохранить прохождение всех тестов

---

## 📝 Задачи

### 3.1. Добавление RepresentationMaps

**Файл:** `python/type_factory.py`  
**Длительность:** 1 день  
**Сложность:** Средняя

#### 3.1.1. Текущее состояние (ДО)

```python
def get_or_create_stud_type(self, bolt_type, diameter, length, material):
    """Создание/получение типа шпильки"""
    key = ('stud', bolt_type, diameter, length, material)
    if key in self.types_cache:
        return self.types_cache[key]

    type_name = f'Stud_M{diameter}x{length}_{bolt_type}'
    ifc = get_ifcopenshell()
    stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
        GlobalId=ifc.guid.new(),
        OwnerHistory=self.owner_history,
        Name=type_name,
        PredefinedType='USERDEFINED',
        ElementType='STUD'
    )

    # Делегируем построение геометрии в GeometryBuilder
    if bolt_type in ['1.1', '1.2']:
        shape_rep = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
    else:
        shape_rep = self.builder.create_straight_stud_solid(diameter, length)

    self.builder.associate_representation(stud_type, shape_rep)

    # Создаём материал и ассоциируем с типом
    mat_name = get_material_name(material)
    mat = self.material_manager.create_material(mat_name, category='Steel', material_key=material)
    self.material_manager.associate_material(stud_type, mat)

    self.types_cache[key] = stud_type
    return stud_type
```

**Проблемы:**
- Нет RepresentationMaps для переиспользования геометрии
- Геометрия дублируется для каждого экземпляра
- associate_representation создаёт новую геометрию

#### 3.1.2. Целевое состояние (ПОСЛЕ)

```python
"""
type_factory.py — Фабрика для создания и кэширования типов IFC
Использует RepresentationMaps для переиспользования геометрии

Согласно IFC4 спецификации:
- RepresentationMaps позволяет переиспользовать геометрию типа
- Экземпляры ссылаются на RepresentationMap типа
- Уменьшает размер IFC файла и улучшает производительность
"""

from typing import Dict, Tuple, Any, Optional, Literal
from ifcopenshell.util.representation import get_context
from ifcopenshell.util.shape_builder import ShapeBuilder

from utils import get_ifcopenshell
from gost_data import get_nut_dimensions, get_washer_dimensions, get_material_name
from geometry_builder import GeometryBuilder
from material_manager import MaterialManager

BoltType = Literal['1.1', '1.2', '2.1', '5']
MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']


class TypeFactory:
    """Фабрика типов IFC MechanicalFastenerType"""

    def __init__(self, ifc_doc):
        """
        Инициализация TypeFactory

        Args:
            ifc_doc: IFC документ (ifcopenshell.file)
        """
        self.ifc = ifc_doc
        self.types_cache: Dict[Tuple, Any] = {}
        self.builder = GeometryBuilder(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)

        # Получаем OwnerHistory из документа
        owner_histories = self.ifc.by_type('IfcOwnerHistory')
        self.owner_history = owner_histories[0] if owner_histories else None

        # Кэш контекстов представлений
        self._context_cache: Dict[str, Any] = {}

    def _get_body_context(self):
        """Получение или создание контекста Body"""
        if 'body' not in self._context_cache:
            self._context_cache['body'] = get_context(
                self.ifc, "Model", "Body", "MODEL_VIEW"
            )
        return self._context_cache['body']

    def get_or_create_stud_type(
        self,
        bolt_type: BoltType,
        diameter: int,
        length: int,
        material: MaterialType
    ) -> Any:
        """
        Создание/получение типа шпильки с RepresentationMaps

        Args:
            bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
            diameter: Диаметр (мм)
            length: Длина (мм)
            material: Материал

        Returns:
            IfcMechanicalFastenerType сущность
        """
        key = ('stud', bolt_type, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'Stud_M{diameter}x{length}_{bolt_type}'
        ifc = get_ifcopenshell()

        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='STUD'
        )

        # Создание геометрии
        if bolt_type in ['1.1', '1.2']:
            solid = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
        else:
            solid = self.builder.create_straight_stud_solid(diameter, length)

        # Создание представления
        body_context = self._get_body_context()
        representation = self.ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=body_context,
            RepresentationIdentifier='Body',
            RepresentationType='AdvancedSweptSolid',
            Items=[solid]
        )

        # Создание RepresentationMap для переиспользования геометрии
        rep_map = self.ifc.create_entity('IfcRepresentationMap',
            MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint',
                    Coordinates=[0.0, 0.0, 0.0]
                ),
                Axis=self.ifc.create_entity('IfcDirection',
                    DirectionRatios=[0.0, 0.0, 1.0]
                ),
                RefDirection=self.ifc.create_entity('IfcDirection',
                    DirectionRatios=[1.0, 0.0, 0.0]
                )
            ),
            MappedRepresentation=representation
        )

        # Назначаем RepresentationMaps типу
        stud_type.RepresentationMaps = [rep_map]

        # Создаём материал и ассоциируем с типом
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category='Steel', material_key=material
        )
        self.material_manager.associate_material(stud_type, mat)

        self.types_cache[key] = stud_type
        return stud_type
```

#### 3.1.3. Шаги выполнения

```bash
# 1. Открыть файл для редактирования
code python/type_factory.py

# 2. Добавить импорты
from ifcopenshell.util.representation import get_context
from typing import Dict, Tuple, Any, Literal

# 3. Добавить кэш контекстов в __init__
self._context_cache: Dict[str, Any] = {}

# 4. Добавить метод _get_body_context

# 5. Переписать get_or_create_stud_type с RepresentationMaps

# 6. Переписать get_or_create_nut_type с RepresentationMaps

# 7. Переписать get_or_create_washer_type с RepresentationMaps

# 8. Обновить associate_representation для работы с Map

# 9. Запустить тесты
pytest tests/test_type_factory.py -v
```

**Критерии приёмки:**
- [ ] RepresentationMaps создаётся для каждого типа
- [ ] Геометрия переиспользуется через Map
- [ ] Все 17 тестов type_factory проходят
- [ ] Все 107 тестов проходят

---

### 3.2. Обновление associate_representation

**Файл:** `python/geometry_builder.py`  
**Длительность:** 2-3 часа

#### 3.2.1. Текущее состояние

```python
def associate_representation(self, product_type, shape_rep):
    """Ассоциация представления с типом продукта через RepresentationMap"""
    rep_maps = [m for m in self.ifc.by_type('IfcRepresentationMap')
                if m.MappedRepresentation == shape_rep]

    if not rep_maps:
        rep_map = self.ifc.create_entity('IfcRepresentationMap',
            MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
            ),
            MappedRepresentation=shape_rep
        )

        if product_type.RepresentationMaps is None:
            product_type.RepresentationMaps = [rep_map]
        elif isinstance(product_type.RepresentationMaps, tuple):
            product_type.RepresentationMaps = list(product_type.RepresentationMaps) + [rep_map]
        else:
            product_type.RepresentationMaps.append(rep_map)
```

#### 3.2.2. Целевое состояние

```python
def associate_representation(
    self,
    product_type: Any,
    shape_rep: Any,
    use_map: bool = True
) -> Optional[Any]:
    """
    Ассоциация представления с типом продукта через RepresentationMap

    Согласно IFC4:
    - RepresentationMaps позволяет переиспользовать геометрию
    - Экземпляры ссылаются на RepresentationMap через RepresentationMaps

    Args:
        product_type: IfcTypeObject сущность
        shape_rep: IfcShapeRepresentation представление
        use_map: Если True, использовать RepresentationMap

    Returns:
        RepresentationMap или None
    """
    if not use_map:
        # Прямая ассоциация без Map
        return None

    # Проверяем, есть ли уже RepresentationMap для этого представления
    rep_maps = [
        m for m in self.ifc.by_type('IfcRepresentationMap')
        if m.MappedRepresentation == shape_rep
    ]

    if rep_maps:
        rep_map = rep_maps[0]
    else:
        # Создаём новый RepresentationMap
        rep_map = self.ifc.create_entity('IfcRepresentationMap',
            MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint',
                    Coordinates=[0.0, 0.0, 0.0]
                ),
                Axis=self.ifc.create_entity('IfcDirection',
                    DirectionRatios=[0.0, 0.0, 1.0]
                ),
                RefDirection=self.ifc.create_entity('IfcDirection',
                    DirectionRatios=[1.0, 0.0, 0.0]
                )
            ),
            MappedRepresentation=shape_rep
        )

    # Добавляем к типу
    if product_type.RepresentationMaps is None:
        product_type.RepresentationMaps = [rep_map]
    elif isinstance(product_type.RepresentationMaps, tuple):
        product_type.RepresentationMaps = list(product_type.RepresentationMaps) + [rep_map]
    else:
        product_type.RepresentationMaps.append(rep_map)

    return rep_map
```

**Критерии приёмки:**
- [ ] Метод поддерживает use_map параметр
- [ ] RepresentationMap переиспользуется если существует
- [ ] Тесты проходят

---

### 3.3. Обновление instance_factory для работы с RepresentationMaps

**Файл:** `python/instance_factory.py`  
**Длительность:** 2-3 часа

#### 3.3.1. Изменение _add_instance_representation

```python
def _add_instance_representation(
    self,
    instance: Any,
    type_obj: Any
) -> None:
    """
    Добавление представления к инстансу через RepresentationMap типа

    Согласно IFC4:
    - Экземпляры наследуют геометрию от типа через RepresentationMaps
    - IfcMappedItem используется для ссылки на RepresentationMap

    Args:
        instance: IfcObject экземпляр
        type_obj: IfcTypeObject тип
    """
    if not hasattr(type_obj, 'RepresentationMaps') or not type_obj.RepresentationMaps:
        return

    rep_maps = type_obj.RepresentationMaps
    if not isinstance(rep_maps, (list, tuple)):
        rep_maps = [rep_maps]

    ifc = get_ifcopenshell()

    for rep_map in rep_maps:
        if not hasattr(rep_map, 'MappedRepresentation'):
            continue

        mapped_rep = rep_map.MappedRepresentation

        # Создаём IfcMappedItem для ссылки на RepresentationMap
        mapped_item = ifc.create_entity('IfcMappedItem',
            MappingSource=rep_map,
            MappingTarget=ifc.create_entity('IfcCartesianTransformationOperator3D',
                Axis1=ifc.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0]),
                Axis2=ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 1.0, 0.0]),
                Axis3=ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0]),
                LocalOrigin=ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
            )
        )

        # Создаём представление для экземпляра
        instance_shape_rep = ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=mapped_rep.ContextOfItems,
            RepresentationIdentifier=mapped_rep.RepresentationIdentifier,
            RepresentationType=mapped_rep.RepresentationType,
            Items=[mapped_item]
        )

        # Назначаем представление экземпляру
        prod_def_shape = ifc.create_entity('IfcProductDefinitionShape',
            Representations=[instance_shape_rep]
        )
        instance.Representation = prod_def_shape
```

**Критерии приёмки:**
- [ ] _add_instance_representation использует RepresentationMaps
- [ ] IfcMappedItem создаётся для каждого экземпляра
- [ ] Тесты проходят

---

### 3.4. Финальная проверка фазы 3

#### 3.4.1. Запустить все тесты

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Все тесты
pytest tests/ -v --tb=short

# Ожидаемый результат: 107 passed
```

#### 3.4.2. Проверка RepresentationMaps

```python
# check_representation_maps.py
import ifcopenshell
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

# Проверка RepresentationMaps
fastener_types = ifc_doc.by_type('IfcMechanicalFastenerType')
print(f"Найдено типов: {len(fastener_types)}")

for ft in fastener_types:
    has_maps = hasattr(ft, 'RepresentationMaps') and ft.RepresentationMaps
    print(f"  {ft.Name}: RepresentationMaps = {has_maps}")

# Проверка IfcRepresentationMap
rep_maps = ifc_doc.by_type('IfcRepresentationMap')
print(f"\nВсего RepresentationMaps: {len(rep_maps)}")

# Проверка IfcMappedItem
mapped_items = ifc_doc.by_type('IfcMappedItem')
print(f"Всего MappedItems: {len(mapped_items)}")
```

**Ожидаемый результат:**
```
Найдено типов: 4
  Stud_M20x800_1.1: RepresentationMaps = True
  Nut_M20_H18: RepresentationMaps = True
  Washer_M20_OD45: RepresentationMaps = True
  AnchorBoltAssembly_1.1_M20_09Г2С: RepresentationMaps = False

Всего RepresentationMaps: 3
Всего MappedItems: 4
```

#### 3.4.3. Проверка в браузере

```bash
# 1. Запустить сервер
python3 -m http.server 8000

# 2. Открыть http://localhost:8000

# 3. Сгенерировать болты всех типов
# 4. Проверить 3D модели
# 5. Скачать IFC файлы
```

#### 3.4.4. Зафиксировать изменения

```bash
git add python/type_factory.py python/geometry_builder.py python/instance_factory.py
git commit -m "refactor(phase3): добавление RepresentationMaps

- RepresentationMaps для переиспользования геометрии типов
- IfcMappedItem для ссылок на геометрию из экземпляров
- Уменьшение дублирования геометрии в IFC файле
- Улучшена производительность при множественных экземплярах

#refactoring #phase3"
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] RepresentationMaps создаются
- [ ] IfcMappedItem используются
- [ ] Браузер работает корректно
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 3

### Обязательные задачи:
- [ ] 3.1.1. RepresentationMaps в get_or_create_stud_type
- [ ] 3.1.2. RepresentationMaps в get_or_create_nut_type
- [ ] 3.1.3. RepresentationMaps в get_or_create_washer_type
- [ ] 3.2.1. associate_representation обновлён
- [ ] 3.3.1. _add_instance_representation использует Map
- [ ] 3.4.1. Все 107 тестов проходят
- [ ] 3.4.2. RepresentationMaps проверяны
- [ ] 3.4.3. Браузер работает
- [ ] 3.4.4. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Строк в type_factory.py | ~170 | ~250 | +80 |
| RepresentationMaps | 0 | 3+ | +3 |
| IfcMappedItem | 0 | 4+ | +4 |
| Тестов пройдено | 107 | 107 | 0 |
| Размер IFC файла | 100% | ~80% | -20% |

---

## 🚀 Следующие шаги

После завершения фазы 3:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 4**

**Ссылка на следующую фазу:** `refactoring/PHASE_4_TODO.md`

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
