"""
Тесты для gost_data.py - ГОСТ справочники и валидация
"""
import pytest


class TestBoltTypes:
    """Тесты для типов болтов"""

    def test_bolt_types_defined(self):
        """Все типы болтов должны быть определены"""
        from gost_data import BOLT_TYPES
        
        assert '1.1' in BOLT_TYPES
        assert '1.2' in BOLT_TYPES
        assert '2.1' in BOLT_TYPES
        assert '5' in BOLT_TYPES

    def test_bolt_type_structure(self):
        """Структура типа болта должна содержать required поля"""
        from gost_data import BOLT_TYPES
        
        for bolt_type, data in BOLT_TYPES.items():
            assert 'name' in data
            assert 'execution' in data
            assert 'has_bend' in data
            assert isinstance(data['execution'], list)
            assert len(data['execution']) > 0

    def test_bent_types_have_radius_factor(self):
        """Изогнутые болты должны иметь bend_radius_factor"""
        from gost_data import BOLT_TYPES
        
        for bolt_type, data in BOLT_TYPES.items():
            if data['has_bend']:
                assert 'bend_radius_factor' in data


class TestDiameters:
    """Тесты для диаметров"""

    def test_available_diameters_defined(self):
        """Доступные диаметры должны быть определены"""
        from gost_data import AVAILABLE_DIAMETERS
        
        assert len(AVAILABLE_DIAMETERS) > 0
        assert 20 in AVAILABLE_DIAMETERS

    def test_diameter_limits_defined(self):
        """Ограничения диаметров должны быть определены для всех типов"""
        from gost_data import DIAMETER_LIMITS, BOLT_TYPES
        
        for bolt_type in BOLT_TYPES:
            assert bolt_type in DIAMETER_LIMITS
            min_d, max_d = DIAMETER_LIMITS[bolt_type]
            assert min_d > 0
            assert max_d > min_d


class TestBoltDimData:
    """Тесты для данных размеров болтов"""

    def test_bolt_dim_data_not_empty(self):
        """BOLT_DIM_DATA не должен быть пустым"""
        from gost_data import BOLT_DIM_DATA
        
        assert len(BOLT_DIM_DATA) > 0

    def test_bolt_dim_data_format(self):
        """Формат ключей BOLT_DIM_DATA должен быть {диаметр}_{длина}"""
        from gost_data import BOLT_DIM_DATA
        
        for key in BOLT_DIM_DATA:
            assert '_' in key
            parts = key.split('_')
            assert len(parts) == 2
            assert parts[0].isdigit()
            assert parts[1].isdigit()

    def test_bolt_dim_data_values(self):
        """Значения BOLT_DIM_DATA должны быть списками правильной длины"""
        from gost_data import BOLT_DIM_DATA
        
        for key, data in BOLT_DIM_DATA.items():
            assert isinstance(data, list)
            assert len(data) >= 13  # Минимальная длина по спецификации


class TestNutDimensions:
    """Тесты для размеров гаек"""

    def test_nut_dimensions_defined(self):
        """Размеры гаек должны быть определены"""
        from gost_data import NUT_DIM_DATA
        
        assert len(NUT_DIM_DATA) > 0
        assert '20' in NUT_DIM_DATA

    def test_nut_dimensions_structure(self):
        """Структура размеров гайки: [диаметр, s_width, height]"""
        from gost_data import NUT_DIM_DATA
        
        for diameter, data in NUT_DIM_DATA.items():
            assert len(data) == 3
            assert data[0] == int(diameter)  # Диаметр должен совпадать с ключом
            assert data[1] > data[0]  # s_width > diameter
            assert data[2] > 0  # height > 0


class TestWasherDimensions:
    """Тесты для размеров шайб"""

    def test_washer_dimensions_defined(self):
        """Размеры шайб должны быть определены"""
        from gost_data import WASHER_DIM_DATA
        
        assert len(WASHER_DIM_DATA) > 0
        assert '20' in WASHER_DIM_DATA

    def test_washer_dimensions_structure(self):
        """Структура размеров шайбы: [nominal, inner, outer, thickness]"""
        from gost_data import WASHER_DIM_DATA
        
        for diameter, data in WASHER_DIM_DATA.items():
            assert len(data) == 4
            assert data[0] == int(diameter)  # Номинальный диаметр
            assert data[1] > data[0]  # Внутренний > номинального
            assert data[2] > data[1]  # Внешний > внутреннего
            assert data[3] > 0  # Толщина > 0


