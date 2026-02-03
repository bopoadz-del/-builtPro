"""IFC Parser API endpoints for BIM model analysis."""

from __future__ import annotations

import logging
import tempfile
import os
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel

from backend.services.ifc_parser import (
    IFC_AVAILABLE,
    ElementCategory,
    IFCParseResult,
    parse_ifc,
    parse_ifc_bytes,
    get_elements_by_type,
    get_elements_by_category,
    get_elements_by_level,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Store parsed models in memory for the session (demo purposes)
_parsed_models: dict[str, IFCParseResult] = {}


class ElementResponse(BaseModel):
    """Single BIM element response."""
    global_id: str
    ifc_type: str
    name: Optional[str]
    description: Optional[str] = None
    category: str
    level: Optional[str] = None
    material: Optional[str] = None


class ModelInfoResponse(BaseModel):
    """IFC model metadata response."""
    schema_version: str
    application: Optional[str]
    project_name: Optional[str]
    site_name: Optional[str]
    building_name: Optional[str]
    author: Optional[str]
    organization: Optional[str]
    creation_date: Optional[str]


class ParseSummaryResponse(BaseModel):
    """Summary of parsed IFC model."""
    model_id: str
    model_info: ModelInfoResponse
    total_elements: int
    element_counts: dict[str, int]
    levels: list[str]
    materials: list[str]
    categories_summary: dict[str, int]
    errors: list[str]
    ifc_library_available: bool


class ElementsListResponse(BaseModel):
    """Paginated list of elements."""
    elements: list[ElementResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


@router.get("/ifc_parser-ping")
async def ping():
    """Health check endpoint."""
    return {
        "service": "ifc_parser",
        "status": "ok",
        "ifcopenshell_available": IFC_AVAILABLE
    }


@router.get("/ifc/status")
async def ifc_status():
    """Check IFC parsing capability status."""
    return {
        "ifcopenshell_installed": IFC_AVAILABLE,
        "fallback_available": True,
        "supported_types": [
            "IfcWall", "IfcColumn", "IfcBeam", "IfcSlab", "IfcDoor",
            "IfcWindow", "IfcStair", "IfcRoof", "IfcFooting", "IfcRailing",
            "IfcCurtainWall", "IfcFurniture", "IfcPipeSegment", "IfcDuctSegment"
        ],
        "categories": [c.value for c in ElementCategory]
    }


@router.post("/ifc/parse", response_model=ParseSummaryResponse)
async def parse_ifc_file(
    file: UploadFile = File(...),
    model_id: Optional[str] = Form(None)
):
    """Parse an uploaded IFC file and extract BIM elements.
    
    Returns a summary of the model with element counts and metadata.
    The parsed model is cached for subsequent queries using the returned model_id.
    """
    if not file.filename or not file.filename.lower().endswith('.ifc'):
        raise HTTPException(
            status_code=400,
            detail="Please upload a valid IFC file (.ifc extension)"
        )
    
    try:
        content = await file.read()
        
        if len(content) < 100:
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty or too small"
            )
        
        # Parse the IFC file
        result = parse_ifc_bytes(content, file.filename)
        
        # Generate model ID if not provided
        if not model_id:
            import hashlib
            model_id = hashlib.md5(content[:1000]).hexdigest()[:12]
        
        # Cache the parsed result
        _parsed_models[model_id] = result
        
        # Calculate category summary
        categories_summary = {}
        for element in result.elements:
            cat = element.category.value
            categories_summary[cat] = categories_summary.get(cat, 0) + 1
        
        return ParseSummaryResponse(
            model_id=model_id,
            model_info=ModelInfoResponse(
                schema_version=result.model_info.schema_version,
                application=result.model_info.application,
                project_name=result.model_info.project_name,
                site_name=result.model_info.site_name,
                building_name=result.model_info.building_name,
                author=result.model_info.author,
                organization=result.model_info.organization,
                creation_date=result.model_info.creation_date
            ),
            total_elements=result.total_elements,
            element_counts=result.element_counts,
            levels=result.levels,
            materials=result.materials,
            categories_summary=categories_summary,
            errors=result.errors,
            ifc_library_available=IFC_AVAILABLE
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"IFC parsing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse IFC file: {str(e)}")


@router.get("/ifc/{model_id}/elements", response_model=ElementsListResponse)
async def get_model_elements(
    model_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    ifc_type: Optional[str] = Query(None, description="Filter by IFC type (e.g., IfcWall)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    level: Optional[str] = Query(None, description="Filter by building level")
):
    """Get elements from a parsed IFC model with optional filtering.
    
    The model must have been parsed first using /ifc/parse.
    """
    if model_id not in _parsed_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found. Please parse the IFC file first."
        )
    
    result = _parsed_models[model_id]
    elements = result.elements
    
    # Apply filters
    if ifc_type:
        elements = [e for e in elements if e.ifc_type.lower() == ifc_type.lower()]
    
    if category:
        try:
            cat_enum = ElementCategory(category)
            elements = [e for e in elements if e.category == cat_enum]
        except ValueError:
            # Try case-insensitive match
            elements = [e for e in elements if e.category.value.lower() == category.lower()]
    
    if level:
        elements = [e for e in elements if e.level and level.lower() in e.level.lower()]
    
    # Paginate
    total = len(elements)
    start = (page - 1) * page_size
    end = start + page_size
    page_elements = elements[start:end]
    
    return ElementsListResponse(
        elements=[
            ElementResponse(
                global_id=e.global_id,
                ifc_type=e.ifc_type,
                name=e.name,
                description=e.description,
                category=e.category.value,
                level=e.level,
                material=e.material
            )
            for e in page_elements
        ],
        total=total,
        page=page,
        page_size=page_size,
        has_more=end < total
    )


@router.get("/ifc/{model_id}/element/{global_id}")
async def get_element_details(model_id: str, global_id: str):
    """Get detailed information about a specific element including properties and quantities."""
    if model_id not in _parsed_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found"
        )
    
    result = _parsed_models[model_id]
    element = next((e for e in result.elements if e.global_id == global_id), None)
    
    if not element:
        raise HTTPException(
            status_code=404,
            detail=f"Element {global_id} not found in model"
        )
    
    return element.to_dict()


