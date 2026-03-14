# 📋 Phase 0: Подготовка

**Длительность:** 1-2 дня  
**Приоритет:** 🔴 Критический  
**Статус:** ⏳ Ожидает

---

## ⚠️ Проверка перед началом

**Это первая фаза — предыдущие шаги не требуются.**

Перед началом Phase 0 убедитесь:
- [ ] У вас есть доступ к репозиторию
- [ ] Установлен Python 3.13
- [ ] Установлен Node.js (опционально, для JavaScript тестов)
- [ ] Все зависимости установлены (`pip install -r requirements.txt`)

---

## 📌 Обзор фазы

Подготовительная фаза для настройки инфраструктуры разработки перед началом основного рефакторинга.

### Цели:
- ✅ Настроить pre-commit hooks для автоматического форматирования
- ✅ Убедиться, что все 107 тестов проходят
- ✅ Настроить CI/CD (опционально)
- ✅ Зафиксировать текущее состояние кода

---

## 📝 Задачи

### 0.1. Настройка pre-commit hooks

**Файл:** `.pre-commit-config.yaml`

**Шаги:**

#### 0.1.1. Создать файл `.pre-commit-config.yaml`

```yaml
# .pre-commit-config.yaml
# Автоматическое форматирование и линтинг кода

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
        args: ["--max-line-length=100", "--ignore=E501,W503"]

  # mypy - статическая проверка типов
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        args: ["--ignore-missing-imports", "--no-strict-optional"]
        additional_dependencies:
          - types-all
```

#### 0.1.2. Установить pre-commit

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Установка pre-commit и зависимостей
pip install pre-commit black isort flake8 mypy

# Установка git hook
pre-commit install

# Проверка установки
pre-commit --version
```

#### 0.1.3. Запустить на всех файлах

```bash
# Запустить на всех файлах в репозитории
pre-commit run --all-files

# Ожидаемый результат:
# black - passed
# isort - passed
# flake8 - passed
# mypy - passed (с предупреждениями о missing imports)
```

#### 0.1.4. Проверка работы hook

```bash
# Создать тестовый файл
echo "print('hello')" > test_hook.py

# Попытаться сделать commit
git add test_hook.py
git commit -m "test: pre-commit hook"

# Ожидаемый результат: файлы будут отформатированы автоматически
```

**Критерии приёмки:**
- [ ] Файл `.pre-commit-config.yaml` создан
- [ ] `pre-commit install` выполнен успешно
- [ ] `pre-commit run --all-files` проходит без ошибок
- [ ] Hook автоматически форматирует код при commit

---

### 0.2. Проверка тестов

**Шаги:**

#### 0.2.1. Запустить все тесты

```bash
cd /Users/vdobranov/Yandex.Disk.localized/Python/Mac/ANCHOR-BOLT-GENERATOR
source .venv/bin/activate

# Запустить все тесты
pytest tests/ -v --tb=short

# Ожидаемый результат:
# ============================= 107 passed in 0.56s ==============================
```

#### 0.2.2. Запустить с покрытием

```bash
# Установить coverage
pip install coverage pytest-cov

# Запустить с покрытием
pytest tests/ -v --cov=python --cov-report=html --cov-report=term-missing

# Открыть отчёт
open htmlcov/index.html
```

#### 0.2.3. Запустить отдельные модули

```bash
# Тесты для каждого модуля
pytest tests/test_gost_data.py -v              # 36 тестов
pytest tests/test_geometry_builder.py -v       # 15 тестов
pytest tests/test_type_factory.py -v           # 17 тестов
pytest tests/test_instance_factory.py -v       # 14 тестов
pytest tests/test_material_manager.py -v       # 12 тестов
pytest tests/test_main.py -v                   # 10 тестов
pytest tests/test_utils.py -v                  # 3 теста
```

#### 0.2.4. Зафиксировать результат

```bash
# Сохранить результат в файл
pytest tests/ -v --tb=short > refactoring/test_results_before_refactoring.txt

# Создать снимок покрытия
coverage run -m pytest tests/
coverage report -m > refactoring/coverage_before_refactoring.txt
coverage html -d refactoring/coverage_before_refactoring
```

**Критерии приёмки:**
- [ ] Все 107 тестов проходят
- [ ] Покрытие кода зафиксировано
- [ ] Результаты сохранены в `refactoring/`

---

### 0.3. Настройка CI/CD (опционально)

**Файл:** `.github/workflows/tests.yml`

**Шаги:**

#### 0.3.1. Создать workflow файл

```yaml
# .github/workflows/tests.yml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12', '3.13']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest ifcopenshell numpy coverage pytest-cov

      - name: Run tests with coverage
        run: |
          pytest tests/ -v --cov=python --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          flags: unittests
          name: codecov-umbrella
