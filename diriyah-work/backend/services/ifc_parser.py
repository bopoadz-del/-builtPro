"""IFC (Industry Foundation Classes) Parser Service.

Parses IFC/BIM files to extract building elements, properties, quantities, and relationships.
Uses IfcOpenShell when available, with fallback parsing for basic extraction.
"""

from __future__ import annotations

import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import IfcOpenShell
try:
    import ifcopenshell
    import ifcopenshell.geom
    import ifcopenshell.util.element as element_util
    IFC_AVAILABLE = True
except ImportError:
    ifcopenshell = None
    element_util = None
    IFC_AVAILABLE = False
    logger.info("IfcOpenShell not installed - using fallback IFC parsing")


class ElementCategory(str, Enum):
    """BIM element categories."""
    STRUCTURAL = "Structural"
    ARCHITECTURAL = "Architectural"
    MEP = "MEP"
    SITE = "Site"
    FURNITURE = "Furniture"
    OTHER = "Other"


@dataclass
class PropertySet:
    """Property set containing element properties."""
    name: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Quantity:
    """Quantity measurement for an element."""
    name: str
    value: float
    unit: str
    quantity_type: str  # Length, Area, Volume, Count, Weight


@dataclass 
class BIMElement:
    """Represents a building element from the IFC model."""
    global_id: str
    ifc_type: str
    name: Optional[str]
    description: Optional[str] = None
    category: ElementCategory = ElementCategory.OTHER
    level: Optional[str] = None
    material: Optional[str] = None
    properties: list[PropertySet] = field(default_factory=list)
    quantities: list[Quantity] = field(default_factory=list)
    parent_id: Optional[str] = None
    children_ids: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "global_id": self.global_id,
            "ifc_type": self.ifc_type,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "level": self.level,
            "material": self.material,
            "properties": [
                {"name": ps.name, "properties": ps.properties}
                for ps in self.properties
            ],
            "quantities": [
                {"name": q.name, "value": q.value, "unit": q.unit, "type": q.quantity_type}
                for q in self.quantities
            ],
            "parent_id": self.parent_id,
            "children_ids": self.children_ids
        }


@dataclass
class IFCModelInfo:
    """High-level information about an IFC model."""
    schema_version: str
    application: Optional[str]
    project_name: Optional[str]
    site_name: Optional[str]
    building_name: Optional[str]
    author: Optional[str]
    organization: Optional[str]
    creation_date: Optional[str]


@dataclass
class IFCParseResult:
    """Complete result of parsing an IFC file."""
    model_info: IFCModelInfo
    elements: list[BIMElement]
    element_counts: dict[str, int]
    levels: list[str]
    materials: list[str]
    total_elements: int
    errors: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "model_info": {
                "schema_version": self.model_info.schema_version,
                "application": self.model_info.application,
                "project_name": self.model_info.project_name,
                "site_name": self.model_info.site_name,
                "building_name": self.model_info.building_name,
                "author": self.model_info.author,
                "organization": self.model_info.organization,
                "creation_date": self.model_info.creation_date
            },
            "elements": [e.to_dict() for e in self.elements],
            "element_counts": self.element_counts,
            "levels": self.levels,
            "materials": self.materials,
            "total_elements": self.total_elements,
            "errors": self.errors
        }


