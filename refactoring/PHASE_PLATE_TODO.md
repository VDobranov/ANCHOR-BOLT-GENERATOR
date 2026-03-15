# 📋 Phase: Добавление анкерной плиты для типа 2.1

**Длительность:** 1-2 дня
**Приоритет:** 🟠 Высокий
**Статус:** ⏳ Ожидает
**Зависимости:** Phase 2 (разделение gost_data.py)

---

## 📌 Обзор

Добавление нового компонента — анкерной плиты (base plate) для болтов типа 2.1.

Согласно ГОСТ 24379.1-2012, тип 2.1 (фундаментный болт с анкерной плитой) включает:
- Шпилька
- Анкерная плита
- Верхняя шайба
- 2 верхних гайки
- 2 нижних гайки

---

## 📊 Характеристики анкерных плит

| Номинальный диаметр, d | Диаметр отверстия, D | Длина/ширина плиты, B | Толщина плиты, S | Масса плиты, m (кг) |
|------------------------|---------------------|----------------------|-----------------|---------------------|
| 16 | 22 | 65 | 14 | 0,42 |
| 20 | 26 | 80 | 16 | 0,74 |
| 24 | 32 | 100 | 18 | 1,30 |
| 30 | 38 | 120 | 20 | 2,08 |
| 36 | 45 | 150 | 20 | 3,28 |
| 42 | 50 | 170 | 25 | 5,29 |
| 48 | 60 | 190 | 28 | 7,31 |

---

## 📝 Задачи

### 1. Добавление данных плит в `python/data/fastener_dimensions.py`

**Файл:** `python/data/fastener_dimensions.py`
**Длительность:** 1 час

```python
# Данные анкерных плит по ГОСТ 24379.1-2012
# Формат: диаметр: {отверстие, ширина, толщина, масса}
PLATE_DIM_DATA: Dict[int, Dict[str, Any]] = {
    16: {"hole_d": 22, "width": 65, "thickness": 14, "mass": 0.42},
    20: {"hole_d": 26, "width": 80, "thickness": 16, "mass": 0.74},
    24: {"hole_d": 32, "width": 100, "thickness": 18, "mass": 1.30},
    30: {"hole_d": 38, "width": 120, "thickness": 20, "mass": 2.08},
    36: {"hole_d": 45, "width": 150, "thickness": 20, "mass": 3.28},
    42: {"hole_d": 50, "width": 170, "thickness": 25, "mass": 5.29},
    48: {"hole_d": 60, "width": 190, "thickness": 28, "mass": 7.31},
}


def get_plate_dimensions(diameter: int) -> Optional[Dict[str, Any]]:
    """Получить размеры анкерной плиты по диаметру болта"""
    if diameter not in PLATE_DIM_DATA:
        return None
    return PLATE_DIM_DATA[diameter]
```

**Экспорт из `python/data/__init__.py`:**
```python
from .fastener_dimensions import (
    NUT_DIM_DATA,
    WASHER_DIM_DATA,
    PLATE_DIM_DATA,  # Новый экспорт
    get_nut_dimensions,
    get_washer_dimensions,
    get_plate_dimensions,  # Новая функция
)
```

---

### 2. Добавление функции валидации

**Файл:** `python/data/validation.py`
**Длительность:** 30 минут

```python
def validate_plate_diameter(diameter: int) -> bool:
    """Проверка допустимости диаметра для анкерной плиты"""
    from .fastener_dimensions import PLATE_DIM_DATA
    return diameter in PLATE_DIM_DATA
```

---

### 3. Создание геометрии плиты в `geometry_builder.py`

**Файл:** `python/geometry_builder.py`
**Длительность:** 2 часа
**Сложность:** Средняя

```python
def create_plate_solid(self, diameter: int, width: int, thickness: int, hole_diameter: int):
    """
    Создание 3D геометрии анкерной плиты
    
    Анкерная плита — квадратная пластина с круглым отверстием
    
    Args:
        diameter: Номинальный диаметр болта
        width: Длина/ширина плиты (B)
        thickness: Толщина плиты (S)
        hole_diameter: Диаметр отверстия (D)
    
    Returns:
        IfcShapeRepresentation с геометрией плиты
    """
    context = self._get_context()
    
    # Создаём квадратный профиль с отверстием
    # Квадрат от (-width/2, -width/2) до (width/2, width/2)
    half = width / 2.0
    
    # Внешний контур (квадрат)
    square_points = [
        V(-half, -half),
        V(half, -half),
        V(half, half),
        V(-half, half),
    ]
    square_curve = self.builder.polyline(square_points, closed=True)
    
    # Внутреннее отверстие (круг)
    hole_radius = hole_diameter / 2.0
    hole_circle = self.builder.circle((0.0, 0.0), hole_radius)
    
    # Профиль с отверстием
    profile = self.builder.profile(square_curve, inner_curves=[hole_circle])
    
    # Экструзия
    swept_area = self.builder.extrude(profile, magnitude=thickness)
    
    return self._create_shape_representation(context, swept_area)
```

