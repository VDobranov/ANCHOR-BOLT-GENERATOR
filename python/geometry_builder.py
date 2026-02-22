"""
geometry_builder.py — Построение IFC геометрии
Кривые, профили, выдавливание
"""

import math


class GeometryBuilder:
    """Построитель IFC геометрии"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc

    @staticmethod
    def to_float_list(coordinates):
        """Конвертация координат в список float"""
        return [float(x) for x in coordinates]

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
        Для изогнутых болтов (1.1, 1.2): линия + дуга + линия
        Для прямых (2.1, 5): одна линия
        """
        segments = []
        has_bend = bolt_type in ['1.1', '1.2']

        if has_bend:
            radius = diameter * (1.5 if bolt_type == '1.1' else 2.0)
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

    def create_hexagon_profile(self, nominal_diameter, height):
        """Создание шестиугольного профиля для гайки"""
        outer_diameter = nominal_diameter * 1.5

        vertices = []
        for i in range(6):
            angle = (i * 60 - 90) * math.pi / 180.0
            x = outer_diameter / 2.0 * math.cos(angle)
            y = outer_diameter / 2.0 * math.sin(angle)
            vertices.append(self.ifc.create_entity('IfcCartesianPoint',
                Coordinates=self.to_float_list([x, y])
            ))

        outer_loop = self.ifc.create_entity('IfcPolyline',
            Points=vertices + [vertices[0]]
        )

        # Внутреннее отверстие
        hole_center = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list([0, 0])
        )
        hole_placement = self.ifc.create_entity('IfcAxis2Placement2D',
            Location=hole_center,
            RefDirection=self.ifc.create_entity('IfcDirection',
                DirectionRatios=self.to_float_list([1, 0])
            )
        )
        hole_circle = self.ifc.create_entity('IfcCircle',
            Radius=float(nominal_diameter / 2.0 + 0.5),
            Position=hole_placement
        )

        return self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            OuterCurve=outer_loop,
            InnerCurves=[hole_circle]
        )

    def create_washer_profile(self, outer_diameter, inner_diameter):
        """Создание профиля шайбы (кольцо)"""
        center = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list([0, 0])
        )

        outer_placement = self.ifc.create_entity('IfcAxis2Placement2D',
            Location=center,
            RefDirection=self.ifc.create_entity('IfcDirection',
                DirectionRatios=self.to_float_list([1, 0])
            )
        )
        outer_circle = self.ifc.create_entity('IfcCircle',
            Radius=float(outer_diameter / 2.0),
            Position=outer_placement
        )

        inner_placement = self.ifc.create_entity('IfcAxis2Placement2D',
            Location=center,
            RefDirection=self.ifc.create_entity('IfcDirection',
                DirectionRatios=self.to_float_list([1, 0])
            )
        )
        inner_circle = self.ifc.create_entity('IfcCircle',
            Radius=float(inner_diameter / 2.0),
            Position=inner_placement
        )

        return self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
            ProfileType='AREA',
            OuterCurve=outer_circle,
            InnerCurves=[inner_circle]
        )

    def create_extruded_solid(self, profile, extrusion_height, direction=(0, 0, 1)):
        """Создание IfcExtrudedAreaSolid"""
        base_point = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list([0, 0, 0])
        )
        base_placement = self.ifc.create_entity('IfcAxis2Placement3D',
            Location=base_point,
            Axis=self.ifc.create_entity('IfcDirection',
                DirectionRatios=self.to_float_list(direction)
            ),
            RefDirection=self.ifc.create_entity('IfcDirection',
                DirectionRatios=self.to_float_list([1, 0, 0])
            )
        )

        extrusion_dir = self.ifc.create_entity('IfcDirection',
            DirectionRatios=self.to_float_list(direction)
        )

        return self.ifc.create_entity('IfcExtrudedAreaSolid',
            SweptArea=profile,
            Position=base_placement,
            ExtrudedDirection=extrusion_dir,
            Depth=float(extrusion_height)
        )

    def create_swept_disk_solid(self, axis_curve, radius):
        """Создание IfcSweptDiskSolid"""
        return self.ifc.create_entity('IfcSweptDiskSolid',
            Directrix=axis_curve,
            Radius=float(radius)
        )

    def create_placement(self, location=(0, 0, 0), z_axis=(0, 0, 1), x_axis=(1, 0, 0)):
        """Создание 3D размещения"""
        location_point = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=self.to_float_list(location)
        )
        axis = self.ifc.create_entity('IfcDirection',
            DirectionRatios=self.to_float_list(z_axis)
        )
        ref_direction = self.ifc.create_entity('IfcDirection',
            DirectionRatios=self.to_float_list(x_axis)
        )

        return self.ifc.create_entity('IfcAxis2Placement3D',
            Location=location_point, Axis=axis, RefDirection=ref_direction
        )


# Convenience functions
def create_stud_representation(ifc_doc, bolt_type, diameter, length, execution=1):
    """Создание представления шпильки"""
    builder = GeometryBuilder(ifc_doc)
    axis_curve = builder.create_composite_curve_stud(bolt_type, diameter, length, execution)
    return builder.create_swept_disk_solid(axis_curve, diameter / 2.0)


def create_nut_representation(ifc_doc, diameter, height):
    """Создание представления гайки"""
    builder = GeometryBuilder(ifc_doc)
    profile = builder.create_hexagon_profile(diameter, height)
    return builder.create_extruded_solid(profile, height)


def create_washer_representation(ifc_doc, outer_diameter, inner_diameter, thickness):
    """Создание представления шайбы"""
    builder = GeometryBuilder(ifc_doc)
    profile = builder.create_washer_profile(outer_diameter, inner_diameter)
    return builder.create_extruded_solid(profile, thickness)
