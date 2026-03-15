# 📋 Phase 2: Разделение модулей

**Длительность:** 3-4 дня  
**Приоритет:** 🟠 Высокий  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Перед началом Phase 2 убедитесь, что выполнена Phase 1:**

- [ ] Workaround для shape_builder удалён
- [ ] `builder.deep_copy()` используется вместо ручного дублирования
- [ ] Экспорт через `io.StringIO()` работает
- [ ] Все 107 тестов проходят после Phase 1
- [ ] Изменения Phase 1 закоммичены

**Если Phase 1 не выполнена:**
1. Откройте `refactoring/PHASE_1_TODO.md`
2. Выполните все задачи Phase 1
3. Убедитесь, что все тесты проходят
4. Вернитесь к этому файлу

---

## 📌 Обзор фазы

Разделение большого модуля `gost_data.py` (443 строки) на несколько специализированных модулей для улучшения поддерживаемости и соблюдения Single Responsibility Principle.

### Цели:
- ✅ Создать пакет `python/data/` для данных ГОСТ
- ✅ Создать пакет `python/services/` для бизнес-логики
- ✅ Разделить `gost_data.py` на 6 специализированных модулей
- ✅ Сохранить обратную совместимость через wrapper
- ✅ Сохранить прохождение всех 107 тестов

---

## 📝 Задачи

### 2.1. Создание пакета `python/data/`

**Длительность:** 1 день  
**Сложность:** Средняя  
**Файлов:** 5

#### 2.1.1. Создать структуру директорий

```bash
# Создать директорию
mkdir -p python/data

# Создать файлы
touch python/data/__init__.py
touch python/data/bolt_dimensions.py
touch python/data/fastener_dimensions.py
touch python/data/materials.py
touch python/data/validation.py
```

#### 2.1.2. Файл `python/data/__init__.py`

```python
"""
python/data/ — Модуль данных ГОСТ для анкерных болтов

Содержит:
- BOLT_DIM_DATA: данные размеров болтов
- NUT_DIM_DATA: размеры гаек
- WASHER_DIM_DATA: размеры шайб
- MATERIALS: данные о материалах
- BOLT_TYPES, AVAILABLE_DIAMETERS, AVAILABLE_LENGTHS: константы
- validate_parameters: функция валидации
"""

from .bolt_dimensions import (
    BOLT_DIM_DATA,
    AVAILABLE_DIAMETERS,
    DIAMETER_LIMITS,
    get_bolt_dimensions
)
from .fastener_dimensions import (
    NUT_DIM_DATA,
    WASHER_DIM_DATA,
    get_nut_dimensions,
    get_washer_dimensions
)
from .materials import (
    MATERIALS,
    get_material_name
)
from .validation import (
    BOLT_TYPES,
    AVAILABLE_LENGTHS,
    MASS_INDICES,
    validate_parameters
)

__all__ = [
    # Константы
    'BOLT_TYPES',
    'AVAILABLE_DIAMETERS',
    'DIAMETER_LIMITS',
    'AVAILABLE_LENGTHS',
    'MASS_INDICES',

    # Данные
    'BOLT_DIM_DATA',
    'NUT_DIM_DATA',
    'WASHER_DIM_DATA',
    'MATERIALS',

    # Функции
    'get_bolt_dimensions',
    'get_nut_dimensions',
    'get_washer_dimensions',
    'get_material_name',
    'validate_parameters'
]
```

**Критерии приёмки:**
- [ ] Директория `python/data/` создана
- [ ] Все 5 файлов созданы
- [ ] `__init__.py` экспортирует все публичные символы

---

### 2.2. Файл `python/data/bolt_dimensions.py`

**Длительность:** 2-3 часа  
**Строк:** ~200

#### 2.2.1. Содержимое файла

