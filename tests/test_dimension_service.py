"""
Тесты для dimension_service.py - сервис размеров

Тесты для сервиса получения размеров болтов и компонентов.
"""

import os
import sys

import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestDimensionService:
    """Тесты для DimensionService"""

    def test_get_bolt_dimensions(self):
        """Получение размеров болта"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_bolt_dimensions("5", 12, 300)

        assert dims is not None
        assert dims["diameter"] == 12
        assert dims["length"] == 300
        assert "bolt_type" in dims
        assert dims["bolt_type"] == "5"

    def test_get_bolt_dimensions_not_found(self):
        """Получение несуществующих размеров болта"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_bolt_dimensions("5", 12, 9999)

        assert dims is None

    def test_get_hook_length(self):
        """Получение вылета крюка"""
        from services.dimension_service import DimensionService

        hook_length = DimensionService.get_hook_length(12, 300)

        assert hook_length == 40

    def test_get_hook_length_not_found(self):
        """Получение вылета крюка для несуществующего болта"""
        from services.dimension_service import DimensionService

        hook_length = DimensionService.get_hook_length(12, 9999)

        assert hook_length is None

    def test_get_bend_radius(self):
        """Получение радиуса загиба"""
        from services.dimension_service import DimensionService

        radius = DimensionService.get_bend_radius(12, 300)

        assert radius == 12

    def test_get_bend_radius_default(self):
        """Получение радиуса загиба по умолчанию (диаметр)"""
        from services.dimension_service import DimensionService

        radius = DimensionService.get_bend_radius(12, 9999)

        assert radius == 12  # По умолчанию равен диаметру

    def test_get_thread_length(self):
        """Получение длины резьбы"""
        from services.dimension_service import DimensionService

        thread_length = DimensionService.get_thread_length(12, 300)

        assert thread_length == 80

    def test_get_thread_length_not_found(self):
        """Получение длины резьбы для несуществующего болта"""
        from services.dimension_service import DimensionService

        thread_length = DimensionService.get_thread_length(12, 9999)

        assert thread_length is None

    def test_get_mass(self):
        """Получение массы болта"""
        from services.dimension_service import DimensionService

        # Масса из dim.csv для M12x300 тип 5 = 0.27
        mass = DimensionService.get_mass(12, 300, "5")

        assert mass == 0.27

    def test_get_mass_not_found(self):
        """Получение массы для несуществующего болта"""
        from services.dimension_service import DimensionService

        mass = DimensionService.get_mass(12, 9999, "5")

        assert mass is None

    def test_get_nut_dimensions(self):
        """Получение размеров гайки"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_nut_dimensions(12)

        assert dims is not None
        assert dims["diameter"] == 12
        assert "height" in dims

    def test_get_nut_dimensions_not_found(self):
        """Получение размеров несуществующей гайки"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_nut_dimensions(999)

        assert dims is None

    def test_get_washer_dimensions(self):
        """Получение размеров шайбы"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_washer_dimensions(12)

        assert dims is not None
        assert "nominal_diameter" in dims or "diameter" in dims
        assert "outer_diameter" in dims
        assert "thickness" in dims

    def test_get_washer_dimensions_not_found(self):
        """Получение размеров несуществующей шайбы"""
        from services.dimension_service import DimensionService

        dims = DimensionService.get_washer_dimensions(999)

        assert dims is None
