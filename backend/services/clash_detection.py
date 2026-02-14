# BIM Clash Detection Service - ITEM 140
# Automatic detection of clashes and conflicts in BIM models

from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import math

from ..core.logging_config import get_logger

logger = get_logger(__name__)


class ClashType(str, Enum):
    """Types of clashes in BIM models."""
    HARD_CLASH = "hard_clash"  # Physical overlap
    SOFT_CLASH = "soft_clash"  # Clearance violation
    WORKFLOW_CLASH = "workflow_clash"  # Sequencing issue
    TIME_CLASH = "time_clash"  # 4D schedule conflict


class ClashSeverity(str, Enum):
    """Severity levels for clashes."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ClashStatus(str, Enum):
    """Status of clash resolution."""
    NEW = "new"
    ACTIVE = "active"
    APPROVED = "approved"
    RESOLVED = "resolved"
    CLOSED = "closed"


@dataclass
class BoundingBox:
    """3D bounding box."""
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    @property
    def center(self) -> Tuple[float, float, float]:
        """Get center point."""
        return (
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2
        )

    @property
    def dimensions(self) -> Tuple[float, float, float]:
        """Get dimensions."""
        return (
            self.max_x - self.min_x,
            self.max_y - self.min_y,
            self.max_z - self.min_z
        )

    def intersects(self, other: 'BoundingBox') -> bool:
        """Check if this box intersects with another."""
        return not (
            self.max_x < other.min_x or self.min_x > other.max_x or
            self.max_y < other.min_y or self.min_y > other.max_y or
            self.max_z < other.min_z or self.min_z > other.max_z
        )

    def clearance_distance(self, other: 'BoundingBox') -> float:
        """Calculate minimum clearance distance to another box."""
        if self.intersects(other):
            return 0.0

        dx = max(0, max(other.min_x - self.max_x, self.min_x - other.max_x))
        dy = max(0, max(other.min_y - self.max_y, self.min_y - other.max_y))
        dz = max(0, max(other.min_z - self.max_z, self.min_z - other.max_z))

        return math.sqrt(dx * dx + dy * dy + dz * dz)


@dataclass
class BIMElement:
    """Simplified BIM element for clash detection."""
    id: str
    name: str
    ifc_type: str
    discipline: str  # Structural, Architectural, MEP
    bounding_box: BoundingBox
    level: Optional[str] = None
    system: Optional[str] = None


@dataclass
class Clash:
    """Detected clash between BIM elements."""
    id: str
    type: ClashType
    severity: ClashSeverity
    element_a: BIMElement
    element_b: BIMElement
    clash_point: Tuple[float, float, float]
    clearance_distance: float
    detected_date: datetime = field(default_factory=datetime.utcnow)
    status: ClashStatus = ClashStatus.NEW
    assigned_to: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    resolution: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'severity': self.severity.value,
            'element_a': {
                'id': self.element_a.id,
                'name': self.element_a.name,
                'type': self.element_a.ifc_type,
                'discipline': self.element_a.discipline
            },
            'element_b': {
                'id': self.element_b.id,
                'name': self.element_b.name,
                'type': self.element_b.ifc_type,
                'discipline': self.element_b.discipline
            },
            'clash_point': self.clash_point,
            'clearance_distance': self.clearance_distance,
            'detected_date': self.detected_date.isoformat(),
            'status': self.status.value,
            'assigned_to': self.assigned_to,
            'notes': self.notes,
            'resolution': self.resolution
        }


@dataclass
class ClashDetectionReport:
    """Clash detection analysis report."""
    total_clashes: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    by_discipline: Dict[str, int]
    clashes: List[Clash]
    run_date: datetime = field(default_factory=datetime.utcnow)
    model_version: Optional[str] = None


class ClashDetectionService:
    """
    BIM clash detection service.

    Features:
    - Hard clash detection (physical overlaps)
    - Soft clash detection (clearance violations)
    - Discipline-specific rules
    - Severity assessment
    - Clash grouping and management
    - Resolution tracking
    """

    def __init__(
        self,
        hard_clash_tolerance: float = 0.001,  # meters
        soft_clash_clearance: Dict[str, float] = None
    ):
        """
        Initialize clash detection service.

        Args:
            hard_clash_tolerance: Tolerance for hard clashes (meters)
            soft_clash_clearance: Required clearances by element type
        """
        self.logger = get_logger(self.__class__.__name__)
        self.hard_clash_tolerance = hard_clash_tolerance
        self.soft_clash_clearance = soft_clash_clearance or {
            'default': 0.05,  # 50mm default clearance
            'duct': 0.15,     # 150mm for ducts
            'pipe': 0.10,     # 100mm for pipes
            'cable_tray': 0.10,  # 100mm for cable trays
        }

        self.clash_counter = 0

    def detect_clashes(
        self,
        elements: List[BIMElement],
        rules: Optional[Dict[str, Any]] = None
    ) -> ClashDetectionReport:
        """
        Detect clashes in BIM model.

        Args:
            elements: List of BIM elements to check
            rules: Optional custom detection rules

        Returns:
            Clash detection report
        """
        self.logger.info(f"Starting clash detection for {len(elements)} elements")

        clashes = []

        # Check all pairs of elements
        for i in range(len(elements)):
            for j in range(i + 1, len(elements)):
                element_a = elements[i]
                element_b = elements[j]

                # Skip if same discipline (optional rule)
                if element_a.discipline == element_b.discipline:
                    continue

                # Check for clashes
                detected_clashes = self._check_element_pair(element_a, element_b)
                clashes.extend(detected_clashes)

        # Generate report
        report = self._generate_report(clashes)

        self.logger.info(
            f"Clash detection complete: {report.total_clashes} clashes found"
        )

        return report

    def _check_element_pair(
        self,
        element_a: BIMElement,
        element_b: BIMElement
    ) -> List[Clash]:
        """Check a pair of elements for clashes."""
        clashes = []

        # Check bounding box intersection
        if element_a.bounding_box.intersects(element_b.bounding_box):
            # Hard clash detected
            clash = self._create_clash(
                ClashType.HARD_CLASH,
                element_a,
                element_b,
                0.0
            )
            clashes.append(clash)

        else:
            # Check clearance for soft clash
            clearance = element_a.bounding_box.clearance_distance(
                element_b.bounding_box
            )

            required_clearance = self._get_required_clearance(element_a, element_b)

            if clearance < required_clearance:
                # Soft clash detected
                clash = self._create_clash(
                    ClashType.SOFT_CLASH,
                    element_a,
                    element_b,
                    clearance
                )
                clashes.append(clash)

        return clashes

    def _create_clash(
        self,
        clash_type: ClashType,
        element_a: BIMElement,
        element_b: BIMElement,
        clearance: float
    ) -> Clash:
        """Create a clash object."""
        self.clash_counter += 1

        # Calculate clash point (midpoint between element centers)
        center_a = element_a.bounding_box.center
        center_b = element_b.bounding_box.center

        clash_point = (
            (center_a[0] + center_b[0]) / 2,
            (center_a[1] + center_b[1]) / 2,
            (center_a[2] + center_b[2]) / 2
        )

        # Determine severity
        severity = self._assess_severity(clash_type, element_a, element_b, clearance)

        return Clash(
            id=f"CLASH-{self.clash_counter:05d}",
            type=clash_type,
            severity=severity,
            element_a=element_a,
            element_b=element_b,
            clash_point=clash_point,
            clearance_distance=clearance
        )

    def _get_required_clearance(
        self,
        element_a: BIMElement,
        element_b: BIMElement
    ) -> float:
        """Get required clearance between elements."""
        # Check element types for specific clearances
        for element in [element_a, element_b]:
            ifc_type_lower = element.ifc_type.lower()

            if 'duct' in ifc_type_lower:
                return self.soft_clash_clearance['duct']
            elif 'pipe' in ifc_type_lower:
                return self.soft_clash_clearance['pipe']
            elif 'cable' in ifc_type_lower or 'tray' in ifc_type_lower:
                return self.soft_clash_clearance['cable_tray']

        return self.soft_clash_clearance['default']

    def _assess_severity(
        self,
        clash_type: ClashType,
        element_a: BIMElement,
        element_b: BIMElement,
        clearance: float
    ) -> ClashSeverity:
        """Assess clash severity."""
        # Hard clashes are always at least High severity
        if clash_type == ClashType.HARD_CLASH:
            # Critical if involving structural elements
            if 'structural' in element_a.discipline.lower() or \
               'structural' in element_b.discipline.lower():
                return ClashSeverity.CRITICAL

            return ClashSeverity.HIGH

        # Soft clash severity based on clearance violation
        required_clearance = self._get_required_clearance(element_a, element_b)
        violation_ratio = (required_clearance - clearance) / required_clearance

        if violation_ratio > 0.75:
            return ClashSeverity.HIGH
        elif violation_ratio > 0.5:
            return ClashSeverity.MEDIUM
        else:
            return ClashSeverity.LOW

    def _generate_report(self, clashes: List[Clash]) -> ClashDetectionReport:
        """Generate clash detection report."""
        by_type = {}
        by_severity = {}
        by_discipline = {}

        for clash in clashes:
            # Count by type
            type_key = clash.type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1

            # Count by severity
            severity_key = clash.severity.value
            by_severity[severity_key] = by_severity.get(severity_key, 0) + 1

            # Count by discipline pair
            discipline_pair = f"{clash.element_a.discipline} vs {clash.element_b.discipline}"
            by_discipline[discipline_pair] = by_discipline.get(discipline_pair, 0) + 1

        return ClashDetectionReport(
            total_clashes=len(clashes),
            by_type=by_type,
            by_severity=by_severity,
            by_discipline=by_discipline,
            clashes=clashes
        )

    def update_clash_status(
        self,
        clash: Clash,
        new_status: ClashStatus,
        assigned_to: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Clash:
        """
        Update clash status.

        Args:
            clash: Clash to update
            new_status: New status
            assigned_to: Optional assignee
            notes: Optional notes

        Returns:
            Updated clash
        """
        clash.status = new_status

        if assigned_to:
            clash.assigned_to = assigned_to

        if notes:
            clash.notes.append(f"{datetime.utcnow().isoformat()}: {notes}")

        self.logger.info(f"Updated clash {clash.id} status to {new_status.value}")

        return clash

    def group_clashes(
        self,
        clashes: List[Clash],
        group_by: str = "discipline"
    ) -> Dict[str, List[Clash]]:
        """
        Group clashes by criteria.

        Args:
            clashes: List of clashes
            group_by: Grouping criteria (discipline, severity, type, level)

        Returns:
            Grouped clashes
        """
        groups = {}

        for clash in clashes:
            if group_by == "discipline":
                key = f"{clash.element_a.discipline} vs {clash.element_b.discipline}"
            elif group_by == "severity":
                key = clash.severity.value
            elif group_by == "type":
                key = clash.type.value
            elif group_by == "level":
                key = clash.element_a.level or "Unknown"
            else:
                key = "All"

            if key not in groups:
                groups[key] = []

            groups[key].append(clash)

        return groups


# Singleton instance
_clash_detection_service = None


def get_clash_detection_service() -> ClashDetectionService:
    """Get or create clash detection service singleton."""
    global _clash_detection_service
    if _clash_detection_service is None:
        _clash_detection_service = ClashDetectionService()
    return _clash_detection_service
