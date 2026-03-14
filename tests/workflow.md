# TDD Workflow для ANCHOR-BOLT-GENERATOR

## Обзор

Проект использует Test-Driven Development (TDD) подход для разработки Python и JavaScript модулей.

## Быстрый старт

### Запуск всех Python тестов
```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate
pytest tests/ -v
```

### Запуск всех JavaScript тестов
```bash
npm test
```

### Запуск тестов с покрытием (Python)
```bash
pytest tests/ --cov=python --cov-report=term-missing
```

### Запуск тестов с покрытием (JavaScript)
```bash
npm run test:coverage
```

## Запуск тестов для конкретных модулей

```bash
# Python тесты
pytest tests/test_gost_data.py -v
pytest tests/test_geometry_builder.py -v
pytest tests/test_type_factory.py -v
pytest tests/test_instance_factory.py -v
pytest tests/test_document_manager.py -v
pytest tests/test_container.py -v
pytest tests/test_dimension_service.py -v

# JavaScript тесты
npm test -- js/tests/validationService.test.js
npm test -- js/tests/helpers.test.js
npm test -- js/tests/constants.test.js
```

### Запуск тестов с фильтрацией по имени
```bash
# Тесты валидации
pytest tests/test_gost_data.py::TestValidateParameters -v

# Тесты кэширования
pytest tests/test_type_factory.py -k caching -v

# Тесты DI контейнера
pytest tests/test_container.py -k register -v
```

## Структура тестов

### Python тесты
```
tests/
├── conftest.py                    # Фикстуры и Mock классы
├── test_utils.py                  # Тесты utils.py
├── test_validate_utils.py         # Тесты validate_utils.py
├── test_gost_data.py              # Тесты gost_data.py
├── test_geometry_builder.py       # Тесты geometry_builder.py
├── test_geometry_converter.py     # Тесты geometry_converter.py
├── test_type_factory.py           # Тесты type_factory.py
├── test_instance_factory.py       # Тесты instance_factory.py
├── test_material_manager.py       # Тесты material_manager.py
├── test_main.py                   # Тесты main.py
├── test_document_manager.py       # Тесты document_manager.py
├── test_container.py              # Тесты container.py
├── test_dimension_service.py      # Тесты dimension_service.py
└── validate_utils.py              # Утилиты валидации
```

### JavaScript тесты
```
js/tests/
├── validationService.test.js      # Тесты validationService
├── helpers.test.js                # Тесты helpers
└── constants.test.js              # Тесты constants
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
- Добавление type hints

### 5. Повторный запуск тестов
```bash
pytest tests/ -v  # Все тесты должны пройти
pre-commit run --all-files  # Все проверки должны пройти
```

## Mock объекты

### Python Mock классы (в conftest.py)

```python
from conftest import MockIfcEntity, MockIfcDoc

class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type: str, *args, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs

    def is_a(self) -> str:
        return self._entity_type

    @property
    def dim(self) -> Optional[int]:
        # Определение размерности
        ...

class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities: List[MockIfcEntity] = []
        self._by_type: Dict[str, List[MockIfcEntity]] = {}

    def create_entity(self, entity_type: str, *args, **kwargs) -> MockIfcEntity:
        ...

    def by_type(self, entity_type: str) -> List[MockIfcEntity]:
        ...
```

### Использование Mock в тестах

```python
from conftest import MockIfcDoc

def test_create_bolt_assembly():
    """Тест с Mock документом"""
    from instance_factory import InstanceFactory

    mock_ifc = MockIfcDoc()
    factory = InstanceFactory(mock_ifc)

    result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')

    assert isinstance(result, dict)
    assert 'mesh_data' in result
```

## Использование patch для моков

```python
from unittest.mock import patch

