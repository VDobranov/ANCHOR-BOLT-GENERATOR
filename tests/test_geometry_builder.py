"""
Тесты для geometry_builder.py - построение IFC геометрии
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
        if self._entity_type in ["IfcCircle", "IfcPolyline", "IfcCompositeCurve"]:
            return 2
        return None


class MockIfcDoc:
    """Mock для IFC документа"""

    def __init__(self):
        self.entities = []
        self._by_type = {}
        self.schema = "IFC4"  # Для совместимости с shape_builder

    def create_entity(self, entity_type, *args, **kwargs):
        if entity_type in ["IfcLineIndex", "IfcArcIndex"] and args:
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


class TestGeometryBuilderInit:
    """Тесты инициализации GeometryBuilder"""

    def test_geometry_builder_init(self):
        """GeometryBuilder должен инициализироваться с ifc_doc"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        assert builder.ifc is mock_ifc
        assert builder._context is None


class TestCreateLine:
    """Тесты create_line"""

    def test_create_line_creates_polyline(self):
        """create_line должен создавать IfcIndexedPolyCurve через shape_builder"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        result = builder.create_line([0, 0, 0], [10, 10, 10])

        assert result is not None
        # shape_builder создаёт IfcIndexedPolyCurve
        assert result.is_a() == "IfcIndexedPolyCurve"


class TestCreateCompositeCurveStud:
    """Тесты create_composite_curve_stud"""

    def test_create_curve_type_1_1_indexed_polycurve(self):
        """Для типа 1.1 должен создаваться IfcIndexedPolyCurve с дугой"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        result = builder.create_composite_curve_stud("1.1", 20, 800)

        assert result is not None
        # Для типа 1.1 используется IfcIndexedPolyCurve (BlenderBIM подход)
        assert result.is_a() == "IfcIndexedPolyCurve"
        # Проверка, что Segments содержит list entity instances
        assert hasattr(result, "Segments")
        assert len(result.Segments) == 3  # линия + дуга + линия
        # Проверка что сегменты - это entity instances
        for seg in result.Segments:
            assert hasattr(seg, "is_a") or isinstance(seg, MockIfcEntity)

    def test_create_curve_type_2_1_indexed_polycurve(self):
        """Для типа 2.1 должен создаваться IfcIndexedPolyCurve (прямая линия)"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        result = builder.create_composite_curve_stud("2.1", 20, 800)

        assert result is not None
        # Теперь используется IfcIndexedPolyCurve вместо IfcCompositeCurve
        assert result.is_a() == "IfcIndexedPolyCurve"

    def test_create_curve_type_5_indexed_polycurve(self):
        """Для типа 5 должен создаваться IfcIndexedPolyCurve (прямая линия)"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        result = builder.create_composite_curve_stud("5", 20, 800)

        assert result is not None
        # Теперь используется IfcIndexedPolyCurve вместо IfcCompositeCurve
        assert result.is_a() == "IfcIndexedPolyCurve"


class TestCreateSweptDiskSolid:
    """Тесты create_swept_disk_solid"""

    def test_create_swept_disk_solid(self):
        """create_swept_disk_solid должен вызывать builder.create_swept_disk_solid"""
        from unittest.mock import patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        with patch.object(builder.builder, "create_swept_disk_solid") as mock_method:
            mock_method.return_value = MockIfcEntity("IfcSweptDiskSolid")
            curve = MockIfcEntity("IfcIndexedPolyCurve")
            result = builder.create_swept_disk_solid(curve, 10.0)

            assert mock_method.called
            assert result is not None


class TestCreateStraightStudSolid:
    """Тесты create_straight_stud_solid"""

    def test_create_straight_stud_solid(self):
        """create_straight_stud_solid должен вызывать builder.circle, profile, extrude"""
        from unittest.mock import MagicMock, patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        mock_context = MagicMock()
        mock_context.ContextIdentifier = "Body"

        with patch.object(builder, "_get_context", return_value=mock_context), patch.object(
            builder.builder, "circle"
        ) as mock_circle, patch.object(builder.builder, "profile") as mock_profile, patch.object(
            builder.builder, "extrude"
        ) as mock_extrude, patch.object(
            builder, "_create_shape_representation"
        ) as mock_repr:

            mock_circle.return_value = MockIfcEntity("IfcCircle")
            mock_profile.return_value = MockIfcEntity("IfcArbitraryProfileDefWithVoids")
            mock_extrude.return_value = MockIfcEntity("IfcExtrudedAreaSolid")
            mock_repr.return_value = MockIfcEntity("IfcShapeRepresentation")

            result = builder.create_straight_stud_solid(20, 800)

            assert mock_circle.called
            assert mock_profile.called
            assert mock_extrude.called
            assert result is not None


