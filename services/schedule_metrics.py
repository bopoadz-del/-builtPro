"""
Schedule metrics and critical path calculation utilities.

This module provides functions to compute the critical path and
schedule slack for a set of tasks represented as dictionaries with
start and finish dates and predecessor relationships. It implements a
simple Critical Path Method (CPM) using a directed acyclic graph and
dynamic programming. Dates are parsed using Python's ``datetime``
library; durations are computed in days.

Task schema:

```
{
    "id": "1",
    "name": "Task Name",
    "start": "2026-01-01",
    "finish": "2026-01-05",
    "dependencies": ["0", ...]  # optional list of predecessor IDs
}
```

The algorithm assumes tasks without predecessors start at day zero. It
computes earliest and latest start/finish times, slack, and returns
the list of critical tasks (slack == 0).
"""

from datetime import datetime
from typing import Dict, List, Tuple, Any


def _parse_date(date_str: str) -> datetime:
    """Parse ISO8601 or date string to ``datetime``; raise if invalid.

    The enterprise demo schedules may use simple date formats (YYYY-MM-DD)
    or full ISO timestamps. This helper tries multiple patterns. If none
    match, it raises ``ValueError`` to signal an unsupported format.

    Args:
        date_str: Input date string.

    Returns:
        A ``datetime`` instance representing the parsed date.
    """
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    raise ValueError(f"Unsupported date format: {date_str}")


def compute_critical_path(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute critical path and slack for a list of tasks.

    Given a set of tasks with start and finish dates and optional
    predecessor relationships, this function applies a simple Critical
    Path Method (CPM) algorithm to derive timing metrics per task. It
    computes earliest and latest start/finish times, slack and the
    overall project duration. The tasks are assumed to form a Directed
    Acyclic Graph (DAG); circular dependencies will lead to undefined
    behaviour.

    Args:
        tasks: List of task dictionaries. Each task must contain at
            least ``id``, ``start`` and ``finish`` keys. A
            ``dependencies`` key may specify predecessor IDs.

    Returns:
        A dictionary with per-task timing details, the list of IDs on
        the critical path and the total project duration (in days).
    """
    # Build quick lookup from ID to task dict
    task_map: Dict[str, Dict[str, Any]] = {t["id"]: t for t in tasks}
    # Ensure each task has a dependencies list
    for t in tasks:
        t.setdefault("dependencies", [])

    # Compute durations (in days). If parsing fails or dates are equal
    # or invalid, fall back to a duration of 1 day to ensure progress.
    durations: Dict[str, float] = {}
    for t in tasks:
        try:
            start = _parse_date(t.get("start", ""))
            finish = _parse_date(t.get("finish", ""))
            duration = (finish - start).days or 0
            if duration <= 0:
                duration = 1
        except Exception:
            duration = 1
        durations[t["id"]] = duration

    # Build predecessors and successors adjacency lists
    successors: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
    predecessors: Dict[str, List[str]] = {t["id"]: [] for t in tasks}
    for t in tasks:
        for pred in t.get("dependencies", []):
            if pred in task_map:
                predecessors[t["id"]].append(pred)
                successors[pred].append(t["id"])

    # Perform topological sort (Kahn's algorithm) to determine order
    from collections import deque
    queue = deque([tid for tid, preds in predecessors.items() if not preds])
    topo_order: List[str] = []
    while queue:
        tid = queue.popleft()
        topo_order.append(tid)
        for succ in successors[tid]:
            predecessors[succ].remove(tid)
            if not predecessors[succ]:
                queue.append(succ)

    # Calculate earliest start/finish times
    earliest_start: Dict[str, float] = {}
    earliest_finish: Dict[str, float] = {}
    for tid in topo_order:
        deps = task_map[tid].get("dependencies", [])
        if not deps:
            earliest_start[tid] = 0.0
        else:
            earliest_start[tid] = max(earliest_finish[p] for p in deps if p in earliest_finish)
        earliest_finish[tid] = earliest_start[tid] + durations[tid]

    # Determine the total project duration
    project_duration = max(earliest_finish.values()) if earliest_finish else 0.0

    # Calculate latest finish/start times
    latest_finish: Dict[str, float] = {}
    latest_start: Dict[str, float] = {}
    # End tasks have no successors
    end_tasks = [tid for tid, succs in successors.items() if not succs]
    for tid in end_tasks:
        latest_finish[tid] = project_duration
        latest_start[tid] = project_duration - durations[tid]
    # Traverse tasks in reverse topological order
    for tid in reversed(topo_order):
        if tid not in latest_finish:
            succs = successors[tid]
            latest_finish[tid] = min(latest_start[s] for s in succs)
            latest_start[tid] = latest_finish[tid] - durations[tid]

    # Compute slack (float) and identify critical tasks (slack == 0)
    slack: Dict[str, float] = {}
    critical_tasks: List[str] = []
    for tid in topo_order:
        es = earliest_start[tid]
        ls = latest_start[tid]
        slack_val = ls - es
        slack[tid] = slack_val
        if abs(slack_val) < 1e-6:
            critical_tasks.append(tid)

    # Construct per-task metrics result
    per_task = {}
    for tid in topo_order:
        per_task[tid] = {
            "duration": durations[tid],
            "earliest_start": earliest_start[tid],
            "earliest_finish": earliest_finish[tid],
            "latest_start": latest_start[tid],
            "latest_finish": latest_finish[tid],
            "slack": slack[tid],
        }

    return {
        "tasks": per_task,
        "critical_path": critical_tasks,
        "project_duration": project_duration,
    }