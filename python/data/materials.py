"""
materials.py — Данные о материалах для анкерных болтов

Based on ГОСТ 24379.1-2012 and related standards
"""

from typing import Any, Dict, Optional

# Материалы согласно ГОСТ
MATERIALS: Dict[str, Dict[str, Any]] = {
    "09Г2С": {
        "gost": "19281-2014",
        "tensile_strength": 490,  # МПа
        "yield_strength": 390,
        "density": 7850,  # кг/м³
        "description": "Низколегированная сталь",
    },
    "ВСт3пс2": {
        "gost": "535-88",
        "tensile_strength": 345,
        "yield_strength": 235,
        "density": 7850,
        "description": "Углеродистая конструкционная сталь",
    },
    "10Г2": {
        "gost": "19281-2014",
        "tensile_strength": 490,
        "yield_strength": 390,
        "density": 7850,
        "description": "Низколегированная сталь",
    },
}


def get_material_name(material: str) -> str:
    """
    Форматирование имени материала для IFC.

    Args:
        material: Название материала (например, '09Г2С')

    Returns:
        Строка в формате: "09Г2С ГОСТ 19281-2014"
    """
    info = MATERIALS.get(material)
    if info:
        return f"{material} ГОСТ {info['gost']}"
    return material


def get_material_properties(material: str) -> Optional[Dict[str, Any]]:
    """
    Получить свойства материала.

    Args:
        material: Название материала

    Returns:
        Dict со свойствами материала или None
    """
    return MATERIALS.get(material)