```python
"""
python/data/bolt_dimensions.py — Данные размеров болтов из dim.csv

Based on ГОСТ 24379.1-2012

Формат исходных данных (dim.csv):
- Формат строки: диаметр_длина;L;l;R;d;l0;l1;l2;l3;r;Масса 1.1;Масса 1.2;Масса 2.1;Масса 5
- Индексы: 0=L, 1=l, 2=R, 3=d, 4=l0, 5=масса_1.1, 6=масса_1.2, 7=масса_2.1, 8=масса_5, 9=l1, 10=l2, 11=l3, 12=r
"""

from typing import TypedDict, Optional, Dict, List, Tuple, Literal


# =============================================================================
# Типы данных
# =============================================================================

BoltType = Literal['1.1', '1.2', '2.1', '5']


class BoltDimension(TypedDict):
    """
    Структура данных размеров болта

    Attributes:
        length: Длина болта (мм)
        hook_length: Вылет крюка (мм)
        bend_radius: Радиус загиба (мм)
        diameter: Диаметр болта (мм)
        thread_length: Длина резьбы (мм)
        mass_1_1: Масса для типа 1.1 (кг) или None
        mass_1_2: Масса для типа 1.2 (кг) или None
        mass_2_1: Масса для типа 2.1 (кг) или None
        mass_5: Масса для типа 5 (кг) или None
        l1: Длина верхнего участка (мм)
        l2: Длина вылета с отгибом (мм)
        l3: Смещение отгиба (мм)
        r: Радиус отгиба (мм)
    """
    length: int
    hook_length: int
    bend_radius: int
    diameter: int
    thread_length: int
    mass_1_1: Optional[float]
    mass_1_2: Optional[float]
    mass_2_1: Optional[float]
    mass_5: Optional[float]
    l1: int
    l2: int
    l3: int
    r: int


# =============================================================================
# Константы
# =============================================================================

# Доступные диаметры согласно ГОСТ (из dim.csv)
AVAILABLE_DIAMETERS: List[int] = [12, 16, 20, 24, 30, 36, 42, 48]

# Ограничения диаметров по типам болтов
DIAMETER_LIMITS: Dict[BoltType, Tuple[int, int]] = {
    '1.1': (12, 48),  # М12–М48
    '1.2': (12, 48),  # М12–М48
    '2.1': (16, 48),  # М16–М48
    '5': (12, 48)     # М12–М48
}

# Параметры болтов из dim.csv
# Ключ формата: "{диаметр}_{длина}"
# Значение: [длина, вылет крюка, радиус загиба, диаметр, длина резьбы,
#            масса_1.1, масса_1.2, масса_2.1, масса_5, l1, l2, l3, r]
BOLT_DIM_DATA: Dict[str, BoltDimension] = {
    # Диаметр 12 мм
    "12_150": {
        "length": 150,
        "hook_length": 40,
        "bend_radius": 12,
        "diameter": 12,
        "thread_length": 80,
        "mass_1_1": None,
        "mass_1_2": None,
        "mass_2_1": None,
        "mass_5": 0.18,
        "l1": 100,
        "l2": 50,
        "l3": 25,
        "r": 8
    },
    "12_200": {
        "length": 200,
        "hook_length": 40,
        "bend_radius": 12,
        "diameter": 12,
        "thread_length": 80,
        "mass_1_1": None,
        "mass_1_2": None,
        "mass_2_1": None,
        "mass_5": 0.27,
        "l1": 100,
        "l2": 50,
        "l3": 25,
        "r": 8
    },
    "12_250": {
        "length": 250,
        "hook_length": 40,
        "bend_radius": 12,
        "diameter": 12,
        "thread_length": 80,
        "mass_1_1": None,
        "mass_1_2": None,
        "mass_2_1": None,
        "mass_5": 0.32,
        "l1": 100,
        "l2": 50,
        "l3": 25,
        "r": 8
    },
    "12_300": {
        "length": 300,
        "hook_length": 40,
        "bend_radius": 12,
        "diameter": 12,
        "thread_length": 80,
        "mass_1_1": 0.35,
        "mass_1_2": 0.35,
        "mass_2_1": None,
        "mass_5": 0.32,
        "l1": 100,
        "l2": 50,
        "l3": 25,
        "r": 8
    },
    # ... (продолжить для всех 150+ записей из BOLT_DIM_DATA)
}


# =============================================================================
# Функции
# =============================================================================

def get_bolt_dimensions(diameter: int, length: int) -> Optional[BoltDimension]:
    """
    Получить размеры болта по диаметру и длине

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        BoltDimension с размерами или None если болт не найден

    Example:
        >>> dims = get_bolt_dimensions(20, 800)
        >>> print(dims['hook_length'])
        60
    """
    key = f"{diameter}_{length}"
    return BOLT_DIM_DATA.get(key)


def get_available_lengths_for_type(
    bolt_type: BoltType,
    diameter: int
) -> List[int]:
    """
    Получить доступные длины для типа и диаметра

    Args:
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
        diameter: Диаметр болта (мм)

    Returns:
        Отсортированный список доступных длин (мм)
    """
    from .validation import AVAILABLE_LENGTHS

    key = (bolt_type, diameter)
    return AVAILABLE_LENGTHS.get(key, [])
```

