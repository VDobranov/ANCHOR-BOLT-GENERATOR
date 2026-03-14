"""
Тесты для material_manager.py - менеджер материалов IFC
"""

import pytest
from conftest import MockIfcDoc


class TestMaterialManager:
    """Тесты для MaterialManager (с моками)"""

    def test_create_material_without_properties(self):
        """MaterialManager должен создавать IfcMaterial без свойств"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал без material_key (чтобы не создавать свойства)
        material = manager.create_material("09Г2С ГОСТ 19281-2014", category="Steel")

        assert material is not None
        assert material.is_a() == "IfcMaterial"
        assert material.Name == "09Г2С ГОСТ 19281-2014"
        assert material.Category == "Steel"

    def test_create_material_caching(self):
        """MaterialManager должен кэшировать материалы"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал дважды с одинаковым именем (без material_key)
        mat1 = manager.create_material("09Г2С ГОСТ 19281-2014", category="Steel")
        mat2 = manager.create_material("09Г2С ГОСТ 19281-2014", category="Steel")

        # Должен вернуться тот же самый объект из кэша
        assert mat1 is mat2
        assert manager.get_cached_materials_count() == 1

    def test_get_material(self):
        """MaterialManager должен возвращать материал из кэша"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал
        manager.create_material("09Г2С ГОСТ 19281-2014", category="Steel")

        # Получаем из кэша
        material = manager.get_material("09Г2С ГОСТ 19281-2014")

        assert material is not None
        assert material.Name == "09Г2С ГОСТ 19281-2014"

    def test_get_material_not_found(self):
        """MaterialManager должен возвращать None для несуществующего материала"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        material = manager.get_material("NonExistent")

        assert material is None

    def test_create_material_list(self):
        """MaterialManager должен создавать IfcMaterialList"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём несколько материалов
        mat1 = manager.create_material("Material1", category="Steel")
        mat2 = manager.create_material("Material2", category="Steel")

        # Создаём список материалов
        material_list = manager.create_material_list([mat1, mat2])

        assert material_list is not None
        assert material_list.is_a() == "IfcMaterialList"
        assert len(material_list.Materials) == 2

    def test_associate_material(self):
        """MaterialManager должен создавать IfcRelAssociatesMaterial"""
        from material_manager import MaterialManager

        mock_ifc = MockIfcDoc()
        manager = MaterialManager(mock_ifc)

        # Создаём материал
        material = manager.create_material("09Г2С ГОСТ 19281-2014", category="Steel")

        # Создаём тестовую сущность
        entity = mock_ifc.create_entity("IfcMechanicalFastenerType", Name="TestType")

        # Ассоциируем материал
        rel = manager.associate_material(entity, material)

        assert rel is not None
        assert rel.is_a() == "IfcRelAssociatesMaterial"
        assert len(rel.RelatedObjects) == 1
        assert rel.RelatedObjects[0] is entity
        assert rel.RelatingMaterial is material


class TestMaterialManagerWithRealIfc:
    """Тесты для MaterialManager с реальным ifcopenshell"""

    def test_create_standard_psets(self):
        """MaterialManager должен создавать стандартные PropertySets"""
        import ifcopenshell
        from material_manager import MaterialManager

        f = ifcopenshell.file()
        manager = MaterialManager(f)

        # Создаём материал с material_key для создания свойств
        material = manager.create_material(
            "09Г2С ГОСТ 19281-2014", category="Steel", material_key="09Г2С"
        )

        # Проверяем создание PropertySets
        mat_props_list = f.by_type("IfcMaterialProperties")
        assert len(mat_props_list) == 2  # Pset_MaterialCommon и Pset_MaterialSteel

        # Проверяем Pset_MaterialCommon
        pset_common = None
        pset_steel = None
        for pset in mat_props_list:
            if pset.Name == "Pset_MaterialCommon":
                pset_common = pset
            elif pset.Name == "Pset_MaterialSteel":
                pset_steel = pset

        assert pset_common is not None
        assert pset_steel is not None
        assert pset_common.Material == material
        assert pset_steel.Material == material

        # Проверяем свойства Pset_MaterialCommon
        common_prop_names = [p.Name for p in pset_common.Properties]
        assert "MassDensity" in common_prop_names

        # Проверяем свойства Pset_MaterialSteel
        steel_prop_names = [p.Name for p in pset_steel.Properties]
        assert "YieldStress" in steel_prop_names
        assert "UltimateStress" in steel_prop_names
        assert "StructuralGrade" in steel_prop_names

    def test_create_standard_psets_caching(self):
        """MaterialManager должен кэшировать PropertySets"""
        import ifcopenshell
        from material_manager import MaterialManager

        f = ifcopenshell.file()
        manager = MaterialManager(f)

        # Создаём материал с material_key
        material = manager.create_material(
            "09Г2С ГОСТ 19281-2014", category="Steel", material_key="09Г2С"
        )

        # Получаем количество PropertySets
        count1 = manager.get_cached_properties_count()

        # Создаём тот же материал снова (должен вернуться из кэша)
        material2 = manager.create_material(
            "09Г2С ГОСТ 19281-2014", category="Steel", material_key="09Г2С"
        )

        # Количество PropertySets не должно измениться
        count2 = manager.get_cached_properties_count()
        assert count1 == count2

    def test_material_properties_values(self):
        """MaterialManager должен создавать свойства с правильными значениями"""
        import ifcopenshell
        from material_manager import MaterialManager

        f = ifcopenshell.file()
        manager = MaterialManager(f)

        # Создаём материал
        material = manager.create_material(
            "09Г2С ГОСТ 19281-2014", category="Steel", material_key="09Г2С"
        )

        # Находим PropertySets
        mat_props_list = f.by_type("IfcMaterialProperties")

        for pset in mat_props_list:
            if pset.Name == "Pset_MaterialCommon":
                for prop in pset.Properties:
                    if prop.Name == "MassDensity":
                        assert prop.NominalValue[0] == 7850.0

            elif pset.Name == "Pset_MaterialSteel":
                for prop in pset.Properties:
                    if prop.Name == "YieldStress":
                        assert prop.NominalValue[0] == 390.0
                    elif prop.Name == "UltimateStress":
                        assert prop.NominalValue[0] == 490.0
                    elif prop.Name == "StructuralGrade":
                        assert prop.NominalValue[0] == "09Г2С"


class TestGetMaterialName:
    """Тесты для функции get_material_name"""

    def test_get_material_name_09g2s(self):
        """Функция должна возвращать имя в формате '09Г2С ГОСТ 19281-2014'"""
        from gost_data import get_material_name

        result = get_material_name("09Г2С")
        assert result == "09Г2С ГОСТ 19281-2014"

    def test_get_material_name_vst3ps2(self):
        """Функция должна возвращать имя в формате 'ВСт3пс2 ГОСТ 535-88'"""
        from gost_data import get_material_name

        result = get_material_name("ВСт3пс2")
        assert result == "ВСт3пс2 ГОСТ 535-88"

    def test_get_material_name_10g2(self):
        """Функция должна возвращать имя в формате '10Г2 ГОСТ 19281-2014'"""
        from gost_data import get_material_name

        result = get_material_name("10Г2")
        assert result == "10Г2 ГОСТ 19281-2014"

    def test_get_material_name_unknown(self):
        """Функция должна возвращать исходное имя для неизвестного материала"""
        from gost_data import get_material_name

        result = get_material_name("UnknownMaterial")
        assert result == "UnknownMaterial"