class TestMaterials:
    """Тесты для материалов"""

    def test_materials_defined(self):
        """Материалы должны быть определены"""
        from gost_data import MATERIALS
        
        assert '09Г2С' in MATERIALS
        assert 'ВСт3пс2' in MATERIALS
        assert '10Г2' in MATERIALS

    def test_material_structure(self):
        """Структура материала должна содержать required поля"""
        from gost_data import MATERIALS
        
        for material, data in MATERIALS.items():
            assert 'gost' in data
            assert 'tensile_strength' in data
            assert 'density' in data
            assert data['tensile_strength'] > 0
            assert data['density'] > 0


class TestAvailableLengths:
    """Тесты для доступных длин"""

    def test_available_lengths_generated(self):
        """AVAILABLE_LENGTHS должен быть сгенерирован из BOLT_DIM_DATA"""
        from gost_data import AVAILABLE_LENGTHS
        
        assert len(AVAILABLE_LENGTHS) > 0

    def test_available_lengths_structure(self):
        """Ключи AVAILABLE_LENGTHS должны быть кортежами (type, exec, diameter)"""
        from gost_data import AVAILABLE_LENGTHS
        
        for key, lengths in AVAILABLE_LENGTHS.items():
            assert isinstance(key, tuple)
            assert len(key) == 3
            assert isinstance(lengths, list)
            assert len(lengths) > 0
            # Проверка сортировки
            assert lengths == sorted(lengths)


class TestHelperFunctions:
    """Тесты для вспомогательных функций"""

    def test_get_bolt_hook_length(self):
        """get_bolt_hook_length должна возвращать вылет крюка"""
        from gost_data import get_bolt_hook_length
        
        # M20x800
        result = get_bolt_hook_length(20, 800)
        assert result is not None
        assert result > 0

    def test_get_bolt_hook_length_not_found(self):
        """get_bolt_hook_length должна возвращать None для несуществующего болта"""
        from gost_data import get_bolt_hook_length
        
        result = get_bolt_hook_length(12, 9999)
        assert result is None

    def test_get_bolt_bend_radius(self):
        """get_bolt_bend_radius должна возвращать радиус загиба"""
        from gost_data import get_bolt_bend_radius
        
        result = get_bolt_bend_radius(20, 800)
        assert result is not None
        assert result > 0

    def test_get_thread_length(self):
        """get_thread_length должна возвращать длину резьбы"""
        from gost_data import get_thread_length
        
        result = get_thread_length(20, 800)
        assert result is not None
        assert result > 0

    def test_get_bolt_mass(self):
        """get_bolt_mass должна возвращать массу для валидных параметров"""
        from gost_data import get_bolt_mass
        
        # M20x800 тип 1.1
        result = get_bolt_mass(20, 800, '1.1')
        assert result is not None
        assert result > 0

    def test_get_bolt_mass_not_exists(self):
        """get_bolt_mass должна возвращать None для несуществующего болта"""
        from gost_data import get_bolt_mass
        
        # M12x150 тип 1.1 не существует (None масса)
        result = get_bolt_mass(12, 150, '1.1')
        assert result is None

    def test_get_nut_dimensions(self):
        """get_nut_dimensions должна возвращать размеры гайки"""
        from gost_data import get_nut_dimensions
        
        result = get_nut_dimensions(20)
        assert result is not None
        assert 'diameter' in result
        assert 's_width' in result
        assert 'height' in result

    def test_get_nut_dimensions_not_found(self):
        """get_nut_dimensions должна возвращать None для неизвестного диаметра"""
        from gost_data import get_nut_dimensions
        
        result = get_nut_dimensions(999)
        assert result is None

    def test_get_washer_dimensions(self):
        """get_washer_dimensions должна возвращать размеры шайбы"""
        from gost_data import get_washer_dimensions
        
        result = get_washer_dimensions(20)
        assert result is not None
        assert 'nominal_diameter' in result
        assert 'inner_diameter' in result
        assert 'outer_diameter' in result
        assert 'thickness' in result

    def test_get_bolt_all_dimensions(self):
        """get_bolt_all_dimensions должна возвращать все размеры"""
        from gost_data import get_bolt_all_dimensions
        
        result = get_bolt_all_dimensions(20, 800)
        assert result is not None
        assert 'L' in result
        assert 'l' in result
        assert 'R' in result
        assert 'd' in result
        assert 'l0' in result


