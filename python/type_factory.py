"""
type_factory.py — Фабрика для создания и кэширования типов IFC
Использует geometry_builder для построения геометрии
"""

import math
from gost_data import get_nut_dimensions, get_washer_dimensions


def _get_ifcopenshell():
    """Ленивый импорт ifcopenshell"""
    from main import _get_ifcopenshell as get_ifc
    return get_ifc()


class TypeFactory:
    """Фабрика типов IFC MechanicalFastenerType"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.types_cache = {}
        self._context = None

    def get_or_create_stud_type(self, bolt_type, execution, diameter, length, material):
        """Создание/получение типа шпильки"""
        key = ('stud', bolt_type, execution, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'Stud_M{diameter}x{length}_{bolt_type}_exec{execution}'
        ifcopenshell = _get_ifcopenshell()
        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifcopenshell.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='STUD'
        )

        self._create_stud_geometry(stud_type, bolt_type, diameter, length, execution)
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
        ifcopenshell = _get_ifcopenshell()

        nut_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifcopenshell.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='NUT'
        )

        self._create_nut_geometry(nut_type, diameter, height)
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
        ifcopenshell = _get_ifcopenshell()

        washer_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifcopenshell.guid.new(),
            Name=type_name,
            PredefinedType='USERDEFINED',
            ElementType='WASHER'
        )

        self._create_washer_geometry(washer_type, diameter, outer_d, thickness)
        self.types_cache[key] = washer_type
        return washer_type

    def get_or_create_assembly_type(self, bolt_type, diameter, material):
        """Создание/получение типа сборки"""
        key = ('assembly', bolt_type, diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'AnchorBoltAssembly_{bolt_type}_M{diameter}_{material}'
        ifcopenshell = _get_ifcopenshell()

        assembly_type = self.ifc.create_entity('IfcMechanicalFastenerType',
            GlobalId=ifcopenshell.guid.new(),
            Name=type_name,
            PredefinedType='ANCHORBOLT'
        )

        self.types_cache[key] = assembly_type
        return assembly_type

    def _get_context(self):
        """Получение или создание геометрического контекста"""
        if self._context:
            return self._context

        contexts = self.ifc.by_type('IfcGeometricRepresentationContext')
        if contexts:
            self._context = contexts[0]
            return self._context

        self._context = self.ifc.create_entity('IfcGeometricRepresentationContext',
            ContextType='Model',
            CoordinateSpaceDimension=3,
            Precision=1e-05,
            WorldCoordinateSystem=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
            )
        )
        return self._context

    def _create_stud_geometry(self, product_type, bolt_type, diameter, length, execution):
        """Создание геометрии шпильки (цилиндр или изогнутая форма)"""
        has_bend = bolt_type in ['1.1', '1.2']
        context = self._get_context()

        if has_bend:
            # Bent stud: используем IfcSweptDiskSolid с составной кривой
            from geometry_builder import GeometryBuilder
            builder = GeometryBuilder(self.ifc)
            axis_curve = builder.create_composite_curve_stud(bolt_type, diameter, length, execution)
            swept_area = self.ifc.create_entity('IfcSweptDiskSolid',
                Directrix=axis_curve,
                Radius=float(diameter / 2.0)
            )
        else:
            # Straight stud: цилиндр через IfcExtrudedAreaSolid
            placement = self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
            )
            profile = self.ifc.create_entity('IfcCircleProfileDef',
                ProfileType='AREA',
                ProfileName='CircularProfile',
                Radius=diameter / 2.0
            )
            direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
            swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
                SweptArea=profile,
                Position=placement,
                ExtrudedDirection=direction,
                Depth=length
            )

        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=context,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[swept_area]
        )

        self.ifc.create_entity('IfcProductDefinitionShape',
            Representations=[shape_rep]
        )

        self._associate_representation(product_type, shape_rep)

    def _create_nut_geometry(self, product_type, diameter, height):
        """Создание геометрии гайки (шестиугольник с отверстием)"""
        from gost_data import get_nut_dimensions
        
        context = self._get_context()
        
        # Получаем размер под ключ из DIM.py
        nut_dim = get_nut_dimensions(diameter)
        s_width = nut_dim['s_width'] if nut_dim else diameter * 1.5
        
        # Размер под ключ (S) — расстояние между параллельными гранями
        # Радиус описанной окружности (до вершин): R = S / cos(30°) = 2S/√3
        outer_radius = s_width / math.cos(math.pi / 6)  # S / cos(30°)
        inner_radius = diameter / 2.0 + 0.5

        # Внешний шестиугольник
        outer_points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            outer_points.append(self.ifc.create_entity('IfcCartesianPoint', Coordinates=[x, y]))
        outer_points.append(outer_points[0])

        outer_polyline = self.ifc.create_entity('IfcPolyline', Points=outer_points)

        # Внутреннее отверстие
        inner_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])
        inner_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=inner_center),
            Radius=inner_radius
        )

        # Профиль с отверстием
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            ProfileName='HexNutProfile',
            OuterCurve=outer_polyline,
            InnerCurves=[inner_circle]
        )

        # Экструзия
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        )
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=placement,
            ExtrudedDirection=direction,
            Depth=height
        )

        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=context,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[swept_area]
        )

        self.ifc.create_entity('IfcProductDefinitionShape', Representations=[shape_rep])
        self._associate_representation(product_type, shape_rep)

    def _create_washer_geometry(self, product_type, inner_diameter, outer_diameter, thickness):
        """Создание геометрии шайбы (кольцо)"""
        context = self._get_context()
        inner_radius = inner_diameter / 2.0 + 0.5
        outer_radius = outer_diameter / 2.0

        center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])

        outer_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
            Radius=outer_radius
        )
        inner_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
            Radius=inner_radius
        )

        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            ProfileName='WasherProfile',
            OuterCurve=outer_circle,
            InnerCurves=[inner_circle]
        )

        placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        )
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=placement,
            ExtrudedDirection=direction,
            Depth=thickness
        )

        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=context,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[swept_area]
        )

        self.ifc.create_entity('IfcProductDefinitionShape', Representations=[shape_rep])
        self._associate_representation(product_type, shape_rep)

    def _associate_representation(self, product_type, shape_rep):
        """Ассоциация представления с типом продукта"""
        rep_maps = [m for m in self.ifc.by_type('IfcRepresentationMap')
                    if m.MappedRepresentation == shape_rep]

        if not rep_maps:
            rep_map = self.ifc.create_entity('IfcRepresentationMap',
                MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                    Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
                ),
                MappedRepresentation=shape_rep
            )

            if product_type.RepresentationMaps is None:
                product_type.RepresentationMaps = [rep_map]
            elif isinstance(product_type.RepresentationMaps, tuple):
                product_type.RepresentationMaps = list(product_type.RepresentationMaps) + [rep_map]
            else:
                product_type.RepresentationMaps.append(rep_map)

    def get_cached_types_count(self):
        """Количество закэшированных типов"""
        return len(self.types_cache)