**Критерии приёмки:**
- [ ] TypedDict для BoltDimension определён
- [ ] Все константы перенесены из gost_data.py
- [ ] Все данные BOLT_DIM_DATA перенесены (150+ записей)
- [ ] Функции с type hints и docstrings
- [ ] Black форматирование применено

---

### 2.3. Файл `python/data/fastener_dimensions.py`

**Длительность:** 1-2 часа  
**Строк:** ~80

#### 2.3.1. Содержимое файла

```python
"""
python/data/fastener_dimensions.py — Данные размеров гаек и шайб

Based on ГОСТ 24379.1-2012 и связанные стандарты
"""

from typing import TypedDict, Optional, Dict


# =============================================================================
# Типы данных
# =============================================================================

class NutDimension(TypedDict):
    """
    Структура данных размеров гайки

    Attributes:
        diameter: Номинальный диаметр (мм)
        s_width: Размер под ключ (мм)
        height: Высота гайки (мм)
    """
    diameter: int
    s_width: int
    height: float


class WasherDimension(TypedDict):
    """
    Структура данных размеров шайбы

    Attributes:
        nominal_diameter: Номинальный диаметр (мм)
        inner_diameter: Внутренний диаметр (мм)
        outer_diameter: Внешний диаметр (мм)
        thickness: Толщина (мм)
    """
    nominal_diameter: int
    inner_diameter: int
    outer_diameter: int
    thickness: int


# =============================================================================
# Данные
# =============================================================================

# Параметры гаек
# Формат: "{диаметр}": [диаметр, размер под ключ, высота]
NUT_DIM_DATA: Dict[str, list] = {
    "12": [12, 18, 10.8],
    "16": [16, 24, 14.8],
    "20": [20, 30, 18.0],
    "24": [24, 36, 21.5],
    "30": [30, 46, 25.6],
    "36": [36, 55, 31.0],
    "42": [42, 65, 34.0],
    "48": [48, 75, 38.0]
}

# Параметры шайб
# Формат: "{диаметр}": [диаметр номинальный, диаметр отверстия, внешний диаметр, высота]
WASHER_DIM_DATA: Dict[str, list] = {
    "12": [12, 13, 36, 3],
    "16": [16, 17, 42, 4],
    "20": [20, 21, 45, 8],
    "24": [24, 25, 55, 8],
    "30": [30, 32, 80, 10],
    "36": [36, 38, 90, 10],
    "42": [42, 44, 95, 14],
    "48": [48, 50, 105, 14]
}


# =============================================================================
# Функции
# =============================================================================

def get_nut_dimensions(diameter: int) -> Optional[NutDimension]:
    """
    Получить размеры гайки по диаметру болта

    Args:
        diameter: Диаметр болта (мм)

    Returns:
        NutDimension с размерами или None если гайка не найдена

    Example:
        >>> nut = get_nut_dimensions(20)
        >>> print(nut['s_width'])
        30
    """
    data = NUT_DIM_DATA.get(str(diameter))
    if data:
        return NutDimension(
            diameter=data[0],
            s_width=data[1],
            height=data[2]
        )
    return None


def get_washer_dimensions(diameter: int) -> Optional[WasherDimension]:
    """
    Получить размеры шайбы по диаметру болта

    Args:
        diameter: Диаметр болта (мм)

    Returns:
        WasherDimension с размерами или None если шайба не найдена

    Example:
        >>> washer = get_washer_dimensions(20)
        >>> print(washer['outer_diameter'])
        45
    """
    data = WASHER_DIM_DATA.get(str(diameter))
    if data:
        return WasherDimension(
            nominal_diameter=data[0],
            inner_diameter=data[1],
            outer_diameter=data[2],
            thickness=data[3]
        )
    return None
```

