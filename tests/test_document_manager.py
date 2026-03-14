"""
Тесты для document_manager.py - менеджер IFC документов

Интеграционные тесты для управления множественными документами.
"""

import os
import sys

import pytest

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


class TestIFCDocumentManager:
    """Тесты для IFCDocumentManager"""

    def test_create_document(self):
        """IFCDocumentManager должен создавать новый документ"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test-doc")

        assert doc is not None
        assert doc.schema == "IFC4"
        assert "test-doc" in manager.list_documents()

    def test_create_document_with_custom_schema(self):
        """IFCDocumentManager должен поддерживать кастомную схему"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test-doc", schema="IFC4")

        assert doc.schema == "IFC4"

    def test_create_duplicate_document_raises(self):
        """Создание дубликата документа должно вызывать ошибку"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test-doc")

        with pytest.raises(ValueError, match="уже существует"):
            manager.create_document("test-doc")

    def test_get_document(self):
        """Получение документа по ID"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test-doc")
        retrieved = manager.get_document("test-doc")

        assert retrieved is doc

    def test_get_document_not_found(self):
        """Получение несуществующего документа должно вызывать ошибку"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()

        with pytest.raises(ValueError, match="не найден"):
            manager.get_document("nonexistent")

    def test_get_current_document(self):
        """Получение текущего документа без указания ID"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test-doc")
        retrieved = manager.get_document()  # Без ID, должен вернуть текущий

        assert retrieved is doc

    def test_delete_document(self):
        """Удаление документа"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test-doc")
        manager.delete_document("test-doc")

        assert "test-doc" not in manager.list_documents()

    def test_delete_current_document(self):
        """Удаление текущего документа должно сбрасывать current_id"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test-doc")
        manager.delete_document("test-doc")

        assert manager.get_current_id() is None

    def test_get_material_manager(self):
        """Получение менеджера материалов для документа"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test-doc")
        mat_manager = manager.get_material_manager("test-doc")

        assert mat_manager is not None

    def test_reset_document(self):
        """Сброс документа"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc1 = manager.create_document("test-doc")
        doc2 = manager.reset_document("test-doc")

        assert doc2 is not None
        assert doc2.schema == "IFC4"

    def test_list_documents(self):
        """Получение списка документов"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("doc1")
        manager.create_document("doc2")

        docs = manager.list_documents()

        assert len(docs) == 2
        assert "doc1" in docs
        assert "doc2" in docs

    def test_clear_all(self):
        """Очистка всех документов"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("doc1")
        manager.create_document("doc2")
        manager.clear_all()

        assert len(manager.list_documents()) == 0
        assert manager.get_current_id() is None

    def test_multiple_documents_isolated(self):
        """Несколько документов должны быть изолированы"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc1 = manager.create_document("doc1")
        doc2 = manager.create_document("doc2")

        assert doc1 is not doc2
        assert len(doc1.by_type("IfcProject")) == 1
        assert len(doc2.by_type("IfcProject")) == 1


class TestGlobalManager:
    """Тесты для глобального менеджера"""

    def test_get_manager(self):
        """get_manager должен возвращать один и тот же экземпляр"""
        from document_manager import get_manager, reset_manager

        reset_manager()
        manager1 = get_manager()
        manager2 = get_manager()

        assert manager1 is manager2

    def test_reset_manager(self):
        """reset_manager должен сбрасывать глобальный менеджер"""
        from document_manager import get_manager, reset_manager

        reset_manager()
        manager1 = get_manager()
        reset_manager()
        manager2 = get_manager()

        assert manager1 is not manager2
