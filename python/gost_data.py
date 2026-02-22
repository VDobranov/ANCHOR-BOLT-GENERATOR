"""
gost_data.py - ГОСТ справочники и валидация параметров
Based on ГОСТ 24379.1-2012 and related standards
"""

# Типы болтов и их характеристики
BOLT_TYPES = {
    '1.1': {
        'name': 'Тип 1. Исполнение 1',
        'execution': [1, 2],
        'has_bend': True,
        'bend_radius_factor': 1.5  # R = d * factor
    },
    '1.2': {
        'name': 'Тип 1. Исполнение 2',
        'execution': [1, 2],
        'has_bend': True,
        'bend_radius_factor': 2.0  # R = d * factor
    },
    '2.1': {
        'name': 'Тип 2. Исполнение 1',
        'execution': [1],
        'has_bend': False
    },
    '5': {
        'name': 'Тип 5',
        'execution': [1],
        'has_bend': False
    }
}

# Доступные диаметры согласно ГОСТ
AVAILABLE_DIAMETERS = [12, 16, 20, 24, 30, 36, 42, 48, 56, 64, 72, 80, 90, 100]

# Доступные длины для каждой комбинации типа, исполнения и диаметра
AVAILABLE_LENGTHS = {
    ('1.1', 1, 12): [400, 500, 630, 800, 1000, 1250],
    ('1.1', 1, 16): [500, 630, 800, 1000, 1250, 1600],
    ('1.1', 1, 20): [500, 630, 800, 1000, 1250, 1600],
    ('1.1', 1, 24): [630, 800, 1000, 1250, 1600],
    ('1.1', 1, 30): [800, 1000, 1250, 1600],
    ('1.1', 1, 36): [800, 1000, 1250, 1600],
    ('1.1', 1, 42): [1000, 1250, 1600],
    ('1.1', 1, 48): [1000, 1250, 1600],
    ('1.1', 1, 56): [1250, 1600],
    ('1.1', 1, 64): [1250, 1600],
    ('1.1', 1, 72): [1600],
    ('1.1', 1, 80): [1600],
    ('1.1', 1, 90): [1600],
    ('1.1', 1, 100): [1600],

    ('1.1', 2, 12): [400, 500, 630, 800, 1000, 1250],
    ('1.1', 2, 16): [500, 630, 800, 1000, 1250, 1600],
    ('1.1', 2, 20): [500, 630, 800, 1000, 1250, 1600],
    ('1.1', 2, 24): [630, 800, 1000, 1250, 1600],
    ('1.1', 2, 30): [800, 1000, 1250, 1600],
    ('1.1', 2, 36): [800, 1000, 1250, 1600],
    ('1.1', 2, 42): [1000, 1250, 1600],
    ('1.1', 2, 48): [1000, 1250, 1600],
    ('1.1', 2, 56): [1250, 1600],
    ('1.1', 2, 64): [1250, 1600],
    ('1.1', 2, 72): [1600],
    ('1.1', 2, 80): [1600],
    ('1.1', 2, 90): [1600],
    ('1.1', 2, 100): [1600],

    ('1.2', 1, 12): [400, 500, 630, 800],
    ('1.2', 1, 16): [500, 630, 800, 1000],
    ('1.2', 1, 20): [500, 630, 800, 1000],
    ('1.2', 1, 24): [630, 800, 1000],
    ('1.2', 1, 30): [800, 1000],
    ('1.2', 1, 36): [800, 1000],
    ('1.2', 1, 42): [1000],
    ('1.2', 1, 48): [1000],
    ('1.2', 1, 56): [1000],
    ('1.2', 1, 64): [1000],
    ('1.2', 1, 72): [1000],
    ('1.2', 1, 80): [1000],
    ('1.2', 1, 90): [1000],
    ('1.2', 1, 100): [1000],

    ('1.2', 2, 12): [400, 500, 630, 800],
    ('1.2', 2, 16): [500, 630, 800, 1000],
    ('1.2', 2, 20): [500, 630, 800, 1000],
    ('1.2', 2, 24): [630, 800, 1000],
    ('1.2', 2, 30): [800, 1000],
    ('1.2', 2, 36): [800, 1000],
    ('1.2', 2, 42): [1000],
    ('1.2', 2, 48): [1000],
    ('1.2', 2, 56): [1000],
    ('1.2', 2, 64): [1000],
    ('1.2', 2, 72): [1000],
    ('1.2', 2, 80): [1000],
    ('1.2', 2, 90): [1000],
    ('1.2', 2, 100): [1000],

    # Type 2.1
    ('2.1', 1, 12): [500, 630, 800, 1000, 1250],
    ('2.1', 1, 16): [500, 630, 800, 1000, 1250],
    ('2.1', 1, 20): [500, 630, 800, 1000, 1250],
    ('2.1', 1, 24): [630, 800, 1000, 1250],
    ('2.1', 1, 30): [800, 1000, 1250],
    ('2.1', 1, 36): [800, 1000, 1250],
    ('2.1', 1, 42): [1000, 1250],
    ('2.1', 1, 48): [1000, 1250],
    ('2.1', 1, 56): [1250],
    ('2.1', 1, 64): [1250],
    ('2.1', 1, 72): [1250],
    ('2.1', 1, 80): [1250],
    ('2.1', 1, 90): [1250],
    ('2.1', 1, 100): [1250],

    # Type 5
    ('5', 1, 12): [500, 630, 800],
    ('5', 1, 16): [500, 630, 800],
    ('5', 1, 20): [500, 630, 800],
    ('5', 1, 24): [630, 800],
    ('5', 1, 30): [800],
    ('5', 1, 36): [800],
    ('5', 1, 42): [1000],
    ('5', 1, 48): [1000],
    ('5', 1, 56): [1000],
    ('5', 1, 64): [1000],
    ('5', 1, 72): [1000],
    ('5', 1, 80): [1000],
    ('5', 1, 90): [1000],
    ('5', 1, 100): [1000],
}

