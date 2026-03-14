"""
Тесты для type_factory.py - фабрика и кэширование типов
"""

import pytest


class MockIfcEntity:
    """Mock для IFC сущности"""

    def __init__(self, entity_type, *args, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs
        # Обработка positional аргументов
        if args:
            for i, arg in enumerate(args):
                setattr(self, f"arg{i}", arg)
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Установим RepresentationMaps по умолчанию для типов
        if entity_type == "IfcMechanicalFastenerType":
            if not hasattr(self, "RepresentationMaps"):
                self.RepresentationMaps = None

    def is_a(self):
        return self._entity_type

    def __getattr__(self, name):
        return self._kwargs.get(name)

    @property
    def dim(self):
        """Определение размерности для кривых и точек"""
        if "3D" in self._entity_type:
            return 3
        if "2D" in self._entity_type:
            return 2
        if self._entity_type == "IfcIndexedPolyCurve":
            points = self._kwargs.get("Points")
            if points and hasattr(points, "dim"):
                return points.dim
            return 3
        if self._entity_type in ["IfcCircle", "IfcPolyline"]:
            return 2
        return None


class MockIfcDoc:
    """Mock для IFC документа с поддержкой IfcReal и IfcText"""

    def __init__(self):
        self.entities = []
        self._by_type = {}
        self.schema = "IFC4"  # Для совместимости с shape_builder

    def create_entity(self, entity_type, *args, **kwargs):
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

    def __getattr__(self, name):
        # Динамическая поддержка методов типа createIfcIndexedPolyCurve
        if name.startswith("create"):
            entity_type = name[6:]

            def create_method(*args, **kwargs):
                return self.create_entity(entity_type, *args, **kwargs)

            return create_method
        raise AttributeError(f"'MockIfcDoc' object has no attribute '{name}'")

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
        from unittest.mock import MagicMock, patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastenerType"

    def test_get_or_create_stud_type_name_format(self):
        """Имя типа должно следовать формату Stud_M{diameter}x{length}_{type}"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")

        assert "Stud_M20x800" in result.Name
        assert "1.1" in result.Name

    def test_get_or_create_stud_type_caching(self):
        """get_or_create_stud_type должен кэшировать результаты"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            # Первый вызов
            result1 = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")
            # Второй вызов с теми же параметрами
            result2 = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")

        # Должен вернуться тот же объект из кэша
        assert result1 is result2

    def test_get_or_create_stud_type_different_params_not_cached(self):
        """Разные параметры должны создавать разные типы"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            result1 = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")
            result2 = factory.get_or_create_stud_type("1.1", 20, 1000, "09Г2С")  # Другая длина

        assert result1 is not result2
        assert result1.Name != result2.Name


class TestGetOrCreateNutType:
    """Тесты get_or_create_nut_type"""

    def test_get_or_create_nut_type_creates_entity(self):
        """get_or_create_nut_type должен создавать IfcMechanicalFastenerType"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_nut_type(20, "09Г2С")

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastenerType"

    def test_get_or_create_nut_type_name_format(self):
        """Имя типа должно следовать формату Nut_M{diameter}_H{height}"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_nut_type(20, "09Г2С")

        assert "Nut_M20" in result.Name
        assert "H" in result.Name

    def test_get_or_create_nut_type_caching(self):
        """get_or_create_nut_type должен кэшировать результаты"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            result1 = factory.get_or_create_nut_type(20, "09Г2С")
            result2 = factory.get_or_create_nut_type(20, "09Г2С")

        assert result1 is result2

    def test_get_or_create_nut_type_different_diameter_not_cached(self):
        """Разные диаметры должны создавать разные типы"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            result1 = factory.get_or_create_nut_type(20, "09Г2С")
            result2 = factory.get_or_create_nut_type(24, "09Г2С")

        assert result1 is not result2


class TestGetOrCreateWasherType:
    """Тесты get_or_create_washer_type"""

    def test_get_or_create_washer_type_creates_entity(self):
        """get_or_create_washer_type должен создавать IfcMechanicalFastenerType"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_washer_type(20, "09Г2С")

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastenerType"

    def test_get_or_create_washer_type_name_format(self):
        """Имя типа должно следовать формату Washer_M{diameter}_OD{outer_d}"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):

            result = factory.get_or_create_washer_type(20, "09Г2С")

        assert "Washer_M20" in result.Name
        assert "OD" in result.Name

    def test_get_or_create_washer_type_caching(self):
        """get_or_create_washer_type должен кэшировать результаты"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            result1 = factory.get_or_create_washer_type(20, "09Г2С")
            result2 = factory.get_or_create_washer_type(20, "09Г2С")

        assert result1 is result2


class TestGetOrCreateAssemblyType:
    """Тесты get_or_create_assembly_type"""

    def test_get_or_create_assembly_type_creates_entity(self):
        """get_or_create_assembly_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        result = factory.get_or_create_assembly_type("1.1", 20, "09Г2С")

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastenerType"

    def test_get_or_create_assembly_type_name_format(self):
        """Имя типа должно следовать формату AnchorBoltAssembly_{type}_M{diameter}_{material}"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        result = factory.get_or_create_assembly_type("1.1", 20, "09Г2С")

        assert "AnchorBoltAssembly_1.1_M20" in result.Name
        assert "09Г2С" in result.Name

    def test_get_or_create_assembly_type_caching(self):
        """get_or_create_assembly_type должен кэшировать результаты"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        result1 = factory.get_or_create_assembly_type("1.1", 20, "09Г2С")
        result2 = factory.get_or_create_assembly_type("1.1", 20, "09Г2С")

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
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")
            factory.get_or_create_nut_type(20, "09Г2С")
            factory.get_or_create_washer_type(20, "09Г2С")

        assert factory.get_cached_types_count() == 3


class TestMaterialAssociation:
    """Тесты для проверки ассоциации материалов"""

    def test_stud_type_creates_material(self):
        """get_or_create_stud_type должен создавать IfcMaterial"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")

        # Проверяем, что был создан IfcMaterial
        materials = mock_ifc.by_type("IfcMaterial")
        assert len(materials) == 1
        assert materials[0].Name == "09Г2С ГОСТ 19281-2014"
        assert materials[0].Category == "Steel"

    def test_stud_type_creates_rel_associates_material(self):
        """get_or_create_stud_type должен создавать IfcRelAssociatesMaterial"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            stud_type = factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")

        # Проверяем, что была создана связь
        rel_associates = mock_ifc.by_type("IfcRelAssociatesMaterial")
        assert len(rel_associates) == 1
        rel = rel_associates[0]
        assert len(rel.RelatedObjects) == 1
        assert rel.RelatedObjects[0] is stud_type

    def test_nut_type_creates_material(self):
        """get_or_create_nut_type должен создавать IfcMaterial и связь"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_nut_type(20, "09Г2С")

        materials = mock_ifc.by_type("IfcMaterial")
        rel_associates = mock_ifc.by_type("IfcRelAssociatesMaterial")

        assert len(materials) == 1
        assert materials[0].Name == "09Г2С ГОСТ 19281-2014"
        assert len(rel_associates) == 1

    def test_washer_type_creates_material(self):
        """get_or_create_washer_type должен создавать IfcMaterial и связь"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_washer_type(20, "09Г2С")

        materials = mock_ifc.by_type("IfcMaterial")
        rel_associates = mock_ifc.by_type("IfcRelAssociatesMaterial")

        assert len(materials) == 1
        assert materials[0].Name == "09Г2С ГОСТ 19281-2014"
        assert len(rel_associates) == 1

    def test_same_material_cached(self):
        """Одинаковые материалы должны кэшироваться"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")
            factory.get_or_create_nut_type(20, "09Г2С")

        # Должен быть создан только один материал
        materials = mock_ifc.by_type("IfcMaterial")
        assert len(materials) == 1

    def test_different_materials(self):
        """Разные материалы должны создаваться отдельно"""
        from unittest.mock import patch

        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")
        with patch.object(
            factory.builder.builder, "polyline", return_value=MockIfcEntity("IfcIndexedPolyCurve")
        ), patch.object(
            factory.builder.builder,
            "create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch.object(
            factory.builder.builder, "circle", return_value=MockIfcEntity("IfcCircle")
        ), patch.object(
            factory.builder.builder,
            "profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch.object(
            factory.builder.builder, "extrude", return_value=MockIfcEntity("IfcExtrudedAreaSolid")
        ), patch.object(
            factory.builder.builder, "get_representation", return_value=mock_shape_rep
        ):
            factory.get_or_create_stud_type("1.1", 20, 800, "09Г2С")
            factory.get_or_create_stud_type("1.1", 20, 800, "ВСт3пс2")

        # Должны быть созданы два разных материала
        materials = mock_ifc.by_type("IfcMaterial")
        assert len(materials) == 2