---

### 4. Создание типа плиты в `type_factory.py`

**Файл:** `python/type_factory.py`
**Длительность:** 1 час

```python
def get_or_create_plate_type(self, diameter, material):
    """
    Создание/получение типа анкерной плиты с RepresentationMap
    
    Args:
        diameter: Диаметр болта (мм)
        material: Материал
    
    Returns:
        IfcMechanicalFastenerType для плиты
    """
    key = ("plate", diameter, material)
    if key in self.types_cache:
        return self.types_cache[key]
    
    plate_dim = get_plate_dimensions(diameter)
    if not plate_dim:
        raise ValueError(f"Анкерная плита для диаметра М{diameter} не найдена")
    
    width = plate_dim["width"]
    thickness = plate_dim["thickness"]
    hole_d = plate_dim["hole_d"]
    
    type_name = f"Plate_M{diameter}_B{width}_S{thickness}"
    ifc = get_ifcopenshell()
    
    plate_type = self.ifc.create_entity(
        "IfcMechanicalFastenerType",
        GlobalId=ifc.guid.new(),
        OwnerHistory=self.owner_history,
        Name=type_name,
        PredefinedType="USERDEFINED",
        ElementType="ANCHORPLATE",
    )
    
    # Создание геометрии
    shape_rep = self.builder.create_plate_solid(diameter, width, thickness, hole_d)
    self.builder.associate_representation(plate_type, shape_rep)
    
    # Кэширование RepresentationMap
    geom_key = ("plate", diameter)
    rep_maps = plate_type.RepresentationMaps
    if rep_maps:
        self.representation_maps[geom_key] = rep_maps[0]
    
    # Создание материала
    mat_name = get_material_name(material)
    mat = self.material_manager.create_material(
        mat_name, category="Steel", material_key=material
    )
    self.material_manager.associate_material(plate_type, mat)
    
    self.types_cache[key] = plate_type
    return plate_type
```

---

### 5. Обновление состава сборки для типа 2.1 в `instance_factory.py`

**Файл:** `python/instance_factory.py`
**Длительность:** 2 часа
**Сложность:** Высокая

#### 5.1. Обновление флага наличия плиты

```python
# Автоматическое определение состава сборки по типу болта
has_top_washer = True
has_top_nut1 = True
has_top_nut2 = True
has_bottom_nut = bolt_type == "2.1"
has_bottom_nut2 = bolt_type == "2.1"
has_plate = bolt_type == "2.1"  # Новый флаг
```

#### 5.2. Получение типа плиты

```python
stud_type = self.type_factory.get_or_create_stud_type(bolt_type, diameter, length, material)
nut_type = self.type_factory.get_or_create_nut_type(diameter, material)
washer_type = self.type_factory.get_or_create_washer_type(diameter, material)
assembly_type = self.type_factory.get_or_create_assembly_type(bolt_type, diameter, material)

# Получение типа плиты (только для типа 2.1)
plate_type = None
if has_plate:
    plate_type = self.type_factory.get_or_create_plate_type(diameter, material)
```

#### 5.3. Позиционирование компонентов для типа 2.1

**Важно:** Анкерная плита размещается **между двумя нижними гайками**.

Порядок компонентов снизу вверх:
1. Нижняя гайка 2 (самая нижняя, Z = 0)
2. **Анкерная плита** (Z = толщина нижней гайки)
3. Нижняя гайка 1 (Z = толщина нижней гайки + толщина плиты)
4. ... далее шпилька и верхние компоненты

```python
# Получение размеров нижней гайки для расчёта позиций
nut_dim = get_nut_dimensions(diameter)
nut_height = nut_dim["height"] if nut_dim else 10
plate_thickness = plate_dim["thickness"] if has_plate else 0

# Позиции для типа 2.1 (снизу вверх):
# Z=0: Нижняя гайка 2
# Z=nut_height: Анкерная плита
# Z=nut_height + plate_thickness: Нижняя гайка 1
# Z=nut_height + plate_thickness + nut_height: Шпилька (начало)
```

#### 5.4. Создание экземпляра плиты