# Параметры болтов по ГОСТ 24379.1-2012, 19281-2014
BOLT_DIMENSIONS_SPEC = {
    12: {
        'thread_pitch': 1.75,
        'nut_height': 10,
        'washer_thickness': 2,
        'washer_outer_diameter': 24,
        'washer_inner_diameter': 14,
        's_width': 18,  # ключ
        'mass_per_meter': 0.888  # кг/м
    },
    16: {
        'thread_pitch': 2.0,
        'nut_height': 13,
        'washer_thickness': 3,
        'washer_outer_diameter': 30,
        'washer_inner_diameter': 18,
        's_width': 24,
        'mass_per_meter': 1.573
    },
    20: {
        'thread_pitch': 2.5,
        'nut_height': 16,
        'washer_thickness': 4,
        'washer_outer_diameter': 37,
        'washer_inner_diameter': 22,
        's_width': 30,
        'mass_per_meter': 2.466
    },
    24: {
        'thread_pitch': 3.0,
        'nut_height': 19,
        'washer_thickness': 4,
        'washer_outer_diameter': 44,
        'washer_inner_diameter': 26,
        's_width': 36,
        'mass_per_meter': 3.567
    },
    30: {
        'thread_pitch': 3.5,
        'nut_height': 24,
        'washer_thickness': 5,
        'washer_outer_diameter': 56,
        'washer_inner_diameter': 33,
        's_width': 46,
        'mass_per_meter': 5.570
    },
    36: {
        'thread_pitch': 4.0,
        'nut_height': 29,
        'washer_thickness': 6,
        'washer_outer_diameter': 66,
        'washer_inner_diameter': 39,
        's_width': 55,
        'mass_per_meter': 7.994
    },
    42: {
        'thread_pitch': 4.5,
        'nut_height': 34,
        'washer_thickness': 7,
        'washer_outer_diameter': 78,
        'washer_inner_diameter': 45,
        's_width': 65,
        'mass_per_meter': 10.88
    },
    48: {
        'thread_pitch': 5.0,
        'nut_height': 38,
        'washer_thickness': 8,
        'washer_outer_diameter': 90,
        'washer_inner_diameter': 52,
        's_width': 75,
        'mass_per_meter': 14.25
    },
    56: {
        'thread_pitch': 5.5,
        'nut_height': 45,
        'washer_thickness': 9,
        'washer_outer_diameter': 105,
        'washer_inner_diameter': 60,
        's_width': 85,
        'mass_per_meter': 19.40
    },
    64: {
        'thread_pitch': 6.0,
        'nut_height': 51,
        'washer_thickness': 10,
        'washer_outer_diameter': 120,
        'washer_inner_diameter': 68,
        's_width': 95,
        'mass_per_meter': 25.10
    },
    72: {
        'thread_pitch': 6.0,
        'nut_height': 57,
        'washer_thickness': 11,
        'washer_outer_diameter': 135,
        'washer_inner_diameter': 78,
        's_width': 105,
        'mass_per_meter': 32.00
    },
    80: {
        'thread_pitch': 6.0,
        'nut_height': 64,
        'washer_thickness': 12,
        'washer_outer_diameter': 150,
        'washer_inner_diameter': 85,
        's_width': 120,
        'mass_per_meter': 39.40
    },
    90: {
        'thread_pitch': 6.0,
        'nut_height': 72,
        'washer_thickness': 14,
        'washer_outer_diameter': 170,
        'washer_inner_diameter': 95,
        's_width': 135,
        'mass_per_meter': 50.30
    },
    100: {
        'thread_pitch': 6.0,
        'nut_height': 80,
        'washer_thickness': 16,
        'washer_outer_diameter': 190,
        'washer_inner_diameter': 105,
        's_width': 150,
        'mass_per_meter': 61.50
    }
}

