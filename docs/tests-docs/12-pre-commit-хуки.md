# Pre-commit хуки

## Обзор

Проект использует pre-commit для автоматических проверок кода.

## Установка

```bash
# Установка pre-commit
pip install pre-commit
pre-commit install

# Запуск всех проверок
pre-commit run --all-files
```

## Проверки

| Хук | Назначение |
|-----|------------|
| **black** | Форматирование Python кода |
| **isort** | Сортировка импортов |
| **flake8** | Линтинг кода |
| **mypy** | Проверка type hints |

## Конфигурация (.pre-commit-config.yaml)

```yaml
repos:
  # Black - форматирование Python кода
  - repo: https://github.com/psf/black
    rev: 24.1.0
    hooks:
      - id: black
        language_version: python3.13
        args: [--line-length=100]

  # isort - сортировка импортов
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
        args: ["--profile", "black", "--line-length=100"]

  # flake8 - линтер
  - repo: https://github.com/pycqa/flake8
    rev: 7.0.0
    hooks:
      - id: flake8
        args: ["--max-line-length=100", "--ignore=E501,W503,F401,F841"]

  # mypy - проверка типов
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ["--ignore-missing-imports", "--no-strict-optional"]
```

## Исключения

- `tests/` — исключён из flake8 и mypy (Mock классы)
- Игнорируемые ошибки: E501, W503, F401, F841, E402, E731

## Запуск перед коммитом

```bash
# Автоматический запуск при git commit
git commit -m "Сообщение"

# Ручной запуск
pre-commit run --all-files
```