# Mapping IFC types to categories
IFC_TYPE_CATEGORIES = {
    # Structural
    "IfcBeam": ElementCategory.STRUCTURAL,
    "IfcColumn": ElementCategory.STRUCTURAL,
    "IfcFooting": ElementCategory.STRUCTURAL,
    "IfcPile": ElementCategory.STRUCTURAL,
    "IfcSlab": ElementCategory.STRUCTURAL,
    "IfcWall": ElementCategory.STRUCTURAL,
    "IfcWallStandardCase": ElementCategory.STRUCTURAL,
    "IfcRoof": ElementCategory.STRUCTURAL,
    "IfcStair": ElementCategory.STRUCTURAL,
    "IfcStairFlight": ElementCategory.STRUCTURAL,
    "IfcRamp": ElementCategory.STRUCTURAL,
    "IfcRampFlight": ElementCategory.STRUCTURAL,
    "IfcRailing": ElementCategory.STRUCTURAL,
    "IfcReinforcingBar": ElementCategory.STRUCTURAL,
    "IfcReinforcingMesh": ElementCategory.STRUCTURAL,
    "IfcTendon": ElementCategory.STRUCTURAL,
    
    # Architectural
    "IfcDoor": ElementCategory.ARCHITECTURAL,
    "IfcWindow": ElementCategory.ARCHITECTURAL,
    "IfcCurtainWall": ElementCategory.ARCHITECTURAL,
    "IfcCovering": ElementCategory.ARCHITECTURAL,
    "IfcPlate": ElementCategory.ARCHITECTURAL,
    
    # MEP
    "IfcPipeSegment": ElementCategory.MEP,
    "IfcPipeFitting": ElementCategory.MEP,
    "IfcDuctSegment": ElementCategory.MEP,
    "IfcDuctFitting": ElementCategory.MEP,
    "IfcCableSegment": ElementCategory.MEP,
    "IfcCableFitting": ElementCategory.MEP,
    "IfcFlowTerminal": ElementCategory.MEP,
    "IfcSanitaryTerminal": ElementCategory.MEP,
    "IfcLightFixture": ElementCategory.MEP,
    "IfcElectricAppliance": ElementCategory.MEP,
    "IfcPump": ElementCategory.MEP,
    "IfcFan": ElementCategory.MEP,
    "IfcBoiler": ElementCategory.MEP,
    "IfcChiller": ElementCategory.MEP,
    
    # Site
    "IfcSite": ElementCategory.SITE,
    "IfcGeographicElement": ElementCategory.SITE,
    
    # Furniture
    "IfcFurniture": ElementCategory.FURNITURE,
    "IfcFurnishingElement": ElementCategory.FURNITURE,
}


def _get_category(ifc_type: str) -> ElementCategory:
    """Get element category from IFC type."""
    return IFC_TYPE_CATEGORIES.get(ifc_type, ElementCategory.OTHER)


