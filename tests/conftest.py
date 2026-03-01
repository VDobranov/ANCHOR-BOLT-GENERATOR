"""
Конфигурация и фикстуры для pytest тестов
"""
import sys
import os

# Добавляем python директорию в path для импортов
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

import pytest


@pytest.fixture(scope='session')
def python_path():
    """Возвращает путь к python модулям"""
    return os.path.join(os.path.dirname(__file__), '..', 'python')


@pytest.fixture(scope='function')
def valid_bolt_params():
    """Параметры валидного болта по умолчанию"""
    return {
        'bolt_type': '1.1',
        'execution': 1,
        'diameter': 20,
        'length': 800,
        'material': '09Г2С'
    }


@pytest.fixture(scope='function')
def all_bolt_types():
    """Все поддерживаемые типы болтов"""
    return ['1.1', '1.2', '2.1', '5']


@pytest.fixture(scope='function')
def all_diameters():
    """Все доступные диаметры"""
    return [12, 16, 20, 24, 30, 36, 42, 48]


@pytest.fixture(scope='function')
def all_materials():
    """Все доступные материалы"""
    return ['09Г2С', 'ВСт3пс2', '10Г2']