```

#### 0.3.2. Настроить Codecov (опционально)

```bash
# Добавить репозиторий на https://codecov.io/
# Получить токен и добавить в GitHub Secrets
```

**Критерии приёмки:**
- [ ] Workflow файл создан
- [ ] Тесты запускаются при push/PR
- [ ] Покрытие загружается в Codecov

---

### 0.4. Фиксация текущего состояния

**Шаги:**

#### 0.4.1. Создать ветку для рефакторинга

```bash
# Убедиться, что мы на main
git checkout main
git pull

# Создать ветку для рефакторинга
git checkout -b refactor/phase0-preparation

# Закоммитить текущее состояние
git add .
git commit -m "chore: фиксация состояния перед рефакторингом"
git push -u origin refactor/phase0-preparation
```

#### 0.4.2. Создать чеклист фазы

Скопировать этот файл в `refactoring/PHASE_0_TODO.md`

#### 0.4.3. Обновить главный README

Добавить секцию "Refactoring Progress" в `README.md`:

```markdown
## 🔄 Refactoring Progress

| Фаза | Статус | Дата начала | Дата завершения |
|------|--------|-------------|-----------------|
| 0 - Подготовка | ⏳ Ожидает | - | - |
| 1 - Критические исправления | ⏳ Ожидает | - | - |
| 2 - Разделение модулей | ⏳ Ожидает | - | - |
| 3 - Улучшение геометрии | ⏳ Ожидает | - | - |
| 4 - Устранение зависимостей | ⏳ Ожидает | - | - |
| 5 - Улучшение архитектуры | ⏳ Ожидает | - | - |
| 6 - Type hints | ⏳ Ожидает | - | - |
| 7 - Улучшение тестов | ⏳ Ожидает | - | - |
| 8 - JavaScript рефакторинг | ⏳ Ожидает | - | - |
```

**Критерии приёмки:**
- [ ] Ветка создана
- [ ] Текущее состояние закоммичено
- [ ] README обновлён

---

## ✅ Чеклист завершения фазы 0

### Обязательные задачи:
- [ ] 0.1.1. Файл `.pre-commit-config.yaml` создан
- [ ] 0.1.2. Pre-commit установлен и настроен
- [ ] 0.1.3. `pre-commit run --all-files` проходит
- [ ] 0.2.1. Все 107 тестов проходят
- [ ] 0.2.2. Покрытие зафиксировано
- [ ] 0.4.1. Ветка создана

### Опциональные задачи:
- [ ] 0.3.1. CI/CD workflow создан
- [ ] 0.3.2. Codecov настроен

---

## 📊 Метрики фазы

| Метрика | Значение |
|---------|----------|
| Длительность | 1-2 дня |
| Сложность | Низкая |
| Риск | Минимальный |
| Файлов изменено | 2-3 |
| Строк добавлено | ~50 |

---

## 🚀 Следующие шаги

После завершения фазы 0:

1. Убедиться, что все чек-боксы отмечены
2. Создать pull request
3. Получить approval
4. Перейти к **Фазе 1**

**Ссылка на следующую фазу:** `refactoring/PHASE_1_TODO.md`

---

## 📚 Приложения

### A. Команды для быстрой проверки

```bash
# Быстрая проверка тестов
pytest tests/ -q

# Проверка конкретного модуля
pytest tests/test_gost_data.py -q

# Запуск pre-commit
pre-commit run --all-files

# Проверка стиля
black --check python/
isort --check python/
flake8 python/
```

### B. Полезные ссылки

- [Black документация](https://black.readthedocs.io/)
- [isort документация](https://pycqa.github.io/isort/)
- [flake8 документация](https://flake8.pycqa.org/)
- [mypy документация](https://mypy.readthedocs.io/)
- [pre-commit документация](https://pre-commit.com/)
- [pytest документация](https://docs.pytest.org/)

---

**Версия:** 1.0  
**Дата создания:** 2026-03-14  
**Автор:** AI Assistant  
**Статус:** Готов к выполнению
