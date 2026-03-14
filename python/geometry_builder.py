"""
geometry_builder.py — Построение IFC геометрии
Использует ifcopenshell.util.shape_builder для стандартного API

Workaround для циклического импорта VectorType (IfcOpenShell #7562):
Создаём mock VectorType перед импортом shape_builder
"""

import math
import sys
import types
from typing import Any, Sequence

# Workaround: создаём mock VectorType перед импортом shape_builder
if 'ifcopenshell.util.shape_builder' not in sys.modules:
    _mock_sb = types.ModuleType('ifcopenshell.util.shape_builder')
    _mock_sb.VectorType = Any
    _mock_sb.V = lambda *coords: [float(c) for c in coords]
    sys.modules['ifcopenshell.util.shape_builder'] = _mock_sb

from utils import get_ifcopenshell
from ifcopenshell.util.representation import get_context

# Удаляем mock и импортируем реальный модуль
del sys.modules['ifcopenshell.util.shape_builder']
from ifcopenshell.util.shape_builder import ShapeBuilder

# Экспортируем V для использования в других модулях
V = lambda *coords: [float(c) for c in coords]


class GeometryBuilder:
    """Построитель IFC геометрии с использованием shape_builder"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc
        self.builder = ShapeBuilder(ifc_doc)
        self._context = None

    def _get_context(self):
        """Получение или создание геометрического контекста"""
        if self._context:
            return self._context

        # Пробуем получить контекст через get_context
        self._context = get_context(self.ifc, "Model", "Body", "MODEL_VIEW")
        
        # Если контекст не найден, создаём вручную
        if self._context is None:
            contexts = self.ifc.by_type('IfcGeometricRepresentationContext')
            if contexts:
                self._context = contexts[0]
            else:
                # Создаём новый контекст
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
        """Создание IfcPolyline между двумя точками через shape_builder"""
        return self.builder.polyline([V(*point1), V(*point2)])

    def _calculate_tangent_point(self, center_x, center_z, diameter, point_x, point_z):
        """
        Находит точку касания окружности из внешней точки.
        Возвращает точку касания с меньшим X (дуга против часовой стрелки).
        
        Args:
            center_x, center_z: Координаты центра окружности
            diameter: Диаметр окружности
            point_x, point_z: Координаты внешней точки
            
        Returns:
            (x, y, z): Точка касания
        """
        rad = diameter / 2

        # Вектор от центра окружности к внешней точке
        dx = point_x - center_x
        dz = point_z - center_z
        d = math.sqrt(dx**2 + dz**2)

        # Проверка: точка внутри или на окружности
        if d < rad:
            raise ValueError("Внешняя точка внутри окружности, касательные невозможны.")
        elif math.isclose(d, rad):
            return (point_x, 0., point_z)  # Точка на окружности

        # Угол между радиусом и линией к внешней точке
        alpha_C = math.acos(rad / d)

        # Угол линии от центра к внешней точке
        theta = math.atan2(dz, dx)

        # Углы двух точек касания
        angle_T1 = theta - alpha_C
        angle_T2 = theta + alpha_C

        # Координаты точек касания (в системе центра)
        T1_x = center_x + rad * math.cos(angle_T1)
        T1_z = center_z + rad * math.sin(angle_T1)
        T2_x = center_x + rad * math.cos(angle_T2)
        T2_z = center_z + rad * math.sin(angle_T2)

        # Возвращаем точку с меньшим X
        if T1_x < T2_x:
            return (T1_x, 0., T1_z)
        else:
            return (T2_x, 0., T2_z)

    def _get_arc_vertex(self, p1, p2, r, large_arc=False):
        """
        Вычисляет вершину дуги по двум точкам и радиусу.
        Дуга строится против часовой стрелки от p1 к p2.
        
        Args:
            p1: Начальная точка (x1, y1, z1)
            p2: Конечная точка (x2, y2, z2)
            r: Радиус дуги
            large_arc: Если True, используется большая дуга
            
        Returns:
            (x, y, z): Вершина дуги
        """
        x1, y1, z1 = p1
        x2, y2, z2 = p2

        # Вектор между точками
        dx, dz = x2 - x1, z2 - z1
        d = math.sqrt(dx**2 + dz**2)

        if d == 0:
            raise ValueError("Точки p1 и p2 совпадают.")
        if d > 2 * r:
            raise ValueError("Расстояние между точками больше диаметра дуги.")

        # Середина хорды
        xm, zm = (x1 + x2) / 2, (z1 + z2) / 2

        # Расстояние от центра до хорды
        h = math.sqrt(r**2 - (d / 2)**2)

        # Центр дуги (перпендикуляр к хорде)
        cx = xm - h * dz / d
        cz = zm + h * dx / d

        # Единичный вектор от центра дуги к середине хорды
        vx_dir = (xm - cx) / h
        vz_dir = (zm - cz) / h

        # Вершина дуги (большая дуга — противоположная сторона)
        if large_arc:
            return (cx - vx_dir * r, 0., cz - vz_dir * r)
        else:
            return (cx + vx_dir * r, 0., cz + vz_dir * r)

    def _calculate_stud_points_type_1_2(self, d, L, l1, l2, l3, r):
        """
        Расчёт 6 точек для шпильки типа 1.2.
        
        Args:
            d: Диаметр болта
            L: Длина болта
            l1: Длина верхнего участка (из крюка)
            l2: Длина нижнего горизонтального участка
            l3: Длина нижнего участка (радиус загиба)
            r: Радиус загиба
            
        Returns:
            Список из 6 точек [[x1,y1,z1], ..., [x6,y6,z6]]
        """
        # Точка 1: начало
        p1 = [0., 0., 0.]
        
        # Точка 2: конец вертикального участка
        p2 = [0., 0., float(-L + l1)]
        
        # Центр дуги загиба
        bend_center_x = float(-l3 + d + r)
        bend_center_z = float(-L + d + r)
        
        # Точка 3: точка касания дуги (рассчитывается через tangent point)
        # Используем диаметр пути центра трубы: r*2 + d
        p3_tup = self._calculate_tangent_point(bend_center_x, bend_center_z, r*2 + d, 0., p2[2])
        p3 = [float(p3_tup[0]), 0., float(p3_tup[2])]
        
        # Точка 5: центр дуги пути центра трубы
        p5 = [bend_center_x, 0., float(bend_center_z - r - d/2)]
        
        # Точка 4: вершина дуги
        p4_tup = self._get_arc_vertex(tuple(p3), tuple(p5), r + d/2)
        p4 = [float(p4_tup[0]), 0., float(p4_tup[2])]
        
        # Точка 6: конец горизонтального участка
        p6 = [float(l2 - l3), 0., p5[2]]
        
        return [p1, p2, p3, p4, p5, p6]

    def create_composite_curve_stud(self, bolt_type, diameter, length):
        """
        Создание составной кривой для шпильки через shape_builder.polyline()

        Для типа 1.1: подход BlenderBIM (AGGREGATE_FBOLTS.py)
        - IfcIndexedPolyCurve с IfcCartesianPointList3D
        - IfcLineIndex + IfcArcIndex + IfcLineIndex
        - 5 точек: p1(0,0,0), p2(0,0,-Ll+r), p3(r-r/√2, 0, -Ll+r-r/√2), p4(r,0,-Ll), p5(r+L0,0,-Ll)

        Для типа 1.2: точный алгоритм с IfcIndexedPolyCurve
        - 6 точек с точным расчётом касательной и вершины дуги
        - IfcLineIndex((1,2,3)), IfcArcIndex((3,4,5)), IfcLineIndex((5,6))

        Для типа 2.1, 5: прямая линия
        """
        from gost_data import get_bolt_bend_radius, get_bolt_l1, get_bolt_l2, get_bolt_l3, get_thread_length, get_bolt_hook_length

        # Для типа 1.1 используем подход BlenderBIM
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

            # shape_builder.polyline с arc_points=[2] (индекс средней точки дуги)
            points = [V(*p1), V(*p2), V(*p3), V(*p4), V(*p5)]
            return self.builder.polyline(points, arc_points=[2])

        # Для типа 1.2 используем точный алгоритм
        if bolt_type == '1.2':
            R = get_bolt_bend_radius(diameter, length) or diameter
            r = R + diameter / 2.0  # Радиус пути центра трубы
            l1 = get_bolt_l1(diameter, length) or 0
            l2 = get_bolt_l2(diameter, length) or 0
            l3 = get_bolt_l3(diameter, length) or R

            # Расчёт 6 точек для типа 1.2
            points = self._calculate_stud_points_type_1_2(diameter, length, l1, l2, l3, R)

            # shape_builder.polyline с arc_points=[3] (индекс средней точки дуги p4)
            points_v = [V(*p) for p in points]
            return self.builder.polyline(points_v, arc_points=[3])

        # Для типов 2.1, 5 - прямая шпилька
        # Простая линия от (0, 0, length) до (0, 0, 0)
        points = [V(0.0, 0.0, float(length)), V(0.0, 0.0, 0.0)]
        return self.builder.polyline(points)

    def create_swept_disk_solid(self, axis_curve, radius):
        """Создание IfcSweptDiskSolid через shape_builder"""
        return self.builder.create_swept_disk_solid(axis_curve, float(radius))

    def create_straight_stud_solid(self, diameter, length):
        """Создание цилиндра для прямой шпильки через shape_builder.extrude()"""
        context = self._get_context()

        # Создаём круглый профиль и экструзию
        circle = self.builder.circle((0.0, 0.0), diameter / 2.0)
        profile = self.builder.profile(circle)
        swept_area = self.builder.extrude(profile, magnitude=length)

        return self._create_shape_representation(context, swept_area)

    def create_bent_stud_solid(self, bolt_type, diameter, length):
        """Создание геометрии изогнутой шпильки через IfcSweptDiskSolid"""
        context = self._get_context()

        axis_curve = self.create_composite_curve_stud(bolt_type, diameter, length)
        swept_area = self.create_swept_disk_solid(axis_curve, diameter / 2.0)

        return self._create_shape_representation(context, swept_area)

    def create_nut_solid(self, diameter, height):
        """Создание геометрии гайки (шестиугольник с отверстием) через shape_builder"""
        from gost_data import get_nut_dimensions

        context = self._get_context()

        # Получаем размер под ключ из DIM.py
        nut_dim = get_nut_dimensions(diameter)
        s_width = nut_dim['s_width'] if nut_dim else diameter * 1.5

        # Размер под ключ (S) — расстояние между параллельными гранями
        # Радиус описанной окружности (до вершин): R = S / √3
        outer_radius = s_width / math.sqrt(3)
        inner_radius = diameter / 2.0 + 0.5

        # Внешний шестиугольник через polyline
        hex_points = []
        for i in range(6):
            angle = i * math.pi / 3
            x = outer_radius * math.cos(angle)
            y = outer_radius * math.sin(angle)
            hex_points.append(V(x, y))

        outer_curve = self.builder.polyline(hex_points, closed=True)

        # Внутреннее отверстие (круг)
        inner_circle = self.builder.circle((0.0, 0.0), inner_radius)

        # Профиль с отверстием
        profile = self.builder.profile(outer_curve, inner_curves=[inner_circle])

        # Экструзия
        swept_area = self.builder.extrude(profile, magnitude=height)

        return self._create_shape_representation(context, swept_area)

    def create_washer_solid(self, inner_diameter, outer_diameter, thickness):
        """Создание геометрии шайбы (кольцо) через shape_builder"""
        context = self._get_context()
        inner_radius = inner_diameter / 2.0 + 0.5
        outer_radius = outer_diameter / 2.0

        # Внешний и внутренний круги
        outer_circle = self.builder.circle((0.0, 0.0), outer_radius)
        inner_circle = self.builder.circle((0.0, 0.0), inner_radius)

        # Профиль с отверстием
        profile = self.builder.profile(outer_circle, inner_curves=[inner_circle])

        # Экструзия
        swept_area = self.builder.extrude(profile, magnitude=thickness)

        return self._create_shape_representation(context, swept_area)

    def _create_shape_representation(self, context, swept_area):
        """Создание IfcShapeRepresentation и IfcProductDefinitionShape через shape_builder"""
        shape_rep = self.builder.get_representation(context, [swept_area], "SweptSolid")
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
