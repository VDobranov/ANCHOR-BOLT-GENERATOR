# IFC-иерархия

## Структура документа

IFC-документ строится по иерархическому принципу от проекта к отдельным элементам.

```
IfcProject
└── IfcSite
    └── IfcBuilding
        └── IfcBuildingStorey
            └── IfcMechanicalFastener (Сборка: ANCHORBOLT)
                ├── IfcMechanicalFastener (Шпилька: USERDEFINED)
                ├── IfcMechanicalFastener (Гайка #1: USERDEFINED)
                ├── IfcMechanicalFastener (Гайка #2: USERDEFINED)
                ├── IfcMechanicalFastener (Шайба #1: USERDEFINED)
                └── IfcMechanicalFastener (Шайба #2: USERDEFINED)
```

## Уровни иерархии

### IfcProject

Корневой элемент IFC-документа. Содержит:

- Имя проекта
- Описание
- Версию IFC (IFC4 ADD2 TC1)
- Единицы измерения
- Геометрический контекст

### IfcSite

Участок земли или территория строительства. Параметры:

- Название участка
- Координаты (опционально)
- Система координат

### IfcBuilding

Здание или сооружение. Параметры:

- Название здания
- Относительное размещение

### IfcBuildingStorey

Этаж или уровень сооружения. Для фундаментных болтов:

- Уровень фундамента
- Отметка низа болта (Z=0)

## IfcMechanicalFastener

### Сборка (ANCHORBOLT)

Представляет собой контейнер для компонентов болта:

- `ObjectType` = "ANCHORBOLT"
- `Name` = "Болт фундаментный {тип}.{диаметр}x{длина}"
- `Description` = описание по ГОСТ

### Компоненты

| Компонент | ObjectType  | Описание                 |
| --------- | ----------- | ------------------------ |
| Шпилька   | USERDEFINED | Основной стержень болта  |
| Гайка     | USERDEFINED | Крепёжная гайка (2 шт.)  |
| Шайба     | USERDEFINED | Опорная шайба (1 шт.)    |
| Плита     | USERDEFINED | Анкерная плита (тип 2.1) |

## Представление геометрии

### RepresentationMaps

Геометрия определяется один раз на уровне типа:

```
IfcMechanicalFastenerType
└── RepresentationMaps
    └── IfcRepresentationMap
        └── MappedRepresentation (IfcShapeRepresentation)
            └── Items (IfcSweptDiskSolid / IfcExtrudedAreaSolid)
```

### IfcMappedItem

Экземпляры ссылаются на тип через IfcMappedItem:

```
IfcProductDefinitionShape
└── Representations
    └── IfcMappedItem
        └── MappingSource → IfcRepresentationMap
        └── MappingTarget → IfcCartesianTransformationOperator3D
```

## Позиционирование

### ObjectPlacement

Каждый компонент размещается через относительное размещение:

- `IfcLocalPlacement`
- `PlacementRelTo` — родительский объект
- `RelativePlacement` — `IfcAxis2Placement3D`

### Система координат

- Начало (0, 0, 0) — отметка низа резьбы
- Ось Z — продольная ось болта
- Ось X — направление вылета крюка (для типов 1.1, 1.2)

## Материалы

### IfcMaterial

Для каждого компонента определяется материал:

```
IfcMaterial
├── Name = "09Г2С"
├── Description = "ГОСТ 19281-2014"
└── Category = "Сталь"
```

### IfcRelAssociatesMaterial

Связь материала с объектами:

```
IfcRelAssociatesMaterial
├── RelatingMaterial → IfcMaterial
└── RelatedObjects → [IfcMechanicalFastener, ...]
```