**Критерии приёмки:**
- [ ] TypedDict для NutDimension и WasherDimension
- [ ] Данные NUT_DIM_DATA и WASHER_DIM_DATA перенесены
- [ ] Функции с type hints и docstrings

---

### 2.4. Файл `python/data/materials.py`

**Длительность:** 1 час  
**Строк:** ~80

#### 2.4.1. Содержимое файла

```python
"""
python/data/materials.py — Данные о материалах по ГОСТ

Based on:
- ГОСТ 19281-2014 (низколегированная сталь)
- ГОСТ 535-88 (углеродистая конструкционная сталь)
"""

from typing import TypedDict, Literal, Dict, Optional


# =============================================================================
# Типы данных
# =============================================================================

MaterialType = Literal['09Г2С', 'ВСт3пс2', '10Г2']


class MaterialInfo(TypedDict):
    """
    Структура данных материала

    Attributes:
        gost: Номер ГОСТ
        tensile_strength: Предел прочности (МПа)
        yield_strength: Предел текучести (МПа)
        density: Плотность (кг/м³)
        description: Описание материала
    """
    gost: str
    tensile_strength: int
    yield_strength: int
    density: int
    description: str


# =============================================================================
# Данные
# =============================================================================

MATERIALS: Dict[MaterialType, MaterialInfo] = {
    '09Г2С': {
        'gost': '19281-2014',
        'tensile_strength': 490,
        'yield_strength': 390,
        'density': 7850,
        'description': 'Низколегированная сталь'
    },
    'ВСт3пс2': {
        'gost': '535-88',
        'tensile_strength': 345,
        'yield_strength': 235,
        'density': 7850,
        'description': 'Углеродистая конструкционная сталь'
    },
    '10Г2': {
        'gost': '19281-2014',
        'tensile_strength': 490,
        'yield_strength': 390,
        'density': 7850,
        'description': 'Низколегированная сталь'
    }
}


# =============================================================================
# Функции
# =============================================================================

def get_material_name(material: MaterialType) -> str:
    """
    Форматирование имени материала для IFC

    Args:
        material: Тип материала (например, '09Г2С')

    Returns:
        Строка в формате: "09Г2С ГОСТ 19281-2014"

    Example:
        >>> get_material_name('09Г2С')
        '09Г2С ГОСТ 19281-2014'
        >>> get_material_name('ВСт3пс2')
        'ВСт3пс2 ГОСТ 535-88'
    """
    info = MATERIALS.get(material)
    if info:
        return f"{material} ГОСТ {info['gost']}"
    return material


def get_material_info(material: MaterialType) -> Optional[MaterialInfo]:
    """
    Получить полную информацию о материале

    Args:
        material: Тип материала

    Returns:
        MaterialInfo или None если материал не найден
    """
    return MATERIALS.get(material)


def get_material_density(material: MaterialType) -> Optional[int]:
    """
    Получить плотность материала

    Args:
        material: Тип материала

    Returns:
        Плотность (кг/м³) или None
    """
    info = MATERIALS.get(material)
    return info['density'] if info else None


def get_material_strength(material: MaterialType) -> tuple[Optional[int], Optional[int]]:
    """
    Получить прочностные характеристики материала

    Args:
        material: Тип материала

    Returns:
        Кортеж (yield_strength, tensile_strength) в МПа
    """
    info = MATERIALS.get(material)
    if info:
        return (info['yield_strength'], info['tensile_strength'])
    return (None, None)
```

**Критерии приёмки:**
- [ ] TypedDict для MaterialInfo
- [ ] Данные MATERIALS перенесены
- [ ] Функции с type hints и docstrings

---

### 2.5. Файл `python/data/validation.py`

**Длительность:** 2-3 часа  
**Строк:** ~150

#### 2.5.1. Содержимое файла

