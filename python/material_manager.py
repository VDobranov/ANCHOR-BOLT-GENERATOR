"""
material_manager.py — Управление материалами IFC
"""

from gost_data import MATERIALS


def _get_ifcopenshell():
    """Ленивый импорт ifcopenshell"""
    from main import _get_ifcopenshell as get_ifc
    return get_ifc()


class MaterialManager:
    """Управление материалами и их привязкой к объектам"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.materials = {}

    def get_or_create_material(self, material_name):
        """Получение или создание материала"""
        if material_name in self.materials:
            return self.materials[material_name]

        mat_info = MATERIALS.get(material_name, {})
        material = self.ifc.create_entity('IfcMaterial',
            Name=material_name,
            Description=mat_info.get('description', '')
        )

        self.materials[material_name] = material
        return material

    def assign_material(self, shape_or_type, material):
        """Привязка материала к объекту"""
        ifcopenshell = _get_ifcopenshell()
        return self.ifc.create_entity('IfcRelAssociatesMaterial',
            GlobalId=ifcopenshell.guid.new(),
            RelatingMaterial=material,
            RelatedObjects=[shape_or_type]
        )