def test_create_bolt_assembly_with_mock():
    """Тест с моком _generate_mesh_data"""
    from instance_factory import InstanceFactory
    from conftest import MockIfcDoc

    mock_ifc = MockIfcDoc()
    factory = InstanceFactory(mock_ifc)

    # Мокаем метод чтобы избежать ifcopenshell.geom
    with patch.object(factory, '_generate_mesh_data', return_value={'meshes': []}):
        result = factory.create_bolt_assembly('1.1', 1, 20, 800, '09Г2С')

    assert isinstance(result, dict)
```

## Фикстуры pytest

### Встроенные фикстуры (conftest.py)

```python
@pytest.fixture(scope="function")
def mock_ifc_doc():
    """Создание Mock IFC документа"""
    return MockIfcDoc()

@pytest.fixture(scope="function")
def valid_bolt_params():
    """Параметры валидного болта по умолчанию"""
    return {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}

@pytest.fixture(scope="function")
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ["1.1", "1.2", "2.1", "5"]
```

### Использование фикстур

```python
def test_with_fixture(mock_ifc_doc, valid_bolt_params):
    """Тест с использованием фикстур"""
    from instance_factory import InstanceFactory

    factory = InstanceFactory(mock_ifc_doc)
    result = factory.create_bolt_assembly(**valid_bolt_params)

    assert result is not None
```

## Покрытие тестами

### Покрывается тестами:
- ✅ Валидация параметров (gost_data.py, validate_utils.py)
- ✅ Справочники и размеры (data/*.py)
- ✅ Сервисы (services/dimension_service.py)
- ✅ Построение геометрии (geometry_builder.py)
- ✅ Кэширование типов (type_factory.py)
- ✅ Создание инстансов (instance_factory.py)
- ✅ Менеджер материалов (material_manager.py)
- ✅ Менеджер документов (document_manager.py)
- ✅ DI контейнер (container.py)
- ✅ Protocol интерфейсы (protocols.py)
- ✅ JavaScript утилиты (js/utils/*.js)
- ✅ JavaScript сервисы (js/services/*.js)
- ✅ JavaScript константы (js/core/constants.js)

### Не покрывается тестами:
- ❌ Интеграция с ifcopenshell.geom (требуется Pyodide)
- ❌ Генерация IFC файлов в браузере (интеграционное тестирование)
- ❌ Three.js визуализация (JavaScript integration)
- ❌ geometry_converter.py (требует реальный ifcopenshell)

## CI/CD Интеграция

### Python тесты в CI/CD

```yaml
# .github/workflows/python-tests.yml
name: Python Tests

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
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run pre-commit
        run: |
          pip install pre-commit
          pre-commit run --all-files
      - name: Run tests with coverage
        run: |
          pytest tests/ --cov=python --cov-report=xml -v
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### JavaScript тесты в CI/CD

```yaml
# .github/workflows/js-tests.yml
name: JavaScript Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Статистика тестов

### Python тесты
```
======================== 152 passed, 2 skipped in 6.10s ========================
```

- **152 тестов пройдено**
- **2 теста пропущено** (требуют ifcopenshell.geom)
- **0 тестов упало**
- **Покрытие:** 82%

### JavaScript тесты
```
Test Suites: 3 passed, 3 total
Tests:       38 passed, 38 total
```

- **38 тестов пройдено**
- **0 тестов упало**
- **Покрытие:** ~70%

## Добавление новых тестов

### Python тесты

1. Создайте новый тестовый файл `test_<module>.py` в `tests/`
2. Импортируйте Mock классы из `conftest`
3. Добавьте тестовые классы с префиксом `Test`
4. Добавьте тестовые методы с префиксом `test_`
5. Запустите тесты: `pytest tests/test_<module>.py -v`

Пример:
```python
# tests/test_new_module.py
from conftest import MockIfcDoc

class TestNewModule:
    def test_something(self, mock_ifc_doc):
        from new_module import new_function
        result = new_function(mock_ifc_doc)
        assert result is not None
