"""
Тесты для instance_factory.py — создание инстансов болтов
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


@pytest.fixture(autouse=True)
def reset_document_manager():
    """Сброс менеджера документов между тестами"""
    from document_manager import IFCDocumentManager

    IFCDocumentManager._instances = {}
    yield


class TestInstanceFactoryInit:
    """Тесты инициализации InstanceFactory"""

    def test_init(self):
        """InstanceFactory должен инициализироваться"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        assert factory.ifc == doc
        assert factory.type_factory is not None
        assert factory.material_manager is not None

    def test_init_with_type_factory(self):
        """InstanceFactory с кастомным type_factory"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory
        from type_factory import TypeFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        type_factory = TypeFactory(doc)
        factory = InstanceFactory(doc, type_factory=type_factory)

        assert factory.type_factory == type_factory


class TestCreateBoltAssembly:
    """Тесты create_bolt_assembly"""

    def test_create_bolt_assembly_type_1_1(self):
        """create_bolt_assembly для типа 1.1"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        assert result is not None
        assert "assembly" in result
        assert "stud" in result

    def test_create_bolt_assembly_type_2_1(self):
        """create_bolt_assembly для типа 2.1 с плитой"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="2.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        assert result is not None
        # Тип 2.1 должен иметь больше компонентов чем тип 1.1 (плита + дополнительные гайки)
        components = result.get("components", [])
        # У типа 2.1 должно быть больше 5 компонентов (шпилька, шайба, 2 гайки + плита + 2 гайки)
        assert (
            len(components) >= 5
        ), f"Тип 2.1 должен иметь >= 5 компонентов, найдено: {len(components)}"

    def test_create_bolt_assembly_type_5(self):
        """create_bolt_assembly для типа 5 (прямой болт)"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="5",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        assert result is not None
        assert "assembly" in result

    def test_create_bolt_assembly_with_material(self):
        """create_bolt_assembly с разным материалом"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        for material in ["09Г2С", "ВСт3пс2", "10Г2"]:
            result = factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=800,
                material=material,
            )
            assert result is not None

    def test_create_bolt_assembly_with_ifc_class(self):
        """create_bolt_assembly с разным Ifc классом"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        for assembly_class in ["IfcMechanicalFastener", "IfcElementAssembly"]:
            result = factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=800,
                material="09Г2С",
                assembly_class=assembly_class,
            )
            assert result is not None

    def test_create_bolt_assembly_with_assembly_mode(self):
        """create_bolt_assembly с разным режимом сборки"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        for assembly_mode in ["separate", "unified"]:
            result = factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=800,
                material="09Г2С",
                assembly_mode=assembly_mode,
            )
            assert result is not None

    def test_create_bolt_assembly_with_geometry_type(self):
        """create_bolt_assembly с разным типом геометрии"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        for geometry_type in ["solid", "mesh"]:
            result = factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=800,
                material="09Г2С",
                geometry_type=geometry_type,
            )
            assert result is not None

    def test_create_bolt_assembly_creates_entities(self):
        """create_bolt_assembly должен создавать IFC сущности"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        initial_count = len(list(doc))

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        # Количество сущностей должно увеличиться
        final_count = len(list(doc))
        assert final_count > initial_count

    def test_create_bolt_assembly_creates_fasteners(self):
        """create_bolt_assembly должен создавать IfcMechanicalFastener"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        fasteners = doc.by_type("IfcMechanicalFastener")
        assert len(fasteners) > 0

    def test_create_bolt_assembly_creates_material(self):
        """create_bolt_assembly должен создавать материал"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        materials = doc.by_type("IfcMaterial")
        assert len(materials) > 0

    def test_create_bolt_assembly_invalid_bolt_type(self):
        """create_bolt_assembly должен вызывать ошибку для неверного типа"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        with pytest.raises((ValueError, KeyError)):
            factory.create_bolt_assembly(
                bolt_type="invalid",
                diameter=20,
                length=800,
                material="09Г2С",
            )

    def test_create_bolt_assembly_invalid_diameter(self):
        """create_bolt_assembly должен вызывать ошибку для неверного диаметра"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        with pytest.raises((ValueError, KeyError)):
            factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=999,
                length=800,
                material="09Г2С",
            )

    def test_create_bolt_assembly_invalid_length(self):
        """create_bolt_assembly должен вызывать ошибку для неверной длины"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        with pytest.raises((ValueError, KeyError)):
            factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=-100,
                material="09Г2С",
            )

    def test_create_bolt_assembly_invalid_material(self):
        """create_bolt_assembly должен вызывать ошибку для неверного материала"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        with pytest.raises((ValueError, KeyError)):
            factory.create_bolt_assembly(
                bolt_type="1.1",
                diameter=20,
                length=800,
                material="invalid_material",
            )

    def test_create_bolt_assembly_nominal_diameter(self):
        """create_bolt_assembly должен устанавливать NominalDiameter для всех IfcMechanicalFastener"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        # Проверяем NominalDiameter у всех IfcMechanicalFastener
        fasteners = doc.by_type("IfcMechanicalFastener")
        assert len(fasteners) > 0
        for fastener in fasteners:
            assert hasattr(fastener, "NominalDiameter")
            assert fastener.NominalDiameter == 20

    def test_create_bolt_assembly_nominal_length(self):
        """create_bolt_assembly должен устанавливать NominalLength для шпилек и сборки"""
        from document_manager import IFCDocumentManager
        from instance_factory import InstanceFactory

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        factory = InstanceFactory(doc)

        result = factory.create_bolt_assembly(
            bolt_type="1.1",
            diameter=20,
            length=800,
            material="09Г2С",
        )

        # Проверяем NominalLength у сборки и шпильки
        fasteners = doc.by_type("IfcMechanicalFastener")
        assembly = result["assembly"]
        stud = result["stud"]

        # Сборка должна иметь NominalLength
        assert hasattr(assembly, "NominalLength")
        assert assembly.NominalLength == 800

        # Шпилька должна иметь NominalLength
        assert hasattr(stud, "NominalLength")
        assert stud.NominalLength == 800
