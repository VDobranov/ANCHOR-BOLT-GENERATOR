# 📋 Task 2: Создание геометрии плиты

**Файл:** `python/geometry_builder.py`  
**Длительность:** 2 часа  
**Приоритет:** 🟠 Высокий  
**Статус:** ⏳ Ожидает

---

## 🎯 Цель

Создать метод `create_plate_solid()` для генерации 3D геометрии анкерной плиты.

---

## ✅ Чек-лист

- [ ] 2.1. Изучить существующие методы создания геометрии в `GeometryBuilder`
- [ ] 2.2. Добавить метод `create_plate_solid()` в класс `GeometryBuilder`
- [ ] 2.3. Реализовать создание квадратного профиля с круглым отверстием
- [ ] 2.4. Реализовать экструзию профиля
- [ ] 2.5. Добавить тесты геометрии плиты
- [ ] 2.6. Запустить все тесты проекта
- [ ] 2.7. Закоммитить изменения

---

## 📝 Детали реализации

### Геометрия плиты

Анкерная плита — квадратная пластина с круглым отверстием в центре:
- **Внешний контур:** квадрат от (-B/2, -B/2) до (B/2, B/2)
- **Внутреннее отверстие:** круг диаметром D в центре (0, 0)
- **Экструзия:** вдоль оси Z на толщину S

### Сигнатура метода

```python
def create_plate_solid(
    self,
    diameter: int,
    width: int,
    thickness: int,
    hole_diameter: int
) -> IfcShapeRepresentation:
    """
    Создание 3D геометрии анкерной плиты
    
    Args:
        diameter: Номинальный диаметр болта
        width: Длина/ширина плиты (B)
        thickness: Толщина плиты (S)
        hole_diameter: Диаметр отверстия (D)
    
    Returns:
        IfcShapeRepresentation с геометрией плиты
    """
```

### Алгоритм

1. Получить контекст представления
2. Создать внешний контур (квадрат):
   - Точки: (-B/2, -B/2) → (B/2, -B/2) → (B/2, B/2) → (-B/2, B/2)
   - Замкнуть контур
3. Создать внутреннее отверстие (круг):
   - Центр: (0, 0)
   - Радиус: D/2
4. Создать профиль с отверстием
5. Выполнить экструзию вдоль Z на толщину S
6. Вернуть представление формы

---

## 📝 Пример кода

```python
def create_plate_solid(
    self,
    diameter: int,
    width: int,
    thickness: int,
    hole_diameter: int
) -> IfcShapeRepresentation:
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

## 🧪 Тесты для проверки

- Создание плиты М20: width=80, thickness=16, hole_diameter=26
- Проверка наличия представления формы
- Проверка количества элементов геометрии
- Визуальная проверка в IFC viewer (опционально)

---

## 🔗 Ссылки

- [PHASE_PLATE_TODO.md](./PHASE_PLATE_TODO.md#2-создание-геометрии-плиты-в-geometry_builderpy)
- [TASK_01_PLATE_DATA.md](./TASK_01_PLATE_DATA.md) — предыдущая задача
