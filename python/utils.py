"""
utils.py — Общие утилиты для Python-модулей
"""

# Ленивый импорт ifcopenshell
_ifcopenshell_cache = None


def get_ifcopenshell():
    """
    Получение ifcopenshell с ленивым импортом
    
    Returns:
        ifcopenshell модуль или None если недоступен
    """
    global _ifcopenshell_cache
    if _ifcopenshell_cache is None:
        try:
            import ifcopenshell as _ifc
            _ifcopenshell_cache = _ifc
        except ImportError:
            return None
    return _ifcopenshell_cache


def is_ifcopenshell_available():
    """Проверка доступности ifcopenshell"""
    return get_ifcopenshell() is not None
