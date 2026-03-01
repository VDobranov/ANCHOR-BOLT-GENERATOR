"""
geometry_builder.py — Построение IFC геометрии
Кривые, профили, выдавливание
"""

import math
from utils import get_ifcopenshell


class GeometryBuilder:
    """Построитель IFC геометрии"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self._context = None

    @staticmethod
    def to_float_list(coordinates):
        """Конвертация координат в список float"""
        return [float(x) for x in coordinates]

    def _get_context(self):
        """Получение или создание геометрического контекста"""
        if self._context:
            return self._context

        contexts = self.ifc.by_type('IfcGeometricRepresentationContext')
        if contexts:
            self._context = contexts[0]
            return self._context

        self._context = self.ifc.create_entity('IfcGeometricRepresentationContext',
            ContextType='Model',
            CoordinateSpaceDimension=3,
            Precision=1e-05,
            WorldCoordinateSystem=self.ifc.create_entity('IfcAxis2Placement3D',
                Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
            )
        )
        return self._context

    def create_line(self, point1, point2):
        """Создание IfcPolyline между двумя точками"""
        p1 = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list(point1)
        )
        p2 = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list(point2)
        )
        return self.ifc.create_entity('IfcPolyline', Points=[p1, p2])

    def create_composite_curve_stud(self, bolt_type, diameter, length, execution=1):
        """
        Создание составной кривой для шпильки
        
        Для типа 1.1: подход BlenderBIM (AGGREGATE_FBOLTS.py)
        - IfcIndexedPolyCurve с IfcCartesianPointList3D
        - IfcLineIndex + IfcArcIndex + IfcLineIndex
        - 5 точек: p1(0,0,0), p2(0,0,-Ll+r), p3(r-r/√2, 0, -Ll+r-r/√2), p4(r,0,-Ll), p5(r+L0,0,-Ll)
        
        Для типа 1.2, 2.1, 5: старый подход с IfcCompositeCurve
        """
        from gost_data import get_bolt_bend_radius, get_thread_length, get_bolt_hook_length

        # ТОЛЬКО для типа 1.1 используем новый подход BlenderBIM
        if bolt_type == '1.1':
            R = get_bolt_bend_radius(diameter, length) or diameter
            r = R + diameter / 2.0  # Радиус пути центра трубы
            Ll = length - diameter / 2.0
            L0 = get_thread_length(diameter, length) or 0
            L2 = get_bolt_hook_length(diameter, length) or 0

            # 5 точек как в BlenderBIM
            p1 = [0.0, 0.0, 0.0]
            p2 = [0.0, 0.0, -Ll + r]
            p3 = [r - r / math.sqrt(2), 0.0, -Ll + r - r / math.sqrt(2)]
            p4 = [r, 0.0, -Ll]
            p5 = [r + L2, 0.0, -Ll]

            # IfcCartesianPointList3D
            point_list = self.ifc.create_entity('IfcCartesianPointList3D',
                CoordList=[p1, p2, p3, p4, p5]
            )

            # Сегменты: линия + дуга + линия (как в BlenderBIM)
            # IfcSegmentIndexSelect - в ifcopenshell это entity instances
            # Для IfcIndexedPolyCurve.Segments нужен список entity instances
            line1 = self.ifc.create_entity('IfcLineIndex', [1, 2])
            arc = self.ifc.create_entity('IfcArcIndex', [2, 3, 4])
            line2 = self.ifc.create_entity('IfcLineIndex', [4, 5])

            # IfcIndexedPolyCurve
            return self.ifc.create_entity('IfcIndexedPolyCurve',
                Points=point_list,
                Segments=[line1, arc, line2],
                SelfIntersect=False
            )

        # Для типов 1.2, 2.1, 5 - старый подход
        segments = []
        has_bend = bolt_type in ['1.1', '1.2']

        if has_bend:
            radius = get_bolt_bend_radius(diameter, length) or diameter
            upper_length = length - radius

            # Верхняя вертикальная линия
            line1 = self.create_line([0.0, 0.0, float(length)], [0.0, 0.0, float(upper_length)])
            seg1 = self.ifc.create_entity('IfcCompositeCurveSegment',
                Transition='CONTINUOUS', SameSense=True, ParentCurve=line1
            )
            segments.append(seg1)

            # Дуга (аппроксимированная полилинией)
            num_segments = 12
            arc_points = []

            # Начальная точка дуги
            arc_points.append(self.ifc.create_entity('IfcCartesianPoint',
                Coordinates=[0.0, 0.0, float(upper_length)]
            ))

            # Промежуточные точки
            for i in range(1, num_segments):
                angle = (math.pi / 2) * (i / num_segments)
                x = radius * (1 - math.cos(angle))
                z = length - radius - radius * math.sin(angle)
                arc_points.append(self.ifc.create_entity('IfcCartesianPoint',
                    Coordinates=[x, 0.0, z]
                ))

            # Конечная точка дуги
            arc_points.append(self.ifc.create_entity('IfcCartesianPoint',
                Coordinates=[float(radius), 0.0, float(length - 2 * radius)]
            ))

            arc_polyline = self.ifc.create_entity('IfcPolyline', Points=arc_points)
            seg2 = self.ifc.create_entity('IfcCompositeCurveSegment',
                Transition='CONTINUOUS', SameSense=True, ParentCurve=arc_polyline
            )
            segments.append(seg2)

            # Нижняя горизонтальная линия
            line2 = self.create_line(
                [float(radius), 0.0, float(length - 2 * radius)],
                [float(radius), 0.0, 0.0]
            )
            seg3 = self.ifc.create_entity('IfcCompositeCurveSegment',
                Transition='CONTINUOUS', SameSense=True, ParentCurve=line2
            )
            segments.append(seg3)
        else:
            # Прямая шпилька
            line = self.create_line([0.0, 0.0, float(length)], [0.0, 0.0, 0.0])
            seg = self.ifc.create_entity('IfcCompositeCurveSegment',
                Transition='CONTINUOUS', SameSense=True, ParentCurve=line
            )
            segments.append(seg)

        return self.ifc.create_entity('IfcCompositeCurve',
            Segments=segments, SelfIntersect=False
        )

    def create_swept_disk_solid(self, axis_curve, radius):
        """Создание IfcSweptDiskSolid"""
        return self.ifc.create_entity('IfcSweptDiskSolid',
            Directrix=axis_curve,
            Radius=float(radius)
        )

    def create_straight_stud_solid(self, diameter, length):
        """Создание цилиндра для прямой шпильки через IfcExtrudedAreaSolid"""
        context = self._get_context()
        
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        )
        profile = self.ifc.create_entity('IfcCircleProfileDef',
            ProfileType='AREA',
            ProfileName='CircularProfile',
            Radius=diameter / 2.0
        )
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=placement,
            ExtrudedDirection=direction,
            Depth=length
        )
        
        return self._create_shape_representation(context, swept_area)

    def create_bent_stud_solid(self, bolt_type, diameter, length, execution):
        """Создание геометрии изогнутой шпильки через IfcSweptDiskSolid"""
        context = self._get_context()
        
        axis_curve = self.create_composite_curve_stud(bolt_type, diameter, length, execution)
        swept_area = self.ifc.create_entity('IfcSweptDiskSolid',
            Directrix=axis_curve,
            Radius=float(diameter / 2.0)
        )
        
        return self._create_shape_representation(context, swept_area)

    def create_nut_solid(self, diameter, height):
        """Создание геометрии гайки (шестиугольник с отверстием)"""
        from gost_data import get_nut_dimensions
        
        context = self._get_context()
        
        # Получаем размер под ключ из DIM.py
        nut_dim = get_nut_dimensions(diameter)
        s_width = nut_dim['s_width'] if nut_dim else diameter * 1.5
        
        # Размер под ключ (S) — расстояние между параллельными гранями
        # Радиус описанной окружности (до вершин): R = S / √3
        outer_radius = s_width / math.sqrt(3)
        inner_radius = diameter / 2.0 + 0.5
        
        # Внешний шестиугольник
        outer_points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            outer_points.append(self.ifc.create_entity('IfcCartesianPoint', Coordinates=[x, y]))
        outer_points.append(outer_points[0])
        
        outer_polyline = self.ifc.create_entity('IfcPolyline', Points=outer_points)
        
        # Внутреннее отверстие
        inner_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])
        inner_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=inner_center),
            Radius=inner_radius
        )
        
        # Профиль с отверстием
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            ProfileName='HexNutProfile',
            OuterCurve=outer_polyline,
            InnerCurves=[inner_circle]
        )
        
        # Экструзия
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        )
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=placement,
            ExtrudedDirection=direction,
            Depth=height
        )
        
        return self._create_shape_representation(context, swept_area)

    def create_washer_solid(self, inner_diameter, outer_diameter, thickness):
        """Создание геометрии шайбы (кольцо)"""
        context = self._get_context()
        inner_radius = inner_diameter / 2.0 + 0.5
        outer_radius = outer_diameter / 2.0
        
        center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])
        
        outer_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
            Radius=outer_radius
        )
        inner_circle = self.ifc.create_entity('IfcCircle',
            Position=self.ifc.create_entity('IfcAxis2Placement2D', Location=center),
            Radius=inner_radius
        )
        
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            ProfileName='WasherProfile',
            OuterCurve=outer_circle,
            InnerCurves=[inner_circle]
        )
        
        placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
        )
        direction = self.ifc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0])
        swept_area = self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=placement,
            ExtrudedDirection=direction,
            Depth=thickness
        )
        
        return self._create_shape_representation(context, swept_area)

    def _create_shape_representation(self, context, swept_area):
        """Создание IfcShapeRepresentation и IfcProductDefinitionShape"""
        shape_rep = self.ifc.create_entity('IfcShapeRepresentation',
            ContextOfItems=context,
            RepresentationIdentifier='Body',
            RepresentationType='SweptSolid',
            Items=[swept_area]
        )
        
        self.ifc.create_entity('IfcProductDefinitionShape',
            Representations=[shape_rep]
        )
        
        return shape_rep

    def associate_representation(self, product_type, shape_rep):
        """Ассоциация представления с типом продукта через RepresentationMap"""
        rep_maps = [m for m in self.ifc.by_type('IfcRepresentationMap')
                    if m.MappedRepresentation == shape_rep]
        
        if not rep_maps:
            rep_map = self.ifc.create_entity('IfcRepresentationMap',
                MappingOrigin=self.ifc.create_entity('IfcAxis2Placement3D',
                    Location=self.ifc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0])
                ),
                MappedRepresentation=shape_rep
            )
            
            if product_type.RepresentationMaps is None:
                product_type.RepresentationMaps = [rep_map]
            elif isinstance(product_type.RepresentationMaps, tuple):
                product_type.RepresentationMaps = list(product_type.RepresentationMaps) + [rep_map]
            else:
                product_type.RepresentationMaps.append(rep_map)
