"""
document_manager.py — Менеджер IFC документов

Управление множественными IFC документами:
- Каждый документ имеет уникальный ID
- Документы изолированы друг от друга
- Поддержка тестирования через временные документы
"""

import os
import tempfile
import time
from typing import Any, Dict, Optional

import ifcopenshell
import numpy as np
from ifcopenshell.api import run
from material_manager import MaterialManager
from utils import get_ifcopenshell


class IFCDocumentManager:
    """
    Менеджер IFC документов с поддержкой множественных документов

    Пример использования:
        manager = IFCDocumentManager()
        doc = manager.create_document('my-bolt', schema='IFC4')
        # ... работа с документом
        manager.delete_document('my-bolt')
    """

    def __init__(self):
        """Инициализация менеджера"""
        self._documents: Dict[str, Any] = {}
        self._material_managers: Dict[str, MaterialManager] = {}
        self._current_id: Optional[str] = None

    def create_document(self, doc_id: str, schema: str = "IFC4") -> Any:
        """
        Создание нового IFC документа

        Args:
            doc_id: Уникальный идентификатор документа
            schema: IFC схема (по умолчанию 'IFC4')

        Returns:
            IFC документ (ifcopenshell.file)
        """
        if doc_id in self._documents:
            raise ValueError(f"Документ '{doc_id}' уже существует")

        doc = self._initialize_document(schema)
        self._documents[doc_id] = doc
        self._material_managers[doc_id] = MaterialManager(doc)
        self._current_id = doc_id

        return doc

    def _initialize_document(self, schema: str) -> Any:
        """
        Инициализация нового IFC документа

        Создаёт базовую структуру:
        - IfcOwnerHistory (#1)
        - IfcProject
        - IfcSite
        - IfcBuilding
        - IfcBuildingStorey

        Args:
            schema: IFC схема

        Returns:
            IFC документ
        """
        ifc = get_ifcopenshell()
        if ifc is None:
            raise RuntimeError(
                "ifcopenshell не доступен. Убедитесь, что он установлен через micropip."
            )

        # Создаём базовый файл с IfcOwnerHistory на ID #1 через SPF
        timestamp = int(time.time())

        # Согласно buildingSMART IFC Header Policy:
        # - FILE_DESCRIPTION: ViewDefinition для IFC4 — ReferenceView_V1.2
        # - FILE_NAME: name, time_stamp (ISO 8601), author, organization,
        #              preprocessor_version, originating_system, authorization
        # - originating_system формат: "Company - Application - Version"

        spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');
