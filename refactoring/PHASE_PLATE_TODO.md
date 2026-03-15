# 📋 Phase: Добавление анкерной плиты для типа 2.1 (ИСПРАВЛЕННЫЙ ПЛАН)

**Длительность:** 1-2 дня
**Приоритет:** 🟠 Высокий
**Статус:** ⏳ Ожидает
**Зависимости:** Phase 2 (разделение gost_data.py)

---

## 📌 Обзор

Добавление нового компонента — анкерной плиты (base plate) для болтов типа 2.1.

**Ключевое изменение:** Положение шпильки типа 2.1 должно быть аналогично другим типам:
- **Z=0 на отметке низа резьбы** (начало резьбы)
- Геометрия шпильки: от Z=+l0 (верх) до Z=-(L-l0) (низ)

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

### 0. Исправление геометрии шпильки типа 2.1

**Файл:** `python/geometry_builder.py`
**Длительность:** 30 минут
**Приоритет:** 🔴 Критичный (должно быть выполнено перед остальными задачами)

#### Проблема:
Текущая геометрия типа 2.1 строится от (0, 0, length) до (0, 0, 0), что означает:
- Верх шпильки: Z = length
- Низ шпильки: Z = 0

Это **не соответствует** позиционированию типов 1.1, 1.2 и 5, где Z=0 — это начало резьбы.

#### Решение:

```python
# Тип 2.1: прямая шпилька с резьбой по всей длине
# Низ резьбы в Z=0 (аналогично типам 1.1, 1.2 и 5)
if bolt_type == "2.1":
    # Получаем длину резьбы
    l0 = get_thread_length(diameter, length) or length
    
    # Тип 2.1: прямая шпилька длиной L с резьбой l0
    # Низ резьбы в Z=0, значит:
    # - Верх шпильки (конец резьбы): Z = +l0
    # - Низ шпильки: Z = -(L - l0)
    # Общая длина: l0 + (L - l0) = L
    p1 = V(0.0, 0.0, float(l0))
    p2 = V(0.0, 0.0, float(-(length - l0)))
    
    return self.builder.polyline([p1, p2])
```

#### После изменения:
- **Z=0**: начало резьбы (реперная точка)
- **Z=+l0**: верх шпильки (конец резьбы)
- **Z=-(L-l0)**: низ шпильки

---

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

---

### 2. Создание геометрии плиты в `geometry_builder.py`

**Файл:** `python/geometry_builder.py`
**Длительность:** 2 часа

```python
def create_plate_solid(self, diameter: int, width: int, thickness: int, hole_diameter: int):
    """
    Создание 3D геометрии анкерной плиты
    
    Анкерная плита — квадратная пластина с круглым отверстием
    Центр отверстия в (0, 0), плита в плоскости XY
    
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
    
    # Экструзия вдоль оси Z
    swept_area = self.builder.extrude(profile, magnitude=thickness)
    
    return self._create_shape_representation(context, swept_area)
```

---

### 3. Создание типа плиты в `type_factory.py`

**Файл:** `python/type_factory.py`
**Длительность:** 1 час

```python
def get_or_create_plate_type(self, diameter, material):
    """Создание/получение типа анкерной плиты с RepresentationMap"""
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

### 4. Обновление состава сборки для типа 2.1

**Файл:** `python/instance_factory.py`
**Длительность:** 2 часа

#### 4.1. Позиционирование компонентов (ИСПРАВЛЕННОЕ)

**Важно:** Z=0 — это начало резьбы (реперная точка для всех типов).

Порядок компонентов типа 2.1 **снизу вверх**:

```
  ↑ Z
  │
  │    ┌─────────────────┐
l0│    │═════════════════│ ← Верх шпильки (конец резьбы)
  │    │                 │
0 │    ├─────────────────┤ ← Z=0: Начало резьбы (реперная точка)
  │    │                 │
  │    │    Шпилька      │
  │    │                 │
  │    ├─────────────────┤ ← Z = -L + l0: Низ шпильки
  │    ├─────────────────┤ ← Z = -L + H + S + H/2: Центр нижней гайки 1
  │    │  Нижняя гайка 1  │
  │    ├═════════════════┤ ← Z = -L + H + S: Верх плиты
  │    │  Анкерная плита  │ ← Толщина S
  │    ├═════════════════┤ ← Z = -L + H: Низ плиты / Верх нижней гайки 2
  │    │  Нижняя гайка 2  │
  │    └─────────────────┘ ← Z = -L + H/2: Центр нижней гайки 2
-L│                         ← Z = -L: Низ болта (условно)
```

**Обозначения:**
- L — полная длина болта
- l0 — длина резьбы
- H — высота гайки
- S — толщина плиты

#### 4.2. Код позиционирования

```python
# Получение размеров компонентов
nut_dim = get_nut_dimensions(diameter)
nut_height = nut_dim["height"] if nut_dim else 10
washer_thickness = washer_dim["thickness"] if washer_dim else 3

# Получаем длину резьбы для позиционирования шпильки
from gost_data import get_thread_length
l0 = get_thread_length(diameter, length) or length

# Для типа 2.1: позиции отсчитываются от начала резьбы (Z=0)
# L — полная длина болта

# Позиции для типа 2.1 (снизу вверх):
bottom_z = -length + l0  # Низ шпильки (Z = -L + l0)

# Нижняя гайка 2: центр на Z = bottom_z - nut_height/2
# Но для типа 2.1 нижние гайки и плита размещаются ПОД шпилькой

