"""
Тесты для container.py — Dependency Injection контейнер

Тесты для DI контейнера и управления зависимостями.
"""

import os
import sys

import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestDIContainer:
    """Тесты для DIContainer"""

    def test_init(self):
        """DIContainer должен инициализироваться с ifc_doc"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        assert container.get_ifc_document() is mock_ifc

    def test_get_ifc_document(self):
        """get_ifc_document должен возвращать переданный документ"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        assert container.get_ifc_document() is mock_ifc

    def test_get_geometry_builder(self):
        """get_geometry_builder должен возвращать GeometryBuilder"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)
        builder = container.get_geometry_builder()

        assert builder is not None
        # Проверка кэширования
        assert container.get_geometry_builder() is builder

    def test_get_material_manager(self):
        """get_material_manager должен возвращать MaterialManager"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)
        manager = container.get_material_manager()

        assert manager is not None
        # Проверка кэширования
        assert container.get_material_manager() is manager

    def test_get_type_factory(self):
        """get_type_factory должен возвращать TypeFactory"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)
        factory = container.get_type_factory()

        assert factory is not None
        # Проверка кэширования
        assert container.get_type_factory() is factory

    def test_get_instance_factory(self):
        """get_instance_factory должен возвращать InstanceFactory"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)
        factory = container.get_instance_factory()

        assert factory is not None
        # Проверка кэширования
        assert container.get_instance_factory() is factory

    def test_register_and_resolve(self):
        """register и resolve должны работать корректно"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        test_obj = {"test": "value"}
        container.register("test_service", lambda: test_obj)

        resolved = container.resolve("test_service")
        assert resolved is test_obj

    def test_resolve_not_found(self):
        """resolve должен вызывать KeyError для несуществующей зависимости"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        with pytest.raises(KeyError, match="not found"):
            container.resolve("nonexistent")

    def test_reset(self):
        """reset должен очищать кэш экземпляров"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        builder1 = container.get_geometry_builder()
        container.reset()
        builder2 = container.get_geometry_builder()

        assert builder1 is not builder2

    def test_getitem(self):
        """__getitem__ должен работать как resolve"""
        from conftest import MockIfcDoc
        from container import DIContainer

        mock_ifc = MockIfcDoc()
        container = DIContainer(mock_ifc)

        test_obj = {"test": "value"}
        container.register("test_service", lambda: test_obj)

        assert container["test_service"] is test_obj


class TestGlobalContainer:
    """Тесты для глобального контейнера"""

    def test_get_container(self):
        """get_container должен возвращать один и тот же экземпляр"""
        from conftest import MockIfcDoc
        from container import get_container, reset_container

        reset_container()
        mock_ifc = MockIfcDoc()
        container1 = get_container(mock_ifc)
        container2 = get_container()

        assert container1 is container2

    def test_get_container_no_doc(self):
        """get_container без doc должен вызывать ValueError"""
        from container import get_container, reset_container

        reset_container()

        with pytest.raises(ValueError, match="ifc_doc required"):
            get_container()

    def test_reset_container(self):
        """reset_container должен сбрасывать глобальный контейнер"""
        from conftest import MockIfcDoc
        from container import get_container, reset_container

        reset_container()
        mock_ifc1 = MockIfcDoc()
        container1 = get_container(mock_ifc1)
        reset_container()
        mock_ifc2 = MockIfcDoc()
        container2 = get_container(mock_ifc2)

        assert container1 is not container2
