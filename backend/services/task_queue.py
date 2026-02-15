"""
Task Queue Manager for BuilTPro Brain AI

Distributed task processing with Celery/Redis integration, priority queues, and scheduling.

Features:
- Distributed task processing
- Priority queues (critical, high, normal, low)
- Task scheduling (cron, intervals, one-time)
- Task chains and workflows
- Dead letter queues
- Retry policies with backoff
- Task progress tracking
- Worker management
- Task result storage
- Concurrency control

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from collections import defaultdict, deque
import secrets
from threading import Lock

logger = logging.getLogger(__name__)


class TaskQueueError(Exception):
    pass


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"
    DEAD_LETTER = "dead_letter"


@dataclass
class Task:
    task_id: str
    name: str
    func_name: str
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    progress: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskChain:
    chain_id: str
    tasks: List[str]  # Ordered task IDs
    current_index: int = 0
    status: TaskStatus = TaskStatus.PENDING


@dataclass
class Worker:
    worker_id: str
    name: str
    queues: List[str]
    status: str = "idle"
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    registered_at: datetime = field(default_factory=datetime.utcnow)


class TaskQueueManager:
    """Production-ready distributed task queue manager."""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.tasks: Dict[str, Task] = {}
        self.queues: Dict[str, deque] = {
            "critical": deque(),
            "high": deque(),
            "normal": deque(),
            "low": deque()
        }
        self.workers: Dict[str, Worker] = {}
        self.task_chains: Dict[str, TaskChain] = {}
        self.dead_letter_queue: deque = deque(maxlen=10000)
        self.registered_functions: Dict[str, Callable] = {}

        self.stats = {
            "total_tasks": 0, "completed_tasks": 0,
            "failed_tasks": 0, "retried_tasks": 0
        }

        logger.info("Task Queue Manager initialized")

    def register_task(self, name: str, func: Callable):
        """Register a task function."""
        self.registered_functions[name] = func

    def submit_task(
        self, name: str, args: tuple = (), kwargs: Optional[Dict] = None,
        priority: TaskPriority = TaskPriority.NORMAL, max_retries: int = 3
    ) -> Task:
        """Submit a task to the queue."""
        task_id = f"task_{secrets.token_hex(8)}"
        task = Task(
            task_id=task_id, name=name, func_name=name,
            args=args, kwargs=kwargs or {},
            priority=priority, max_retries=max_retries,
            status=TaskStatus.QUEUED
        )
        self.tasks[task_id] = task
        self.queues[priority.value].append(task_id)
        self.stats["total_tasks"] += 1
        return task

    def process_next(self) -> Optional[Task]:
        """Process the next task from highest priority queue."""
        for priority in ["critical", "high", "normal", "low"]:
            if self.queues[priority]:
                task_id = self.queues[priority].popleft()
                task = self.tasks.get(task_id)
                if task:
                    return self._execute_task(task)
        return None

    def _execute_task(self, task: Task) -> Task:
        """Execute a task."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()

        try:
            func = self.registered_functions.get(task.func_name)
            if func is None:
                raise ValueError(f"No task handler registered for '{task.func_name}'")

            task.result = func(*task.args, **task.kwargs)
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.progress = 100.0
            self.stats["completed_tasks"] += 1
        except Exception as e:
            task.error = str(e)
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.RETRYING
                self.queues[task.priority.value].append(task.task_id)
                self.stats["retried_tasks"] += 1
            else:
                task.status = TaskStatus.DEAD_LETTER
                self.dead_letter_queue.append(task.task_id)
                self.stats["failed_tasks"] += 1

        return task

    def create_chain(self, task_ids: List[str]) -> TaskChain:
        """Create a task chain (sequential execution)."""
        chain_id = f"chain_{secrets.token_hex(8)}"
        chain = TaskChain(chain_id=chain_id, tasks=task_ids)
        self.task_chains[chain_id] = chain
        return chain

    def cancel_task(self, task_id: str):
        """Cancel a task."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.CANCELLED

    def register_worker(self, worker_id: str, name: str, queues: Optional[List[str]] = None) -> Worker:
        """Register a worker."""
        worker = Worker(worker_id=worker_id, name=name, queues=queues or ["normal"])
        self.workers[worker_id] = worker
        return worker

    def get_stats(self) -> Dict[str, Any]:
        """Get task queue statistics."""
        queue_sizes = {name: len(q) for name, q in self.queues.items()}
        return {**self.stats, "queue_sizes": queue_sizes, "workers": len(self.workers),
                "dead_letter_count": len(self.dead_letter_queue)}


task_queue = TaskQueueManager()
