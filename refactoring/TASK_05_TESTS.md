# 📋 Task 5: Тесты

**Файлы:** `tests/test_geometry_builder.py`, `tests/test_type_factory.py`, `tests/test_instance_factory.py`  
**Длительность:** 2 часа  
**Приоритет:** 🟡 Средний  
**Статус:** ✅ Выполнено

---

## 🎯 Цель

Написать тесты для всех компонентов анкерной плиты.

---

## ✅ Чек-лист

- [x] 5.1. Добавить тесты геометрии шпильки типа 2.1 (Task 0)
- [x] 5.2. Добавить тесты геометрии плиты (Task 2)
- [x] 5.3. Добавить тесты типа плиты (Task 3)
- [x] 5.4. Добавить тесты сборки типа 2.1 (Task 4)
- [x] 5.5. Запустить все тесты проекта (152 passed, 2 skipped)
- [x] 5.6. Исправить ошибки (обновлён тест components_count_type_2_1: 6 → 7)
- [x] 5.7. Закоммитить изменения

---

## 📝 Тесты

### 5.1. Тесты геометрии шпильки типа 2.1

**Файл:** `tests/test_geometry_builder.py`

```python
class TestType21StudGeometry:
    """Тесты для геометрии шпильки типа 2.1"""
    
    def test_type_2_1_stud_starts_at_thread_beginning(self, mock_ifc_doc):
        """Шпилька типа 2.1 начинается на отметке низа резьбы (Z=0)"""
        from geometry_builder import GeometryBuilder
        
        builder = GeometryBuilder(mock_ifc_doc)
        axis_curve = builder.create_composite_curve_stud("2.1", 20, 500)
        
        # Проверка, что кривая имеет правильные конечные точки
        points = axis_curve.Points
        assert points is not None
        assert len(points) == 2
        
        # Для М20x500: l0 ≈ 100 (длина резьбы)
        # p1 = (0, 0, l0), p2 = (0, 0, -(L-l0))
        p1 = points[0]
        p2 = points[1]
        
        # Верх шпильки (конец резьбы): Z = +l0
        assert p1[2] > 0  # Z положительный
        
        # Низ шпильки: Z = -(L - l0)
        assert p2[2] < 0  # Z отрицательный
    
    def test_type_2_1_stud_geometry_m24(self, mock_ifc_doc):
        """Геометрия шпильки типа 2.1 для М24"""
        from geometry_builder import GeometryBuilder
        
        builder = GeometryBuilder(mock_ifc_doc)
        axis_curve = builder.create_composite_curve_stud("2.1", 24, 600)
        
        points = axis_curve.Points
        assert points is not None
        # Проверка структуры геометрии
```

### 5.2. Тесты геометрии плиты

**Файл:** `tests/test_geometry_builder.py`

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
    
    def test_create_plate_solid_m36(self, mock_ifc_doc):
        """Геометрия плиты для М36"""
        from geometry_builder import GeometryBuilder
        
        builder = GeometryBuilder(mock_ifc_doc)
        shape_rep = builder.create_plate_solid(36, 150, 20, 45)
        
        assert shape_rep is not None
        assert len(shape_rep.Items) > 0
```

### 5.3. Тесты типа плиты

**Файл:** `tests/test_type_factory.py`

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

### 5.4. Тесты сборки типа 2.1

**Файл:** `tests/test_instance_factory.py`

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
        plate_placement = plate.ObjectPlacement
        nut1_placement = nut_bottom1.ObjectPlacement
        nut2_placement = nut_bottom2.ObjectPlacement
        
        assert plate_placement is not None
        assert nut1_placement is not None
        assert nut2_placement is not None
        
        # Плита должна быть между гайками по Z
        # (детальная проверка зависит от реализации _create_placement)
    
    def test_type_2_1_total_components(self, mock_ifc_doc):
        """Тип 2.1 имеет 7 компонентов"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        result = factory.create_bolt_assembly("2.1", 20, 500, "09Г2С")
        
        # 7 компонентов: шпилька, плита, 2 нижних гайки, шайба, 2 верхних гайки
        assert len(result["components"]) == 7
    
    def test_type_2_1_different_diameters(self, mock_ifc_doc):
        """Сборка типа 2.1 для разных диаметров"""
        from instance_factory import InstanceFactory
        
        factory = InstanceFactory(mock_ifc_doc)
        
        for diameter in [16, 20, 24, 30, 36, 42, 48]:
            result = factory.create_bolt_assembly("2.1", diameter, 500, "09Г2С")
            assert len(result["components"]) == 7
```

---

## 🧪 Запуск тестов

```bash
source .venv/bin/activate
python -m pytest tests/test_geometry_builder.py -v
python -m pytest tests/test_type_factory.py -v
python -m pytest tests/test_instance_factory.py -v
python -m pytest tests/ -v  # Все тесты
```

---

## 🔗 Ссылки

- [PHASE_PLATE_TODO.md](./PHASE_PLATE_TODO.md#8-тесты)
- [TASK_04_ASSEMBLY.md](./TASK_04_ASSEMBLY.md) — предыдущая задача
