"""
instance_factory.py — Создание инстансов болтов и сборок
"""

from typing import Any, Dict, Optional, Tuple

from gost_data import (
    get_material_name,
    get_nut_dimensions,
    get_washer_dimensions,
    validate_parameters,
)
from material_manager import MaterialManager
from protocols import IfcDocumentProtocol, TypeFactoryProtocol
from type_factory import TypeFactory
from utils import get_ifcopenshell


class InstanceFactory:
    """Фабрика инстансов болтов"""

    def __init__(
        self,
        ifc_doc: IfcDocumentProtocol,
        type_factory: Optional[TypeFactoryProtocol] = None,
        geometry_type: str = "solid",
    ):
        self.ifc: IfcDocumentProtocol = ifc_doc
        self.type_factory: TypeFactoryProtocol = type_factory or TypeFactory(
            ifc_doc, geometry_type=geometry_type
        )
        self.material_manager = MaterialManager(ifc_doc)

    def create_bolt_assembly(
        self,
        bolt_type,
        diameter,
        length,
        material,
        assembly_class="IfcMechanicalFastener",
        assembly_mode="separate",
        geometry_type="solid",
    ):
        """
        Создание полной сборки анкерного болта

        Args:
            assembly_class: Класс сборки ("IfcMechanicalFastener" или "IfcElementAssembly")
            assembly_mode: Режим сборки ("separate" или "unified")
            geometry_type: Тип геометрии ("solid" или "mesh")

        Состав сборки по умолчанию:
        - Типы 1.1, 1.2, 5: шпилька + верхняя шайба + 2 верхних гайки
        - Тип 2.1: шпилька + верхняя шайба + 2 верхних гайки + 2 нижних гайки

        Returns:
            dict с assembly, stud, components и mesh_data
        """
        ifc = get_ifcopenshell()

        # Валидация параметров
        validate_parameters(bolt_type, diameter, length, material)

        # Получение размеров компонентов
        nut_dim = get_nut_dimensions(diameter)
        washer_dim = get_washer_dimensions(diameter)

        nut_height = nut_dim["height"] if nut_dim else 10
        washer_thickness = washer_dim["thickness"] if washer_dim else 3

        # Автоматическое определение состава сборки по типу болта
        has_top_washer = True
        has_top_nut1 = True
        has_top_nut2 = True
        has_bottom_nut = bolt_type == "2.1"
        has_bottom_nut2 = bolt_type == "2.1"
        has_plate = bolt_type == "2.1"  # Анкерная плита только для типа 2.1

        # Получение размеров плиты (только для типа 2.1)
        plate_thickness = 0
        if has_plate:
            from data import get_plate_dimensions

            plate_dim_data = get_plate_dimensions(diameter)
            plate_thickness = plate_dim_data["thickness"] if plate_dim_data else 0

        # Получение типов - ТОЛЬКО для separate режима
        stud_type = None
        nut_type = None
        washer_type = None
        plate_type = None

        if assembly_mode == "separate":
            stud_type = self.type_factory.get_or_create_stud_type(
                bolt_type, diameter, length, material
            )
            nut_type = self.type_factory.get_or_create_nut_type(diameter, material)
            washer_type = self.type_factory.get_or_create_washer_type(diameter, material)
            if has_plate:
                plate_type = self.type_factory.get_or_create_plate_type(diameter, material)

        assembly_type = self.type_factory.get_or_create_assembly_type(
            bolt_type, diameter, length, material, assembly_class
        )

        # Получение storey для размещения
        storeys = self.ifc.by_type("IfcBuildingStorey")
        storey = storeys[0] if storeys else None

        # Получение OwnerHistory (единый для всех элементов)
        owner_histories = self.ifc.by_type("IfcOwnerHistory")
        owner_history = owner_histories[0] if owner_histories else None

        # Создание assembly с OwnerHistory
        assembly_placement = self.ifc.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=None,
            RelativePlacement=self.ifc.create_entity(
                "IfcAxis2Placement3D",
                Location=self.ifc.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0]),
                Axis=self.ifc.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
                RefDirection=self.ifc.create_entity(
                    "IfcDirection", DirectionRatios=[1.0, 0.0, 0.0]
                ),
            ),
        )

        # Согласно правилу OJT001: если экземпляр связан с типом через IfcRelDefinesByType
        # и у типа PredefinedType != NOTDEFINED, то PredefinedType у экземпляра должен быть пустым
        # ObjectType указывается для уточнения типа объекта
        if assembly_class == "IfcElementAssembly":
            assembly = self.ifc.create_entity(
                "IfcElementAssembly",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                Name=assembly_type.Name,
                ObjectType="ANCHORBOLT",
                ObjectPlacement=assembly_placement,
            )
        else:
            assembly = self.ifc.create_entity(
                "IfcMechanicalFastener",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                Name=assembly_type.Name,
                ObjectPlacement=assembly_placement,
            )
        self._add_instance_representation(assembly, assembly_type)

        # Создаём материал сборки и ассоциируем с assembly
        mat_name = get_material_name(material)
        mat = self.material_manager.get_material(mat_name)
        if mat:
            self.material_manager.associate_material(assembly, mat)

        # Компоненты - ТОЛЬКО для separate режима
        components = []
        stud_instances = []
        nut_instances = []
        washer_instances = []
        plate_instances = []

        if assembly_mode == "separate":
            # Шпилька
            stud_offset = 0.0
            stud_axis_down = False
            if bolt_type in ("1.1", "1.2"):
                from gost_data import get_thread_length

                stud_offset = get_thread_length(diameter, length) or 0
            elif bolt_type in ("2.1", "5"):
                from gost_data import get_thread_length

                l0 = get_thread_length(diameter, length) or length
                stud_offset = l0
                stud_axis_down = True
            stud_placement = self._create_placement(
                (0, 0, stud_offset), axis_down=stud_axis_down, rel_to=assembly_placement
            )
            stud = self.ifc.create_entity(
                "IfcMechanicalFastener",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                Name=stud_type.Name,
                ObjectPlacement=stud_placement,
            )
            self._add_instance_representation(stud, stud_type)
            stud_instances.append(stud)
            components.append(stud)

            # Шайба
            if has_top_washer:
                washer_top = self._create_component(
                    "Washer",
                    (0, 0, washer_thickness / 2),
                    washer_type,
                    washer_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(washer_top)

            # Гайка 1
            if has_top_nut1:
                nut_top1 = self._create_component(
                    "Nut",
                    (0, 0, washer_thickness / 2 + nut_height / 2),
                    nut_type,
                    nut_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(nut_top1)

            # Гайка 2
            if has_top_nut2:
                nut_top2 = self._create_component(
                    "Nut",
                    (0, 0, washer_thickness + nut_height + nut_height / 2),
                    nut_type,
                    nut_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(nut_top2)

            # Нижняя гайка 2
            if has_bottom_nut2:
                from gost_data import get_thread_length

                l0 = get_thread_length(diameter, length) or length
                stud_bottom = -(length - l0)
                nut_bottom2 = self._create_component(
                    "Nut",
                    (0, 0, stud_bottom + 18),
                    nut_type,
                    nut_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(nut_bottom2)

            # Плита
            if has_plate and plate_type:
                from gost_data import get_thread_length

                l0 = get_thread_length(diameter, length) or length
                stud_bottom = -(length - l0)
                # Плита лежит НА нижней гайке 2: центр на Z = stud_bottom + 18 + nut_height/2 + plate_thickness/2
                plate_center_z = stud_bottom + 18 + nut_height / 2 + plate_thickness / 2
                plate = self._create_component(
                    "Plate",
                    (0, 0, plate_center_z),
                    plate_type,
                    plate_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(plate)

            # Нижняя гайка 1
            if has_bottom_nut:
                from gost_data import get_thread_length

                l0 = get_thread_length(diameter, length) or length
                stud_bottom = -(length - l0)
                # Нижняя гайка 1 лежит НА плите: центр на Z = stud_bottom + 18 + nut_height/2 + plate_thickness + nut_height/2
                nut_bottom_z = stud_bottom + 18 + nut_height / 2 + plate_thickness + nut_height / 2
                nut_bottom = self._create_component(
                    "Nut",
                    (0, 0, nut_bottom_z),
                    nut_type,
                    nut_instances,
                    owner_history,
                    assembly_placement,
                )
                components.append(nut_bottom)

        # IfcRelDefinesByType
        self.ifc.create_entity(
            "IfcRelDefinesByType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            RelatingType=assembly_type,
            RelatedObjects=[assembly],
        )
        if stud_instances:
            self.ifc.create_entity(
                "IfcRelDefinesByType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingType=stud_type,
                RelatedObjects=stud_instances,
            )
        if nut_instances:
            self.ifc.create_entity(
                "IfcRelDefinesByType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingType=nut_type,
                RelatedObjects=nut_instances,
            )
        if washer_instances:
            self.ifc.create_entity(
                "IfcRelDefinesByType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingType=washer_type,
                RelatedObjects=washer_instances,
            )
        if plate_instances:
            self.ifc.create_entity(
                "IfcRelDefinesByType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingType=plate_type,
                RelatedObjects=plate_instances,
            )

        # IfcRelContainedInSpatialStructure
        # Согласно правилам SPS003, SPS005, SPS007:
        # Компоненты сборки (IfcRelAggregates) не должны быть в пространственной структуре.
        # Только главный элемент сборки помещается в IfcRelContainedInSpatialStructure.
        if storey:
            elements = [assembly]  # Только assembly, без компонентов
            self.ifc.create_entity(
                "IfcRelContainedInSpatialStructure",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingStructure=storey,
                RelatedElements=elements,
            )

        # IfcRelAggregates и IfcRelConnectsElements - ТОЛЬКО для separate
        if assembly_mode == "separate":
            self.ifc.create_entity(
                "IfcRelAggregates",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingObject=assembly,
                RelatedObjects=components,
            )
            for i in range(len(components) - 1):
                self.ifc.create_entity(
                    "IfcRelConnectsElements",
                    GlobalId=ifc.guid.new(),
                    OwnerHistory=owner_history,
                    RelatingElement=components[i],
                    RelatedElement=components[i + 1],
                )

        # Unified mode - булева геометрия
        if assembly_mode == "unified":
            self._apply_unified_mode(assembly, geometry_type, bolt_type, diameter, length)

        # Mesh data
        if assembly_mode == "unified":
            mesh_data = self._generate_mesh_data_unified(
                assembly, bolt_type, diameter, length, material, assembly.Name
            )
        else:
            mesh_data = self._generate_mesh_data_with_assembly_id(
                components, bolt_type, diameter, length, material, assembly, assembly.Name
            )

        return {
            "assembly": assembly,
            "stud": stud if assembly_mode == "separate" else None,
            "components": components,
            "mesh_data": mesh_data,
            "ifc_doc": self.ifc,
        }

    def _create_placement(self, location, axis_down=False, rel_to=None):
        """Создание 3D размещения

        Согласно правилу OJP001: если элемент является частью другого элемента
        через IfcRelAggregates, то его размещение должно быть относительным
        (PlacementRelTo должен указывать на размещение контейнера).

        Args:
            location: Координаты (x, y, z)
            axis_down: Направление оси Z (-1 или 1)
            rel_to: IfcLocalPlacement контейнера (для относительного размещения)
        """
        coords = [float(x) for x in location]
        # Для типа 2.1 и 5: ось направлена вниз, чтобы шпилька шла от Z=0 до Z=+length
        # но размещалась от Z=l0 вниз до Z=-(L-l0)
        axis_z = -1.0 if axis_down else 1.0
        return self.ifc.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=rel_to,
            RelativePlacement=self.ifc.create_entity(
                "IfcAxis2Placement3D",
                Location=self.ifc.create_entity("IfcCartesianPoint", Coordinates=coords),
                Axis=self.ifc.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, axis_z]),
                RefDirection=self.ifc.create_entity(
                    "IfcDirection", DirectionRatios=[1.0, 0.0, 0.0]
                ),
            ),
        )

    def _create_component(
        self,
        comp_type,
        location,
        type_obj,
        instances_list,
        owner_history=None,
        assembly_placement=None,
    ):
        """Создание компонента (гайка/шайба/плита)

        Имя наследуется из типа.
        PredefinedType не указывается (наследуется от типа через IfcRelDefinesByType).
        Согласно правилу OJT001: если экземпляр связан с типом, PredefinedType должен быть пустым.
        Согласно правилу OJP001: размещение компонента должно быть относительным assembly_placement.
        """
        ifc = get_ifcopenshell()
        placement = self._create_placement(location, rel_to=assembly_placement)
        component = self.ifc.create_entity(
            "IfcMechanicalFastener",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            Name=type_obj.Name,
            ObjectPlacement=placement,
        )
        self._add_instance_representation(component, type_obj)
        instances_list.append(component)
        return component

    def _add_instance_representation(self, instance, type_obj):
        """
        Добавление представления к инстансу через IfcMappedItem

        Согласно IFC4 спецификации:
        - IfcMappedItem ссылается на RepresentationMap типа
        - Геометрия не дублируется, а переиспользуется
        - Уменьшает размер IFC файла

        Args:
            instance: Экземпляр IfcMechanicalFastener
            type_obj: Тип IfcMechanicalFastenerType с RepresentationMaps
        """
        if not hasattr(type_obj, "RepresentationMaps") or not type_obj.RepresentationMaps:
            return

        rep_maps = type_obj.RepresentationMaps
        if not isinstance(rep_maps, (list, tuple)):
            rep_maps = [rep_maps]

        # Создаём IfcMappedItem для каждой RepresentationMap
        mapped_items = []
        for rep_map in rep_maps:
            if not hasattr(rep_map, "MappingOrigin"):
                continue

            mapped_item = self.ifc.create_entity(
                "IfcMappedItem",
                MappingSource=rep_map,
                MappingTarget=self.ifc.create_entity(
                    "IfcCartesianTransformationOperator3D",
                    Axis1=self.ifc.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0]),
                    Axis2=self.ifc.create_entity("IfcDirection", DirectionRatios=[0.0, 1.0, 0.0]),
                    LocalOrigin=self.ifc.create_entity(
                        "IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0]
                    ),
                    Scale=1.0,
                ),
            )
            mapped_items.append(mapped_item)

        if not mapped_items:
            return

        # Создаём представление с IfcMappedItem
        try:
            # Получаем контекст из первой RepresentationMap
            first_map = rep_maps[0]
            if hasattr(first_map, "MappedRepresentation"):
                context = first_map.MappedRepresentation.ContextOfItems
                identifier = first_map.MappedRepresentation.RepresentationIdentifier
            else:
                context = None
                identifier = "Body"

            # Для IfcMappedItem RepresentationType должен быть 'MappedRepresentation'
            # Согласно IFC спецификации: Items типа IfcMappedItem требуют RepresentationType='MappedRepresentation'
            rep_type = "MappedRepresentation"

            instance_shape_rep = self.ifc.create_entity(
                "IfcShapeRepresentation",
                ContextOfItems=context,
                RepresentationIdentifier=identifier,
                RepresentationType=rep_type,
                Items=mapped_items,
            )
            prod_def_shape = self.ifc.create_entity(
                "IfcProductDefinitionShape", Representations=[instance_shape_rep]
            )
            instance.Representation = prod_def_shape
        except Exception as e:
            print(f"Warning: Could not create representation for {instance.Name}: {e}")

    def _duplicate_geometric_items(self, items):
        """
        Дублирование геометрических элементов через ShapeBuilder.deep_copy()

        Согласно документации IfcOpenShell:
        - deep_copy() создаёт полную копию геометрии со всеми зависимостями
        - Поддерживает все типы сущностей IFC
        - Значительно проще и надёжнее ручного дублирования

        Args:
            items: Список IFC сущностей для дублирования

        Returns:
            Список скопированных сущностей
        """
        from ifcopenshell.util.shape_builder import ShapeBuilder

        builder = ShapeBuilder(self.ifc)
        return [builder.deep_copy(item) for item in items]

    def _weld_nearby_vertices(self, verts, faces, tolerance=0.01):
        """
        Сваривает вершины которые находятся близко друг к другу

        Нужно для BRP002: IfcClosedShell должен быть связным.
        Булевы операции создают вершины в местах касания компонентов,
        но они не имеют одинаковых координат из-за погрешностей вычислений.

        Args:
            verts: Плоский список координат [x1, y1, z1, x2, y2, z2, ...]
            faces: Плоский список индексов граней [v0, v1, v2, v3, v4, v5, ...]
            tolerance: Допуск в мм (вершины ближе этого расстояния свариваются)

        Returns:
            Кортеж (new_verts, new_faces) со сваренными вершинами и обновлёнными гранями
        """
        if not verts or not faces:
            return verts, faces

        import numpy as np

        # Преобразуем в numpy array для удобства
        verts_array = np.array(verts).reshape(-1, 3)

        # Словарь для маппинга вершин: старый индекс -> новый индекс
        vertex_map = {}
        # Список представительных вершин
        unique_verts = []

        for i, vert in enumerate(verts_array):
            # Ищем ближайшую представительную вершину
            found = False
            for j, unique_vert in enumerate(unique_verts):
                if np.linalg.norm(vert - unique_vert) < tolerance:
                    vertex_map[i] = j
                    found = True
                    break

            if not found:
                # Добавляем новую представительную вершину
                vertex_map[i] = len(unique_verts)
                unique_verts.append(vert)

        # Обновляем грани
        new_faces = []
        for i in range(0, len(faces), 3):
            v0, v1, v2 = faces[i], faces[i + 1], faces[i + 2]
            new_faces.extend([vertex_map[v0], vertex_map[v1], vertex_map[v2]])

        # Возвращаем плоский список координат представительных вершин
        new_verts = []
        for vert in unique_verts:
            new_verts.extend(vert.tolist())

        return new_verts, new_faces

    def _fix_triangle_orientation(self, verts, faces):
        """
        Исправляет ориентацию треугольников для GEM001.

        Для IfcClosedShell все грани должны быть ориентированы так, чтобы
        нормали были направлены наружу. Это обеспечивает, что каждое ребро
        используется ровно 1 раз с правильной ориентацией.

        Алгоритм:
        1. Вычисляем центр масс всех вершин
        2. Для каждого треугольника вычисляем нормаль
        3. Если нормаль направлена внутрь (к центру), инвертируем треугольник

        Args:
            verts: Плоский список координат [x1, y1, z1, ...]
            faces: Плоский список индексов [v0, v1, v2, ...]

        Returns:
            Кортеж (verts, new_faces) с исправленной ориентацией
        """
        if not verts or not faces:
            return verts, faces

        import numpy as np

        verts_array = np.array(verts).reshape(-1, 3)

        # Вычисляем центр масс
        center = np.mean(verts_array, axis=0)

        new_faces = []
        for i in range(0, len(faces), 3):
            v0, v1, v2 = faces[i], faces[i + 1], faces[i + 2]

            p0 = verts_array[v0]
            p1 = verts_array[v1]
            p2 = verts_array[v2]

            # Вычисляем нормаль треугольника (правое правило)
            edge1 = p1 - p0
            edge2 = p2 - p0
            normal = np.cross(edge1, edge2)

            # Вектор от центра к треугольнику
            to_triangle = p0 - center

            # Если нормаль направлена внутрь (скалярное произведение < 0), инвертируем
            if np.dot(normal, to_triangle) < 0:
                # Инвертируем порядок вершин
                new_faces.extend([v0, v2, v1])
            else:
                new_faces.extend([v0, v1, v2])

        return verts, new_faces

    def _generate_mesh_data(
        self, components, bolt_type, diameter, length, material, assembly_name=None
    ):
        """Генерация mesh данных через ifcopenshell.geom"""
        from geometry_converter import convert_assembly_to_meshes

        color_map = {
            "STUD": 0x8B8B8B,
            "WASHER": 0xA9A9A9,
            "NUT": 0x696969,
            "ANCHORBOLT": 0x4F4F4F,
        }

        # Преобразуем assembly_name в строку Python
        if assembly_name and hasattr(assembly_name, "__str__"):
            assembly_name = str(assembly_name)

        # Формируем информацию о сборке
        assembly_info = {
            "bolt_type": bolt_type,
            "diameter": diameter,
            "length": length,
            "material": material,
            "name": assembly_name or f"bolt_{bolt_type}_M{diameter}x{length}",
            "globalId": None,  # Будет установлен ниже
        }

        # Конвертация IFC геометрии в Three.js mesh
        mesh_data = convert_assembly_to_meshes(self.ifc, components, color_map, assembly_info)

        if not mesh_data or not mesh_data.get("meshes"):
            print(f"Warning: ifcopenshell.geom failed to generate mesh data")
            return {"meshes": []}

        return mesh_data

    def _generate_mesh_data_with_assembly_id(
        self, components, bolt_type, diameter, length, material, assembly, assembly_name=None
    ):
        """Генерация mesh данных с GlobalId сборки"""
        from geometry_converter import convert_assembly_to_meshes

        color_map = {
            "STUD": 0x8B8B8B,
            "WASHER": 0xA9A9A9,
            "NUT": 0x696969,
            "ANCHORBOLT": 0x4F4F4F,
        }

        if assembly_name and hasattr(assembly_name, "__str__"):
            assembly_name = str(assembly_name)

        assembly_info = {
            "bolt_type": bolt_type,
            "diameter": diameter,
            "length": length,
            "material": material,
            "name": assembly_name or f"bolt_{bolt_type}_M{diameter}x{length}",
            "globalId": assembly.GlobalId,
        }

        mesh_data = convert_assembly_to_meshes(self.ifc, components, color_map, assembly_info)

        if not mesh_data or not mesh_data.get("meshes"):
            print(f"Warning: ifcopenshell.geom failed to generate mesh data")
            return {"meshes": []}

        return mesh_data

    def _apply_unified_mode(self, assembly, geometry_type, bolt_type, diameter, length):
        """Булево объединение геометрии через IfcCSGSolid"""
        from geometry_builder import GeometryBuilder
        from gost_data import get_nut_dimensions, get_thread_length, get_washer_dimensions

        builder = GeometryBuilder(self.ifc)
        nut_dim = get_nut_dimensions(diameter)
        washer_dim = get_washer_dimensions(diameter)
        nut_height = nut_dim["height"] if nut_dim else 10
        washer_thickness = washer_dim["thickness"] if washer_dim else 3

        all_solids = []

        # Определяем состав сборки
        has_top_washer = True
        has_top_nut1 = True
        has_top_nut2 = True
        has_bottom_nut2 = bolt_type == "2.1"
        has_plate = bolt_type == "2.1"
        has_bottom_nut = bolt_type == "2.1"

        # Вычисляем l0 для позиционирования
        l0 = get_thread_length(diameter, length) or length

        # Шпилька — создаётся с учётом типа
        if bolt_type in ["1.1", "1.2"]:
            # Изогнутая шпилька: геометрия от Z=0 до Z=-Ll
            # В separate режиме шпилька имеет ObjectPlacement Z=l0
            # В unified режиме создаём геометрию сразу в мировых координатах
            # Смещаем на l0 вверх
            stud_solid = builder.create_bent_stud_solid_raw(
                bolt_type, diameter, length, position=(0.0, 0.0, l0)
            )
        else:
            # Прямая шпилька: в separate режиме геометрия от (0,0,0) до (0,0,-length)
            # ObjectPlacement Z=l0 смещает инстанс в мир на Z=l0
            # В unified режиме создаём геометрию сразу в мировых координатах
            # От Z=l0 до Z=l0-length
            stud_solid = builder.create_straight_stud_solid_raw(
                diameter, length, position=(0.0, 0.0, l0)
            )
        all_solids.append(stud_solid)

        # Шайба: в separate ObjectPlacement Z=washer_thickness/2=4мм, геометрия 0..8мм
        # В мире: 4..12мм, центр 8мм
        # В unified: position=washer_thickness/2=4мм даёт геометрию от 4мм до 12мм
        washer_solid = builder.create_washer_solid_raw(
            diameter,
            washer_dim["outer_diameter"] if washer_dim else diameter + 10,
            washer_thickness,
            position=(0.0, 0.0, washer_thickness / 2),
        )
        all_solids.append(washer_solid)

        # Гайка 1: лежит на шайбе (Z=12мм), центр на Z = 20мм
        # Шайба: 4-12мм, гайка 1: 12-28мм
        # position = washer_thickness/2 + washer_thickness = 4 + 8 = 12мм
        nut_solid_1 = builder.create_nut_solid_raw(
            diameter,
            nut_height,
            position=(0.0, 0.0, washer_thickness / 2 + washer_thickness),
        )
        all_solids.append(nut_solid_1)

        # Гайка 2: с просветом 4мм, position = washer_thickness/2 + washer_thickness + nut_height + 4
        # = 4 + 8 + 16 + 4 = 32мм, геометрия от 32 до 48мм
        nut_solid_2 = builder.create_nut_solid_raw(
            diameter,
            nut_height,
            position=(
                0.0,
                0.0,
                washer_thickness / 2 + washer_thickness + nut_height + 4,
            ),
        )
        all_solids.append(nut_solid_2)

        # Нижняя гайка 2 (тип 2.1): центр на Z = stud_bottom + 18
        if has_bottom_nut2:
            stud_bottom = -(length - l0)  # Низ шпильки
            nut_bottom_z = stud_bottom + 18
            nut_solid_bottom2 = builder.create_nut_solid_raw(
                diameter, nut_height, position=(0.0, 0.0, nut_bottom_z)
            )
            all_solids.append(nut_solid_bottom2)

        # Плита (тип 2.1): между нижней гайкой 2 и нижней гайкой 1
        if has_plate:
            from data import get_plate_dimensions

            plate_dim = get_plate_dimensions(diameter)
            if plate_dim:
                # Плита лежит НА нижней гайке 2: центр на Z = stud_bottom + 18 + nut_height/2 + plate_thickness/2
                plate_thickness = plate_dim["thickness"]
                plate_z = stud_bottom + 18 + nut_height / 2 + plate_thickness / 2
                plate_solid = builder.create_plate_solid_raw(
                    diameter,
                    plate_dim["width"],
                    plate_thickness,
                    plate_dim["hole_d"],
                    position=(0.0, 0.0, plate_z),
                )
                all_solids.append(plate_solid)

        # Нижняя гайка 1 (тип 2.1): над плитой
        if has_bottom_nut:
            stud_bottom = -(length - l0)
            plate_thickness = (
                get_plate_dimensions(diameter)["thickness"] if get_plate_dimensions(diameter) else 0
            )
            # Гайка лежит НА плите: центр на Z = stud_bottom + 18 + nut_height/2 + plate_thickness + nut_height/2
            nut_bottom_z = stud_bottom + 18 + nut_height / 2 + plate_thickness + nut_height / 2
            nut_solid_bottom = builder.create_nut_solid_raw(
                diameter, nut_height, position=(0.0, 0.0, nut_bottom_z)
            )
            all_solids.append(nut_solid_bottom)

        # Булево объединение
        if len(all_solids) >= 2:
            unified_shape = builder.create_boolean_union(all_solids)
            context = builder._get_context()

            if geometry_type == "faceted":
                # Для faceted режима: извлекаем mesh из IfcCSGSolid и создаём IfcFacetedBrep
                import ifcopenshell
                import ifcopenshell.geom
                from ifcopenshell.util.shape_builder import ShapeBuilder

                shape_builder = ShapeBuilder(self.ifc)

                # Извлекаем mesh из IfcCSGSolid через ifcopenshell.geom
                try:
                    # Создаём временное представление
                    temp_shape_rep = self.ifc.create_entity(
                        "IfcShapeRepresentation",
                        ContextOfItems=context,
                        RepresentationIdentifier="Body",
                        RepresentationType="SolidModel",
                        Items=[unified_shape],
                    )

                    # Создаём временный продукт для извлечения геометрии
                    temp_product = self.ifc.create_entity(
                        "IfcBuildingElementProxy",
                        GlobalId=ifcopenshell.guid.new(),
                        Name="TempProxyForMesh",
                        ObjectPlacement=self.ifc.create_entity(
                            "IfcLocalPlacement",
                            None,
                            self.ifc.create_entity(
                                "IfcAxis2Placement3D",
                                self.ifc.create_entity("IfcCartesianPoint", (0.0, 0.0, 0.0)),
                            ),
                        ),
                        Representation=self.ifc.create_entity(
                            "IfcProductDefinitionShape",
                            Representations=[temp_shape_rep],
                        ),
                    )

                    # Извлекаем mesh через ifcopenshell.geom
                    # WELD_VERTICES=True для сварки вершин
                    settings = ifcopenshell.geom.settings()
                    settings.set(settings.WELD_VERTICES, True)
                    settings.set(settings.USE_WORLD_COORDS, True)

                    shape = ifcopenshell.geom.create_shape(settings, temp_product)

                    # Перед удалением temp_product, очищаем temp_shape_rep.Items
                    temp_shape_rep.Items = []

                    # Удаляем временный продукт и всю цепочку связанных сущностей
                    import ifcopenshell.util.element

                    context = temp_shape_rep.ContextOfItems
                    ifcopenshell.util.element.remove_deep2(
                        self.ifc, temp_product, do_not_delete={context}
                    )

                    if shape and len(shape.geometry.verts) > 0:
                        verts = shape.geometry.verts
                        faces = shape.geometry.faces

                        # Масштабируем в мм
                        verts_mm = [v * 1000.0 for v in verts]

                        # Свариваем вершины которые находятся близко друг к другу
                        # Это нужно для BRP002: IfcClosedShell должен быть связным
                        verts_mm, faces = self._weld_nearby_vertices(
                            verts_mm, faces, tolerance=0.01
                        )

                        # Исправляем ориентацию треугольников для GEM001
                        # Все нормали должны быть направлены наружу
                        verts_mm, faces = self._fix_triangle_orientation(verts_mm, faces)

                        # Преобразуем в points и triangles
                        points = [tuple(verts_mm[i : i + 3]) for i in range(0, len(verts_mm), 3)]
                        triangles = [list(faces[i : i + 3]) for i in range(0, len(faces), 3)]

                        # Создаём IfcFacetedBrep
                        faceted_brep = shape_builder.faceted_brep(points, triangles)

                        # Создаём представление с Brep
                        shape_rep = builder.create_shape_representation_from_brep(faceted_brep)
                        old_representation = assembly.Representation
                        assembly.Representation = self.ifc.create_entity(
                            "IfcProductDefinitionShape", Representations=[shape_rep]
                        )

                        # Удаляем unified_shape и all_solids
                        import ifcopenshell.util.element

                        protected = {
                            *self.ifc.by_type("IfcGeometricRepresentationContext"),
                            *self.ifc.by_type("IfcOwnerHistory"),
                            *self.ifc.by_type("IfcPerson"),
                            *self.ifc.by_type("IfcOrganization"),
                        }

                        ifcopenshell.util.element.remove_deep2(
                            self.ifc, unified_shape, do_not_delete=protected
                        )

                        if old_representation:
                            ifcopenshell.util.element.remove_deep2(
                                self.ifc, old_representation, do_not_delete=protected
                            )
                    else:
                        raise ValueError("Empty mesh from ifcopenshell.geom")

                except Exception as e:
                    # Fallback к SolidModel
                    print(
                        f"Warning: Could not create FacetedBrep: {e}. Falling back to SolidModel."
                    )
                    shape_rep = self.ifc.create_entity(
                        "IfcShapeRepresentation",
                        ContextOfItems=context,
                        RepresentationIdentifier="Body",
                        RepresentationType="SolidModel",
                        Items=[unified_shape],
                    )
                    assembly.Representation = self.ifc.create_entity(
                        "IfcProductDefinitionShape", Representations=[shape_rep]
                    )
            else:
                # Solid режим: используем IfcCSGSolid напрямую
                shape_rep = self.ifc.create_entity(
                    "IfcShapeRepresentation",
                    ContextOfItems=context,
                    RepresentationIdentifier="Body",
                    RepresentationType="SolidModel",
                    Items=[unified_shape],
                )
                assembly.Representation = self.ifc.create_entity(
                    "IfcProductDefinitionShape", Representations=[shape_rep]
                )

    def _generate_mesh_data_unified(
        self, assembly, bolt_type, diameter, length, material, assembly_name=None
    ):
        """Генерация mesh из IfcCSGSolid"""
        from geometry_converter import convert_ifc_to_mesh

        # Цвет как у шпильки в separate режиме (STUD: 0x8B8B8B)
        color_map = {"ANCHORBOLT": 0x8B8B8B}

        # Преобразуем assembly_name в строку Python
        if assembly_name and hasattr(assembly_name, "__str__"):
            assembly_name = str(assembly_name)

        mesh_data = convert_ifc_to_mesh(self.ifc, assembly)
        if not mesh_data:
            return {"meshes": []}

        return {
            "meshes": [
                {
                    "id": assembly.id(),
                    "name": assembly_name or "Assembly",
                    "vertices": mesh_data["vertices"],
                    "indices": mesh_data["indices"],
                    "normals": mesh_data["normals"],
                    "color": color_map.get("ANCHORBOLT", 0x4F4F4F),
                    "metadata": {
                        "Type": "ANCHORBOLT",
                        "GlobalId": assembly.GlobalId,
                        "unified": True,
                    },
                }
            ],
            "assembly_info": {
                "bolt_type": bolt_type,
                "diameter": diameter,
                "length": length,
                "material": material,
                "name": assembly_name or f"bolt_{bolt_type}_M{diameter}x{length}",
                "globalId": assembly.GlobalId,
            },
        }


