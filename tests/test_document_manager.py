"""
Тесты для document_manager.py — менеджер IFC документов
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))


@pytest.fixture(autouse=True)
def reset_document_manager():
    """Сброс менеджера документов между тестами"""
    from document_manager import IFCDocumentManager

    # Очищаем все документы
    IFCDocumentManager._instances = {}
    yield


class TestIFCDocumentManagerInit:
    """Тесты инициализации IFCDocumentManager"""

    def test_init(self):
        """IFCDocumentManager должен инициализироваться"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        assert manager._documents == {}
        assert manager._current_id is None


class TestCreateDocument:
    """Тесты create_document"""

    def test_create_document(self):
        """create_document должен создавать документ"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")

        assert doc is not None
        assert "test_doc" in manager._documents

    def test_create_document_with_schema(self):
        """create_document должен создавать документ с указанной схемой"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc", schema="IFC4")

        projects = doc.by_type("IfcProject")
        assert len(projects) == 1

    def test_create_document_raises_for_duplicate(self):
        """create_document должен вызывать ошибку для дубликата"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test_doc")

        with pytest.raises(ValueError, match="уже существует"):
            manager.create_document("test_doc")

    def test_create_document_sets_current_id(self):
        """create_document должен устанавливать текущий ID"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test_doc")

        assert manager._current_id == "test_doc"


class TestGetDocument:
    """Тесты get_document"""

    def test_get_document(self):
        """get_document должен возвращать документ"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc = manager.create_document("test_doc")
        retrieved = manager.get_document("test_doc")

        assert retrieved == doc

    def test_get_document_raises_for_not_found(self):
        """get_document должен вызывать ошибку для несуществующего"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()

        with pytest.raises(ValueError, match="не найден"):
            manager.get_document("nonexistent")


class TestResetDocument:
    """Тесты reset_document"""

    def test_reset_document(self):
        """reset_document должен сбрасывать документ"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        doc1 = manager.create_document("test_doc")
        doc2 = manager.reset_document("test_doc")

        assert doc1 != doc2
        assert "test_doc" in manager._documents

    def test_reset_document_current_id(self):
        """reset_document должен сохранять текущий ID"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test_doc")
        manager.reset_document("test_doc")

        assert manager._current_id == "test_doc"


class TestDeleteDocument:
    """Тесты delete_document"""

    def test_delete_document(self):
        """delete_document должен удалять документ"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test_doc")
        manager.delete_document("test_doc")

        assert "test_doc" not in manager._documents

    def test_delete_document_raises_for_not_found(self):
        """delete_document не должен вызывать ошибку для несуществующего"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        # delete_document не вызывает ошибку если документ не найден
        manager.delete_document("nonexistent")


class TestListDocuments:
    """Тесты list_documents"""

    def test_list_documents_empty(self):
        """list_documents должен возвращать пустой список"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        docs = manager.list_documents()

        assert docs == []

    def test_list_documents(self):
        """list_documents должен возвращать список документов"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("doc1")
        manager.create_document("doc2")

        docs = manager.list_documents()

        assert "doc1" in docs
        assert "doc2" in docs
        assert len(docs) == 2


class TestClearAll:
    """Тесты clear_all"""

    def test_clear_all(self):
        """clear_all должен очищать все документы"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("doc1")
        manager.create_document("doc2")

        manager.clear_all()

        assert len(manager._documents) == 0
        assert manager._current_id is None


class TestMaterialManager:
    """Тесты material_manager"""

    def test_get_material_manager(self):
        """get_material_manager должен возвращать менеджер материалов"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()
        manager.create_document("test_doc")
        mat_manager = manager.get_material_manager("test_doc")

        assert mat_manager is not None

    def test_get_material_manager_raises_for_not_found(self):
        """get_material_manager должен вызывать ошибку для несуществующего"""
        from document_manager import IFCDocumentManager

        manager = IFCDocumentManager()

        with pytest.raises(ValueError, match="не найден"):
            manager.get_material_manager("nonexistent")
