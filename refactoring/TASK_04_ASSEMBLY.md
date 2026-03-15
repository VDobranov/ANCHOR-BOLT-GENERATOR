# 📋 Task 4: Обновление сборки типа 2.1

**Файл:** `python/instance_factory.py`  
**Длительность:** 2 часа  
**Приоритет:** 🔴 Критичный  
**Статус:** ⏳ Ожидает

---

## 🎯 Цель

Обновить сборку типа 2.1: добавить анкерную плиту между двумя нижними гайками.

---

## ✅ Чек-лист

- [ ] 4.1. Изучить текущую реализацию `create_bolt_assembly()` для типа 2.1
- [ ] 4.2. Добавить флаг `has_plate = bolt_type == "2.1"`
- [ ] 4.3. Добавить получение типа плиты через `get_or_create_plate_type()`
- [ ] 4.4. Рассчитать позиции компонентов (шпилька, гайки, плита)
- [ ] 4.5. Создать нижнюю гайку 2 (самая нижняя)
- [ ] 4.6. Создать анкерную плиту (между гайками)
- [ ] 4.7. Создать нижнюю гайку 1 (над плитой)
- [ ] 4.8. Создать шпильку (Z=0 на начале резьбы)
- [ ] 4.9. Создать верхние компоненты (шайба, гайки)
- [ ] 4.10. Добавить тесты сборки типа 2.1
- [ ] 4.11. Запустить все тесты проекта
- [ ] 4.12. Закоммитить изменения

---

## 📊 Схема сборки типа 2.1

```
  ↑ Z
  │
  │    ┌─────────────────┐
l0│    │═════════════════│ ← Верх шпильки (конец резьбы, Z=+l0)
  │    │                 │
0 │    ├─────────────────┤ ← Z=0: Начало резьбы (реперная точка)
  │    │                 │
  │    │    Шпилька      │
  │    │                 │
  │    ├─────────────────┤ ← Z = -L + l0: Низ шпильки
  │    ├─────────────────┤ ← Z = -L + l0 + H/2: Центр нижней гайки 1
  │    │  Нижняя гайка 1  │
  │    ├═════════════════┤ ← Z = -L + l0: Верх плиты
  │    │  Анкерная плита  │ ← Толщина S
  │    ├═════════════════┤ ← Z = -L + l0 - S: Низ плиты / Верх нижней гайки 2
  │    │  Нижняя гайка 2  │
  │    └─────────────────┘ ← Z = -L + l0 - S - H/2: Центр нижней гайки 2
```

**Обозначения:**
- L — полная длина болта
- l0 — длина резьбы
- H — высота гайки
- S — толщина плиты

---

## 📝 Детали реализации

### Позиции компонентов

```python
# Получение размеров компонентов
nut_dim = get_nut_dimensions(diameter)
nut_height = nut_dim["height"] if nut_dim else 10
washer_dim = get_washer_dimensions(diameter)
washer_thickness = washer_dim["thickness"] if washer_dim else 3
plate_dim = get_plate_dimensions(diameter)
plate_thickness = plate_dim["thickness"] if has_plate else 0

# Получаем длину резьбы для позиционирования
from gost_data import get_thread_length
l0 = get_thread_length(diameter, length) or length

# Базовая позиция (низ шпильки)
bottom_z = -length + l0  # Z = -L + l0

# Позиции для типа 2.1 (снизу вверх):
nut2_center_z = bottom_z - nut_height / 2  # Центр нижней гайки 2
plate_bottom_z = bottom_z - nut_height  # Низ плиты
plate_center_z = plate_bottom_z + plate_thickness / 2  # Центр плиты
nut1_bottom_z = plate_bottom_z + plate_thickness  # Низ нижней гайки 1
nut1_center_z = nut1_bottom_z + nut_height / 2  # Центр нижней гайки 1
```

### Код создания компонентов

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

# Шпилька (без дополнительного смещения, т.к. геометрия уже с Z=0)
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

## 🧪 Тесты для проверки

### TestType21Assembly

```python
class TestType21Assembly:
    """Тесты для сборки типа 2.1"""
    
    def test_type_2_1_has_plate(self, mock_ifc_doc):
        """Тип 2.1 включает анкерную плиту"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")
        
        # Проверка наличия плиты
        plate_components = [
            c for c in result["components"]
            if hasattr(c, "ObjectType") and c.ObjectType == "ANCHORPLATE"
        ]
        assert len(plate_components) == 1
    
    def test_type_2_1_plate_between_nuts(self, mock_ifc_doc):
        """Плита между двумя нижними гайками"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")
        
        # Найти компоненты
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

## 🔗 Ссылки

- [PHASE_PLATE_TODO.md](./PHASE_PLATE_TODO.md#4-обновление-состава-сборки-для-типа-21-в-instance_factorypy)
- [TASK_03_PLATE_TYPE.md](./TASK_03_PLATE_TYPE.md) — предыдущая задача
