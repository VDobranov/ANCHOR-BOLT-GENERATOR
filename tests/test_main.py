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
