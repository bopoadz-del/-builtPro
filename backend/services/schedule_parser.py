"""
Service functions to parse project schedule files (XER, XML, MPP).

Currently provides a simple placeholder parser that reads the text
content of the uploaded file and returns basic metadata such as
number of lines and file size.  This lays the groundwork for more
sophisticated schedule analysis such as critical path calculation,
resource loading and schedule health metrics in future iterations.
"""

from pathlib import Path
from typing import Any, Dict

# Import compute_critical_path relative to this package to avoid import issues when
# `app` is not in the top-level package path.
from .schedule_metrics import compute_critical_path


def parse_schedule_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a schedule file (XER, XML, MPP) and return extracted tasks.

    The parser attempts to detect the file format based on the extension.
    For Primavera P6 XER files, it reads the file as a tab‑separated
    values (TSV) document and extracts task rows. For Microsoft Project
    XML files (.xml or .mpp exported as XML), it parses the XML tree and
    extracts task information and predecessor links. For unsupported
    formats, it falls back to returning basic metadata.

    Args:
        file_path: Path to the uploaded schedule file.

    Returns:
        A dictionary with filename, file size, and either a `tasks`
        array with parsed tasks or a placeholder analysis for
        unsupported formats.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"{file_path} does not exist")

    suffix = file_path.suffix.lower().lstrip('.')
    result: Dict[str, Any] = {
        "filename": file_path.name,
        "file_size": file_path.stat().st_size,
    }

    if suffix == 'xer':
        tasks = _parse_xer(file_path)
        metrics = compute_critical_path(tasks) if tasks else None
        result.update({
            "format": "XER",
            "tasks": tasks,
            "task_count": len(tasks),
            "analysis": metrics,
        })
    elif suffix in {'xml', 'mpp'}:
        tasks = _parse_mpp_xml(file_path)
        metrics = compute_critical_path(tasks) if tasks else None
        result.update({
            "format": "XML",
            "tasks": tasks,
            "task_count": len(tasks),
            "analysis": metrics,
        })
    else:
        # Fallback: basic metadata only
        try:
            content = file_path.read_text(errors="ignore")
            lines = content.splitlines()
            line_count = len(lines)
        except Exception:
            line_count = 0
        result.update({
            "format": suffix or "unknown",
            "analysis": {
                "summary": "Unsupported schedule format",
                "line_count": line_count,
                "details": "Only XER and MPP/XML formats are supported in this version.",
            }
        })
    return result


def _parse_xer(file_path: Path) -> list[Dict[str, Any]]:
    """Parse a Primavera P6 XER file and extract tasks.

    The XER format is a tab‑delimited export where tables are stored
    sequentially. This simplified parser scans all lines and treats any
    row with at least five tab‑separated columns as a task record. The
    first five columns are mapped to fields: ID, WBS code, Name,
    Start Date, Finish Date. In practice, XER files have many tables
    (e.g., TASK, PROJECT, etc.) with varying schemas; a full parser
    should split by table sections and map columns by header rows. This
    implementation provides a best‑effort extraction for demonstration.

    Args:
        file_path: Path to the XER file.

    Returns:
        A list of task dictionaries with keys: id, wbs, name, start,
        finish.
    """
    tasks: list[Dict[str, Any]] = []
    try:
        with file_path.open('r', errors='ignore') as f:
            for line in f:
                # Skip empty lines and comment markers
                if not line.strip() or line.startswith('%'):
                    continue
                cols = line.rstrip('\n').split('\t')
                if len(cols) >= 5:
                    task = {
                        "id": cols[0].strip(),
                        "wbs": cols[1].strip(),
                        "name": cols[2].strip(),
                        "start": cols[3].strip(),
                        "finish": cols[4].strip(),
                    }
                    tasks.append(task)
    except Exception:
        # Fail silently and return empty list if parsing fails
        pass
    return tasks


def _parse_mpp_xml(file_path: Path) -> list[Dict[str, Any]]:
    """Parse an MS Project XML file (.xml or .mpp exported as XML).

    Uses Python's built‑in XML parser to find Task elements and
    extract key fields. Each task includes an ID (UID), name, start and
    finish dates, and a list of predecessor IDs (dependencies). If
    parsing fails or the structure is unexpected, returns an empty list.

    Args:
        file_path: Path to the XML file.

    Returns:
        A list of task dictionaries with keys: id, name, start,
        finish, dependencies (list[str]).
    """
    tasks: list[Dict[str, Any]] = []
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        # Find all Task elements (MS Project namespace may be absent)
        for task_elem in root.iterfind('.//Task'):
            try:
                uid_elem = task_elem.find('UID')
                name_elem = task_elem.find('Name')
                start_elem = task_elem.find('Start')
                finish_elem = task_elem.find('Finish')
                uid = uid_elem.text.strip() if uid_elem is not None and uid_elem.text else ''
                name = name_elem.text.strip() if name_elem is not None and name_elem.text else ''
                start = start_elem.text.strip() if start_elem is not None and start_elem.text else ''
                finish = finish_elem.text.strip() if finish_elem is not None and finish_elem.text else ''
                # Dependencies: PredecessorLink elements with PredecessorUID
                dependencies: list[str] = []
                for pred_link in task_elem.findall('PredecessorLink'):
                    pred_uid_elem = pred_link.find('PredecessorUID')
                    if pred_uid_elem is not None and pred_uid_elem.text:
                        dependencies.append(pred_uid_elem.text.strip())
                # Skip summary tasks (no name) if desired
                tasks.append({
                    "id": uid,
                    "name": name,
                    "start": start,
                    "finish": finish,
                    "dependencies": dependencies,
                })
            except Exception:
                continue
    except Exception:
        # Parsing error
        pass
    return tasks
