"""
instance_factory.py - Создание инстансов болтов и управление их размещением
"""

from type_factory import TypeFactory
from gost_data import validate_parameters, get_bolt_spec
import math


class InstanceFactory:
    """Фабрика для создания инстансов болтов и компонентов"""

    def __init__(self, ifc_doc, type_factory=None):
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)
        self.instances = []

    def create_bolt_assembly(self, bolt_type, execution, diameter, length, material,
                            has_bottom_nut=False, has_top_nut=False, has_washers=False):
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

        # Define assembly by type
        self.ifc.create_entity('IfcRelDefinesByType',
                              GlobalId=self._generate_guid(),
                              RelatingType=assembly_type,
                              RelatedObjects=[assembly])

        # Create instances for components
        components = []
        z_position = 0

        # Stud instance
        stud_placement = self._create_placement((0, 0, z_position))
        stud = self.ifc.create_entity('IfcMechanicalFastener',
                                     GlobalId=self._generate_guid(),
                                     Name=f'Stud_M{diameter}x{length}',
                                     ObjectType='STUD',
                                     Placement=stud_placement)

        self.ifc.create_entity('IfcRelDefinesByType',
                              GlobalId=self._generate_guid(),
                              RelatingType=stud_type,
                              RelatedObjects=[stud])

        components.append(stud)

        # Calculate positions for nuts and washers
        washer_thickness = spec.get('washer_thickness', 3)
        nut_height = spec.get('nut_height', 10)

        component_instances = [stud]

        # Bottom washer (optional)
        if has_washers:
            z_pos = 0
            washer_bottom_placement = self._create_placement((0, 0, z_pos))
            washer_bottom = self.ifc.create_entity('IfcMechanicalFastener',
                                                  GlobalId=self._generate_guid(),
                                                  Name=f'Washer_Bottom_M{diameter}',
                                                  ObjectType='WASHER',
                                                  Placement=washer_bottom_placement)

            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=washer_type,
                                  RelatedObjects=[washer_bottom])

            component_instances.append(washer_bottom)

            z_position += washer_thickness

        # Bottom nut (optional)
        if has_bottom_nut:
            nut_bottom_placement = self._create_placement((0, 0, z_position))
            nut_bottom = self.ifc.create_entity('IfcMechanicalFastener',
                                               GlobalId=self._generate_guid(),
                                               Name=f'Nut_Bottom_M{diameter}',
                                               ObjectType='NUT',
                                               Placement=nut_bottom_placement)

            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=nut_type,
                                  RelatedObjects=[nut_bottom])

            component_instances.append(nut_bottom)

            z_position += nut_height

        # Top side positions (from top down)
        z_top = length

        # Top washer
        if has_washers:
            z_pos = z_top - washer_thickness
            washer_top_placement = self._create_placement((0, 0, z_pos))
            washer_top = self.ifc.create_entity('IfcMechanicalFastener',
                                               GlobalId=self._generate_guid(),
                                               Name=f'Washer_Top_M{diameter}',
                                               ObjectType='WASHER',
                                               Placement=washer_top_placement)

            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=washer_type,
                                  RelatedObjects=[washer_top])

            component_instances.append(washer_top)

            z_top -= washer_thickness

        # Top nut
        if has_top_nut:
            nut_top_placement = self._create_placement((0, 0, z_top - nut_height))
            nut_top = self.ifc.create_entity('IfcMechanicalFastener',
                                            GlobalId=self._generate_guid(),
                                            Name=f'Nut_Top_M{diameter}',
                                            ObjectType='NUT',
                                            Placement=nut_top_placement)

            self.ifc.create_entity('IfcRelDefinesByType',
                                  GlobalId=self._generate_guid(),
                                  RelatingType=nut_type,
                                  RelatedObjects=[nut_top])

            component_instances.append(nut_top)

        # Create aggregation relationship (assembly contains components)
        if storey:
            self.ifc.create_entity('IfcRelAggregates',
                                  GlobalId=self._generate_guid(),
                                  RelatingObject=storey,
                                  RelatedObjects=[assembly])

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

        # Generate mesh data for 3D visualization
        mesh_data = self._generate_mesh_data(
            bolt_type, diameter, length, material,
            has_bottom_nut, has_top_nut, has_washers
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

    def _generate_mesh_data(self, bolt_type, diameter, length, material,
                           has_bottom_nut, has_top_nut, has_washers):
        """Generate simplified mesh data for 3D visualization"""
        meshes = []

        # Stud (cylinder)
        stud_mesh = self._create_cylinder_mesh(
            radius=diameter / 2,
            height=length,
            position=(0, 0, length / 2),
            color=0x8B8B8B,  # Gray
            name='Stud',
            id='stud_0'
        )
        meshes.append(stud_mesh)

        # Washers and nuts
        z_pos = 0
        spec = get_bolt_spec(diameter)
        washer_thickness = spec.get('washer_thickness', 3)
        washer_od = spec.get('washer_outer_diameter', diameter + 10)
        nut_height = spec.get('nut_height', 10)

        # Bottom washer
        if has_washers:
            washer_mesh = self._create_ring_mesh(
                outer_radius=washer_od / 2,
                inner_radius=diameter / 2 + 0.5,
                height=washer_thickness,
                position=(0, 0, z_pos + washer_thickness / 2),
                color=0xA9A9A9,  # Dark gray
                name='Washer_Bottom',
                id='washer_bottom_0'
            )
            meshes.append(washer_mesh)
            z_pos += washer_thickness

        # Bottom nut
        if has_bottom_nut:
            nut_mesh = self._create_hex_mesh(
                diameter=diameter * 1.5,
                height=nut_height,
                position=(0, 0, z_pos + nut_height / 2),
                color=0x696969,  # Dim gray
                name='Nut_Bottom',
                id='nut_bottom_0'
            )
            meshes.append(nut_mesh)

        # Top components
        z_top = length

        if has_washers:
            washer_mesh = self._create_ring_mesh(
                outer_radius=washer_od / 2,
                inner_radius=diameter / 2 + 0.5,
                height=washer_thickness,
                position=(0, 0, z_top - washer_thickness / 2),
                color=0xA9A9A9,
                name='Washer_Top',
                id='washer_top_0'
            )
            meshes.append(washer_mesh)
            z_top -= washer_thickness

        if has_top_nut:
            nut_mesh = self._create_hex_mesh(
                diameter=diameter * 1.5,
                height=nut_height,
                position=(0, 0, z_top - nut_height / 2),
                color=0x696969,
                name='Nut_Top',
                id='nut_top_0'
            )
            meshes.append(nut_mesh)

        return {'meshes': meshes}

    def _create_cylinder_mesh(self, radius, height, position, color, name, id):
        """Create simplified cylinder mesh"""
        segments = 16
        vertices = []
        indices = []

        # Top and bottom centers
        vertices.append(list(position))  # 0: bottom center
        vertices.append([position[0], position[1], position[2] + height])  # 1: top center

        # Bottom circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + radius * math.cos(angle)
            y = position[1] + radius * math.sin(angle)
            vertices.append([x, y, position[2]])

        # Top circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + radius * math.cos(angle)
            y = position[1] + radius * math.sin(angle)
            vertices.append([x, y, position[2] + height])

        # Bottom triangles
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([0, 2 + i, 2 + next_i])

        # Top triangles
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([1, 2 + segments + next_i, 2 + segments + i])

        # Side triangles
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([2 + i, 2 + segments + i, 2 + next_i])
            indices.extend([2 + next_i, 2 + segments + i, 2 + segments + next_i])

        return {
            'vertices': [v for vertex in vertices for v in vertex],
            'indices': indices,
            'color': color,
            'name': name,
            'id': id,
            'metadata': {}
        }

    def _create_ring_mesh(self, outer_radius, inner_radius, height, position, color, name, id):
        """Create ring/washer mesh"""
        segments = 16
        vertices = []
        indices = []

        # Bottom outer circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + outer_radius * math.cos(angle)
            y = position[1] + outer_radius * math.sin(angle)
            vertices.append([x, y, position[2] - height / 2])

        # Bottom inner circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + inner_radius * math.cos(angle)
            y = position[1] + inner_radius * math.sin(angle)
            vertices.append([x, y, position[2] - height / 2])

        # Top outer circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + outer_radius * math.cos(angle)
            y = position[1] + outer_radius * math.sin(angle)
            vertices.append([x, y, position[2] + height / 2])

        # Top inner circle
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = position[0] + inner_radius * math.cos(angle)
            y = position[1] + inner_radius * math.sin(angle)
            vertices.append([x, y, position[2] + height / 2])

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
            'name': name,
            'id': id,
            'metadata': {}
        }

    def _create_hex_mesh(self, diameter, height, position, color, name, id):
        """Create hexagonal nut mesh"""
        vertices = []
        indices = []

        # Hexagon vertices
        hex_vertices = []
        for i in range(6):
            angle = (i * 60) * math.pi / 180
            x = position[0] + (diameter / 2) * math.cos(angle)
            y = position[1] + (diameter / 2) * math.sin(angle)
            hex_vertices.append((x, y))

        # Bottom hexagon
        for x, y in hex_vertices:
            vertices.append([x, y, position[2] - height / 2])

        # Top hexagon
        for x, y in hex_vertices:
            vertices.append([x, y, position[2] + height / 2])

        # Bottom triangles
        for i in range(6):
            next_i = (i + 1) % 6
            indices.extend([i, next_i, 6])  # Simple fan triangulation

        # Top triangles
        for i in range(6):
            next_i = (i + 1) % 6
            indices.extend([6 + i, 12, 6 + next_i])

        # Side quads as triangles
        for i in range(6):
            next_i = (i + 1) % 6
            indices.extend([i, 6 + i, 6 + next_i])
            indices.extend([i, 6 + next_i, next_i])

        return {
            'vertices': [v for vertex in vertices for v in vertex],
            'indices': indices,
            'color': color,
            'name': name,
            'id': id,
            'metadata': {}
        }

    def _create_placement(self, location=(0, 0, 0)):
        """Create 3D placement"""
        location_point = self.ifc.create_entity('IfcCartesianPoint', Coordinates=location)
        axis = self.ifc.create_entity('IfcDirection', DirectionRatios=(0, 0, 1))
        ref_dir = self.ifc.create_entity('IfcDirection', DirectionRatios=(1, 0, 0))

        return self.ifc.create_entity('IfcAxis2Placement3D',
                                     Location=location_point,
                                     Axis=axis,
                                     RefDirection=ref_dir)

    def _generate_guid(self):
        """Generate IFC GUID"""
        import uuid
        import base64
        uuid_bytes = uuid.uuid4().bytes
        return base64.b64encode(uuid_bytes).decode()[:22]


def generate_bolt_assembly(params):
    """
    Main entry point for bolt generation
    Called from JavaScript via Pyodide

    Args:
        params: dict with bolt parameters

    Returns:
        tuple: (ifc_string, mesh_data_dict)
    """
    from main import get_ifc_document

    ifc_doc = get_ifc_document()

    if not ifc_doc:
        raise RuntimeError("IFC document not initialized")

    factory = InstanceFactory(ifc_doc)

    result = factory.create_bolt_assembly(
        bolt_type=params.get('bolt_type'),
        execution=params.get('execution', 1),
        diameter=params.get('diameter'),
        length=params.get('length'),
        material=params.get('material'),
        has_bottom_nut=params.get('has_bottom_nut', False),
        has_top_nut=params.get('has_top_nut', False),
        has_washers=params.get('has_washers', False)
    )

    # Export IFC as string
    ifc_string = ifc_doc.write()

    return (ifc_string, result['mesh_data'])
