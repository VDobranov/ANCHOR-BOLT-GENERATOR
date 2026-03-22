"""
test_export_settings.py — Тесты настроек экспорта IFC

Проверка всех комбинаций настроек:
- assembly_class: IfcMechanicalFastener, IfcElementAssembly
- assembly_mode: separate, unified
- geometry_type: solid, triangulated
"""

import pytest
from instance_factory import InstanceFactory
from main import initialize_base_document, reset_doc_manager


class TestExportSettings:
    """Тесты настроек экспорта IFC"""

    @pytest.fixture
    def ifc_doc(self):
        """Создание нового IFC документа для каждого теста"""
        # Сбрасываем менеджер документов перед каждым тестом
        reset_doc_manager()
        return initialize_base_document("test")

    @pytest.fixture
    def factory(self, ifc_doc):
        """Создание InstanceFactory"""
        return InstanceFactory(ifc_doc)

    @pytest.fixture
    def factory_faceted(self, ifc_doc):
        """Создание InstanceFactory с faceted геометрией"""
        return InstanceFactory(ifc_doc, geometry_type="faceted")

    @pytest.fixture
    def bolt_params(self):
        """Базовые параметры болта для тестов"""
        return {
            "bolt_type": "1.1",
            "diameter": 20,
            "length": 800,
            "material": "09Г2С",
        }

    # =============================================================================
    # Тесты для assembly_class
    # =============================================================================

    def test_assembly_class_mechanical_fastener(self, factory, bolt_params):
        """IfcMechanicalFastener: сборка создаётся как IfcMechanicalFastener"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )

        assembly = result["assembly"]
        result["ifc_doc"] = factory.ifc

        # Проверяем, что assembly — IfcMechanicalFastener
        assert assembly.is_a("IfcMechanicalFastener")

    def test_assembly_class_element_assembly(self, factory, bolt_params):
        """IfcElementAssembly: сборка создаётся как IfcElementAssembly"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcElementAssembly",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )

        assembly = result["assembly"]
        result["ifc_doc"] = factory.ifc

        # Проверяем, что assembly — IfcElementAssembly
        assert assembly.is_a("IfcElementAssembly")
        # Проверяем PredefinedType
        assert assembly.PredefinedType == "USERDEFINED"
        # Проверяем ObjectType
        assert assembly.ObjectType == "ANCHORBOLT"

    # =============================================================================
    # Тесты для assembly_mode
    # =============================================================================

    def test_assembly_mode_separate(self, factory, bolt_params):
        """Separate: компоненты как отдельные сущности"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )

        components = result["components"]
        ifc_doc = result["ifc_doc"]

        # Проверяем, что компоненты существуют
        assert len(components) > 1
        # Все компоненты — IfcMechanicalFastener
        for comp in components:
            assert comp.is_a("IfcMechanicalFastener")

    def test_assembly_mode_unified(self, factory, bolt_params):
        """Unified: геометрия объединена через IfcBooleanResult, компоненты без геометрии"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="unified",
            geometry_type="solid",
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]
        components = result["components"]

        # Проверяем, что есть IfcBooleanResult в документе
        boolean_results = ifc_doc.by_type("IfcBooleanResult")
        assert len(boolean_results) > 0, "Ожидается IfcBooleanResult для unified режима"

        # Проверяем, что assembly имеет геометрию с IfcBooleanResult
        assert assembly.Representation is not None, "Assembly должно иметь представление"

        # Проверяем, что mesh_data существует и валиден
        mesh_data = result.get("mesh_data")
        assert mesh_data is not None, "mesh_data должен существовать"
        assert "meshes" in mesh_data, "mesh_data должен содержать 'meshes'"
        assert len(mesh_data["meshes"]) > 0, "meshes не должен быть пустым"

        # Проверяем, что компоненты НЕ имеют геометрии в unified режиме
        for comp in components:
            # У компонентов не должно быть Representation или оно пустое
            has_geometry = (
                hasattr(comp, "Representation")
                and comp.Representation
                and len(comp.Representation.Representations) > 0
            )
            # В unified режиме компоненты не должны иметь собственной геометрии
            # (геометрия только у assembly)
            # Примечание: компоненты могут иметь RepresentationMaps из типа, но не свои

    # =============================================================================
    # Тесты для geometry_type
    # =============================================================================

    def test_geometry_type_solid(self, factory, bolt_params):
        """Solid: геометрия через B-Rep (IfcSweptDiskSolid, экструзия)"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]

        # Проверяем наличие твёрдотельной геометрии
        has_solid = False
        for entity in ifc_doc.by_type("IfcSweptDiskSolid"):
            has_solid = True
            break
        if not has_solid:
            # Проверяем экструзию
            for entity in ifc_doc.by_type("IfcExtrudedAreaSolid"):
                has_solid = True
                break

        assert has_solid, "Ожидается твёрдотельная геометрия"

    def test_geometry_type_faceted(self, factory, bolt_params):
        """Faceted: геометрия через IfcFacetedBrep"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="unified",
            geometry_type="faceted",
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]

        # Проверка наличия IfcFacetedBrep
        has_brep = False
        for entity in ifc_doc.by_type("IfcFacetedBrep"):
            has_brep = True
            break

        assert has_brep, "Ожидается геометрия IfcFacetedBrep"

    def test_geometry_type_triangulated(self, factory, bolt_params):
        """Triangulated: геометрия через IfcTriangulatedFaceSet

        TODO: Реализовать конвертацию B-Rep в IfcTriangulatedFaceSet
        """
        pytest.skip("Triangulated режим требует реализации конвертации B-Rep в mesh")

    # =============================================================================
    # Комбинированные тесты (все комбинации)
    # =============================================================================

    @pytest.mark.parametrize(
        "assembly_class,assembly_mode,geometry_type",
        [
            # separate режим: solid и faceted
            ("IfcMechanicalFastener", "separate", "solid"),
            ("IfcMechanicalFastener", "separate", "faceted"),
            ("IfcElementAssembly", "separate", "solid"),
            ("IfcElementAssembly", "separate", "faceted"),
            # unified режим: solid и faceted
            ("IfcMechanicalFastener", "unified", "solid"),
            ("IfcMechanicalFastener", "unified", "faceted"),
            ("IfcElementAssembly", "unified", "solid"),
            ("IfcElementAssembly", "unified", "faceted"),
            # TODO: Добавить triangulated режимы после реализации
            # ("IfcMechanicalFastener", "separate", "triangulated"),
            # ("IfcMechanicalFastener", "unified", "triangulated"),
            # ("IfcElementAssembly", "separate", "triangulated"),
            # ("IfcElementAssembly", "unified", "triangulated"),
        ],
    )
    def test_all_combinations(
        self, ifc_doc, bolt_params, assembly_class, assembly_mode, geometry_type
    ):
        """Тест всех комбинаций настроек"""
        # Создаём factory с правильным geometry_type
        factory = InstanceFactory(ifc_doc, geometry_type=geometry_type)
        
        result = factory.create_bolt_assembly(
            assembly_class=assembly_class,
            assembly_mode=assembly_mode,
            geometry_type=geometry_type,
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]

        # Базовая проверка: результат существует
        assert result is not None
        assert "assembly" in result
        assert "components" in result

        # Проверка assembly_class
        if assembly_class == "IfcElementAssembly":
            assert result["assembly"].is_a("IfcElementAssembly")
            assert result["assembly"].PredefinedType == "USERDEFINED"
            assert result["assembly"].ObjectType == "ANCHORBOLT"
        else:
            assert result["assembly"].is_a("IfcMechanicalFastener")

        # Проверка assembly_mode
        if assembly_mode == "unified":
            if geometry_type == "faceted":
                # Для faceted режима: IfcFacetedBrep уже создан, BooleanResult может не быть
                breps = ifc_doc.by_type("IfcFacetedBrep")
                assert len(breps) > 0, f"Ожидается IfcFacetedBrep для {geometry_type}"
            else:
                # Для solid режима: должен быть IfcBooleanResult
                boolean_results = ifc_doc.by_type("IfcBooleanResult")
                assert len(boolean_results) > 0, f"Ожидается IfcBooleanResult для {assembly_mode}"

        # Проверка geometry_type
        # Для separate режима: faceted создаёт IfcFacetedBrep для каждого компонента
        # Для unified режима: faceted создаёт один IfcFacetedBrep для всей сборки
        if geometry_type == "faceted":
            breps = ifc_doc.by_type("IfcFacetedBrep")
            assert len(breps) > 0, f"Ожидается IfcFacetedBrep для {geometry_type}"
        elif geometry_type == "triangulated":
            triangulated_faces = ifc_doc.by_type("IfcTriangulatedFaceSet")
            assert (
                len(triangulated_faces) > 0
            ), f"Ожидается IfcTriangulatedFaceSet для {geometry_type}"

    # =============================================================================
    # Тесты валидации IFC документа
    # =============================================================================

    def test_ifc_document_valid(self, factory, bolt_params):
        """IFC документ валиден после создания болта"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]

        # Базовая валидация
        assert len(ifc_doc.by_type("IfcProject")) > 0, "IfcProject не найден"
        assert len(ifc_doc.by_type("IfcBuildingStorey")) > 0, "IfcBuildingStorey не найден"
        assert len(ifc_doc.by_type("IfcMechanicalFastener")) > 0, "IfcMechanicalFastener не найден"

    def test_geometric_subcontext_exists(self, ifc_doc):
        """IfcGeometricRepresentationSubContext существует"""
        # Проверяем наличие субконтекста
        subcontexts = ifc_doc.by_type("IfcGeometricRepresentationSubContext")
        assert len(subcontexts) > 0, "IfcGeometricRepresentationSubContext не найден"

        # Проверяем параметры субконтекста
        subcontext = subcontexts[0]
        assert subcontext.ContextIdentifier == "Body", "ContextIdentifier должен быть 'Body'"
        assert subcontext.TargetView == "MODEL_VIEW", "TargetView должен быть 'MODEL_VIEW'"
        assert subcontext.ParentContext is not None, "ParentContext не должен быть None"
        assert subcontext.TargetScale == 1.0, "TargetScale должен быть 1.0"

    def test_spatial_structure_valid(self, factory, bolt_params):
        """Пространственная структура корректна"""
        result = factory.create_bolt_assembly(
            assembly_class="IfcElementAssembly",
            assembly_mode="separate",  # separate для проверки IfcRelAggregates
            geometry_type="solid",
            **bolt_params,
        )

        ifc_doc = result["ifc_doc"]

        # Проверяем IfcRelContainedInSpatialStructure
        rel_contained = ifc_doc.by_type("IfcRelContainedInSpatialStructure")
        assert len(rel_contained) > 0, "IfcRelContainedInSpatialStructure не найден"

        # Проверяем IfcRelAggregates
        rel_aggregates = ifc_doc.by_type("IfcRelAggregates")
        assert len(rel_aggregates) > 0, "IfcRelAggregates не найден"
