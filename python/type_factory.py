"""
type_factory.py — Фабрика для создания и кэширования типов IFC
Вся геометрия делегирована в geometry_builder.py
"""

from utils import get_ifcopenshell
from gost_data import get_nut_dimensions, get_washer_dimensions
from geometry_builder import GeometryBuilder


class TypeFactory:
    """Фабрика типов IFC MechanicalFastenerType"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.types_cache = {}
        self.builder = GeometryBuilder(ifc_doc)

    def get_or_create_stud_type(self, bolt_type, execution, diameter, length, material):
        """Создание/получение типа шпильки"""
        key = ('stud', bolt_type, execution, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'Stud_M{diameter}x{length}_{bolt_type}_exec{execution}'
        ifc = get_ifcopenshell()
        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='STUD'
        )

        # Делегируем построение геометрии в GeometryBuilder
        if bolt_type in ['1.1', '1.2']:
            shape_rep = self.builder.create_bent_stud_solid(
                bolt_type, diameter, length, execution
            )
        else:
            shape_rep = self.builder.create_straight_stud_solid(diameter, length)

        self.builder.associate_representation(stud_type, shape_rep)
        self.types_cache[key] = stud_type
        return stud_type

    def get_or_create_nut_type(self, diameter, material):
        """Создание/получение типа гайки"""
        key = ('nut', diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        nut_dim = get_nut_dimensions(diameter)
        height = nut_dim['height'] if nut_dim else 10
        type_name = f'Nut_M{diameter}_H{height}'
        ifc = get_ifcopenshell()

        nut_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='NUT'
        )

        # Делегируем построение геометрии в GeometryBuilder
        shape_rep = self.builder.create_nut_solid(diameter, height)
        self.builder.associate_representation(nut_type, shape_rep)
        self.types_cache[key] = nut_type
        return nut_type

    def get_or_create_washer_type(self, diameter, material):
        """Создание/получение типа шайбы"""
        key = ('washer', diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        washer_dim = get_washer_dimensions(diameter)
        outer_d = washer_dim['outer_diameter'] if washer_dim else diameter + 10
        thickness = washer_dim['thickness'] if washer_dim else 3
        type_name = f'Washer_M{diameter}_OD{outer_d}'
        ifc = get_ifcopenshell()

        washer_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='WASHER'
        )

        # Делегируем построение геометрии в GeometryBuilder
        shape_rep = self.builder.create_washer_solid(diameter, outer_d, thickness)
        self.builder.associate_representation(washer_type, shape_rep)
        self.types_cache[key] = washer_type
        return washer_type

    def get_or_create_assembly_type(self, bolt_type, diameter, material):
        """Создание/получение типа сборки"""
        key = ('assembly', bolt_type, diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'AnchorBoltAssembly_{bolt_type}_M{diameter}_{material}'
        ifc = get_ifcopenshell()

        assembly_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifc.guid.new(),
            Name=type_name,
            PredefinedType='ANCHORBOLT'
        )

        # Сборка не имеет собственной геометрии
        self.types_cache[key] = assembly_type
        return assembly_type

    def get_cached_types_count(self):
        """Количество закэшированных типов"""
        return len(self.types_cache)
