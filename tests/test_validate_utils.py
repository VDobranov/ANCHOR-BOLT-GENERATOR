"""
Тесты для validate_utils.py — утилиты валидации IFC
"""

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


@pytest.fixture(autouse=True)
def reset_document_manager():
    """Сброс менеджера документов между тестами"""
    from main import reset_doc_manager

    reset_doc_manager()
    yield
    reset_doc_manager()


class TestIFCValidationHandler:
    """Тесты IFCValidationHandler"""

    def test_init(self):
        """IFCValidationHandler должен инициализироваться"""
        from validate_utils import IFCValidationHandler

        handler = IFCValidationHandler()
        assert handler.errors == []
        assert handler.current_error_lines == []

    def test_emit_error_message(self):
        """emit должен добавлять сообщения об ошибках"""
        from validate_utils import IFCValidationHandler

        handler = IFCValidationHandler()

        # Создаём mock record
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Test error",
            args=(),
            exc_info=None,
        )
        handler.emit(record)
        handler.flush()  # Нужно вызвать flush для сохранения ошибок

        assert len(handler.errors) == 1
        assert "Test error" in handler.errors[0]

    def test_emit_non_error_message(self):
        """emit должен игнорировать не-error сообщения"""
        from validate_utils import IFCValidationHandler

        handler = IFCValidationHandler()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test info",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

        assert len(handler.errors) == 0

    def test_flush(self):
        """flush должен сохранять оставшиеся ошибки"""
        from validate_utils import IFCValidationHandler

        handler = IFCValidationHandler()
        handler.current_error_lines = ["error1", "error2"]
        handler.flush()

        assert len(handler.errors) == 1
        assert "error1\nerror2" in handler.errors[0]
        assert handler.current_error_lines == []


class TestValidateIfcFile:
    """Тесты validate_ifc_file"""

    def test_validate_ifc_file_returns_list_or_none(self):
        """validate_ifc_file должен возвращать список или None"""
        from main import initialize_base_document
        from validate_utils import HAS_VALIDATE, validate_ifc_file

        ifc_doc = initialize_base_document()
        result = validate_ifc_file(ifc_doc)

        # Функция может возвращать список или None если валидация недоступна
        if HAS_VALIDATE:
            assert result is None or isinstance(result, list)
        else:
            # Если валидация недоступна, должно быть исключение
            pass

    def test_validate_ifc_file_express_rules_false(self):
        """validate_ifc_file с express_rules=False"""
        from main import initialize_base_document
        from validate_utils import HAS_VALIDATE, validate_ifc_file

        ifc_doc = initialize_base_document()
        result = validate_ifc_file(ifc_doc, express_rules=False)

        if HAS_VALIDATE:
            assert result is None or isinstance(result, list)

    def test_validate_ifc_file_raises_without_ifcopenshell(self, monkeypatch):
        """validate_ifc_file должен вызывать RuntimeError если ifcopenshell.validate недоступен"""
        # Мокаем HAS_VALIDATE в False
        import validate_utils
        from main import initialize_base_document
        from validate_utils import validate_ifc_file

        original_value = validate_utils.HAS_VALIDATE
        validate_utils.HAS_VALIDATE = False

        try:
            ifc_doc = initialize_base_document()
            with pytest.raises(RuntimeError, match="ifcopenshell.validate не доступен"):
                validate_ifc_file(ifc_doc)
        finally:
            validate_utils.HAS_VALIDATE = original_value


class TestAssertValidIfc:
    """Тесты assert_valid_ifc"""

    def test_assert_valid_ifc_passes(self):
        """assert_valid_ifc не должен вызывать ошибок для валидного"""
        from main import initialize_base_document
        from validate_utils import assert_valid_ifc

        ifc_doc = initialize_base_document()
        # Не должно вызывать исключений
        assert_valid_ifc(ifc_doc)

    def test_assert_valid_ifc_with_message(self):
        """assert_valid_ifc с кастомным сообщением"""
        from main import initialize_base_document
        from validate_utils import assert_valid_ifc

        ifc_doc = initialize_base_document()
        # Не должно вызывать исключений даже с msg
        assert_valid_ifc(ifc_doc, msg="Custom message")

    def test_assert_valid_ifc_raises_for_invalid(self, monkeypatch):
        """assert_valid_ifc должен вызывать AssertionError для невалидного"""
        # Мокаем validate_ifc_file чтобы возвращала ошибки
        import validate_utils
        from validate_utils import assert_valid_ifc

        def mock_validate(doc):
            return ["Error 1", "Error 2"]

        original_validate = validate_utils.validate_ifc_file
        validate_utils.validate_ifc_file = mock_validate

        try:
            with pytest.raises(AssertionError, match="IFC валидация не пройдена"):
                assert_valid_ifc(None)
        finally:
            validate_utils.validate_ifc_file = original_validate

    def test_assert_valid_ifc_with_custom_message(self, monkeypatch):
        """assert_valid_ifc с кастомным сообщением при ошибке"""
        import validate_utils
        from validate_utils import assert_valid_ifc

        def mock_validate(doc):
            return ["Error 1"]

        original_validate = validate_utils.validate_ifc_file
        validate_utils.validate_ifc_file = mock_validate

        try:
            with pytest.raises(AssertionError, match="Custom error message"):
                assert_valid_ifc(None, msg="Custom error message")
        finally:
            validate_utils.validate_ifc_file = original_validate
