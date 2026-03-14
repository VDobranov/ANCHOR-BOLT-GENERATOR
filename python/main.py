"""
main.py — Entry point для Pyodide

Управление IFC документами через IFCDocumentManager:
- Поддержка множественных документов
- Изоляция документов друг от друга
- Улучшенная тестируемость
"""

from typing import Any, Optional

from document_manager import IFCDocumentManager, get_manager

# =============================================================================
# Глобальный менеджер документов
# =============================================================================

_doc_manager: Optional[IFCDocumentManager] = None


def get_doc_manager() -> IFCDocumentManager:
    """
    Получение менеджера документов

    Returns:
        IFCDocumentManager экземпляр
    """
    global _doc_manager
    if _doc_manager is None:
        _doc_manager = IFCDocumentManager()
    return _doc_manager


def reset_doc_manager() -> None:
    """Сброс менеджера документов"""
    global _doc_manager
    _doc_manager = None


# =============================================================================
# API для обратной совместимости
# =============================================================================


def initialize_base_document(doc_id: str = "default") -> Any:
    """
    Инициализация базового документа

    Args:
        doc_id: Идентификатор документа (по умолчанию 'default')

    Returns:
        IFC документ (ifcopenshell.file)
    """
    manager = get_doc_manager()
    return manager.create_document(doc_id)


def get_ifc_document(doc_id: Optional[str] = None) -> Any:
    """
    Получение текущего IFC документа

    Args:
        doc_id: Идентификатор документа (по умолчанию текущий)

    Returns:
        IFC документ

    Raises:
        ValueError: Если документ не найден
    """
    manager = get_doc_manager()
    return manager.get_document(doc_id)


def reset_ifc_document(doc_id: Optional[str] = None) -> Any:
    """
    Сброс IFC документа и создание нового

    Args:
        doc_id: Идентификатор документа (по умолчанию текущий)

    Returns:
        Сброшенный IFC документ
    """
    manager = get_doc_manager()
    return manager.reset_document(doc_id)


def get_material_manager(doc_id: Optional[str] = None) -> Any:
    """
    Получение менеджера материалов

    Args:
        doc_id: Идентификатор документа (по умолчанию текущий)

    Returns:
        MaterialManager экземпляр
    """
    manager = get_doc_manager()
    return manager.get_material_manager(doc_id)


# =============================================================================
# Новое API для работы с множественными документами
# =============================================================================


def create_document(doc_id: str, schema: str = "IFC4") -> Any:
    """
    Создание нового IFC документа

    Args:
        doc_id: Уникальный идентификатор документа
        schema: IFC схема (по умолчанию 'IFC4')

    Returns:
        IFC документ
    """
    manager = get_doc_manager()
    return manager.create_document(doc_id, schema)


def delete_document(doc_id: str) -> None:
    """
    Удаление IFC документа

    Args:
        doc_id: Идентификатор удаляемого документа
    """
    manager = get_doc_manager()
    manager.delete_document(doc_id)


def list_documents() -> list:
    """
    Получение списка всех документов

    Returns:
        Список идентификаторов документов
    """
    manager = get_doc_manager()
    return manager.list_documents()


def clear_all_documents() -> None:
    """Очистка всех документов"""
    manager = get_doc_manager()
    manager.clear_all()


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    try:
        doc = initialize_base_document()
        print("✓ IFC документ инициализирован")
        print(f"  Document ID: {get_doc_manager().get_current_id()}")
        print(f"  Documents: {list_documents()}")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
