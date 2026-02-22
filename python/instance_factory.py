"""
instance_factory.py — Создание инстансов болтов и сборок
"""

import numpy as np
from type_factory import TypeFactory
from gost_data import validate_parameters, get_bolt_spec


def _get_ifcopenshell():
    """Ленивый импорт ifcopenshell"""
    from main import _get_ifcopenshell as get_ifc
    return get_ifc()


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(self, ifc_doc, type_factory=None):
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)

    def create_bolt_assembly(self, bolt_type, execution, diameter, length, material,
                            has_bottom_nut=False, has_top_nut1=False,
                            has_top_nut2=False, has_washers=False):
        """
        Создание полной сборки анкерного болта

        Returns:
            dict с assembly, stud, components и mesh_data
        """
        ifcopenshell = _get_ifcopenshell()
        
        # Валидация параметров
        validate_parameters(bolt_type, execution, diameter, length, material)
        spec = get_bolt_spec(diameter)

        # Получение типов
        stud_type = self.type_factory.get_or_create_stud_type(
            bolt_type, execution, diameter, length, material
        )
        nut_type = self.type_factory.get_or_create_nut_type(diameter, material)
        washer_type = self.type_factory.get_or_create_washer_type(diameter, material)
        assembly_type = self.type_factory.get_or_create_assembly_type(
            bolt_type, diameter, material
        )

        # Получение storey для размещения
        storeys = self.ifc.by_type('IfcBuildingStorey')
        storey = storeys[0] if storeys else None

        # Создание assembly
        assembly = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifcopenshell.guid.new(),
            Name=f'AnchorBolt_{bolt_type}_M{diameter}x{length}',
            ObjectType='ANCHORBOLT',
            PredefinedType='ANCHORBOLT'
        )
        self._add_instance_representation(assembly, assembly_type)

        # Компоненты
        components = []
        stud_instances = []
        nut_instances = []
        washer_instances = []

        # Шпилька
        stud_placement = self._create_placement((0, 0, 0))
        stud = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifcopenshell.guid.new(),
            Name=f'Stud_M{diameter}x{length}',
            ObjectType='STUD',
            ObjectPlacement=stud_placement
        )
        self._add_instance_representation(stud, stud_type)
        stud_instances.append(stud)
        components.append(stud)

        # Размеры компонентов
        washer_thickness = spec.get('washer_thickness', 3)
        nut_height = spec.get('nut_height', 10)

        # Верхняя шайба (для всех типов)
        if has_washers:
            washer_top = self._create_component(
                'Washer', f'Washer_Top_M{diameter}', 'WASHER',
                (0, 0, washer_thickness / 2),
                washer_type, washer_instances
            )
            components.append(washer_top)

        # Верхняя гайка 1
        if has_top_nut1:
            z_pos = washer_thickness / 2 if has_washers else 0
            nut_top1 = self._create_component(
                'Nut', f'Nut_Top1_M{diameter}', 'NUT',
                (0, 0, z_pos + nut_height / 2),
                nut_type, nut_instances
            )
            components.append(nut_top1)

        # Верхняя гайка 2
        if has_top_nut2:
            z_pos = (washer_thickness + nut_height) if has_washers and has_top_nut1 else \
                    (washer_thickness / 2 + nut_height) if has_washers else nut_height
            nut_top2 = self._create_component(
                'Nut', f'Nut_Top2_M{diameter}', 'NUT',
                (0, 0, z_pos + nut_height / 2),
                nut_type, nut_instances
            )
            components.append(nut_top2)

        # Нижняя шайба (только для типа 2.x)
        if has_washers and bolt_type.startswith('2.'):
            washer_bottom = self._create_component(
                'Washer', f'Washer_Bottom_M{diameter}', 'WASHER',
                (0, 0, length - washer_thickness / 2),
                washer_type, washer_instances
            )
            components.append(washer_bottom)

        # Нижняя гайка (только для типа 2.x)
        if has_bottom_nut and bolt_type.startswith('2.'):
            z_pos = length + washer_thickness / 2 if has_washers else length
            nut_bottom = self._create_component(
                'Nut', f'Nut_Bottom_M{diameter}', 'NUT',
                (0, 0, z_pos + nut_height / 2),
                nut_type, nut_instances
            )
            components.append(nut_bottom)

        # IfcRelDefinesByType для каждого типа
        self.ifc.create_entity('IfcRelDefinesByType',
            GlobalId=ifcopenshell.guid.new(),
            RelatingType=assembly_type,
            RelatedObjects=[assembly]
        )
        if stud_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifcopenshell.guid.new(),
                RelatingType=stud_type,
                RelatedObjects=stud_instances
            )
        if nut_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifcopenshell.guid.new(),
                RelatingType=nut_type,
                RelatedObjects=nut_instances
            )
        if washer_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifcopenshell.guid.new(),
                RelatingType=washer_type,
                RelatedObjects=washer_instances
            )

        # IfcRelContainedInSpatialStructure
        if storey:
            self.ifc.create_entity('IfcRelContainedInSpatialStructure',
                GlobalId=ifcopenshell.guid.new(),
                RelatingStructure=storey,
                RelatedElements=[assembly] + components
            )

        # IfcRelAggregates
        self.ifc.create_entity('IfcRelAggregates',
            GlobalId=ifcopenshell.guid.new(),
            RelatingObject=assembly,
            RelatedObjects=components
        )

        # IfcRelConnectsElements между компонентами
        for i in range(len(components) - 1):
            self.ifc.create_entity('IfcRelConnectsElements',
                GlobalId=ifcopenshell.guid.new(),
                RelatingElement=components[i],
                RelatedElement=components[i + 1]
            )

        # Mesh data для 3D визуализации
        mesh_data = self._generate_mesh_data(
            components, bolt_type, diameter, length, material,
            has_bottom_nut, has_top_nut1, has_top_nut2, has_washers
        )

        return {
            'assembly': assembly,
            'stud': stud,
            'components': components,
            'mesh_data': mesh_data
        }

    def _create_placement(self, location):
        """Создание 3D размещения"""
        coords = [float(x) for x in location]
        return self.ifc.create_entity('IfcLocalPlacement',
            PlacementRelTo=None,
            RelativePlacement=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=coords),
                Axis=self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0]),
                RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0])
            )
        )

    def _create_component(self, comp_type, name, object_type, location, type_obj, instances_list):
        """Создание компонента (гайка/шайба)"""
        ifcopenshell = _get_ifcopenshell()
        placement = self._create_placement(location)
        component = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifcopenshell.guid.new(),
            Name=name,
            ObjectType=object_type,
            ObjectPlacement=placement
        )
        self._add_instance_representation(component, type_obj)
        instances_list.append(component)
        return component

    def _add_instance_representation(self, instance, type_obj):
        """Добавление представления к инстансу через RepresentationMap типа"""
        if not hasattr(type_obj, 'RepresentationMaps') or not type_obj.RepresentationMaps:
            return

        rep_maps = type_obj.RepresentationMaps
        if not isinstance(rep_maps, (list, tuple)):
            rep_maps = [rep_maps]

        for rep_map in rep_maps:
            if not hasattr(rep_map, 'MappedRepresentation'):
                continue

            mapped_rep = rep_map.MappedRepresentation
            context = mapped_rep.ContextOfItems
            identifier = mapped_rep.RepresentationIdentifier
            rep_type = mapped_rep.RepresentationType
            items = mapped_rep.Items

            try:
                duplicated_items = self._duplicate_geometric_items(items)
                instance_shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
                    ContextOfItems=context,
                    RepresentationIdentifier=identifier,
                    RepresentationType=rep_type,
                    Items=duplicated_items
                )
                prod_def_shape = self.ifc.create_entity('IfcProductDefinitionShape',
                    Representations=[instance_shape_rep]
                )
                instance.Representation = prod_def_shape
            except Exception as e:
                print(f"Warning: Could not create representation for {instance.Name}: {e}")

    def _duplicate_geometric_items(self, items):
        """Дублирование геометрических элементов"""
        duplicated = []
        for item in items:
            if item.is_a() == 'IfcSweptDiskSolid':
                directrix = self._duplicate_curve(item.Directrix)
                duplicated.append(self.ifc.create_entity('IfcSweptDiskSolid',
                    Directrix=directrix, Radius=item.Radius
                ))
            elif item.is_a() == 'IfcExtrudedAreaSolid':
                swept_area = self._duplicate_profile(item.SweptArea)
                position = self._duplicate_placement(item.Position)
                direction = self._duplicate_direction(item.ExtrudedDirection)
                duplicated.append(self.ifc.create_entity('IfcExtrudedAreaSolid',
                    SweptArea=swept_area, Position=position,
                    ExtrudedDirection=direction, Depth=item.Depth
                ))
            else:
                duplicated.append(item)
        return duplicated

    def _duplicate_curve(self, curve):
        """Дублирование кривой"""
        if curve.is_a() == 'IfcCompositeCurve':
            segments = [self._duplicate_curve_segment(s) for s in curve.Segments]
            return self.ifc.create_entity('IfcCompositeCurve',
                Segments=segments, SelfIntersect=curve.SelfIntersect
            )
        elif curve.is_a() == 'IfcPolyline':
            points = [self.ifc.create_entity('IfcCartesianPoint', Coordinates=p.Coordinates)
                     for p in curve.Points]
            return self.ifc.create_entity('IfcPolyline', Points=points)
        return curve

    def _duplicate_curve_segment(self, segment):
        """Дублирование сегмента кривой"""
        return self.ifc.create_entity('IfcCompositeCurveSegment',
            Transition=segment.Transition,
            SameSense=segment.SameSense,
            ParentCurve=self._duplicate_curve(segment.ParentCurve)
        )

    def _duplicate_placement(self, placement):
        """Дублирование размещения"""
        if placement.is_a() == 'IfcAxis2Placement3D':
            return self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint',
                    Coordinates=placement.Location.Coordinates
                ),
                Axis=self._duplicate_direction(placement.Axis) if placement.Axis else None,
                RefDirection=self._duplicate_direction(placement.RefDirection) if placement.RefDirection else None
            )
        return placement

    def _duplicate_direction(self, direction):
        """Дублирование направления"""
        return self.ifc.create_entity('IfcDirection',
            DirectionRatios=direction.DirectionRatios
        )

    def _duplicate_profile(self, profile):
        """Дублирование профиля"""
        return profile  # Упрощённо возвращаем оригинал

    def _generate_mesh_data(self, components, bolt_type, diameter, length, material,
                           has_bottom_nut, has_top_nut1, has_top_nut2, has_washers):
        """Генерация mesh данных для Three.js"""
        meshes = []
        color_map = {
            'STUD': 0x8B8B8B,
            'WASHER': 0xA9A9A9,
            'NUT': 0x696969,
            'ANCHORBOLT': 0x4F4F4F
        }

        for i, component in enumerate(components):
            mesh = self._create_fallback_mesh(
                component, i, diameter, length, color_map,
                bolt_type, has_bottom_nut, has_top_nut1, has_top_nut2, has_washers
            )
            if mesh:
                meshes.append(mesh)

        return {'meshes': meshes}

    def _create_fallback_mesh(self, component, index, diameter, length, color_map,
                             bolt_type, has_bottom_nut, has_top_nut1, has_top_nut2, has_washers):
        """Создание упрощённого mesh для визуализации"""
        comp_type = component.ObjectType or 'UNKNOWN'
        color = color_map.get(comp_type, 0xCCCCCC)
        spec = get_bolt_spec(diameter)

        # Получение позиции из placement
        placement = component.ObjectPlacement
        position = [0, 0, 0]
        if placement and hasattr(placement, 'RelativePlacement'):
            loc = placement.RelativePlacement.Location
            if loc:
                position = list(loc.Coordinates)

        if comp_type == 'STUD':
            return self._create_stud_mesh(diameter, length, bolt_type, color, index, component)
        elif comp_type == 'NUT':
            return self._create_nut_mesh(diameter, spec, color, index, position, component)
        elif comp_type == 'WASHER':
            return self._create_washer_mesh(diameter, spec, color, index, position, component)

        return None

    def _create_stud_mesh(self, diameter, length, bolt_type, color, index, component):
        """Mesh шпильки"""
        has_bend = bolt_type in ['1.1', '1.2']
        radius = diameter * (1.5 if bolt_type == '1.1' else 2.0) if has_bend else 0

        vertices = []
        indices = []

        if has_bend:
            # Bent stud: вертикальная часть + дуга + горизонтальная часть
            segments = 32
            upper_length = length - 2 * radius

            # Верхняя вертикальная часть
            for i in range(segments // 2):
                angle = (2 * np.pi * i) / (segments // 2)
                x = (diameter / 2) * np.cos(angle)
                y = (diameter / 2) * np.sin(angle)
                vertices.extend([x, y, upper_length])
                vertices.extend([x, y, length])

            # Дуга
            for i in range(segments // 4 + 1):
                angle = np.pi / 2 + (np.pi / 2) * (i / (segments // 4))
                cx = radius
                cz = length - 2 * radius
                x = cx + radius * np.cos(angle)
                z = cz + radius * np.sin(angle)
                for j in range(2):
                    rad = (diameter / 2) * (0.5 + 0.5 * np.sin(angle - np.pi / 2))
                    theta = (2 * np.pi * j) / 2
                    vertices.extend([
                        x + rad * np.cos(theta),
                        rad * np.sin(theta),
                        z
                    ])

            # Горизонтальная часть
            for i in range(segments // 2):
                angle = (2 * np.pi * i) / (segments // 2)
                x = radius + (diameter / 2) * np.cos(angle)
                y = (diameter / 2) * np.sin(angle)
                vertices.extend([x, y, 0])
                vertices.extend([x, y, radius])
        else:
            # Straight stud: цилиндр
            segments = 32
            for i in range(segments):
                angle = (2 * np.pi * i) / segments
                x = (diameter / 2) * np.cos(angle)
                y = (diameter / 2) * np.sin(angle)
                vertices.extend([x, y, 0])
                vertices.extend([x, y, length])

        # Индексы
        for i in range(0, len(vertices) // 3 - 2, 2):
            indices.extend([i, i + 1, i + 2])
            indices.extend([i + 1, i + 3, i + 2])

        return {
            'id': getattr(component, 'id', f'mesh_{index}'),
            'name': getattr(component, 'Name', f'Component_{index}'),
            'vertices': vertices,
            'indices': indices,
            'color': color,
            'metadata': {
                'Type': 'STUD',
                'Diameter': diameter,
                'Length': length,
                'BoltType': bolt_type
            }
        }

    def _create_nut_mesh(self, diameter, spec, color, index, position, component):
        """Mesh гайки (шестиугольник)"""
        height = spec.get('nut_height', 10)
        outer_radius = diameter * 0.75
        inner_radius = diameter / 2 + 0.5
        z_offset = position[2]

        vertices = []
        indices = []

        # Шестиугольник
        for i in range(6):
            angle = (2 * np.pi * i) / 6
            x = outer_radius * np.cos(angle)
            y = outer_radius * np.sin(angle)
            vertices.extend([x, y, z_offset])
            vertices.extend([x, y, z_offset + height])

        # Индексы для сторон
        for i in range(6):
            next_i = (i + 1) % 6
            indices.extend([i * 2, i * 2 + 1, next_i * 2])
            indices.extend([i * 2 + 1, next_i * 2 + 1, next_i * 2])

        # Верхняя и нижняя грани
        center_top = len(vertices) // 3
        vertices.extend([0, 0, z_offset + height])
        center_bottom = len(vertices) // 3
        vertices.extend([0, 0, z_offset])

        for i in range(6):
            next_i = (i + 1) % 6
            indices.extend([center_top, i * 2 + 1, next_i * 2 + 1])
            indices.extend([center_bottom, next_i * 2, i * 2])

        return {
            'id': getattr(component, 'id', f'mesh_{index}'),
            'name': getattr(component, 'Name', f'Nut_{index}'),
            'vertices': vertices,
            'indices': indices,
            'color': color,
            'metadata': {
                'Type': 'NUT',
                'Diameter': diameter,
                'Height': height
            }
        }

    def _create_washer_mesh(self, diameter, spec, color, index, position, component):
        """Mesh шайбы (кольцо)"""
        thickness = spec.get('washer_thickness', 3)
        outer_radius = spec.get('washer_outer_diameter', diameter + 10) / 2
        z_offset = position[2]

        vertices = []
        indices = []
        segments = 32

        # Внешнее и внутреннее кольцо
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            x_outer = outer_radius * np.cos(angle)
            y_outer = outer_radius * np.sin(angle)
            vertices.extend([x_outer, y_outer, z_offset])
            vertices.extend([x_outer, y_outer, z_offset + thickness])

        # Индексы
        for i in range(segments - 1):
            indices.extend([i * 2, i * 2 + 1, (i + 1) * 2])
            indices.extend([i * 2 + 1, (i + 1) * 2 + 1, (i + 1) * 2])

        return {
            'id': getattr(component, 'id', f'mesh_{index}'),
            'name': getattr(component, 'Name', f'Washer_{index}'),
            'vertices': vertices,
            'indices': indices,
            'color': color,
            'metadata': {
                'Type': 'WASHER',
                'Diameter': diameter,
                'OuterDiameter': outer_radius * 2,
                'Thickness': thickness
            }
        }


def generate_bolt_assembly(params):
    """
    Главная функция для генерации болта
    Args:
        params: dict с параметрами болта
    Returns:
        (ifc_string, mesh_data)
    """
    from main import get_ifc_document
    import io
    
    ifc_doc = get_ifc_document()

    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(
        bolt_type=params['bolt_type'],
        execution=params['execution'],
        diameter=params['diameter'],
        length=params['length'],
        material=params['material'],
        has_bottom_nut=params.get('has_bottom_nut', False),
        has_top_nut1=params.get('has_top_nut1', False),
        has_top_nut2=params.get('has_top_nut2', False),
        has_washers=params.get('has_washers', False)
    )

    # Экспорт в строку через временный файл
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        temp_path = f.name
    
    ifc_doc.write(temp_path)
    
    with open(temp_path, 'r') as f:
        ifc_str = f.read()
    
    import os
    os.unlink(temp_path)
    
    return (ifc_str, result['mesh_data'])


def get_element_properties(element_id):
    """Получение свойств элемента по ID"""
    from main import get_ifc_document
    ifc_doc = get_ifc_document()

    entities = ifc_doc.by_id(element_id)
    if entities:
        entity = entities[0]
        return {
            'id': entity.id(),
            'name': getattr(entity, 'Name', 'Unknown'),
            'type': entity.is_a(),
            'object_type': getattr(entity, 'ObjectType', None)
        }
    return {}
