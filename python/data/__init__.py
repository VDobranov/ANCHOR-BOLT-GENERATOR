"""
python/data/ — Модуль данных ГОСТ для анкерных болтов

Содержит:
- BOLT_DIM_DATA: данные размеров болтов
- NUT_DIM_DATA, WASHER_DIM_DATA: размеры гаек и шайб
- MATERIALS: данные о материалах
- BOLT_TYPES, AVAILABLE_DIAMETERS, AVAILABLE_LENGTHS: константы
- validate_parameters: функция валидации
"""

from .bolt_dimensions import (
    AVAILABLE_DIAMETERS,
    BOLT_DIM_DATA,
    DIAMETER_LIMITS,
    get_bolt_dimensions,
)
from .fastener_dimensions import (
    NUT_DIM_DATA,
    PLATE_DIM_DATA,
    WASHER_DIM_DATA,
    get_nut_dimensions,
    get_plate_dimensions,
    get_washer_dimensions,
)
from .materials import MATERIALS, get_material_name, get_material_properties
from .validation import (
    AVAILABLE_LENGTHS,
    BOLT_TYPES,
    MASS_INDICES,
    get_bolt_bend_radius,
    get_bolt_hook_length,
    get_bolt_mass,
    get_thread_length,
    validate_parameters,
)

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
    "PLATE_DIM_DATA",
    # Functions
    "get_bolt_dimensions",
    "get_nut_dimensions",
    "get_washer_dimensions",
    "get_plate_dimensions",
    "get_material_name",
    "get_material_properties",
    "validate_parameters",
    "get_bolt_hook_length",
    "get_bolt_bend_radius",
    "get_thread_length",
    "get_bolt_mass",
]
