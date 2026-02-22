"""
instance_factory.py — Создание инстансов болтов и сборок
"""

from utils import get_ifcopenshell
from type_factory import TypeFactory
from gost_data import validate_parameters, get_nut_dimensions, get_washer_dimensions


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
        ifc = get_ifcopenshell()

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
        ifc = get_ifcopenshell()
        assembly = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifc.guid.new(),
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
        # Для типа 1.1: смещение вверх на длину резьбы, чтобы начало резьбы было в (0,0,0)
        stud_offset = 0.0
        if bolt_type == '1.1':
            from gost_data import get_thread_length
            stud_offset = get_thread_length(diameter, length) or 0
        stud_placement = self._create_placement((0, 0, stud_offset))
        stud = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifc.guid.new(),
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
            GlobalId=ifc.guid.new(),
            RelatingType=assembly_type,
            RelatedObjects=[assembly]
        )
        if stud_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifc.guid.new(),
                RelatingType=stud_type,
                RelatedObjects=stud_instances
            )
        if nut_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifc.guid.new(),
                RelatingType=nut_type,
                RelatedObjects=nut_instances
            )
        if washer_instances:
            self.ifc.create_entity('IfcRelDefinesByType',
                GlobalId=ifc.guid.new(),
                RelatingType=washer_type,
                RelatedObjects=washer_instances
            )

        # IfcRelContainedInSpatialStructure
        if storey:
            self.ifc.create_entity('IfcRelContainedInSpatialStructure',
                GlobalId=ifc.guid.new(),
                RelatingStructure=storey,
                RelatedElements=[assembly] + components
            )

        # IfcRelAggregates
        self.ifc.create_entity('IfcRelAggregates',
            GlobalId=ifc.guid.new(),
            RelatingObject=assembly,
            RelatedObjects=components
        )

        # IfcRelConnectsElements между компонентами
        for i in range(len(components) - 1):
            self.ifc.create_entity('IfcRelConnectsElements',
                GlobalId=ifc.guid.new(),
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
        ifc = get_ifcopenshell()
        placement = self._create_placement(location)
        component = self.ifc.create_entity('IfcMechanicalFastener',
            GlobalId=ifc.guid.new(),
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
        mesh_data = convert_assembly_to_meshes(self.ifc, components, color_map)

        if not mesh_data or not mesh_data.get('meshes'):
            print(f"Warning: ifcopenshell.geom failed to generate mesh data")
            return {'meshes': []}

        return mesh_data


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
