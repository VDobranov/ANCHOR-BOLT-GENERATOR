# Gherkin-валидация IFC

## Обзор

Проект использует **ifc-gherkin-rules** (buildingSMART) для валидации IFC-моделей на соответствие спецификации.

## Структура

```
tests/features/
└── environment.py              # Конфигурация Behave

external/ifc-gherkin-rules/
└── features/rules/             # 100+ правил валидации
    ├── IFC/                    # Правила IFC (IFC101, IFC102)
    ├── MPD/                    # RepresentationType/Identifier (MPD001)
    ├── GEM/                    # Геометрическая валидация
    ├── SPS/                    # Пространственная структура
    └── ...
```

## Запуск валидации

```bash
# Запуск всех правил
behave tests/features/

# Конкретное правило
behave external/ifc-gherkin-rules/features/rules/IFC/IFC101*.feature

# С исключением правил
behave external/ifc-gherkin-rules/features/rules/ \
  --exclude features/rules/GEM/GEM113*.feature
```

## Пример правила (Gherkin)

```gherkin
Feature: IFC101 - Only official IFC versions allowed

  Scenario: Verifying Current Schema Identifier
    Given An IFC model
    Then The Schema Identifier of the model must be 'IFC2X3' or 'IFC4' or 'IFC4X3_ADD2'
```

## Конфигурация

`tests/features/environment.py`:

```python
def before_all(context):
    # Путь к step definitions из buildingSMART
    gherkin_rules_path = project_root / "external" / "ifc-gherkin-rules" / "features" / "steps"
    sys.path.insert(0, str(gherkin_rules_path))

def before_scenario(context, scenario):
    context.model = None
    context.ifc_file = None
```

## Категории правил

| Категория | Описание                        | Примеры        |
| --------- | ------------------------------- | -------------- |
| IFC       | Версия IFC, deprecated сущности | IFC101, IFC102 |
| MPD       | RepresentationType/Identifier   | MPD001         |
| GEM       | Геометрическая валидация        | GEM001, GEM003 |
| SPS       | Пространственная структура      | SPS001, SPS007 |

## Исключения

- **GEM113** — известный баг в валидаторе buildingSMART (класс Line без @dataclass)
- Исключается в CI/CD до фикса в upstream
