"""
conftest.py — Конфигурация и фикстуры для pytest тестов

Централизованное хранилище:
- Mock классов для тестирования
- Фикстур для общих объектов
- Конфигурации тестов
"""

import os
import sys
from typing import Any, Dict, List, Optional

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))

import pytest

# =============================================================================
# Mock классы
# =============================================================================


class MockIfcEntity:
    """
    Mock для IFC сущности

    Используется в тестах для имитации поведения ifcopenshell сущностей.
    Поддерживает основные атрибуты и методы IFC entity.

    Attributes:
        _entity_type: Тип сущности (например, 'IfcMechanicalFastenerType')
        _kwargs: Атрибуты сущности
    """

    def __init__(self, entity_type: str, *args, **kwargs):
        """
        Инициализация Mock сущности

        Args:
            entity_type: Тип сущности
            *args: Позиционные аргументы
            **kwargs: Именованные атрибуты сущности
        """
        self._entity_type = entity_type
        self._kwargs = kwargs

        # Обработка positional аргументов
        if args:
            for i, arg in enumerate(args):
                setattr(self, f"arg{i}", arg)

        # Установка атрибутов
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Установим RepresentationMaps и HasPropertySets по умолчанию для типов
        if entity_type == "IfcMechanicalFastenerType":
            if not hasattr(self, "RepresentationMaps"):
                self.RepresentationMaps = None
            if not hasattr(self, "HasPropertySets"):
                self.HasPropertySets = []

    def is_a(self, entity_type: Optional[str] = None) -> str:
        """Получение типа сущности или проверка типа"""
        if entity_type is None:
            return self._entity_type
        return self._entity_type if self._entity_type == entity_type else ""

    def get_info(self) -> Dict[str, Any]:
        """Получение информации о сущности для ifcopenshell.api"""
        return {"entity_type": self._entity_type, **self._kwargs}

    def __getattr__(self, name: str) -> Any:
        """Получение атрибута"""
        return self._kwargs.get(name)

    def __setattr__(self, name: str, value: Any):
        """Установка атрибута"""
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            self._kwargs[name] = value
            super().__setattr__(name, value)

    def __repr__(self) -> str:
        """Строковое представление"""
        return f"MockIfcEntity({self._entity_type})"

    @property
    def dim(self) -> Optional[int]:
        """
        Определение размерности для кривых и точек

        Returns:
            2 для 2D, 3 для 3D, None если не определено
        """
        if "3D" in self._entity_type:
            return 3
        if "2D" in self._entity_type:
            return 2
        if self._entity_type == "IfcIndexedPolyCurve":
            points = self._kwargs.get("Points")
            if points and hasattr(points, "dim"):
                return points.dim
            return 3
        if self._entity_type in [
            "IfcCircle",
            "IfcPolyline",
            "IfcCompositeCurve",
            "IfcArcIndex",
            "IfcLineIndex",
        ]:
            return 2
        return None


class MockIfcDoc:
    """
    Mock для IFC документа

    Используется в тестах для имитации поведения ifcopenshell.file.
    Поддерживает создание сущностей, запросы by_type, и базовые методы.

    Attributes:
        entities: Список всех созданных сущностей
        _by_type: Словарь сущностей по типам
        schema: IFC схема (по умолчанию 'IFC4')
    """

    def __init__(self):
        """Инициализация Mock документа"""
        self.entities: List[MockIfcEntity] = []
        self._by_type: Dict[str, List[MockIfcEntity]] = {}
        self.schema: str = "IFC4"

    def create_entity(self, entity_type: str, *args, **kwargs) -> MockIfcEntity:
        """
        Создание IFC сущности

        Args:
            entity_type: Тип сущности (например, 'IfcMechanicalFastener')
            *args: Позиционные аргументы
            **kwargs: Именованные атрибуты

        Returns:
            Созданная Mock сущность
        """
        # Поддержка IfcReal и IfcText для PropertySets
        if entity_type == "IfcReal":
            value = args[0] if args else kwargs.get("Value", 0.0)
            entity = MockIfcEntity(entity_type, Value=value)
        elif entity_type == "IfcText":
            value = args[0] if args else kwargs.get("Value", "")
            entity = MockIfcEntity(entity_type, Value=value)
        elif entity_type in ["IfcLineIndex", "IfcArcIndex"] and args:
            entity = MockIfcEntity(entity_type, Indices=args[0])
        else:
            entity = MockIfcEntity(entity_type, *args, **kwargs)

        self.entities.append(entity)

        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)

        return entity

    def __getattr__(self, name: str):
        """
        Динамическая поддержка методов

        Args:
            name: Имя метода

        Returns:
            Функция для создания сущности
        """
        # Динамическая поддержка методов типа createIfcIndexedPolyCurve
        if name.startswith("create"):
            entity_type = name[6:]

            def create_method(*args, **kwargs):
                return self.create_entity(entity_type, *args, **kwargs)

            return create_method
        raise AttributeError(f"'MockIfcDoc' object has no attribute '{name}'")

    def by_type(self, entity_type: str) -> List[MockIfcEntity]:
        """
        Получение сущностей по типу

        Args:
            entity_type: Тип сущности

        Returns:
            Список сущностей указанного типа
        """
        return self._by_type.get(entity_type, [])

    def __len__(self) -> int:
        """Количество сущностей в документе"""
        return len(self.entities)


