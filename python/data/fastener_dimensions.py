"""
fastener_dimensions.py — Размеры гаек и шайб

Based on ГОСТ 24379.1-2012 and related standards
"""

from typing import Any, Dict, Optional

# Параметры гаек из DIM.py
# Формат: "{диаметр}": [диаметр номинальный, s_width, высота]
# Примечание: s_width > diameter для всех размеров
NUT_DIM_DATA: Dict[str, list] = {
    "12": [12, 19, 10],
    "16": [16, 24, 13],
    "20": [20, 30, 16],
    "24": [24, 36, 19],
    "30": [30, 46, 24],
    "36": [36, 55, 29],
    "42": [42, 65, 34],
    "48": [48, 75, 38],
}

# Параметры шайб из DIM.py
# Формат: "{диаметр}": [диаметр номинальный, inner_diameter, outer_diameter, thickness]
WASHER_DIM_DATA: Dict[str, list] = {
    "12": [12, 13, 36, 3],
    "16": [16, 17, 42, 4],
    "20": [20, 21, 45, 8],
    "24": [24, 25, 55, 8],
    "30": [30, 32, 80, 10],
    "36": [36, 38, 90, 10],
    "42": [42, 44, 95, 14],
    "48": [48, 50, 105, 14],
}


def get_nut_dimensions(diameter: int) -> Optional[Dict[str, Any]]:
    """
    Получить размеры гайки для данного диаметра.

    Args:
        diameter: Диаметр болта (мм)

    Returns:
        Dict с размерами гайки или None
    """
    key = str(diameter)
    if key not in NUT_DIM_DATA:
        return None

    data = NUT_DIM_DATA[key]
    return {
        "diameter": data[0],
        "s_width": data[1],  # Размер под ключ
        "height": data[2],
    }


def get_washer_dimensions(diameter: int) -> Optional[Dict[str, Any]]:
    """
    Получить размеры шайбы для данного диаметра.

    Args:
        diameter: Диаметр болта (мм)

    Returns:
        Dict с размерами шайбы или None
    """
    key = str(diameter)
    if key not in WASHER_DIM_DATA:
        return None

    data = WASHER_DIM_DATA[key]
    return {
        "nominal_diameter": data[0],
        "inner_diameter": data[1],
        "outer_diameter": data[2],
        "thickness": data[3],
    }
