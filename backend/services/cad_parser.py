"""
CAD file analysis service.

This module provides a function to analyze Computer‑Aided Design (CAD) files.
It currently supports basic detection of common CAD formats based solely on
file extensions and returns simple metadata about the uploaded file. In a
production system this module would integrate with specialised libraries
or services (e.g. OpenCascade, IFC parsing, Autodesk Forge) to extract
detailed geometry, metadata and perform tasks such as clash detection,
quantity take‑offs and 3D preview generation.

Supported extensions include:

* `.dwg` – AutoCAD drawing files
* `.dxf` – AutoCAD exchange files
* `.dwf` – Design Web Format
* `.dgn` – Bentley MicroStation design
* `.rvt` – Autodesk Revit
* `.ifc` – Industry Foundation Classes (BIM)
* `.step`, `.stp` – ISO 10303 STEP files
* `.iges`, `.igs` – Initial Graphics Exchange Specification
* `.stl` – Stereolithography
* `.3dm` – Rhino 3D model

Other extensions will still return basic metadata but are not
recognised as CAD formats.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


SUPPORTED_CAD_EXTENSIONS = {
    ".dwg",
    ".dxf",
    ".dwf",
    ".dgn",
    ".rvt",
    ".ifc",
    ".step",
    ".stp",
    ".iges",
    ".igs",
    ".stl",
    ".3dm",
}


def parse_cad_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a CAD file and return simple metadata.

    Currently this function performs only basic analysis: it determines
    the file extension, checks if it is a known CAD format and reports
    the file name, extension and size. A placeholder message indicates
    that advanced CAD analysis is not yet implemented.

    Args:
        file_path: Path to the uploaded file on disk.

    Returns:
        A dictionary containing metadata about the file. Keys include:
        - ``file_name``: The base name of the file.
        - ``file_ext``: The lowercase file extension.
        - ``file_size``: Size in bytes.
        - ``cad_format``: Boolean indicating if the extension is recognised
          as a CAD format.
        - ``message``: Human‑readable description of the result.

    Raises:
        FileNotFoundError: If the provided file_path does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    file_name = file_path.name
    ext = file_path.suffix.lower()
    file_size = file_path.stat().st_size

    is_cad = ext in SUPPORTED_CAD_EXTENSIONS

    if is_cad:
        message = (
            "CAD file detected but detailed analysis is not yet implemented. "
            "The file has been stored successfully."
        )
    else:
        message = (
            "The uploaded file is not a recognised CAD format. Only basic metadata "
            "is returned."
        )

    return {
        "file_name": file_name,
        "file_ext": ext,
        "file_size": file_size,
        "cad_format": is_cad,
        "message": message,
    }