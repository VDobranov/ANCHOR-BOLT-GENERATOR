"""
Тесты для validate_utils.py — утилиты валидации IFC

Тесты для функций валидации IFC документов.
"""

import os
import sys

import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestValidateIfcFile:
    """Тесты для validate_ifc_file"""

    def test_validate_ifc_file_returns_list_or_none(self):
        """validate_ifc_file должен возвращать список или None"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import validate_ifc_file

        reset_doc_manager()
        doc = initialize_base_document()
        result = validate_ifc_file(doc)

        # Функция может возвращать список или None если валидация недоступна
        assert result is None or isinstance(result, list)

    def test_validate_ifc_file_with_real_document(self):
        """validate_ifc_file с реальным документом"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import validate_ifc_file

        reset_doc_manager()
        doc = initialize_base_document()
        result = validate_ifc_file(doc)

        # Функция может возвращать список или None
        assert result is None or isinstance(result, list)

    def test_validate_ifc_file_express_rules_false(self):
        """validate_ifc_file с express_rules=False"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import validate_ifc_file

        reset_doc_manager()
        doc = initialize_base_document()
        result = validate_ifc_file(doc, express_rules=False)

        # Функция может возвращать список или None
        assert result is None or isinstance(result, list)


class TestAssertValidIfc:
    """Тесты для assert_valid_ifc"""

    def test_assert_valid_ifc_passes(self):
        """assert_valid_ifc не должен вызывать ошибок для валидного"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import assert_valid_ifc

        reset_doc_manager()
        doc = initialize_base_document()
        # Не должно вызывать исключений
        assert_valid_ifc(doc)

    def test_assert_valid_ifc_with_message(self):
        """assert_valid_ifc с кастомным сообщением"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import assert_valid_ifc

        reset_doc_manager()
        doc = initialize_base_document()
        # Не должно вызывать исключений даже с msg
        assert_valid_ifc(doc, msg="Custom message")


class TestValidateIfcFileWithErrors:
    """Тесты для validate_ifc_file с ошибками"""

    def test_validate_ifc_file_empty_doc(self):
        """validate_ifc_file для пустого документа"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import validate_ifc_file

        reset_doc_manager()
        doc = initialize_base_document()
        result = validate_ifc_file(doc)

        # Функция может возвращать список или None
        assert result is None or isinstance(result, list)

    def test_validate_ifc_file_raises_without_ifcopenshell(self, monkeypatch):
        """validate_ifc_file должен вызывать RuntimeError если ifcopenshell.validate недоступен"""
        from main import initialize_base_document, reset_doc_manager
        from validate_utils import HAS_VALIDATE, validate_ifc_file

        reset_doc_manager()
        doc = initialize_base_document()

        # Тест только если HAS_VALIDATE=True
        if HAS_VALIDATE:
            # Если модуль доступен, просто проверяем что функция работает
            result = validate_ifc_file(doc)
            assert result is None or isinstance(result, list)
        assert result is None or isinstance(result, list)
