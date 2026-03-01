"""
Тесты для utils.py
"""
import pytest


class TestUtils:
    """Тесты для функций из utils.py"""

    def test_get_ifcopenshell_returns_module_or_none(self):
        """get_ifcopenshell должен возвращать модуль или None"""
        from utils import get_ifcopenshell
        
        result = get_ifcopenshell()
        # В среде Pyodide должен возвращать модуль, в обычном Python - None
        assert result is None or hasattr(result, 'file')

    def test_is_ifcopenshell_available_returns_bool(self):
        """is_ifcopenshell_available должен возвращать bool"""
        from utils import is_ifcopenshell_available
        
        result = is_ifcopenshell_available()
        assert isinstance(result, bool)

    def test_get_ifcopenshell_cached(self):
        """get_ifcopenshell должен кэшировать результат"""
        from utils import get_ifcopenshell, _ifcopenshell_cache
        
        # Первый вызов
        result1 = get_ifcopenshell()
        # Второй вызов
        result2 = get_ifcopenshell()
        
        # Результаты должны быть одинаковыми (кэширование)
        assert result1 is result2
