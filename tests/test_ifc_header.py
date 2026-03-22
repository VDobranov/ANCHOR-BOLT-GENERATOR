"""
Тесты для проверки заголовка IFC файла согласно buildingSMART IFC Header Policy

https://github.com/buildingSMART/IFC4.x-IF/tree/header-policy/docs/IFC-file-header/README.md
"""

import re
import tempfile
import os
from datetime import datetime

import pytest

from main import initialize_base_document, reset_doc_manager
from instance_factory import InstanceFactory


def get_ifc_header(ifc_doc):
    """Извлечение заголовка из IFC документа"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as tmp:
        tmp_path = tmp.name
    
    ifc_doc.write(tmp_path)
    
    with open(tmp_path, 'r') as f:
        content = f.read()
    
    os.unlink(tmp_path)
    
    # Извлекаем заголовок
    header_start = content.find('HEADER;')
    header_end = content.find('ENDSEC')
    
    if header_start == -1 or header_end == -1:
        return None
    
    return content[header_start:header_end + 7]


def parse_header(header):
    """Парсинг заголовка IFC файла"""
    if not header:
        return None
    
    result = {}
    
    # FILE_DESCRIPTION
    desc_match = re.search(r"FILE_DESCRIPTION\(\(([^)]+)\),\s*'([^']+)'\)", header)
    if desc_match:
        result['description'] = desc_match.group(1)
        result['implementation_level'] = desc_match.group(2)
    
    # FILE_NAME
    name_match = re.search(
        r"FILE_NAME\(\s*'([^']*)',\s*'([^']*)',\s*\(([^)]*)\),\s*\(([^)]*)\),\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)",
        header
    )
    if name_match:
        result['name'] = name_match.group(1)
        result['time_stamp'] = name_match.group(2)
        result['author'] = name_match.group(3)
        result['organization'] = name_match.group(4)
        result['preprocessor_version'] = name_match.group(5)
        result['originating_system'] = name_match.group(6)
        result['authorization'] = name_match.group(7)
    
    # FILE_SCHEMA
    schema_match = re.search(r"FILE_SCHEMA\(\(\s*'([^']+)'\s*\)\)", header)
    if schema_match:
        result['schema'] = schema_match.group(1)
    
    return result


class TestIFCHeader:
    """Тесты для проверки заголовка IFC файла"""
    
    @pytest.fixture
    def ifc_doc(self):
        """Создание тестового IFC документа"""
        reset_doc_manager()
        ifc = initialize_base_document('test')
        builder = InstanceFactory(ifc, geometry_type='faceted')
        
        builder.create_bolt_assembly(
            bolt_type='1.1',
            diameter=20,
            length=500,
            material='09Г2С',
            assembly_class='IfcMechanicalFastener',
            assembly_mode='unified',
            geometry_type='faceted'
        )
        
        return ifc
    
    def test_header_exists(self, ifc_doc):
        """Заголовок IFC файла должен существовать"""
        header = get_ifc_header(ifc_doc)
        assert header is not None, "Заголовок IFC файла отсутствует"
        assert 'HEADER;' in header, "Отсутствует HEADER;"
        assert 'ENDSEC;' in header, "Отсутствует ENDSEC;"
    
    def test_header_order(self, ifc_doc):
        """Порядок секций заголовка: FILE_DESCRIPTION, FILE_NAME, FILE_SCHEMA"""
        header = get_ifc_header(ifc_doc)
        assert header is not None
        
        desc_pos = header.find('FILE_DESCRIPTION')
        name_pos = header.find('FILE_NAME')
        schema_pos = header.find('FILE_SCHEMA')
        
        assert desc_pos != -1, "Отсутствует FILE_DESCRIPTION"
        assert name_pos != -1, "Отсутствует FILE_NAME"
        assert schema_pos != -1, "Отсутствует FILE_SCHEMA"
        
        assert desc_pos < name_pos < schema_pos, \
            "Неправильный порядок секций: должно быть FILE_DESCRIPTION, FILE_NAME, FILE_SCHEMA"
    
    def test_file_description_exists(self, ifc_doc):
        """FILE_DESCRIPTION должен существовать"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed is not None, "Не удалось распарсить заголовок"
        assert 'description' in parsed, "Отсутствует description в FILE_DESCRIPTION"
        assert 'implementation_level' in parsed, "Отсутствует implementation_level в FILE_DESCRIPTION"
    
    def test_file_description_implementation_level(self, ifc_doc):
        """implementation_level должен быть '2;1' согласно ISO10303-21"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed['implementation_level'] == '2;1', \
            f"implementation_level должен быть '2;1', а не '{parsed['implementation_level']}'"
    
    def test_file_description_view_definition(self, ifc_doc):
        """ViewDefinition должен быть официальным для IFC4"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        # Для IFC4 официальные ViewDefinition: ReferenceView_V1.2, IFC4Precast
        valid_views = ['ReferenceView_V1.2', 'IFC4Precast']
        
        description = parsed['description']
        assert any(view in description for view in valid_views), \
            f"ViewDefinition '{description}' не является официальным для IFC4. " \
            f"Допустимые: {valid_views}"
    
    def test_file_name_exists(self, ifc_doc):
        """FILE_NAME должен существовать со всеми полями"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed is not None, "Не удалось распарсить заголовок"
        
        required_fields = [
            'name', 'time_stamp', 'author', 'organization',
            'preprocessor_version', 'originating_system', 'authorization'
        ]
        
        for field in required_fields:
            assert field in parsed, f"Отсутствует поле {field} в FILE_NAME"
    
    def test_file_name_not_empty(self, ifc_doc):
        """Поля FILE_NAME не должны быть пустыми"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        # name не должен быть пустым
        assert parsed['name'] and parsed['name'].strip(), \
            "FILE_NAME.name не должен быть пустым"
        
        # author не должен быть пустым
        author = parsed['author'].strip("' ")
        assert author, "FILE_NAME.author не должен быть пустым"
        
        # organization не должна быть пустой
        org = parsed['organization'].strip("' ")
        assert org, "FILE_NAME.organization не должна быть пустой"
        
        # authorization не должен быть пустым
        auth = parsed['authorization'].strip("' ")
        assert auth, "FILE_NAME.authorization не должен быть пустым"
    
    def test_file_name_timestamp_iso8601(self, ifc_doc):
        """time_stamp должен быть в формате ISO 8601"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        timestamp = parsed['time_stamp']
        
        # Проверяем формат ISO 8601
        iso8601_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        assert re.match(iso8601_pattern, timestamp), \
            f"time_stamp '{timestamp}' не соответствует формату ISO 8601"
        
        # Проверяем что часы указаны 2 цифрами (00-23)
        hour_match = re.search(r'T(\d{2}):', timestamp)
        assert hour_match, "Не удалось извлечь часы из time_stamp"
        
        hour = int(hour_match.group(1))
        assert 0 <= hour <= 23, f"Часы должны быть от 00 до 23, а не {hour}"
    
    def test_file_name_organization_not_software_company(self, ifc_doc):
        """organization не должно содержать имя компании-разработчика ПО"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        org = parsed['organization']
        originating = parsed['originating_system']
        
        # organization не должно совпадать с originating_system
        # (который содержит имя компании-разработчика)
        assert org != originating, \
            "organization не должно содержать имя компании-разработчика ПО"
    
    def test_file_name_originating_system_format(self, ifc_doc):
        """originating_system должен быть в формате 'Company - Application - Version'"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        originating = parsed['originating_system']
        
        # Проверяем наличие разделителей " - "
        parts = originating.split(' - ')
        assert len(parts) >= 3, \
            f"originating_system должен быть в формате 'Company - Application - Version', " \
            f"а не '{originating}'"
        
        # Проверяем что версия содержит только цифры и разделители (PEP440)
        version = parts[-1]
        # Разрешены цифры, точки, и суффиксы alpha, beta, rc
        pep440_pattern = r'^[\d.]+(-[a-zA-Z\d.]+)?$'
        assert re.match(pep440_pattern, version), \
            f"Версия '{version}' не соответствует формату PEP440"
    
    def test_file_name_originating_system_not_placeholder(self, ifc_doc):
        """originating_system не должно быть плейсхолдером"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        originating = parsed['originating_system']
        
        invalid_values = ['', '$', 'Unknown', 'IfcOpenShell']
        assert originating not in invalid_values, \
            f"originating_system не должно быть '{originating}'"
        
        # Не должно содержать только имя ОС
        assert originating.lower() != 'windows', \
            "originating_system не должно быть названием ОС"
    
    def test_file_schema_exists(self, ifc_doc):
        """FILE_SCHEMA должен существовать"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed is not None, "Не удалось распарсить заголовок"
        assert 'schema' in parsed, "Отсутствует schema в FILE_SCHEMA"
    
    def test_file_schema_valid_identifier(self, ifc_doc):
        """schema_identifier должен быть валидным"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        schema = parsed['schema']
        
        # Валидные схемы IFC
        valid_schemas = ['IFC2X3', 'IFC4', 'IFC4X3_ADD2', 'IFC4X3_ADD1']
        assert schema in valid_schemas, \
            f"schema '{schema}' не является валидной. Допустимые: {valid_schemas}"
    
    def test_file_schema_matches_view_definition(self, ifc_doc):
        """ViewDefinition должен соответствовать версии схемы"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        schema = parsed['schema']
        description = parsed['description']
        
        # Соответствие схем и ViewDefinition
        valid_combinations = {
            'IFC2X3': ['CoordinationView_V2.0', 'SpaceBoundaryAddonView', 
                       'BasicFMHandoverView', 'StructuralAnalysisView'],
            'IFC4': ['ReferenceView_V1.2', 'IFC4Precast'],
            'IFC4X3_ADD2': ['ReferenceView', 'Alignment-basedView'],
            'IFC4X3_ADD1': ['ReferenceView', 'Alignment-basedView'],
        }
        
        valid_views = valid_combinations.get(schema, [])
        
        if valid_views:
            assert any(view in description for view in valid_views), \
                f"ViewDefinition '{description}' не соответствует схеме '{schema}'. " \
                f"Допустимые: {valid_views}"


class TestIFCHeaderSeparateMode:
    """Тесты заголовка для separate режима"""
    
    @pytest.fixture
    def ifc_doc(self):
        reset_doc_manager()
        ifc = initialize_base_document('test')
        builder = InstanceFactory(ifc, geometry_type='faceted')
        
        builder.create_bolt_assembly(
            bolt_type='1.1',
            diameter=20,
            length=500,
            material='09Г2С',
            assembly_class='IfcMechanicalFastener',
            assembly_mode='separate',
            geometry_type='faceted'
        )
        
        return ifc
    
    def test_header_valid_separate(self, ifc_doc):
        """Заголовок должен быть валидным для separate режима"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed is not None
        assert parsed['schema'] == 'IFC4'
        assert parsed['implementation_level'] == '2;1'


class TestIFCHeaderSolidGeometry:
    """Тесты заголовка для solid геометрии"""
    
    @pytest.fixture
    def ifc_doc(self):
        reset_doc_manager()
        ifc = initialize_base_document('test')
        builder = InstanceFactory(ifc, geometry_type='solid')
        
        builder.create_bolt_assembly(
            bolt_type='1.1',
            diameter=20,
            length=500,
            material='09Г2С',
            assembly_class='IfcMechanicalFastener',
            assembly_mode='unified',
            geometry_type='solid'
        )
        
        return ifc
    
    def test_header_valid_solid(self, ifc_doc):
        """Заголовок должен быть валидным для solid геометрии"""
        header = get_ifc_header(ifc_doc)
        parsed = parse_header(header)
        
        assert parsed is not None
        assert parsed['schema'] == 'IFC4'
        assert parsed['implementation_level'] == '2;1'
