# TDD Процесс

## Обзор

Red-Green-Refactor цикл для разработки через тестирование.

## 1. Написание теста (Red)

```python
# tests/test_example.py
def test_validate_valid_parameters():
    """Валидация должна проходить для корректных параметров"""
    from gost_data import validate_parameters

    # Должно работать без исключений
    result = validate_parameters('1.1', 1, 20, 800, '09Г2С')
    assert result is True
```

### Запуск теста
```bash
pytest tests/test_example.py -v
```

**Ожидаемый результат:** Тест падает (функция не реализована)

## 2. Реализация (Green)

```python
# python/gost_data.py
def validate_parameters(bolt_type, execution, diameter, length, material):
    errors = []

    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")

    if errors:
        raise ValueError('\n'.join(errors))

    return True
```

### Запуск теста
```bash
pytest tests/test_example.py -v
```

**Ожидаемый результат:** Тест проходит

## 3. Рефакторинг (Refactor)

- Улучшение кода без изменения поведения
- Удаление дублирования
- Упрощение логики
- Добавление type hints

### Пример рефакторинга

```python
def validate_parameters(
    bolt_type: str,
    execution: int,
    diameter: int,
    length: int,
    material: str
) -> bool:
    """Валидация параметров болта по ГОСТ."""
    errors = []

    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")

    if errors:
        raise ValueError('\n'.join(errors))

    return True
```

## 4. Повторный запуск тестов

```bash
# Все тесты
pytest tests/ -v

# Pre-commit проверки
pre-commit run --all-files
```

**Ожидаемый результат:** Все тесты проходят

## Цикл TDD

```
┌─────────────┐
│     Red     │ ──► Тест падает (функция не реализована)
└─────────────┘
       │
       ▼
┌─────────────┐
│    Green    │ ──► Тест проходит (минимальная реализация)
└─────────────┘
       │
       ▼
┌─────────────┐
│  Refactor   │ ──► Улучшение кода
└─────────────┘
       │
       ▼
   Повтор
```
