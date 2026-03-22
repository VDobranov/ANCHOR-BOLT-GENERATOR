"""
Behave environment configuration for IFC Validation

Этот файл настраивает контекст для всех Gherkin-сценариев.
Используем step definitions из buildingSMART/ifc-gherkin-rules.
"""

import os
import sys
from pathlib import Path

# Добавляем пути к step definitions из buildingSMART
project_root = Path(__file__).parent.parent.parent
gherkin_rules_path = project_root / "external" / "ifc-gherkin-rules" / "features" / "steps"

if str(gherkin_rules_path) not in sys.path:
    sys.path.insert(0, str(gherkin_rules_path))


def before_all(context):
    """
    Выполняется перед всеми сценариями.
    """
    # Настраиваем логирование
    context.config.setup_logging()
    
    # Путь к тестовым IFC файлам
    context.test_files_dir = Path(__file__).parent.parent / "fixtures"
    context.test_files_dir.mkdir(exist_ok=True, parents=True)
    
    print(f"\n{'='*60}")
    print("IFC Gherkin Validation - buildingSMART")
    print(f"{'='*60}")
    print(f"Feature files: {project_root / 'external' / 'ifc-gherkin-rules' / 'features' / 'rules'}")
    print(f"Step definitions: {gherkin_rules_path}")
    print(f"{'='*60}\n")


def before_scenario(context, scenario):
    """
    Выполняется перед каждым сценарием.
    """
    context.model = None
    context.ifc_file = None


def after_scenario(context, scenario):
    """
    Выполняется после каждого сценария.
    """
    if hasattr(context, 'model') and context.model:
        context.model = None


def after_all(context):
    """
    Выполняется после всех сценариев.
    """
    print(f"\n{'='*60}")
    print("Validation complete")
    print(f"{'='*60}\n")
