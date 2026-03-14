"""
container.py — Dependency Injection контейнер

Централизованное управление зависимостями:
- Регистрация сервисов
- Получение зависимостей
- Ленивая инициализация
"""

from typing import Any, Callable, Dict, Optional, Type

from protocols import (
    GeometryBuilderProtocol,
    IfcDocumentProtocol,
    InstanceFactoryProtocol,
    MaterialManagerProtocol,
    TypeFactoryProtocol,
)


class DIContainer:
    """
    Контейнер для управления зависимостями

    Пример использования:
        container = DIContainer(ifc_doc)
        factory = container.get_instance_factory()
        result = factory.create_bolt_assembly(...)
    """

    def __init__(self, ifc_doc: IfcDocumentProtocol):
        """
        Инициализация контейнера

        Args:
            ifc_doc: IFC документ
        """
        self._ifc_doc = ifc_doc
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}

        # Регистрируем фабрики по умолчанию
        self._register_default_factories()

    def _register_default_factories(self):
        """Регистрация фабрик по умолчанию"""
        from geometry_builder import GeometryBuilder
        from instance_factory import InstanceFactory
        from material_manager import MaterialManager
        from type_factory import TypeFactory

        self._factories["geometry_builder"] = lambda: GeometryBuilder(self._ifc_doc)
        self._factories["material_manager"] = lambda: MaterialManager(self._ifc_doc)
        self._factories["type_factory"] = lambda: TypeFactory(self._ifc_doc)
        self._factories["instance_factory"] = lambda: InstanceFactory(
            self._ifc_doc, self.get_type_factory()
        )

    def get_ifc_document(self) -> IfcDocumentProtocol:
        """Получение IFC документа"""
        return self._ifc_doc

    def get_geometry_builder(self) -> GeometryBuilderProtocol:
        """Получение GeometryBuilder"""
        if "geometry_builder" not in self._instances:
            self._instances["geometry_builder"] = self._factories["geometry_builder"]()
        return self._instances["geometry_builder"]

    def get_material_manager(self) -> MaterialManagerProtocol:
        """Получение MaterialManager"""
        if "material_manager" not in self._instances:
            self._instances["material_manager"] = self._factories["material_manager"]()
        return self._instances["material_manager"]

    def get_type_factory(self) -> TypeFactoryProtocol:
        """Получение TypeFactory"""
        if "type_factory" not in self._instances:
            self._instances["type_factory"] = self._factories["type_factory"]()
        return self._instances["type_factory"]

    def get_instance_factory(self) -> InstanceFactoryProtocol:
        """Получение InstanceFactory"""
        if "instance_factory" not in self._instances:
            self._instances["instance_factory"] = self._factories["instance_factory"]()
        return self._instances["instance_factory"]

    def register(self, name: str, factory: Callable[[], Any], singleton: bool = True) -> None:
        """
        Регистрация зависимости

        Args:
            name: Имя зависимости
            factory: Фабрика для создания объекта
            singleton: Если True, объект кэшируется
        """
        self._factories[name] = factory
        if not singleton and name in self._instances:
            del self._instances[name]

    def resolve(self, name: str) -> Any:
        """
        Разрешение зависимости по имени

        Args:
            name: Имя зависимости

        Returns:
            Экземпляр зависимости
        """
        if name in self._instances:
            return self._instances[name]

        if name not in self._factories:
            raise KeyError(f"Dependency '{name}' not found")

        instance = self._factories[name]()
        self._instances[name] = instance
        return instance

    def reset(self) -> None:
        """Сброс всех закэшированных экземпляров"""
        self._instances.clear()

    def __getitem__(self, name: str) -> Any:
        """Получение зависимости через []"""
        return self.resolve(name)


# =============================================================================
# Глобальный контейнер (для обратной совместимости)
# =============================================================================

_container: Optional[DIContainer] = None


def get_container(ifc_doc: IfcDocumentProtocol = None) -> DIContainer:
    """
    Получение глобального контейнера

    Args:
        ifc_doc: IFC документ (только для первого вызова)

    Returns:
        DIContainer экземпляр
    """
    global _container
    if _container is None:
        if ifc_doc is None:
            raise ValueError("ifc_doc required for first call to get_container()")
        _container = DIContainer(ifc_doc)
    return _container


def reset_container() -> None:
    """Сброс глобального контейнера"""
    global _container
    _container = None
