"""
main.py - Entry point for Pyodide
Initializes the base IFC document and provides the main interface
"""

try:
    from ifcopenshell import file as ifc_file
except ImportError:
    # Fallback if ifcopenshell not available in Pyodide
    ifc_file = None
    print("Warning: ifcopenshell not available, will use stub")

import uuid
import base64

# Global IFC document
ifc_doc = None


def generate_guid():
    """Generate IFC GUID"""
    uuid_bytes = uuid.uuid4().bytes
    guid_str = base64.b64encode(uuid_bytes).decode()[:22]
    return guid_str


def initialize_base_document():
    """Initialize empty IFC4 ADD2 TC1 document with Project/Site/Building/StoreyStructure"""
    global ifc_doc

    if ifc_file is None:
        raise RuntimeError("ifcopenshell not available in this environment")

    try:
        # Create IFC4 ADD2 TC1 file
        ifc_doc = ifc_file.create(schema='IFC4')

        # Project
        project = ifc_doc.create_entity('IfcProject',
                                       GlobalId=generate_guid(),
                                       Name='Anchor Bolt Generator',
                                       Description='Generated anchor bolts with IFC4 ADD2 TC1')

        # Site
        site = ifc_doc.create_entity('IfcSite',
                                    GlobalId=generate_guid(),
                                    Name='Default Site')

        # Building
        building = ifc_doc.create_entity('IfcBuilding',
                                        GlobalId=generate_guid(),
                                        Name='Default Building')

        # BuildingStorey
        storey = ifc_doc.create_entity('IfcBuildingStorey',
                                      GlobalId=generate_guid(),
                                      Name='Storey 1',
                                      Elevation=0.0)

        # Set up hierarchy
        # Project -> Site
        ifc_doc.create_entity('IfcRelAggregates',
                             GlobalId=generate_guid(),
                             RelatingObject=project,
                             RelatedObjects=[site])

        # Site -> Building
        ifc_doc.create_entity('IfcRelAggregates',
                             GlobalId=generate_guid(),
                             RelatingObject=site,
                             RelatedObjects=[building])

        # Building -> StoreyStructure
        ifc_doc.create_entity('IfcRelAggregates',
                             GlobalId=generate_guid(),
                             RelatingObject=building,
                             RelatedObjects=[storey])

        # Create unit assignments
        length_unit = ifc_doc.create_entity('IfcSIUnit',
                                           UnitType='LENGTHUNIT',
                                           Prefix='MILLI',
                                           Name='METRE')

        mass_unit = ifc_doc.create_entity('IfcSIUnit',
                                         UnitType='MASSUNIT',
                                         Name='GRAM')

        plane_angle = ifc_doc.create_entity('IfcSIUnit',
                                           UnitType='PLANEANGLEUNIT',
                                           Name='RADIAN')

        ifc_doc.create_entity('IfcUnitAssignment',
                             Units=[length_unit, mass_unit, plane_angle])

        # Create world coordinate system
        ifc_doc.create_entity('IfcAxis2Placement2D',
                             Location=ifc_doc.create_entity('IfcCartesianPoint', Coordinates=(0, 0)))

        ifc_doc.create_entity('IfcAxis2Placement3D',
                             Location=ifc_doc.create_entity('IfcCartesianPoint', Coordinates=(0, 0, 0)),
                             Axis=ifc_doc.create_entity('IfcDirection', DirectionRatios=(0, 0, 1)),
                             RefDirection=ifc_doc.create_entity('IfcDirection', DirectionRatios=(1, 0, 0)))

        return ifc_doc

    except Exception as e:
        print(f"Error initializing IFC document: {e}")
        raise


def get_ifc_document():
    """Get current IFC document"""
    global ifc_doc
    if ifc_doc is None:
        raise RuntimeError("IFC document not initialized. Call initialize_base_document() first.")
    return ifc_doc


if __name__ == '__main__':
    # Test initialization
    try:
        doc = initialize_base_document()
        print(f"✓ IFC document initialized")
    except Exception as e:
        print(f"✗ Error: {e}")
