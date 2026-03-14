"""
material_manager.py — Менеджер материалов IFC

Управление созданием и кэшированием IfcMaterial, IfcMaterialList,
IfcMaterialProperties и ассоциаций через IfcRelAssociatesMaterial

Согласно IFC43 (риск: используется для IFC4 ADD2 TC1):
- Pset_MaterialCommon: MassDensity
- Pset_MaterialSteel: YieldStress, UltimateStress, StructuralGrade
"""

from typing import Any, Dict, Optional

from protocols import IfcDocumentProtocol
from utils import get_ifcopenshell


class MaterialManager:
    """Менеджер материалов IFC"""

    def __init__(self, ifc_doc: IfcDocumentProtocol):
        self.ifc: IfcDocumentProtocol = ifc_doc
        self.materials_cache: Dict[str, Any] = {}
        self.material_properties_cache: Dict[str, Any] = {}
        # Получаем OwnerHistory из документа
        owner_histories = self.ifc.by_type("IfcOwnerHistory")
        self.owner_history = owner_histories[0] if owner_histories else None

    def create_material(self, name, description=None, category=None, material_key=None):
        """
        Создание или получение материала по имени

        Args:
            name: Имя материала (например, "09Г2С ГОСТ 19281-2014")
            description: Описание материала (опционально)
            category: Категория материала (например, "Steel")
            material_key: Ключ материала для создания свойств (например, "09Г2С")

        Returns:
            IfcMaterial сущность
        """
        if name in self.materials_cache:
            return self.materials_cache[name]

        ifc = get_ifcopenshell()
        material = self.ifc.create_entity(
            "IfcMaterial", Name=name, Description=description, Category=category
        )

        self.materials_cache[name] = material

        # Создаём стандартные PropertySets если передан material_key
        if material_key:
            self.create_standard_psets(material, material_key)

        return material

    def get_material(self, name):
        """
        Получение материала из кэша

        Args:
            name: Имя материала

        Returns:
            IfcMaterial сущность или None
        """
        return self.materials_cache.get(name)

    def create_material_list(self, materials, name=None):
        """
        Создание списка материалов IfcMaterialList

        Args:
            materials: Список IfcMaterial сущностей
            name: Имя списка (опционально, не используется в IFC4)

        Returns:
            IfcMaterialList сущность
        """
        ifc = get_ifcopenshell()
        # IfcMaterialList в IFC4 не имеет атрибута Name
        material_list = self.ifc.create_entity("IfcMaterialList", Materials=materials)
        return material_list

    def associate_material(self, entity, material):
        """
        Ассоциация материала с сущностью через IfcRelAssociatesMaterial

        Args:
            entity: IFC сущность (например, IfcMechanicalFastenerType)
            material: IfcMaterial или IfcMaterialList

        Returns:
            IfcRelAssociatesMaterial сущность
        """
        ifc = get_ifcopenshell()
        rel = self.ifc.create_entity(
            "IfcRelAssociatesMaterial",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=f"MaterialAssociation_{entity.Name}",
            RelatedObjects=[entity],
            RelatingMaterial=material,
        )
        return rel

    def create_material_properties(self, material, pset_name, properties_dict):
        """
        Создание IfcMaterialProperties с набором свойств

        Args:
            material: IfcMaterial сущность
            pset_name: Имя набора свойств (например, 'Pset_MaterialCommon')
            properties_dict: Словарь свойств {name: value}

        Returns:
            IfcMaterialProperties сущность
        """
        # Создание IfcPropertySingleValue для каждого свойства
        prop_entities = []
        for prop_name, prop_value in properties_dict.items():
            # Определяем тип значения
            if isinstance(prop_value, (int, float)):
                nominal_value = self.ifc.create_entity("IfcReal", float(prop_value))
            elif isinstance(prop_value, str):
                nominal_value = self.ifc.create_entity("IfcText", prop_value)
            else:
                continue

            prop = self.ifc.create_entity(
                "IfcPropertySingleValue", Name=prop_name, NominalValue=nominal_value
            )
            prop_entities.append(prop)

        # Создание IfcMaterialProperties
        mat_props = self.ifc.create_entity(
            "IfcMaterialProperties", Name=pset_name, Properties=prop_entities, Material=material
        )

        return mat_props

    def create_standard_psets(self, material, material_key):
        """
        Создание стандартных PropertySets для материала

        Создаёт:
        - Pset_MaterialCommon: MassDensity
        - Pset_MaterialSteel: YieldStress, UltimateStress, StructuralGrade

        Args:
            material: IfcMaterial сущность
            material_key: Ключ материала (например, '09Г2С')
        """
        from gost_data import MATERIALS

        # Проверка кэша
        cache_key_common = (material, "Pset_MaterialCommon")
        cache_key_steel = (material, "Pset_MaterialSteel")

        if cache_key_common in self.material_properties_cache:
            return

        mat_info = MATERIALS.get(material_key)

        if not mat_info:
            return

        # Pset_MaterialCommon
        common_props = {"MassDensity": mat_info["density"]}  # кг/м³
        pset_common = self.create_material_properties(material, "Pset_MaterialCommon", common_props)
        self.material_properties_cache[cache_key_common] = pset_common

        # Pset_MaterialSteel (для всех материалов в нашем случае)
        steel_props = {
            "YieldStress": mat_info["yield_strength"],  # МПа
            "UltimateStress": mat_info["tensile_strength"],  # МПа
            "StructuralGrade": material_key,  # например, '09Г2С'
        }
        pset_steel = self.create_material_properties(material, "Pset_MaterialSteel", steel_props)
        self.material_properties_cache[cache_key_steel] = pset_steel

    def get_cached_materials_count(self):
        """Количество закэшированных материалов"""
        return len(self.materials_cache)

    def get_cached_properties_count(self):
        """Количество закэшированных PropertySets"""
        return len(self.material_properties_cache)
