"""
Тесты для type_factory.py - фабрика и кэширование типов
"""

from unittest.mock import patch

import pytest
from conftest import MockIfcDoc, MockIfcEntity


class TestTypeFactoryInit:
    """Тесты инициализации TypeFactory"""

    def test_type_factory_init(self, mock_ifc_api_run):
        """TypeFactory должен инициализироваться с ifc_doc"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        assert factory.ifc is mock_ifc
        assert factory.types_cache == {}
        assert factory.builder is not None


class TestGetOrCreateStudType:
    """Тесты get_or_create_stud_type"""

    def test_get_or_create_stud_type_creates_entity(self, mock_ifc_api_run):
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

    def test_get_or_create_stud_type_name_format(self, mock_ifc_api_run):
        """Имя типа должно следовать формату \"Шпилька {t}.М{d}×{L} {M} ГОСТ 24379.1-2012\" """

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

        assert result.Name == "Шпилька 1.М20×800 09Г2С ГОСТ 24379.1-2012"

    def test_get_or_create_stud_type_caching(self, mock_ifc_api_run):
        """get_or_create_stud_type должен кэшировать результаты"""

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

    def test_get_or_create_stud_type_different_params_not_cached(self, mock_ifc_api_run):
        """Разные параметры должны создавать разные типы"""

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

    def test_get_or_create_nut_type_creates_entity(self, mock_ifc_api_run):
        """get_or_create_nut_type должен создавать IfcMechanicalFastenerType"""

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

    def test_get_or_create_nut_type_name_format(self, mock_ifc_api_run):
        """Имя типа должно следовать формату \"Гайка М{d} ГОСТ 5915-70\" """

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

        assert result.Name == "Гайка М20 ГОСТ 5915-70"

    def test_get_or_create_nut_type_caching(self, mock_ifc_api_run):
        """get_or_create_nut_type должен кэшировать результаты"""

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

    def test_get_or_create_nut_type_different_diameter_not_cached(self, mock_ifc_api_run):
        """Разные диаметры должны создавать разные типы"""

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

    def test_get_or_create_washer_type_creates_entity(self, mock_ifc_api_run):
        """get_or_create_washer_type должен создавать IfcMechanicalFastenerType"""

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

    def test_get_or_create_washer_type_name_format(self, mock_ifc_api_run):
        """Имя типа должно следовать формату \"Шайба М{d} ГОСТ 24379.1-2012\" """

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

        assert result.Name == "Шайба М20 ГОСТ 24379.1-2012"

    def test_get_or_create_washer_type_caching(self, mock_ifc_api_run):
        """get_or_create_washer_type должен кэшировать результаты"""

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

    def test_get_or_create_assembly_type_creates_entity(self, mock_ifc_api_run):
        """get_or_create_assembly_type должен создавать IfcMechanicalFastenerType"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        # Используем IfcElementAssembly чтобы избежать ifcopenshell.api для Pset
        result = factory.get_or_create_assembly_type(
            "1.1", 20, 800, "09Г2С", assembly_class="IfcElementAssembly"
        )

        assert result is not None
        assert result.is_a() == "IfcElementAssemblyType"

    def test_get_or_create_assembly_type_name_format(self, mock_ifc_api_run):
        """Имя типа должно следовать формату "Болт {T}.М{d}×{L} {M} ГОСТ 24379.1-2012" """
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        # Используем IfcElementAssembly чтобы избежать ifcopenshell.api для Pset
        result = factory.get_or_create_assembly_type(
            "1.1", 20, 800, "09Г2С", assembly_class="IfcElementAssembly"
        )

        assert result.Name == "Болт 1.1.М20×800 09Г2С ГОСТ 24379.1-2012"

    def test_get_or_create_assembly_type_caching(self, mock_ifc_api_run):
        """get_or_create_assembly_type должен кэшировать результаты"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        # Используем IfcElementAssembly чтобы избежать ifcopenshell.api для Pset
        result1 = factory.get_or_create_assembly_type(
            "1.1", 20, 800, "09Г2С", assembly_class="IfcElementAssembly"
        )
        result2 = factory.get_or_create_assembly_type(
            "1.1", 20, 800, "09Г2С", assembly_class="IfcElementAssembly"
        )

        assert result1 is result2

    def test_get_or_create_assembly_type_with_pset(self, mock_ifc_api_run):
        """get_or_create_assembly_type должен добавлять Pset_MechanicalFastenerAnchorBolt"""
        from document_manager import IFCDocumentManager
        from type_factory import TypeFactory

        # Используем MockIfcDoc вместо реального документа
        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        result = factory.get_or_create_assembly_type("1.1", 20, 800, "09Г2С")

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastenerType"

        # Проверяем наличие Pset_MechanicalFastenerAnchorBolt
        psets = mock_ifc.by_type("IfcPropertySet")
        anchor_pset = None
        common_pset = None
        for pset in psets:
            if pset.Name == "Pset_MechanicalFastenerAnchorBolt":
                anchor_pset = pset
            elif pset.Name == "Pset_ElementComponentCommon":
                common_pset = pset

        # Проверяем Pset_MechanicalFastenerAnchorBolt
        assert anchor_pset is not None
        prop_names = [p.Name for p in anchor_pset.HasProperties]
        assert "AnchorBoltDiameter" in prop_names
        assert "AnchorBoltLength" in prop_names
        assert "AnchorBoltProtrusionLength" in prop_names
        assert "AnchorBoltThreadLength" in prop_names

        # Проверяем Pset_ElementComponentCommon
        assert common_pset is not None
        common_props = {p.Name: p.NominalValue.Value for p in common_pset.HasProperties}
        assert common_props.get("CorrosionTreatment") == "GALVANISED"
        assert common_props.get("DeliveryType") == "LOOSE"
        assert common_props.get("Status") == "NEW"


class TestGetCachedTypesCount:
    """Тесты get_cached_types_count"""

    def test_get_cached_types_count_empty(self, mock_ifc_api_run):
        """get_cached_types_count должен возвращать 0 для пустого кэша"""
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = TypeFactory(mock_ifc)

        assert factory.get_cached_types_count() == 0

    def test_get_cached_types_count_after_adding(self, mock_ifc_api_run):
        """get_cached_types_count должен увеличиваться после добавления типов"""

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

    def test_stud_type_creates_material(self, mock_ifc_api_run):
        """get_or_create_stud_type должен создавать IfcMaterial"""

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

    def test_stud_type_creates_rel_associates_material(self, mock_ifc_api_run):
        """get_or_create_stud_type должен создавать IfcRelAssociatesMaterial"""

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

    def test_nut_type_creates_material(self, mock_ifc_api_run):
        """get_or_create_nut_type должен создавать IfcMaterial и связь"""

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

    def test_washer_type_creates_material(self, mock_ifc_api_run):
        """get_or_create_washer_type должен создавать IfcMaterial и связь"""

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

    def test_same_material_cached(self, mock_ifc_api_run):
        """Одинаковые материалы должны кэшироваться"""

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

    def test_different_materials(self, mock_ifc_api_run):
        """Разные материалы должны создаваться отдельно"""

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
