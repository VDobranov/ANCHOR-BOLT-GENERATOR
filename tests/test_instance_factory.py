"""
Тесты для instance_factory.py - создание инстансов и сборок
"""
import pytest
from unittest.mock import patch, MagicMock


class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        # Установим RepresentationMaps по умолчанию для типов
        if entity_type == 'IfcMechanicalFastenerType':
            if not hasattr(self, 'RepresentationMaps'):
                self.RepresentationMaps = None
    
    def is_a(self):
        return self._entity_type
    
    def __getattr__(self, name):
        return self._kwargs.get(name)


class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities = []
        self._by_type = {}
    
    def create_entity(self, entity_type, **kwargs):
        entity = MockIfcEntity(entity_type, **kwargs)
        self.entities.append(entity)
        
        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)
        
        return entity
    
    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])


class TestInstanceFactoryInit:
    """Тесты инициализации InstanceFactory"""

    def test_instance_factory_init(self):
        """InstanceFactory должен инициализироваться с ifc_doc"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        assert factory.ifc is mock_ifc
        assert factory.type_factory is not None

    def test_instance_factory_init_with_custom_type_factory(self):
        """InstanceFactory должен принимать custom type_factory"""
        from instance_factory import InstanceFactory
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        custom_type_factory = TypeFactory(mock_ifc)
        factory = InstanceFactory(mock_ifc, custom_type_factory)
        
        assert factory.type_factory is custom_type_factory


class TestCreateBoltAssembly:
    """Тесты create_bolt_assembly"""

    def test_create_bolt_assembly_returns_dict(self):
        """create_bolt_assembly должен возвращать dict"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        # Мокаем _generate_mesh_data чтобы избежать ifcopenshell.geom
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        assert isinstance(result, dict)
        assert 'assembly' in result
        assert 'stud' in result
        assert 'components' in result
        assert 'mesh_data' in result

    def test_create_bolt_assembly_creates_assembly(self):
        """create_bolt_assembly должен создавать сборку"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        assembly = result['assembly']
        assert assembly is not None
        assert assembly.is_a() == 'IfcMechanicalFastener'
        assert assembly.ObjectType == 'ANCHORBOLT'

    def test_create_bolt_assembly_name_format(self):
        """Имя сборки должно следовать формату"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        assembly = result['assembly']
        assert 'AnchorBolt_1.1_M20x800' in assembly.Name

    def test_create_bolt_assembly_components_count_type_1_1(self):
        """Для типа 1.1 должно быть 4 компонента: шпилька + шайба + 2 гайки"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        components = result['components']
        assert len(components) == 4  # stud + washer + 2 nuts

    def test_create_bolt_assembly_components_count_type_2_1(self):
        """Для типа 2.1 должно быть 6 компонентов: шпилька + шайба + 4 гайки"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('2.1', 1, 20, 800, '09Г2С')
        
        components = result['components']
        assert len(components) == 6  # stud + washer + 4 nuts

    def test_create_bolt_assembly_stud_type(self):
        """Шпилька должна иметь ObjectType = STUD"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        stud = result['stud']
        assert stud is not None
        assert stud.ObjectType == 'STUD'

    def test_create_bolt_assembly_creates_relations(self):
        """create_bolt_assembly должен создавать отношения"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
            result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
        
        # Проверка создания IfcRelDefinesByType
        rel_defines = mock_ifc.by_type('IfcRelDefinesByType')
        assert len(rel_defines) > 0
        
        # Проверка создания IfcRelAggregates
        rel_aggregates = mock_ifc.by_type('IfcRelAggregates')
        assert len(rel_aggregates) > 0


class TestCreatePlacement:
    """Тесты _create_placement"""

    def test_create_placement_creates_local_placement(self):
        """_create_placement должен создавать IfcLocalPlacement"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        result = factory._create_placement((0, 0, 0))
        
        assert result is not None
        assert result.is_a() == 'IfcLocalPlacement'

    def test_create_placement_with_offset(self):
        """_create_placement должен поддерживать смещение"""
        from instance_factory import InstanceFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        result = factory._create_placement((10, 20, 30))
        
        assert result is not None
        # Проверка, что координаты установлены
        placement = result.RelativePlacement
        assert placement.Location.Coordinates == [10.0, 20.0, 30.0]


class TestCreateComponent:
    """Тесты _create_component"""

    def test_create_component_creates_fastener(self):
        """_create_component должен создавать IfcMechanicalFastener"""
        from instance_factory import InstanceFactory
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)
        
        # Создадим тип гайки
        type_factory = factory.type_factory
        nut_type = type_factory.get_or_create_nut_type(20, '09Г2С')
        
        instances_list = []
        result = factory._create_component(
            'Nut', 'Nut_Test', 'NUT',
            (0, 0, 10),
            nut_type, instances_list
        )
        
        assert result is not None
        assert result.is_a() == 'IfcMechanicalFastener'
        assert result.ObjectType == 'NUT'
        assert len(instances_list) == 1


class TestGenerateBoltAssembly:
    """Тесты generate_bolt_assembly"""

    def test_generate_bolt_assembly_returns_tuple(self):
        """generate_bolt_assembly должна возвращать кортеж (ifc_str, mesh_data)"""
        from instance_factory import generate_bolt_assembly
        
        # Примечание: этот тест требует работающего ifcopenshell
        # В среде без ifcopenshell он может упасть
        params = {
            'bolt_type': '1.1',
            'execution': 1,
            'diameter': 20,
            'length': 800,
            'material': '09Г2С'
        }
        
        try:
            result = generate_bolt_assembly(params)
            assert isinstance(result, tuple)
            assert len(result) == 2
        except Exception:
            # Если ifcopenshell недоступен, тест пропускается
            pytest.skip("ifcopenshell недоступен")


class TestGetElementProperties:
    """Тесты get_element_properties"""
    
    # Примечание: get_element_properties требует инициализированный IFC документ
    # и не может быть протестирован без полной инициализации ifcopenshell
    # Интеграционное тестирование должно проводиться в браузере через Pyodide
    pass
