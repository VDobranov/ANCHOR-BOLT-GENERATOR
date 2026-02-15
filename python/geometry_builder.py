"""
geometry_builder.py - Построение геометрии для компонентов болта
Кривые, профили, выдавливание для IFC представления
"""

import math
import numpy as np


def to_float_list(coordinates):
    """Convert coordinates to list of floats for ifcopenshell compatibility"""
    return [float(x) for x in coordinates]


class GeometryBuilder:
    """Класс для построения IFC геометрии"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc

    def create_line(self, point1, point2):
        """Create IfcLine between two points"""
        p1 = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list(point1))
        p2 = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list(point2))
        return self.ifc.create_entity('IfcLine', Pnt=p1, Dir=self._create_direction(point2, point1))

    def create_circle_arc(self, center, radius, start_angle, end_angle, normal=(0, 0, 1)):
        """Create circular arc segment in 3D space"""
        # Convert angles to radians if needed
        start = math.radians(start_angle) if start_angle > math.pi else start_angle
        end = math.radians(end_angle) if end_angle > math.pi else end_angle

        # For simplified representation, create arc as IfcCircularArcSegment3D
        center_point = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list(center))

        # Radius vector
        radius_point = (center[0] + radius, center[1], center[2])

        start_point = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=to_float_list([
                center[0] + radius * math.cos(start),
                center[1],
                center[2] + radius * math.sin(start)
            ]))

        end_point = self.ifc.create_entity('IfcCartesianPoint',
            Coordinates=to_float_list([
                center[0] + radius * math.cos(end),
                center[1],
                center[2] + radius * math.sin(end)
            ]))

        axis = self.ifc.create_entity('IfcAxis2Placement3D',
                                     Location=center_point,
                                     Axis=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list(normal)),
                                     RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0, 0])))

        return self.ifc.create_entity('IfcCircularArcSegment3D',
                                     StartPoint=start_point,
                                     EndPoint=end_point,
                                     Placement=axis,
                                     Radius=float(radius))

    def create_composite_curve_stud(self, bolt_type, diameter, length, execution=1):
        """
        Create composite curve for stud based on bolt type
        For bent bolts (1.1, 1.2): line + arc + line
        For straight bolts (2.1, 5): single line
        The bolt is oriented along the Z-axis from top to bottom (from +Z to -Z),
        with the origin at the bottom of the threaded portion.
        """
        segments = []

        # Determine if bolt has bend
        has_bend = bolt_type in ['1.1', '1.2']

        if has_bend:
            # Bent stud: upper straight part + arc + lower straight part
            radius = diameter * (1.5 if bolt_type == '1.1' else 2.0)

            # Upper straight line: from top (0,0,length) to bend point (0,0,length-radius)
            line1 = self.create_line([0.0, 0.0, float(length)], [0.0, 0.0, float(length - radius)])
            seg1 = self.ifc.create_entity('IfcCompositeCurveSegment',
                                         Transition='Continuous',
                                         SameSense=True,
                                         ParentCurve=line1)
            segments.append(seg1)

            # Circular arc: center at (radius, 0, length-radius), radius = radius
            # From (0,0,length-radius) to (radius,0,length-radius-radius)
            arc_center = (radius, 0.0, float(length - radius))
            # Arc from +Y direction to -X direction (rotated 90 degrees)
            arc = self.create_circle_arc(arc_center, radius, math.pi / 2, math.pi)
            seg2 = self.ifc.create_entity('IfcCompositeCurveSegment',
                                         Transition='Continuous',
                                         SameSense=True,
                                         ParentCurve=arc)
            segments.append(seg2)

            # Lower straight line: from bend point (radius,0,length-radius-radius) to bottom (radius,0,0)
            line2 = self.create_line([float(radius), 0.0, float(length - 2 * radius)], [float(radius), 0.0, 0.0])
            seg3 = self.ifc.create_entity('IfcCompositeCurveSegment',
                                         Transition='Continuous',
                                         SameSense=True,
                                         ParentCurve=line2)
            segments.append(seg3)
        else:
            # Straight stud: simple line from top (0,0,length) to bottom (0,0,0)
            line = self.create_line([0.0, 0.0, float(length)], [0.0, 0.0, 0.0])
            seg = self.ifc.create_entity('IfcCompositeCurveSegment',
                                        Transition='Continuous',
                                        SameSense=True,
                                        ParentCurve=line)
            segments.append(seg)

        # Create composite curve
        composite = self.ifc.create_entity('IfcCompositeCurve',
                                          Segments=segments,
                                          SelfIntersect=False)

        return composite

    def create_circle_profile(self, diameter):
        """Create circular profile for sweptsurface"""
        radius = diameter / 2.0
        circle_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list([0, 0, 0]))

        # Create circle placement
        placement = self.ifc.create_entity('IfcAxis2Placement2D',
                                          Location=circle_center,
                                          RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0])))

        # Create circle profile
        circle = self.ifc.create_entity('IfcCircle',
                                       Radius=float(radius),
                                       Position=placement)

        # Create profile def
        profile = self.ifc.create_entity('IfcProfileDefWithPosition',
                                        Position=placement)
        profile.Curve = circle

        return profile

    def create_hexagon_profile(self, nominal_diameter, height):
        """Create hexagonal profile for nut"""
        # Hex width across flats = S (from GOST_DATA)
        # For simplified representation, use outer diameter
        outer_diameter = nominal_diameter * 1.5

        # Create hexagon vertices
        vertices = []
        for i in range(6):
            angle = (i * 60 - 90) * math.pi / 180.0
            x = outer_diameter / 2.0 * math.cos(angle)
            y = outer_diameter / 2.0 * math.sin(angle)
            vertices.append(self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list([x, y])))

        # Create polyline for hexagon outer boundary
        outer_loop = self.ifc.create_entity('IfcPolyline', Points=vertices + [vertices[0]])

        # Create inner hole (circle)
        hole_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list([0, 0]))
        hole_placement = self.ifc.create_entity('IfcAxis2Placement2D',
                                               Location=hole_center,
                                               RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0])))
        hole_circle = self.ifc.create_entity('IfcCircle',
                                            Radius=float(nominal_diameter / 2.0 + 0.5),  # Small clearance
                                            Position=hole_placement)
        hole = self.ifc.create_entity('IfcPolyline',
                                     Points=[hole_center])  # Simplified

        # Create profile with voids
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
                                        ProfileType='AREA',
                                        OuterCurve=outer_loop,
                                        InnerCurves=[hole_circle])

        return profile

    def create_washer_profile(self, outer_diameter, inner_diameter):
        """Create ring profile for washer"""
        # Outer circle
        outer_center = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list([0, 0]))
        outer_placement = self.ifc.create_entity('IfcAxis2Placement2D',
                                                Location=outer_center,
                                                RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0])))
        outer_circle = self.ifc.create_entity('IfcCircle',
                                             Radius=float(outer_diameter / 2.0),
                                             Position=outer_placement)

        # Inner circle (hole)
        inner_placement = self.ifc.create_entity('IfcAxis2Placement2D',
                                                Location=outer_center,
                                                RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0])))
        inner_circle = self.ifc.create_entity('IfcCircle',
                                             Radius=float(inner_diameter / 2.0),
                                             Position=inner_placement)

        # Create profile with void
        profile = self.ifc.create_entity('IfcArbitraryProfileDefWithVoids',
                                        ProfileType='AREA',
                                        OuterCurve=outer_circle,
                                        InnerCurves=[inner_circle])

        return profile

    def create_extruded_solid(self, profile, extrusion_height, direction=(0, 0, 1)):
        """Create extruded area solid"""
        # Base placement
        base_point = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list([0, 0, 0]))
        base_placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                               Location=base_point,
                                               Axis=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list(direction)),
                                               RefDirection=self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([1, 0, 0])))

        # Extrusion direction
        extrusion_dir = self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list(direction))

        # Create extruded solid
        solid = self.ifc.create_entity('IfcExtrudedAreaSolid',
                                      SweptArea=profile,
                                      Position=base_placement,
                                      ExtrudedDirection=extrusion_dir,
                                      Depth=float(extrusion_height))

        return solid

    def create_swept_disk_solid(self, axis_curve, radius):
        """Create swept disk solid for stud (revolution of circle along curve)"""
        # In IFC, IfcSweptDiskSolid represents a disk swept along a curve
        solid = self.ifc.create_entity('IfcSweptDiskSolid',
                                      Directrix=axis_curve,
                                      Radius=float(radius))

        return solid

    def _create_direction(self, to_point, from_point):
        """Helper to create direction"""
        dx = to_point[0] - from_point[0]
        dy = to_point[1] - from_point[1]
        dz = to_point[2] - from_point[2]
        return self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list([dx, dy, dz]))

    def create_placement(self, location=(0, 0, 0), z_axis=(0, 0, 1), x_axis=(1, 0, 0)):
        """Create 3D placement with location and axes"""
        location_point = self.ifc.create_entity('IfcCartesianPoint', Coordinates=to_float_list(location))
        axis = self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list(z_axis))
        ref_direction = self.ifc.create_entity('IfcDirection', DirectionRatios=to_float_list(x_axis))

        placement = self.ifc.create_entity('IfcAxis2Placement3D',
                                          Location=location_point,
                                          Axis=axis,
                                          RefDirection=ref_direction)
        return placement


def create_stud_representation(ifc_doc, bolt_type, diameter, length, execution=1):
    """Create representation for stud"""
    builder = GeometryBuilder(ifc_doc)

    # Create axis curve
    axis_curve = builder.create_composite_curve_stud(bolt_type, diameter, length, execution)

    # Create swept disk solid
    stud_radius = diameter / 2.0
    geometry = builder.create_swept_disk_solid(axis_curve, stud_radius)

    return geometry


def create_nut_representation(ifc_doc, diameter, height):
    """Create representation for nut"""
    builder = GeometryBuilder(ifc_doc)

    # Create hexagonal profile
    profile = builder.create_hexagon_profile(diameter, height)

    # Create extruded solid
    geometry = builder.create_extruded_solid(profile, height)

    return geometry


def create_washer_representation(ifc_doc, outer_diameter, inner_diameter, thickness):
    """Create representation for washer"""
    builder = GeometryBuilder(ifc_doc)

    # Create ring profile
    profile = builder.create_washer_profile(outer_diameter, inner_diameter)

    # Create extruded solid
    geometry = builder.create_extruded_solid(profile, thickness)

    return geometry


if __name__ == '__main__':
    print("✓ geometry_builder.py module loaded")