```python
"""
python/data/validation.py — Валидация параметров болтов по ГОСТ

Based on ГОСТ 24379.1-2012
"""

from typing import Set, Dict, List, Tuple, Literal
from .bolt_dimensions import BOLT_DIM_DATA, AVAILABLE_DIAMETERS, DIAMETER_LIMITS, BoltType
from .materials import MATERIALS, MaterialType


# =============================================================================
# Константы
# =============================================================================

# Типы болтов (допустимые значения)
BOLT_TYPES: Set[BoltType] = {'1.1', '1.2', '2.1', '5'}

# Индексы масс по типам болтов (ключи в BoltDimension)
MASS_INDICES: Dict[BoltType, str] = {
    '1.1': 'mass_1_1',
    '1.2': 'mass_1_2',
    '2.1': 'mass_2_1',
    '5': 'mass_5'
}

# Доступные длины для каждой комбинации типа и диаметра
# Генерируется автоматически из BOLT_DIM_DATA на основе наличия массы
AVAILABLE_LENGTHS: Dict[Tuple[BoltType, int], List[int]] = {}


# =============================================================================
# Инициализация AVAILABLE_LENGTHS
# =============================================================================

def _init_available_lengths():
    """Инициализация AVAILABLE_LENGTHS из BOLT_DIM_DATA"""
    for key, data in BOLT_DIM_DATA.items():
        diameter = int(key.split('_')[0])
        length = int(data['length'])

        for bolt_type in BOLT_TYPES:
            mass_key = MASS_INDICES[bolt_type]
            # Проверяем, что масса существует (не None)
            if data.get(mass_key) is not None:
                type_key = (bolt_type, diameter)
                if type_key not in AVAILABLE_LENGTHS:
                    AVAILABLE_LENGTHS[type_key] = []
                if length not in AVAILABLE_LENGTHS[type_key]:
                    AVAILABLE_LENGTHS[type_key].append(length)

    # Сортировка длин
    for type_key in AVAILABLE_LENGTHS:
        AVAILABLE_LENGTHS[type_key].sort()


# Инициализировать при импорте модуля
_init_available_lengths()


# =============================================================================
# Функции валидации
# =============================================================================

def validate_parameters(
    bolt_type: BoltType,
    diameter: int,
    length: int,
    material: MaterialType
) -> bool:
    """
    Валидация параметров болта по ГОСТ

    Проверяет:
    1. Тип болта существует
    2. Диаметр поддерживается
    3. Диаметр в диапазоне для типа
    4. Материал существует
    5. Длина доступна для комбинации тип+диаметр
    6. Масса существует для данной комбинации

    Args:
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        material: Материал болта

    Raises:
        ValueError: Если параметры не валидны (список ошибок в сообщении)

    Returns:
        True если параметры валидны

    Example:
        >>> validate_parameters('1.1', 20, 800, '09Г2С')
        True
        >>> validate_parameters('9.9', 20, 800, '09Г2С')
        ValueError: Неизвестный тип болта: 9.9
    """
    errors = []

    # Validate bolt type
    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")

    # Validate diameter
    if diameter not in AVAILABLE_DIAMETERS:
        errors.append(f"Неподдерживаемый диаметр: М{diameter}")

    # Validate diameter limits for bolt type
    if bolt_type in DIAMETER_LIMITS:
        min_d, max_d = DIAMETER_LIMITS[bolt_type]
        if diameter < min_d or diameter > max_d:
            errors.append(
                f"Диаметр М{diameter} недоступен для типа {bolt_type}. "
                f"Доступен диапазон: М{min_d}–М{max_d}"
            )

    # Validate material
    if material not in MATERIALS:
        errors.append(f"Неизвестный материал: {material}")

    # Validate length
    if bolt_type in BOLT_TYPES:
        key = (bolt_type, diameter)
        if key not in AVAILABLE_LENGTHS:
            errors.append(
                f"Комбинация типа {bolt_type} и диаметра М{diameter} не существует"
            )
        elif length not in AVAILABLE_LENGTHS[key]:
            available = AVAILABLE_LENGTHS[key]
            errors.append(
                f"Длина {length} недоступна. Доступные длины: {available}"
            )
        else:
            # Дополнительная проверка: масса для данного типа должна существовать
            dim_key = f"{diameter}_{length}"
            if dim_key in BOLT_DIM_DATA:
                mass_key = MASS_INDICES[bolt_type]
                if BOLT_DIM_DATA[dim_key].get(mass_key) is None:
                    errors.append(
                        f"Болт типа {bolt_type} с параметрами М{diameter}×{length} "
                        f"не существует (нет массы)"
                    )

    if errors:
        raise ValueError('\n'.join(errors))

    return True


def is_valid_bolt_combination(
    bolt_type: BoltType,
    diameter: int,
    length: int
) -> bool:
    """
    Проверить существование болта данной комбинации (без material)

    Args:
        bolt_type: Тип болта
        diameter: Диаметр
        length: Длина

    Returns:
        True если болт существует
    """
    try:
        validate_parameters(bolt_type, diameter, length, '09Г2С')
        return True
    except ValueError:
        return False


def get_bolt_mass(
    diameter: int,
    length: int,
    bolt_type: BoltType
) -> Optional[float]:
    """
    Получить массу болта данного диаметра, длины и типа

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        bolt_type: Тип болта

    Returns:
        Масса в кг или None, если болт такого типа не существует

    Example:
        >>> get_bolt_mass(20, 800, '1.1')
        1.32
    """
    key = f"{diameter}_{length}"
    if key not in BOLT_DIM_DATA:
        return None

    data = BOLT_DIM_DATA[key]
    mass_key = MASS_INDICES.get(bolt_type)

    if mass_key is None:
        return None

    return data.get(mass_key)
```

