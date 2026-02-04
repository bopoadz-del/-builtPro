"""QTO API helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from fastapi import APIRouter

router = APIRouter(prefix="/qto")

DEFAULT_UNIT_RATES: Dict[str, Dict[str, float | str]] = {
    "IfcWall": {"rate": 850, "unit": "m²"},
    "IfcColumn": {"rate": 900, "unit": "m³"},
    "IfcSlab": {"rate": 450, "unit": "m²"},
}

TYPICAL_QUANTITIES: Dict[str, Dict[str, float]] = {
    "IfcWall": {"area": 100.0},
    "IfcColumn": {"volume": 20.0},
    "IfcSlab": {"area": 200.0},
}


@dataclass
class QuantityItem:
    element_type: str
    description: str
    count: int
    quantity: float
    unit: str
    unit_rate: float
    total_cost: float
    category: str


@dataclass
class QTOSummary:
    items: List[QuantityItem]
    total_cost: float
    category_totals: Dict[str, float]

    def to_dict(self) -> Dict[str, object]:
        return {
            "items": [item.__dict__ for item in self.items],
            "total_cost": self.total_cost,
            "category_totals": self.category_totals,
        }
