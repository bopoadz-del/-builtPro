"""Quantity Take-Off (QTO) API for BIM-based quantity extraction and cost estimation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, Body
from pydantic import BaseModel

from backend.services.qto_pipeline import generate_qto
from backend.services.ifc_parser import (
    IFC_AVAILABLE,
    IFCParseResult,
    parse_ifc_bytes,
    ElementCategory,
    BIMElement,
)

logger = logging.getLogger(__name__)
router = APIRouter()


class QuantityType(str, Enum):
    """Types of quantities for construction."""
    VOLUME = "volume"
    AREA = "area"
    LENGTH = "length"
    COUNT = "count"
    WEIGHT = "weight"


class UnitSystem(str, Enum):
    """Measurement unit systems."""
    METRIC = "metric"
    IMPERIAL = "imperial"


# Default unit rates for cost estimation (SAR - Saudi Riyal)
DEFAULT_UNIT_RATES = {
    "IfcWall": {"rate": 850, "unit": "m²", "description": "Concrete/Masonry Wall"},
    "IfcWallStandardCase": {"rate": 850, "unit": "m²", "description": "Standard Wall"},
    "IfcColumn": {"rate": 12000, "unit": "m³", "description": "Concrete Column"},
    "IfcBeam": {"rate": 11000, "unit": "m³", "description": "Concrete Beam"},
    "IfcSlab": {"rate": 450, "unit": "m²", "description": "Concrete Slab"},
    "IfcFooting": {"rate": 8500, "unit": "m³", "description": "Foundation Footing"},
    "IfcDoor": {"rate": 2500, "unit": "ea", "description": "Door (standard)"},
    "IfcWindow": {"rate": 3500, "unit": "ea", "description": "Window (standard)"},
    "IfcStair": {"rate": 15000, "unit": "ea", "description": "Staircase"},
    "IfcRoof": {"rate": 650, "unit": "m²", "description": "Roof Assembly"},
    "IfcRailing": {"rate": 450, "unit": "m", "description": "Railing/Handrail"},
    "IfcCurtainWall": {"rate": 2200, "unit": "m²", "description": "Curtain Wall"},
    "IfcReinforcingBar": {"rate": 4500, "unit": "ton", "description": "Reinforcement Steel"},
    "IfcPipeSegment": {"rate": 180, "unit": "m", "description": "Piping"},
    "IfcDuctSegment": {"rate": 320, "unit": "m", "description": "HVAC Duct"},
    "IfcFurniture": {"rate": 5000, "unit": "ea", "description": "Furniture Item"},
}

# Typical quantities per element (fallback when not in IFC)
TYPICAL_QUANTITIES = {
    "IfcWall": {"area": 15.0, "volume": 2.25, "length": 5.0},  # 5m x 3m wall, 15cm thick
    "IfcWallStandardCase": {"area": 15.0, "volume": 2.25, "length": 5.0},
    "IfcColumn": {"volume": 0.36, "height": 3.0},  # 0.4m x 0.3m x 3m
    "IfcBeam": {"volume": 0.27, "length": 6.0},  # 0.3m x 0.15m x 6m
    "IfcSlab": {"area": 25.0, "volume": 5.0},  # 5m x 5m x 0.2m
    "IfcFooting": {"volume": 1.5},  # 1.5m x 1.5m x 0.67m
    "IfcDoor": {"count": 1, "area": 2.0},
    "IfcWindow": {"count": 1, "area": 1.5},
    "IfcStair": {"count": 1, "area": 8.0},
    "IfcRoof": {"area": 50.0},
    "IfcRailing": {"length": 3.0},
    "IfcCurtainWall": {"area": 20.0},
    "IfcReinforcingBar": {"weight": 0.05},  # tons per bar
    "IfcPipeSegment": {"length": 3.0},
    "IfcDuctSegment": {"length": 2.5},
}


@dataclass
class QuantityItem:
    """Single quantity line item."""
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
    """Complete QTO summary."""
    items: list[QuantityItem] = field(default_factory=list)
    total_cost: float = 0.0
    currency: str = "SAR"
    category_totals: dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "items": [
                {
                    "element_type": item.element_type,
                    "description": item.description,
                    "count": item.count,
                    "quantity": round(item.quantity, 2),
                    "unit": item.unit,
                    "unit_rate": item.unit_rate,
                    "total_cost": round(item.total_cost, 2),
                    "category": item.category
                }
                for item in self.items
            ],
            "total_cost": round(self.total_cost, 2),
            "currency": self.currency,
            "category_totals": {k: round(v, 2) for k, v in self.category_totals.items()}
        }


class QTORequest(BaseModel):
    """Request for QTO calculation from element data."""
    elements: list[dict]
    unit_rates: Optional[dict] = None
    currency: str = "SAR"


class QTOResponse(BaseModel):
    """QTO calculation response."""
    items: list[dict]
    total_cost: float
    currency: str
    category_totals: dict[str, float]
    element_count: int
    model_id: Optional[str] = None


class CostDatabaseEntry(BaseModel):
    """Custom cost database entry."""
    element_type: str
    rate: float
    unit: str
    description: Optional[str] = None


def _calculate_element_quantity(element: BIMElement) -> tuple[float, str]:
    """Calculate the primary quantity for an element."""
    # First try to get from element's own quantities
    if element.quantities:
        for q in element.quantities:
            if q.quantity_type == "Volume" and q.value > 0:
                return q.value, "m³"
            elif q.quantity_type == "Area" and q.value > 0:
                return q.value, "m²"
            elif q.quantity_type == "Length" and q.value > 0:
                return q.value, "m"
    
    # Fallback to typical quantities
    typical = TYPICAL_QUANTITIES.get(element.ifc_type, {})
    
    # Choose appropriate quantity based on element type
    if element.ifc_type in ["IfcColumn", "IfcBeam", "IfcFooting"]:
        return typical.get("volume", 1.0), "m³"
    elif element.ifc_type in ["IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcRoof", "IfcCurtainWall"]:
        return typical.get("area", 1.0), "m²"
    elif element.ifc_type in ["IfcRailing", "IfcPipeSegment", "IfcDuctSegment"]:
        return typical.get("length", 1.0), "m"
    elif element.ifc_type in ["IfcDoor", "IfcWindow", "IfcStair", "IfcFurniture"]:
        return 1.0, "ea"
    elif element.ifc_type == "IfcReinforcingBar":
        return typical.get("weight", 0.05), "ton"
    
    return 1.0, "ea"


def _calculate_qto_from_ifc(result: IFCParseResult, custom_rates: Optional[dict] = None) -> QTOSummary:
    """Calculate QTO from parsed IFC result."""
    rates = {**DEFAULT_UNIT_RATES}
    if custom_rates:
        rates.update(custom_rates)
    
    # Group elements by type
    elements_by_type: dict[str, list[BIMElement]] = {}
    for element in result.elements:
        if element.ifc_type not in elements_by_type:
            elements_by_type[element.ifc_type] = []
        elements_by_type[element.ifc_type].append(element)
    
    items = []
    total_cost = 0.0
    category_totals: dict[str, float] = {}
    
    for ifc_type, elements in elements_by_type.items():
        rate_info = rates.get(ifc_type, {"rate": 0, "unit": "ea", "description": ifc_type})
        
        # Calculate total quantity
        total_quantity = 0.0
        for element in elements:
            qty, _ = _calculate_element_quantity(element)
            total_quantity += qty
        
        # Calculate cost
        item_cost = total_quantity * rate_info["rate"]
        total_cost += item_cost
        
        # Get category
        category = elements[0].category.value if elements else "Other"
        category_totals[category] = category_totals.get(category, 0) + item_cost
        
        items.append(QuantityItem(
            element_type=ifc_type,
            description=rate_info.get("description", ifc_type),
            count=len(elements),
            quantity=total_quantity,
            unit=rate_info["unit"],
            unit_rate=rate_info["rate"],
            total_cost=item_cost,
            category=category
        ))
    
    return QTOSummary(
        items=items,
        total_cost=total_cost,
        category_totals=category_totals
    )


@router.get('/qto')
def get_qto(file_id: str = Query(...), mime_type: str = Query(...)):
    """Legacy QTO endpoint - generates QTO from file ID."""
    try:
        result = generate_qto(file_id, mime_type)
        return {'status': 'ok', 'quantities': result}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


@router.get('/qto/rates')
async def get_default_rates():
    """Get the default unit rates for QTO calculation."""
    return {
        "rates": DEFAULT_UNIT_RATES,
        "currency": "SAR",
        "note": "Rates are indicative for Saudi Arabia market (2024). Adjust based on actual project conditions."
    }


@router.post('/qto/rates')
async def update_rates(entries: list[CostDatabaseEntry]):
    """Update unit rates for QTO calculation (session only)."""
    updated = {}
    for entry in entries:
        DEFAULT_UNIT_RATES[entry.element_type] = {
            "rate": entry.rate,
            "unit": entry.unit,
            "description": entry.description or entry.element_type
        }
        updated[entry.element_type] = DEFAULT_UNIT_RATES[entry.element_type]
    
    return {
        "status": "updated",
        "updated_rates": updated
    }


@router.post('/qto/calculate', response_model=QTOResponse)
async def calculate_qto(
    file: UploadFile = File(...),
    currency: str = Form("SAR"),
    apply_contingency: float = Form(0.0, description="Contingency percentage (0-50)")
):
    """Calculate QTO from an uploaded IFC file.
    
    Parses the IFC file, extracts quantities, and calculates costs
    using default or custom unit rates.
    """
    if not file.filename or not file.filename.lower().endswith('.ifc'):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid IFC file"
        )
    
    if apply_contingency < 0 or apply_contingency > 50:
        raise HTTPException(
            status_code=400,
            detail="Contingency must be between 0 and 50 percent"
        )
    
    try:
        content = await file.read()
        
        # Parse IFC
        parse_result = parse_ifc_bytes(content, file.filename)
        
        if parse_result.total_elements == 0:
            raise HTTPException(
                status_code=400,
                detail="No elements found in IFC file"
            )
        
        # Calculate QTO
        qto = _calculate_qto_from_ifc(parse_result)
        qto.currency = currency
        
        # Apply contingency
        if apply_contingency > 0:
            contingency_multiplier = 1 + (apply_contingency / 100)
            qto.total_cost *= contingency_multiplier
            for cat in qto.category_totals:
                qto.category_totals[cat] *= contingency_multiplier
            for item in qto.items:
                item.total_cost *= contingency_multiplier
        
        # Generate model ID
        import hashlib
        model_id = hashlib.md5(content[:1000]).hexdigest()[:12]
        
        return QTOResponse(
            items=[
                {
                    "element_type": item.element_type,
                    "description": item.description,
                    "count": item.count,
                    "quantity": round(item.quantity, 2),
                    "unit": item.unit,
                    "unit_rate": item.unit_rate,
                    "total_cost": round(item.total_cost, 2),
                    "category": item.category
                }
                for item in qto.items
            ],
            total_cost=round(qto.total_cost, 2),
            currency=qto.currency,
            category_totals={k: round(v, 2) for k, v in qto.category_totals.items()},
            element_count=parse_result.total_elements,
            model_id=model_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QTO calculation failed: {e}")
        raise HTTPException(status_code=500, detail=f"QTO calculation failed: {str(e)}")


@router.post('/qto/calculate-manual')
async def calculate_qto_manual(request: QTORequest):
    """Calculate QTO from manually provided element data.
    
    Useful for:
    - Testing without IFC file
    - Custom element lists
    - Integration with other systems
    """
    rates = {**DEFAULT_UNIT_RATES}
    if request.unit_rates:
        for k, v in request.unit_rates.items():
            if isinstance(v, dict):
                rates[k] = v
            else:
                rates[k] = {"rate": v, "unit": "ea", "description": k}
    
    items = []
    total_cost = 0.0
    category_totals: dict[str, float] = {}
    
    # Group by element type
    elements_by_type: dict[str, list[dict]] = {}
    for elem in request.elements:
        elem_type = elem.get("ifc_type", elem.get("type", "Unknown"))
        if elem_type not in elements_by_type:
            elements_by_type[elem_type] = []
        elements_by_type[elem_type].append(elem)
    
    for elem_type, elements in elements_by_type.items():
        rate_info = rates.get(elem_type, {"rate": 0, "unit": "ea", "description": elem_type})
        
        # Sum quantities
        total_qty = 0.0
        for elem in elements:
            qty = elem.get("quantity", elem.get("area", elem.get("volume", elem.get("length", 1.0))))
            total_qty += float(qty)
        
        item_cost = total_qty * rate_info["rate"]
        total_cost += item_cost
        
        category = elem.get("category", "Other")
        category_totals[category] = category_totals.get(category, 0) + item_cost
        
        items.append({
            "element_type": elem_type,
            "description": rate_info.get("description", elem_type),
            "count": len(elements),
            "quantity": round(total_qty, 2),
            "unit": rate_info["unit"],
            "unit_rate": rate_info["rate"],
            "total_cost": round(item_cost, 2),
            "category": category
        })
    
    return QTOResponse(
        items=items,
        total_cost=round(total_cost, 2),
        currency=request.currency,
        category_totals={k: round(v, 2) for k, v in category_totals.items()},
        element_count=len(request.elements)
    )


@router.post('/qto/compare')
async def compare_qto(
    baseline: QTORequest = Body(..., description="Baseline/budget QTO"),
    actual: QTORequest = Body(..., description="Actual/current QTO")
):
    """Compare two QTOs to identify variances.
    
    Useful for:
    - Budget vs actual comparison
    - Design revision impact analysis
    - Value engineering assessment
    """
    # Calculate both QTOs
    baseline_items = {}
    baseline_total = 0.0
    for elem in baseline.elements:
        elem_type = elem.get("ifc_type", elem.get("type", "Unknown"))
        qty = float(elem.get("quantity", 1.0))
        rate = DEFAULT_UNIT_RATES.get(elem_type, {}).get("rate", 0)
        cost = qty * rate
        
        if elem_type not in baseline_items:
            baseline_items[elem_type] = {"quantity": 0, "cost": 0, "count": 0}
        baseline_items[elem_type]["quantity"] += qty
        baseline_items[elem_type]["cost"] += cost
        baseline_items[elem_type]["count"] += 1
        baseline_total += cost
    
    actual_items = {}
    actual_total = 0.0
    for elem in actual.elements:
        elem_type = elem.get("ifc_type", elem.get("type", "Unknown"))
        qty = float(elem.get("quantity", 1.0))
        rate = DEFAULT_UNIT_RATES.get(elem_type, {}).get("rate", 0)
        cost = qty * rate
        
        if elem_type not in actual_items:
            actual_items[elem_type] = {"quantity": 0, "cost": 0, "count": 0}
        actual_items[elem_type]["quantity"] += qty
        actual_items[elem_type]["cost"] += cost
        actual_items[elem_type]["count"] += 1
        actual_total += cost
    
    # Calculate variances
    all_types = set(baseline_items.keys()) | set(actual_items.keys())
    variances = []
    
    for elem_type in all_types:
        base = baseline_items.get(elem_type, {"quantity": 0, "cost": 0, "count": 0})
        act = actual_items.get(elem_type, {"quantity": 0, "cost": 0, "count": 0})
        
        qty_variance = act["quantity"] - base["quantity"]
        cost_variance = act["cost"] - base["cost"]
        pct_variance = ((act["cost"] / base["cost"]) - 1) * 100 if base["cost"] > 0 else 100 if act["cost"] > 0 else 0
        
        variances.append({
            "element_type": elem_type,
            "baseline_quantity": round(base["quantity"], 2),
            "actual_quantity": round(act["quantity"], 2),
            "quantity_variance": round(qty_variance, 2),
            "baseline_cost": round(base["cost"], 2),
            "actual_cost": round(act["cost"], 2),
            "cost_variance": round(cost_variance, 2),
            "variance_percent": round(pct_variance, 1),
            "status": "over" if cost_variance > 0 else "under" if cost_variance < 0 else "on_budget"
        })
    
    # Sort by absolute variance
    variances.sort(key=lambda x: abs(x["cost_variance"]), reverse=True)
    
    return {
        "baseline_total": round(baseline_total, 2),
        "actual_total": round(actual_total, 2),
        "total_variance": round(actual_total - baseline_total, 2),
        "variance_percent": round(((actual_total / baseline_total) - 1) * 100, 1) if baseline_total > 0 else 0,
        "variances": variances,
        "summary": {
            "over_budget_items": len([v for v in variances if v["status"] == "over"]),
            "under_budget_items": len([v for v in variances if v["status"] == "under"]),
            "on_budget_items": len([v for v in variances if v["status"] == "on_budget"])
        }
    }


@router.post('/qto/export')
async def export_qto(
    file: UploadFile = File(...),
    format: str = Form("csv", description="Export format: csv, json"),
    currency: str = Form("SAR")
):
    """Calculate QTO and export to CSV or JSON format."""
    if format not in ["csv", "json"]:
        raise HTTPException(status_code=400, detail="Format must be 'csv' or 'json'")
    
    # Calculate QTO
    content = await file.read()
    parse_result = parse_ifc_bytes(content, file.filename or "model.ifc")
    qto = _calculate_qto_from_ifc(parse_result)
    qto.currency = currency
    
    if format == "json":
        return qto.to_dict()
    
    # Generate CSV
    import io
    output = io.StringIO()
    output.write("Element Type,Description,Count,Quantity,Unit,Unit Rate,Total Cost,Category\n")
    
    for item in qto.items:
        output.write(f'"{item.element_type}","{item.description}",{item.count},{item.quantity:.2f},"{item.unit}",{item.unit_rate},{item.total_cost:.2f},"{item.category}"\n')
    
    output.write(f'\n"TOTAL","",,,,"",{qto.total_cost:.2f},""\n')
    
    from fastapi.responses import Response
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=qto_export.csv"}
    )
