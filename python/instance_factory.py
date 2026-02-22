"""
instance_factory.py — Создание инстансов болтов и сборок
"""

import numpy as np
from type_factory import TypeFactory
from gost_data import validate_parameters, get_nut_dimensions, get_washer_dimensions


def _get_ifcopenshell():
    """Ленивый импорт ifcopenshell"""
    from main import _get_ifcopenshell as get_ifc
    return get_ifc()


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(self, ifc_doc, type_factory=None):
        self.ifc = ifc_doc
        self.type_factory = type_factory or TypeFactory(ifc_doc)

    def create_bolt_assembly(self, bolt_type, execution, diameter, length, material):
        """
        Создание полной сборки анкерного болта
        
        Состав сборки по умолчанию:
        - Типы 1.1, 1.2, 5: шпилька + верхняя шайба + 2 верхних гайки
        - Тип 2.1: шпилька + верхняя шайба + 2 верхних гайки + 2 нижних гайки

        Returns:
            dict с assembly, stud, components и mesh_data
        """
        ifcopenshell = _get_ifcopenshell()

        # Валидация параметров
        validate_parameters(bolt_type, execution, diameter, length, material)
        
        # Получение размеров компонентов
        nut_dim = get_nut_dimensions(diameter)
        washer_dim = get_washer_dimensions(diameter)
        
        nut_height = nut_dim['height'] if nut_dim else 10
        washer_thickness = washer_dim['thickness'] if washer_dim else 3

        # Автоматическое определение состава сборки по типу болта
        has_top_washer = True
        has_top_nut1 = True
        has_top_nut2 = True
        has_bottom_nut = bolt_type == '2.1'
        has_bottom_nut2 = bolt_type == '2.1'

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

        # Верхняя шайба (для всех типов)
        if has_top_washer:
            washer_top = self._create_component(
                'Washer', f'Washer_Top_M{diameter}', 'WASHER',
                (0, 0, washer_thickness / 2),
                washer_type, washer_instances
            )
            components.append(washer_top)

        # Верхняя гайка 1
        if has_top_nut1:
            z_pos = washer_thickness / 2
            nut_top1 = self._create_component(
                'Nut', f'Nut_Top1_M{diameter}', 'NUT',
                (0, 0, z_pos + nut_height / 2),
                nut_type, nut_instances
            )
            components.append(nut_top1)

        # Верхняя гайка 2
        if has_top_nut2:
            z_pos = washer_thickness + nut_height
            nut_top2 = self._create_component(
                'Nut', f'Nut_Top2_M{diameter}', 'NUT',
                (0, 0, z_pos + nut_height / 2),
                nut_type, nut_instances
            )
            components.append(nut_top2)

        # Нижняя гайка 1 (только для типа 2.1)
        if has_bottom_nut:
            z_pos = length - washer_thickness / 2 - nut_height / 2
            nut_bottom = self._create_component(
                'Nut', f'Nut_Bottom1_M{diameter}', 'NUT',
                (0, 0, z_pos),
                nut_type, nut_instances
            )
            components.append(nut_bottom)

        # Нижняя гайка 2 (только для типа 2.1)
        if has_bottom_nut2:
            z_pos = length - washer_thickness / 2 - nut_height * 1.5
            nut_bottom2 = self._create_component(
                'Nut', f'Nut_Bottom2_M{diameter}', 'NUT',
                (0, 0, z_pos),
                nut_type, nut_instances
            )
            components.append(nut_bottom2)

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
            components, bolt_type, diameter, length, material
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

    def _generate_mesh_data(self, components, bolt_type, diameter, length, material):
        """Генерация mesh данных через ifcopenshell.geom"""
        from geometry_converter import convert_assembly_to_meshes
        
        color_map = {
            'STUD': 0x8B8B8B,
            'WASHER': 0xA9A9A9,
            'NUT': 0x696969,
            'ANCHORBOLT': 0x4F4F4F
        }

        # Конвертация IFC геометрии в Three.js mesh
        # Используем только ifcopenshell.geom — fallback отключён
        mesh_data = convert_assembly_to_meshes(self.ifc, components, color_map)

        if not mesh_data or not mesh_data.get('meshes'):
            # Если geom не вернул данные — возвращаем пустой список
            print(f"Warning: ifcopenshell.geom failed to generate mesh data")
            return {'meshes': []}

        return mesh_data
    
    def _generate_fallback_mesh_data(self, components, bolt_type, diameter, length, color_map):
        """Fallback: генерация mesh данных вручную (если ifcopenshell.geom недоступен)"""
        meshes = []
        
        for i, component in enumerate(components):
            mesh = self._create_fallback_mesh(
                component, i, diameter, length, color_map, bolt_type
            )
            if mesh:
                meshes.append(mesh)
        
        return {'meshes': meshes}

    def _create_fallback_mesh(self, component, index, diameter, length, color_map, bolt_type):
        """Создание упрощённого mesh для визуализации"""
        comp_type = component.ObjectType or 'UNKNOWN'
        color = color_map.get(comp_type, 0xCCCCCC)

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
            return self._create_nut_mesh(diameter, None, color, index, position, component)
        elif comp_type == 'WASHER':
            return self._create_washer_mesh(diameter, None, color, index, position, component)

        return None

    def _create_stud_mesh(self, diameter, length, bolt_type, color, index, component):
        """Mesh шпильки (упрощённая версия)"""
        has_bend = bolt_type in ['1.1', '1.2']
        bend_radius = diameter * (1.5 if bolt_type == '1.1' else 2.0)
        radius = diameter / 2.0
        segments = 24

        vertices = []
        indices = []

        if has_bend:
            # Изогнутая шпилька: вертикальная часть + дуга 90° + горизонтальный крюк
            # Вертикальная часть: от z=0 до z=length-bend_radius
            # Дуга: от (0, length-bend_radius) до (bend_radius, length)
            # Горизонтальный крюк: от x=bend_radius до x=0 (возврат назад)
            
            vertical_length = length - bend_radius
            
            # 1. Вертикальная часть (цилиндр вдоль оси Z от 0 до vertical_length)
            vert_base = 0
            for i in range(segments):
                angle = (2 * np.pi * i) / segments
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                vertices.extend([x, y, 0])
                vertices.extend([x, y, vertical_length])

            # Соединяем вертикальную часть
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([vert_base + i * 2, vert_base + next_i * 2, vert_base + i * 2 + 1])
                indices.extend([vert_base + i * 2 + 1, vert_base + next_i * 2, vert_base + next_i * 2 + 1])

            # 2. Дуга 90° (от вертикальной к горизонтальной)
            arc_segments = 12
            arc_base = len(vertices) // 3

            for i in range(arc_segments + 1):
                t = i / arc_segments
                angle = (np.pi / 2) * t  # 0 до 90 градусов

                # Центр дуги в точке (0, 0, vertical_length)
                center_x = 0
                center_z = vertical_length

                # Позиция центра сечения на дуге (движение вверх и вправо)
                arc_x = center_x + bend_radius * np.sin(angle)  # от 0 до bend_radius
                arc_z = center_z + bend_radius * (1 - np.cos(angle))  # от vertical_length до length

                # Сечение (круг) перпендикулярно направлению дуги
                for j in range(segments):
                    theta = (2 * np.pi * j) / segments
                    local_r = radius * np.cos(theta)
                    local_y = radius * np.sin(theta)

                    # Поворот сечения перпендикулярно касательной дуги
                    # Касательная направлена под углом angle к вертикали
                    tan_angle = angle
                    x = arc_x + local_r * np.cos(tan_angle)
                    y = local_y
                    z = arc_z - local_r * np.sin(tan_angle)

                    vertices.extend([x, y, z])

            # Соединяем дугу
            for i in range(arc_segments):
                for j in range(segments):
                    next_i = i + 1
                    next_j = (j + 1) % segments

                    idx = arc_base + i * segments + j
                    idx_next_i = arc_base + next_i * segments + j
                    idx_next_j = arc_base + i * segments + next_j
                    idx_next_both = arc_base + next_i * segments + next_j

                    indices.extend([idx, idx_next_j, idx_next_i])
                    indices.extend([idx_next_j, idx_next_both, idx_next_i])

            # 3. Горизонтальный крюк (цилиндр вдоль оси X от bend_radius до 0)
            hook_base = len(vertices) // 3
            for i in range(segments):
                angle = (2 * np.pi * i) / segments
                y = radius * np.cos(angle)
                z = radius * np.sin(angle)
                vertices.extend([bend_radius, y, length])
                vertices.extend([0, y, length])

            # Соединяем горизонтальную часть
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([hook_base + i * 2, hook_base + next_i * 2, hook_base + i * 2 + 1])
                indices.extend([hook_base + i * 2 + 1, hook_base + next_i * 2, hook_base + next_i * 2 + 1])

            # 4. Торцы
            # Нижний торец вертикальной части (z=0)
            bottom_center = len(vertices) // 3
            vertices.extend([0, 0, 0])
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([bottom_center, vert_base + i * 2, vert_base + next_i * 2])

            # Концевой торец крюка (x=0)
            hook_end_center = len(vertices) // 3
            vertices.extend([0, 0, length])
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([hook_end_center, hook_base + next_i * 2 + 1, hook_base + i * 2 + 1])

        else:
            # Прямая шпилька: цилиндр с торцами
            for i in range(segments):
                angle = (2 * np.pi * i) / segments
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                vertices.extend([x, y, 0])
                vertices.extend([x, y, length])

            # Соединяем цилиндр
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([i * 2, next_i * 2, i * 2 + 1])
                indices.extend([i * 2 + 1, next_i * 2, next_i * 2 + 1])

            # Нижний торец (z=0)
            center_bottom_idx = len(vertices) // 3
            vertices.extend([0, 0, 0])
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([center_bottom_idx, i * 2, next_i * 2])

            # Верхний торец (z=length)
            center_top_idx = len(vertices) // 3
            vertices.extend([0, 0, length])
            for i in range(segments):
                next_i = (i + 1) % segments
                indices.extend([center_top_idx, next_i * 2 + 1, i * 2 + 1])

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
        from gost_data import get_nut_dimensions
        import math

        nut_dim = get_nut_dimensions(diameter)
        height = nut_dim['height'] if nut_dim else 10
        s_width = nut_dim['s_width'] if nut_dim else diameter * 1.5

        # Размер под ключ (S) — расстояние между параллельными гранями
        # Радиус описанной окружности (до вершин): R = S / √3
        outer_radius = s_width / math.sqrt(3)
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
        """Mesh шайбы (кольцо с торцами)"""
        from gost_data import get_washer_dimensions
        
        washer_dim = get_washer_dimensions(diameter)
        thickness = washer_dim['thickness'] if washer_dim else 3
        outer_radius = washer_dim['outer_diameter'] / 2 if washer_dim else (diameter + 10) / 2
        inner_radius = washer_dim['inner_diameter'] / 2 if washer_dim else (diameter + 2) / 2
        z_offset = position[2]

        vertices = []
        indices = []
        segments = 32

        # Внешний цилиндр
        outer_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            x = outer_radius * np.cos(angle)
            y = outer_radius * np.sin(angle)
            vertices.extend([x, y, z_offset])
            vertices.extend([x, y, z_offset + thickness])

        # Соединяем внешний цилиндр
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([outer_base + i * 2, outer_base + i * 2 + 1, outer_base + next_i * 2])
            indices.extend([outer_base + i * 2 + 1, outer_base + next_i * 2 + 1, outer_base + next_i * 2])

        # Внутренний цилиндр (отверстие)
        inner_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            x = inner_radius * np.cos(angle)
            y = inner_radius * np.sin(angle)
            vertices.extend([x, y, z_offset])
            vertices.extend([x, y, z_offset + thickness])

        # Соединяем внутренний цилиндр (обратная нормаль)
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([inner_base + i * 2, inner_base + next_i * 2 + 1, inner_base + next_i * 2])
            indices.extend([inner_base + i * 2, inner_base + i * 2 + 1, inner_base + next_i * 2 + 1])

        # Нижний торец (кольцо)
        bottom_outer_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            vertices.extend([outer_radius * np.cos(angle), outer_radius * np.sin(angle), z_offset])
        
        bottom_inner_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            vertices.extend([inner_radius * np.cos(angle), inner_radius * np.sin(angle), z_offset])

        # Соединяем нижний торец
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([bottom_outer_base + i, bottom_inner_base + i, bottom_outer_base + next_i])
            indices.extend([bottom_outer_base + next_i, bottom_inner_base + i, bottom_inner_base + next_i])

        # Верхний торец (кольцо)
        top_outer_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            vertices.extend([outer_radius * np.cos(angle), outer_radius * np.sin(angle), z_offset + thickness])
        
        top_inner_base = len(vertices) // 3
        for i in range(segments):
            angle = (2 * np.pi * i) / segments
            vertices.extend([inner_radius * np.cos(angle), inner_radius * np.sin(angle), z_offset + thickness])

        # Соединяем верхний торец (обратная нормаль)
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.extend([top_outer_base + i, top_outer_base + next_i, top_inner_base + i])
            indices.extend([top_outer_base + next_i, top_inner_base + next_i, top_inner_base + i])

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
                'Thickness': thickness,
                'InnerDiameter': inner_radius * 2
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
    from main import reset_ifc_document
    import io

    # Сброс документа: удаление предыдущих болтов
    ifc_doc = reset_ifc_document()

    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(
        bolt_type=params['bolt_type'],
        execution=params['execution'],
        diameter=params['diameter'],
        length=params['length'],
        material=params['material']
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
