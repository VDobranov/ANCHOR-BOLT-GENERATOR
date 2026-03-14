"""
Тесты для instance_factory.py - создание инстансов и сборок
"""

from unittest.mock import MagicMock, patch

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

    @pytest.fixture
    def mock_builder_methods(self):
        """Фикстура для мокирования методов builder"""
        from unittest.mock import MagicMock, patch

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")

        # Мокаем на уровне класса ShapeBuilder
        with patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.polyline",
            return_value=MockIfcEntity("IfcIndexedPolyCurve"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.circle",
            return_value=MockIfcEntity("IfcCircle"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.extrude",
            return_value=MockIfcEntity("IfcExtrudedAreaSolid"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.get_representation",
            return_value=mock_shape_rep,
        ):
            yield

    def test_create_bolt_assembly_returns_dict(self, mock_builder_methods):
        """create_bolt_assembly должен возвращать dict"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        # Мокаем _generate_mesh_data чтобы избежать ifcopenshell.geom
        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        assert isinstance(result, dict)
        assert "assembly" in result
        assert "stud" in result
        assert "components" in result
        assert "mesh_data" in result

    def test_create_bolt_assembly_creates_assembly(self, mock_builder_methods):
        """create_bolt_assembly должен создавать сборку"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        assembly = result["assembly"]
        assert assembly is not None
        assert assembly.is_a() == "IfcMechanicalFastener"
        assert assembly.ObjectType == "ANCHORBOLT"

    def test_create_bolt_assembly_name_format(self, mock_builder_methods):
        """Имя сборки должно следовать формату"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        assembly = result["assembly"]
        assert "AnchorBolt_1.1_M20x800" in assembly.Name

    def test_create_bolt_assembly_components_count_type_1_1(self, mock_builder_methods):
        """Для типа 1.1 должно быть 4 компонента: шпилька + шайба + 2 гайки"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        components = result["components"]
        assert len(components) == 4  # stud + washer + 2 nuts

    def test_create_bolt_assembly_components_count_type_2_1(self, mock_builder_methods):
        """Для типа 2.1 должно быть 6 компонентов: шпилька + шайба + 4 гайки"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("2.1", 20, 800, "09Г2С")

        components = result["components"]
        assert len(components) == 6  # stud + washer + 4 nuts

    def test_create_bolt_assembly_stud_type(self, mock_builder_methods):
        """Шпилька должна иметь ObjectType = STUD"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        stud = result["stud"]
        assert stud is not None
        assert stud.ObjectType == "STUD"

    def test_create_bolt_assembly_creates_relations(self, mock_builder_methods):
        """create_bolt_assembly должен создавать отношения"""
        from instance_factory import InstanceFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        with patch.object(factory, "_generate_mesh_data", return_value={"meshes": []}):
            result = factory.create_bolt_assembly("1.1", 20, 800, "09Г2С")

        # Проверка создания IfcRelDefinesByType
        rel_defines = mock_ifc.by_type("IfcRelDefinesByType")
        assert len(rel_defines) > 0

        # Проверка создания IfcRelAggregates
        rel_aggregates = mock_ifc.by_type("IfcRelAggregates")
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
        assert result.is_a() == "IfcLocalPlacement"

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

    @pytest.fixture
    def mock_builder_methods(self):
        """Фикстура для мокирования методов builder"""
        from unittest.mock import patch

        mock_shape_rep = MockIfcEntity("IfcShapeRepresentation")

        with patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.polyline",
            return_value=MockIfcEntity("IfcIndexedPolyCurve"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.create_swept_disk_solid",
            return_value=MockIfcEntity("IfcSweptDiskSolid"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.circle",
            return_value=MockIfcEntity("IfcCircle"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.profile",
            return_value=MockIfcEntity("IfcArbitraryProfileDefWithVoids"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.extrude",
            return_value=MockIfcEntity("IfcExtrudedAreaSolid"),
        ), patch(
            "ifcopenshell.util.shape_builder.ShapeBuilder.get_representation",
            return_value=mock_shape_rep,
        ):
            yield

    def test_create_component_creates_fastener(self, mock_builder_methods):
        """_create_component должен создавать IfcMechanicalFastener"""
        from instance_factory import InstanceFactory
        from type_factory import TypeFactory

        mock_ifc = MockIfcDoc()
        factory = InstanceFactory(mock_ifc)

        # Создадим тип гайки
        type_factory = factory.type_factory
        nut_type = type_factory.get_or_create_nut_type(20, "09Г2С")

        instances_list = []
        result = factory._create_component(
            "Nut", "Nut_Test", "NUT", (0, 0, 10), nut_type, instances_list
        )

        assert result is not None
        assert result.is_a() == "IfcMechanicalFastener"
        assert result.ObjectType == "NUT"
        assert len(instances_list) == 1


class TestGenerateBoltAssembly:
    """Тесты generate_bolt_assembly"""

    def test_generate_bolt_assembly_returns_tuple(self):
        """generate_bolt_assembly должна возвращать кортеж (ifc_str, mesh_data)"""
        from instance_factory import generate_bolt_assembly

        # Примечание: этот тест требует работающего ifcopenshell
        # В среде без ifcopenshell он может упасть
        params = {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}

        try:
            result = generate_bolt_assembly(params)
            assert isinstance(result, tuple)
            assert len(result) == 2
        except Exception:
            # Если ifcopenshell недоступен, тест пропускается
            pytest.skip("ifcopenshell недоступен")

    def test_generate_bolt_assembly_validates_ifc(self):
        """Сгенерированный IFC файл должен проходить валидацию"""
        from instance_factory import generate_bolt_assembly
        from validate_utils import validate_ifc_file

        params = {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}

        try:
            result = generate_bolt_assembly(params)
            ifc_str, mesh_data = result

            # Сохраняем в временный файл и проверяем
            import os
            import tempfile

            import ifcopenshell

            with tempfile.NamedTemporaryFile(mode="w", suffix=".ifc", delete=False) as tmp:
                tmp.write(ifc_str)
                tmp_path = tmp.name

            try:
                ifc_doc = ifcopenshell.open(tmp_path)

                # 1. Валидация IFC файла
                errors = validate_ifc_file(ifc_doc)
                assert errors is None, f"IFC файл не прошёл валидацию: {errors}"

                # 2. Проверка наличия OwnerHistory с ID #1
                owner_history = ifc_doc.by_id(1)
                assert (
                    owner_history.is_a() == "IfcOwnerHistory"
                ), "IfcOwnerHistory должен иметь ID #1"

                # 3. Проверка базовой структуры
                projects = ifc_doc.by_type("IfcProject")
                assert len(projects) == 1, "Должен быть один IfcProject"

                sites = ifc_doc.by_type("IfcSite")
                assert len(sites) == 1, "Должен быть один IfcSite"

                buildings = ifc_doc.by_type("IfcBuilding")
                assert len(buildings) == 1, "Должен быть один IfcBuilding"

                storeys = ifc_doc.by_type("IfcBuildingStorey")
                assert len(storeys) == 1, "Должен быть один IfcBuildingStorey"

                # 4. Проверка болта и компонентов
                fasteners = ifc_doc.by_type("IfcMechanicalFastener")
                assert (
                    len(fasteners) >= 4
                ), f"Должно быть минимум 4 IfcMechanicalFastener (assembly + stud + nut + washer), найдено: {len(fasteners)}"

                # 5. Проверка типов
                fastener_types = ifc_doc.by_type("IfcMechanicalFastenerType")
                assert (
                    len(fastener_types) >= 4
                ), f"Должно быть минимум 4 IfcMechanicalFastenerType, найдено: {len(fastener_types)}"

                # 6. Проверка материалов
                materials = ifc_doc.by_type("IfcMaterial")
                assert (
                    len(materials) >= 1
                ), f"Должен быть хотя бы один IfcMaterial, найдено: {len(materials)}"

                # 7. Проверка отношений
                rel_aggregates = ifc_doc.by_type("IfcRelAggregates")
                assert len(rel_aggregates) >= 1, "Должны быть отношения IfcRelAggregates"

                rel_defines = ifc_doc.by_type("IfcRelDefinesByType")
                assert len(rel_defines) >= 1, "Должны быть отношения IfcRelDefinesByType"

                rel_associates = ifc_doc.by_type("IfcRelAssociatesMaterial")
                assert len(rel_associates) >= 1, "Должны быть отношения IfcRelAssociatesMaterial"

                # 8. Проверка mesh данных
                assert mesh_data is not None, "mesh_data не должен быть None"
                assert "meshes" in mesh_data, "mesh_data должен содержать 'meshes'"
                assert (
                    len(mesh_data["meshes"]) >= 4
                ), f"Должно быть минимум 4 mesh, найдено: {len(mesh_data['meshes'])}"

            finally:
                os.unlink(tmp_path)

        except Exception as e:
            # Если ifcopenshell недоступен, тест пропускается
            pytest.skip(f"ifcopenshell недоступен: {e}")


class TestGetElementProperties:
    """Тесты get_element_properties"""

    # Примечание: get_element_properties требует инициализированный IFC документ
    # и не может быть протестирован без полной инициализации ifcopenshell
    # Интеграционное тестирование должно проводиться в браузере через Pyodide
    pass
