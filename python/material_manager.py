"""
material_manager.py — Менеджер материалов IFC

Управление созданием и кэшированием IfcMaterial, IfcMaterialList
и ассоциаций через IfcRelAssociatesMaterial
"""

from utils import get_ifcopenshell


class MaterialManager:
    """Менеджер материалов IFC"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.materials_cache = {}

    def create_material(self, name, description=None, category=None):
        """
        Создание или получение материала по имени

        Args:
            name: Имя материала (например, "09Г2С ГОСТ 19281-2014")
            description: Описание материала (опционально)
            category: Категория материала (например, "Steel")

        Returns:
            IfcMaterial сущность
        """
        if name in self.materials_cache:
            return self.materials_cache[name]

        ifc = get_ifcopenshell()
        material = self.ifc.create_entity(
            'IfcMaterial',
            Name=name,
            Description=description,
            Category=category
        )

        self.materials_cache[name] = material
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
        material_list = self.ifc.create_entity(
            'IfcMaterialList',
            Materials=materials
        )
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
            'IfcRelAssociatesMaterial',
            GlobalId=ifc.guid.new(),
            Name=f'MaterialAssociation_{entity.Name}',
            RelatedObjects=[entity],
            RelatingMaterial=material
        )
        return rel

    def get_cached_materials_count(self):
        """Количество закэшированных материалов"""
        return len(self.materials_cache)
