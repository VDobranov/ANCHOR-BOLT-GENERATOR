# 📋 Task 1: Добавление данных плит

**Файл:** `python/data/fastener_dimensions.py`  
**Длительность:** 1 час  
**Приоритет:** 🟠 Высокий  
**Статус:** ⏳ Ожидает

---

## 🎯 Цель

Добавить данные анкерных плит по ГОСТ 24379.1-2012 в модуль данных.

---

## ✅ Чек-лист

- [ ] 1.1. Открыть `python/data/fastener_dimensions.py`
- [ ] 1.2. Добавить словарь `PLATE_DIM_DATA` с данными плит
- [ ] 1.3. Добавить функцию `get_plate_dimensions(diameter)`
- [ ] 1.4. Открыть `python/data/__init__.py`
- [ ] 1.5. Добавить экспорт `PLATE_DIM_DATA` и `get_plate_dimensions`
- [ ] 1.6. Запустить тесты данных (`tests/test_data/`)
- [ ] 1.7. Запустить все тесты проекта
- [ ] 1.8. Закоммитить изменения

---

## 📊 Данные плит (7 типоразмеров)

| d  | D  | B   | S  | m (кг) |
|----|----|-----|----|--------|
| 16 | 22 | 65  | 14 | 0,42   |
| 20 | 26 | 80  | 16 | 0,74   |
| 24 | 32 | 100 | 18 | 1,30   |
| 30 | 38 | 120 | 20 | 2,08   |
| 36 | 45 | 150 | 20 | 3,28   |
| 42 | 50 | 170 | 25 | 5,29   |
| 48 | 60 | 190 | 28 | 7,31   |

**Обозначения:**
- d — номинальный диаметр болта
- D — диаметр отверстия плиты
- B — длина/ширина плиты (квадратная)
- S — толщина плиты
- m — масса плиты

---

## 📝 Код для добавления

### В `python/data/fastener_dimensions.py`:

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
    """Получить размеры анкерной плиты по диаметру болта
    
    Args:
        diameter: Номинальный диаметр болта (мм)
    
    Returns:
        Dict с ключами: hole_d, width, thickness, mass
        или None, если диаметр не найден
    """
    if diameter not in PLATE_DIM_DATA:
        return None
    return PLATE_DIM_DATA[diameter]
```

### В `python/data/__init__.py`:

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

## 🧪 Тесты для проверки

- `get_plate_dimensions(20)` возвращает `{"hole_d": 26, "width": 80, "thickness": 16, "mass": 0.74}`
- `get_plate_dimensions(12)` возвращает `None` (нет в данных)
- Все существующие тесты данных проходят

---

## 🔗 Ссылки

- [PHASE_PLATE_TODO.md](./PHASE_PLATE_TODO.md#1-добавление-данных-плит-в-pythondatafastener_dimensionspy)
- [TASK_00_STUD_GEOMETRY.md](./TASK_00_STUD_GEOMETRY.md) — предыдущая задача
