"""
instance_factory.py - Создание инстансов болтов и управление их размещением
"""

from type_factory import TypeFactory
from gost_data import validate_parameters, get_bolt_spec

# ifcopenshell imported lazily after micropip installation
# import ifcopenshell
# import ifcopenshell.geom as geom


class InstanceFactory:
    """Фабрика для создания инстансов болтов и компонентов"""

    def __init__(self, ifc_doc, type_factory=None):
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)
        self.instances = []

    def create_bolt_assembly(self, bolt_type, execution, diameter, length, material,
                            has_bottom_nut=False, has_top_nut1=False, has_top_nut2=False, has_washers=False):
        """
        Create complete anchor bolt assembly with all components

        Returns:
            {
                'assembly': assembly_instance,
                'stud': stud_instance,
                'components': [list of all component instances],
                'mesh_data': {vertices, indices, colors for 3D visualization}
            }
        """
        # Validate parameters
        validate_parameters(bolt_type, execution, diameter, length, material)

        # Get bolt specifications
        spec = get_bolt_spec(diameter)

        # Get types
        stud_type = self.type_factory.get_or_create_stud_type(
            bolt_type, execution, diameter, length, material
        )
        nut_type = self.type_factory.get_or_create_nut_type(diameter, material)
        washer_type = self.type_factory.get_or_create_washer_type(diameter, material)
        assembly_type = self.type_factory.get_or_create_assembly_type(
            bolt_type, diameter, material
        )

        # Get storey for placement
        storeys = self.ifc.by_type('IfcBuildingStorey')
        storey = storeys[0] if storeys else None

        # Create assembly instance
        assembly = self.ifc.create_entity('IfcMechanicalFastener',
                                         GlobalId=self._generate_guid(),
                                         Name=f'AnchorBolt_{bolt_type}_M{diameter}x{length}',
                                         ObjectType='ANCHORBOLT',
                                         PredefinedType='ANCHORBOLT')

        # Add direct representation to the assembly instance for ifcopenshell.geom compatibility
        self._add_direct_representation(assembly, assembly_type)

        # Create instances for components
        components = []

        # Calculate positions for nuts and washers
        washer_thickness = spec.get('washer_thickness', 3)
        nut_height = spec.get('nut_height', 10)

        # Create lists to group instances by type
        stud_instances = []
        nut_instances = []
        washer_instances = []

        # Stud instance - positioned from bottom (length) to top (0), so top is closer to origin
        # For bent bolts, the placement should reflect the actual orientation
        if bolt_type in ['1.1', '1.2']:
            # For bent bolts, position at the bottom (where the straight part begins)
            stud_placement = self._create_placement((0, 0, 0))  # Positioned at the bottom
        else:
            # For straight bolts, position at the top
            stud_placement = self._create_placement((0, 0, 0))  # Origin at top of threaded portion

        stud = self.ifc.create_entity('IfcMechanicalFastener',
                                     GlobalId=self._generate_guid(),
                                     Name=f'Stud_M{diameter}x{length}',
                                     ObjectType='STUD',
                                     ObjectPlacement=stud_placement)

        # Add direct representation to the stud instance for ifcopenshell.geom compatibility
        self._add_direct_representation(stud, stud_type)
        stud_instances.append(stud)

        component_instances = [stud]

        # Top washer (optional) - placed at the top (closer to origin), available for all bolt types
        washer_top = None
        if has_washers:
            washer_top_placement = self._create_placement((0, 0, washer_thickness/2))  # Closer to origin
            washer_top = self.ifc.create_entity('IfcMechanicalFastener',
                                               GlobalId=self._generate_guid(),
                                               Name=f'Washer_Top_M{diameter}',
                                               ObjectType='WASHER',
                                               ObjectPlacement=washer_top_placement)

            # Add direct representation to the washer instance for ifcopenshell.geom compatibility
            self._add_direct_representation(washer_top, washer_type)
            washer_instances.append(washer_top)

            component_instances.append(washer_top)

        # Top nut 1 (optional) - placed at the top (closer to origin), available for all bolt types
        nut_top1 = None
        if has_top_nut1:
            if has_washers and washer_top:
                # Place nut above washer (closer to origin)
                nut_top1_placement = self._create_placement((0, 0, washer_thickness/2 + nut_height/2))
            else:
                # Place nut at the top (closer to origin)
                nut_top1_placement = self._create_placement((0, 0, nut_height/2))

            nut_top1 = self.ifc.create_entity('IfcMechanicalFastener',
                                            GlobalId=self._generate_guid(),
                                            Name=f'Nut_Top1_M{diameter}',
                                            ObjectType='NUT',
                                            ObjectPlacement=nut_top1_placement)

            # Add direct representation to the nut instance for ifcopenshell.geom compatibility
            self._add_direct_representation(nut_top1, nut_type)
            nut_instances.append(nut_top1)

            component_instances.append(nut_top1)

        # Top nut 2 (optional) - placed above the first nut (even closer to origin), available for all bolt types
        if has_top_nut2:
            if nut_top1:
                # Place nut2 above nut1 (closer to origin)
                nut_top2_placement = self._create_placement((0, 0, washer_thickness + nut_height + nut_height/2))
            elif has_washers and washer_top:
                # Place nut2 above washer (when no nut1 but washer exists)
                nut_top2_placement = self._create_placement((0, 0, washer_thickness/2 + nut_height + nut_height/2))
            else:
                # Place nut2 at the top plus one nut height
                nut_top2_placement = self._create_placement((0, 0, nut_height + nut_height/2))

            nut_top2 = self.ifc.create_entity('IfcMechanicalFastener',
                                            GlobalId=self._generate_guid(),
                                            Name=f'Nut_Top2_M{diameter}',
                                            ObjectType='NUT',
                                            ObjectPlacement=nut_top2_placement)

            # Add direct representation to the nut instance for ifcopenshell.geom compatibility
            self._add_direct_representation(nut_top2, nut_type)
            nut_instances.append(nut_top2)

            component_instances.append(nut_top2)

        # Bottom washer (optional) - placed at the bottom (farther from origin), only for bolt type 2.x
        if has_washers and bolt_type.startswith('2.'):
            washer_bottom_placement = self._create_placement((0, 0, length - washer_thickness/2))  # At the bottom (farther from origin)
            washer_bottom = self.ifc.create_entity('IfcMechanicalFastener',
                                                  GlobalId=self._generate_guid(),
                                                  Name=f'Washer_Bottom_M{diameter}',
                                                  ObjectType='WASHER',
                                                  ObjectPlacement=washer_bottom_placement)

            # Add direct representation to the washer instance for ifcopenshell.geom compatibility
            self._add_direct_representation(washer_bottom, washer_type)
            washer_instances.append(washer_bottom)

            component_instances.append(washer_bottom)

        # Bottom nut (optional) - placed below the washer, only for bolt type 2.x
        if has_bottom_nut and bolt_type.startswith('2.'):
            nut_bottom_placement = self._create_placement((0, 0, length + washer_thickness/2 + nut_height/2))  # Below washer
            nut_bottom = self.ifc.create_entity('IfcMechanicalFastener',
                                               GlobalId=self._generate_guid(),
                                               Name=f'Nut_Bottom_M{diameter}',
                                               ObjectType='NUT',
                                               ObjectPlacement=nut_bottom_placement)

            # Add direct representation to the nut instance for ifcopenshell.geom compatibility
            self._add_direct_representation(nut_bottom, nut_type)
            nut_instances.append(nut_bottom)

            component_instances.append(nut_bottom)

        # Create single IfcRelDefinesByType relationships for each type
        # Assembly type relationship
        self.ifc.create_entity('IfcRelDefinesByType',
                              GlobalId=self._generate_guid(),
                              RelatingType=assembly_type,
                              RelatedObjects=[assembly])

        # Stud type relationship
        if stud_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=stud_type,
                                  RelatedObjects=stud_instances)

        # Nut type relationship (if there are any nuts)
        if nut_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=nut_type,
                                  RelatedObjects=nut_instances)

        # Washer type relationship (if there are any washers)
        if washer_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=washer_type,
                                  RelatedObjects=washer_instances)

        # Create containment relationship - all components are contained in the spatial structure
        if storey:
            # Add all components (including assembly) to the spatial structure
            all_components = [assembly] + component_instances
            self.ifc.create_entity('IfcRelContainedInSpatialStructure',
                                  GlobalId=self._generate_guid(),
                                  RelatingStructure=storey,
                                  RelatedElements=all_components)

        # Create aggregation relationship (assembly contains components)
        self.ifc.create_entity('IfcRelAggregates',
                              GlobalId=self._generate_guid(),
                              RelatingObject=assembly,
                              RelatedObjects=component_instances)

        # Create connections between components
        for i in range(len(component_instances) - 1):
            self.ifc.create_entity('IfcRelConnectsElements',
                                  GlobalId=self._generate_guid(),
                                  RelatingElement=component_instances[i],
                                  RelatedElement=component_instances[i + 1])

        # Generate mesh data for 3D visualization using ifcopenshell.geom
        mesh_data = self._generate_mesh_data_with_geom(
            component_instances, bolt_type, diameter, length, material,
            has_bottom_nut, has_top_nut1, has_top_nut2, has_washers
        )

        self.instances.append({
            'assembly': assembly,
            'components': component_instances,
            'mesh_data': mesh_data
        })

        return {
            'assembly': assembly,
            'stud': stud,
            'components': component_instances,
            'mesh_data': mesh_data
        }

    def _add_direct_representation(self, instance, type_obj):
        """Add direct representation to instance for ifcopenshell.geom compatibility"""
        # Check if the type has representation maps
        if hasattr(type_obj, 'RepresentationMaps') and type_obj.RepresentationMaps:
            # Get the first representation map from the type
            rep_map = type_obj.RepresentationMaps[0] if isinstance(type_obj.RepresentationMaps, (list, tuple)) else type_obj.RepresentationMaps

            # If it's a single map, put it in a list
            if not isinstance(rep_map, (list, tuple)):
                rep_maps = [rep_map]
            else:
                rep_maps = rep_map

            # For each representation map in the type
            for rep_map in rep_maps:
                if hasattr(rep_map, 'MappedRepresentation'):
                    mapped_rep = rep_map.MappedRepresentation

                    # Get the context and type information
                    context = mapped_rep.ContextOfItems
                    identifier = mapped_rep.RepresentationIdentifier
                    rep_type = mapped_rep.RepresentationType
                    items = mapped_rep.Items  # This should be the geometric elements

                    # Create a new shape representation for the instance by duplicating the items from the type
                    # This ensures that each instance has its own representation which is required by some IFC viewers
                    try:
                        # Duplicate each geometric item from the type to the instance
                        duplicated_items = []
                        for item in items:
                            # Create a duplicate of the geometric item
                            if item.is_a() == 'IfcSweptDiskSolid':
                                # For IfcSweptDiskSolid, duplicate the Directrix and copy other properties
                                duplicated_directrix = self._duplicate_curve(item.Directrix)
                                duplicated_item = self.ifc.create_entity('IfcSweptDiskSolid',
                                                                       Directrix=duplicated_directrix,
                                                                       Radius=item.Radius)
                                duplicated_items.append(duplicated_item)
                            elif item.is_a() == 'IfcExtrudedAreaSolid':
                                # For IfcExtrudedAreaSolid, duplicate the SweptArea and copy other properties
                                duplicated_swept_area = self._duplicate_profile(item.SweptArea)
                                duplicated_position = self._duplicate_placement(item.Position)
                                duplicated_extruded_direction = self._duplicate_direction(item.ExtrudedDirection)
                                duplicated_item = self.ifc.create_entity('IfcExtrudedAreaSolid',
                                                                       SweptArea=duplicated_swept_area,
                                                                       Position=duplicated_position,
                                                                       ExtrudedDirection=duplicated_extruded_direction,
                                                                       Depth=item.Depth)
                                duplicated_items.append(duplicated_item)
                            else:
                                # For other items, just add them directly
                                duplicated_items.append(item)

                        instance_shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                                                                  ContextOfItems=context,
                                                                  RepresentationIdentifier=identifier,
                                                                  RepresentationType=rep_type,
                                                                  Items=duplicated_items)

                        # Create a product definition shape containing this representation
                        prod_def_shape = self.ifc.create_entity('IfcProductDefinitionShape',
                                                               Representations=[instance_shape_rep])

                        # Link the product definition shape to the instance
                        instance.Representation = prod_def_shape
                    except Exception as e:
                        # If duplication doesn't work, create a minimal representation
                        print(f"Could not create representation for {instance.Name}: {str(e)}")
                        # Fallback: create a minimal representation to avoid "Representation is NULL" error
                        try:
                            # Create a minimal context if needed
                            context = self._get_or_create_context()

                            # Create a minimal representation
                            instance_shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                                                                      ContextOfItems=context,
                                                                      RepresentationIdentifier='Body',
                                                                      RepresentationType='SweptSolid',
                                                                      Items=[])

                            prod_def_shape = self.ifc.create_entity('IfcProductDefinitionShape',
                                                                   Representations=[instance_shape_rep])

                            instance.Representation = prod_def_shape
                        except Exception as fallback_error:
                            print(f"Fallback representation creation also failed: {str(fallback_error)}")
    
    def _get_or_create_context(self):
        """Get or create geometric representation context"""
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

    def _duplicate_curve(self, curve):
        """Duplicate a curve entity"""
        if curve.is_a() == 'IfcCompositeCurve':
            # Duplicate composite curve
            duplicated_segments = []
            for segment in curve.Segments:
                duplicated_segment = self._duplicate_curve_segment(segment)
                duplicated_segments.append(duplicated_segment)
            return self.ifc.create_entity('IfcCompositeCurve',
                                         Segments=duplicated_segments,
                                         SelfIntersect=curve.SelfIntersect)
        elif curve.is_a() == 'IfcPolyline':
            # Duplicate polyline
            duplicated_points = []
            for point in curve.Points:
                duplicated_point = self._duplicate_point(point)
                duplicated_points.append(duplicated_point)
            return self.ifc.create_entity('IfcPolyline',
                                         Points=duplicated_points)
        else:
            # For other curve types, return the original
            return curve

    def _duplicate_curve_segment(self, segment):
        """Duplicate a curve segment"""
        duplicated_parent_curve = self._duplicate_curve(segment.ParentCurve)
        return self.ifc.create_entity('IfcCompositeCurveSegment',
                                     Transition=segment.Transition,
                                     SameSense=segment.SameSense,
                                     ParentCurve=duplicated_parent_curve)

    def _duplicate_point(self, point):
        """Duplicate a point entity"""
        return self.ifc.create_entity('IfcCartesianPoint',
                                     Coordinates=point.Coordinates)

    def _duplicate_direction(self, direction):
        """Duplicate a direction entity"""
        return self.ifc.create_entity('IfcDirection',
                                     DirectionRatios=direction.DirectionRatios)

    def _duplicate_placement(self, placement):
        """Duplicate a placement entity"""
        if placement.is_a() == 'IfcLocalPlacement':
            # For IfcLocalPlacement, duplicate the relative placement and parent placement
            duplicated_relative_placement = self._duplicate_placement(placement.RelativePlacement) if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement else None
            duplicated_placement_rel_to = self._duplicate_placement(placement.PlacementRelTo) if hasattr(placement, 'PlacementRelTo') and placement.PlacementRelTo else None
            return self.ifc.create_entity('IfcLocalPlacement',
                                         PlacementRelTo=duplicated_placement_rel_to,
                                         RelativePlacement=duplicated_relative_placement)
        elif placement.is_a() == 'IfcAxis2Placement3D':
            duplicated_location = self._duplicate_point(placement.Location)
            duplicated_axis = self._duplicate_direction(placement.Axis) if placement.Axis else None
            duplicated_ref_direction = self._duplicate_direction(placement.RefDirection) if placement.RefDirection else None
            return self.ifc.create_entity('IfcAxis2Placement3D',
                                         Location=duplicated_location,
                                         Axis=duplicated_axis,
                                         RefDirection=duplicated_ref_direction)
        else:
            # For other placement types, return the original
            return placement

    def _duplicate_profile(self, profile):
        """Duplicate a profile entity"""
        # For now, return the original profile
        # In a more complex implementation, we would duplicate the profile properly
        return profile

    def _generate_mesh_data_with_geom(self, components, bolt_type, diameter, length, material,
                                     has_bottom_nut, has_top_nut1, has_top_nut2, has_washers):
        """Generate mesh data with fallback to manual generation (optimized for Pyodide)"""
        meshes = []
        
        # Map component types to colors
        color_map = {
            'STUD': 0x8B8B8B,      # Gray
            'WASHER': 0xA9A9A9,    # Dark gray
            'NUT': 0x696969,       # Dim gray
            'ANCHORBOLT': 0x4F4F4F # Darker gray
        }
        
        # In Pyodide environment, directly use the fallback method for better reliability
        for i, component in enumerate(components):
            # Create mesh using the improved fallback method that accounts for placement
            fallback_mesh = self._create_fallback_mesh(component, i, diameter, length, color_map)
            if fallback_mesh:
                meshes.append(fallback_mesh)

        return {'meshes': meshes}

    def _create_fallback_mesh(self, component, index, diameter, length, color_map):
        """Create simplified fallback mesh if geometry extraction fails"""
        import math
        
        comp_type = component.ObjectType or 'UNKNOWN'
        color = color_map.get(comp_type, 0xCCCCCC)
        
        # Get bolt specifications
        spec = get_bolt_spec(diameter)
        
        # Create basic shapes based on component type
        if comp_type == 'STUD':
            # Get bolt type from component name to determine if it's bent
            comp_name = component.Name or ""
            bolt_type = "1.1"  # Default assumption
            
            # Extract bolt type from the name
            if "_1.1_" in comp_name:
                bolt_type = "1.1"
            elif "_1.2_" in comp_name:
                bolt_type = "1.2"
            elif "_2.1_" in comp_name:
                bolt_type = "2.1"
            elif "_5_" in comp_name:
                bolt_type = "5"

            # Determine if bolt has bend
            has_bend = bolt_type in ['1.1', '1.2']
            
            segments = 16  # Number of segments for circular cross-section
            vertices = []
            indices = []

            # Get the placement of the component to determine position
            placement = component.ObjectPlacement
            if placement and hasattr(placement, 'Location'):
                loc = placement.Location.Coordinates
                pos_x, pos_y, pos_z = loc[0], loc[1], loc[2]
            else:
                pos_x, pos_y, pos_z = 0.0, 0.0, 0.0

            if has_bend:
                # For bent studs, create a simplified representation
                # Match the geometry created in geometry_builder.py
                radius = diameter * (1.5 if bolt_type == '1.1' else 2.0)

                # Create 3 main parts: upper straight, arc, lower straight
                # Following the same logic as in geometry_builder.create_composite_curve_stud
                # Upper straight line: from top (pos_x,pos_y,pos_z+length) to bend point (pos_x,pos_y,pos_z+length-radius)
                
                # Calculate upper straight points
                num_upper_points = 10
                upper_points = []
                for i in range(num_upper_points):
                    z = pos_z + length - i * radius / (num_upper_points - 1)
                    upper_points.append((pos_x, pos_y, z))

                # Calculate arc points (same as in geometry_builder)
                num_arc_points = 10
                arc_points = []
                for i in range(num_arc_points):
                    angle = (math.pi / 2) * (i / num_arc_points)  # From 0 to pi/2
                    x = pos_x + radius * (1 - math.cos(angle))
                    y = pos_y
                    z = pos_z + length - radius - radius * math.sin(angle)
                    arc_points.append((x, y, z))

                # Calculate lower straight points: from bend point (pos_x+radius,pos_y,pos_z+length-2*radius) to bottom (pos_x+radius,pos_y,pos_z)
                num_lower_points = 10
                lower_points = []
                for i in range(num_lower_points):
                    z = pos_z + length - 2 * radius - i * (length - 2 * radius) / (num_lower_points - 1)
                    x = pos_x + radius
                    y = pos_y
                    lower_points.append((x, y, z))

                # Combine all points
                all_points = upper_points + arc_points + lower_points

                # Create tube-like shape by connecting circular cross-sections at each point
                for i, (cx, cy, cz) in enumerate(all_points):
                    # Create circular cross-section at this point
                    for j in range(segments):
                        angle = 2 * math.pi * j / segments
                        x = cx + (diameter / 2) * math.cos(angle)
                        y = cy + (diameter / 2) * math.sin(angle)
                        z = cz
                        vertices.extend([x, y, z])

                # Create indices to connect adjacent cross-sections
                for i in range(len(all_points) - 1):
                    for j in range(segments):
                        next_j = (j + 1) % segments

                        # Connect current cross-section to next
                        indices.extend([
                            i * segments + j,
                            i * segments + next_j,
                            (i + 1) * segments + j
                        ])
                        indices.extend([
                            i * segments + next_j,
                            (i + 1) * segments + next_j,
                            (i + 1) * segments + j
                        ])
            else:
                # Create straight cylinder for other bolt types
                # Top and bottom centers (with corrected orientation: top is closer to origin)
                vertices.append([pos_x, pos_y, pos_z])  # 0: top center (closer to origin)
                vertices.append([pos_x, pos_y, pos_z + length])  # 1: bottom center (farther from origin)

                # Top circle (closer to origin)
                for i in range(segments):
                    angle = 2 * math.pi * i / segments
                    x = pos_x + (diameter / 2) * math.cos(angle)
                    y = pos_y + (diameter / 2) * math.sin(angle)
                    z = pos_z
                    vertices.append([x, y, z])

                # Bottom circle (farther from origin)
                for i in range(segments):
                    angle = 2 * math.pi * i / segments
                    x = pos_x + (diameter / 2) * math.cos(angle)
                    y = pos_y + (diameter / 2) * math.sin(angle)
                    z = pos_z + length
                    vertices.append([x, y, z])

                # Top triangles
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([0, 2 + i, 2 + next_i])

                # Bottom triangles
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([1, 2 + segments + next_i, 2 + segments + i])

                # Side triangles
                for i in range(segments):
                    next_i = (i + 1) % segments
                    indices.extend([2 + i, 2 + segments + i, 2 + next_i])
                    indices.extend([2 + next_i, 2 + segments + i, 2 + segments + next_i])

            return {
                'vertices': vertices,
                'indices': indices,
                'color': color,
                'name': component.Name or f'{comp_type}_{index}',
                'id': component.GlobalId,
                'metadata': {
                    'type': comp_type,
                    'diameter': diameter,
                    'length': length,
                    'bolt_type': bolt_type
                }
            }
        elif comp_type == 'WASHER':
            # Create a ring for washer
            washer_thickness = spec.get('washer_thickness', 3)
            washer_od = spec.get('washer_outer_diameter', diameter + 10)
            
            segments = 16
            vertices = []
            indices = []

            # Get the placement of the component to determine position
            placement = component.ObjectPlacement
            if placement and hasattr(placement, 'Location'):
                loc = placement.Location.Coordinates
                pos_x, pos_y, pos_z = loc[0], loc[1], loc[2]
            else:
                pos_x, pos_y, pos_z = 0.0, 0.0, 0.0
            
            # Bottom outer circle
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = pos_x + (washer_od / 2) * math.cos(angle)
                y = pos_y + (washer_od / 2) * math.sin(angle)
                z = pos_z - washer_thickness / 2
                vertices.append([x, y, z])

            # Bottom inner circle
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = pos_x + (diameter / 2) * math.cos(angle)
                y = pos_y + (diameter / 2) * math.sin(angle)
                z = pos_z - washer_thickness / 2
                vertices.append([x, y, z])

            # Top outer circle
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = pos_x + (washer_od / 2) * math.cos(angle)
                y = pos_y + (washer_od / 2) * math.sin(angle)
                z = pos_z + washer_thickness / 2
                vertices.append([x, y, z])

            # Top inner circle
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                x = pos_x + (diameter / 2) * math.cos(angle)
                y = pos_y + (diameter / 2) * math.sin(angle)
                z = pos_z + washer_thickness / 2
                vertices.append([x, y, z])

            # Bottom faces
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([i, segments + next_i, segments + i])
                indices.extend([i, next_i, segments + next_i])

            # Top faces
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([2 * segments + i, 3 * segments + i, 3 * segments + next_i])
                indices.extend([2 * segments + i, 3 * segments + next_i, 2 * segments + next_i])

            # Side faces (outer and inner)
            for i in range(segments):
                next_i = (i + 1) % segments
                # Outer
                indices.extend([i, 2 * segments + i, 2 * segments + next_i])
                indices.extend([i, 2 * segments + next_i, next_i])
                # Inner
                indices.extend([segments + i, segments + next_i, 3 * segments + next_i])
                indices.extend([segments + i, 3 * segments + next_i, 3 * segments + i])

            return {
                'vertices': [v for vertex in vertices for v in vertex],
                'indices': indices,
                'color': color,
                'name': component.Name or f'{comp_type}_{index}',
                'id': component.GlobalId,
                'metadata': {
                    'type': comp_type,
                    'diameter': diameter,
                    'outer_diameter': washer_od,
                    'thickness': washer_thickness
                }
            }
        elif comp_type == 'NUT':
            # Create hexagonal nut
            nut_height = spec.get('nut_height', 10)
            # Standard ratio for hex nuts: across flats = nominal diameter * 1.5
            across_flats = diameter * 1.5  # This is the distance between opposite flats
            # Calculate the distance from center to a corner of the hexagon
            across_corners = across_flats / math.cos(math.pi/6)  # approximately across_flats * 1.1547
            
            vertices = []
            indices = []

            # Get the placement of the component to determine position
            placement = component.ObjectPlacement
            if placement and hasattr(placement, 'Location'):
                loc = placement.Location.Coordinates
                pos_x, pos_y, pos_z = loc[0], loc[1], loc[2]
            else:
                pos_x, pos_y, pos_z = 0.0, 0.0, 0.0

            # Create hexagon vertices (top and bottom)
            for height_offset in [-nut_height/2, nut_height/2]:  # Bottom and top
                for i in range(6):  # 6 corners of hexagon
                    angle = i * math.pi / 3  # 60 degrees in radians
                    x = pos_x + (across_corners / 2) * math.cos(angle)
                    y = pos_y + (across_corners / 2) * math.sin(angle)
                    z = pos_z + height_offset
                    vertices.extend([x, y, z])

            # Create indices for top and bottom faces
            # Bottom face (first 6 vertices)
            for i in range(6):
                next_i = (i + 1) % 6
                indices.extend([0, next_i, i])  # Fan triangulation for center point

            # Top face (next 6 vertices)
            for i in range(6):
                next_i = (i + 1) % 6
                indices.extend([6, 6 + i, 6 + next_i])  # Fan triangulation for center point

            # Side faces (connecting top and bottom hexagons)
            for i in range(6):
                next_i = (i + 1) % 6
                # Two triangles for each side face
                indices.extend([i, next_i, 6 + next_i])
                indices.extend([i, 6 + next_i, 6 + i])

            return {
                'vertices': vertices,
                'indices': indices,
                'color': color,
                'name': component.Name or f'{comp_type}_{index}',
                'id': component.GlobalId,
                'metadata': {
                    'type': comp_type,
                    'diameter': diameter,
                    'height': nut_height,
                    'across_flats': across_flats
                }
            }
        else:
            # Default fallback - small cube at component's location
            # Get the placement of the component to determine position
            placement = component.ObjectPlacement
            if placement and hasattr(placement, 'Location'):
                loc = placement.Location.Coordinates
                pos_x, pos_y, pos_z = loc[0], loc[1], loc[2]
            else:
                pos_x, pos_y, pos_z = 0.0, 0.0, 0.0

            # Small cube of 10mm size centered at the component's location
            size = 10.0
            vertices = [
                [pos_x - size/2, pos_y - size/2, pos_z - size/2],  # 0: front bottom left
                [pos_x + size/2, pos_y - size/2, pos_z - size/2],  # 1: front bottom right
                [pos_x + size/2, pos_y + size/2, pos_z - size/2],  # 2: front top right
                [pos_x - size/2, pos_y + size/2, pos_z - size/2],  # 3: front top left
                [pos_x - size/2, pos_y - size/2, pos_z + size/2],  # 4: back bottom left
                [pos_x + size/2, pos_y - size/2, pos_z + size/2],  # 5: back bottom right
                [pos_x + size/2, pos_y + size/2, pos_z + size/2], # 6: back top right
                [pos_x - size/2, pos_y + size/2, pos_z + size/2]  # 7: back top left
            ]
            indices = [
                0, 1, 2, 0, 2, 3,  # Front
                4, 7, 6, 4, 6, 5,  # Back
                0, 4, 5, 0, 5, 1,  # Bottom
                2, 6, 7, 2, 7, 3,  # Top
                0, 3, 7, 0, 7, 4,  # Left
                1, 5, 6, 1, 6, 2   # Right
            ]
            
            return {
                'vertices': [v for vertex in vertices for v in vertex],
                'indices': indices,
                'color': color,
                'name': component.Name or f'{comp_type}_{index}',
                'id': component.GlobalId,
                'metadata': {'type': comp_type}
            }

    def _create_placement(self, location=(0, 0, 0)):
        """Create 3D placement as IfcLocalPlacement"""
        # Convert location to list of floats
        location_list = [float(x) for x in location]
        location_point = self.ifc.create_entity('IfcCartesianPoint', Coordinates=location_list)
        # For bolt oriented along Z-axis from bottom to top (so top is closer to origin),
        # the axis should point in positive Z direction
        axis = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        ref_dir = self.ifc.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0])

        # Create the relative placement as IfcAxis2Placement3D
        relative_placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                                   Location=location_point,
                                                   Axis=axis,
                                                   RefDirection=ref_dir)

        # Create the local placement with the relative placement
        # For the parent placement, we'll use the global coordinate system (None)
        return self.ifc.create_entity('IfcLocalPlacement',
                                     PlacementRelTo=None,  # Reference to parent placement (None for global)
                                     RelativePlacement=relative_placement)

    def _generate_guid(self):
        """Generate IFC GUID using ifcopenshell"""
        import ifcopenshell
        return ifcopenshell.guid.new()


def generate_bolt_assembly(params):
    """
    Main entry point for bolt generation
    Called from JavaScript via Pyodide

    Args:
        params: dict with bolt parameters

    Returns:
        tuple: (ifc_string, mesh_data_dict)
    """
    from main import initialize_base_document
    
    # Create a new document for this specific bolt
    temp_doc = initialize_base_document()

    factory = InstanceFactory(temp_doc)

    result = factory.create_bolt_assembly(
        bolt_type=params.get('bolt_type'),
        execution=params.get('execution', 1),
        diameter=params.get('diameter'),
        length=params.get('length'),
        material=params.get('material'),
        has_bottom_nut=params.get('has_bottom_nut', False),
        has_top_nut1=params.get('has_top_nut1', False),
        has_top_nut2=params.get('has_top_nut2', False),
        has_washers=params.get('has_washers', False)
    )

    # Export IFC as string
    # Write to temporary file in Pyodide's virtual filesystem, then read back as string
    temp_path = '/tmp/temp_bolt.ifc'
    temp_doc.write(temp_path)

    with open(temp_path, 'r') as f:
        ifc_string = f.read()

    return (ifc_string, result['mesh_data'])
