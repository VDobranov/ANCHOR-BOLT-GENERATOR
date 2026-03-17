"""
protocols.py — Protocol интерфейсы для dependency injection

Согласно PEP 544:
- Protocol определяет структурный подтип
- Позволяет использовать duck typing с проверкой типов
- Устраняет необходимость в явных интерфейсах
"""

from typing import Any, List, Optional, Protocol, runtime_checkable

# =============================================================================
# IFC Document Protocol
# =============================================================================


@runtime_checkable
class IfcDocumentProtocol(Protocol):
    """
    Протокол для IFC документа

    Определяет минимальный интерфейс для работы с IFC файлом.
    Позволяет использовать mock объекты в тестах.
    """

    def create_entity(self, entity_type: str, *args, **kwargs) -> Any:
        """Создание IFC сущности"""
        ...

    def by_type(self, entity_type: str, include_subtypes: bool = False) -> List[Any]:
        """Получение сущностей по типу"""
        ...

    def by_id(self, id: int) -> Any:
        """Получение сущности по ID"""
        ...

    def by_guid(self, guid: str) -> Any:
        """Получение сущности по GUID"""
        ...

    def write(self, filepath: str) -> None:
        """Запись в файл"""
        ...

    def remove(self, entity: Any) -> None:
        """Удаление сущности"""
        ...

    def get_inverse(self, entity: Any) -> List[Any]:
        """Получение обратных ссылок"""
        ...

    def traverse(self, entity: Any, max_levels: Optional[int] = None) -> List[Any]:
        """Обход графа сущности"""
        ...

    @property
    def schema(self) -> str:
        """Схема IFC (например, 'IFC4')"""
        ...

    def __len__(self) -> int:
        """Количество сущностей в файле"""
        ...


# =============================================================================
# Geometry Builder Protocol
# =============================================================================


@runtime_checkable
class GeometryBuilderProtocol(Protocol):
    """
    Протокол для построителя геометрии

    Определяет интерфейс для создания IFC геометрии.
    """

    def create_bent_stud_solid(self, bolt_type: str, diameter: int, length: int) -> Any:
        """Создание изогнутой шпильки"""
        ...

    def create_straight_stud_solid(self, diameter: int, length: int) -> Any:
        """Создание прямой шпильки"""
        ...

    def create_nut_solid(self, diameter: int, height: int) -> Any:
        """Создание гайки"""
        ...

    def create_washer_solid(self, diameter: int, outer_diameter: int, thickness: int) -> Any:
        """Создание шайбы"""
        ...

    def associate_representation(self, product_type: Any, shape_rep: Any) -> None:
        """Ассоциация представления с типом продукта"""
        ...


# =============================================================================
# Material Manager Protocol
# =============================================================================


@runtime_checkable
class MaterialManagerProtocol(Protocol):
    """
    Протокол для менеджера материалов

    Определяет интерфейс для управления материалами IFC.
    """

    def create_material(
        self,
        name: str,
        description: Optional[str] = None,
        category: Optional[str] = None,
        material_key: Optional[str] = None,
    ) -> Any:
        """Создание или получение материала"""
        ...

    def get_material(self, name: str) -> Optional[Any]:
        """Получение материала по имени"""
        ...

    def associate_material(self, ifc_entity: Any, material: Any) -> None:
        """Ассоциация материала с сущностью"""
        ...

    def create_material_list(self, materials: List[Any]) -> Any:
        """Создание списка материалов"""
        ...


# =============================================================================
# Type Factory Protocol
# =============================================================================


@runtime_checkable
class TypeFactoryProtocol(Protocol):
    """
    Протокол для фабрики типов

    Определяет интерфейс для создания типов IFC.
    """

    def get_or_create_stud_type(
        self, bolt_type: str, diameter: int, length: int, material: str
    ) -> Any:
        """Создание/получение типа шпильки"""
        ...

    def get_or_create_nut_type(self, diameter: int, material: str) -> Any:
        """Создание/получение типа гайки"""
        ...

    def get_or_create_washer_type(self, diameter: int, material: str) -> Any:
        """Создание/получение типа шайбы"""
        ...

    def get_or_create_assembly_type(
        self, bolt_type: str, diameter: int, length: int, material: str
    ) -> Any:
        """Создание/получение типа сборки"""
        ...

    def get_representation_map(
        self,
        component_type: str,
        diameter: int,
        length: Optional[int] = None,
        bolt_type: Optional[str] = None,
    ) -> Optional[Any]:
        """Получение RepresentationMap для компонента"""
        ...


# =============================================================================
# Instance Factory Protocol
# =============================================================================


@runtime_checkable
class InstanceFactoryProtocol(Protocol):
    """
    Протокол для фабрики инстансов

    Определяет интерфейс для создания инстансов болтов.
    """

    def create_bolt_assembly(
        self, bolt_type: str, diameter: int, length: int, material: str
    ) -> Any:
        """Создание полной сборки анкерного болта"""
        ...


# =============================================================================
# Dimension Service Protocol
# =============================================================================


@runtime_checkable
class DimensionServiceProtocol(Protocol):
    """
    Протокол для сервиса размеров

    Определяет интерфейс для работы с размерами болтов.
    """

    def get_bolt_dimensions(self, bolt_type: str, diameter: int, length: int) -> Optional[Any]:
        """Получение полных размеров болта"""
        ...

    def get_hook_length(self, diameter: int, length: int) -> Optional[int]:
        """Получить вылет крюка"""
        ...

    def get_bend_radius(self, diameter: int, length: int) -> int:
        """Получить радиус загиба"""
        ...

    def get_thread_length(self, diameter: int, length: int) -> Optional[int]:
        """Получить длину резьбы"""
        ...

    def get_nut_dimensions(self, diameter: int) -> Optional[Any]:
        """Получить размеры гайки"""
        ...

    def get_washer_dimensions(self, diameter: int) -> Optional[Any]:
        """Получить размеры шайбы"""
        ...


__all__ = [
    "IfcDocumentProtocol",
    "GeometryBuilderProtocol",
    "MaterialManagerProtocol",
    "TypeFactoryProtocol",
    "InstanceFactoryProtocol",
    "DimensionServiceProtocol",
]