def _parse_with_ifcopenshell(file_path: str) -> IFCParseResult:
    """Parse IFC file using IfcOpenShell library."""
    model = ifcopenshell.open(file_path)
    errors = []
    
    # Extract model info
    schema_version = model.schema
    
    # Get project info
    project = None
    site = None
    building = None
    application = None
    author = None
    organization = None
    creation_date = None
    
    try:
        projects = model.by_type("IfcProject")
        if projects:
            project = projects[0]
    except Exception as e:
        errors.append(f"Could not extract project: {e}")
    
    try:
        sites = model.by_type("IfcSite")
        if sites:
            site = sites[0]
    except Exception:
        pass
    
    try:
        buildings = model.by_type("IfcBuilding")
        if buildings:
            building = buildings[0]
    except Exception:
        pass
    
    try:
        owner_history = model.by_type("IfcOwnerHistory")
        if owner_history:
            oh = owner_history[0]
            if hasattr(oh, "OwningApplication") and oh.OwningApplication:
                application = oh.OwningApplication.ApplicationFullName
            if hasattr(oh, "OwningUser") and oh.OwningUser:
                if hasattr(oh.OwningUser, "ThePerson") and oh.OwningUser.ThePerson:
                    person = oh.OwningUser.ThePerson
                    names = []
                    if hasattr(person, "GivenName") and person.GivenName:
                        names.append(person.GivenName)
                    if hasattr(person, "FamilyName") and person.FamilyName:
                        names.append(person.FamilyName)
                    author = " ".join(names) if names else None
                if hasattr(oh.OwningUser, "TheOrganization") and oh.OwningUser.TheOrganization:
                    organization = oh.OwningUser.TheOrganization.Name
            if hasattr(oh, "CreationDate") and oh.CreationDate:
                from datetime import datetime
                try:
                    creation_date = datetime.fromtimestamp(oh.CreationDate).isoformat()
                except Exception:
                    pass
    except Exception:
        pass
    
    model_info = IFCModelInfo(
        schema_version=schema_version,
        application=application,
        project_name=project.Name if project and hasattr(project, "Name") else None,
        site_name=site.Name if site and hasattr(site, "Name") else None,
        building_name=building.Name if building and hasattr(building, "Name") else None,
        author=author,
        organization=organization,
        creation_date=creation_date
    )
    
    # Extract building elements
    elements = []
    element_counts = {}
    levels_set = set()
    materials_set = set()
    
    # Element types to extract
    element_types = [
        "IfcWall", "IfcWallStandardCase", "IfcColumn", "IfcBeam", "IfcSlab",
        "IfcDoor", "IfcWindow", "IfcStair", "IfcRoof", "IfcFooting",
        "IfcRailing", "IfcCurtainWall", "IfcPlate", "IfcCovering",
        "IfcPipeSegment", "IfcDuctSegment", "IfcCableSegment",
        "IfcFurniture", "IfcReinforcingBar"
    ]
    
    for ifc_type in element_types:
        try:
            type_elements = model.by_type(ifc_type)
            element_counts[ifc_type] = len(type_elements)
            
            for elem in type_elements:
                try:
                    # Get basic info
                    global_id = elem.GlobalId if hasattr(elem, "GlobalId") else str(id(elem))
                    name = elem.Name if hasattr(elem, "Name") else None
                    description = elem.Description if hasattr(elem, "Description") else None
                    
                    # Get level/storey
                    level = None
                    try:
                        if element_util:
                            container = element_util.get_container(elem)
                            if container and hasattr(container, "Name"):
                                level = container.Name
                                levels_set.add(level)
                    except Exception:
                        pass
                    
                    # Get material
                    material = None
                    try:
                        if hasattr(elem, "HasAssociations"):
                            for rel in elem.HasAssociations:
                                if rel.is_a("IfcRelAssociatesMaterial"):
                                    mat = rel.RelatingMaterial
                                    if hasattr(mat, "Name"):
                                        material = mat.Name
                                        materials_set.add(material)
                                    break
                    except Exception:
                        pass
                    
                    # Get property sets
                    property_sets = []
                    try:
                        if hasattr(elem, "IsDefinedBy"):
                            for rel in elem.IsDefinedBy:
                                if rel.is_a("IfcRelDefinesByProperties"):
                                    pset = rel.RelatingPropertyDefinition
                                    if hasattr(pset, "Name") and hasattr(pset, "HasProperties"):
                                        props = {}
                                        for prop in pset.HasProperties:
                                            if hasattr(prop, "Name") and hasattr(prop, "NominalValue"):
                                                val = prop.NominalValue
                                                if hasattr(val, "wrappedValue"):
                                                    props[prop.Name] = val.wrappedValue
                                        if props:
                                            property_sets.append(PropertySet(name=pset.Name, properties=props))
                    except Exception:
                        pass
                    
                    # Get quantities
                    quantities = []
                    try:
                        if hasattr(elem, "IsDefinedBy"):
                            for rel in elem.IsDefinedBy:
                                if rel.is_a("IfcRelDefinesByProperties"):
                                    qset = rel.RelatingPropertyDefinition
                                    if qset.is_a("IfcElementQuantity") and hasattr(qset, "Quantities"):
                                        for q in qset.Quantities:
                                            q_name = q.Name if hasattr(q, "Name") else "Unknown"
                                            q_value = 0.0
                                            q_unit = ""
                                            q_type = "Count"
                                            
                                            if q.is_a("IfcQuantityLength"):
                                                q_value = q.LengthValue if hasattr(q, "LengthValue") else 0
                                                q_unit = "m"
                                                q_type = "Length"
                                            elif q.is_a("IfcQuantityArea"):
                                                q_value = q.AreaValue if hasattr(q, "AreaValue") else 0
                                                q_unit = "m²"
                                                q_type = "Area"
                                            elif q.is_a("IfcQuantityVolume"):
                                                q_value = q.VolumeValue if hasattr(q, "VolumeValue") else 0
                                                q_unit = "m³"
                                                q_type = "Volume"
                                            elif q.is_a("IfcQuantityWeight"):
                                                q_value = q.WeightValue if hasattr(q, "WeightValue") else 0
                                                q_unit = "kg"
                                                q_type = "Weight"
                                            elif q.is_a("IfcQuantityCount"):
                                                q_value = q.CountValue if hasattr(q, "CountValue") else 0
                                                q_unit = "ea"
                                                q_type = "Count"
                                            
                                            quantities.append(Quantity(
                                                name=q_name,
                                                value=float(q_value) if q_value else 0.0,
                                                unit=q_unit,
                                                quantity_type=q_type
                                            ))
                    except Exception:
                        pass
                    
                    elements.append(BIMElement(
                        global_id=global_id,
                        ifc_type=ifc_type,
                        name=name,
                        description=description,
                        category=_get_category(ifc_type),
                        level=level,
                        material=material,
                        properties=property_sets,
                        quantities=quantities
                    ))
                    
                except Exception as e:
                    errors.append(f"Error parsing element {ifc_type}: {e}")
                    
        except Exception as e:
            errors.append(f"Could not extract {ifc_type}: {e}")
    
    return IFCParseResult(
        model_info=model_info,
        elements=elements,
        element_counts=element_counts,
        levels=sorted(list(levels_set)),
        materials=sorted(list(materials_set)),
        total_elements=len(elements),
        errors=errors
    )


