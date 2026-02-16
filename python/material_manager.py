"""
material_manager.py - Управление материалами в IFC документе
"""

from gost_data import MATERIALS


class MaterialManager:
    """Управление материалами и их привязкой к объектам"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.materials = {}  # Кэш созданных материалов

    def get_or_create_material(self, material_name):
        """Get or create IfcMaterial by name"""
        if material_name in self.materials:
            return self.materials[material_name]

        mat_info = MATERIALS.get(material_name, {})

        # Create IfcMaterial
        material = self.ifc.create_entity('IfcMaterial',
                                         Name=material_name,
                                         Description=mat_info.get('description', ''))

        self.materials[material_name] = material
        return material

    def assign_material(self, shape_or_type, material):
        """Assign material to IFC object using IfcRelAssociatesMaterial"""
        rel = self.ifc.create_entity('IfcRelAssociatesMaterial',
                                    GlobalId=self._generate_guid(),
                                    RelatingMaterial=material,
                                    RelatedObjects=[shape_or_type])
        return rel

    def _generate_guid(self):
        """Generate IFC GUID using ifcopenshell"""
        from main import _get_ifcopenshell
        ifcopenshell = _get_ifcopenshell()
        if ifcopenshell is None:
            raise RuntimeError("ifcopenshell not available in material_manager._generate_guid()")
        return ifcopenshell.guid.new()