@router.get("/ifc/{model_id}/summary")
async def get_model_summary(model_id: str):
    """Get a comprehensive summary of the parsed model."""
    if model_id not in _parsed_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found"
        )
    
    result = _parsed_models[model_id]
    
    # Calculate statistics
    elements_by_category = {}
    elements_by_level = {}
    elements_by_material = {}
    
    for element in result.elements:
        # By category
        cat = element.category.value
        elements_by_category[cat] = elements_by_category.get(cat, 0) + 1
        
        # By level
        if element.level:
            elements_by_level[element.level] = elements_by_level.get(element.level, 0) + 1
        
        # By material
        if element.material:
            elements_by_material[element.material] = elements_by_material.get(element.material, 0) + 1
    
    return {
        "model_id": model_id,
        "model_info": {
            "schema_version": result.model_info.schema_version,
            "project_name": result.model_info.project_name,
            "building_name": result.model_info.building_name,
            "organization": result.model_info.organization
        },
        "statistics": {
            "total_elements": result.total_elements,
            "element_types": len(result.element_counts),
            "levels_count": len(result.levels),
            "materials_count": len(result.materials)
        },
        "elements_by_type": result.element_counts,
        "elements_by_category": elements_by_category,
        "elements_by_level": elements_by_level,
        "elements_by_material": elements_by_material,
        "levels": result.levels,
        "materials": result.materials
    }


@router.get("/ifc/{model_id}/hierarchy")
async def get_model_hierarchy(model_id: str):
    """Get the spatial hierarchy of the model (Site > Building > Storey > Elements)."""
    if model_id not in _parsed_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found"
        )
    
    result = _parsed_models[model_id]
    
    # Build hierarchy
    hierarchy = {
        "project": result.model_info.project_name or "Unknown Project",
        "site": result.model_info.site_name or "Unknown Site",
        "building": result.model_info.building_name or "Unknown Building",
        "levels": {}
    }
    
    for level in result.levels:
        level_elements = [e for e in result.elements if e.level == level]
        hierarchy["levels"][level] = {
            "element_count": len(level_elements),
            "by_type": {}
        }
        for elem in level_elements:
            ifc_type = elem.ifc_type
            if ifc_type not in hierarchy["levels"][level]["by_type"]:
                hierarchy["levels"][level]["by_type"][ifc_type] = 0
            hierarchy["levels"][level]["by_type"][ifc_type] += 1
    
    # Add elements without level assignment
    unassigned = [e for e in result.elements if not e.level]
    if unassigned:
        hierarchy["levels"]["_unassigned"] = {
            "element_count": len(unassigned),
            "by_type": {}
        }
        for elem in unassigned:
            ifc_type = elem.ifc_type
            if ifc_type not in hierarchy["levels"]["_unassigned"]["by_type"]:
                hierarchy["levels"]["_unassigned"]["by_type"][ifc_type] = 0
            hierarchy["levels"]["_unassigned"]["by_type"][ifc_type] += 1
    
    return hierarchy


@router.delete("/ifc/{model_id}")
async def delete_parsed_model(model_id: str):
    """Remove a parsed model from cache."""
    if model_id not in _parsed_models:
        raise HTTPException(
            status_code=404,
            detail=f"Model {model_id} not found"
        )
    
    del _parsed_models[model_id]
    return {"status": "deleted", "model_id": model_id}


@router.get("/ifc/models")
async def list_parsed_models():
    """List all currently cached parsed models."""
    return {
        "models": [
            {
                "model_id": mid,
                "project_name": result.model_info.project_name,
                "total_elements": result.total_elements
            }
            for mid, result in _parsed_models.items()
        ],
        "count": len(_parsed_models)
    }
