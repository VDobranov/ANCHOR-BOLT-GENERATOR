"""
validate_utils.py — Утилиты для валидации IFC файлов

Использование:
    from validate_utils import validate_ifc_file, assert_valid_ifc
    
    # Валидация файла
    errors = validate_ifc_file(ifc_doc)
    
    # Assert в тестах
    assert_valid_ifc(ifc_doc)
"""

import logging
from typing import List, Optional, Any

try:
    from ifcopenshell import validate as ifc_validate
    HAS_VALIDATE = True
except ImportError:
    HAS_VALIDATE = False


class IFCValidationHandler(logging.Handler):
    """Handler для сбора ошибок валидации"""
    
    def __init__(self):
        super().__init__()
        self.errors: List[str] = []
    
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.errors.append(self.format(record))


def validate_ifc_file(ifc_doc) -> Optional[List[Any]]:
    """
    Валидация IFC документа
    
    Args:
        ifc_doc: IFC документ (ifcopenshell.file)
    
    Returns:
        Список ошибок или None если документ валиден
    """
    if not HAS_VALIDATE:
        raise RuntimeError("ifcopenshell.validate не доступен")
    
    # Создаём logger для сбора ошибок
    logger = logging.getLogger('IFC_Validation')
    logger.setLevel(logging.ERROR)
    
    # Очищаем существующие handlers
    logger.handlers = []
    
    # Добавляем handler для сбора ошибок
    handler = IFCValidationHandler()
    logger.addHandler(handler)
    
    # Запускаем валидацию
    result = ifc_validate.validate(ifc_doc, logger)
    
    # Проверяем результат
    if result is None:
        return None
    
    if hasattr(result, '__len__') and len(result) == 0:
        return None
    
    return result


def assert_valid_ifc(ifc_doc, msg: str = None):
    """
    Assert для проверки валидности IFC документа в тестах
    
    Args:
        ifc_doc: IFC документ (ifcopenshell.file)
        msg: Сообщение об ошибке (опционально)
    
    Raises:
        AssertionError: Если документ не валиден
    """
    errors = validate_ifc_file(ifc_doc)
    
    if errors:
        error_msg = f"IFC валидация не пройдена: {len(errors)} ошибок\n"
        for i, error in enumerate(errors[:10], 1):
            error_msg += f"  {i}. {error}\n"
        if len(errors) > 10:
            error_msg += f"  ... и ещё {len(errors) - 10} ошибок"
        
        if msg:
            error_msg = f"{msg}\n{error_msg}"
        
        raise AssertionError(error_msg)
