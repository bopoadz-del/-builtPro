"""Hydration worker entrypoint."""

from __future__ import annotations

import logging
import os
import signal
import time

from backend.backend.db import SessionLocal, init_db
from backend.hydration.models import WorkspaceSource
from backend.hydration.pipeline import HydrationOptions, HydrationPipeline


logger = logging.getLogger("hydration-worker")
_running = True


def _handle_shutdown(signum: int, _frame) -> None:
    global _running
    logger.info("Received signal %s, shutting down.", signum)
    _running = False


def _run_once() -> None:
    init_db()
    session = SessionLocal()
    try:
        workspace_ids = [
            row[0] for row in session.query(WorkspaceSource.workspace_id).distinct().all()
        ]
        if not workspace_ids:
            logger.info("No hydration sources configured. Waiting for work.")
            return

        pipeline = HydrationPipeline(session)
        options = HydrationOptions()
        for workspace_id in workspace_ids:
            if not _running:
                break
            pipeline.hydrate_workspace(str(workspace_id), options)
    finally:
        session.close()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    poll_seconds = int(os.getenv("HYDRATION_POLL_SECONDS", "60"))
    run_once = os.getenv("WORKER_RUN_ONCE", "false").lower() == "true"

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    logger.info("Starting hydration worker.")
    while _running:
        _run_once()
        if run_once:
            break
        time.sleep(poll_seconds)

    logger.info("Hydration worker stopped.")


if __name__ == "__main__":
    main()
