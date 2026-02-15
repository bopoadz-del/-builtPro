from datetime import datetime, timedelta
import asyncio

import pytest

from backend.services.session_manager import (
    SessionManager,
    SessionError,
    SessionStatus,
)
from backend.services.notification_service import (
    NotificationService,
    NotificationChannel,
    NotificationCategory,
    NotificationPriority,
    NotificationStatus,
)
from backend.services.task_queue import TaskQueueManager, TaskStatus


@pytest.fixture(autouse=True)
def reset_singletons():
    SessionManager._instance = None
    NotificationService._instance = None
    TaskQueueManager._instance = None
    yield


def test_refresh_rejects_revoked_session():
    manager = SessionManager()
    session = manager.create_session("user-1")
    manager.revoke_session(session.session_id)

    with pytest.raises(SessionError):
        manager.refresh_session(session.refresh_token)

    assert manager.sessions[session.session_id].status == SessionStatus.REVOKED


def test_scheduled_notifications_are_delivered_when_due():
    service = NotificationService()
    service.create_template(
        template_id="tmpl-1",
        name="test",
        channel=NotificationChannel.IN_APP,
        category=NotificationCategory.INFO,
        subject_template="Hello {name}",
        body_template="Body {name}",
    )

    future = datetime.utcnow() + timedelta(seconds=1)
    notification = service.send_notification(
        notification_id="n-1",
        user_id="u-1",
        template_id="tmpl-1",
        variables={"name": "Ada"},
        priority=NotificationPriority.NORMAL,
        scheduled_at=future,
    )

    assert notification.status == NotificationStatus.QUEUED
    assert "n-1" in service.scheduled_notifications

    # Nothing should process before due time.
    processed_early = asyncio.run(service.process_queue())
    assert processed_early == 0

    service.scheduled_notifications["n-1"].scheduled_at = datetime.utcnow() - timedelta(seconds=1)
    processed = asyncio.run(service.process_queue())

    assert processed == 1
    assert service.notifications["n-1"].status == NotificationStatus.SENT
    assert "n-1" not in service.scheduled_notifications


def test_missing_task_handler_goes_to_dead_letter():
    queue = TaskQueueManager()
    task = queue.submit_task("unknown-handler", max_retries=0)

    executed = queue.process_next()

    assert executed is task
    assert executed.status == TaskStatus.DEAD_LETTER
    assert "No task handler registered" in (executed.error or "")
    assert queue.stats["failed_tasks"] == 1
    assert queue.stats["completed_tasks"] == 0