class TestValidateParameters:
    """Тесты для валидации параметров"""

    def test_validate_valid_parameters(self):
        """Валидация должна проходить для корректных параметров"""
        from gost_data import validate_parameters
        
        # Должно работать без исключений
        result = validate_parameters('1.1', 1, 20, 800, '09Г2С')
        assert result is True

    def test_validate_invalid_bolt_type(self):
        """Валидация должна падать для неизвестного типа болта"""
        from gost_data import validate_parameters
        
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('9.9', 1, 20, 800, '09Г2С')
        
        assert 'Неизвестный тип болта' in str(exc_info.value)

    def test_validate_invalid_diameter(self):
        """Валидация должна падать для неподдерживаемого диаметра"""
        from gost_data import validate_parameters
        
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('1.1', 1, 999, 800, '09Г2С')
        
        assert 'Неподдерживаемый диаметр' in str(exc_info.value)

    def test_validate_diameter_out_of_range(self):
        """Валидация должна падать для диаметра вне диапазона типа"""
        from gost_data import validate_parameters
        
        # Тип 2.1 поддерживает диаметры от 16 мм
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('2.1', 1, 12, 800, '09Г2С')
        
        assert 'недоступен для типа' in str(exc_info.value)

    def test_validate_invalid_material(self):
        """Валидация должна падать для неизвестного материала"""
        from gost_data import validate_parameters
        
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('1.1', 1, 20, 800, 'НеизвестныйМатериал')
        
        assert 'Неизвестный материал' in str(exc_info.value)

    def test_validate_invalid_length(self):
        """Валидация должна падать для недоступной длины"""
        from gost_data import validate_parameters
        
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('1.1', 1, 20, 9999, '09Г2С')
        
        assert 'недоступна' in str(exc_info.value)

    def test_validate_invalid_execution(self):
        """Валидация должна падать для неподдерживаемого исполнения"""
        from gost_data import validate_parameters
        
        # Тип 2.1 поддерживает только исполнение 1
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('2.1', 2, 20, 800, '09Г2С')
        
        assert 'Исполнение' in str(exc_info.value)

    def test_validate_multiple_errors(self):
        """Валидация должна собирать несколько ошибок"""
        from gost_data import validate_parameters
        
        with pytest.raises(ValueError) as exc_info:
            validate_parameters('9.9', 1, 999, 9999, 'Неизвестный')
        
        errors = str(exc_info.value).split('\n')
        assert len(errors) >= 2  # Минимум 2 ошибки


class TestGetTypeInfo:
    """Тесты для функций получения информации"""

    def test_get_bolt_type_info(self):
        """get_bolt_type_info должна возвращать информацию о типе"""
        from gost_data import get_bolt_type_info
        
        result = get_bolt_type_info('1.1')
        assert result is not None
        assert 'name' in result

    def test_get_bolt_type_info_not_found(self):
        """get_bolt_type_info должна возвращать пустой dict для неизвестного типа"""
        from gost_data import get_bolt_type_info
        
        result = get_bolt_type_info('9.9')
        assert result == {}

    def test_get_material_info(self):
        """get_material_info должна возвращать информацию о материале"""
        from gost_data import get_material_info
        
        result = get_material_info('09Г2С')
        assert result is not None
        assert 'gost' in result

    def test_get_material_info_not_found(self):
        """get_material_info должна возвращать пустой dict для неизвестного материала"""
        from gost_data import get_material_info
        
        result = get_material_info('Неизвестный')
        assert result == {}
