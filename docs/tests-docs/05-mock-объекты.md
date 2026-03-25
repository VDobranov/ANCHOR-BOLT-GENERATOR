# Mock объекты

## Назначение

Mock объекты используются для изоляции тестов от внешних зависимостей (ifcopenshell.geom).

## Python Mock классы (conftest.py)

### MockIfcEntity

Mock для IFC сущности:

```python
from conftest import MockIfcEntity, MockIfcDoc

class MockIfcEntity:
    """Mock для IFC сущности"""
    def __init__(self, entity_type: str, *args, **kwargs):
        self._entity_type = entity_type
        self._kwargs = kwargs

    def is_a(self) -> str:
        """Получение типа сущности"""
        return self._entity_type

    @property
    def dim(self) -> Optional[int]:
        """Определение размерности"""
        ...
```

### MockIfcDoc

Mock для IFC документа:

```python
class MockIfcDoc:
    """Mock для IFC документа"""
    def __init__(self):
        self.entities: List[MockIfcEntity] = []
        self._by_type: Dict[str, List[MockIfcEntity]] = {}

    def create_entity(self, entity_type: str, *args, **kwargs) -> MockIfcEntity:
        """Создание IFC сущности"""
        ...

    def by_type(self, entity_type: str) -> List[MockIfcEntity]:
        """Получение сущностей по типу"""
        ...
```

## Использование Mock в тестах

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

## Когда использовать Mock

| Ситуация                      | Решение                    |
| ----------------------------- | -------------------------- |
| Тесты с ifcopenshell.geom     | MockIfcDoc                 |
| Сегментация при тестировании  | Mock + @pytest.mark.skipif |
| Изоляция внешних зависимостей | unittest.mock.patch        |