```

### JavaScript тесты

1. Создайте новый тестовый файл `<module>.test.js` в `js/tests/`
2. Импортируйте тестируемый модуль
3. Добавьте тесты с использованием `describe` и `test`
4. Запустите тесты: `npm test`

Пример:
```javascript
// js/tests/newModule.test.js
import { newFunction } from '../utils/newModule.js';

describe('newFunction', () => {
    test('должен возвращать правильное значение', () => {
        const result = newFunction(42);
        expect(result).toBe(84);
    });
});
```

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
    from conftest import MockIfcDoc

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
    from conftest import MockIfcDoc

    mock_ifc = MockIfcDoc()
    builder = GeometryBuilder(mock_ifc)

    result = builder.create_nut_solid(20, 18)

    assert result is not None
    assert result.is_a() == 'IfcShapeRepresentation'
```

### Тест DI контейнера
```python
def test_container_get_geometry_builder():
    """get_geometry_builder должен возвращать GeometryBuilder"""
    from container import DIContainer
    from conftest import MockIfcDoc

    mock_ifc = MockIfcDoc()
    container = DIContainer(mock_ifc)
    builder = container.get_geometry_builder()

    assert builder is not None
    # Проверка кэширования
    assert container.get_geometry_builder() is builder
```

### Тест JavaScript валидации
```javascript
import { ValidationService } from '../services/validationService.js';

describe('ValidationService.validateDiameter', () => {
    test('должен возвращать valid=true для правильного диаметра', () => {
        const result = ValidationService.validateDiameter(20);
        expect(result.valid).toBe(true);
        expect(result.error).toBeNull();
    });

    test('должен возвращать valid=false для неподдерживаемого диаметра', () => {
        const result = ValidationService.validateDiameter(15);
        expect(result.valid).toBe(false);
        expect(result.error).toContain('Диаметр должен быть одним из');
    });
});
```

## Отчёт о покрытии

### Python coverage

```bash
# Установка coverage
pip install pytest-cov

# Запуск с coverage
pytest tests/ --cov=python --cov-report=term-missing

# HTML отчёт
pytest tests/ --cov=python --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### JavaScript coverage

```bash
# Запуск с coverage
npm run test:coverage

# Отчёт в coverage/
open coverage/index.html
```

## Pre-commit хуки

Проект использует pre-commit для автоматических проверок:

```bash
# Установка pre-commit
pip install pre-commit
pre-commit install

# Запуск всех проверок
pre-commit run --all-files
```

### Проверки:
- ✅ **black** — форматирование кода
- ✅ **isort** — сортировка импортов
- ✅ **flake8** — линтинг
- ✅ **mypy** — проверка type hints

## Решение проблем

### Segmentation fault при тестировании
Если тесты вызывают segmentation fault (обычно из-за ifcopenshell.geom):
1. Используйте mock для изоляции ifcopenshell.geom
2. Пометьте тест как `@pytest.mark.skipif` для сред без ifcopenshell

### RuntimeError: IFC документ не инициализирован
Для тестов требующих инициализированный IFC документ:
1. Используйте mock для `get_ifc_document()`
2. Или пометьте тест как интеграционный

### ModuleNotFoundError в Pyodide
Если модуль не найден в Pyodide:
1. Добавьте модуль в `PYTHON_MODULES` в `js/core/config.js`
2. Убедитесь, что файл загружается в правильную директорию FS
3. Проверьте, что зависимости модуля также загружены

### JavaScript тесты не находят модули
1. Убедитесь, что `type: "module"` указан в `package.json`
2. Проверьте, что импорты используют `.js` расширение
3. Запустите `npm install` для установки зависимостей

## Ресурсы

- [pytest документация](https://docs.pytest.org/)
- [unittest.mock документация](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py документация](https://coverage.readthedocs.io/)
- [Jest документация](https://jestjs.io/)
- [Pre-commit документация](https://pre-commit.com/)
