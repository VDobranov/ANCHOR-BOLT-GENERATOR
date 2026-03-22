"""
Behave environment configuration for IFC Validation

Этот файл настраивает контекст для всех Gherkin-сценариев.
"""

import os
import sys
from pathlib import Path

# Добавляем пути к step definitions из buildingSMART
project_root = Path(__file__).parent.parent
gherkin_rules_path = project_root / "external" / "ifc-gherkin-rules" / "features" / "steps"

if str(gherkin_rules_path) not in sys.path:
    sys.path.insert(0, str(gherkin_rules_path))


def before_all(context):
    """
    Выполняется перед всеми сценариями.
    """
    # Настраиваем логирование
    context.config.setup_logging()
    
    # Путь к тестовым IFC файлам - используем абсолютный путь
    context.test_files_dir = Path(__file__).parent.parent / "fixtures"
    
    # Создаём директорию если не существует
    context.test_files_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"\n{'='*60}")
    print("IFC Gherkin Validation - buildingSMART")
    print(f"{'='*60}")
    print(f"Test files directory: {context.test_files_dir}")
    print(f"Step definitions: {Path(__file__).parent / 'steps'}")
    print(f"{'='*60}\n")


def before_scenario(context, scenario):
    """
    Выполняется перед каждым сценарием.
    """
    # Сбрасываем контекст сценария
    context.model = None
    context.ifc_file = None
    context.validation_errors = []
    context.validation_warnings = []


def after_scenario(context, scenario):
    """
    Выполняется после каждого сценария.
    """
    # Очищаем модель если была загружена
    if hasattr(context, 'model') and context.model:
        context.model = None


def after_all(context):
    """
    Выполняется после всех сценариев.
    """
    print(f"\n{'='*60}")
    print("Validation complete")
    print(f"{'='*60}\n")
