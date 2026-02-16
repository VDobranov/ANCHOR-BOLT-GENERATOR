"""
type_factory.py - Создание и кэширование типов IFC
Динамическое создание IfcMechanicalFastenerType с уникальным кэшированием
"""

from gost_data import get_bolt_spec
import math


class TypeFactory:
    """Фабрика для создания и кэширования типов болтов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.types_cache = {}  # Кэш типов: (type_name, params_tuple) -> type_object

    def get_or_create_stud_type(self, bolt_type, execution, diameter, length, material):
        """Get or create IfcMechanicalFastenerType for stud with geometry"""
        key = ('stud', bolt_type, execution, diameter, length, material)

        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f'Stud_M{diameter}x{length}_{bolt_type}_exec{execution}'

        # Create the type
        stud_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                          GlobalId=self._generate_guid(),
                                          Name=type_name,
                                          PredefinedType='USERDEFINED',
                                          ElementType='STUD')

        # Create geometry representation
        self._create_cylinder_geometry(stud_type, diameter, length)

        self.types_cache[key] = stud_type
        return stud_type

    def get_or_create_nut_type(self, diameter, material):
        """Get or create IfcMechanicalFastenerType for nut with geometry"""
        key = ('nut', diameter, material)

        if key in self.types_cache:
            return self.types_cache[key]

        spec = get_bolt_spec(diameter)
        height = spec.get('nut_height', 10)

        type_name = f'Nut_M{diameter}_H{height}'

        nut_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                         GlobalId=self._generate_guid(),
                                         Name=type_name,
                                         PredefinedType='USERDEFINED',
                                         ElementType='NUT')

        # Create hexagonal nut geometry
        self._create_hex_nut_geometry(nut_type, diameter, height)

        self.types_cache[key] = nut_type
        return nut_type

    def get_or_create_washer_type(self, diameter, material):
        """Get or create IfcMechanicalFastenerType for washer with geometry"""
        key = ('washer', diameter, material)

        if key in self.types_cache:
            return self.types_cache[key]

        spec = get_bolt_spec(diameter)
        outer_d = spec.get('washer_outer_diameter', diameter + 10)
        thickness = spec.get('washer_thickness', 3)

        type_name = f'Washer_M{diameter}_OD{outer_d}'

        washer_type = self.ifc.create_entity('IfcMechanicalFastenerType',
                                            GlobalId=self._generate_guid(),
                                            Name=type_name,
                                            PredefinedType='USERDEFINED',
                                            ElementType='WASHER')

        # Create washer geometry (ring)
        self._create_washer_geometry(washer_type, diameter, outer_d, thickness)

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

    def _create_cylinder_geometry(self, product_type, diameter, length):
        """Create geometry for stud - straight for types 2.1, 5 and bent for types 1.1, 1.2"""
        # Import geometry builder here to avoid circular imports
        from geometry_builder import GeometryBuilder

        builder = GeometryBuilder(self.ifc)

        # Extract bolt type and execution from the product type name
        type_name = product_type.Name or ""
        bolt_type = "1.1"  # Default assumption
        execution = 1  # Default assumption

        # Extract bolt type from the name
        if "_1.1_" in type_name:
            bolt_type = "1.1"
        elif "_1.2_" in type_name:
            bolt_type = "1.2"
        elif "_2.1_" in type_name:
            bolt_type = "2.1"
        elif "_5_" in type_name:
            bolt_type = "5"

        # Extract execution from the name
        if "_exec1" in type_name:
            execution = 1
        elif "_exec2" in type_name:
            execution = 2

        # Determine if bolt has bend
        has_bend = bolt_type in ['1.1', '1.2']

        if has_bend:
            # Create bent geometry for types 1.1 and 1.2
            # Create axis curve for bent stud
            axis_curve = builder.create_composite_curve_stud(bolt_type, diameter, length, execution)

            # Create swept disk solid for bent stud
            stud_radius = diameter / 2.0
            swept_area = self.ifc.create_entity('IfcSweptDiskSolid',
                                              Directrix=axis_curve,
                                              Radius=float(stud_radius))
        else:
            # Create straight geometry for types 2.1 and 5
            # Create axis placement
            placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                              Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]))

            # Create circular profile
            profile = self.ifc.create_entity('IfcCircleProfileDef',
                                            ProfileType='AREA',
                                            ProfileName='CircularProfile',
                                            Radius=diameter / 2.0)

            # Create extrusion direction
            direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])

            # Create swept area solid (extruded cylinder)
            swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
                                               SweptArea=profile,
                                               Position=placement,
                                               ExtrudedDirection=direction,
                                               Depth=length)

        # Create geometric representation
        rep_item = [swept_area]
        rep_context = self._get_representation_context()

        # Create shape representation
        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                                          ContextOfItems=rep_context,
                                          RepresentationIdentifier='Body',
                                          RepresentationType='SweptSolid',
                                          Items=rep_item)

        # Link representation to the product type
        self.ifc.create_entity('IfcProductDefinitionShape',
                              Representations=[shape_rep])

        # Associate the representation with the product type
        self._associate_representation(product_type, shape_rep)

    def _create_hex_nut_geometry(self, product_type, diameter, height):
        """Create hexagonal nut geometry"""
        # Create axis placement
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                          Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]))

        # Create hexagonal profile with inner hole
        # Outer hexagon
        outer_radius = diameter * 0.75  # Standard ratio for hex nuts
        inner_radius = diameter / 2.0 + 0.5  # Slightly larger than thread

        # Create outer hexagon points
        outer_points = []
        for i in range(6):
            angle = i * math.pi / 3  # 60 degrees in radians
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            outer_points.append(self.ifc.create_entity('IfcCartesianPoint', Coordinates=[x, y]))
        
        # Close the polygon
        outer_points.append(outer_points[0])
        
        # Create polyline for outer profile
        outer_polyline = self.ifc.create_entity('IfcPolyline', Points=outer_points)

        # Create inner circle for the hole
        inner_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])
        inner_circle = self.ifc.create_entity('IfcCircle',
                                             Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=inner_center),
                                             Radius=inner_radius)

        # Create profile with voids
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
                                        ProfileType='AREA',
                                        ProfileName='HexNutProfile',
                                        OuterCurve=outer_polyline,
                                        InnerCurves=[inner_circle])

        # Create extrusion direction
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])

        # Create swept area solid (extruded hex nut)
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
                                           SweptArea=profile,
                                           Position=placement,
                                           ExtrudedDirection=direction,
                                           Depth=height)

        # Create geometric representation
        rep_item = [swept_area]
        rep_context = self._get_representation_context()
        
        # Create shape representation
        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                                          ContextOfItems=rep_context,
                                          RepresentationIdentifier='Body',
                                          RepresentationType='SweptSolid',
                                          Items=rep_item)

        # Link representation to the product type
        self.ifc.create_entity('IfcProductDefinitionShape',
                              Representations=[shape_rep])

        # Associate the representation with the product type
        self._associate_representation(product_type, shape_rep)

    def _create_washer_geometry(self, product_type, inner_diameter, outer_diameter, thickness):
        """Create washer geometry (ring)"""
        # Create axis placement
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                          Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]))

        # Create ring profile with inner and outer circles
        inner_radius = inner_diameter / 2.0 + 0.5  # Slightly larger than thread
        outer_radius = outer_diameter / 2.0

        # Create center point
        center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])

        # Create outer circle
        outer_circle = self.ifc.create_entity('IfcCircle',
                                             Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
                                             Radius=outer_radius)

        # Create inner circle
        inner_circle = self.ifc.create_entity('IfcCircle',
                                             Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
                                             Radius=inner_radius)

        # Create profile with voids
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
                                        ProfileType='AREA',
                                        ProfileName='WasherProfile',
                                        OuterCurve=outer_circle,
                                        InnerCurves=[inner_circle])

        # Create extrusion direction
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])

        # Create swept area solid (extruded washer)
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
                                           SweptArea=profile,
                                           Position=placement,
                                           ExtrudedDirection=direction,
                                           Depth=thickness)

        # Create geometric representation
        rep_item = [swept_area]
        rep_context = self._get_representation_context()
        
        # Create shape representation
        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                                          ContextOfItems=rep_context,
                                          RepresentationIdentifier='Body',
                                          RepresentationType='SweptSolid',
                                          Items=rep_item)

        # Link representation to the product type
        self.ifc.create_entity('IfcProductDefinitionShape',
                              Representations=[shape_rep])

        # Associate the representation with the product type
        self._associate_representation(product_type, shape_rep)

    def _get_representation_context(self):
        """Get or create representation context"""
        # Look for existing context
        contexts = self.ifc.by_type('IfcGeometricRepresentationContext')
        if contexts:
            return contexts[0]
        
        # Create new context if not found
        return self.ifc.create_entity('IfcGeometricRepresentationContext',
                                     ContextType='Model',
                                     CoordinateSpaceDimension=3,
                                     Precision=1e-05,
                                     WorldCoordinateSystem=self.ifc.create_entity('IfcAxis2Placement3D',
                                                                               Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])))

    def _associate_representation(self, product_type, shape_rep):
        """Associate representation with product type"""
        # Find the representation maps for this type
        rep_maps = [m for m in self.ifc.by_type('IfcRepresentationMap') if m.MappedRepresentation == shape_rep]
        
        if not rep_maps:
            # Create a new representation map
            rep_map = self.ifc.create_entity('IfcRepresentationMap',
                                            MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                                                                               Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])),
                                            MappedRepresentation=shape_rep)
            
            # Check if RepresentationMaps exists and is mutable
            if not hasattr(product_type, 'RepresentationMaps') or product_type.RepresentationMaps is None:
                # Create a new list and assign it
                product_type.RepresentationMaps = [rep_map]
            else:
                # If it's a tuple, convert to list first
                if isinstance(product_type.RepresentationMaps, tuple):
                    product_type.RepresentationMaps = list(product_type.RepresentationMaps)
                product_type.RepresentationMaps.append(rep_map)
        else:
            # If map already exists, just ensure it's associated with the type
            if not hasattr(product_type, 'RepresentationMaps') or product_type.RepresentationMaps is None:
                product_type.RepresentationMaps = []
            elif isinstance(product_type.RepresentationMaps, tuple):
                product_type.RepresentationMaps = list(product_type.RepresentationMaps)
                
            for rep_map in rep_maps:
                if rep_map not in product_type.RepresentationMaps:
                    product_type.RepresentationMaps.append(rep_map)

    def get_cached_types_count(self):
        """Get count of cached types"""
        return len(self.types_cache)

    def _generate_guid(self):
        """Generate IFC GUID using ifcopenshell"""
        from main import _get_ifcopenshell
        ifcopenshell = _get_ifcopenshell()
        if ifcopenshell is None:
            raise RuntimeError("ifcopenshell not available in type_factory._generate_guid()")
        return ifcopenshell.guid.new()
