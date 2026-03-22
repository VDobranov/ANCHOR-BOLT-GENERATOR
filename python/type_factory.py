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

    def __init__(
        self, ifc_doc: IfcDocumentProtocol, geometry_type: str = "solid"
    ):
        self.ifc: IfcDocumentProtocol = ifc_doc
        self.types_cache: Dict[Any, Any] = {}
        self.representation_maps: Dict[tuple, Any] = {}  # Кэш RepresentationMap по ключу
        self.builder = GeometryBuilder(ifc_doc)
        self.material_manager = MaterialManager(ifc_doc)
        self.geometry_type = geometry_type  # "solid" или "faceted"
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

        # Маппинг типа болта в позицию {t}
        type_map = {"1.1": "1", "1.2": "2", "2.1": "3", "5": "7"}
        t = type_map.get(bolt_type, bolt_type)
        type_name = f"Шпилька {t}.М{diameter}×{length} {material} ГОСТ 24379.1-2012"
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

        # Конвертация в faceted если нужно
        if self.geometry_type == "faceted":
            shape_rep = self._create_faceted_representation(shape_rep)

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

        # Конвертация в faceted если нужно
        if self.geometry_type == "faceted":
            shape_rep = self._create_faceted_representation(shape_rep)

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
        type_name = f"Шайба М{diameter} ГОСТ 24379.1-2012"
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

        # Конвертация в faceted если нужно
        if self.geometry_type == "faceted":
            shape_rep = self._create_faceted_representation(shape_rep)

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

        type_name = f"Плита {width} ГОСТ 24379.1-2012"
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

        # Конвертация в faceted если нужно
        if self.geometry_type == "faceted":
            shape_rep = self._create_faceted_representation(shape_rep)

        self.builder.associate_representation(plate_type, shape_rep)

        # Создание материала и ассоциация
        mat_name = get_material_name(material)
        mat = self.material_manager.create_material(
            mat_name, category="Steel", material_key=material
        )
        self.material_manager.associate_material(plate_type, mat)

        self.types_cache[key] = plate_type
        return plate_type

    def get_or_create_assembly_type(
        self,
        bolt_type: str,
        diameter: int,
        length: int,
        material: str,
        assembly_class: str = "IfcMechanicalFastener",
    ):
        """
        Создание или получение типа сборки

        Args:
            bolt_type: Тип болта
            diameter: Диаметр
            length: Длина
            material: Материал
            assembly_class: Класс сборки ('IfcMechanicalFastener' или 'IfcElementAssembly')

        Returns:
            IfcMechanicalFastenerType или IfcElementAssemblyType
        """
        key = ("assembly", bolt_type, diameter, length, material, assembly_class)
        if key in self.types_cache:
            return self.types_cache[key]

        type_name = f"Болт {bolt_type}.М{diameter}×{length} {material} ГОСТ 24379.1-2012"
        ifc = get_ifcopenshell()

        # Выбираем тип в зависимости от assembly_class
        if assembly_class == "IfcElementAssembly":
            assembly_type = self.ifc.create_entity(
                "IfcElementAssemblyType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=self.owner_history,
                Name=type_name,
                PredefinedType="USERDEFINED",
                ElementType="ANCHORBOLT",
            )
        else:
            assembly_type = self.ifc.create_entity(
                "IfcMechanicalFastenerType",
                GlobalId=ifc.guid.new(),
                OwnerHistory=self.owner_history,
                Name=type_name,
                PredefinedType="ANCHORBOLT",
            )

        # Создаём материал сборки
        # Согласно IFC102: IfcMaterialList deprecated в IFC4
        # Используем прямой IfcMaterial вместо списка
        mat_name = get_material_name(material)
        mat = self.material_manager.get_material(mat_name)
        if mat:
            # Ассоциируем материал напрямую (без IfcMaterialList)
            self.material_manager.associate_material(assembly_type, mat)

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

    def _create_faceted_representation(self, solid_representation):
        """
        Создание IfcFacetedBrep из solid representation

        Заменяет solid геометрию в RepresentationMaps на faceted.

        Args:
            solid_representation: IfcShapeRepresentation с solid геометрией

        Returns:
            IfcShapeRepresentation с IfcFacetedBrep (тот же объект что и solid_representation)
        """
        import ifcopenshell
        import ifcopenshell.geom
        from ifcopenshell.util.shape_builder import ShapeBuilder

        shape_builder = ShapeBuilder(self.ifc)

        # Создаём временный продукт для извлечения mesh
        context = solid_representation.ContextOfItems

        temp_shape_rep = self.ifc.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="SolidModel",
            Items=[solid_representation.Items[0]],
        )

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
                "IfcProductDefinitionShape", Representations=[temp_shape_rep]
            ),
        )

        # Извлекаем mesh через ifcopenshell.geom
        # WELD_VERTICES=False чтобы избежать несвязных рёбер (BRP002)
        settings = ifcopenshell.geom.settings()
        settings.set(settings.WELD_VERTICES, False)
        settings.set(settings.USE_WORLD_COORDS, True)

        shape = ifcopenshell.geom.create_shape(settings, temp_product)

        # Удаляем временный продукт и всю цепочку связанных сущностей
        # Используем remove_deep2 с do_not_delete для защиты контекста
        # Контекст используется в других представлениях, поэтому не должен быть удалён
        import ifcopenshell.util.element
        
        context = temp_shape_rep.ContextOfItems
        ifcopenshell.util.element.remove_deep2(
            self.ifc, 
            temp_product,
            do_not_delete={context}
        )

        if shape and len(shape.geometry.verts) > 0:
            verts = shape.geometry.verts
            faces = shape.geometry.faces

            # Масштабируем из метров в миллиметры
            verts_mm = [v * 1000.0 for v in verts]

            points = [tuple(verts_mm[i : i + 3]) for i in range(0, len(verts_mm), 3)]
            triangles = [list(faces[i : i + 3]) for i in range(0, len(faces), 3)]

            faceted_brep = shape_builder.faceted_brep(points, triangles)

            # Заменяем Items в оригинальном RepresentationMaps на faceted_brep
            # Это важно чтобы solid геометрия не оставалась в файле
            old_items = list(solid_representation.Items)
            solid_representation.Items = [faceted_brep]
            solid_representation.RepresentationType = "Brep"

            # Удаляем неиспользуемые solid сущности и всю их геометрию
            # Используем ifcopenshell.util.element.remove_deep2() с also_consider
            # also_consider=[solid_representation] чтобы traverse() не шёл через него на faceted_brep
            import ifcopenshell.util.element
            
            for item in old_items:
                try:
                    # also_consider включает solid_representation в подграф
                    # Это предотвращает переход traverse() на faceted_brep через solid_representation
                    ifcopenshell.util.element.remove_deep2(self.ifc, item, also_consider=[solid_representation])
                except Exception:
                    pass  # Некоторые сущности могут использоваться в других местах

            return solid_representation