def generate_bolt_assembly(
    params: Dict[str, Any],
    assembly_class="IfcMechanicalFastener",
    assembly_mode="separate",
    geometry_type="solid",
) -> Tuple[str, Dict[str, Any]]:
    """
    Главная функция для генерации болта

    Args:
        params: dict с параметрами болта:
            - bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
            - diameter: Диаметр (мм)
            - length: Длина (мм)
            - material: Материал ('09Г2С', 'ВСт3пс2', '10Г2')
        assembly_class: Класс сборки ('IfcMechanicalFastener' или 'IfcElementAssembly')
        assembly_mode: Режим формирования ('separate' или 'unified')
        geometry_type: Тип геометрии ('solid' или 'triangulated')

    Returns:
        Кортеж (ifc_string, mesh_data):
            - ifc_string: IFC файл в виде строки
            - mesh_data: Данные для 3D визуализации
    """
    import tempfile

    from main import reset_ifc_document

    # Сброс документа: удаление предыдущих болтов
    ifc_doc = reset_ifc_document()

    factory = InstanceFactory(ifc_doc, geometry_type=geometry_type)
    result = factory.create_bolt_assembly(
        bolt_type=params["bolt_type"],
        diameter=params["diameter"],
        length=params["length"],
        material=params["material"],
        assembly_class=assembly_class,
        assembly_mode=assembly_mode,
        geometry_type=geometry_type,
    )

    # Экспорт во временный файл (для совместимости с ifcopenshell.write)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".ifc", delete=False) as tmp:
        tmp_path = tmp.name

    ifc_doc.write(tmp_path)

    # Чтение файла и возврат строки
    with open(tmp_path, "r") as f:
        ifc_str = f.read()

    # Очистка временного файла
    import os

    os.unlink(tmp_path)

    return (ifc_str, result["mesh_data"])
