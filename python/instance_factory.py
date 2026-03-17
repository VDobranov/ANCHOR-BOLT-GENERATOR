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
        self, ifc_doc: IfcDocumentProtocol, type_factory: Optional[TypeFactoryProtocol] = None
    ):
        self.ifc: IfcDocumentProtocol = ifc_doc
        self.type_factory: TypeFactoryProtocol = type_factory or TypeFactory(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)

    def create_bolt_assembly(self, bolt_type, diameter, length, material):
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

        # Получение типов
        stud_type = self.type_factory.get_or_create_stud_type(bolt_type, diameter, length, material)
        nut_type = self.type_factory.get_or_create_nut_type(diameter, material)
        washer_type = self.type_factory.get_or_create_washer_type(diameter, material)
        assembly_type = self.type_factory.get_or_create_assembly_type(bolt_type, diameter, material)

        # Получение типа плиты (только для типа 2.1)
        plate_type = None
        if has_plate:
            plate_type = self.type_factory.get_or_create_plate_type(diameter, material)

        # Получение storey для размещения
        storeys = self.ifc.by_type("IfcBuildingStorey")
        storey = storeys[0] if storeys else None

        # Получение OwnerHistory (единый для всех элементов)
        owner_histories = self.ifc.by_type("IfcOwnerHistory")
        owner_history = owner_histories[0] if owner_histories else None

        # Создание assembly с OwnerHistory
        # PredefinedType=ANCHORBOLT (из типа), поэтому ObjectType не указываем ($)
        ifc = get_ifcopenshell()
        assembly = self.ifc.create_entity(
            "IfcMechanicalFastener",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            Name=f"AnchorBolt_{bolt_type}_M{diameter}x{length}",
        )
        self._add_instance_representation(assembly, assembly_type)

        # Создаём материал сборки и ассоциируем с assembly
        mat_name = get_material_name(material)
        mat = self.material_manager.get_material(mat_name)
        if mat:
            self.material_manager.associate_material(assembly, mat)

        # Компоненты
        components = []
        stud_instances = []
        nut_instances = []
        washer_instances = []
        plate_instances = []  # Для типа 2.1

        # Шпилька
        # Для типа 1.1: смещение вверх на длину резьбы, чтобы начало резьбы было в (0,0,0)
        # Для типа 1.2: смещение на l0 (длина резьбы), чтобы низ резьбы был в (0,0,0)
        # Для типа 2.1: геометрия от Z=0 до Z=+length, размещаем на Z=l0 с осью вниз
        # Для типа 5: геометрия от Z=0 до Z=+length, размещаем на Z=l0 с осью вниз
        stud_offset = 0.0
        stud_axis_down = False
        if bolt_type in ("1.1", "1.2"):
            from gost_data import get_thread_length

            stud_offset = get_thread_length(diameter, length) or 0
        elif bolt_type in ("2.1", "5"):
            from gost_data import get_thread_length

            l0 = get_thread_length(diameter, length) or length
            stud_offset = l0  # Размещаем на Z=l0
            stud_axis_down = True  # Ось направлена вниз
        stud_placement = self._create_placement((0, 0, stud_offset), axis_down=stud_axis_down)
        # Маппинг типа болта в позицию {t}
        type_map = {"1.1": "1", "1.2": "2", "2.1": "3", "5": "7"}
        t = type_map.get(bolt_type, bolt_type)
        stud = self.ifc.create_entity(
            "IfcMechanicalFastener",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            Name=f"Шпилька {t}.М{diameter}×{length} ГОСТ 24379.1-2012",
            ObjectPlacement=stud_placement,
        )
        self._add_instance_representation(stud, stud_type)
        stud_instances.append(stud)
        components.append(stud)

        # Верхняя шайба (для всех типов)
        if has_top_washer:
            washer_top = self._create_component(
                "Washer",
                f"Шайба М{diameter} ГОСТ 24379.1-2012",
                (0, 0, washer_thickness / 2),
                washer_type,
                washer_instances,
                owner_history,
            )
            components.append(washer_top)

        # Верхняя гайка 1
        if has_top_nut1:
            z_pos = washer_thickness / 2
            nut_top1 = self._create_component(
                "Nut",
                f"Гайка М{diameter} ГОСТ 5915-70",
                (0, 0, z_pos + nut_height / 2),
                nut_type,
                nut_instances,
                owner_history,
            )
            components.append(nut_top1)

        # Верхняя гайка 2
        if has_top_nut2:
            z_pos = washer_thickness + nut_height
            nut_top2 = self._create_component(
                "Nut",
                f"Гайка М{diameter} ГОСТ 5915-70",
                (0, 0, z_pos + nut_height / 2),
                nut_type,
                nut_instances,
                owner_history,
            )
            components.append(nut_top2)

        # Нижняя гайка 2 (только для типа 2.1, самая нижняя)
        if has_bottom_nut2:
            # Позиция: центр на 18 мм выше низа шпильки
            from gost_data import get_thread_length

            l0 = get_thread_length(diameter, length) or length
            stud_bottom = -(length - l0)  # Низ шпильки
            z_pos = stud_bottom + 18  # Центр нижней гайки 2
            nut_bottom2 = self._create_component(
                "Nut",
                f"Гайка М{diameter} ГОСТ 5915-70",
                (0, 0, z_pos),
                nut_type,
                nut_instances,
                owner_history,
            )
            components.append(nut_bottom2)

        # Анкерная плита (только для типа 2.1, между нижними гайками)
        if has_plate and plate_type:
            from gost_data import get_thread_length

            from data import get_plate_dimensions

            l0 = get_thread_length(diameter, length) or length
            stud_bottom = -(length - l0)  # Низ шпильки
            # Плита над гайкой 2: центр на Z = stud_bottom + 18 + H + S/2 = stud_bottom + 34
            plate_center_z = stud_bottom + 34  # Центр плиты
            plate_placement = self._create_placement((0, 0, plate_center_z))
            # Получаем размеры плиты для имени
            plate_dim = get_plate_dimensions(diameter)
            width = plate_dim["width"] if plate_dim else 0
            plate = self.ifc.create_entity(
                "IfcMechanicalFastener",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                Name=f"Плита {width} ГОСТ 24379.1-2012",
                ObjectPlacement=plate_placement,
            )
            self._add_instance_representation(plate, plate_type)
            plate_instances.append(plate)
            components.append(plate)

        # Нижняя гайка 1 (только для типа 2.1, над плитой)
        if has_bottom_nut:
            # Гайка над плитой: центр на Z = stud_bottom + 18 + H + S + H/2 = stud_bottom + 50
            from gost_data import get_thread_length

            l0 = get_thread_length(diameter, length) or length
            stud_bottom = -(length - l0)  # Низ шпильки
            z_pos = stud_bottom + 50  # Центр гайки 1
            nut_bottom = self._create_component(
                "Nut",
                f"Гайка М{diameter} ГОСТ 5915-70",
                (0, 0, z_pos),
                nut_type,
                nut_instances,
                owner_history,
            )
            components.append(nut_bottom)

        # IfcRelDefinesByType для каждого типа
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
        if storey:
            self.ifc.create_entity(
                "IfcRelContainedInSpatialStructure",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingStructure=storey,
                RelatedElements=[assembly] + components,
            )

        # IfcRelAggregates
        self.ifc.create_entity(
            "IfcRelAggregates",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            RelatingObject=assembly,
            RelatedObjects=components,
        )

        # IfcRelConnectsElements между компонентами
        for i in range(len(components) - 1):
            self.ifc.create_entity(
                "IfcRelConnectsElements",
                GlobalId=ifc.guid.new(),
                OwnerHistory=owner_history,
                RelatingElement=components[i],
                RelatedElement=components[i + 1],
            )

        # Mesh data для 3D визуализации
        mesh_data = self._generate_mesh_data(components, bolt_type, diameter, length, material)

        return {
            "assembly": assembly,
            "stud": stud,
            "components": components,
            "mesh_data": mesh_data,
        }

    def _create_placement(self, location, axis_down=False):
        """Создание 3D размещения"""
        coords = [float(x) for x in location]
        # Для типа 2.1 и 5: ось направлена вниз, чтобы шпилька шла от Z=0 до Z=+length
        # но размещалась от Z=l0 вниз до Z=-(L-l0)
        axis_z = -1.0 if axis_down else 1.0
        return self.ifc.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=None,
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
        self, comp_type, name, location, type_obj, instances_list, owner_history=None
    ):
        """Создание компонента (гайка/шайба/плита)

        PredefinedType и ObjectType наследуются из типа.
        """
        ifc = get_ifcopenshell()
        placement = self._create_placement(location)
        component = self.ifc.create_entity(
            "IfcMechanicalFastener",
            GlobalId=ifc.guid.new(),
            OwnerHistory=owner_history,
            Name=name,
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

    def _generate_mesh_data(self, components, bolt_type, diameter, length, material):
        """Генерация mesh данных через ifcopenshell.geom"""
        from geometry_converter import convert_assembly_to_meshes

        color_map = {"STUD": 0x8B8B8B, "WASHER": 0xA9A9A9, "NUT": 0x696969, "ANCHORBOLT": 0x4F4F4F}

        # Конвертация IFC геометрии в Three.js mesh
        mesh_data = convert_assembly_to_meshes(self.ifc, components, color_map)

        if not mesh_data or not mesh_data.get("meshes"):
            print(f"Warning: ifcopenshell.geom failed to generate mesh data")
            return {"meshes": []}

        return mesh_data


def generate_bolt_assembly(params: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Главная функция для генерации болта

    Args:
        params: dict с параметрами болта:
            - bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
            - diameter: Диаметр (мм)
            - length: Длина (мм)
            - material: Материал ('09Г2С', 'ВСт3пс2', '10Г2')

    Returns:
        Кортеж (ifc_string, mesh_data):
            - ifc_string: IFC файл в виде строки
            - mesh_data: Данные для 3D визуализации
    """
    import tempfile

    from main import reset_ifc_document

    # Сброс документа: удаление предыдущих болтов
    ifc_doc = reset_ifc_document()

    factory = InstanceFactory(ifc_doc)
    result = factory.create_bolt_assembly(
        bolt_type=params["bolt_type"],
        diameter=params["diameter"],
        length=params["length"],
        material=params["material"],
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
