# CI/CD Интеграция

## Актуальный workflow (ifc-validation.yml)

```yaml
# .github/workflows/ifc-validation.yml
name: IFC Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate-ifc:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
      with:
        submodules: recursive
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install ifcopenshell behave
        pip install -r external/ifc-gherkin-rules/requirements.txt
    - name: Generate test IFC file
      run: |
        PYTHONPATH=python:$PYTHONPATH python -c "..."
    - name: Run buildingSMART Gherkin Validation
      run: |
        cd external/ifc-gherkin-rules
        python -m behave \
          --define input=../../test_bolt.ifc \
          --tags="-@disabled" \
          --tags="-@IFC2X3" \
          --tags="-@IFC4.3" \
          --tags="-@critical" \
          --exclude features/rules/GEM/GEM113*.feature \
          features/rules/

  pytest:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: pip install pytest ifcopenshell
    - name: Run pytest
      run: |
        PYTHONPATH=python:$PYTHONPATH python -m pytest tests/ -v --tb=short
```

## Этапы CI/CD

| Этап | Описание |
|------|----------|
| Checkout | Загрузка кода и подмодулей |
| Setup Python | Установка Python 3.11 |
| Dependencies | Установка ifcopenshell, behave, pytest |
| Generate IFC | Генерация тестового IFC файла |
| Gherkin Validation | Запуск правил buildingSMART |
| Pytest | Запуск unit-тестов Python |

## Триггеры

- Push в ветки: `main`, `develop`
- Pull request в `main`

## Исключения правил

| Правило | Причина |
|---------|---------|
| GEM113 | Баг в валидаторе buildingSMART |
| @disabled | Отключенные правила |
| @IFC2X3 | Не применимо к IFC4 |
| @IFC4.3 | Не применимо к IFC4 ADD2 TC1 |
| @critical | Критические правила (требуют доработки) |