**Критерии приёмки:**
- [ ] AVAILABLE_LENGTHS генерируется автоматически
- [ ] validate_parameters с полной проверкой
- [ ] get_bolt_mass функция
- [ ] Type hints и docstrings

---

### 2.6. Файл `python/gost_data.py` (wrapper для обратной совместимости)

**Длительность:** 1 час  
**Строк:** ~50

#### 2.6.1. Содержимое файла

```python
"""
gost_data.py — Обратная совместимость

Все функции и данные перемещены в:
- python/data/bolt_dimensions.py
- python/data/fastener_dimensions.py
- python/data/materials.py
- python/data/validation.py

Этот файл предоставляет обратную совместимость через ре-экспорт.
"""

# Импорты для обратной совместимости
from .data.bolt_dimensions import (
    BOLT_DIM_DATA,
    AVAILABLE_DIAMETERS,
    DIAMETER_LIMITS,
    get_bolt_dimensions,
    BoltType
)
from .data.fastener_dimensions import (
    NUT_DIM_DATA,
    WASHER_DIM_DATA,
    get_nut_dimensions,
    get_washer_dimensions
)
from .data.materials import (
    MATERIALS,
    get_material_name,
    MaterialType
)
from .data.validation import (
    BOLT_TYPES,
    AVAILABLE_LENGTHS,
    MASS_INDICES,
    validate_parameters,
    get_bolt_mass
)

# Функции-геттеры (перенаправляют в data модули)
from .services.dimension_service import (
    get_bolt_hook_length,
    get_bolt_bend_radius,
    get_thread_length,
    get_bolt_l1,
    get_bolt_l2,
    get_bolt_l3
)

__all__ = [
    # Константы
    'BOLT_TYPES',
    'AVAILABLE_DIAMETERS',
    'DIAMETER_LIMITS',
    'AVAILABLE_LENGTHS',
    'MASS_INDICES',

    # Данные
    'BOLT_DIM_DATA',
    'NUT_DIM_DATA',
    'WASHER_DIM_DATA',
    'MATERIALS',

    # Типы
    'BoltType',
    'MaterialType',

    # Функции из data
    'get_bolt_dimensions',
    'get_nut_dimensions',
    'get_washer_dimensions',
    'get_material_name',
    'validate_parameters',
    'get_bolt_mass',

    # Функции из services
    'get_bolt_hook_length',
    'get_bolt_bend_radius',
    'get_thread_length',
    'get_bolt_l1',
    'get_bolt_l2',
    'get_bolt_l3'
]
```

**Критерии приёмки:**
- [ ] Все импорты работают
- [ ] Обратная совместимость сохранена
- [ ] Тесты проходят без изменений

