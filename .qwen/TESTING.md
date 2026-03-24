# TDD Workflow для ANCHOR-BOLT-GENERATOR

## Обзор

TDD-подход к разработке: три уровня тестирования (Python unit-тесты, JavaScript unit-тесты, IFC-валидация Gherkin). Статистика: 276 Python тестов, 97 JavaScript тестов, 100+ правил валидации IFC.

→ Подробнее: [docs/tests-docs/01-обзор.md](../docs/tests-docs/01-обзор.md)

## Быстрый старт

Запуск всех тестов: `pytest tests/ -v` (Python), `npm test` (JavaScript). Запуск с покрытием: `pytest --cov=python`, `npm run test:coverage`. Фильтрация по имени: `-k <pattern>`, `::<TestClass>::<method>`.

→ Подробнее: [docs/tests-docs/02-быстрый-старт.md](../docs/tests-docs/02-быстрый-старт.md)

## Структура тестов

Python: 15 тестовых файлов в `tests/` (conftest.py с Mock-классами, тесты модулей python/). JavaScript: 6 файлов в `js/tests/` (setup.js с mock глобальных объектов, тесты утилит, сервисов, констант). Gherkin: environment.py + 100 правил buildingSMART в `external/ifc-gherkin-rules/`.

→ Подробнее: [docs/tests-docs/03-структура-тестов.md](../docs/tests-docs/03-структура-тестов.md)

## TDD Процесс

Цикл Red-Green-Refactor: (1) тест падает → (2) минимальная реализация → (3) рефакторинг. Завершение: `pytest tests/ -v && npm test && pre-commit run --all-files`.

→ Подробнее: [docs/tests-docs/04-tdd-процесс.md](../docs/tests-docs/04-tdd-процесс.md)

## Mock объекты

MockIfcEntity и MockIfcDoc (conftest.py) изолируют тесты от ifcopenshell.geom. unittest.mock.patch для моков методов. Для JavaScript: mock THREE, DOM, UI в `js/tests/setup.js`.

→ Подробнее: [docs/tests-docs/05-mock-объекты.md](../docs/tests-docs/05-mock-объекты.md)

## Фикстуры pytest

Встроенные: mock_ifc_doc, valid_bolt_params, all_bolt_types, all_diameters, all_materials. Scope: function/class/module/session. Параметризация: `@pytest.fixture(params=[...])`.

→ Подробнее: [docs/tests-docs/06-фикстуры-pytest.md](../docs/tests-docs/06-фикстуры-pytest.md)

## Покрытие тестами

Python: 95% (данные, сервисы, фабрики, менеджеры, контейнер). JavaScript: 100% (утилиты, сервисы, константы, статусы). Не покрывается: geometry_converter, ifc_generator, main, validate_utils, protocols, utils, geometry_builder, instance_factory, document_manager (сложные mock или интеграционные зависимости).

→ Подробнее: [docs/tests-docs/07-покрытие-тестами.md](../docs/tests-docs/07-покрытие-тестами.md)

## Gherkin-валидация IFC

buildingSMART ifc-gherkin-rules: 100+ правил (IFC, MPD, GEM, SPS). Запуск: `behave tests/features/`. Исключения: GEM113 (баг валидатора).

→ Подробнее: [docs/tests-docs/08-gherkin-валидация.md](../docs/tests-docs/08-gherkin-валидация.md)

## CI/CD Интеграция

GitHub Actions (ifc-validation.yml): триггеры push/PR → Gherkin Validation (buildingSMART) → Pytest → JS Tests. Этапы: checkout, setup-python/setup-node, dependencies, generate IFC, validation, js-tests.

→ Подробнее: [docs/tests-docs/09-ci-cd.md](../docs/tests-docs/09-ci-cd.md)

## Статистика тестов

Python: 276 passed, 1 skipped. JavaScript: 97 passed.

## Добавление новых тестов

Python: создать test*<module>.py, импортировать Mock из conftest, класс Test<Module>, методы test*\*. JavaScript: <module>.test.js, describe/test. Best practices: фикстуры, mock, один тест — одна проверка.

→ Подробнее: [docs/tests-docs/10-добавление-новых-тестов.md](../docs/tests-docs/10-добавление-новых-тестов.md)

## Примеры тестов

Типы тестов: валидация (assert/raises), кэширование (is), геометрия (is_a), DI (кэширование), JavaScript (expect).

→ Подробнее: [docs/tests-docs/11-примеры-тестов.md](../docs/tests-docs/11-примеры-тестов.md)

## Pre-commit хуки

Автоматические проверки: black (форматирование), isort (импорты), flake8 (линтинг), mypy (типы), prettier (JS/CSS/MD), eslint (JS). Исключения: tests/. Установка: `pre-commit install`.

→ Подробнее: [docs/tests-docs/12-pre-commit-хуки.md](../docs/tests-docs/12-pre-commit-хуки.md)

## Решение проблем

Типовые проблемы: Segmentation fault (mock ifcopenshell.geom), RuntimeError (mock IFC), ModuleNotFoundError (PYTHON_MODULES), Jest import error (type: module + .js).

→ Подробнее: [docs/tests-docs/13-решение-проблем.md](../docs/tests-docs/13-решение-проблем.md)

## Ресурсы

Внешние: pytest, unittest.mock, Coverage.py, Jest, Pre-commit, buildingSMART ifc-gherkin-rules, IFC4 ADD2 TC1. Внутренние: ARCHITECTURE.md, workflow.md, js/tests/README.md.

→ Подробнее: [docs/tests-docs/14-ресурсы.md](../docs/tests-docs/14-ресурсы.md)
