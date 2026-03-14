"""
Тесты для main.py - управление IFC документом
"""
import pytest
import sys
import os

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))


class TestSpatialElementsPlacement:
    """Тесты ObjectPlacement для пространственных элементов"""

    def test_site_has_object_placement(self):
        """IfcSite должен иметь ObjectPlacement"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        sites = ifc_doc.by_type('IfcSite')

        assert len(sites) == 1
        assert sites[0].ObjectPlacement is not None
        assert sites[0].ObjectPlacement.is_a() == 'IfcLocalPlacement'

    def test_building_has_object_placement(self):
        """IfcBuilding должен иметь ObjectPlacement"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        buildings = ifc_doc.by_type('IfcBuilding')

        assert len(buildings) == 1
        assert buildings[0].ObjectPlacement is not None
        assert buildings[0].ObjectPlacement.is_a() == 'IfcLocalPlacement'

    def test_storey_has_object_placement(self):
        """IfcBuildingStorey должен иметь ObjectPlacement"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        storeys = ifc_doc.by_type('IfcBuildingStorey')

        assert len(storeys) == 1
        assert storeys[0].ObjectPlacement is not None
        assert storeys[0].ObjectPlacement.is_a() == 'IfcLocalPlacement'

    def test_placement_hierarchy(self):
        """ObjectPlacement должен быть у всех элементов"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        
        sites = ifc_doc.by_type('IfcSite')
        buildings = ifc_doc.by_type('IfcBuilding')
        storeys = ifc_doc.by_type('IfcBuildingStorey')

        # Все элементы имеют ObjectPlacement
        assert sites[0].ObjectPlacement is not None
        assert buildings[0].ObjectPlacement is not None
        assert storeys[0].ObjectPlacement is not None
        
        # Примечание: edit_object_placement создаёт размещения относительно мировой СК
        # Для создания иерархии нужно использовать прямое создание сущностей


class TestOwnerHistory:
    """Тесты IfcOwnerHistory"""

    def test_owner_history_created(self):
        """IfcOwnerHistory должен быть создан"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        owner_histories = ifc_doc.by_type('IfcOwnerHistory')

        assert len(owner_histories) >= 1

    def test_project_has_owner_history(self):
        """IfcProject должен иметь OwnerHistory"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        projects = ifc_doc.by_type('IfcProject')

        assert len(projects) == 1
        assert projects[0].OwnerHistory is not None

    def test_site_has_owner_history(self):
        """IfcSite должен иметь OwnerHistory"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        sites = ifc_doc.by_type('IfcSite')

        assert len(sites) == 1
        assert sites[0].OwnerHistory is not None

    def test_building_has_owner_history(self):
        """IfcBuilding должен иметь OwnerHistory"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        buildings = ifc_doc.by_type('IfcBuilding')

        assert len(buildings) == 1
        assert buildings[0].OwnerHistory is not None

    def test_storey_has_owner_history(self):
        """IfcBuildingStorey должен иметь OwnerHistory"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        storeys = ifc_doc.by_type('IfcBuildingStorey')

        assert len(storeys) == 1
        assert storeys[0].OwnerHistory is not None

    def test_owner_history_attributes(self):
        """IfcOwnerHistory должен иметь обязательные атрибуты"""
        from main import initialize_base_document, get_ifc_document

        ifc_doc = initialize_base_document()
        owner_history = ifc_doc.by_type('IfcOwnerHistory')[0]

        assert owner_history.OwningUser is not None
        assert owner_history.OwningApplication is not None
        assert owner_history.CreationDate is not None