def _parse_with_fallback(file_path: str) -> IFCParseResult:
    """Fallback IFC parsing using regex when IfcOpenShell is unavailable."""
    errors = []
    elements = []
    element_counts = {}
    levels_set = set()
    materials_set = set()
    
    # Read file content
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return IFCParseResult(
            model_info=IFCModelInfo(
                schema_version="Unknown",
                application=None,
                project_name=None,
                site_name=None,
                building_name=None,
                author=None,
                organization=None,
                creation_date=None
            ),
            elements=[],
            element_counts={},
            levels=[],
            materials=[],
            total_elements=0,
            errors=[f"Could not read file: {e}"]
        )
    
    # Extract schema version
    schema_match = re.search(r'FILE_SCHEMA\s*\(\s*\(\s*[\'"]([^\'"]+)[\'"]', content)
    schema_version = schema_match.group(1) if schema_match else "Unknown"
    
    # Extract project name
    project_match = re.search(r"IFCPROJECT\s*\([^,]*,\s*[^,]*,\s*'([^']*)'", content, re.IGNORECASE)
    project_name = project_match.group(1) if project_match else None
    
    # Extract building name
    building_match = re.search(r"IFCBUILDING\s*\([^,]*,\s*[^,]*,\s*'([^']*)'", content, re.IGNORECASE)
    building_name = building_match.group(1) if building_match else None
    
    # Extract site name
    site_match = re.search(r"IFCSITE\s*\([^,]*,\s*[^,]*,\s*'([^']*)'", content, re.IGNORECASE)
    site_name = site_match.group(1) if site_match else None
    
    # Extract organization
    org_match = re.search(r"IFCORGANIZATION\s*\([^,]*,\s*'([^']*)'", content, re.IGNORECASE)
    organization = org_match.group(1) if org_match else None
    
    model_info = IFCModelInfo(
        schema_version=schema_version,
        application=None,
        project_name=project_name,
        site_name=site_name,
        building_name=building_name,
        author=None,
        organization=organization,
        creation_date=None
    )
    
    # Extract elements using regex
    element_patterns = [
        (r"#(\d+)\s*=\s*IFCWALL\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcWall"),
        (r"#(\d+)\s*=\s*IFCWALLSTANDARDCASE\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcWallStandardCase"),
        (r"#(\d+)\s*=\s*IFCCOLUMN\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcColumn"),
        (r"#(\d+)\s*=\s*IFCBEAM\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcBeam"),
        (r"#(\d+)\s*=\s*IFCSLAB\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcSlab"),
        (r"#(\d+)\s*=\s*IFCDOOR\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcDoor"),
        (r"#(\d+)\s*=\s*IFCWINDOW\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcWindow"),
        (r"#(\d+)\s*=\s*IFCSTAIR\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcStair"),
        (r"#(\d+)\s*=\s*IFCROOF\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcRoof"),
        (r"#(\d+)\s*=\s*IFCFOOTING\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcFooting"),
        (r"#(\d+)\s*=\s*IFCRAILING\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcRailing"),
        (r"#(\d+)\s*=\s*IFCFURNITURE\s*\([^,]*,\s*'([^']*)'(?:,\s*'([^']*)')?", "IfcFurniture"),
    ]
    
    for pattern, ifc_type in element_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        element_counts[ifc_type] = len(matches)
        
        for match in matches:
            elem_id = match[0] if len(match) > 0 else "unknown"
            global_id = match[1] if len(match) > 1 else f"fallback_{elem_id}"
            name = match[2] if len(match) > 2 and match[2] else None
            
            elements.append(BIMElement(
                global_id=global_id,
                ifc_type=ifc_type,
                name=name,
                category=_get_category(ifc_type)
            ))
    
    # Extract building storeys
    storey_pattern = r"IFCBUILDINGSTOREY\s*\([^,]*,\s*'[^']*'(?:,\s*'([^']*)')?"
    storey_matches = re.findall(storey_pattern, content, re.IGNORECASE)
    levels_set = set(m for m in storey_matches if m)
    
    # Extract materials
    material_pattern = r"IFCMATERIAL\s*\(\s*'([^']*)'"
    material_matches = re.findall(material_pattern, content, re.IGNORECASE)
    materials_set = set(material_matches)
    
    if not elements:
        errors.append("No elements extracted - IfcOpenShell recommended for full parsing")
    
    return IFCParseResult(
        model_info=model_info,
        elements=elements,
        element_counts=element_counts,
        levels=sorted(list(levels_set)),
        materials=sorted(list(materials_set)),
        total_elements=len(elements),
        errors=errors
    )


