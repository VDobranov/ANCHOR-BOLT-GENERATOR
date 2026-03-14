"""
gost_data.py — ГОСТ справочники и валидация параметров

Модуль-обёртка для обратной совместимости.
Все данные и функции перемещены в пакет python/data/

Based on ГОСТ 24379.1-2012 and related standards
"""

# Импортируем всё из нового пакета для обратной совместимости
from data.bolt_dimensions import (
    AVAILABLE_DIAMETERS,
    BOLT_DIM_DATA,
    DIAMETER_LIMITS,
    get_bolt_dimensions,
)
from data.fastener_dimensions import (
    NUT_DIM_DATA,
    WASHER_DIM_DATA,
    get_nut_dimensions,
    get_washer_dimensions,
)
from data.materials import MATERIALS, get_material_name, get_material_properties
from data.validation import (
    AVAILABLE_LENGTHS,
    BOLT_TYPES,
    MASS_INDICES,
    get_bolt_bend_radius,
    get_bolt_hook_length,
    get_bolt_mass,
    get_thread_length,
    validate_parameters,
)


# Дополнительные функции для обратной совместимости
def get_bolt_l1(diameter: int, length: int) -> int:
    """Получить l1 (длина верхнего участка) для болта"""
    dims = get_bolt_dimensions(diameter, length)
    return dims["l1"] if dims else None


def get_bolt_l2(diameter: int, length: int) -> int:
    """Получить l2 (длина нижнего горизонтального участка) для болта"""
    dims = get_bolt_dimensions(diameter, length)
    return dims["l2"] if dims else None


def get_bolt_l3(diameter: int, length: int) -> int:
    """Получить l3 (длина нижнего участка) для болта"""
    dims = get_bolt_dimensions(diameter, length)
    return dims["l3"] if dims else None


__all__ = [
    # Constants
    "BOLT_TYPES",
    "AVAILABLE_DIAMETERS",
    "DIAMETER_LIMITS",
    "AVAILABLE_LENGTHS",
    "MASS_INDICES",
    "MATERIALS",
    # Data
    "BOLT_DIM_DATA",
    "NUT_DIM_DATA",
    "WASHER_DIM_DATA",
    # Functions
    "get_bolt_dimensions",
    "get_nut_dimensions",
    "get_washer_dimensions",
    "get_material_name",
    "get_material_properties",
    "validate_parameters",
    "get_bolt_hook_length",
    "get_bolt_bend_radius",
    "get_thread_length",
    "get_bolt_mass",
    # Legacy functions
    "get_bolt_l1",
    "get_bolt_l2",
    "get_bolt_l3",
]
