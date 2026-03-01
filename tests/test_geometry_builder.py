"""
Тесты для geometry_builder.py - построение IFC геометрии
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
        # Поддержка как positional, так и keyword аргументов
        # Для IfcLineIndex и IfcArcIndex первый аргумент - список индексов
        if entity_type in ['IfcLineIndex', 'IfcArcIndex'] and args:
            entity = MockIfcEntity(entity_type, Indices=args[0])
        else:
            entity = MockIfcEntity(entity_type, *args, **kwargs)
        self.entities.append(entity)
        
        if entity_type not in self._by_type:
            self._by_type[entity_type] = []
        self._by_type[entity_type].append(entity)
        
        return entity
    
    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])


class TestGeometryBuilderInit:
    """Тесты инициализации GeometryBuilder"""

    def test_geometry_builder_init(self):
        """GeometryBuilder должен инициализироваться с ifc_doc"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        assert builder.ifc is mock_ifc
        assert builder._context is None


class TestToFloatList:
    """Тесты to_float_list"""

    def test_to_float_list_with_integers(self):
        """to_float_list должен конвертировать integers в floats"""
        from geometry_builder import GeometryBuilder
        
        result = GeometryBuilder.to_float_list([1, 2, 3])
        
        assert result == [1.0, 2.0, 3.0]
        assert all(isinstance(x, float) for x in result)

    def test_to_float_list_with_floats(self):
        """to_float_list должен работать с floats"""
        from geometry_builder import GeometryBuilder
        
        result = GeometryBuilder.to_float_list([1.5, 2.5, 3.5])
        
        assert result == [1.5, 2.5, 3.5]


class TestCreateLine:
    """Тесты create_line"""

    def test_create_line_creates_polyline(self):
        """create_line должен создавать IfcPolyline"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_line([0, 0, 0], [10, 10, 10])
        
        assert result is not None
        assert result.is_a() == 'IfcPolyline'


class TestCreateCompositeCurveStud:
    """Тесты create_composite_curve_stud"""

    def test_create_curve_type_1_1_indexed_polycurve(self):
        """Для типа 1.1 должен создаваться IfcIndexedPolyCurve"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_composite_curve_stud('1.1', 20, 800, 1)
        
        assert result is not None
        # Для типа 1.1 используется IfcIndexedPolyCurve (BlenderBIM подход)
        assert result.is_a() == 'IfcIndexedPolyCurve'
        # Проверка, что Segments содержит list entity instances
        assert hasattr(result, 'Segments')
        assert len(result.Segments) == 3  # линия + дуга + линия
        # Проверка что сегменты - это entity instances
        for seg in result.Segments:
            assert hasattr(seg, 'is_a') or isinstance(seg, MockIfcEntity)

    def test_create_curve_type_2_1_composite_curve(self):
        """Для типа 2.1 должен создаваться IfcCompositeCurve"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_composite_curve_stud('2.1', 20, 800, 1)
        
        assert result is not None
        assert result.is_a() == 'IfcCompositeCurve'

    def test_create_curve_type_5_composite_curve(self):
        """Для типа 5 должен создаваться IfcCompositeCurve"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_composite_curve_stud('5', 20, 800, 1)
        
        assert result is not None
        assert result.is_a() == 'IfcCompositeCurve'


class TestCreateSweptDiskSolid:
    """Тесты create_swept_disk_solid"""

    def test_create_swept_disk_solid(self):
        """create_swept_disk_solid должен создавать IfcSweptDiskSolid"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        # Сначала создадим кривую
        curve = builder.create_composite_curve_stud('2.1', 20, 800, 1)
        
        result = builder.create_swept_disk_solid(curve, 10.0)
        
        assert result is not None
        assert result.is_a() == 'IfcSweptDiskSolid'


class TestCreateStraightStudSolid:
    """Тесты create_straight_stud_solid"""

    def test_create_straight_stud_solid(self):
        """create_straight_stud_solid должен создавать геометрию прямой шпильки"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_straight_stud_solid(20, 800)
        
        assert result is not None
        assert result.is_a() == 'IfcShapeRepresentation'


class TestCreateBentStudSolid:
    """Тесты create_bent_stud_solid"""

    def test_create_bent_stud_solid_type_1_1(self):
        """create_bent_stud_solid должен создавать геометрию изогнутой шпильки 1.1"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_bent_stud_solid('1.1', 20, 800, 1)
        
        assert result is not None
        assert result.is_a() == 'IfcShapeRepresentation'

    def test_create_bent_stud_solid_type_1_2(self):
        """create_bent_stud_solid должен создавать геометрию изогнутой шпильки 1.2"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_bent_stud_solid('1.2', 20, 800, 1)
        
        assert result is not None
        assert result.is_a() == 'IfcShapeRepresentation'


class TestCreateNutSolid:
    """Тесты create_nut_solid"""

    def test_create_nut_solid(self):
        """create_nut_solid должен создавать геометрию гайки"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_nut_solid(20, 18)
        
        assert result is not None
        assert result.is_a() == 'IfcShapeRepresentation'


class TestCreateWasherSolid:
    """Тесты create_washer_solid"""

    def test_create_washer_solid(self):
        """create_washer_solid должен создавать геометрию шайбы"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        result = builder.create_washer_solid(20, 45, 8)
        
        assert result is not None
        assert result.is_a() == 'IfcShapeRepresentation'


class TestAssociateRepresentation:
    """Тесты associate_representation"""

    def test_associate_representation_creates_map(self):
        """associate_representation должен создавать RepresentationMap"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        # Создадим тип и representation
        product_type = mock_ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId='test',
            Name='TestType',
            RepresentationMaps=None
        )
        shape_rep = mock_ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=None,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[]
        )
        
        builder.associate_representation(product_type, shape_rep)
        
        # Проверим, что RepresentationMaps был создан
        assert product_type.RepresentationMaps is not None
        assert len(product_type.RepresentationMaps) > 0
    
    def test_associate_representation_handles_existing_maps(self):
        """associate_representation должен добавлять к существующим RepresentationMaps"""
        from geometry_builder import GeometryBuilder
        
        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)
        
        # Создадим тип с существующим RepresentationMaps
        existing_map = mock_ifc.create_entity('IfcRepresentationMap',
            MappingOrigin=None,
            MappedRepresentation=None
        )
        product_type = mock_ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId='test',
            Name='TestType',
            RepresentationMaps=[existing_map]
        )
        shape_rep = mock_ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=None,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[]
        )
        
        builder.associate_representation(product_type, shape_rep)
        
        # Проверим, что RepresentationMaps был добавлен
        assert len(product_type.RepresentationMaps) == 2
