"""
Step definitions на русском языке для IFC Gherkin тестов
"""

from behave import given, then, when
import ifcopenshell
import tempfile
import os
from pathlib import Path


@given('IFC файл с генератором анкерных болтов')
def step_load_anchor_bolt_ifc(context):
    """
    Загружает IFC файл сгенерированный генератором анкерных болтов.
    """
    # Импортируем генератор
    from main import initialize_base_document, reset_doc_manager
    from instance_factory import InstanceFactory
    
    # Создаём новый документ
    reset_doc_manager()
    ifc_doc = initialize_base_document('test')
    
    # Создаём болт
    builder = InstanceFactory(ifc_doc, geometry_type='solid')
    result = builder.create_bolt_assembly(
        bolt_type='1.1',
        diameter=20,
        length=500,
        material='09Г2С',
        assembly_class='IfcMechanicalFastener',
        assembly_mode='separate',
        geometry_type='solid'
    )
    
    # Сохраняем модель в контекст
    context.model = ifc_doc
    context.ifc_file = result['ifc_doc']


@then('Должно быть ровно {num:d} экземпляр(ов) .{entity}.')
def step_check_entity_count_exact(context, num, entity):
    """
    Проверяет что количество сущностей равно указанному.
    """
    if context.model is None:
        raise RuntimeError("Модель не загружена. Используйте 'Given IFC файл...'")
    
    instances = context.model.by_type(entity)
    actual_count = len(instances)
    
    assert actual_count == num, (
        f"Ожидалось {num} экземпляр(ов) {entity}, "
        f"но найдено {actual_count}"
    )


@then('Должно быть хотя бы {num:d} экземпляр(ов) .{entity}.')
def step_check_entity_count_at_least(context, num, entity):
    """
    Проверяет что количество сущностей не меньше указанного.
    """
    if context.model is None:
        raise RuntimeError("Модель не загружена. Используйте 'Given IFC файл...'")
    
    instances = context.model.by_type(entity)
    actual_count = len(instances)
    
    assert actual_count >= num, (
        f"Ожидалось хотя бы {num} экземпляр(ов) {entity}, "
        f"но найдено {actual_count}"
    )


@then('Должно быть не более {num:d} экземпляр(ов) .{entity}.')
def step_check_entity_count_at_most(context, num, entity):
    """
    Проверяет что количество сущностей не больше указанного.
    """
    if context.model is None:
        raise RuntimeError("Модель не загружена. Используйте 'Given IFC файл...'")
    
    instances = context.model.by_type(entity)
    actual_count = len(instances)
    
    assert actual_count <= num, (
        f"Ожидалось не более {num} экземпляр(ов) {entity}, "
        f"но найдено {actual_count}"
    )
