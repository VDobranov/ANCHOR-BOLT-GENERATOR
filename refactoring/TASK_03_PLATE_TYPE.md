# 📋 Task 3: Создание типа плиты

**Файл:** `python/type_factory.py`  
**Длительность:** 1 час  
**Приоритет:** 🟠 Высокий  
**Статус:** ⏳ Ожидает

---

## 🎯 Цель

Создать метод `get_or_create_plate_type()` для создания/кэширования типа анкерной плиты.

---

## ✅ Чек-лист

- [ ] 3.1. Изучить существующие методы создания типов в `TypeFactory`
- [ ] 3.2. Добавить метод `get_or_create_plate_type()` в класс `TypeFactory`
- [ ] 3.3. Реализовать кэширование типов плит
- [ ] 3.4. Реализовать создание `IfcMechanicalFastenerType` для плиты
- [ ] 3.5. Реализовать ассоциацию геометрии через `create_plate_solid()`
- [ ] 3.6. Реализовать ассоциацию материала
- [ ] 3.7. Добавить тесты типа плиты
- [ ] 3.8. Запустить все тесты проекта
- [ ] 3.9. Закоммитить изменения

---

## 📝 Детали реализации

### Сигнатура метода

```python
def get_or_create_plate_type(
    self,
    diameter: int,
    material: str
) -> IfcMechanicalFastenerType:
    """
    Создание/получение типа анкерной плиты с RepresentationMap
    
    Args:
        diameter: Номинальный диаметр болта (мм)
        material: Материал (код, например "09Г2С")
    
    Returns:
        IfcMechanicalFastenerType для плиты
    """
```

### Алгоритм

1. Проверить кэш типов по ключу `("plate", diameter, material)`
2. Получить размеры плиты из `get_plate_dimensions(diameter)`
3. Создать имя типа: `Plate_M{diameter}_B{width}_S{thickness}`
4. Создать `IfcMechanicalFastenerType`:
   - `Name`: имя типа
   - `PredefinedType`: `"USERDEFINED"`
   - `ElementType`: `"ANCHORPLATE"`
5. Создать геометрию через `create_plate_solid()`
6. Ассоциировать представление с типом
7. Создать/получить материал и ассоциировать с типом
8. Сохранить в кэш и вернуть

---

## 📝 Пример кода

```python
def get_or_create_plate_type(
    self,
    diameter: int,
    material: str
) -> IfcMechanicalFastenerType:
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

## 🧪 Тесты для проверки

### TestGetOrCreatePlateType

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

---

## 🔗 Ссылки

- [PHASE_PLATE_TODO.md](./PHASE_PLATE_TODO.md#3-создание-типа-плиты-в-type_factorypy)
- [TASK_02_PLATE_GEOMETRY.md](./TASK_02_PLATE_GEOMETRY.md) — предыдущая задача
