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
        length_unit = f.create_entity(
            "IfcSIUnit", UnitType="LENGTHUNIT", Prefix="MILLI", Name="METRE"
        )
        mass_unit = f.create_entity("IfcSIUnit", UnitType="MASSUNIT", Name="GRAM")
        plane_angle = f.create_entity("IfcSIUnit", UnitType="PLANEANGLEUNIT", Name="RADIAN")

        unit_assignment = f.create_entity(
            "IfcUnitAssignment", Units=[length_unit, mass_unit, plane_angle]
        )

        # Геометрический контекст
        world_coordinate_system = f.create_entity(
            "IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=[0.0, 0.0, 0.0]),
            Axis=f.create_entity("IfcDirection", DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=f.create_entity("IfcDirection", DirectionRatios=[1.0, 0.0, 0.0]),
        )

        geometric_context = f.create_entity(
            "IfcGeometricRepresentationContext",
            ContextType="Model",
            CoordinateSpaceDimension=3,
            Precision=1e-05,
            WorldCoordinateSystem=world_coordinate_system,
        )

        # Создаём субконтекст для 3D Body representation через API
        # Улучшает совместимость с Tekla, Revit, Solibri
        from ifcopenshell.api import context

        body_subcontext = context.add_context(
            f,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
            parent=geometric_context,
            target_scale=1.0,
        )

        # Привязка к проекту
        # Только основной контекст добавляется в RepresentationContexts
        # Субконтексты связаны через ParentContext
        projects = f.by_type("IfcProject")
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
            "project": self._get_project_info(),
            "entities_count": len(self.ifc),
            "entity_types": self._count_entity_types(),
            "mechanical_fasteners": self._count_fasteners(),
            "materials": self._count_materials(),
        }

    def _get_project_info(self):
        """Информация о проекте"""
        projects = self.ifc.by_type("IfcProject")
        if projects:
            proj = projects[0]
            return {
                "name": proj.Name or "Unnamed",
                "description": proj.Description or "",
                "schema": self.ifc.schema,
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
        fasteners = self.ifc.by_type("IfcMechanicalFastener")
        grouped = {}
        for f in fasteners:
            ftype = f.ObjectType or "Unknown"
            grouped[ftype] = grouped.get(ftype, 0) + 1
        return {"total": len(fasteners), "by_type": grouped}

    def _count_materials(self):
        """Подсчёт материалов"""
        materials = self.ifc.by_type("IfcMaterial")
        return {
            "total": len(materials),
            "materials": [{"name": m.Name, "description": m.Description} for m in materials],
        }

    def validate(self):
        """Базовая валидация документа"""
        errors = []
        warnings = []

        if not self.ifc.by_type("IfcProject"):
            errors.append("IfcProject не найден")

        if not self.ifc.schema.startswith("IFC4"):
            warnings.append(f"Схема {self.ifc.schema}, ожидается IFC4")

        if not self.ifc.by_type("IfcBuildingStorey"):
            warnings.append("IfcBuildingStorey не найден")

        if not self.ifc.by_type("IfcMechanicalFastener"):
            warnings.append("IfcMechanicalFastener не найден")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}

    def get_element_properties(self, global_id):
        """
        Извлечение PropertySet для элемента по GlobalId

        Args:
            global_id: GlobalId элемента (строка)

        Returns:
            dict с name, ifc_type и property_sets или None если элемент не найден
            {
                'name': str,
                'ifc_type': str,
                'property_sets': [
                    {
                        'name': str,
                        'properties': [
                            {'name': str, 'value': any, 'type': str}
                        ]
                    }
                ]
            }
        """
        # Поиск элемента по GlobalId
        element = None
        for entity in self.ifc:
            if hasattr(entity, "GlobalId") and entity.GlobalId == global_id:
                element = entity
                break

        if element is None:
            return None

        # Получаем IFC тип элемента (конвертируем в строку)
        ifc_type = str(element.is_a()) if hasattr(element, "is_a") else "Unknown"

        property_sets = []

        # 1. Получение PropertySet через IsDefinedBy (прямые Pset на экземпляре)
        is_defined_by = getattr(element, "IsDefinedBy", None)
        if is_defined_by:
            for rel in is_defined_by:
                if rel.is_a("IfcRelDefinesByProperties"):
                    pset = rel.RelatingPropertyDefinition
                    properties = self._extract_properties(pset)
                    if properties:
                        property_sets.append({"name": pset.Name, "properties": properties})

        # 2. Получение PropertySet из типа (через IsTypedBy)
        # Элементы связаны с типом через IfcRelDefinesByType
        is_typed_by = getattr(element, "IsTypedBy", None)
        if is_typed_by:
            for rel in is_typed_by:
                if rel.is_a("IfcRelDefinesByType"):
                    related_type = rel.RelatingType

                    # Получение PropertySet через HasPropertySets на типе
                    # Это включает и Pset созданные через IfcRelDefinesByProperties
                    has_property_sets = getattr(related_type, "HasPropertySets", None)
                    if has_property_sets:
                        # Конвертируем кортеж в список, если нужно
                        if isinstance(has_property_sets, tuple):
                            has_property_sets = list(has_property_sets)
                        for pset in has_property_sets:
                            properties = self._extract_properties(pset)
                            if properties:
                                property_sets.append({"name": pset.Name, "properties": properties})

        return {
            "name": element.Name or element.ObjectType or "Unnamed",
            "ifc_type": ifc_type,
            "property_sets": property_sets,
        }

    def _extract_properties(self, pset):
        """Извлечение свойств из PropertySet"""
        properties = []
        has_properties = getattr(pset, "HasProperties", None)
        if has_properties:
            for prop in has_properties:
                value = None
                prop_type = None

                # Проверяем IfcPropertyEnumeratedValue
                if prop.is_a("IfcPropertyEnumeratedValue"):
                    enum_values = getattr(prop, "EnumerationValues", None)
                    if enum_values and len(enum_values) > 0:
                        # Берём первое значение из enumeration
                        first_val = enum_values[0]
                        if hasattr(first_val, "value"):
                            value = first_val.value
                        elif hasattr(first_val, "wrappedValue"):
                            value = first_val.wrappedValue
                        else:
                            value = str(first_val)
                        prop_type = "IfcPropertyEnumeratedValue"
                else:
                    # IfcPropertySingleValue и другие
                    prop_value = getattr(prop, "NominalValue", None)
                    if prop_value is not None:
                        try:
                            # Пытаемся получить .value для оберток
                            value = prop_value.value
                            prop_type = prop_value.is_a()
                        except (AttributeError, TypeError):
                            # Если это entity_instance (IfcLengthMeasure и т.д.)
                            # Конвертируем в float через обёртку
                            if hasattr(prop_value, "wrappedValue"):
                                value = prop_value.wrappedValue
                                prop_type = prop_value.is_a()
                            else:
                                # Для простых типов
                                value = (
                                    float(prop_value)
                                    if isinstance(prop_value, (int, float))
                                    else str(prop_value)
                                )
                                prop_type = type(prop_value).__name__

                properties.append(
                    {
                        "name": prop.Name,
                        "value": value,
                        "type": prop_type,
                    }
                )
        return properties