---

### 2.7. Создание пакета `python/services/`

**Длительность:** 1 день  
**Сложность:** Средняя  
**Файлов:** 2

#### 2.7.1. Создать структуру

```bash
mkdir -p python/services
touch python/services/__init__.py
touch python/services/dimension_service.py
```

#### 2.7.2. Файл `python/services/__init__.py`

```python
"""
python/services/ — Бизнес-логика и сервисы

Содержит сервисные функции для работы с размерами болтов.
"""

from .dimension_service import (
    get_bolt_hook_length,
    get_bolt_bend_radius,
    get_thread_length,
    get_bolt_l1,
    get_bolt_l2,
    get_bolt_l3
)

__all__ = [
    'get_bolt_hook_length',
    'get_bolt_bend_radius',
    'get_thread_length',
    'get_bolt_l1',
    'get_bolt_l2',
    'get_bolt_l3'
]
```

#### 2.7.3. Файл `python/services/dimension_service.py`

```python
"""
python/services/dimension_service.py — Сервис для получения размеров болтов

Предоставляет функции для получения специфических размеров болтов
на основе данных из dim.csv.
"""

from typing import Optional, Literal
from ..data.bolt_dimensions import BOLT_DIM_DATA

BoltType = Literal['1.1', '1.2', '2.1', '5']


def get_bolt_hook_length(diameter: int, length: int) -> Optional[int]:
    """
    Получить вылет крюка для болта данного диаметра и длины

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Вылет крюка (мм) или None если болт не найден

    Example:
        >>> get_bolt_hook_length(20, 800)
        60
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['hook_length']
    return None


def get_bolt_bend_radius(diameter: int, length: int) -> int:
    """
    Получить радиус загиба для болта данного диаметра и длины

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Радиус загиба (мм), по умолчанию равен диаметру

    Example:
        >>> get_bolt_bend_radius(20, 800)
        20
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['bend_radius']
    return diameter  # По умолчанию


def get_thread_length(diameter: int, length: int) -> Optional[int]:
    """
    Получить длину резьбы для болта данного диаметра и длины

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Длина резьбы (мм) или None если болт не найден

    Example:
        >>> get_thread_length(20, 800)
        100
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['thread_length']
    return None


def get_bolt_l1(diameter: int, length: int) -> Optional[int]:
    """
    Получить l1 (длина верхнего участка) для болта

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Длина l1 (мм) или None
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l1']
    return None


def get_bolt_l2(diameter: int, length: int) -> Optional[int]:
    """
    Получить l2 (длина вылета с отгибом) для болта

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Длина l2 (мм) или None
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l2']
    return None


def get_bolt_l3(diameter: int, length: int) -> Optional[int]:
    """
    Получить l3 (смещение отгиба) для болта

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)

    Returns:
        Длина l3 (мм) или None
    """
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key]['l3']
    return None
```

**Критерии приёмки:**
- [ ] Все функции-геттеры перенесены
- [ ] Type hints и docstrings
- [ ] Импорты из data модулей

---

### 2.8. Обновление импортов во всех файлах

**Длительность:** 2-3 часа  
**Файлов:** 8

#### 2.8.1. Файлы для обновления

```bash
# Список файлов для обновления импортов
python/main.py
python/instance_factory.py
python/type_factory.py
python/geometry_builder.py
python/material_manager.py
python/geometry_converter.py
tests/test_gost_data.py
tests/test_type_factory.py
tests/test_instance_factory.py
tests/test_material_manager.py
```

#### 2.8.2. Примеры изменений

**До:**
```python
from gost_data import validate_parameters, get_nut_dimensions, get_material_name
```

**После (вариант 1 — через wrapper):**
```python
from gost_data import validate_parameters, get_nut_dimensions, get_material_name
```
(ничего не меняется благодаря wrapper)

**После (вариант 2 — прямые импорты):**
```python
from data.validation import validate_parameters
from data.fastener_dimensions import get_nut_dimensions
from data.materials import get_material_name
```

#### 2.8.3. Проверка импортов

