"""
test_ifc_rules.py — Тесты правил валидации IFC buildingsmart

Проверка соответствия правилам из:
https://buildingsmart.github.io/ifc-gherkin-rules/branches/main/features/index.html

Применимые правила для анкерных болтов:
- OJT001: Object predefined type
- SPS001: Basic spatial structure for buildings
- SPS007: Spatial containment
- MAT000: Materials
- GEM051: Presence of geometric context
- GEM052: Correct geometric subcontexts
- PJS101: Project presence
- PJS003: Globally Unique Identifiers
- IFC105: Resource entities need to be referenced
- MPD001: Correct use of RepresentationType and RepresentationIdentifier
- LOP000: Local placement
"""

import pytest
from instance_factory import InstanceFactory
from main import initialize_base_document, reset_doc_manager


class TestIFCRules:
    """Тесты правил валидации IFC buildingsmart"""

    @pytest.fixture
    def ifc_doc(self):
        """Создание нового IFC документа для каждого теста"""
        reset_doc_manager()
        return initialize_base_document("test")

    @pytest.fixture
    def factory(self, ifc_doc):
        """Создание InstanceFactory"""
        return InstanceFactory(ifc_doc)

    @pytest.fixture
    def bolt_params(self):
        """Базовые параметры болта"""
        return {
            "bolt_type": "1.1",
            "diameter": 20,
            "length": 800,
            "material": "09Г2С",
        }

    # =============================================================================
    # OJT001: Object predefined type - v3
    # =============================================================================

    def test_ojt001_predefined_type_rule(self, factory, bolt_params):
        """
        OJT001: Предопределённый тип объекта
        
        Требование: Если экземпляр связан с типом через IfcRelDefinesByType
        и у типа PredefinedType != NOTDEFINED, то PredefinedType у экземпляра
        должен быть пустым.
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcElementAssembly",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]

        # PredefinedType должен быть пустым
        assert assembly.PredefinedType is None, "PredefinedType должен быть пустым (OJT001)"

        # ObjectType должен быть указан
        assert assembly.ObjectType == "ANCHORBOLT", "ObjectType должен быть указан"

        # Должна быть связь с типом
        rel_defines = ifc_doc.by_type("IfcRelDefinesByType")
        assert len(rel_defines) > 0, "Должна быть связь IfcRelDefinesByType"

        # Проверяем связь для assembly
        assembly_type_relation = None
        for rel in rel_defines:
            if assembly in (rel.RelatedObjects or []):
                assembly_type_relation = rel
                break

        assert assembly_type_relation is not None, "Assembly должен быть связан с типом"

        # У типа PredefinedType != NOTDEFINED
        relating_type = assembly_type_relation.RelatingType
        assert relating_type.PredefinedType is not None, "Тип должен иметь PredefinedType"
        assert not relating_type.PredefinedType.startswith("NOTDEFINED"), \
            "PredefinedType типа не должен быть NOTDEFINED"

    # =============================================================================
    # SPS001: Basic spatial structure for buildings - v2
    # =============================================================================

    def test_sps001_basic_spatial_structure(self, factory, bolt_params):
        """
        SPS001: Базовая пространственная структура для зданий
        
        Требование: Модель должна содержать IfcProject, IfcSite, IfcBuilding, IfcBuildingStorey
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]

        # Проверяем наличие всех уровней пространственной структуры
        projects = ifc_doc.by_type("IfcProject")
        assert len(projects) == 1, "Должен быть один IfcProject"

        sites = ifc_doc.by_type("IfcSite")
        assert len(sites) >= 1, "Должен быть хотя бы один IfcSite"

        buildings = ifc_doc.by_type("IfcBuilding")
        assert len(buildings) >= 1, "Должен быть хотя бы один IfcBuilding"

        storeys = ifc_doc.by_type("IfcBuildingStorey")
        assert len(storeys) >= 1, "Должен быть хотя бы один IfcBuildingStorey"

    # =============================================================================
    # SPS007: Spatial containment - v6
    # =============================================================================

    def test_sps007_spatial_containment(self, factory, bolt_params):
        """
        SPS007: Пространственное вложение
        
        Требование: Элементы должны быть привязаны к пространственной структуре
        через IfcRelContainedInSpatialStructure
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]

        # Проверяем IfcRelContainedInSpatialStructure
        rel_contained = ifc_doc.by_type("IfcRelContainedInSpatialStructure")
        assert len(rel_contained) > 0, "Должен быть IfcRelContainedInSpatialStructure"

        # Проверяем что assembly включён в пространственную структуру
        found = False
        for rel in rel_contained:
            if assembly in (rel.RelatedElements or []):
                found = True
                # Проверяем что RelatedStructure — это IfcBuildingStorey
                assert rel.RelatingStructure.is_a("IfcBuildingStorey"), \
                    "Элемент должен быть привязан к IfcBuildingStorey"
                break

        assert found, "Assembly должен быть включён в пространственную структуру (SPS007)"

    # =============================================================================
    # MAT000: Materials - v1
    # =============================================================================

    def test_mat000_materials(self, factory, bolt_params):
        """
        MAT000: Материалы
        
        Требование: Материалы должны быть определены и ассоциированы с элементами
        или их типами
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]

        # Проверяем наличие материалов
        materials = ifc_doc.by_type("IfcMaterial")
        assert len(materials) > 0, "Должны быть определены материалы"

        # Проверяем ассоциацию материалов
        mat_assoc = ifc_doc.by_type("IfcRelAssociatesMaterial")
        assert len(mat_assoc) > 0, "Должна быть ассоциация материалов"

        # Материалы могут быть ассоциированы с типами (наследуется экземплярами)
        # или напрямую с экземплярами
        found_for_type = False
        found_for_instance = False

        for assoc in mat_assoc:
            assert assoc.RelatingMaterial is not None, "Материал должен быть указан"
            
            # Проверяем ассоциацию с типом assembly
            for obj in (assoc.RelatedObjects or []):
                if obj.is_a("IfcMechanicalFastenerType") or obj.is_a("IfcElementAssemblyType"):
                    found_for_type = True
                if obj == assembly:
                    found_for_instance = True

        # Материалы должны быть ассоциированы хотя бы с типами
        assert found_for_type or found_for_instance, \
            "Материалы должны быть ассоциированы с типами или экземплярами (MAT000)"

    # =============================================================================
    # GEM051: Presence of geometric context - v2
    # =============================================================================

    def test_gem051_geometric_context_presence(self, ifc_doc):
        """
        GEM051: Наличие геометрического контекста
        
        Требование: Должен быть определён IfcGeometricRepresentationContext
        """
        contexts = ifc_doc.by_type("IfcGeometricRepresentationContext")
        assert len(contexts) > 0, "Должен быть IfcGeometricRepresentationContext (GEM051)"

        # Проверяем что контекст имеет ContextType='Model'
        model_contexts = [c for c in contexts if getattr(c, 'ContextType', None) == 'Model']
        assert len(model_contexts) > 0, "Должен быть 3D контекст (ContextType='Model')"

    # =============================================================================
    # GEM052: Correct geometric subcontexts - v2
    # =============================================================================

    def test_gem052_geometric_subcontexts(self, ifc_doc):
        """
        GEM052: Корректные геометрические подконтексты
        
        Требование: Подконтексты должны иметь правильные ContextIdentifier и TargetView
        """
        subcontexts = ifc_doc.by_type("IfcGeometricRepresentationSubContext")
        assert len(subcontexts) > 0, "Должен быть IfcGeometricRepresentationSubContext (GEM052)"

        for subcontext in subcontexts:
            # Проверяем ContextIdentifier
            assert subcontext.ContextIdentifier in ["Body", "Box", "Axis", "Annotation"], \
                f"Некорректный ContextIdentifier: {subcontext.ContextIdentifier}"

            # Проверяем TargetView
            assert subcontext.TargetView in ["MODEL_VIEW", "PLAN_VIEW", "SECTION_VIEW"], \
                f"Некорректный TargetView: {subcontext.TargetView}"

            # Проверяем связь с родительским контекстом
            assert subcontext.ParentContext is not None, "Должен быть ParentContext"

    # =============================================================================
    # PJS101: Project presence - v1
    # =============================================================================

    def test_pjs101_project_presence(self, ifc_doc):
        """
        PJS101: Наличие проекта
        
        Требование: Модель должна содержать IfcProject
        """
        projects = ifc_doc.by_type("IfcProject")
        assert len(projects) == 1, "Должен быть ровно один IfcProject (PJS101)"

        project = projects[0]
        assert project.Name, "Project должен иметь Name"
        assert project.GlobalId, "Project должен иметь GlobalId"

    # =============================================================================
    # PJS003: Globally Unique Identifiers - v1
    # =============================================================================

    def test_pjs003_guid_presence(self, factory, bolt_params):
        """
        PJS003: Глобально уникальные идентификаторы
        
        Требование: Все корневые сущности должны иметь уникальный GlobalId
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]

        # Собираем все GlobalId
        global_ids = []
        for entity in ifc_doc:
            if hasattr(entity, 'GlobalId') and entity.GlobalId:
                global_ids.append(entity.GlobalId)

        # Проверяем уникальность
        assert len(global_ids) == len(set(global_ids)), \
            "Все GlobalId должны быть уникальными (PJS003)"

        # Проверяем формат GlobalId (22 символа, base64)
        import re
        guid_pattern = re.compile(r'^[0-9A-Za-z$_]{22}$')
        for guid in global_ids[:10]:  # Проверяем первые 10
            assert guid_pattern.match(guid), f"Некорректный формат GlobalId: {guid}"

    # =============================================================================
    # IFC105: Resource entities need to be referenced by rooted entity - v3
    # =============================================================================

    def test_ifc105_resource_entities_referenced(self, factory, bolt_params):
        """
        IFC105: Ресурсные сущности должны быть сосланы корневой сущностью
        
        Требование: Материалы, профили и другие ресурсы должны использоваться
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]

        # Проверяем что материалы используются
        materials = ifc_doc.by_type("IfcMaterial")
        mat_assoc = ifc_doc.by_type("IfcRelAssociatesMaterial")

        if materials:
            assert len(mat_assoc) > 0, \
                "Материалы должны быть ассоциированы с элементами (IFC105)"

    # =============================================================================
    # MPD001: Correct use of RepresentationType and RepresentationIdentifier - v1
    # =============================================================================

    def test_mpd001_representation_identifiers(self, factory, bolt_params):
        """
        MPD001: Корректное использование RepresentationType и RepresentationIdentifier
        
        Требование: Идентификаторы представлений должны соответствовать контексту
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]

        # Проверяем все ShapeRepresentation
        representations = ifc_doc.by_type("IfcShapeRepresentation")
        
        for rep in representations:
            # Проверяем что ContextOfItems существует
            assert rep.ContextOfItems is not None, \
                "ContextOfItems должен быть указан"

            # Проверяем что RepresentationIdentifier указан
            if rep.RepresentationIdentifier:
                # Допустимые идентификаторы
                valid_identifiers = ["Body", "Axis", "Box", "Annotation", "Profile"]
                assert rep.RepresentationIdentifier in valid_identifiers, \
                    f"Некорректный RepresentationIdentifier: {rep.RepresentationIdentifier}"

    # =============================================================================
    # LOP000: Local placement - v1
    # =============================================================================

    def test_lop000_local_placement(self, factory, bolt_params):
        """
        LOP000: Локальное размещение
        
        Требование: Элементы должны иметь ObjectPlacement с IfcLocalPlacement
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        assembly = result["assembly"]

        # Проверяем что assembly имеет ObjectPlacement
        assert assembly.ObjectPlacement is not None, \
            "Assembly должен иметь ObjectPlacement (LOP000)"

        # Проверяем что это IfcLocalPlacement
        assert assembly.ObjectPlacement.is_a("IfcLocalPlacement"), \
            "ObjectPlacement должен быть IfcLocalPlacement"

        # Проверяем что RelativePlacement указан
        assert assembly.ObjectPlacement.RelativePlacement is not None, \
            "RelativePlacement должен быть указан"

    # =============================================================================
    # SPS003: Correct containment of assemblies - v1
    # =============================================================================

    def test_sps003_assembly_containment(self, factory, bolt_params):
        """
        SPS003: Корректное вложение сборок
        
        Требование: Сборки должны быть привязаны к пространственной структуре
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcElementAssembly",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]

        # Сборка должна быть включена в пространственную структуру
        rel_contained = ifc_doc.by_type("IfcRelContainedInSpatialStructure")
        
        found = False
        for rel in rel_contained:
            if assembly in (rel.RelatedElements or []):
                found = True
                break

        assert found, "Сборка должна быть включена в пространственную структуру (SPS003)"

    # =============================================================================
    # ASM000: Composed elements - v1
    # =============================================================================

    def test_asm000_composed_elements(self, factory, bolt_params):
        """
        ASM000: Составные элементы
        
        Требование: IfcElementAssembly должен иметь компоненты через IfcRelAggregates
        """
        result = factory.create_bolt_assembly(
            assembly_class="IfcElementAssembly",
            assembly_mode="separate",
            geometry_type="solid",
            **bolt_params,
        )
        ifc_doc = result["ifc_doc"]
        assembly = result["assembly"]

        # Для separate режима проверяем IfcRelAggregates
        rel_aggregates = ifc_doc.by_type("IfcRelAggregates")
        
        found = False
        for rel in rel_aggregates:
            if rel.RelatingObject == assembly:
                found = True
                # Проверяем что есть компоненты
                assert rel.RelatedObjects is not None, "Должны быть RelatedObjects"
                assert len(rel.RelatedObjects) > 0, "Должны быть компоненты"
                break

        # Для separate режима должна быть декомпозиция
        if result["components"]:
            assert found, "Сборка должна иметь компоненты через IfcRelAggregates (ASM000)"

    # =============================================================================
    # Комплексный тест: все правила сразу
    # =============================================================================

    def test_all_rules_combined(self, factory, bolt_params):
        """
        Комплексная проверка всех правил для разных комбинаций настроек
        """
        configs = [
            {"assembly_class": "IfcMechanicalFastener", "assembly_mode": "separate"},
            {"assembly_class": "IfcElementAssembly", "assembly_mode": "separate"},
            {"assembly_class": "IfcMechanicalFastener", "assembly_mode": "unified"},
            {"assembly_class": "IfcElementAssembly", "assembly_mode": "unified"},
        ]

        for config in configs:
            result = factory.create_bolt_assembly(
                geometry_type="solid",
                **bolt_params,
                **config,
            )
            ifc_doc = result["ifc_doc"]

            # PJS101: Project presence
            assert len(ifc_doc.by_type("IfcProject")) == 1

            # SPS001: Spatial structure
            assert len(ifc_doc.by_type("IfcSite")) >= 1
            assert len(ifc_doc.by_type("IfcBuilding")) >= 1
            assert len(ifc_doc.by_type("IfcBuildingStorey")) >= 1

            # GEM051: Geometric context
            assert len(ifc_doc.by_type("IfcGeometricRepresentationContext")) > 0

            # GEM052: Subcontexts
            assert len(ifc_doc.by_type("IfcGeometricRepresentationSubContext")) > 0

            # SPS007: Spatial containment
            rel_contained = ifc_doc.by_type("IfcRelContainedInSpatialStructure")
            assert len(rel_contained) > 0

            # MAT000: Materials
            mat_assoc = ifc_doc.by_type("IfcRelAssociatesMaterial")
            assert len(mat_assoc) > 0

            # LOP000: Local placement
            assert result["assembly"].ObjectPlacement is not None
