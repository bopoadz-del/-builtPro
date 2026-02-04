"""Queue worker entrypoint."""

from __future__ import annotations

import logging
import os
import signal
import time


logger = logging.getLogger("queue-worker")
_running = True


def _handle_shutdown(signum: int, _frame) -> None:
    global _running
    logger.info("Received signal %s, shutting down.", signum)
    _running = False


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    poll_seconds = int(os.getenv("QUEUE_POLL_SECONDS", "5"))
    run_once = os.getenv("WORKER_RUN_ONCE", "false").lower() == "true"

    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    logger.info("Starting queue worker.")
    while _running:
        logger.debug("Queue worker heartbeat; no queue backend configured.")
        if run_once:
            break
        time.sleep(poll_seconds)

    logger.info("Queue worker stopped.")


if __name__ == "__main__":
    main()