class TestCreateBentStudSolid:
    """Тесты create_bent_stud_solid"""

    def test_create_bent_stud_solid_type_1_1(self):
        """create_bent_stud_solid должен создавать геометрию изогнутой шпильки 1.1"""
        from unittest.mock import MagicMock, patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        mock_context = MagicMock()
        mock_context.ContextIdentifier = "Body"

        with patch.object(builder, "_get_context", return_value=mock_context), patch.object(
            builder.builder, "create_swept_disk_solid"
        ) as mock_swept, patch.object(builder, "_create_shape_representation") as mock_repr:
            mock_swept.return_value = MockIfcEntity("IfcSweptDiskSolid")
            mock_repr.return_value = MockIfcEntity("IfcShapeRepresentation")
            result = builder.create_bent_stud_solid("1.1", 20, 800)

            assert mock_swept.called
            assert result is not None

    def test_create_bent_stud_solid_type_1_2(self):
        """create_bent_stud_solid должен создавать геометрию изогнутой шпильки 1.2"""
        from unittest.mock import MagicMock, patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        mock_context = MagicMock()
        mock_context.ContextIdentifier = "Body"

        with patch.object(builder, "_get_context", return_value=mock_context), patch.object(
            builder.builder, "create_swept_disk_solid"
        ) as mock_swept, patch.object(builder, "_create_shape_representation") as mock_repr:
            mock_swept.return_value = MockIfcEntity("IfcSweptDiskSolid")
            mock_repr.return_value = MockIfcEntity("IfcShapeRepresentation")
            result = builder.create_bent_stud_solid("1.2", 20, 800)

            assert mock_swept.called
            assert result is not None


class TestCreateNutSolid:
    """Тесты create_nut_solid"""

    def test_create_nut_solid(self):
        """create_nut_solid должен вызывать builder.polyline, circle, profile, extrude"""
        from unittest.mock import MagicMock, patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        mock_context = MagicMock()
        mock_context.ContextIdentifier = "Body"

        with patch.object(builder, "_get_context", return_value=mock_context), patch.object(
            builder.builder, "polyline"
        ) as mock_polyline, patch.object(builder.builder, "circle") as mock_circle, patch.object(
            builder.builder, "profile"
        ) as mock_profile, patch.object(
            builder.builder, "extrude"
        ) as mock_extrude, patch.object(
            builder, "_create_shape_representation"
        ) as mock_repr:

            mock_polyline.return_value = MockIfcEntity("IfcIndexedPolyCurve")
            mock_circle.return_value = MockIfcEntity("IfcCircle")
            mock_profile.return_value = MockIfcEntity("IfcArbitraryProfileDefWithVoids")
            mock_extrude.return_value = MockIfcEntity("IfcExtrudedAreaSolid")
            mock_repr.return_value = MockIfcEntity("IfcShapeRepresentation")

            result = builder.create_nut_solid(20, 18)

            assert mock_polyline.called
            assert mock_circle.called
            assert mock_profile.called
            assert mock_extrude.called
            assert result is not None


class TestCreateWasherSolid:
    """Тесты create_washer_solid"""

    def test_create_washer_solid(self):
        """create_washer_solid должен вызывать builder.circle, profile, extrude"""
        from unittest.mock import MagicMock, patch

        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        mock_context = MagicMock()
        mock_context.ContextIdentifier = "Body"

        with patch.object(builder, "_get_context", return_value=mock_context), patch.object(
            builder.builder, "circle"
        ) as mock_circle, patch.object(builder.builder, "profile") as mock_profile, patch.object(
            builder.builder, "extrude"
        ) as mock_extrude, patch.object(
            builder, "_create_shape_representation"
        ) as mock_repr:

            mock_circle.return_value = MockIfcEntity("IfcCircle")
            mock_profile.return_value = MockIfcEntity("IfcArbitraryProfileDefWithVoids")
            mock_extrude.return_value = MockIfcEntity("IfcExtrudedAreaSolid")
            mock_repr.return_value = MockIfcEntity("IfcShapeRepresentation")

            result = builder.create_washer_solid(20, 45, 8)

            assert mock_circle.called
            assert mock_profile.called
            assert mock_extrude.called
            assert result is not None


class TestAssociateRepresentation:
    """Тесты associate_representation"""

    def test_associate_representation_creates_map(self):
        """associate_representation должен создавать RepresentationMap"""
        from geometry_builder import GeometryBuilder

        mock_ifc = MockIfcDoc()
        builder = GeometryBuilder(mock_ifc)

        # Создадим тип и representation
        product_type = mock_ifc.create_entity(
            "IfcMechanicalFastenerType", GlobalId="test", Name="TestType", RepresentationMaps=None
        )
        shape_rep = mock_ifc.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=None,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[],
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
        existing_map = mock_ifc.create_entity(
            "IfcRepresentationMap", MappingOrigin=None, MappedRepresentation=None
        )
        product_type = mock_ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId="test",
            Name="TestType",
            RepresentationMaps=[existing_map],
        )
        shape_rep = mock_ifc.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=None,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[],
        )

        builder.associate_representation(product_type, shape_rep)

        # Проверим, что RepresentationMaps был добавлен
        assert len(product_type.RepresentationMaps) == 2
