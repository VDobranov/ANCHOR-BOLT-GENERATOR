"""
test_ifc_validation.py — Валидация IFC файлов через ifcopenshell.validate

Тесты проверяют сгенерированные IFC файлы на соответствие стандарту IFC4
с использованием встроенной валидации ifcopenshell.
"""

import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


@pytest.fixture(autouse=True)
def reset_document_manager():
    """Сброс менеджера документов между тестами"""
    from main import reset_doc_manager

    reset_doc_manager()
    yield
    reset_doc_manager()


def validate_ifc_file(filepath: str, express_rules: bool = False) -> tuple:
    """
    Валидация IFC файла через ifcopenshell.validate

    Args:
        filepath: Путь к IFC файлу
        express_rules: Проверять ли правила EXPRESS

    Returns:
        (is_valid, errors, warnings) кортеж
    """
    from ifcopenshell.validate import json_logger, validate

    logger = json_logger()
    validate(filepath, logger, express_rules=express_rules)

    errors = []
    warnings = []

    for stmt in logger.statements:
        # Ошибки имеют уровень severity >= 40
        if stmt.get("severity", 0) >= 40:
            errors.append(stmt)
        else:
            warnings.append(stmt)

    return len(errors) == 0, errors, warnings


class TestIFCValidationBasic:
    """Базовые тесты валидации IFC"""

    def test_empty_document_valid(self):
        """Пустой документ должен проходить валидацию"""
        from ifcopenshell.api import run

        # Создаём документ через API
        f = run("project.create_file")

        # Сохраняем
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            f.write(tmp.name)
            tmp_path = tmp.name

        try:
            is_valid, errors, warnings = validate_ifc_file(tmp_path)
            assert is_valid, f"Валидация не пройдена: {errors}"
        finally:
            os.unlink(tmp_path)


class TestIFCValidationBoltAssembly:
    """Валидация сборок болтов"""

    @pytest.mark.parametrize(
        "bolt_type,diameter,length",
        [
            ("1.1", 20, 800),
            ("1.1", 48, 900),  # М48 минимальная длина
            ("1.2", 16, 500),
            ("2.1", 24, 500),
            ("5", 12, 300),
        ],
        ids=["type1.1_M20", "type1.1_M48", "type1.2_M16", "type2.1_M24", "type5_M12"],
    )
    def test_bolt_assembly_unified_solid(self, bolt_type, diameter, length):
        """Валидация болта в режиме 'Всё одним телом', твердотельная геометрия"""
        from instance_factory import generate_bolt_assembly
        from main import create_document

        create_document("test")

        params = {
            "bolt_type": bolt_type,
            "diameter": diameter,
            "length": length,
            "material": "09Г2С",
        }

        ifc_str, _ = generate_bolt_assembly(
            params,
            assembly_class="IfcMechanicalFastener",
            assembly_mode="unified",
            geometry_type="solid",
            add_standard_pset=True,
            pset_expertise="none",
        )

        # Сохраняем и валидируем
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as tmp:
            tmp.write(ifc_str)
            tmp_path = tmp.name

        try:
            is_valid, errors, warnings = validate_ifc_file(tmp_path)
            assert is_valid, f"Валидация не пройдена для {bolt_type} М{diameter}×{length}: {errors}"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.parametrize(
        "bolt_type,diameter,length",
        [
            ("1.1", 20, 800),
            ("2.1", 24, 500),
            ("5", 16, 400),
        ],
        ids=["type1.1_M20", "type2.1_M24", "type5_M16"],
    )
    def test_bolt_assembly_separate_solid(self, bolt_type, diameter, length):
        """Валидация болта в режиме 'Вроссыпь', твердотельная геометрия"""
        from instance_factory import generate_bolt_assembly
        from main import create_document

        create_document("test")

        params = {
            "bolt_type": bolt_type,
            "diameter": diameter,
            "length": length,
            "material": "09Г2С",
        }

        ifc_str, _ = generate_bolt_assembly(
            params,
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            add_standard_pset=True,
            pset_expertise="none",
        )

        # Сохраняем и валидируем
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as tmp:
            tmp.write(ifc_str)
            tmp_path = tmp.name

        try:
            is_valid, errors, warnings = validate_ifc_file(tmp_path)
            assert is_valid, f"Валидация не пройдена для {bolt_type} М{diameter}×{length}: {errors}"
        finally:
            os.unlink(tmp_path)


