"""IFC parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional


IFC_AVAILABLE = False


class ElementCategory(str, Enum):
    STRUCTURAL = "Structural"
    ARCHITECTURAL = "Architectural"
    MEP = "MEP"
    OTHER = "Other"


@dataclass
class BIMElement:
    global_id: str
    ifc_type: str
    name: Optional[str]
    category: ElementCategory

    def to_dict(self) -> Dict[str, str]:
        return {
            "global_id": self.global_id,
            "ifc_type": self.ifc_type,
            "name": self.name or "",
            "category": self.category.value,
        }


@dataclass
class IFCModelInfo:
    schema_version: str
    application: str
    project_name: str
    site_name: Optional[str]
    building_name: Optional[str]
    author: Optional[str]
    organization: Optional[str]
    creation_date: Optional[str]


@dataclass
class IFCParseResult:
    model_info: Optional[IFCModelInfo] = None
    elements: List[BIMElement] = field(default_factory=list)
    element_counts: Dict[str, int] = field(default_factory=dict)
    levels: List[str] = field(default_factory=list)
    materials: List[str] = field(default_factory=list)
    total_elements: int = 0
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "model_info": self.model_info.__dict__ if self.model_info else None,
            "elements": [element.to_dict() for element in self.elements],
            "element_counts": self.element_counts,
            "levels": self.levels,
            "materials": self.materials,
            "total_elements": self.total_elements,
            "errors": self.errors,
        }


def _get_category(ifc_type: str) -> ElementCategory:
    structural = {"ifcwall", "ifccolumn", "ifcbeam", "ifcslab"}
    architectural = {"ifcdoor", "ifcwindow", "ifcroof"}
    mep = {"ifcpipe", "ifcduct", "ifcpipe segment", "ifcpipesegment"}
    lower = ifc_type.lower()
    if lower in structural:
        return ElementCategory.STRUCTURAL
    if lower in architectural:
        return ElementCategory.ARCHITECTURAL
    if lower in mep:
        return ElementCategory.MEP
    return ElementCategory.OTHER


def parse_ifc(path: str) -> IFCParseResult:
    if not Path(path).exists():
        return IFCParseResult(total_elements=0, errors=["File not found"])
    return IFCParseResult(total_elements=0, errors=["IFC parsing not enabled"])


def parse_ifc_bytes(content: bytes) -> IFCParseResult:
    if not content:
        return IFCParseResult(total_elements=0, errors=["Empty IFC content"])
    return IFCParseResult(total_elements=0, errors=["IFC parsing not enabled"])
