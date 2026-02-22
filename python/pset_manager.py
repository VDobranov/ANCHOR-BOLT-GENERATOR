"""
pset_manager.py — Управление Property Sets
"""


def _get_ifcopenshell():
    """Ленивый импорт ifcopenshell"""
    from main import _get_ifcopenshell as get_ifc
    return get_ifc()


class PSetManager:
    """Управление Property Sets для IFC объектов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc

    def create_pset(self, name, properties_dict):
        """Создание property set"""
        ifcopenshell = _get_ifcopenshell()
        pset = self.ifc.create_entity('IfcPropertySet',
            GlobalId=ifcopenshell.guid.new(),
            Name=name
        )

        props = []
        for prop_name, prop_value in properties_dict.items():
            prop = self.ifc.create_entity('IfcPropertySingleValue',
                Name=prop_name,
                NominalValue=self._create_property_value(prop_value)
            )
            props.append(prop)

        pset.HasProperties = props
        return pset

    def create_pset_mechanical_fastener_common(self, nominal_diameter, nominal_length,
                                              thread_length=None, nut_height=None,
                                              washer_thickness=None):
        """Pset_MechanicalFastenerCommon"""
        properties = {
            'NominalDiameter': nominal_diameter,
            'NominalLength': nominal_length,
        }

        if thread_length:
            properties['ThreadLength'] = thread_length
        if nut_height:
            properties['Height'] = nut_height
        if washer_thickness:
            properties['Thickness'] = washer_thickness

        return self.create_pset('Pset_MechanicalFastenerCommon', properties)

    def create_pset_element_component_common(self, component_type, position_z=0):
        """Pset_ElementComponentCommon"""
        return self.create_pset('Pset_ElementComponentCommon', {
            'ComponentType': component_type,
            'PositionZ': position_z
        })

    def create_pset_manufacturer_type_information(self, manufacturer, type_designation,
                                                 gost_standard):
        """Pset_ManufacturerTypeInformation"""
        return self.create_pset('Pset_ManufacturerTypeInformation', {
            'Manufacturer': manufacturer,
            'TypeDesignation': type_designation,
            'StandardDesignation': gost_standard
        })

    def assign_pset_to_object(self, obj, pset):
        """Привязка property set к объекту"""
        ifcopenshell = _get_ifcopenshell()
        return self.ifc.create_entity('IfcRelDefinesByProperties',
            GlobalId=ifcopenshell.guid.new(),
            RelatingPropertyDefinition=pset,
            RelatedObjects=[obj]
        )

    def assign_pset_to_objects(self, objects, pset):
        """Привязка property set к нескольким объектам"""
        ifcopenshell = _get_ifcopenshell()
        return self.ifc.create_entity('IfcRelDefinesByProperties',
            GlobalId=ifcopenshell.guid.new(),
            RelatingPropertyDefinition=pset,
            RelatedObjects=objects
        )

    def _create_property_value(self, value):
        """Создание IFC property value"""
        if isinstance(value, (int, float)):
            return self.ifc.create_entity('IfcLengthMeasure', wrappedValue=value)
        elif isinstance(value, str):
            return self.ifc.create_entity('IfcText', wrappedValue=value)
        return self.ifc.create_entity('IfcLabel', wrappedValue=str(value))
