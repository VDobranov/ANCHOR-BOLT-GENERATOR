"""
geometry_converter.py — Конвертация IFC геометрии в Three.js mesh
Использует ifcopenshell.geom для извлечения вершин и индексов
"""

import numpy as np
from utils import get_ifcopenshell


def _get_ifcopenshell_geom():
    """Ленивый импорт ifcopenshell.geom"""
    ifc = get_ifcopenshell()
    if ifc is None:
        return None
    try:
        import ifcopenshell.geom
        return ifcopenshell.geom
    except ImportError:
        return None


def convert_ifc_to_mesh(ifc_file, element, weld_vertices=True):
    """
    Конвертация IFC элемента в Three.js mesh данные

    Args:
        ifc_file: IFC документ
        element: IfcEntity (IfcMechanicalFastener или другой)
        weld_vertices: Сваривать ли вершины (уменьшает количество вершин)

    Returns:
        dict с vertices, indices, normals или None если геометрия не извлечена
    """
    geom = _get_ifcopenshell_geom()
    if geom is None:
        print(f"Warning: ifcopenshell.geom not available")
        return None

    try:
        # Настройка параметров
        settings = geom.settings()
        settings.set(settings.WELD_VERTICES, weld_vertices)
        settings.set(settings.USE_WORLD_COORDS, True)

        # Проверка наличия геометрии у элемента
        if not hasattr(element, 'Representation') or not element.Representation:
            print(f"Warning: Element {element.GlobalId} has no representation")
            return None

        # Создание формы
        shape = geom.create_shape(settings, element)

        # Проверка геометрии
        if not shape.geometry or len(shape.geometry.verts) == 0:
            print(f"Warning: Element {element.GlobalId} has empty geometry")
            return None

        # Извлечение геометрии
        verts = np.array(shape.geometry.verts)
        faces = np.array(shape.geometry.faces)
        normals = np.array(shape.geometry.normals)

        # Преобразование индексов граней в плоский список
        indices = faces.flatten()

        return {
            'vertices': verts.tolist(),
            'indices': indices.tolist(),
            'normals': normals.tolist()
        }

    except Exception as e:
        print(f"Warning: Could not convert element {element.GlobalId} ({element.ObjectType}): {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_assembly_to_meshes(ifc_file, components, color_map=None):
    """
    Конвертация сборки болта в список Three.js mesh

    Args:
        ifc_file: IFC документ
        components: список компонентов (IfcMechanicalFastener)
        color_map: dict {ObjectType: color} для раскраски

    Returns:
        dict с meshes для Three.js
    """
    if color_map is None:
        color_map = {
            'STUD': 0x8B8B8B,
            'WASHER': 0xA9A9A9,
            'NUT': 0x696969,
            'ANCHORBOLT': 0x4F4F4F
        }

    meshes = []
    geom_failures = []

    for component in components:
        mesh_data = convert_ifc_to_mesh(ifc_file, component)
        if mesh_data is None:
            geom_failures.append(f"{component.ObjectType} ({component.Name})")
            continue

        comp_type = component.ObjectType or 'UNKNOWN'
        color = color_map.get(comp_type, 0xCCCCCC)

        meshes.append({
            'id': component.id(),
            'name': component.Name or f'Component_{component.id()}',
            'vertices': mesh_data['vertices'],
            'indices': mesh_data['indices'],
            'normals': mesh_data['normals'],
            'color': color,
            'metadata': {
                'Type': comp_type,
                'GlobalId': component.GlobalId
            }
        })

    if geom_failures:
        print(f"Warning: ifcopenshell.geom failed for: {geom_failures}")
        print("  Falling back to manual mesh generation")
        return None  # Возвращаем None для использования fallback

    return {'meshes': meshes}


def generate_bolt_mesh_from_ifc(ifc_file, assembly_data):
    """
    Генерация mesh данных из готовой IFC сборки
    
    Args:
        ifc_file: IFC документ
        assembly_data: dict с assembly и components
    
    Returns:
        dict с meshes для Three.js
    """
    components = assembly_data.get('components', [])
    return convert_assembly_to_meshes(ifc_file, components)
