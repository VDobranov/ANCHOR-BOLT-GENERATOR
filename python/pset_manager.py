"""
pset_manager.py - Управление Property Sets для IFC объектов
"""


class PSetManager:
    """Управление Property Sets (Pset) для типов и инстансов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.psets = {}

    def create_pset(self, name, properties_dict):
        """Create a property set with given properties"""
        # Create property set
        pset = self.ifc.create_entity('IfcPropertySet',
                                     GlobalId=self._generate_guid(),
                                     Name=name)

        # Create and add properties
        props = []
        for prop_name, prop_value in properties_dict.items():
            prop = self.ifc.create_entity('IfcPropertySingleValue',
                                         Name=prop_name,
                                         NominalValue=self._create_property_value(prop_value))
            props.append(prop)

        pset.HasProperties = props
        return pset

    def create_pset_mechanical_fastener_common(self, nominal_diameter, nominal_length,
                                              thread_length=None, nut_height=None,
                                              washer_thickness=None):
        """
        Create Pset_MechanicalFastenerCommon
        Standard property set for mechanical fasteners
        """
        properties = {
            'NominalDiameter': nominal_diameter,
            'NominalLength': nominal_length,
        }

        if thread_length is not None:
            properties['ThreadLength'] = thread_length

        if nut_height is not None:
            properties['Height'] = nut_height

        if washer_thickness is not None:
            properties['Thickness'] = washer_thickness

        pset = self.create_pset('Pset_MechanicalFastenerCommon', properties)
        return pset

    def create_pset_element_component_common(self, component_type, position_z=0):
        """
        Create Pset_ElementComponentCommon for component properties
        """
        properties = {
            'ComponentType': component_type,
            'PositionZ': position_z,
        }

        pset = self.create_pset('Pset_ElementComponentCommon', properties)
        return pset

    def create_pset_manufacturer_type_information(self, manufacturer, type_designation,
                                                 gost_standard):
        """
        Create Pset_ManufacturerTypeInformation
        """
        properties = {
            'Manufacturer': manufacturer,
            'TypeDesignation': type_designation,
            'StandardDesignation': gost_standard,
        }

        pset = self.create_pset('Pset_ManufacturerTypeInformation', properties)
        return pset

    def assign_pset_to_object(self, obj, pset):
        """Assign property set to IFC object"""
        rel = self.ifc.create_entity('IfcRelDefinesByProperties',
                                    GlobalId=self._generate_guid(),
                                    RelatingPropertyDefinition=pset,
                                    RelatedObjects=[obj])
        return rel

    def assign_pset_to_objects(self, objects, pset):
        """Assign property set to multiple objects"""
        rel = self.ifc.create_entity('IfcRelDefinesByProperties',
                                    GlobalId=self._generate_guid(),
                                    RelatingPropertyDefinition=pset,
                                    RelatedObjects=objects)
        return rel

    def _create_property_value(self, value):
        """Create appropriate IFC property value"""
        if isinstance(value, (int, float)):
            return self.ifc.create_entity('IfcLengthMeasure', wrappedValue=value)
        elif isinstance(value, str):
            return self.ifc.create_entity('IfcText', wrappedValue=value)
        else:
            return self.ifc.create_entity('IfcLabel', wrappedValue=str(value))

    def _generate_guid(self):
        """Generate IFC GUID using ifcopenshell"""
        from main import _get_ifcopenshell
        ifcopenshell = _get_ifcopenshell()
        if ifcopenshell is None:
            raise RuntimeError("ifcopenshell not available in pset_manager._generate_guid()")
        return ifcopenshell.guid.new()


def create_fastener_psets(ifc_doc, pset_manager, component_type, diameter,
                         length=None, height=None, material_gost='19281-2014'):
    """
    Helper function to create all necessary PSets for a fastener

    Args:
        ifc_doc: IFC document
        pset_manager: PSetManager instance
        component_type: Type of component (STUD, NUT, WASHER, ASSEMBLY)
        diameter: Nominal diameter in mm
        length: Length (for studs)
        height: Height (for nuts/washers)
        material_gost: GOST standard for material
    """
    psets = []

    # Common pset
    pset_common = pset_manager.create_pset_mechanical_fastener_common(
        nominal_diameter=diameter,
        nominal_length=length if length else 0,
        nut_height=height if height else 0
    )
    psets.append(pset_common)

    # Component pset
    pset_component = pset_manager.create_pset_element_component_common(
        component_type=component_type,
        position_z=0
    )
    psets.append(pset_component)

    # Manufacturer info pset
    pset_mfr = pset_manager.create_pset_manufacturer_type_information(
        manufacturer='ANCHOR-BOLT-GENERATOR',
        type_designation=f'{component_type}_M{diameter}',
        gost_standard=f'ГОСТ {material_gost}'
    )
    psets.append(pset_mfr)

    return psets
