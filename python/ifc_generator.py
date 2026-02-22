"""
ifc_generator.py — Генерация и экспорт IFC файлов
"""


class IFCGenerator:
    """Генератор IFC файлов"""

    def __init__(self, ifc_doc):
        self.ifc = ifc_doc

    def setup_units_and_contexts(self):
        """Настройка единиц и геометрического контекста"""
        f = self.ifc

        # Единицы
        length_unit = f.create_entity('IfcSIUnit',
            UnitType='LENGTHUNIT', Prefix='MILLI', Name='METRE'
        )
        mass_unit = f.create_entity('IfcSIUnit',
            UnitType='MASSUNIT', Name='GRAM'
        )
        plane_angle = f.create_entity('IfcSIUnit',
            UnitType='PLANEANGLEUNIT', Name='RADIAN'
        )

        unit_assignment = f.create_entity('IfcUnitAssignment',
            Units=[length_unit, mass_unit, plane_angle]
        )

        # Геометрический контекст
        world_coordinate_system = f.create_entity('IfcAxis2Placement3D',
            Location=f.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]),
            Axis=f.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=f.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0])
        )

        geometric_context = f.create_entity('IfcGeometricRepresentationContext',
            ContextType='Model',
            CoordinateSpaceDimension=3,
            Precision=1e-05,
            WorldCoordinateSystem=world_coordinate_system
        )

        # Привязка к проекту
        projects = f.by_type('IfcProject')
        if not projects:
            raise ValueError("IfcProject не найден")

        project = projects[0]
        project.UnitsInContext = unit_assignment
        project.RepresentationContexts = [geometric_context]

    def export_to_string(self):
        """Экспорт в строку"""
        return self.ifc.write()

    def export_to_file(self, filepath):
        """Экспорт в файл"""
        self.ifc.write(filepath)
        return filepath

    def get_summary(self):
        """Получение сводки по документу"""
        return {
            'project': self._get_project_info(),
            'entities_count': len(self.ifc),
            'entity_types': self._count_entity_types(),
            'mechanical_fasteners': self._count_fasteners(),
            'materials': self._count_materials()
        }

    def _get_project_info(self):
        """Информация о проекте"""
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
        """Подсчёт типов сущностей"""
        types = {}
        for entity in self.ifc:
            entity_type = entity.is_a()
            types[entity_type] = types.get(entity_type, 0) + 1
        return types

    def _count_fasteners(self):
        """Подсчёт болтов"""
        fasteners = self.ifc.by_type('IfcMechanicalFastener')
        grouped = {}
        for f in fasteners:
            ftype = f.ObjectType or 'Unknown'
            grouped[ftype] = grouped.get(ftype, 0) + 1
        return {'total': len(fasteners), 'by_type': grouped}

    def _count_materials(self):
        """Подсчёт материалов"""
        materials = self.ifc.by_type('IfcMaterial')
        return {
            'total': len(materials),
            'materials': [{'name': m.Name, 'description': m.Description} for m in materials]
        }

    def validate(self):
        """Базовая валидация документа"""
        errors = []
        warnings = []

        if not self.ifc.by_type('IfcProject'):
            errors.append("IfcProject не найден")

        if not self.ifc.schema.startswith('IFC4'):
            warnings.append(f"Схема {self.ifc.schema}, ожидается IFC4")

        if not self.ifc.by_type('IfcBuildingStorey'):
            warnings.append("IfcBuildingStorey не найден")

        if not self.ifc.by_type('IfcMechanicalFastener'):
            warnings.append("IfcMechanicalFastener не найден")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }


def export_ifc_file(ifc_doc, filepath, bolt_type, diameter, length):
    """Экспорт IFC файла с метаданными"""
    gen = IFCGenerator(ifc_doc)
    validation = gen.validate()

    if not validation['valid']:
        return {'status': 'error', 'errors': validation['errors']}

    try:
        gen.export_to_file(filepath)
        return {
            'status': 'success',
            'filepath': filepath,
            'filename': f'bolt_{bolt_type}_M{diameter}x{length}.ifc',
            'validation': validation,
            'summary': gen.get_summary()
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
