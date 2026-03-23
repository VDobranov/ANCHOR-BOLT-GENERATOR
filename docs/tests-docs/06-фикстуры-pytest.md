# Фикстуры pytest

## Встроенные фикстуры (conftest.py)

### mock_ifc_doc

Создание Mock IFC документа:

```python
@pytest.fixture(scope="function")
def mock_ifc_doc() -> MockIfcDoc:
    """Создание Mock IFC документа"""
    return MockIfcDoc()
```

### valid_bolt_params

Параметры валидного болта по умолчанию:

```python
@pytest.fixture(scope="function")
def valid_bolt_params() -> Dict[str, Any]:
    """Параметры валидного болта по умолчанию"""
    return {"bolt_type": "1.1", "diameter": 20, "length": 800, "material": "09Г2С"}
```

### all_bolt_types

Все поддерживаемые типы болтов:

```python
@pytest.fixture(scope="function")
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ["1.1", "1.2", "2.1", "5"]
```

### Дополнительные фикстуры

```python
@pytest.fixture(scope="function")
def all_diameters():
    """Все доступные диаметры"""
    return [12, 16, 20, 24, 30, 36, 42, 48]

@pytest.fixture(scope="function")
def all_materials():
    """Все доступные материалы"""
    return ["09Г2С", "ВСт3пс2", "10Г2"]
```

## Использование фикстур

```python
def test_with_fixture(mock_ifc_doc, valid_bolt_params):
    """Тест с использованием фикстур"""
    from instance_factory import InstanceFactory

    factory = InstanceFactory(mock_ifc_doc)
    result = factory.create_bolt_assembly(**valid_bolt_params)

    assert result is not None
```

## Область действия (scope)

| Scope | Описание |
|-------|----------|
| `function` | Новая фикстура для каждого теста (по умолчанию) |
| `class` | Одна фикстура для всех тестов в классе |
| `module` | Одна фикстура для всех тестов в модуле |
| `session` | Одна фикстура для всей сессии тестов |

## Параметризация фикстур

```python
@pytest.fixture(params=["1.1", "1.2", "2.1", "5"])
def bolt_type(request):
    """Параметризованная фикстура для типов болтов"""
    return request.param
```
