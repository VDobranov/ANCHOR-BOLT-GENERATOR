"""
dimension_service.py — Сервис для получения размеров болтов

Бизнес-логика для работы с размерами фундаментных болтов.
"""

from typing import Any, Dict, List, Literal, Optional

from data.bolt_dimensions import get_bolt_dimensions
from data.fastener_dimensions import get_nut_dimensions, get_washer_dimensions
from data.validation import (
    AVAILABLE_LENGTHS,
    get_bolt_bend_radius,
    get_bolt_hook_length,
    get_bolt_mass,
    get_thread_length,
)

BoltType = Literal["1.1", "1.2", "2.1", "5"]


class DimensionService:
    """
    Сервис для получения размеров болтов и компонентов.

    Предоставляет удобный API для работы с размерами:
    - Размеры болтов по типу, диаметру и длине
    - Размеры гаек и шайб по диаметру
    - Доступные длины для комбинации тип/диаметр
    """

    @staticmethod
    def get_bolt_dimensions(
        bolt_type: BoltType, diameter: int, length: int
    ) -> Optional[Dict[str, Any]]:
        """
        Получить полные размеры болта.

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)
            length: Длина (мм)

        Returns:
            Dict с размерами или None
        """
        dims = get_bolt_dimensions(diameter, length)
        if not dims:
            return None

        return {
            **dims,
            "bolt_type": bolt_type,
            "mass": get_bolt_mass(diameter, length, bolt_type),
        }

    @staticmethod
    def get_hook_length(diameter: int, length: int) -> Optional[int]:
        """Получить вылет крюка"""
        return get_bolt_hook_length(diameter, length)

    @staticmethod
    def get_bend_radius(diameter: int, length: int) -> int:
        """Получить радиус загиба"""
        return get_bolt_bend_radius(diameter, length)

    @staticmethod
    def get_thread_length(diameter: int, length: int) -> Optional[int]:
        """Получить длину резьбы"""
        return get_thread_length(diameter, length)

    @staticmethod
    def get_mass(diameter: int, length: int, bolt_type: BoltType) -> Optional[float]:
        """Получить массу болта"""
        return get_bolt_mass(diameter, length, bolt_type)

    @staticmethod
    def get_nut_dimensions(diameter: int) -> Optional[Dict[str, Any]]:
        """Получить размеры гайки"""
        return get_nut_dimensions(diameter)

    @staticmethod
    def get_washer_dimensions(diameter: int) -> Optional[Dict[str, Any]]:
        """Получить размеры шайбы"""
        return get_washer_dimensions(diameter)

    @staticmethod
    def get_available_lengths(bolt_type: BoltType, diameter: int) -> List[int]:
        """
        Получить доступные длины для типа и диаметра.

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)

        Returns:
            Список доступных длин
        """
        key = (bolt_type, diameter)
        return AVAILABLE_LENGTHS.get(key, [])

    @staticmethod
    def is_valid_length(bolt_type: BoltType, diameter: int, length: int) -> bool:
        """
        Проверка допустимости длины.

        Args:
            bolt_type: Тип болта
            diameter: Диаметр (мм)
            length: Длина (мм)

        Returns:
            True если длина допустима
        """
        lengths = DimensionService.get_available_lengths(bolt_type, diameter)
        return length in lengths