```python
# Анкерная плита (только для типа 2.1)
# Размещается между двумя нижними гайками
if has_plate and plate_type:
    # Позиция плиты: над нижней гайкой 2
    plate_z = nut_height  # Начинается сразу над нижней гайкой
    plate_placement = self._create_placement((0, 0, plate_z))
    plate = self.ifc.create_entity(
        "IfcMechanicalFastener",
        GlobalId=ifc.guid.new(),
        OwnerHistory=owner_history,
        Name=f"Plate_M{diameter}",
        ObjectType="ANCHORPLATE",
        ObjectPlacement=plate_placement,
    )
    self._add_instance_representation(plate, plate_type)
    components.append(plate)
```

#### 5.5. Обновление позиций нижних гаек

```python
# Нижняя гайка 2 (самая нижняя, Z=0)
if has_bottom_nut:
    nut_bottom2 = self._create_component(
        "Nut",
        f"Nut_Bottom2_M{diameter}",
        "NUT",
        (0, 0, nut_height / 2),  # Центр гайки на Z = nut_height/2
        nut_type,
        nut_instances,
        owner_history,
    )
    components.append(nut_bottom2)

# Нижняя гайка 1 (над плитой)
if has_bottom_nut:
    z_pos = nut_height + plate_thickness + nut_height / 2
    nut_bottom1 = self._create_component(
        "Nut",
        f"Nut_Bottom1_M{diameter}",
        "NUT",
        (0, 0, z_pos),
        nut_type,
        nut_instances,
        owner_history,
    )
    components.append(nut_bottom1)
```

#### 5.6. Обновление смещения шпильки

```python
# Шпилька
stud_offset = 0.0
if has_plate:
    # Для типа 2.1 шпилька начинается над плитой и нижней гайкой 1
    # Z = толщина нижней гайки + толщина плиты + толщина нижней гайки
    stud_offset = nut_height + plate_thickness + nut_height
elif bolt_type == "1.1":
    from gost_data import get_thread_length
    stud_offset = get_thread_length(diameter, length) or 0
elif bolt_type == "1.2":
    from gost_data import get_thread_length
    stud_offset = get_thread_length(diameter, length) or 0
```

#### 5.5. Обновление отношений

```python
# IfcRelDefinesByType для плиты
if plate_type and 'plate' in locals():
    self.ifc.create_entity(
        "IfcRelDefinesByType",
        GlobalId=ifc.guid.new(),
        OwnerHistory=owner_history,
        RelatingType=plate_type,
        RelatedObjects=[plate],
    )
```

---

### 6. Обновление mesh данных

**Файл:** `python/instance_factory.py`
**Длительность:** 30 минут

```python
color_map = {
    "STUD": 0x8B8B8B,
    "WASHER": 0xA9A9A9,
    "NUT": 0x696969,
    "ANCHORBOLT": 0x4F4F4F,
    "ANCHORPLATE": 0x5A5A5A,  # Новый цвет для плиты
}
```

---

### 7. Обновление документации

**Файлы:** `README.md`, `FULL_PROJECT_ANALYSIS.md`
**Длительность:** 30 минут

#### README.md

```markdown
### Типы и размеры

| Тип и исполнение | Диаметры | Длины | Состав сборки |
|-----------------|----------|-------|---------------|
| 2.1 | М16–М48 | 200–2800 | Шпилька + **анкерная плита** + шайба + 4 гайки |
```

#### FULL_PROJECT_ANALYSIS.md

Добавить описание анкерной плиты в раздел "Поддерживаемые типы болтов".

---

### 8. Тесты

**Файл:** `tests/test_type_factory.py`
**Длительность:** 1 час

```python
class TestGetOrCreatePlateType:
    """Тесты для get_or_create_plate_type"""
    
    def test_get_or_create_plate_type_creates_entity(self, mock_ifc_doc):
        """Создание типа плиты"""
        from type_factory import TypeFactory
        
        factory = TypeFactory(mock_ifc_doc)
        plate_type = factory.get_or_create_plate_type(20, "09Г2С")
        
        assert plate_type is not None
        assert plate_type.Name == "Plate_M20_B80_S16"
        assert plate_type.ElementType == "ANCHORPLATE"
    
    def test_get_or_create_plate_type_caching(self, mock_ifc_doc):
        """Кэширование типа плиты"""
        from type_factory import TypeFactory
        
        factory = TypeFactory(mock_ifc_doc)
        plate1 = factory.get_or_create_plate_type(20, "09Г2С")
        plate2 = factory.get_or_create_plate_type(20, "09Г2С")
        
        assert plate1 is plate2
    
    def test_get_or_create_plate_type_invalid_diameter(self, mock_ifc_doc):
        """Ошибка для недопустимого диаметра"""
        from type_factory import TypeFactory
        
        factory = TypeFactory(mock_ifc_doc)
        
        with pytest.raises(ValueError, match="Анкерная плита для диаметра М12 не найдена"):
            factory.get_or_create_plate_type(12, "09Г2С")
```

