# Anchor Bolt Generator Documentation

Эта директория содержит документацию для проекта Anchor Bolt Generator.

## Быстрый старт

### Просмотр документации

Откройте `docs/_build/index.html` в браузере после сборки.

### Сборка документации

```bash
# Активация виртуального окружения
source .venv/bin/activate

# Сборка HTML документации
sphinx-build -b html docs docs/_build

# Или с автообновлением при изменении файлов
sphinx-autobuild docs docs/_build
```

### Структура документации

```
docs/
├── conf.py              # Конфигурация Sphinx
├── index.rst            # Главная страница
├── api/
│   └── modules.rst      # Python модули
├── python/              # Автогенерированные RST файлы
│   ├── modules.rst
│   ├── data.rst
│   ├── services.rst
│   └── ...
└── _build/              # Собранные HTML файлы (игнорируется git)
```

## API документация

Документация генерируется автоматически из docstrings в коде Python.

### Основные модули:

- **data/** — Данные ГОСТ (размеры болтов, гаек, шайб, материалы)
- **services/** — Сервисы (DimensionService)
- **geometry_builder.py** — Построение геометрии IFC
- **type_factory.py** — Фабрика типов IFC
- **instance_factory.py** — Фабрика инстансов
- **material_manager.py** — Менеджер материалов
- **document_manager.py** — Менеджер IFC документов
- **protocols.py** — Protocol интерфейсы для DI
- **container.py** — DI контейнер

### Type hints

Все модули имеют type hints. Документация включает информацию о типах параметров и возвращаемых значений.

## Разработка

### Добавление новой страницы документации

1. Создайте `.rst` файл в `docs/` или `docs/api/`
2. Добавьте ссылку в `index.rst` или соответствующий `toctree`
3. Запустите `sphinx-build`

### Формат docstrings

Используется Google style docstrings:

```python
def my_function(param1: int, param2: str) -> bool:
    """
    Краткое описание функции.

    Подробное описание функции, если необходимо.

    Args:
        param1: Описание параметра 1
        param2: Описание параметра 2

    Returns:
        Описание возвращаемого значения

    Raises:
        ValueError: Описание исключения
    """
    return True
```

## Зависимости

Для сборки документации требуются:

- sphinx
- sphinx-autodoc-typehints
- sphinx-rtd-theme

Установка:

```bash
pip install sphinx sphinx-autodoc-typehints sphinx-rtd-theme
```
