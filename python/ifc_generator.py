"""
ifc_generator.py - Генерация и экспорт IFC файлов
"""


class IFCGenerator:
    """Класс для генерации и сохранения IFC файлов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc

    def export_to_string(self):
        """Export IFC document to string (IFC SPF format)"""
        return self.ifc.write()

    def export_to_file(self, filepath):
        """Export IFC document to file"""
        self.ifc.write(filepath)
        return filepath

    def get_summary(self):
        """Get summary of IFC document contents"""
        summary = {
            'project': self._get_project_info(),
            'entities_count': len(self.ifc),
            'entity_types': self._count_entity_types(),
            'mechanical_fasteners': self._count_fasteners(),
            'materials': self._count_materials()
        }
        return summary

    def _get_project_info(self):
        """Get project information"""
        projects = self.ifc.by_type('IfcProject')
        if projects:
            proj = projects[0]
            return {
                'name': proj.Name or 'Unnamed',
                'description': proj.Description or '',
                'schema': self.ifc.schema
            }
        return {}

    def _count_entity_types(self):
        """Count entities by type"""
        types = {}
        for entity in self.ifc:
            entity_type = entity.is_a()
            if entity_type not in types:
                types[entity_type] = 0
            types[entity_type] += 1
        return types

    def _count_fasteners(self):
        """Count mechanical fasteners"""
        fasteners = self.ifc.by_type('IfcMechanicalFastener')
        return {
            'total': len(fasteners),
            'by_type': self._group_fasteners_by_type(fasteners)
        }

    def _count_materials(self):
        """Count materials"""
        materials = self.ifc.by_type('IfcMaterial')
        return {
            'total': len(materials),
            'materials': [{'name': m.Name or 'Unnamed', 'description': m.Description or ''} for m in materials]
        }

    def _group_fasteners_by_type(self, fasteners):
        """Group fasteners by type"""
        grouped = {}
        for fastener in fasteners:
            ftype = fastener.ObjectType or 'Unknown'
            if ftype not in grouped:
                grouped[ftype] = 0
            grouped[ftype] += 1
        return grouped

    def validate_ifc(self):
        """Basic validation of IFC document"""
        errors = []
        warnings = []

        # Check for required project
        projects = self.ifc.by_type('IfcProject')
        if not projects:
            errors.append("No IfcProject found")

        # Check schema version
        if not self.ifc.schema.startswith('IFC4'):
            warnings.append(f"Using schema {self.ifc.schema}, expected IFC4 variant")

        # Check for at least one building storey
        storeys = self.ifc.by_type('IfcBuildingStorey')
        if not storeys:
            warnings.append("No building storey found")

        # Check for mechanical fasteners
        fasteners = self.ifc.by_type('IfcMechanicalFastener')
        if not fasteners:
            warnings.append("No mechanical fasteners found")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def export_ifc_file(ifc_doc, filepath, bolt_type, diameter, length):
    """
    Helper function to export IFC file with metadata

    Args:
        ifc_doc: IFC document
        filepath: Path to save file
        bolt_type: Type of bolt (e.g., '1.1')
        diameter: Diameter in mm
        length: Length in mm

    Returns:
        dict with export result
    """
    generator = IFCGenerator(ifc_doc)

    # Validate
    validation = generator.validate_ifc()

    if not validation['valid']:
        return {
            'status': 'error',
            'errors': validation['errors']
        }

    # Export
    try:
        generator.export_to_file(filepath)

        return {
            'status': 'success',
            'filepath': filepath,
            'filename': f'bolt_{bolt_type}_M{diameter}x{length}.ifc',
            'validation': validation,
            'summary': generator.get_summary()
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }
