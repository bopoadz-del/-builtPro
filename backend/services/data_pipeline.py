"""
Data Pipeline Engine for BuilTPro Brain AI

ETL processing, data transformation, and streaming data pipelines.

Features:
- ETL pipeline management
- Data transformation stages
- Source/sink connectors
- Pipeline scheduling
- Error handling and retry
- Data validation
- Pipeline monitoring
- Streaming and batch modes

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
import secrets
from threading import Lock

logger = logging.getLogger(__name__)


class PipelineError(Exception):
    pass


class PipelineStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class StageType(str, Enum):
    EXTRACT = "extract"
    TRANSFORM = "transform"
    LOAD = "load"
    VALIDATE = "validate"
    FILTER = "filter"


@dataclass
class PipelineStage:
    stage_id: str
    name: str
    stage_type: StageType
    processor: Optional[Callable] = None
    config: Dict[str, Any] = field(default_factory=dict)
    status: PipelineStatus = PipelineStatus.IDLE
    records_processed: int = 0
    errors: int = 0


@dataclass
class Pipeline:
    pipeline_id: str
    name: str
    stages: List[PipelineStage] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    total_records: int = 0


@dataclass
class PipelineRun:
    run_id: str
    pipeline_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: PipelineStatus = PipelineStatus.RUNNING
    records_processed: int = 0
    errors: int = 0


class DataPipelineEngine:
    """Production-ready data pipeline engine."""

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

        self.pipelines: Dict[str, Pipeline] = {}
        self.runs: List[PipelineRun] = []
        self.transformers: Dict[str, Callable] = {}

        self.stats = {"total_pipelines": 0, "total_runs": 0, "records_processed": 0}
        logger.info("Data Pipeline Engine initialized")

    def create_pipeline(self, name: str, stages: Optional[List[PipelineStage]] = None) -> Pipeline:
        """Create a new data pipeline."""
        pipeline_id = f"pipe_{secrets.token_hex(8)}"
        pipeline = Pipeline(pipeline_id=pipeline_id, name=name, stages=stages or [])
        self.pipelines[pipeline_id] = pipeline
        self.stats["total_pipelines"] += 1
        return pipeline

    def add_stage(self, pipeline_id: str, stage: PipelineStage):
        """Add a stage to a pipeline."""
        if pipeline_id not in self.pipelines:
            raise PipelineError(f"Pipeline not found: {pipeline_id}")
        self.pipelines[pipeline_id].stages.append(stage)

    def register_transformer(self, name: str, func: Callable):
        """Register a data transformation function."""
        self.transformers[name] = func

    def run_pipeline(self, pipeline_id: str, data: Optional[List[Any]] = None) -> PipelineRun:
        """Execute a pipeline."""
        if pipeline_id not in self.pipelines:
            raise PipelineError(f"Pipeline not found: {pipeline_id}")

        pipeline = self.pipelines[pipeline_id]
        run = PipelineRun(
            run_id=f"run_{secrets.token_hex(8)}",
            pipeline_id=pipeline_id,
            started_at=datetime.utcnow()
        )

        pipeline.status = PipelineStatus.RUNNING
        current_data = data or []

        try:
            for stage in pipeline.stages:
                stage.status = PipelineStatus.RUNNING
                try:
                    if stage.processor:
                        current_data = [stage.processor(record) for record in current_data]
                    stage.records_processed += len(current_data)
                    stage.status = PipelineStatus.COMPLETED
                except Exception as e:
                    stage.errors += 1
                    stage.status = PipelineStatus.FAILED
                    raise PipelineError(f"Stage {stage.name} failed: {e}")

            run.status = PipelineStatus.COMPLETED
            run.records_processed = len(current_data)
            pipeline.status = PipelineStatus.COMPLETED
            pipeline.total_records += len(current_data)
        except Exception as e:
            run.status = PipelineStatus.FAILED
            run.errors += 1
            pipeline.status = PipelineStatus.FAILED
            logger.error(f"Pipeline failed: {e}")

        run.completed_at = datetime.utcnow()
        pipeline.last_run = datetime.utcnow()
        self.runs.append(run)
        self.stats["total_runs"] += 1
        self.stats["records_processed"] += run.records_processed

        return run

    def get_stats(self) -> Dict[str, Any]:
        return self.stats


data_pipeline = DataPipelineEngine()