# Материалы согласно ГОСТ
MATERIALS = {
    '09Г2С': {
        'gost': '19281-2014',
        'tensile_strength': 490,  # МПа
        'yield_strength': 390,
        'density': 7850,  # кг/м³
        'description': 'Низколегированная сталь'
    },
    'ВСт3пс2': {
        'gost': '535-88',
        'tensile_strength': 345,
        'yield_strength': 235,
        'density': 7850,
        'description': 'Углеродистая конструкционная сталь'
    },
    '10Г2': {
        'gost': '19281-2014',
        'tensile_strength': 490,
        'yield_strength': 390,
        'density': 7850,
        'description': 'Низколегированная сталь'
    }
}


def validate_parameters(bolt_type, execution, diameter, length, material):
    """Validate bolt parameters against ГОСТ standards"""

    errors = []

    # Validate bolt type
    if bolt_type not in BOLT_TYPES:
        errors.append(f"Неизвестный тип болта: {bolt_type}")

    # Validate diameter
    if diameter not in AVAILABLE_DIAMETERS:
        errors.append(f"Неподдерживаемый диаметр: М{diameter}")

    # Validate material
    if material not in MATERIALS:
        errors.append(f"Неизвестный материал: {material}")

    # Validate execution and length
    if bolt_type in BOLT_TYPES:
        if execution not in BOLT_TYPES[bolt_type]['execution']:
            errors.append(f"Исполнение {execution} не поддерживается для типа {bolt_type}")

        key = (bolt_type, execution, diameter)
        if key not in AVAILABLE_LENGTHS:
            errors.append(f"Комбинация типа {bolt_type}, исполнения {execution}, диаметра М{diameter} не существует")
        elif length not in AVAILABLE_LENGTHS[key]:
            available = AVAILABLE_LENGTHS[key]
            errors.append(f"Длина {length} недоступна. Доступные длины: {available}")

    if errors:
        raise ValueError('\n'.join(errors))

    return True


def get_bolt_spec(diameter):
    """Get complete specification for bolt diameter"""
    return BOLT_DIMENSIONS_SPEC.get(diameter, {})


def get_bolt_type_info(bolt_type):
    """Get bolt type information"""
    return BOLT_TYPES.get(bolt_type, {})


def get_material_info(material):
    """Get material information"""
    return MATERIALS.get(material, {})


if __name__ == '__main__':
    # Test validation
    try:
        validate_parameters('1.1', 1, 20, 800, '09Г2С')
        print("✓ Validation passed")
    except ValueError as e:
        print(f"✗ Validation error: {e}")
