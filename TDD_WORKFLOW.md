# TDD Workflow для ANCHOR-BOLT-GENERATOR

## Обзор

Проект использует Test-Driven Development (TDD) подход для разработки Python модулей.

## Быстрый старт

### Запуск всех тестов
```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
pytest tests/ -v
```

### Запуск тестов для конкретного модуля
```bash
# Только тесты для gost_data.py
pytest tests/test_gost_data.py -v

# Только тесты для geometry_builder.py
pytest tests/test_geometry_builder.py -v
```

### Запуск тестов с фильтрацией по имени
```bash
# Тесты валидации
pytest tests/test_gost_data.py::TestValidateParameters -v

# Тесты кэширования
pytest tests/test_type_factory.py -k caching -v
```

## Структура тестов

```
tests/
├── conftest.py              # Фикстуры и конфигурация pytest
├── test_utils.py            # Тесты utils.py (3 теста)
├── test_gost_data.py        # Тесты gost_data.py (36 тестов)
├── test_geometry_builder.py # Тесты geometry_builder.py (15 тестов)
├── test_type_factory.py     # Тесты type_factory.py (17 тестов)
└── test_instance_factory.py # Тесты instance_factory.py (14 тестов)
```

## TDD Процесс

### 1. Написание теста (Red)
```python
# tests/test_example.py
def test_validate_valid_parameters():
    """Валидация должна проходить для корректных параметров"""
    from gost_data import validate_parameters
    
    # Должно работать без исключений
    result = validate_parameters('1.1', 1, 20, 800, '09Г2С')
    assert result is True
```

### 2. Запуск теста (убедиться что падает)
```bash
pytest tests/test_example.py -v
```

### 3. Реализация (Green)
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

### 4. Рефакторинг (Refactor)
- Улучшение кода без изменения поведения
- Удаление дублирования
- Упрощение логики

### 5. Повторный запуск тестов
```bash
pytest tests/ -v  # Все тесты должны пройти
```

## Mock объекты

Для тестирования используются Mock объекты для изоляции зависимостей:

```python
class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities = []
        self._by_type = {}
    
    def create_entity(self, entity_type, **kwargs):
        entity = MockIfcEntity(entity_type, **kwargs)
        self.entities.append(entity)
        return entity
    
    def by_type(self, entity_type):
        return self._by_type.get(entity_type, [])
```

## Использование patch для моков

```python
from unittest.mock import patch

def test_create_bolt_assembly():
    """Тест с моком _generate_mesh_data"""
    from instance_factory import InstanceFactory
    
    mock_ifc = MockIfcDoc()
    factory = InstanceFactory(mock_ifc)
    
    # Мокаем метод чтобы избежать ifcopenshell.geom
    with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
        result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')
    
    assert isinstance(result, dict)
```

## Покрытие тестами

### Покрывается тестами:
- ✅ Валидация параметров (gost_data.py)
- ✅ Справочники и размеры (gost_data.py)
- ✅ Построение геометрии (geometry_builder.py)
- ✅ Кэширование типов (type_factory.py)
- ✅ Создание инстансов (instance_factory.py)
- ✅ Утилиты (utils.py)

### Не покрывается тестами:
- ❌ Интеграция с ifcopenshell.geom (требуется Pyodide)
- ❌ Генерация IFC файлов (интеграционное тестирование в браузере)
- ❌ JavaScript/Three.js визуализация

## CI/CD Интеграция

Для добавления в CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install pytest
      - name: Run tests
        run: |
          pytest tests/ -v
```

## Статистика тестов

```
======================== 85 passed, 1 skipped in 0.31s =========================
```

- **85 тестов пройдено**
- **1 тест пропущен** (требует ifcopenshell)
- **0 тестов упало**

## Добавление новых тестов

1. Создайте новый тестовый файл `test_<module>.py`
2. Добавьте тестовые классы с префиксом `Test`
3. Добавьте тестовые методы с префиксом `test_`
4. Запустите тесты: `pytest tests/test_<module>.py -v`

## Примеры тестов

### Тест валидации
```python
def test_validate_invalid_bolt_type():
    """Валидация должна падать для неизвестного типа болта"""
    from gost_data import validate_parameters
    
    with pytest.raises(ValueError) as exc_info:
        validate_parameters('9.9', 1, 20, 800, '09Г2С')
    
    assert 'Неизвестный тип болта' in str(exc_info.value)
```

### Тест кэширования
```python
def test_get_or_create_stud_type_caching():
    """get_or_create_stud_type должен кэшировать результаты"""
    from type_factory import TypeFactory
    
    mock_ifc = MockIfcDoc()
    factory = TypeFactory(mock_ifc)
    
    result1 = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
    result2 = factory.get_or_create_stud_type('1.1', 1, 20, 800, '09Г2С')
    
    # Должен вернуться тот же объект из кэша
    assert result1 is result2
```

### Тест геометрии
```python
def test_create_nut_solid():
    """create_nut_solid должен создавать геометрию гайки"""
    from geometry_builder import GeometryBuilder
    
    mock_ifc = MockIfcDoc()
    builder = GeometryBuilder(mock_ifc)
    
    result = builder.create_nut_solid(20, 18)
    
    assert result is not None
    assert result.is_a() == 'IfcShapeRepresentation'
```

## Отчёт о покрытии

Для генерации отчёта о покрытии:

```bash
# Установка coverage
pip install coverage

# Запуск с coverage
coverage run -m pytest tests/
coverage report -m
coverage html  # HTML отчёт в htmlcov/
```

## Решение проблем

### Segmentation fault при тестировании
Если тесты вызывают segmentation fault (обычно из-за ifcopenshell.geom):
1. Используйте mock для изоляции ifcopenshell.geom
2. Пометьте тест как `@pytest.mark.skipif` для сред без ifcopenshell

### RuntimeError: IFC документ не инициализирован
Для тестов требующих инициализированный IFC документ:
1. Используйте mock для `get_ifc_document()`
2. Или пометьте тест как интеграционный и пропускайте в unit-тестах

## Ресурсы

- [pytest документация](https://docs.pytest.org/)
- [unittest.mock документация](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py документация](https://coverage.readthedocs.io/)
