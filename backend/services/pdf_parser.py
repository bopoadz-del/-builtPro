"""
PDF file analysis service.

This module uses the ``fitz`` library (PyMuPDF) to inspect PDF documents.
It returns basic metadata such as the number of pages and can generate a
thumbnail of the first page encoded as a base64 PNG. Generating a
thumbnail provides a quick preview of drawings or text contained in
engineering PDFs without requiring the client to download the entire
document. In a more advanced implementation this service could
extract vector drawings, text layers or perform OCR.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Dict, Any

import fitz  # PyMuPDF


def parse_pdf_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a PDF file and return metadata and a thumbnail.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        A dictionary containing:
            - ``file_name``: Name of the PDF file.
            - ``file_size``: Size in bytes.
            - ``page_count``: Number of pages in the document.
            - ``thumbnail_b64``: Base64‑encoded PNG of the first page (if available).
            - ``message``: Human readable information.

    Raises:
        FileNotFoundError: If the file does not exist.
        RuntimeError: If the document cannot be opened as a PDF.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File does not exist: {file_path}")

    file_name = file_path.name
    file_size = file_path.stat().st_size

    try:
        doc = fitz.open(file_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to open PDF: {exc}")

    page_count = doc.page_count
    thumbnail_b64: str | None = None
    message = "PDF processed successfully."

    # Generate a thumbnail from the first page if the document has pages
    if page_count > 0:
        try:
            page = doc.load_page(0)
            # Use a zoom matrix for readability (1 = 72dpi). Adjust if higher resolution is needed.
            pix = page.get_pixmap(matrix=fitz.Matrix(1, 1))
            # Convert to PNG bytes and encode to base64
            png_bytes = pix.tobytes("png")
            thumbnail_b64 = base64.b64encode(png_bytes).decode("ascii")
        except Exception:
            # If thumbnail generation fails, continue without it
            message = "PDF processed but thumbnail generation failed."
            thumbnail_b64 = None
    doc.close()

    return {
        "file_name": file_name,
        "file_size": file_size,
        "page_count": page_count,
        "thumbnail_b64": thumbnail_b64,
        "message": message,
    }