FILE_NAME('anchor_bolt.ifc','{time.strftime('%Y-%m-%dT%H:%M:%S')}',('Anchor Bolt Generator'),('ABG'),'Anchor Bolt Generator 1.0','ABG - Anchor Bolt Generator - 1.0','none');
FILE_SCHEMA(('{schema}'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#6,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG','ABG',$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCORGANIZATION('ABG','ABG',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','Anchor Bolt Generator','ABG');
ENDSEC;
END-ISO-10303-21;
"""

        # Сохраняем во временный файл и открываем
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ifc", delete=False) as tmp:
            tmp.write(spf_content)
            tmp_path = tmp.name

        doc = ifcopenshell.open(tmp_path)
        os.unlink(tmp_path)

        # Сохраняем ссылку на OwnerHistory
        doc.owner_history = doc.by_id(1)

        self._create_base_structure(doc)

        return doc

    def _create_base_structure(self, doc: Any) -> None:
        """
        Создание базовой IFC структуры: Project/Site/Building/Storey

        Args:
            doc: IFC документ
        """
        f = doc
        ifc = get_ifcopenshell()

        # Project с OwnerHistory
        project = f.create_entity(
            "IfcProject",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            Name="Anchor Bolt Generator",
            Description="Generated anchor bolts with IFC4 ADD2 TC1",
        )

        # Site с OwnerHistory
        site = f.create_entity(
            "IfcSite", GlobalId=ifc.guid.new(), OwnerHistory=f.owner_history, Name="Default Site"
        )
        # Размещение сайта (мировая СК, единичная матрица)
        run("geometry.edit_object_placement", f, product=site, matrix=np.eye(4))

        # Building с OwnerHistory
        building = f.create_entity(
            "IfcBuilding",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            Name="Default Building",
        )
        # Размещение здания (относительно сайта, без смещения)
        run("geometry.edit_object_placement", f, product=building, matrix=np.eye(4))

        # BuildingStorey с OwnerHistory
        storey = f.create_entity(
            "IfcBuildingStorey",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            Name="Storey 1",
            Elevation=0.0,
        )
        # Размещение этажа (относительно здания, без смещения)
        run("geometry.edit_object_placement", f, product=storey, matrix=np.eye(4))

        # Иерархия: Project -> Site -> Building -> Storey
        f.create_entity(
            "IfcRelAggregates",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=project,
            RelatedObjects=[site],
        )
        f.create_entity(
            "IfcRelAggregates",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=site,
            RelatedObjects=[building],
        )
        f.create_entity(
            "IfcRelAggregates",
            GlobalId=ifc.guid.new(),
            OwnerHistory=f.owner_history,
            RelatingObject=building,
            RelatedObjects=[storey],
        )

        # World coordinate system
        # IfcAxis2Placement3D создаётся в setup_units_and_contexts() для WorldCoordinateSystem

        # Units and contexts
        from ifc_generator import IFCGenerator

        gen = IFCGenerator(f)
        gen.setup_units_and_contexts()

        # GRF003: Добавляем IfcProjectedCRS для соответствия правилу
        # CRS требуется при наличии IfcBuilding
        # IFC105: Связываем CRS с IfcProject через HasCoordinateOperation
        projected_crs = f.create_entity(
            "IfcProjectedCRS",
            Name="EPSG:3857",  # WGS 84 / Pseudo-Mercator (по умолчанию)
            Description="Web Mercator - Default projected CRS",
            GeodeticDatum="WGS84",
            VerticalDatum="unknown",
        )

        # IFC4: IfcCoordinateReferenceSystemSelect может быть IfcGeometricRepresentationContext
        # Используем контекст как SourceCRS
        context = (
            f.by_type("IfcGeometricRepresentationContext")[0]
            if f.by_type("IfcGeometricRepresentationContext")
            else None
        )

        if context:
            # Создаём IfcMapConversion для связи Project с CRS
            # GRF005: Scale должен быть указан явно
            # Проект использует миллиметры (IfcSIUnit ... .MILLI..METRE), CRS использует метры
            # Scale = 1.0 / 0.001 = 1000.0 (коэффициент преобразования мм в м для координат)
            # Eastings/Northings/OrthogonalHeight = 0.0 (начало координат в точке отсчёта)
            coord_operation = f.create_entity(
                "IfcMapConversion",
                SourceCRS=context,
                TargetCRS=projected_crs,
                Eastings=0.0,
                Northings=0.0,
                OrthogonalHeight=0.0,
                Scale=1000.0,  # Миллиметры в метры (координаты * 1000)
            )

            # Связываем IfcProject с операцией через HasCoordinateOperation
            # В IFC4 IfcProject не имеет HasCoordinateOperation, связь через контекст

    def get_document(self, doc_id: Optional[str] = None) -> Any:
        """
        Получение IFC документа по ID

        Args:
            doc_id: Идентификатор документа (по умолчанию текущий)

        Returns:
            IFC документ

        Raises:
            ValueError: Если документ не найден
        """
        if doc_id is None:
            doc_id = self._current_id

        if doc_id is None or doc_id not in self._documents:
            raise ValueError(f"Документ '{doc_id}' не найден")

        return self._documents[doc_id]

    def get_material_manager(self, doc_id: Optional[str] = None) -> MaterialManager:
        """
        Получение менеджера материалов для документа

        Args:
            doc_id: Идентификатор документа (по умолчанию текущий)

        Returns:
            MaterialManager экземпляр

        Raises:
            ValueError: Если документ не найден
        """
        if doc_id is None:
            doc_id = self._current_id

        if doc_id is None or doc_id not in self._material_managers:
            raise ValueError(f"MaterialManager для документа '{doc_id}' не найден")

        return self._material_managers[doc_id]

    def delete_document(self, doc_id: str) -> None:
        """
        Удаление документа

        Args:
            doc_id: Идентификатор удаляемого документа
        """
        if doc_id in self._documents:
            del self._documents[doc_id]
        if doc_id in self._material_managers:
            del self._material_managers[doc_id]

        if self._current_id == doc_id:
            self._current_id = next(iter(self._documents.keys()), None)

    def reset_document(self, doc_id: Optional[str] = None) -> Any:
        """
        Сброс документа: удаление всех болтов и создание нового

        Args:
            doc_id: Идентификатор документа (по умолчанию текущий)

        Returns:
            Сброшенный IFC документ
        """
        if doc_id is None:
            doc_id = self._current_id

        if doc_id is None or doc_id not in self._documents:
            raise ValueError(f"Документ '{doc_id}' не найден")

        doc = self._documents[doc_id]
        ifc = get_ifcopenshell()

        # Сохраняем базовые структуры
        projects = doc.by_type("IfcProject")
        project = projects[0] if projects else None

        sites = doc.by_type("IfcSite")
        site = sites[0] if sites else None

        buildings = doc.by_type("IfcBuilding")
        building = buildings[0] if buildings else None

        storeys = doc.by_type("IfcBuildingStorey")
        storey = storeys[0] if storeys else None

        # Сохраняем имена материалов для восстановления
        material_names = []
        if doc_id in self._material_managers:
            for name in self._material_managers[doc_id].materials_cache.keys():
                material_names.append(name)

        # Удаляем все MechanicalFastener и связанные сущности
        fasteners = doc.by_type("IfcMechanicalFastener")
        fastener_types = doc.by_type("IfcMechanicalFastenerType")
        rel_defines = doc.by_type("IfcRelDefinesByType")
        rel_aggregates = doc.by_type("IfcRelAggregates")
        rel_connects = doc.by_type("IfcRelConnectsElements")
        rel_contained = doc.by_type("IfcRelContainedInSpatialStructure")
        rel_associates = doc.by_type("IfcRelAssociatesMaterial")
        material_lists = doc.by_type("IfcMaterialList")

        # Удаляем отношения
        for entity in rel_defines + rel_aggregates + rel_connects + rel_contained + rel_associates:
            try:
                doc.remove(entity)
            except Exception:
                pass

        # Удаляем болты и их типы
        for entity in fasteners + fastener_types:
            try:
                doc.remove(entity)
            except Exception:
                pass

        # Удаляем материалы и списки материалов
        for entity in material_lists:
            try:
                doc.remove(entity)
            except Exception:
                pass

        # Пересоздаём базовую структуру с IfcOwnerHistory на ID #1
        timestamp = int(time.time())

        # Согласно buildingSMART IFC Header Policy:
        # - FILE_DESCRIPTION: ViewDefinition для IFC4 — ReferenceView_V1.2
        # - FILE_NAME: name, time_stamp (ISO 8601), author, organization,
        #              preprocessor_version, originating_system, authorization
        # - originating_system формат: "Company - Application - Version"

        spf_content = f"""ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [ReferenceView_V1.2]'),'2;1');
FILE_NAME('anchor_bolt.ifc','{time.strftime('%Y-%m-%dT%H:%M:%S')}',('Anchor Bolt Generator'),('ABG'),'Anchor Bolt Generator 1.0','ABG - Anchor Bolt Generator - 1.0','none');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCOWNERHISTORY(#4,#6,$,$,$,$,$,{timestamp});
#2=IFCPERSON('abg-user',$,$,$,$,$,$,$);
#3=IFCORGANIZATION('ABG','ABG',$,$,$);
#4=IFCPERSONANDORGANIZATION(#2,#3,$);
#5=IFCORGANIZATION('ABG','ABG',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','Anchor Bolt Generator','ABG');
ENDSEC;
END-ISO-10303-21;
"""

        # Сохраняем во временный файл и открываем
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ifc", delete=False) as tmp:
            tmp.write(spf_content)
            tmp_path = tmp.name

        new_doc = ifcopenshell.open(tmp_path)
        os.unlink(tmp_path)

        # Сохраняем ссылку на OwnerHistory
        new_doc.owner_history = new_doc.by_id(1)

        self._create_base_structure(new_doc)

        # Восстанавливаем material_manager
        self._documents[doc_id] = new_doc
        self._material_managers[doc_id] = MaterialManager(new_doc)

        # Восстанавливаем материалы
        for mat_name in material_names:
            self._material_managers[doc_id].create_material(mat_name, category="Steel")

        return new_doc

    def list_documents(self) -> list:
        """
        Получение списка всех документов

        Returns:
            Список идентификаторов документов
        """
        return list(self._documents.keys())

    def get_current_id(self) -> Optional[str]:
        """
        Получение идентификатора текущего документа

        Returns:
            Идентификатор текущего документа или None
        """
        return self._current_id

    def clear_all(self) -> None:
        """Очистка всех документов"""
        self._documents.clear()
        self._material_managers.clear()
        self._current_id = None


# =============================================================================
# Глобальный менеджер (для обратной совместимости)
# =============================================================================

_manager: Optional[IFCDocumentManager] = None


def get_manager() -> IFCDocumentManager:
    """
    Получение глобального менеджера документов

    Returns:
        IFCDocumentManager экземпляр
    """
    global _manager
    if _manager is None:
        _manager = IFCDocumentManager()
    return _manager


def reset_manager() -> None:
    """Сброс глобального менеджера"""
    global _manager
    _manager = None