class TestIFCValidationPSet:
    """Валидация с PropertySets"""

    def test_bolt_with_standard_psets(self):
        """Болт со стандартными PSet должен проходить валидацию"""
        from instance_factory import generate_bolt_assembly
        from main import create_document

        create_document("test")

        params = {
            "bolt_type": "1.1",
            "diameter": 20,
            "length": 800,
            "material": "09Г2С",
        }

        ifc_str, _ = generate_bolt_assembly(
            params,
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            add_standard_pset=True,
            pset_expertise="none",
        )

        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as tmp:
            tmp.write(ifc_str)
            tmp_path = tmp.name

        try:
            is_valid, errors, warnings = validate_ifc_file(tmp_path)
            assert is_valid, f"Валидация не пройдена: {errors}"
        finally:
            os.unlink(tmp_path)

    @pytest.mark.parametrize(
        "pset_expertise",
        ["MGE", "MOGE", "SPB_GAU_CGE", "UGE_PERM"],
        ids=["MGE", "MOGE", "SPB_GAU_CGE", "UGE_PERM"],
    )
    def test_bolt_with_expertise_psets(self, pset_expertise):
        """Болт с PSet для экспертизы должен проходить валидацию"""
        from instance_factory import generate_bolt_assembly
        from main import create_document

        create_document("test")

        params = {
            "bolt_type": "2.1",
            "diameter": 24,
            "length": 500,
            "material": "09Г2С",
        }

        ifc_str, _ = generate_bolt_assembly(
            params,
            assembly_class="IfcMechanicalFastener",
            assembly_mode="separate",
            geometry_type="solid",
            add_standard_pset=True,
            pset_expertise=pset_expertise,
        )

        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as tmp:
            tmp.write(ifc_str)
            tmp_path = tmp.name

        try:
            is_valid, errors, warnings = validate_ifc_file(tmp_path)
            assert is_valid, f"Валидация не пройдена для {pset_expertise}: {errors}"
        finally:
            os.unlink(tmp_path)


class TestIFCValidationExpressRules:
    """Валидация с проверкой EXPRESS правил (более строгая)"""

    @pytest.mark.parametrize(
        "bolt_type,diameter,length,assembly_mode,geometry_type,pset_expertise,material",
        [
            # Тип 1.1 - separate/solid
            ("1.1", 20, 800, "separate", "solid", "none", "09Г2С"),
            ("1.1", 48, 900, "separate", "solid", "none", "09Г2С"),
            # Тип 1.1 - unified/solid
            ("1.1", 20, 800, "unified", "solid", "none", "09Г2С"),
            # Тип 1.2 - separate/solid
            ("1.2", 16, 500, "separate", "solid", "none", "09Г2С"),
            # Тип 2.1 - separate/solid (с плитой)
            ("2.1", 24, 500, "separate", "solid", "none", "09Г2С"),
            ("2.1", 24, 500, "separate", "solid", "MGE", "09Г2С"),
            ("2.1", 24, 500, "separate", "solid", "MOGE", "09Г2С"),
            ("2.1", 24, 500, "separate", "solid", "SPB_GAU_CGE", "09Г2С"),
            ("2.1", 24, 500, "separate", "solid", "UGE_PERM", "09Г2С"),
            # Тип 2.1 - unified/solid
            ("2.1", 24, 500, "unified", "solid", "none", "09Г2С"),
            # Тип 5 - separate/solid
            ("5", 12, 300, "separate", "solid", "none", "09Г2С"),
            # Разные материалы
            ("1.1", 20, 800, "separate", "solid", "none", "ВСт3пс2"),
            ("1.1", 20, 800, "separate", "solid", "none", "10Г2"),
        ],
        ids=[
            "1.1_M20_separate_solid",
            "1.1_M48_separate_solid",
            "1.1_M20_unified_solid",
            "1.2_M16_separate_solid",
            "2.1_M24_separate_solid",
            "2.1_M24_separate_solid_MGE",
            "2.1_M24_separate_solid_MOGE",
            "2.1_M24_separate_solid_SPB_GAU_CGE",
            "2.1_M24_separate_solid_UGE_PERM",
            "2.1_M24_unified_solid",
            "5_M12_separate_solid",
            "1.1_M20_VSt3ps2",
            "1.1_M20_10G2",
        ],
    )
    def test_bolt_express_rules_all_combinations(
        self, bolt_type, diameter, length, assembly_mode, geometry_type, pset_expertise, material
    ):
        """Все сочетания болтов должны проходить валидацию с EXPRESS правилами"""
        from instance_factory import generate_bolt_assembly
        from main import create_document

        create_document("test")

        params = {
            "bolt_type": bolt_type,
            "diameter": diameter,
            "length": length,
            "material": material,
        }

        ifc_str, _ = generate_bolt_assembly(
            params,
            assembly_class="IfcMechanicalFastener",
            assembly_mode=assembly_mode,
            geometry_type=geometry_type,
            add_standard_pset=True,
            pset_expertise=pset_expertise,
        )

        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False, mode="w") as tmp:
            tmp.write(ifc_str)
            tmp_path = tmp.name

        try:
            # Валидация с EXPRESS правилами
            is_valid, errors, warnings = validate_ifc_file(tmp_path, express_rules=True)
            # EXPRESS правила могут давать дополнительные предупреждения, но не ошибки
            assert (
                is_valid
            ), f"EXPRESS валидация не пройдена для {bolt_type} М{diameter}×{length}: {errors}"
        finally:
            os.unlink(tmp_path)
