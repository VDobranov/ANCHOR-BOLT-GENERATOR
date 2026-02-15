"""
main.py - Entry point for Pyodide
Initializes the base IFC document and provides the main interface
"""

try:
    import ifcopenshell
except ImportError:
    # Fallback if ifcopenshell not available in Pyodide
    ifcopenshell = None
    print("Warning: ifcopenshell not available, will use stub")

# Global IFC document
ifc_doc = None


def generate_guid():
    """Generate IFC GUID using ifcopenshell"""
    return ifcopenshell.guid.new()


def initialize_base_document():
    """Initialize empty IFC4 ADD2 TC1 document with Project/Site/Building/StoreyStructure"""
    global ifc_doc

    if ifcopenshell is None:
        raise RuntimeError("ifcopenshell not available in this environment")

    try:
        # Create IFC4 file - use IFC4X3 if IFC4 is not supported
        try:
            ifc_doc = ifcopenshell.file(schema='IFC4')
        except:
            ifc_doc = ifcopenshell.file(schema='IFC4X3')

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

        # Create world coordinate system
        ifc_doc.create_entity('IfcAxis2Placement2D',
                             Location=ifc_doc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0]))

        ifc_doc.create_entity('IfcAxis2Placement3D',
                             Location=ifc_doc.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]),
                             Axis=ifc_doc.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0]),
                             RefDirection=ifc_doc.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0]))

        # Setup units and contexts using IFCGenerator
        from ifc_generator import IFCGenerator
        generator = IFCGenerator(ifc_doc)
        generator.setup_units_and_contexts()

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
