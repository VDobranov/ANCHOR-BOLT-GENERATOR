"""
main.py — Entry point для Pyodide
Управление IFC документом и ifcopenshell
"""

import numpy as np
from utils import get_ifcopenshell
from ifcopenshell.api import run
from material_manager import MaterialManager


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
        self.material_manager = None
        self._initialized = True

    def initialize(self, schema='IFC4'):
        """Инициализация нового документа"""
        import time
        import tempfile
        import os
        import ifcopenshell
        
        ifc = get_ifcopenshell()
        if ifc is None:
            raise RuntimeError("ifcopenshell не доступен. Убедитесь, что он установлен через micropip.")

        # Создаём базовый файл с IfcOwnerHistory на ID #1 через SPF
        timestamp = int(time.time())
        
        spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','{time.strftime('%Y-%m-%dT%H:%M:%S')}',(''),(''),'IfcOpenShell 0.8.4','IfcOpenShell 0.8.4','');
FILE_SCHEMA(('{schema}'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#5,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG',$,$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCAPPLICATION(#2,$,'ABG','ABG');
ENDSEC;
END-ISO-10303-21;
"""
        
        # Сохраняем во временный файл и открываем
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as tmp:
            tmp.write(spf_content)
            tmp_path = tmp.name
        
        self.file = ifcopenshell.open(tmp_path)
        os.unlink(tmp_path)
        
        # Сохраняем ссылку на OwnerHistory
        self.owner_history = self.file.by_id(1)

        self._create_base_structure()
        self.material_manager = MaterialManager(self.file)
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

        # Сохраняем имена материалов для восстановления
        material_names = []
        if self.material_manager:
            for name in self.material_manager.materials_cache.keys():
                material_names.append(name)

        # Удаляем все MechanicalFastener и связанные сущности
        fasteners = self.file.by_type('IfcMechanicalFastener')
        fastener_types = self.file.by_type('IfcMechanicalFastenerType')
        rel_defines = self.file.by_type('IfcRelDefinesByType')
        rel_aggregates = self.file.by_type('IfcRelAggregates')
        rel_connects = self.file.by_type('IfcRelConnectsElements')
        rel_contained = self.file.by_type('IfcRelContainedInSpatialStructure')
        rel_associates = self.file.by_type('IfcRelAssociatesMaterial')
        material_lists = self.file.by_type('IfcMaterialList')

        # Удаляем отношения
        for entity in rel_defines + rel_aggregates + rel_connects + rel_contained + rel_associates:
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

        # Удаляем материалы и списки материалов
        for entity in material_lists:
            try:
                self.file.remove(entity)
            except Exception:
                pass

        # Пересоздаём базовую структуру с IfcOwnerHistory на ID #1
        import time
        timestamp = int(time.time())
        
        spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('','{time.strftime('%Y-%m-%dT%H:%M:%S')}',(''),(''),'IfcOpenShell 0.8.4','IfcOpenShell 0.8.4','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#5,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG',$,$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCAPPLICATION(#2,$,'ABG','ABG');
ENDSEC;
END-ISO-10303-21;
"""
        
        # Сохраняем во временный файл и открываем
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as tmp:
            tmp.write(spf_content)
            tmp_path = tmp.name
        
        self.file = ifcopenshell.open(tmp_path)
        os.unlink(tmp_path)
        
        # Сохраняем ссылку на OwnerHistory
        self.owner_history = self.file.by_id(1)

        self._create_base_structure()

        # Восстанавливаем material_manager
        self.material_manager = MaterialManager(self.file)

        # Восстанавливаем материалы
        for mat_name in material_names:
            self.material_manager.create_material(mat_name, category='Steel')

    def _create_base_structure(self):
        """Создание базовой IFC структуры: Project/Site/Building/Storey"""
        f = self.file
        ifc = get_ifcopenshell()

        # Project с OwnerHistory
        project = f.create_entity('IfcProject',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name='Anchor Bolt Generator',
            Description='Generated anchor bolts with IFC4 ADD2 TC1'
        )

        # Site с OwnerHistory
        site = f.create_entity('IfcSite',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name='Default Site'
        )
        # Размещение сайта (мировая СК, единичная матрица)
        run("geometry.edit_object_placement", f, product=site, matrix=np.eye(4))

        # Building с OwnerHistory
        building = f.create_entity('IfcBuilding',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name='Default Building'
        )
        # Размещение здания (относительно сайта, без смещения)
        run("geometry.edit_object_placement", f, product=building, matrix=np.eye(4))

        # BuildingStorey с OwnerHistory
        storey = f.create_entity('IfcBuildingStorey',
            GlobalId=ifc.guid.new(),
            OwnerHistory=self.owner_history,
            Name='Storey 1',
            Elevation=0.0
        )
        # Размещение этажа (относительно здания, без смещения)
        run("geometry.edit_object_placement", f, product=storey, matrix=np.eye(4))

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


def get_material_manager():
    """Получение менеджера материалов"""
    doc = get_document()
    if doc.material_manager is None:
        doc.initialize()
    return doc.material_manager


if __name__ == '__main__':
    try:
        doc = initialize_base_document()
        print("✓ IFC документ инициализирован")
    except Exception as e:
        print(f"✗ Ошибка: {e}")