**Файл:** `tests/test_instance_factory.py`
**Длительность:** 1 час

```python
class TestCreateBoltAssemblyType21:
    """Тесты для сборки типа 2.1"""
    
    def test_create_bolt_assembly_type_2_1_has_plate(self, mock_ifc_doc):
        """Тип 2.1 включает анкерную плиту"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")
        
        # Проверка наличия плиты в компонентах
        plate_components = [
            c for c in result["components"] 
            if hasattr(c, "ObjectType") and c.ObjectType == "ANCHORPLATE"
        ]
        assert len(plate_components) == 1
    
    def test_create_bolt_assembly_type_2_1_plate_position(self, mock_ifc_doc):
        """Плита размещается между двумя нижними гайками"""
        from instance_factory import InstanceFactory
        from data.fastener_dimensions import get_nut_dimensions

        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")

        # Получить размеры гайки для расчёта ожидаемой позиции
        nut_dim = get_nut_dimensions(20)
        nut_height = nut_dim["height"]

        # Найти плиту и нижние гайки
        plate = next(
            c for c in result["components"]
            if hasattr(c, "ObjectType") and c.ObjectType == "ANCHORPLATE"
        )
        nut_bottom2 = next(
            c for c in result["components"]
            if hasattr(c, "Name") and c.Name == "Nut_Bottom2_M20"
        )
        nut_bottom1 = next(
            c for c in result["components"]
            if hasattr(c, "Name") and c.Name == "Nut_Bottom1_M20"
        )

        # Проверка позиций через ObjectPlacement
        # Нижняя гайка 2: Z = nut_height / 2 (центр)
        # Плита: Z = nut_height (начало над нижней гайкой 2)
        # Нижняя гайка 1: Z = nut_height + plate_thickness + nut_height / 2
        plate_placement = plate.ObjectPlacement
        assert plate_placement is not None
        
        # Проверка порядка компонентов
        # Плита должна быть между двумя нижними гайками
```

**Файл:** `tests/test_geometry_builder.py`
**Длительность:** 30 минут

```python
class TestCreatePlateSolid:
    """Тесты для create_plate_solid"""
    
    def test_create_plate_solid_creates_geometry(self, mock_ifc_doc):
        """Создание геометрии плиты"""
        from geometry_builder import GeometryBuilder
        
        builder = GeometryBuilder(mock_ifc_doc)
        shape_rep = builder.create_plate_solid(20, 80, 16, 26)
        
        assert shape_rep is not None
        assert hasattr(shape_rep, "Items")
        assert len(shape_rep.Items) > 0
```

---

## ✅ Чек-лист завершения

- [ ] Данные плит добавлены в `python/data/fastener_dimensions.py`
- [ ] Функция `get_plate_dimensions()` экспортируется из `python/data/__init__.py`
- [ ] Геометрия плиты реализована в `geometry_builder.py`
- [ ] Тип плиты создан в `type_factory.py`
- [ ] Сборка типа 2.1 обновлена в `instance_factory.py`
- [ ] Mesh данные обновлены
- [ ] Документация обновлена (README, FULL_PROJECT_ANALYSIS)
- [ ] Тесты написаны и проходят
- [ ] Pre-commit хуки проходят
- [ ] Все тесты проходят

---

## 📊 Ожидаемые изменения

### Состав сборки типа 2.1 (ОБНОВЛЁННЫЙ):

**Порядок компонентов снизу вверх:**
1. Нижняя гайка 2 (Z=0, самая нижняя)
2. **Анкерная плита** (между нижними гайками)
3. Нижняя гайка 1 (над плитой)
4. Шпилька (начинается над нижней гайкой 1)
5. Верхняя шайба
6. Верхняя гайка 1
7. Верхняя гайка 2

### Итого компонентов: **7** (было 6)

### Позиции компонентов (для М20):
| Компонент | Позиция Z (мм) | Описание |
|-----------|---------------|----------|
| Нижняя гайка 2 | 0 | Основание |
| Анкерная плита | 16 | Над нижней гайкой 2 (S=16) |
| Нижняя гайка 1 | 32 | Над плитой (H=16) |
| Шпилька | 48 | Начинается над нижней гайкой 1 |
| Верхняя шайба | L-3 | У верха шпильки |
| Верхняя гайка 1 | L+13 | Над шайбой |
| Верхняя гайка 2 | L+29 | На вершине |

*Примечание: L — длина болта, H — высота гайки, S — толщина плиты*

---

## 🔗 Ссылки

- ГОСТ 24379.1-2012 "Болты фундаментные. Общие технические условия"
- [REFACTORING_PLAN_FINAL.md](../REFACTORING_PLAN_FINAL.md)
- [PHASE_2_TODO.md](./PHASE_2_TODO.md)