def parse_ifc(file_path: str) -> IFCParseResult:
    """Parse an IFC file and extract building elements.
    
    Args:
        file_path: Path to the IFC file
    
    Returns:
        IFCParseResult with model info, elements, and quantities
    """
    if not os.path.exists(file_path):
        return IFCParseResult(
            model_info=IFCModelInfo(
                schema_version="Unknown",
                application=None,
                project_name=None,
                site_name=None,
                building_name=None,
                author=None,
                organization=None,
                creation_date=None
            ),
            elements=[],
            element_counts={},
            levels=[],
            materials=[],
            total_elements=0,
            errors=[f"File not found: {file_path}"]
        )
    
    if IFC_AVAILABLE:
        try:
            return _parse_with_ifcopenshell(file_path)
        except Exception as e:
            logger.error(f"IfcOpenShell parsing failed, using fallback: {e}")
            return _parse_with_fallback(file_path)
    else:
        return _parse_with_fallback(file_path)


def parse_ifc_bytes(content: bytes, filename: str = "model.ifc") -> IFCParseResult:
    """Parse IFC content from bytes.
    
    Args:
        content: IFC file content as bytes
        filename: Original filename for reference
    
    Returns:
        IFCParseResult
    """
    with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        result = parse_ifc(tmp_path)
        return result
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def get_elements_by_type(result: IFCParseResult, ifc_type: str) -> list[BIMElement]:
    """Filter elements by IFC type."""
    return [e for e in result.elements if e.ifc_type == ifc_type]


def get_elements_by_category(result: IFCParseResult, category: ElementCategory) -> list[BIMElement]:
    """Filter elements by category."""
    return [e for e in result.elements if e.category == category]


def get_elements_by_level(result: IFCParseResult, level: str) -> list[BIMElement]:
    """Filter elements by building level/storey."""
    return [e for e in result.elements if e.level == level]


__all__ = [
    "IFC_AVAILABLE",
    "ElementCategory",
    "PropertySet",
    "Quantity",
    "BIMElement",
    "IFCModelInfo",
    "IFCParseResult",
    "parse_ifc",
    "parse_ifc_bytes",
    "get_elements_by_type",
    "get_elements_by_category",
    "get_elements_by_level"
]
