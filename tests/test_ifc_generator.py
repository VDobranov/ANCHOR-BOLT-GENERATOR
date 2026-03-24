"""
Тесты для ifc_generator.py — генерация и экспорт IFC файлов
"""

import os
import sys

import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


@pytest.fixture(autouse=True)
def reset_document_manager():
    """Сброс менеджера документов между тестами"""
    from main import reset_doc_manager

    reset_doc_manager()
    yield
    reset_doc_manager()


class TestIFCGenerator:
    """Тесты для IFCGenerator"""

    def test_init(self):
        """IFCGenerator должен инициализироваться с ifc документом"""
        from ifc_generator import IFCGenerator
        from main import initialize_base_document

        ifc_doc = initialize_base_document()
        generator = IFCGenerator(ifc_doc)

        assert generator.ifc == ifc_doc

    def test_setup_units_and_contexts(self):
        """setup_units_and_contexts должен настраивать единицы и контексты"""
        from ifc_generator import IFCGenerator
        from main import initialize_base_document

        ifc_doc = initialize_base_document()
        generator = IFCGenerator(ifc_doc)

        # Вызываем настройку
        generator.setup_units_and_contexts()

        # Проверяем, что единицы созданы
        units = ifc_doc.by_type("IfcUnitAssignment")
        assert len(units) >= 1

        # Проверяем, что геометрический контекст существует
        contexts = ifc_doc.by_type("IfcGeometricRepresentationContext")
        assert len(contexts) >= 1

    def test_export_to_file(self, tmp_path):
        """export_to_file должен экспортировать в файл"""
        from ifc_generator import IFCGenerator
        from main import initialize_base_document

        ifc_doc = initialize_base_document()
        generator = IFCGenerator(ifc_doc)

        filepath = os.path.join(tmp_path, "test.ifc")
        result_path = generator.export_to_file(filepath)

        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 0

        # Проверяем содержимое файла
        with open(result_path, "r") as f:
            content = f.read()
            assert "ISO-10303-21" in content
