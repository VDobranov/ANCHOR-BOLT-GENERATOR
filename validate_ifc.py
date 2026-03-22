#!/usr/bin/env python3
"""
IFC Gherkin Validation Runner

Запускает валидацию IFC файлов с использованием правил buildingSMART.

Использование:
    python validate_ifc.py <path/to/file.ifc> [--rules <path/to/rules>]
"""

import sys
import os
from pathlib import Path

# Добавляем пути
project_root = Path(__file__).parent
gherkin_rules = project_root / "external" / "ifc-gherkin-rules"
features_steps = gherkin_rules / "features" / "steps"

sys.path.insert(0, str(features_steps))

# Импортируем behave
from behave import configuration
from behave import runner as behave_runner

def validate_ifc(ifc_path: str, rules_path: str = None):
    """
    Запускает валидацию IFC файла.
    """
    ifc_path = Path(ifc_path).resolve()
    
    if not ifc_path.exists():
        print(f"Ошибка: Файл не найден: {ifc_path}")
        return 1
    
    if rules_path is None:
        rules_path = gherkin_rules / "features" / "rules"
    
    # Настраиваем behave
    args = [
        str(rules_path),
        "--define", f"ifc_file={ifc_path}",
        "--format", "pretty",
        "--no-capture",
    ]
    
    # Запускаем behave
    os.chdir(gherkin_rules)
    return behave_runner.main(args=args)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python validate_ifc.py <path/to/file.ifc> [--rules <path>]")
        sys.exit(1)
    
    ifc_file = sys.argv[1]
    rules = sys.argv[2] if len(sys.argv) > 2 else None
    
    sys.exit(validate_ifc(ifc_file, rules))
