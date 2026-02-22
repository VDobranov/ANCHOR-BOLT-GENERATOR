"""
gost_data.py - ГОСТ справочники и валидация параметров
Based on ГОСТ 24379.1-2012 and related standards

Данные из DIM.py (BlenderBIM):
- bolt_dim: [длина, вылет крюка, радиус загиба, диаметр, длина резьбы, масса]
- nut_dim: [диаметр, размер под ключ, высота]
- washer_dim: [диаметр номинальный, диаметр отверстия, внешний диаметр, высота]
"""

# Типы болтов и их характеристики
BOLT_TYPES = {
    '1.1': {
        'name': 'Тип 1. Исполнение 1',
        'execution': [1, 2],
        'has_bend': True,
        'bend_radius_factor': 1.0  # R = d (из DIM.py)
    },
    '1.2': {
        'name': 'Тип 1. Исполнение 2',
        'execution': [1, 2],
        'has_bend': True,
        'bend_radius_factor': 2.0  # R = d * 2
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

# Доступные диаметры согласно ГОСТ (из DIM.py)
AVAILABLE_DIAMETERS = [12, 16, 20, 24, 30, 36, 42, 48]

# Ограничения диаметров по типам болтов
DIAMETER_LIMITS = {
    '1.1': (12, 48),  # М12–М48
    '1.2': (12, 48),  # М12–М48
    '2.1': (16, 48),  # М16–М48
    '5': (12, 48)     # М12–М48
}

# Параметры болтов из DIM.py
# Формат: "{диаметр}_{длина}": [длина, вылет крюка, радиус загиба, диаметр, длина резьбы, масса]
BOLT_DIM_DATA = {
    "12_300": [300, 40, 12, 12, 80, 0.35],
    "12_400": [400, 40, 12, 12, 80, 0.44],
    "12_500": [500, 40, 12, 12, 80, 0.52],
    "12_600": [600, 40, 12, 12, 80, 0.61],
    "12_710": [710, 40, 12, 12, 80, 0.71],
    "12_800": [800, 40, 12, 12, 80, 0.79],
    "12_900": [900, 40, 12, 12, 80, 0.88],
    "12_1000": [1000, 40, 12, 12, 80, 0.97],
    "16_300": [300, 50, 16, 16, 90, 0.66],
    "16_400": [400, 50, 16, 16, 90, 0.82],
    "16_500": [500, 50, 16, 16, 90, 0.97],
    "16_600": [600, 50, 16, 16, 90, 1.13],
    "16_710": [710, 50, 16, 16, 90, 1.31],
    "16_800": [800, 50, 16, 16, 90, 1.45],
    "16_900": [900, 50, 16, 16, 90, 1.6],
    "16_1000": [1000, 50, 16, 16, 90, 1.77],
    "16_1120": [1120, 50, 16, 16, 90, 1.95],
    "16_1250": [1250, 50, 16, 16, 90, 2.15],
    "20_400": [400, 60, 20, 20, 100, 1.32],
    "20_500": [500, 60, 20, 20, 100, 1.57],
    "20_600": [600, 60, 20, 20, 100, 1.81],
    "20_710": [710, 60, 20, 20, 100, 2.09],
    "20_800": [800, 60, 20, 20, 100, 2.31],
    "20_900": [900, 60, 20, 20, 100, 2.55],
    "20_1000": [1000, 60, 20, 20, 100, 2.8],
    "20_1120": [1120, 60, 20, 20, 100, 3.1],
    "20_1250": [1250, 60, 20, 20, 100, 3.43],
    "20_1320": [1320, 60, 20, 20, 100, 3.6],
    "20_1400": [1400, 60, 20, 20, 100, 3.79],
    "24_500": [500, 75, 24, 24, 110, 2.35],
    "24_600": [600, 75, 24, 24, 110, 2.71],
    "24_710": [710, 75, 24, 24, 110, 3.1],
    "24_800": [800, 75, 24, 24, 110, 3.42],
    "24_900": [900, 75, 24, 24, 110, 3.77],
    "24_1000": [1000, 75, 24, 24, 110, 4.13],
    "24_1120": [1120, 75, 24, 24, 110, 4.56],
    "24_1250": [1250, 75, 24, 24, 110, 5.03],
    "24_1320": [1320, 75, 24, 24, 110, 5.28],
    "24_1400": [1400, 75, 24, 24, 110, 5.55],
    "24_1500": [1500, 75, 24, 24, 110, 5.9],
    "24_1600": [1600, 75, 24, 24, 110, 6.26],
    "24_1700": [1700, 75, 24, 24, 110, 6.61],
    "30_600": [600, 90, 30, 30, 120, 4.55],
    "30_710": [710, 90, 30, 30, 120, 5.16],
    "30_800": [800, 90, 30, 30, 120, 5.66],
    "30_900": [900, 90, 30, 30, 120, 6.22],
    "30_1000": [1000, 90, 30, 30, 120, 6.77],
    "30_1120": [1120, 90, 30, 30, 120, 7.43],
    "30_1250": [1250, 90, 30, 30, 120, 8.15],
    "30_1320": [1320, 90, 30, 30, 120, 8.53],
    "30_1400": [1400, 90, 30, 30, 120, 8.99],
    "30_1500": [1500, 90, 30, 30, 120, 9.54],
    "30_1600": [1600, 90, 30, 30, 120, 10.1],
    "30_1700": [1700, 90, 30, 30, 120, 10.65],
    "30_1800": [1800, 90, 30, 30, 120, 11.21],
    "30_1900": [1900, 90, 30, 30, 120, 11.76],
    "30_2000": [2000, 90, 30, 30, 120, 12.32],
    "36_710": [710, 110, 36, 36, 130, 7.59],
    "36_800": [800, 110, 36, 36, 130, 8.31],
    "36_900": [900, 110, 36, 36, 130, 9.1],
    "36_1000": [1000, 110, 36, 36, 130, 9.91],
    "36_1120": [1120, 110, 36, 36, 130, 10.85],
    "36_1250": [1250, 110, 36, 36, 130, 11.88],
    "36_1320": [1320, 110, 36, 36, 130, 12.43],
    "36_1400": [1400, 110, 36, 36, 130, 13.1],
    "36_1500": [1500, 110, 36, 36, 130, 13.9],
    "36_1600": [1600, 110, 36, 36, 130, 14.7],
    "36_1700": [1700, 110, 36, 36, 130, 15.5],
    "36_1800": [1800, 110, 36, 36, 130, 16.29],
    "36_1900": [1900, 110, 36, 36, 130, 17.09],
    "36_2000": [2000, 110, 36, 36, 130, 17.89],
    "36_2120": [2120, 110, 36, 36, 130, 18.85],
    "36_2240": [2240, 110, 36, 36, 130, 19.81],
    "36_2300": [2300, 110, 36, 36, 130, 20.29],
    "42_800": [800, 125, 42, 42, 140, 11.81],
    "42_900": [900, 125, 42, 42, 140, 12.89],
    "42_1000": [1000, 125, 42, 42, 140, 13.98],
    "42_1120": [1120, 125, 42, 42, 140, 15.29],
    "42_1250": [1250, 125, 42, 42, 140, 16.71],
    "42_1320": [1320, 125, 42, 42, 140, 17.47],
    "42_1400": [1400, 125, 42, 42, 140, 18.33],
    "42_1500": [1500, 125, 42, 42, 140, 19.42],
    "42_1600": [1600, 125, 42, 42, 140, 20.5],
    "42_1700": [1700, 125, 42, 42, 140, 21.59],
    "42_1800": [1800, 125, 42, 42, 140, 22.68],
    "42_1900": [1900, 125, 42, 42, 140, 23.76],
    "42_2000": [2000, 125, 42, 42, 140, 24.85],
    "42_2120": [2120, 125, 42, 42, 140, 26.16],
    "42_2240": [2240, 125, 42, 42, 140, 27.47],
    "42_2300": [2300, 125, 42, 42, 140, 28.11],
    "42_2360": [2360, 125, 42, 42, 140, 28.76],
    "42_2500": [2500, 125, 42, 42, 140, 30.29],
    "48_900": [900, 150, 48, 48, 150, 17.41],
    "48_1000": [1000, 150, 48, 48, 150, 18.83],
    "48_1120": [1120, 150, 48, 48, 150, 20.53],
    "48_1250": [1250, 150, 48, 48, 150, 22.38],
    "48_1320": [1320, 150, 48, 48, 150, 23.37],
    "48_1400": [1400, 150, 48, 48, 150, 24.51],
    "48_1500": [1500, 150, 48, 48, 150, 25.93],
    "48_1600": [1600, 150, 48, 48, 150, 27.35],
    "48_1700": [1700, 150, 48, 48, 150, 28.77],
    "48_1800": [1800, 150, 48, 48, 150, 30.19],
    "48_1900": [1900, 150, 48, 48, 150, 31.61],
    "48_2000": [2000, 150, 48, 48, 150, 33.03],
    "48_2120": [2120, 150, 48, 48, 150, 34.73],
    "48_2240": [2240, 150, 48, 48, 150, 36.44],
    "48_2300": [2300, 150, 48, 48, 150, 37.29],
    "48_2360": [2360, 150, 48, 48, 150, 38.07],
    "48_2500": [2500, 150, 48, 48, 150, 40.13],
    "48_2650": [2650, 150, 48, 48, 150, 42.26],
    "48_2800": [2800, 150, 48, 48, 150, 44.39]
}

# Параметры гаек из DIM.py
# Формат: "{диаметр}": [диаметр, размер под ключ, высота]
NUT_DIM_DATA = {
    "12": [12, 18, 10.8],
    "16": [16, 24, 14.8],
    "20": [20, 30, 18],
    "24": [24, 36, 21.5],
    "30": [30, 46, 25.6],
    "36": [36, 55, 31],
    "42": [42, 65, 34],
    "48": [48, 75, 38]
}

# Параметры шайб из DIM.py
# Формат: "{диаметр}": [диаметр номинальный, диаметр отверстия, внешний диаметр, высота]
WASHER_DIM_DATA = {
    "12": [12, 13, 36, 3],
    "16": [16, 17, 42, 4],
    "20": [20, 21, 45, 8],
    "24": [24, 25, 55, 8],
    "30": [30, 32, 80, 10],
    "36": [36, 38, 90, 10],
    "42": [42, 44, 95, 14],
    "48": [48, 50, 105, 14]
}

# Доступные длины для каждой комбинации типа, исполнения и диаметра
# Генерируется автоматически из BOLT_DIM_DATA для типа 1.1
AVAILABLE_LENGTHS = {}

# Автогенерация AVAILABLE_LENGTHS из BOLT_DIM_DATA
for key, data in BOLT_DIM_DATA.items():
    diameter = int(key.split('_')[0])
    length = int(data[0])
    
    # Тип 1.1, исполнение 1
    key_1_1_1 = ('1.1', 1, diameter)
    if key_1_1_1 not in AVAILABLE_LENGTHS:
        AVAILABLE_LENGTHS[key_1_1_1] = []
    if length not in AVAILABLE_LENGTHS[key_1_1_1]:
        AVAILABLE_LENGTHS[key_1_1_1].append(length)
    
    # Тип 1.1, исполнение 2 (те же длины)
    key_1_1_2 = ('1.1', 2, diameter)
    if key_1_1_2 not in AVAILABLE_LENGTHS:
        AVAILABLE_LENGTHS[key_1_1_2] = []
    if length not in AVAILABLE_LENGTHS[key_1_1_2]:
        AVAILABLE_LENGTHS[key_1_1_2].append(length)
    
    # Тип 1.2, исполнение 1 (те же длины)
    key_1_2_1 = ('1.2', 1, diameter)
    if key_1_2_1 not in AVAILABLE_LENGTHS:
        AVAILABLE_LENGTHS[key_1_2_1] = []
    if length not in AVAILABLE_LENGTHS[key_1_2_1]:
        AVAILABLE_LENGTHS[key_1_2_1].append(length)
    
    # Тип 1.2, исполнение 2 (те же длины)
    key_1_2_2 = ('1.2', 2, diameter)
    if key_1_2_2 not in AVAILABLE_LENGTHS:
        AVAILABLE_LENGTHS[key_1_2_2] = []
    if length not in AVAILABLE_LENGTHS[key_1_2_2]:
        AVAILABLE_LENGTHS[key_1_2_2].append(length)

# Сортировка длин
for key in AVAILABLE_LENGTHS:
    AVAILABLE_LENGTHS[key].sort()

# Добавляем длины для типа 2.1 и 5 (упрощённо, на основе данных из DIM.py)
# Тип 2.1 (прямые болты) - те же диаметры и длины
for diameter in AVAILABLE_DIAMETERS:
    if diameter >= 16:  # Тип 2.1 от М16
        lengths = [l for (t, e, d), l_list in AVAILABLE_LENGTHS.items() 
                   if d == diameter and t == '1.1' for l in l_list]
        if lengths:
            AVAILABLE_LENGTHS[('2.1', 1, diameter)] = sorted(set(lengths))

# Тип 5 (футорки) - те же диаметры и длины
for diameter in AVAILABLE_DIAMETERS:
    lengths = [l for (t, e, d), l_list in AVAILABLE_LENGTHS.items() 
               if d == diameter and t == '1.1' for l in l_list]
    if lengths:
        AVAILABLE_LENGTHS[('5', 1, diameter)] = sorted(set(lengths))


def get_bolt_hook_length(diameter, length):
    """Получить вылет крюка для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][1]  # вылет крюка
    return None


def get_bolt_bend_radius(diameter, length):
    """Получить радиус загиба для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][2]  # радиус загиба
    return diameter  # fallback: R = d


def get_thread_length(diameter, length):
    """Получить длину резьбы для болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][4]  # длина резьбы
    return None


def get_bolt_mass(diameter, length):
    """Получить массу болта данного диаметра и длины"""
    key = f"{diameter}_{length}"
    if key in BOLT_DIM_DATA:
        return BOLT_DIM_DATA[key][5]  # масса
    return None


# Параметры болтов по ГОСТ 24379.1-2012, 19281-2014
# Обновлённые данные из DIM.py
BOLT_DIMENSIONS_SPEC = {}

for d_str, nut_data in NUT_DIM_DATA.items():
    diameter = int(d_str)
    washer_data = WASHER_DIM_DATA.get(d_str, [diameter, diameter + 1, diameter * 2, 3])
    
    BOLT_DIMENSIONS_SPEC[diameter] = {
        'thread_pitch': 1.75 if diameter == 12 else 2.0 if diameter == 16 else 2.5 if diameter == 20 else 3.0 if diameter == 24 else 3.5 if diameter == 30 else 4.0 if diameter == 36 else 4.5 if diameter == 42 else 5.0,
        'nut_height': nut_data[2],  # высота гайки
        'nut_s_width': nut_data[1],  # размер под ключ
        'washer_thickness': washer_data[3],  # толщина шайбы
        'washer_outer_diameter': washer_data[2],  # внешний диаметр шайбы
        'washer_inner_diameter': washer_data[1],  # диаметр отверстия шайбы
        's_width': nut_data[1],  # ключ (размер под ключ)
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

    # Validate diameter limits for bolt type
    if bolt_type in DIAMETER_LIMITS:
        min_d, max_d = DIAMETER_LIMITS[bolt_type]
        if diameter < min_d or diameter > max_d:
            errors.append(f"Диаметр М{diameter} недоступен для типа {bolt_type}. Доступен диапазон: М{min_d}–М{max_d}")

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


def get_bolt_spec(diameter, length=None):
    """Get complete specification for bolt diameter and optional length"""
    spec = BOLT_DIMENSIONS_SPEC.get(diameter, {}).copy()
    
    if length is not None:
        # Добавить специфичные для длины параметры
        hook_length = get_bolt_hook_length(diameter, length)
        bend_radius = get_bolt_bend_radius(diameter, length)
        thread_length = get_thread_length(diameter, length)
        mass = get_bolt_mass(diameter, length)
        
        spec.update({
            'hook_length': hook_length,
            'bend_radius': bend_radius,
            'thread_length': thread_length,
            'mass': mass
        })
    
    return spec


def get_bolt_type_info(bolt_type):
    """Get bolt type information"""
    return BOLT_TYPES.get(bolt_type, {})


def get_material_info(material):
    """Get material information"""
    return MATERIALS.get(material, {})


def get_nut_dimensions(diameter):
    """Get nut dimensions for given diameter"""
    data = NUT_DIM_DATA.get(str(diameter))
    if data:
        return {
            'diameter': data[0],
            's_width': data[1],  # размер под ключ
            'height': data[2]
        }
    return None


def get_washer_dimensions(diameter):
    """Get washer dimensions for given diameter"""
    data = WASHER_DIM_DATA.get(str(diameter))
    if data:
        return {
            'nominal_diameter': data[0],
            'inner_diameter': data[1],
            'outer_diameter': data[2],
            'thickness': data[3]
        }
    return None


if __name__ == '__main__':
    # Test validation
    try:
        validate_parameters('1.1', 1, 20, 800, '09Г2С')
        print("✓ Validation passed")
        
        # Test get_bolt_spec
        spec = get_bolt_spec(20, 800)
        print(f"✓ Bolt spec for M20x800: {spec}")
        
        # Test dimensions
        print(f"✓ Nut dimensions for M20: {get_nut_dimensions(20)}")
        print(f"✓ Washer dimensions for M20: {get_washer_dimensions(20)}")
        
    except ValueError as e:
        print(f"✗ Validation error: {e}")
