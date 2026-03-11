"""
Тесты для material_manager.py - менеджер материалов IFC
"""
import pytest


class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def is_a(self):
        return self._entity_type

    def __getattr__(self, name):
        return self._kwargs.get(name)


class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities = []
        self._by_type = {}

    def create_entity(self, entity_type, *args, **kwargs):
        entity = MockIfcEntity(entity_type, **kwargs)
        self.entities.append(entity)

        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)

        return entity

    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])


class MockIfcGuid:
    """Mock для ifc.guid"""
    @staticmethod
    def new():
        return 'mock_guid_123'


class MockIfcOpenshell:
    """Mock для ifcopenshell"""
    def __init__(self):
        self.guid = MockIfcGuid()


class TestMaterialManager:
    """Тесты для MaterialManager"""

    def test_create_material(self):
        """MaterialManager должен создавать IfcMaterial"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        material = manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')

        assert material is not None
        assert material.is_a() == 'IfcMaterial'
        assert material.Name == '09Г2С ГОСТ 19281-2014'
        assert material.Category == 'Steel'

    def test_create_material_caching(self):
        """MaterialManager должен кэшировать материалы"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал дважды с одинаковым именем
        mat1 = manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')
        mat2 = manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')

        # Должен вернуться тот же самый объект из кэша
        assert mat1 is mat2
        assert manager.get_cached_materials_count() == 1

    def test_get_material(self):
        """MaterialManager должен возвращать материал из кэша"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал
        manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')

        # Получаем из кэша
        material = manager.get_material('09Г2С ГОСТ 19281-2014')

        assert material is not None
        assert material.Name == '09Г2С ГОСТ 19281-2014'

    def test_get_material_not_found(self):
        """MaterialManager должен возвращать None для несуществующего материала"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        material = manager.get_material('NonExistent')

        assert material is None

    def test_create_material_list(self):
        """MaterialManager должен создавать IfcMaterialList"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём несколько материалов
        mat1 = manager.create_material('Material1', category='Steel')
        mat2 = manager.create_material('Material2', category='Steel')

        # Создаём список материалов
        material_list = manager.create_material_list([mat1, mat2])

        assert material_list is not None
        assert material_list.is_a() == 'IfcMaterialList'
        assert len(material_list.Materials) == 2

    def test_associate_material(self):
        """MaterialManager должен создавать IfcRelAssociatesMaterial"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал
        material = manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')

        # Создаём тестовую сущность
        entity = mock_ifc.create_entity('IfcMechanicalFastenerType', Name='TestType')

        # Ассоциируем материал
        rel = manager.associate_material(entity, material)

        assert rel is not None
        assert rel.is_a() == 'IfcRelAssociatesMaterial'
        assert len(rel.RelatedObjects) == 1
        assert rel.RelatedObjects[0] is entity
        assert rel.RelatingMaterial is material

    def test_create_multiple_materials(self):
        """MaterialManager должен создавать разные материалы"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        mat1 = manager.create_material('09Г2С ГОСТ 19281-2014', category='Steel')
        mat2 = manager.create_material('ВСт3пс2 ГОСТ 535-88', category='Steel')
        mat3 = manager.create_material('10Г2 ГОСТ 19281-2014', category='Steel')

        assert mat1 is not mat2
        assert mat2 is not mat3
        assert mat1 is not mat3
        assert manager.get_cached_materials_count() == 3


class TestGetMaterialName:
    """Тесты для функции get_material_name"""

    def test_get_material_name_09g2s(self):
        """Функция должна возвращать имя в формате '09Г2С ГОСТ 19281-2014'"""
        from gost_data import get_material_name

        result = get_material_name('09Г2С')
        assert result == '09Г2С ГОСТ 19281-2014'

    def test_get_material_name_vst3ps2(self):
        """Функция должна возвращать имя в формате 'ВСт3пс2 ГОСТ 535-88'"""
        from gost_data import get_material_name

        result = get_material_name('ВСт3пс2')
        assert result == 'ВСт3пс2 ГОСТ 535-88'

    def test_get_material_name_10g2(self):
        """Функция должна возвращать имя в формате '10Г2 ГОСТ 19281-2014'"""
        from gost_data import get_material_name

        result = get_material_name('10Г2')
        assert result == '10Г2 ГОСТ 19281-2014'

    def test_get_material_name_unknown(self):
        """Функция должна возвращать исходное имя для неизвестного материала"""
        from gost_data import get_material_name

        result = get_material_name('UnknownMaterial')
        assert result == 'UnknownMaterial'
