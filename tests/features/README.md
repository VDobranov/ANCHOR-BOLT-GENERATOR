# IFC Gherkin Validation

Валидация IFC файлов с использованием Gherkin-правил buildingSMART.

## 🚀 Быстрый старт

### Запуск всех тестов

```bash
behave tests/features/
```

### Запуск конкретного правила

```bash
behave tests/features/rules/PJS101_Project-presence.feature
```

### Запуск по тегам

```bash
# Только пилотные тесты
behave --tags=@pilot

# Только правила PJS (Project)
behave --tags=@PJS

# Исключить отключённые правила
behave --tags="-@disabled"
```

## 📁 Структура

```
tests/features/
├── environment.py              # Настройка контекста Behave
├── steps/
│   └── steps.py                # Step definitions (Python)
└── rules/
    ├── PJS101_Project-presence.feature
    └── ...
```

## 📝 Написание новых тестов

### 1. Создайте .feature файл

```gherkin
@PJS
@version1
Feature: PJS101 - Project presence

    Правило: PJS101 — Наличие проекта
    Требование: Модель должна содержать ровно один IfcProject.

    Scenario: IfcProject существует
        Given IFC файл с генератором анкерных болтов
        
        Then Должно быть ровно 1 экземпляр(ов) .IfcProject.
```

### 2. Добавьте step definition (если нужно)

```python
# tests/features/steps/steps.py

@then('Должно быть ровно {num:d} экземпляр(ов) .{entity}.')
def step_check_entity_count_exact(context, num, entity):
    if context.model is None:
        raise RuntimeError("Модель не загружена")
    
    instances = context.model.by_type(entity)
    actual_count = len(instances)
    
    assert actual_count == num, (
        f"Ожидалось {num} экземпляр(ов) {entity}, "
        f"но найдено {actual_count}"
    )
```

### 3. Запустите тест

```bash
behave tests/features/rules/your-test.feature
```

## 🔧 Доступные step definitions

### Given (Дано)

| Step | Описание |
|------|----------|
| `IFC файл с генератором анкерных болтов` | Загружает IFC файл из генератора |

### Then (Тогда)

| Step | Описание |
|------|----------|
| `Должно быть ровно {n} экземпляр(ов) .{Entity}.` | Проверка точного количества |
| `Должно быть хотя бы {n} экземпляр(ов) .{Entity}.` | Проверка минимального количества |
| `Должно быть не более {n} экземпляр(ов) .{Entity}.` | Проверка максимального количества |

## 🏷 Теги

| Тег | Описание |
|-----|----------|
| `@pilot` | Пилотные тесты |
| `@PJS` | Правила категории Project |
| `@SPS` | Правила категории Spatial |
| `@GEM` | Правила категории Geometry |
| `@version1` | Версия правила v1 |
| `@industry-practice` | Отраслевая практика |

## 📊 Отчётность

### Текстовый отчёт

```bash
behave --format pretty
```

### JSON отчёт

```bash
behave --format json --outfile reports/validation.json
```

### HTML отчёт

```bash
pip install behave-html-formatter
behave --format html --outfile reports/validation.html
```

## 🔍 Отладка

### Запуск с логированием

```bash
behave --logging-level=DEBUG
```

### Остановка на первой ошибке

```bash
behave --stop
```

### Показ step definitions

```bash
behave --steps
```

## 📚 Интеграция с buildingSMART

Этот проект использует step definitions из репозитория [buildingSMART/ifc-gherkin-rules](https://github.com/buildingSMART/ifc-gherkin-rules).

Step definitions buildingSMART находятся в:
```
external/ifc-gherkin-rules/features/steps/
```

Для использования step definitions buildingSMART напрямую, скопируйте нужные шаги в `tests/features/steps/`.

## 🐛 Решение проблем

### Ошибка: "No module named 'steps'"

Убедитесь что PYTHONPATH установлен:

```bash
export PYTHONPATH=python:$PYTHONPATH
behave tests/features/
```

### Ошибка: "Step definition not found"

Проверьте что step definition зарегистрирован в `tests/features/steps/steps.py`.

### Ошибка: "Model not loaded"

Используйте `Given IFC файл с генератором анкерных болтов` перед проверками.

## 📖 Дополнительная документация

- [Behave Documentation](https://behave.readthedocs.io/)
- [Gherkin Syntax](https://cucumber.io/docs/gherkin/reference/)
- [buildingSMART ifc-gherkin-rules](https://github.com/buildingSMART/ifc-gherkin-rules)
