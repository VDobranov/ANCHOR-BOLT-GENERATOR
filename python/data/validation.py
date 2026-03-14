"""
validation.py — Валидация параметров болтов и доступные длины

Based on ГОСТ 24379.1-2012
"""

from typing import Dict, List, Literal, Optional, Set, Tuple

from .bolt_dimensions import AVAILABLE_DIAMETERS, BOLT_DIM_DATA, DIAMETER_LIMITS
from .fastener_dimensions import NUT_DIM_DATA, WASHER_DIM_DATA
from .materials import MATERIALS

# Типы болтов (допустимые значения)
BOLT_TYPES: Set[str] = {"1.1", "1.2", "2.1", "5"}

# Индексы масс по типам болтов
MASS_INDICES: Dict[str, int] = {"1.1": 5, "1.2": 6, "2.1": 7, "5": 8}

# Доступные длины для каждой комбинации типа и диаметра
# Генерируется автоматически из BOLT_DIM_DATA на основе наличия массы
AVAILABLE_LENGTHS: Dict[Tuple[str, int], List[int]] = {}

# Автогенерация AVAILABLE_LENGTHS из BOLT_DIM_DATA на основе наличия массы
for key, data in BOLT_DIM_DATA.items():
    diameter = int(key.split("_")[0])
    length = int(data[0])

    for bolt_type, mass_idx in MASS_INDICES.items():
        # Проверяем, что масса существует (не None)
        if mass_idx < len(data) and data[mass_idx] is not None:
            # Для каждого типа добавляем длины
            if bolt_type in BOLT_TYPES:
                type_key = (bolt_type, diameter)
                if type_key not in AVAILABLE_LENGTHS:
                    AVAILABLE_LENGTHS[type_key] = []
                if length not in AVAILABLE_LENGTHS[type_key]:
                    AVAILABLE_LENGTHS[type_key].append(length)

# Сортировка длин
for type_key in AVAILABLE_LENGTHS:
    AVAILABLE_LENGTHS[type_key].sort()


def get_bolt_hook_length(diameter: int, length: int) -> Optional[int]:
    """Получить вылет крюка для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][1]  # вылет крюка
    return None


def get_bolt_bend_radius(diameter: int, length: int) -> int:
    """Получить радиус загиба для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][2]  # радиус загиба
    return diameter


def get_thread_length(diameter: int, length: int) -> Optional[int]:
    """Получить длину резьбы для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][4]  # длина резьбы
    return None


def get_bolt_mass(diameter: int, length: int, bolt_type: str) -> Optional[float]:
    """
    Получить массу болта данного диаметра, длины и типа.

    Args:
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')

    Returns:
        Масса в кг или None, если болт такого типа не существует
    """
    key = f"{diameter}_{length}"
    if key not in BOLT_DIM_DATA:
        return None

    data = BOLT_DIM_DATA[key]
    mass_idx = MASS_INDICES.get(bolt_type)

    if mass_idx is None or mass_idx >= len(data):
        return None

    return data[mass_idx]


def validate_parameters(bolt_type: str, diameter: int, length: int, material: str) -> bool:
    """
    Валидация параметров болта согласно ГОСТ.

    Args:
        bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
        diameter: Диаметр болта (мм)
        length: Длина болта (мм)
        material: Материал болта

    Returns:
        True если параметры валидны

    Raises:
        ValueError: Если параметры невалидны
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
        min_d, max_d = DIAMETER_LIMITS[bolt_type]  # type: ignore[index]
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
            errors.append(f"Комбинация типа {bolt_type} и диаметра М{diameter} не существует")
        elif length not in AVAILABLE_LENGTHS[key]:
            available = AVAILABLE_LENGTHS[key]
            errors.append(f"Длина {length} недоступна. Доступные длины: {available}")
        else:
            # Дополнительная проверка: масса для данного типа должна существовать
            mass = get_bolt_mass(diameter, length, bolt_type)
            if mass is None:
                errors.append(
                    f"Болт типа {bolt_type} с параметрами М{diameter}×{length} не существует (нет массы)"
                )

    if errors:
        raise ValueError("\n".join(errors))

    return True
