"""
Тесты для type_factory.py - фабрика и кэширование типов
"""
import pytest


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


class TestTypeFactoryInit:
    """Тесты инициализации TypeFactory"""

    def test_type_factory_init(self):
        """TypeFactory должен инициализироваться с ifc_doc"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        assert factory.ifc is mock_ifc
        assert factory.types_cache == {}
        assert factory.builder is not None


class TestGetOrCreateStudType:
    """Тесты get_or_create_stud_type"""

    def test_get_or_create_stud_type_creates_entity(self):
        """get_or_create_stud_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        
        assert result is not None
        assert result.is_a() == 'IfcMechanicalFastenerType'

    def test_get_or_create_stud_type_name_format(self):
        """Имя типа должно следовать формату Stud_M{diameter}x{length}_{type}_exec{execution}"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        
        assert 'Stud_M20x800' in result.Name
        assert '1.1' in result.Name
        assert 'exec1' in result.Name

    def test_get_or_create_stud_type_caching(self):
        """get_or_create_stud_type должен кэшировать результаты"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        # Первый вызов
        result1 = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        # Второй вызов с теми же параметрами
        result2 = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        
        # Должен вернуться тот же объект из кэша
        assert result1 is result2

    def test_get_or_create_stud_type_different_params_not_cached(self):
        """Разные параметры должны создавать разные типы"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result1 = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        result2 = factory.get_or_create_stud_type('1.1', 1, 20, 1000, '09Г2С')  # Другая длина
        
        assert result1 is not result2
        assert result1.Name != result2.Name


class TestGetOrCreateNutType:
    """Тесты get_or_create_nut_type"""

    def test_get_or_create_nut_type_creates_entity(self):
        """get_or_create_nut_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_nut_type(20, '09Г2С')
        
        assert result is not None
        assert result.is_a() == 'IfcMechanicalFastenerType'

    def test_get_or_create_nut_type_name_format(self):
        """Имя типа должно следовать формату Nut_M{diameter}_H{height}"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_nut_type(20, '09Г2С')
        
        assert 'Nut_M20' in result.Name
        assert 'H' in result.Name

    def test_get_or_create_nut_type_caching(self):
        """get_or_create_nut_type должен кэшировать результаты"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result1 = factory.get_or_create_nut_type(20, '09Г2С')
        result2 = factory.get_or_create_nut_type(20, '09Г2С')
        
        assert result1 is result2

    def test_get_or_create_nut_type_different_diameter_not_cached(self):
        """Разные диаметры должны создавать разные типы"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result1 = factory.get_or_create_nut_type(20, '09Г2С')
        result2 = factory.get_or_create_nut_type(24, '09Г2С')
        
        assert result1 is not result2


class TestGetOrCreateWasherType:
    """Тесты get_or_create_washer_type"""

    def test_get_or_create_washer_type_creates_entity(self):
        """get_or_create_washer_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_washer_type(20, '09Г2С')
        
        assert result is not None
        assert result.is_a() == 'IfcMechanicalFastenerType'

    def test_get_or_create_washer_type_name_format(self):
        """Имя типа должно следовать формату Washer_M{diameter}_OD{outer_d}"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_washer_type(20, '09Г2С')
        
        assert 'Washer_M20' in result.Name
        assert 'OD' in result.Name

    def test_get_or_create_washer_type_caching(self):
        """get_or_create_washer_type должен кэшировать результаты"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result1 = factory.get_or_create_washer_type(20, '09Г2С')
        result2 = factory.get_or_create_washer_type(20, '09Г2С')
        
        assert result1 is result2


class TestGetOrCreateAssemblyType:
    """Тесты get_or_create_assembly_type"""

    def test_get_or_create_assembly_type_creates_entity(self):
        """get_or_create_assembly_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_assembly_type('1.1', 20, '09Г2С')
        
        assert result is not None
        assert result.is_a() == 'IfcMechanicalFastenerType'

    def test_get_or_create_assembly_type_name_format(self):
        """Имя типа должно следовать формату AnchorBoltAssembly_{type}_M{diameter}_{material}"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result = factory.get_or_create_assembly_type('1.1', 20, '09Г2С')
        
        assert 'AnchorBoltAssembly_1.1_M20' in result.Name
        assert '09Г2С' in result.Name

    def test_get_or_create_assembly_type_caching(self):
        """get_or_create_assembly_type должен кэшировать результаты"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        result1 = factory.get_or_create_assembly_type('1.1', 20, '09Г2С')
        result2 = factory.get_or_create_assembly_type('1.1', 20, '09Г2С')
        
        assert result1 is result2


class TestGetCachedTypesCount:
    """Тесты get_cached_types_count"""

    def test_get_cached_types_count_empty(self):
        """get_cached_types_count должен возвращать 0 для пустого кэша"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        assert factory.get_cached_types_count() == 0

    def test_get_cached_types_count_after_adding(self):
        """get_cached_types_count должен увеличиваться после добавления типов"""
        from type_factory import TypeFactory
        
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)
        
        factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
        factory.get_or_create_nut_type(20, '09Г2С')
        factory.get_or_create_washer_type(20, '09Г2С')
        
        assert factory.get_cached_types_count() == 3