# Правильный расчёт:
# Шпилька занимает: от Z = -L + l0 до Z = +l0
# Нижние гайки и плита: под шпилькой

# Позиция начала нижней гайки 2 (её верх)
nut2_top_z = -length + l0  # На уровне низа шпильки

# Позиции:
nut2_center_z = nut2_top_z - nut_height / 2  # Центр нижней гайки 2
plate_bottom_z = nut2_top_z - nut_height  # Низ плиты (верх нижней гайки 2)
plate_center_z = plate_bottom_z + plate_thickness / 2  # Центр плиты
nut1_bottom_z = plate_bottom_z + plate_thickness  # Низ нижней гайки 1
nut1_center_z = nut1_bottom_z + nut_height / 2  # Центр нижней гайки 1
```

#### 4.3. Создание компонентов

```python
# Нижняя гайка 2 (самая нижняя)
if has_bottom_nut2:
    nut_bottom2 = self._create_component(
        "Nut",
        f"Nut_Bottom2_M{diameter}",
        "NUT",
        (0, 0, nut2_center_z),
        nut_type,
        nut_instances,
        owner_history,
    )
    components.append(nut_bottom2)

# Анкерная плита (между нижними гайками)
if has_plate and plate_type:
    plate_placement = self._create_placement((0, 0, plate_center_z))
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

# Нижняя гайка 1 (над плитой)
if has_bottom_nut:
    nut_bottom1 = self._create_component(
        "Nut",
        f"Nut_Bottom1_M{diameter}",
        "NUT",
        (0, 0, nut1_center_z),
        nut_type,
        nut_instances,
        owner_history,
    )
    components.append(nut_bottom1)

# Шпилька (без дополнительного смещения, т.к. геометрия уже с Z=0 на начале резьбы)
stud_placement = self._create_placement((0, 0, 0))
stud = self.ifc.create_entity(
    "IfcMechanicalFastener",
    GlobalId=ifc.guid.new(),
    OwnerHistory=owner_history,
    Name=f"Stud_M{diameter}x{length}",
    ObjectType="STUD",
    ObjectPlacement=stud_placement,
)
self._add_instance_representation(stud, stud_type)
stud_instances.append(stud)
components.append(stud)
```

---

### 5. Тесты

#### 5.1. Тест геометрии шпильки типа 2.1

**Файл:** `tests/test_geometry_builder.py`

```python
class TestType21StudGeometry:
    """Тесты для геометрии шпильки типа 2.1"""
    
    def test_type_2_1_stud_starts_at_thread_beginning(self, mock_ifc_doc):
        """Шпилька типа 2.1 начинается на отметке низа резьбы (Z=0)"""
        from geometry_builder import GeometryBuilder
        
        builder = GeometryBuilder(mock_ifc_doc)
        axis_curve = builder.create_composite_curve_stud("2.1", 20, 500)
        
        # Проверка, что кривая проходит через Z=0 (начало резьбы)
        # и имеет правильные конечные точки
        points = axis_curve.Points
        assert points is not None
        
        # Для типа 2.1: p1 = (0, 0, l0), p2 = (0, 0, -(L-l0))
        # l0 для М20x500 ≈ 100 (длина резьбы)
        # p1.z ≈ 100, p2.z ≈ -400
```

#### 5.2. Тест позиции плиты

**Файл:** `tests/test_instance_factory.py`

```python
class TestType21PlatePosition:
    """Тесты для позиции анкерной плиты в типе 2.1"""
    
    def test_plate_between_bottom_nuts(self, mock_ifc_doc):
        """Плита размещена между двумя нижними гайками"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")
        
        # Найти плиту и нижние гайки
        plate = next(c for c in result["components"] 
                     if hasattr(c, "ObjectType") and c.ObjectType == "ANCHORPLATE")
        nut_bottom1 = next(c for c in result["components"] 
                          if hasattr(c, "Name") and c.Name == "Nut_Bottom1_M20")
        nut_bottom2 = next(c for c in result["components"] 
                          if hasattr(c, "Name") and c.Name == "Nut_Bottom2_M20")
        
        # Проверка позиций через ObjectPlacement
        # Плита должна быть между гайками по Z
```

---

## ✅ Чек-лист завершения

- [ ] **Шаг 0:** Исправлена геометрия шпильки типа 2.1 (Z=0 на начале резьбы)
- [ ] Данные плит добавлены в `python/data/fastener_dimensions.py`
- [ ] Функция `get_plate_dimensions()` экспортируется
- [ ] Геометрия плиты реализована в `geometry_builder.py`
- [ ] Тип плиты создан в `type_factory.py`
- [ ] Сборка типа 2.1 обновлена в `instance_factory.py`
- [ ] Mesh данные обновлены
- [ ] Документация обновлена (README, FULL_PROJECT_ANALYSIS)
- [ ] Тесты написаны и проходят
- [ ] Pre-commit хуки проходят

---

## 📊 Итоговая схема сборки типа 2.1

| Компонент | Позиция Z (для М20x500) | Описание |
|-----------|------------------------|----------|
| Верх шпильки | +100 | Конец резьбы |
| **Z=0** | **0** | **Начало резьбы (репер)** |
| Низ шпильки | -400 | Начало нижних компонентов |
| Нижняя гайка 1 | -408 | Над плитой (H=16) |
| Анкерная плита | -424 | Между гайками (S=16) |
| Нижняя гайка 2 | -440 | Самая нижняя |

*Примечание: l0=100 для М20, L=500*
