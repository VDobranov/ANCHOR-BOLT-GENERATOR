"""
geometry_builder.py — Построение IFC геометрии
Использует ifcopenshell.util.shape_builder для стандартного API

Согласно документации IfcOpenShell:
- ShapeBuilder предоставляет стандартное API для построения геометрии
- V — функция для создания векторов координат
"""

import math
from typing import Any, List, Optional, Tuple

from ifcopenshell.util.representation import get_context
from ifcopenshell.util.shape_builder import ShapeBuilder, V


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
            contexts = self.ifc.by_type("IfcGeometricRepresentationContext")
            if contexts:
                self._context = contexts[0]
            else:
                # Создаём новый контекст
                self._context = self.ifc.create_entity(
                    "IfcGeometricRepresentationContext",
                    ContextType="Model",
                    CoordinateSpaceDimension=3,
                    Precision=1e-05,
                    WorldCoordinateSystem=self.ifc.create_entity(
                        "IfcAxis2Placement3D",
                        Location=self.ifc.create_entity(
                            "IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0]
                        ),
                    ),
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
            return (point_x, 0.0, point_z)  # Точка на окружности

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
            return (T1_x, 0.0, T1_z)
        else:
            return (T2_x, 0.0, T2_z)

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
        h = math.sqrt(r**2 - (d / 2) ** 2)

        # Центр дуги (перпендикуляр к хорде)
        cx = xm - h * dz / d
        cz = zm + h * dx / d

        # Единичный вектор от центра дуги к середине хорды
        vx_dir = (xm - cx) / h
        vz_dir = (zm - cz) / h

        # Вершина дуги (большая дуга — противоположная сторона)
        if large_arc:
            return (cx - vx_dir * r, 0.0, cz - vz_dir * r)
        else:
            return (cx + vx_dir * r, 0.0, cz + vz_dir * r)

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
        p1 = [0.0, 0.0, 0.0]

        # Точка 2: конец вертикального участка
        p2 = [0.0, 0.0, float(-L + l1)]

        # Центр дуги загиба
        bend_center_x = float(-l3 + d + r)
        bend_center_z = float(-L + d + r)

        # Точка 3: точка касания дуги (рассчитывается через tangent point)
        # Используем диаметр пути центра трубы: r*2 + d
        p3_tup = self._calculate_tangent_point(bend_center_x, bend_center_z, r * 2 + d, 0.0, p2[2])
        p3 = [float(p3_tup[0]), 0.0, float(p3_tup[2])]

        # Точка 5: центр дуги пути центра трубы
        p5 = [bend_center_x, 0.0, float(bend_center_z - r - d / 2)]

        # Точка 4: вершина дуги
        p4_tup = self._get_arc_vertex(tuple(p3), tuple(p5), r + d / 2)
        p4 = [float(p4_tup[0]), 0.0, float(p4_tup[2])]

        # Точка 6: конец горизонтального участка
        p6 = [float(l2 - l3), 0.0, p5[2]]

        return [p1, p2, p3, p4, p5, p6]

    def create_composite_curve_stud(self, bolt_type, diameter, length, position=None):
        """
        Создание составной кривой для шпильки через shape_builder.polyline()

        Для типа 1.1: подход BlenderBIM (AGGREGATE_FBOLTS.py)
        - IfcIndexedPolyCurve с IfcCartesianPointList3D
        - IfcLineIndex + IfcArcIndex + IfcLineIndex
        - 5 точек: p1(0,0,0), p2(0,0,-Ll+r), p3(r-r/√2, 0, -Ll+r-r/√2), p4(r,0,-Ll), p5(r+L0,0,-Ll)

        Для типа 1.2: точный алгоритм с IfcIndexedPolyCurve
        - 6 точек с точным расчётом касательной и вершины дуги
        - IfcLineIndex((1,2,3)), IfcArcIndex((3,4,5)), IfcLineIndex((5,6))

        Для типа 2.1: прямая линия от (0, 0, length) до (0, 0, 0)

        Для типа 5 (прямой болт): прямая линия длиной L с резьбой l0
        - Низ резьбы в Z=0 (аналогично типам 1.1 и 1.2)
        - Верх шпильки (конец резьбы): Z = +l0
        - Низ шпильки: Z = -(L - l0)
        - Общая длина: l0 + (L - l0) = L
        """
        from gost_data import (
            get_bolt_bend_radius,
            get_bolt_hook_length,
            get_bolt_l1,
            get_bolt_l2,
            get_bolt_l3,
            get_thread_length,
        )

        z_offset = position[2] if position else 0.0

        # Для типа 1.1 используем подход BlenderBIM
        if bolt_type == "1.1":
            R = get_bolt_bend_radius(diameter, length) or diameter
            r = R + diameter / 2.0  # Радиус пути центра трубы
            Ll = length - diameter / 2.0
            L0 = get_thread_length(diameter, length) or 0
            L2 = get_bolt_hook_length(diameter, length) or 0

            # 5 точек как в BlenderBIM, смещённые на z_offset
            p1 = [0.0, 0.0, 0.0 + z_offset]
            p2 = [0.0, 0.0, -Ll + r + z_offset]
            p3 = [r - r / math.sqrt(2), 0.0, -Ll + r - r / math.sqrt(2) + z_offset]
            p4 = [r, 0.0, -Ll + z_offset]
            p5 = [r + L2, 0.0, -Ll + z_offset]

            # shape_builder.polyline с arc_points=[2] (индекс средней точки дуги)
            points = [V(*p1), V(*p2), V(*p3), V(*p4), V(*p5)]
            return self.builder.polyline(points, arc_points=[2])

        # Для типа 1.2 используем точный алгоритм
        if bolt_type == "1.2":
            R = get_bolt_bend_radius(diameter, length) or diameter
            r = R + diameter / 2.0  # Радиус пути центра трубы
            l1 = get_bolt_l1(diameter, length) or 0
            l2 = get_bolt_l2(diameter, length) or 0
            l3 = get_bolt_l3(diameter, length) or R

            # Расчёт 6 точек для типа 1.2
            points = self._calculate_stud_points_type_1_2(diameter, length, l1, l2, l3, R)

            # Смещаем все точки на z_offset
            points = [[p[0], p[1], p[2] + z_offset] for p in points]

            # shape_builder.polyline с arc_points=[3] (индекс средней точки дуги p4)
            points_v = [V(*p) for p in points]
            return self.builder.polyline(points_v, arc_points=[3])

        # Для типов 2.1, 5 - прямая шпилька
        # Тип 2.1: прямая шпилька длиной L с резьбой по всей длине
        # Верх шпильки (начало резьбы) в Z=0, низ в Z=-L
        if bolt_type == "2.1":
            # Тип 2.1: прямая шпилька длиной L
            # Верх шпильки: Z = 0
            # Низ шпильки: Z = -length
            p1 = V(0.0, 0.0, 0.0 + z_offset)
            p2 = V(0.0, 0.0, float(-length) + z_offset)

            return self.builder.polyline([p1, p2])

        # Тип 5: прямая шпилька с резьбой по всей длине
        # Верх шпильки в Z=0, низ в Z=-L
        if bolt_type == "5":
            # Тип 5: прямая шпилька длиной L
            # Верх шпильки: Z = 0
            # Низ шпильки: Z = -length
            p1 = V(0.0, 0.0, 0.0 + z_offset)
            p2 = V(0.0, 0.0, float(-length) + z_offset)

            return self.builder.polyline([p1, p2])

    def create_swept_disk_solid(self, axis_curve, radius):
        """Создание IfcSweptDiskSolid через shape_builder"""
        return self.builder.create_swept_disk_solid(axis_curve, float(radius))

    def create_straight_stud_solid(self, diameter, length):
        """Создание цилиндра для прямой шпильки через shape_builder.extrude()

        Геометрия создаётся от Z=0 до Z=+length.
        Позиционирование выполняется в instance_factory через ObjectPlacement.
        """
        context = self._get_context()

        # Создаём круглый профиль в 2D (XY плоскость)
        circle = self.builder.circle((0.0, 0.0), diameter / 2.0)
        profile = self.builder.profile(circle)
        # Экструзия вверх на +length
        swept_area = self.builder.extrude(profile, magnitude=length)

        return self._create_shape_representation(context, swept_area)

    def create_plate_solid(
        self,
        diameter: int,
        width: int,
        thickness: int,
        hole_diameter: int,
    ) -> Any:
        """
        Создание 3D геометрии анкерной плиты.

        Анкерная плита — квадратная пластина с круглым отверстием в центре.
        Центр отверстия в (0, 0), плита в плоскости XY, экструзия вдоль Z.

        Args:
            diameter: Номинальный диаметр болта (мм)
            width: Длина/ширина плиты (B) (мм)
            thickness: Толщина плиты (S) (мм)
            hole_diameter: Диаметр отверстия (D) (мм)

        Returns:
            IfcShapeRepresentation с геометрией плиты
        """
        context = self._get_context()

        # Создаём квадратный профиль с отверстием
        half = width / 2.0

        # Внешний контур (квадрат)
        square_points = [
            V(-half, -half),
            V(half, -half),
            V(half, half),
            V(-half, half),
        ]
        square_curve = self.builder.polyline(square_points, closed=True)

        # Внутреннее отверстие (круг)
        hole_radius = hole_diameter / 2.0
        hole_circle = self.builder.circle((0.0, 0.0), hole_radius)

        # Профиль с отверстием
        profile = self.builder.profile(square_curve, inner_curves=[hole_circle])

        # Экструзия вдоль оси Z
        swept_area = self.builder.extrude(profile, magnitude=thickness)

        return self._create_shape_representation(context, swept_area)

    def create_bent_stud_solid(self, bolt_type, diameter, length):
        """Создание геометрии изогнутой шпильки через IfcSweptDiskSolid"""
        context = self._get_context()

        axis_curve = self.create_composite_curve_stud(bolt_type, diameter, length)
        swept_area = self.create_swept_disk_solid(axis_curve, diameter / 2.0)

        return self._create_shape_representation(context, swept_area)

    def create_bent_stud_solid_raw(self, bolt_type, diameter, length, position=None):
        """Создание IfcSweptDiskSolid для изогнутой шпильки (без IfcShapeRepresentation)"""
        axis_curve = self.create_composite_curve_stud(bolt_type, diameter, length, position)
        return self.create_swept_disk_solid(axis_curve, diameter / 2.0)

    def create_straight_stud_solid_raw(self, diameter, length, position=None):
        """Создание IfcSweptDiskSolid для прямой шпильки (без IfcShapeRepresentation)"""
        # Прямая ось от (0,0,0) до (0,0,-length) — 3D кривая
        z_offset = position[2] if position else 0.0
        axis = self.builder.polyline([V(0.0, 0.0, z_offset), V(0.0, 0.0, z_offset - length)])
        return self.create_swept_disk_solid(axis, diameter / 2.0)

    def create_nut_solid_raw(self, diameter, height, position=None):
        """Создание IfcExtrudedAreaSolid для гайки (без IfcShapeRepresentation)"""
        from gost_data import get_nut_dimensions

        # Получаем размер под ключ из DIM.py
        nut_dim = get_nut_dimensions(diameter)
        s_width = nut_dim["s_width"] if nut_dim else diameter * 1.5

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

        # Экструзия — возвращаем IfcExtrudedAreaSolid напрямую
        return self.builder.extrude(profile, magnitude=height, position=position)

    def create_washer_solid_raw(self, inner_diameter, outer_diameter, thickness, position=None):
        """Создание IfcExtrudedAreaSolid для шайбы (без IfcShapeRepresentation)"""
        inner_radius = inner_diameter / 2.0 + 0.5
        outer_radius = outer_diameter / 2.0

        # Внешний и внутренний круги
        outer_circle = self.builder.circle((0.0, 0.0), outer_radius)
        inner_circle = self.builder.circle((0.0, 0.0), inner_radius)

        # Профиль с отверстием
        profile = self.builder.profile(outer_circle, inner_curves=[inner_circle])

        # Экструзия — возвращаем IfcExtrudedAreaSolid напрямую
        return self.builder.extrude(profile, magnitude=thickness, position=position)

    def create_plate_solid_raw(self, diameter, width, thickness, hole_d, position=None):
        """Создание IfcExtrudedAreaSolid для плиты (без IfcShapeRepresentation)"""
        # Прямоугольный профиль с отверстием, центрированный вокруг (0,0)
        half = width / 2.0
        square_points = [
            V(-half, -half),
            V(half, -half),
            V(half, half),
            V(-half, half),
        ]
        rect_curve = self.builder.polyline(square_points, closed=True)
        hole_circle = self.builder.circle((0.0, 0.0), hole_d / 2.0)

        # Профиль с отверстием
        profile = self.builder.profile(rect_curve, inner_curves=[hole_circle])

        # Экструзия — возвращаем IfcExtrudedAreaSolid напрямую
        return self.builder.extrude(profile, magnitude=thickness, position=position)

    def create_nut_solid(self, diameter, height):
        """Создание геометрии гайки (шестиугольник с отверстием) через shape_builder"""
        from gost_data import get_nut_dimensions

        context = self._get_context()

        # Получаем размер под ключ из DIM.py
        nut_dim = get_nut_dimensions(diameter)
        s_width = nut_dim["s_width"] if nut_dim else diameter * 1.5

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
        """Создание IfcShapeRepresentation"""
        # Создаём IfcShapeRepresentation с обязательным RepresentationIdentifier
        # В IFC4 RepresentationIdentifier обязателен для Body представлений
        # Для IfcSweptDiskSolid используем тип 'AdvancedSweptSolid'
        shape_rep = self.ifc.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",  # Обязательно для IFC4
            RepresentationType="AdvancedSweptSolid",  # Совместим с IfcSweptDiskSolid
            Items=[swept_area],
        )

        return shape_rep

    def associate_representation(self, product_type, shape_rep):
        """Ассоциация представления с типом продукта через RepresentationMap"""
        rep_maps = [
            m
            for m in self.ifc.by_type("IfcRepresentationMap")
            if m.MappedRepresentation == shape_rep
        ]

        if not rep_maps:
            rep_map = self.ifc.create_entity(
                "IfcRepresentationMap",
                MappingOrigin=self.ifc.create_entity(
                    "IfcAxis2Placement3D",
                    Location=self.ifc.create_entity(
                        "IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0]
                    ),
                ),
                MappedRepresentation=shape_rep,
            )

            if product_type.RepresentationMaps is None:
                product_type.RepresentationMaps = [rep_map]
            elif isinstance(product_type.RepresentationMaps, tuple):
                product_type.RepresentationMaps = list(product_type.RepresentationMaps) + [rep_map]
            else:
                product_type.RepresentationMaps.append(rep_map)

    def create_boolean_union(self, shapes):
        """
        Булево объединение списка solid через IfcCSGSolid

        Args:
            shapes: список IFC solid сущностей (IfcSolidModel) для объединения.
                    Это могут быть IfcSweptDiskSolid, IfcExtrudedAreaSolid, etc.

        Returns:
            IfcCSGSolid (обёртка над IfcBooleanResult)
        """
        if len(shapes) < 2:
            return shapes[0] if shapes else None

        # Все shapes уже IfcSolidModel, создаём цепочку IfcBooleanResult
        result = shapes[0]
        for solid in shapes[1:]:
            result = self.ifc.create_entity(
                "IfcBooleanResult",
                Operator="UNION",  # Без точек — ifcopenshell добавит при экспорте
                FirstOperand=result,
                SecondOperand=solid,
            )

        # Оборачиваем IfcBooleanResult в IfcCSGSolid
        # IfcCSGSolid принимает IfcBooleanOperand (которым является IfcBooleanResult)
        csg_solid = self.ifc.create_entity(
            "IfcCSGSolid",
            TreeRootExpression=result,
        )

        return csg_solid

    def create_triangulated_face_set(self, vertices, faces):
        """
        Создание IfcTriangulatedFaceSet из вершин и граней

        Args:
            vertices: список 3D координат [(x1,y1,z1), (x2,y2,z2), ...]
            faces: список треугольников [[0,1,2], [0,2,3], ...] (индексы 0-based)

        Returns:
            IfcTriangulatedFaceSet
        """
        # Конвертируем вершины в формат для shape_builder
        points = [tuple(v) for v in vertices]

        # shape_builder.triangulated_face_set ожидает индексы 0-based
        return self.builder.triangulated_face_set(points, faces)

    def create_shape_representation_from_face_set(self, face_set):
        """
        Создание IfcShapeRepresentation с IfcTriangulatedFaceSet

        Args:
            face_set: IfcTriangulatedFaceSet

        Returns:
            IfcShapeRepresentation
        """
        context = self._get_context()

        shape_rep = self.ifc.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=context,
            RepresentationIdentifier="Body",
            RepresentationType="Tessellation",  # Для IfcTriangulatedFaceSet
            Items=[face_set],
        )

        return shape_rep
