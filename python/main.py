"""
main.py — Entry point для Pyodide
Управление IFC документом и ifcopenshell
"""

from utils import get_ifcopenshell, is_ifcopenshell_available


class IFCDocument:
    """Класс для управления IFC документом"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self.file = None
        self._initialized = True
    
    def initialize(self, schema='IFC4'):
        """Инициализация нового документа"""
        ifc = get_ifcopenshell()
        if ifc is None:
            raise RuntimeError("ifcopenshell не доступен. Убедитесь, что он установлен через micropip.")

        try:
            self.file = ifc.file(schema=schema)
        except Exception:
            self.file = ifc.file(schema='IFC4X3')

        self._create_base_structure()
        return self.file
    
    def reset(self):
        """Сброс документа: удаление всех болтов и создание нового"""
        ifc = get_ifcopenshell()
        if ifc is None:
            raise RuntimeError("ifcopenshell не доступен")

        # Сохраняем базовые структуры
        projects = self.file.by_type('IfcProject')
        project = projects[0] if projects else None
        
        sites = self.file.by_type('IfcSite')
        site = sites[0] if sites else None
        
        buildings = self.file.by_type('IfcBuilding')
        building = buildings[0] if buildings else None
        
        storeys = self.file.by_type('IfcBuildingStorey')
        storey = storeys[0] if storeys else None
        
        materials = self.file.by_type('IfcMaterial')
        
        # Удаляем все MechanicalFastener и связанные сущности
        fasteners = self.file.by_type('IfcMechanicalFastener')
        fastener_types = self.file.by_type('IfcMechanicalFastenerType')
        rel_defines = self.file.by_type('IfcRelDefinesByType')
        rel_aggregates = self.file.by_type('IfcRelAggregates')
        rel_connects = self.file.by_type('IfcRelConnectsElements')
        rel_contained = self.file.by_type('IfcRelContainedInSpatialStructure')
        
        # Удаляем отношения
        for entity in rel_defines + rel_aggregates + rel_connects + rel_contained:
            try:
                self.file.remove(entity)
            except Exception:
                pass
        
        # Удаляем болты и их типы
        for entity in fasteners + fastener_types:
            try:
                self.file.remove(entity)
            except Exception:
                pass
        
        # Пересоздаём базовую структуру
        self.file = None
        try:
            self.file = ifc.file(schema='IFC4')
        except Exception:
            self.file = ifc.file(schema='IFC4X3')

        self._create_base_structure()
        
        # Восстанавливаем материалы если были
        if materials:
            for mat in materials:
                try:
                    new_mat = self.file.create_entity('IfcMaterial',
                        Name=mat.Name,
                        Description=mat.Description
                    )
                except Exception:
                    pass

    def _create_base_structure(self):
        """Создание базовой IFC структуры: Project/Site/Building/Storey"""
        f = self.file
        ifc = get_ifcopenshell()

        # Project
        project = f.create_entity('IfcProject',
            GlobalId=ifc.guid.new(),
            Name='Anchor Bolt Generator',
            Description='Generated anchor bolts with IFC4 ADD2 TC1'
        )

        # Site
        site = f.create_entity('IfcSite',
            GlobalId=ifc.guid.new(),
            Name='Default Site'
        )

        # Building
        building = f.create_entity('IfcBuilding',
            GlobalId=ifc.guid.new(),
            Name='Default Building'
        )

        # BuildingStorey
        storey = f.create_entity('IfcBuildingStorey',
            GlobalId=ifc.guid.new(),
            Name='Storey 1',
            Elevation=0.0
        )

        # Иерархия: Project -> Site -> Building -> Storey
        f.create_entity('IfcRelAggregates',
            GlobalId=ifc.guid.new(),
            RelatingObject=project,
            RelatedObjects=[site]
        )
        f.create_entity('IfcRelAggregates',
            GlobalId=ifc.guid.new(),
            RelatingObject=site,
            RelatedObjects=[building]
        )
        f.create_entity('IfcRelAggregates',
            GlobalId=ifc.guid.new(),
            RelatingObject=building,
            RelatedObjects=[storey]
        )
        
        # World coordinate system
        f.create_entity('IfcAxis2Placement2D',
            Location=f.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0])
        )
        f.create_entity('IfcAxis2Placement3D',
            Location=f.create_entity('IfcCartesianPoint', Coordinates=[0.0, 0.0, 0.0]),
            Axis=f.create_entity('IfcDirection', DirectionRatios=[0.0, 0.0, 1.0]),
            RefDirection=f.create_entity('IfcDirection', DirectionRatios=[1.0, 0.0, 0.0])
        )
        
        # Units and contexts
        from ifc_generator import IFCGenerator
        gen = IFCGenerator(f)
        gen.setup_units_and_contexts()
    
    def get_file(self):
        """Получение IFC файла"""
        if self.file is None:
            raise RuntimeError("IFC документ не инициализирован")
        return self.file


# Singleton instance
_doc_instance = None


def get_document():
    """Получение экземпляра документа"""
    global _doc_instance
    if _doc_instance is None:
        _doc_instance = IFCDocument()
    return _doc_instance


def initialize_base_document():
    """Инициализация базового документа"""
    doc = get_document()
    return doc.initialize()


def get_ifc_document():
    """Получение текущего IFC документа"""
    doc = get_document()
    return doc.get_file()


def reset_ifc_document():
    """Сброс IFC документа и создание нового"""
    doc = get_document()
    doc.reset()
    return doc.get_file()


if __name__ == '__main__':
    try:
        doc = initialize_base_document()
        print("✓ IFC документ инициализирован")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