def mock_ifcopenshell_api_run(func_name: str, ifc_doc, *args, **kwargs):
    """
    Мок для ifcopenshell.api.run

    Поддерживает:
    - pset.add_pset: создаёт IfcPropertySet
    - pset.edit_pset: добавляет свойства в Pset
    """
    if func_name == "pset.add_pset":
        product = kwargs.get("product")
        name = kwargs.get("name")
        pset = ifc_doc.create_entity("IfcPropertySet", Name=name)
        # Mock entity
        if not isinstance(getattr(product, "HasPropertySets", None), list):
            product.HasPropertySets = []
        product.HasPropertySets.append(pset)
        return pset

    elif func_name == "pset.edit_pset":
        pset = kwargs.get("pset")
        properties = kwargs.get("properties", {})
        # Добавляем свойства в Pset
        # Принудительно устанавливаем в список, если это не список
        if not isinstance(getattr(pset, "HasProperties", None), list):
            pset.HasProperties = []
        for prop_name, prop_value in properties.items():
            prop_entity = ifc_doc.create_entity("IfcPropertySingleValue", Name=prop_name)
            # Создаём NominalValue
            if isinstance(prop_value, float):
                nominal = ifc_doc.create_entity("IfcReal", Value=prop_value)
            elif isinstance(prop_value, int):
                nominal = ifc_doc.create_entity("IfcInteger", Value=prop_value)
            else:
                nominal = ifc_doc.create_entity("IfcText", Value=str(prop_value))
            prop_entity.NominalValue = nominal
            pset.HasProperties.append(prop_entity)
        return pset

    # Для других функций возвращаем пустой dict
    return {}


# =============================================================================
# Фикстуры
# =============================================================================


@pytest.fixture(scope="session")
def python_path() -> str:
    """Возвращает путь к python модулям"""
    return os.path.join(os.path.dirname(__file__), "..", "python")


@pytest.fixture(scope="function")
def mock_ifc_doc() -> MockIfcDoc:
    """
    Создание Mock IFC документа

    Returns:
        Экземпляр MockIfcDoc
    """
    return MockIfcDoc()


@pytest.fixture(scope="function")
def mock_ifc_api_run(monkeypatch):
    """
    Мокирование ifcopenshell.api.run для тестов

    Применяется явно в тестах, требующих мокирования.
    """
    import ifcopenshell.api

    monkeypatch.setattr(ifcopenshell.api, "run", mock_ifcopenshell_api_run)


@pytest.fixture(scope="function")
def valid_bolt_params() -> Dict[str, Any]:
    """Параметры валидного болта по умолчанию"""
    return {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}


@pytest.fixture(scope="function")
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ["1.1", "1.2", "2.1", "5"]


@pytest.fixture(scope="function")
def all_diameters():
    """Все доступные диаметры"""
    return [12, 16, 20, 24, 30, 36, 42, 48]


@pytest.fixture(scope="function")
def all_materials():
    """Все доступные материалы"""
    return ["09Г2С", "ВСт3пс2", "10Г2"]
