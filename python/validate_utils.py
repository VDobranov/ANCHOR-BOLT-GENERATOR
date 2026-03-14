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
from typing import Any, List, Optional

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
        self.current_error_lines: List[str] = []

    def emit(self, record):
        # Собираем все сообщения уровня ERROR и выше
        if record.levelno >= logging.ERROR:
            msg = self.format(record)
            if msg:
                self.current_error_lines.append(msg)
            # Если сообщение пустое, но есть накопленные строки - сохраняем их как одну ошибку
            elif self.current_error_lines:
                self.errors.append("\n".join(self.current_error_lines))
                self.current_error_lines = []

    def flush(self):
        # Сохраняем оставшиеся ошибки при завершении
        if self.current_error_lines:
            self.errors.append("\n".join(self.current_error_lines))
            self.current_error_lines = []


def validate_ifc_file(ifc_doc, express_rules: bool = True) -> Optional[List[str]]:
    """
    Валидация IFC документа

    Args:
        ifc_doc: IFC документ (ifcopenshell.file)
        express_rules: Если True, проверяются EXPRESS правила (типы данных,
            правила WHERE и т.д.). По умолчанию True для полной валидации.

    Returns:
        Список ошибок или None если документ валиден
    """
    if not HAS_VALIDATE:
        raise RuntimeError("ifcopenshell.validate не доступен")

    # Используем root logger для перехвата всех сообщений
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(logging.ERROR)

    # Сохраняем существующие handlers
    original_handlers = root_logger.handlers[:]
    root_logger.handlers = []

    # Добавляем наш handler
    handler = IFCValidationHandler()
    root_logger.addHandler(handler)

    try:
        # Запускаем валидацию с проверкой EXPRESS правил
        ifc_validate.validate(ifc_doc, root_logger, express_rules=express_rules)
    finally:
        # Восстанавливаем logger
        handler.flush()
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)

    errors = handler.errors if handler.errors else None
    return errors


def assert_valid_ifc(ifc_doc, msg: Optional[str] = None):
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