```bash
# Проверить все импорты
python3 -c "
import sys
sys.path.insert(0, 'python')

# Проверка импортов
from gost_data import validate_parameters, get_nut_dimensions, get_material_name
from data import BOLT_DIM_DATA, MATERIALS
from services import get_bolt_hook_length

print('✓ Все импорты работают')
"
```

**Критерии приёмки:**
- [ ] Все импорты работают
- [ ] Тесты проходят

---

### 2.9. Финальная проверка фазы 2

#### 2.9.1. Запустить все тесты

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Все тесты
pytest tests/ -v --tb=short

# Ожидаемый результат: 107 passed
```

#### 2.9.2. Проверка структуры

```bash
# Проверить структуру
tree python/data/
tree python/services/

# Ожидаемый результат:
# python/data/
# ├── __init__.py
# ├── bolt_dimensions.py
# ├── fastener_dimensions.py
# ├── materials.py
# └── validation.py
#
# python/services/
# ├── __init__.py
# └── dimension_service.py
```

#### 2.9.3. Зафиксировать изменения

```bash
# Проверить статус
git status

# Закоммитить изменения
git add python/data/ python/services/ python/gost_data.py
git commit -m "refactor(phase2): разделение gost_data.py на модули

- Создан пакет python/data/ для данных ГОСТ
- Создан пакет python/services/ для бизнес-логики
- gost_data.py теперь wrapper для обратной совместимости
- Разделено 443 строки на 6 специализированных модулей
- Добавлены type hints и TypedDict
- Улучшена документация

#refactoring #phase2"
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] Структура директорий создана
- [ ] Изменения закоммичены

---

## ✅ Чеклист завершения фазы 2

### Обязательные задачи:
- [ ] 2.1.1. Директория `python/data/` создана
- [ ] 2.1.2. `__init__.py` экспортирует все символы
- [ ] 2.2.1. `bolt_dimensions.py` с TypedDict и данными
- [ ] 2.3.1. `fastener_dimensions.py` с данными гаек и шайб
- [ ] 2.4.1. `materials.py` с данными материалов
- [ ] 2.5.1. `validation.py` с валидацией и AVAILABLE_LENGTHS
- [ ] 2.6.1. `gost_data.py` wrapper для обратной совместимости
- [ ] 2.7.1. Директория `python/services/` создана
- [ ] 2.7.3. `dimension_service.py` с функциями-геттерами
- [ ] 2.8.1. Импорты обновлены во всех файлах
- [ ] 2.9.1. Все 107 тестов проходят
- [ ] 2.9.3. Изменения закоммичены

---

## 📊 Метрики фазы

| Метрика | До | После | Изменение |
|---------|-----|-------|-----------|
| Строк в gost_data.py | 443 | 50 | -393 (-89%) |
| Строк в data/ | 0 | ~510 | +510 |
| Строк в services/ | 0 | ~150 | +150 |
| Модулей | 1 | 6 | +5 |
| Type hints | 0% | 90%+ | +90% |
| Тестов пройдено | 107 | 107 | 0 |

---

## 🚀 Следующие шаги

После завершения фазы 2:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 3**

**Ссылка на следующую фазу:** `refactoring/PHASE_3_TODO.md`

---

## 📚 Приложения

### A. Карта импортов

```
# Старые импорты (работают через wrapper)
from gost_data import validate_parameters, BOLT_DIM_DATA

# Новые импорты (прямые)
from data.validation import validate_parameters
from data.bolt_dimensions import BOLT_DIM_DATA
from services.dimension_service import get_bolt_hook_length
```

### B. Структура проекта после фазы 2

```
python/
├── data/
│   ├── __init__.py
│   ├── bolt_dimensions.py      # BOLT_DIM_DATA, get_bolt_dimensions()
│   ├── fastener_dimensions.py  # NUT_DIM_DATA, WASHER_DIM_DATA
│   ├── materials.py            # MATERIALS, get_material_name()
│   └── validation.py           # validate_parameters(), AVAILABLE_LENGTHS
│
├── services/
│   ├── __init__.py
│   └── dimension_service.py    # get_bolt_hook_length(), get_thread_length(), ...
│
├── gost_data.py                # Wrapper для обратной совместимости
└── ...
```

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
