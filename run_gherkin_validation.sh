#!/bin/bash
# Запуск валидации IFC файлов с использованием правил buildingSMART
# Использование: ./run_gherkin_validation.sh <path/to/file.ifc>

IFC_FILE="${1:-bolt_2.1_M20x300.ifc}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GHERKIN_DIR="$SCRIPT_DIR/external/ifc-gherkin-rules"

echo "============================================================"
echo "IFC Gherkin Validation - buildingSMART"
echo "============================================================"
echo "IFC файл: $IFC_FILE"
echo "Правила: $GHERKIN_DIR/features/rules/"
echo "============================================================"

cd "$GHERKIN_DIR"

# Запуск всех правил (кроме отключённых и IFC2X3-only)
python -m behave \
    --define input="$IFC_FILE" \
    --tags="-@disabled" \
    --tags="-@IFC2X3" \
    --tags="-@IFC4.3" \
    --format pretty \
    features/rules/
