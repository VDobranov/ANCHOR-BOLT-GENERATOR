"""
type_factory.py - Создание и кэширование типов IFC
Динамическое создание IfcMechanicalFastenerType с уникальным кэшированием
"""

import uuid
import base64
from gost_data import get_bolt_spec


class TypeFactory:
    """Фабрика для создания и кэширования типов болтов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.types_cache = {}  # Кэш типов: (type_name, params_tuple) -> type_object

    def get_or_create_stud_type(self, bolt_type, execution, diameter, length, material):
        """Get or create IfcMechanicalFastenerType for stud"""
        key = ('stud', bolt_type, execution, diameter, length, material)

        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'Stud_M{diameter}x{length}_{bolt_type}_exec{execution}'

        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                          GlobalId=self._generate_guid(),
                                          Name=type_name,
                                          PredefinedType='USERDEFINED')

        self.types_cache[key] = stud_type
        return stud_type

    def get_or_create_nut_type(self, diameter, material):
        """Get or create IfcMechanicalFastenerType for nut"""
        key = ('nut', diameter, material)

        if key in self.types_cache:
            return self.types_cache[key]

        spec = get_bolt_spec(diameter)
        height = spec.get('nut_height', 10)

        type_name = f'Nut_M{diameter}_H{height}'

        nut_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                         GlobalId=self._generate_guid(),
                                         Name=type_name,
                                         PredefinedType='USERDEFINED')

        self.types_cache[key] = nut_type
        return nut_type

    def get_or_create_washer_type(self, diameter, material):
        """Get or create IfcMechanicalFastenerType for washer"""
        key = ('washer', diameter, material)

        if key in self.types_cache:
            return self.types_cache[key]

        spec = get_bolt_spec(diameter)
        outer_d = spec.get('washer_outer_diameter', diameter + 10)

        type_name = f'Washer_M{diameter}_OD{outer_d}'

        washer_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                            GlobalId=self._generate_guid(),
                                            Name=type_name,
                                            PredefinedType='USERDEFINED')

        self.types_cache[key] = washer_type
        return washer_type

    def get_or_create_assembly_type(self, bolt_type, diameter, material):
        """Get or create IfcMechanicalFastenerType for assembly"""
        key = ('assembly', bolt_type, diameter, material)

        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'AnchorBoltAssembly_{bolt_type}_M{diameter}_{material}'

        assembly_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                              GlobalId=self._generate_guid(),
                                              Name=type_name,
                                              PredefinedType='ANCHORBOLT')

        self.types_cache[key] = assembly_type
        return assembly_type

    def get_cached_types_count(self):
        """Get count of cached types"""
        return len(self.types_cache)

    def _generate_guid(self):
        """Generate IFC GUID"""
        uuid_bytes = uuid.uuid4().bytes
        return base64.b64encode(uuid_bytes).decode()[:22]
