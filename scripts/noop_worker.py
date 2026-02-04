"""Idle worker placeholder for Render debug deployments."""

from __future__ import annotations

import logging
import os
import signal
import time


logger = logging.getLogger("noop-worker")

_running = True


def _handle_shutdown(signum: int, _frame) -> None:
    global _running
    logger.info("Received signal %s, shutting down.", signum)
    _running = False


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    worker_name = os.getenv("WORKER_NAME", "worker")
    logger.info("Starting noop worker for %s. No background jobs are configured.", worker_name)

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    while _running:
        logger.debug("noop worker %s heartbeat", worker_name)
        time.sleep(30)


if __name__ == "__main__":
    main()
