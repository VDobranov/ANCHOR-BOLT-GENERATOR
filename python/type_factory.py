"""
type_factory.py — Фабрика для создания и кэширования типов IFC
Использует RepresentationMaps для переиспользования геометрии

Согласно IFC4 спецификации:
- RepresentationMaps позволяет переиспользовать геометрию типа
- Экземпляры ссылаются на RepresentationMap типа через IfcMappedItem
- Уменьшает размер IFC файла и улучшает производительность
"""

from typing import Any, Dict, Optional

from geometry_builder import GeometryBuilder
from gost_data import get_material_name, get_nut_dimensions, get_washer_dimensions
from material_manager import MaterialManager
from protocols import IfcDocumentProtocol
from utils import get_ifcopenshell


class TypeFactory:
    """
    Фабрика типов IFC MechanicalFastenerType

    Использует RepresentationMaps для переиспользования геометрии:
    - Каждый тип имеет RepresentationMap с геометрией
    - Экземпляры создаются через IfcMappedItem
    - Геометрия кэшируется по ключу (тип, диаметр, длина)
    """

    def __init__(self, ifc_doc: IfcDocumentProtocol):
        self.ifc: IfcDocumentProtocol = ifc_doc
        self.types_cache: Dict[Any, Any] = {}
        self.representation_maps: Dict[tuple, Any] = {}  # Кэш RepresentationMap по ключу
        self.builder = GeometryBuilder(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)
        # Получаем OwnerHistory из документа
        owner_histories = self.ifc.by_type("IfcOwnerHistory")
        self.owner_history = owner_histories[0] if owner_histories else None

    def get_or_create_stud_type(self, bolt_type, diameter, length, material):
        """
        Создание/получение типа шпильки с RepresentationMap

        Args:
            bolt_type: Тип болта ('1.1', '1.2', '2.1', '5')
            diameter: Диаметр (мм)
            length: Длина (мм)
            material: Материал

        Returns:
            IfcMechanicalFastenerType для шпильки
        """
        key = ("stud", bolt_type, diameter, length, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f"Stud_M{diameter}x{length}_{bolt_type}"
        ifc = get_ifcopenshell()
        stud_type = self.ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            ElementType="STUD",
            PredefinedType="USERDEFINED",
        )

        # Делегируем построение геометрии в GeometryBuilder
        if bolt_type in ["1.1", "1.2"]:
            # Изогнутые шпильки: используем IfcSweptDiskSolid с составной кривой
            shape_rep = self.builder.create_bent_stud_solid(bolt_type, diameter, length)
        elif bolt_type in ["2.1", "5"]:
            # Тип 2.1 и 5: прямая шпилька через экструзию
            # Геометрия: от Z=0 до Z=+length
            # Placement: Z=l0 с осью вниз → шпилька от Z=-(L-l0) до Z=+l0
            shape_rep = self.builder.create_straight_stud_solid(diameter, length)
        else:
            # Другие типы
            shape_rep = self.builder.create_straight_stud_solid(diameter, length)

        # Ассоциируем RepresentationMap с типом
        self.builder.associate_representation(stud_type, shape_rep)

        # Кэшируем RepresentationMap для последующего использования
        geom_key = ("stud", bolt_type, diameter, length)
        if geom_key not in self.representation_maps:
            rep_maps = stud_type.RepresentationMaps
            if rep_maps:
                self.representation_maps[geom_key] = rep_maps[0]

        # Создаём материал и ассоциируем с типом
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category="Steel", material_key=material
        )
        self.material_manager.associate_material(stud_type, mat)

        self.types_cache[key] = stud_type
        return stud_type

    def get_or_create_nut_type(self, diameter, material):
        """
        Создание/получение типа гайки с RepresentationMap

        Args:
            diameter: Диаметр (мм)
            material: Материал

        Returns:
            IfcMechanicalFastenerType для гайки
        """
        key = ("nut", diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        nut_dim = get_nut_dimensions(diameter)
        height = nut_dim["height"] if nut_dim else 10
        type_name = f"Гайка М{diameter} ГОСТ 5915-70"
        ifc = get_ifcopenshell()

        nut_type = self.ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            ElementType="NUT",
            PredefinedType="USERDEFINED",
        )

        # Делегируем построение геометрии в GeometryBuilder
        shape_rep = self.builder.create_nut_solid(diameter, height)
        self.builder.associate_representation(nut_type, shape_rep)

        # Кэшируем RepresentationMap
        geom_key = ("nut", diameter)
        if geom_key not in self.representation_maps:
            rep_maps = nut_type.RepresentationMaps
            if rep_maps:
                self.representation_maps[geom_key] = rep_maps[0]

        # Создаём материал и ассоциируем с типом
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category="Steel", material_key=material
        )
        self.material_manager.associate_material(nut_type, mat)

        self.types_cache[key] = nut_type
        return nut_type

    def get_or_create_washer_type(self, diameter, material):
        """
        Создание/получение типа шайбы с RepresentationMap

        Args:
            diameter: Диаметр (мм)
            material: Материал

        Returns:
            IfcMechanicalFastenerType для шайбы
        """
        key = ("washer", diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        washer_dim = get_washer_dimensions(diameter)
        outer_d = washer_dim["outer_diameter"] if washer_dim else diameter + 10
        thickness = washer_dim["thickness"] if washer_dim else 3
        type_name = f"Washer_M{diameter}_OD{outer_d}"
        ifc = get_ifcopenshell()

        washer_type = self.ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            ElementType="WASHER",
            PredefinedType="USERDEFINED",
        )

        # Делегируем построение геометрии в GeometryBuilder
        shape_rep = self.builder.create_washer_solid(diameter, outer_d, thickness)
        self.builder.associate_representation(washer_type, shape_rep)

        # Создаём материал и ассоциируем с типом
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category="Steel", material_key=material
        )
        self.material_manager.associate_material(washer_type, mat)

        self.types_cache[key] = washer_type
        return washer_type

    def get_or_create_plate_type(self, diameter: int, material: str) -> Any:
        """
        Создание/получение типа анкерной плиты с RepresentationMap.

        Args:
            diameter: Диаметр болта (мм)
            material: Материал

        Returns:
            IfcMechanicalFastenerType для плиты
        """
        key = ("plate", diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        from data import get_plate_dimensions

        plate_dim = get_plate_dimensions(diameter)
        if not plate_dim:
            raise ValueError(f"Анкерная плита для диаметра М{diameter} не найдена")

        width = plate_dim["width"]
        thickness = plate_dim["thickness"]
        hole_d = plate_dim["hole_d"]

        type_name = f"Plate_M{diameter}_B{width}_S{thickness}"
        ifc = get_ifcopenshell()

        plate_type = self.ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            ElementType="ANCHORPLATE",
            PredefinedType="USERDEFINED",
        )

        # Создание геометрии
        shape_rep = self.builder.create_plate_solid(diameter, width, thickness, hole_d)
        self.builder.associate_representation(plate_type, shape_rep)

        # Создание материала и ассоциация
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category="Steel", material_key=material
        )
        self.material_manager.associate_material(plate_type, mat)

        self.types_cache[key] = plate_type
        return plate_type

    def get_or_create_assembly_type(self, bolt_type, diameter, material):
        """Создание/получение типа сборки"""
        key = ("assembly", bolt_type, diameter, material)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f"AnchorBoltAssembly_{bolt_type}_M{diameter}_{material}"
        ifc = get_ifcopenshell()

        assembly_type = self.ifc.create_entity(
            "IfcMechanicalFastenerType",
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name=type_name,
            PredefinedType="ANCHORBOLT",
        )

        # Создаём материал сборки (MaterialList)
        mat_name = get_material_name(material)
        mat = self.material_manager.get_material(mat_name)
        if mat:
            # Создаём список материалов для сборки (шпилька + гайки + шайбы)
            material_list = self.material_manager.create_material_list(
                [mat, mat, mat]  # Все компоненты из одного материала
            )
            self.material_manager.associate_material(assembly_type, material_list)

        # Сборка не имеет собственной геометрии
        self.types_cache[key] = assembly_type
        return assembly_type

    def get_cached_types_count(self):
        """Количество закэшированных типов"""
        return len(self.types_cache)

    def get_cached_materials_count(self):
        """Количество закэшированных материалов"""
        return self.material_manager.get_cached_materials_count()

    def get_representation_map(
        self,
        component_type: str,
        diameter: int,
        length: Optional[int] = None,
        bolt_type: Optional[str] = None,
    ):
        """
        Получение RepresentationMap для компонента

        Args:
            component_type: Тип компонента ('stud', 'nut', 'washer')
            diameter: Диаметр (мм)
            length: Длина (мм) - только для stud
            bolt_type: Тип болта - только для stud

        Returns:
            IfcRepresentationMap или None
        """
        geom_key: Any
        if component_type == "stud":
            geom_key = ("stud", bolt_type, diameter, length)
        else:
            geom_key = (component_type, diameter)

        return self.representation_maps.get(geom_key)
