"""
Services for handling archive files (ZIP, TAR, GZ, etc.).

This module provides utilities to inspect and list the contents of
archive files without fully extracting them. It supports common
formats such as ZIP and TAR.*. For other formats like RAR and 7Z,
the implementation returns an informative error. In future
iterations, this service can be extended to support extraction into
sandboxed directories, virus scanning, and type detection.
"""

from pathlib import Path
from typing import Any, Dict, List
import zipfile
import tarfile


def list_archive_contents(file_path: Path) -> Dict[str, Any]:
    """
    Inspect an archive and return a summary of its contents.

    Args:
        file_path: Path to the uploaded archive file.

    Returns:
        A dictionary containing the archive type, file count and a list
        of entries (path strings). If the format is unsupported, the
        result includes an `error` field instead of entries.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Archive file {file_path} does not exist")

    suffix = file_path.suffix.lower().lstrip('.')
    # Determine archive type and list contents
    try:
        if suffix == 'zip':
            with zipfile.ZipFile(file_path, 'r') as zf:
                entries = zf.namelist()
                return {
                    "archive_type": "zip",
                    "file_count": len(entries),
                    "entries": entries,
                }
        elif suffix in {'tar', 'gz', 'tgz', 'bz2', 'xz'}:
            # tarfile can open .tar, .tar.gz, .tgz, .tar.bz2, etc.
            with tarfile.open(file_path, 'r:*') as tf:
                entries = [member.name for member in tf.getmembers()]
                return {
                    "archive_type": "tar",
                    "file_count": len(entries),
                    "entries": entries,
                }
        else:
            # Unsupported format (e.g., rar, 7z)
            return {
                "archive_type": suffix,
                "file_count": 0,
                "error": f"Unsupported archive format: {suffix}",
            }
    except (zipfile.BadZipFile, tarfile.TarError) as exc:
        return {
            "archive_type": suffix,
            "file_count": 0,
            "error": f"Failed to read archive: {exc}",
        }