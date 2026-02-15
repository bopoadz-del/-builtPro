"""
Notification Service for BuilTPro Brain AI

Multi-channel notification system with template management, user preferences,
delivery tracking, and batch processing.

Supported Channels:
- Email (SMTP)
- SMS (Twilio)
- Push notifications (Firebase)
- In-app notifications

Features:
- Template engine with variable substitution
- User notification preferences
- Delivery tracking and retry logic
- Batch processing for bulk notifications
- Priority queues
- Notification history

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict, deque
import re
import asyncio
from threading import Lock
import json

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class NotificationError(Exception):
    """Base exception for notification service errors."""
    pass


class TemplateError(NotificationError):
    """Raised when template processing fails."""
    pass


class DeliveryError(NotificationError):
    """Raised when notification delivery fails."""
    pass


class PreferenceError(NotificationError):
    """Raised when user preference operations fail."""
    pass


# ============================================================================
# Enums
# ============================================================================


class NotificationChannel(str, Enum):
    """Supported notification channels."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    REJECTED = "rejected"


class NotificationCategory(str, Enum):
    """Categories for notification grouping."""
    ALERT = "alert"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    SYSTEM = "system"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class NotificationTemplate:
    """Notification template definition."""
    template_id: str
    name: str
    channel: NotificationChannel
    category: NotificationCategory
    subject_template: str  # For email
    body_template: str
    variables: Set[str]  # Required variables
    default_values: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserPreferences:
    """User notification preferences."""
    user_id: str
    enabled_channels: Set[NotificationChannel]
    muted_categories: Set[NotificationCategory]
    email_address: Optional[str] = None
    phone_number: Optional[str] = None
    push_token: Optional[str] = None
    quiet_hours_start: Optional[int] = None  # Hour 0-23
    quiet_hours_end: Optional[int] = None  # Hour 0-23
    digest_mode: bool = False  # Batch notifications into daily digest
    language: str = "en"


@dataclass
class Notification:
    """A notification instance."""
    notification_id: str
    user_id: str
    channel: NotificationChannel
    category: NotificationCategory
    priority: NotificationPriority
    subject: str
    body: str
    status: NotificationStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class DeliveryReceipt:
    """Delivery tracking receipt."""
    notification_id: str
    channel: NotificationChannel
    status: NotificationStatus
    timestamp: datetime
    provider_response: Dict[str, Any] = field(default_factory=dict)
    error_details: Optional[str] = None


@dataclass
class BatchNotificationRequest:
    """Request for batch notification sending."""
    batch_id: str
    template_id: str
    recipients: List[str]  # User IDs
    variables: Dict[str, str]
    channel: NotificationChannel
    priority: NotificationPriority = NotificationPriority.NORMAL
    scheduled_at: Optional[datetime] = None


# ============================================================================
# Notification Service
# ============================================================================


class NotificationService:
    """
    Production-ready multi-channel notification service.

    Features:
    - Multi-channel delivery (email, SMS, push, in-app)
    - Template management with variable substitution
    - User preference management
    - Delivery tracking and retry logic
    - Batch processing
    - Priority queues
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global notification service."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the notification service."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Storage
        self.templates: Dict[str, NotificationTemplate] = {}
        self.preferences: Dict[str, UserPreferences] = {}
        self.notifications: Dict[str, Notification] = {}
        self.delivery_receipts: Dict[str, List[DeliveryReceipt]] = defaultdict(list)

        # Queues by priority
        self.queues: Dict[NotificationPriority, deque] = {
            priority: deque() for priority in NotificationPriority
        }
        self.scheduled_notifications: Dict[str, Notification] = {}

        # Configuration
        self.retry_delays = [60, 300, 900]  # 1 min, 5 min, 15 min
        self.batch_size = 100
        self.enable_quiet_hours = True

        # Provider stubs (would be replaced with real integrations)
        self._email_enabled = False
        self._sms_enabled = False
        self._push_enabled = False

        logger.info("Notification Service initialized")

    # ========================================================================
    # Template Management
    # ========================================================================

    def create_template(
        self,
        template_id: str,
        name: str,
        channel: NotificationChannel,
        category: NotificationCategory,
        subject_template: str,
        body_template: str,
        default_values: Optional[Dict[str, str]] = None
    ) -> NotificationTemplate:
        """
        Create a new notification template.

        Args:
            template_id: Unique template identifier
            name: Human-readable template name
            channel: Target channel
            category: Notification category
            subject_template: Subject line template (for email)
            body_template: Message body template
            default_values: Default values for variables

        Returns:
            NotificationTemplate object
        """
        try:
            # Extract variables from templates
            variables = self._extract_variables(subject_template, body_template)

            template = NotificationTemplate(
                template_id=template_id,
                name=name,
                channel=channel,
                category=category,
                subject_template=subject_template,
                body_template=body_template,
                variables=variables,
                default_values=default_values or {}
            )

            self.templates[template_id] = template
            logger.info(f"Created template: {template_id} for {channel}")

            return template

        except Exception as e:
            logger.error(f"Failed to create template {template_id}: {e}")
            raise TemplateError(f"Template creation failed: {e}")

    def render_template(
        self,
        template_id: str,
        variables: Dict[str, str]
    ) -> tuple[str, str]:
        """
        Render a template with provided variables.

        Args:
            template_id: Template to render
            variables: Variable values

        Returns:
            Tuple of (subject, body)
        """
        try:
            if template_id not in self.templates:
                raise TemplateError(f"Template not found: {template_id}")

            template = self.templates[template_id]

            # Merge with defaults
            merged_vars = {**template.default_values, **variables}

            # Check required variables
            missing = template.variables - set(merged_vars.keys())
            if missing:
                raise TemplateError(f"Missing required variables: {missing}")

            # Render subject and body
            subject = self._substitute_variables(template.subject_template, merged_vars)
            body = self._substitute_variables(template.body_template, merged_vars)

            return subject, body

        except TemplateError:
            raise
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            raise TemplateError(f"Rendering failed: {e}")

    def _extract_variables(self, *templates: str) -> Set[str]:
        """Extract variable names from templates (format: {{variable_name}})."""
        variables = set()
        pattern = r'\{\{(\w+)\}\}'

        for template in templates:
            matches = re.findall(pattern, template)
            variables.update(matches)

        return variables

    def _substitute_variables(self, template: str, variables: Dict[str, str]) -> str:
        """Substitute variables in template."""
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{{{key}}}}}", str(value))
        return result

    # ========================================================================
    # User Preferences
    # ========================================================================

    def set_user_preferences(self, preferences: UserPreferences) -> None:
        """Set notification preferences for a user."""
        try:
            self.preferences[preferences.user_id] = preferences
            logger.info(f"Updated preferences for user {preferences.user_id}")

        except Exception as e:
            logger.error(f"Failed to set preferences: {e}")
            raise PreferenceError(f"Preference update failed: {e}")

    def get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get notification preferences for a user."""
        if user_id not in self.preferences:
            # Return default preferences
            return UserPreferences(
                user_id=user_id,
                enabled_channels={
                    NotificationChannel.EMAIL,
                    NotificationChannel.IN_APP
                },
                muted_categories=set()
            )

        return self.preferences[user_id]

    def is_channel_allowed(
        self,
        user_id: str,
        channel: NotificationChannel,
        category: NotificationCategory
    ) -> bool:
        """Check if a notification channel is allowed for a user."""
        prefs = self.get_user_preferences(user_id)

        # Check if channel is enabled
        if channel not in prefs.enabled_channels:
            return False

        # Check if category is muted
        if category in prefs.muted_categories:
            return False

        # Check quiet hours
        if self.enable_quiet_hours and prefs.quiet_hours_start is not None:
            current_hour = datetime.utcnow().hour
            if self._is_quiet_hours(current_hour, prefs.quiet_hours_start, prefs.quiet_hours_end):
                return False

        return True

    def _is_quiet_hours(self, current: int, start: int, end: int) -> bool:
        """Check if current hour is within quiet hours."""
        if end > start:
            return start <= current < end
        else:  # Wraps around midnight
            return current >= start or current < end

    # ========================================================================
    # Notification Sending
    # ========================================================================

    def send_notification(
        self,
        notification_id: str,
        user_id: str,
        template_id: str,
        variables: Dict[str, str],
        channel: Optional[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        scheduled_at: Optional[datetime] = None
    ) -> Notification:
        """
        Send a notification to a user.

        Args:
            notification_id: Unique notification ID
            user_id: Target user
            template_id: Template to use
            variables: Template variables
            channel: Override channel (uses template default if None)
            priority: Notification priority
            scheduled_at: Optional scheduled delivery time

        Returns:
            Notification object
        """
        try:
            # Get template
            if template_id not in self.templates:
                raise NotificationError(f"Template not found: {template_id}")

            template = self.templates[template_id]
            target_channel = channel or template.channel

            # Check user preferences
            if not self.is_channel_allowed(user_id, target_channel, template.category):
                logger.info(f"Notification blocked by user preferences: {user_id}")
                raise NotificationError("Notification blocked by user preferences")

            # Render template
            subject, body = self.render_template(template_id, variables)

            # Create notification
            notification = Notification(
                notification_id=notification_id,
                user_id=user_id,
                channel=target_channel,
                category=template.category,
                priority=priority,
                subject=subject,
                body=body,
                status=NotificationStatus.PENDING,
                scheduled_at=scheduled_at
            )

            self.notifications[notification_id] = notification

            # Queue for delivery
            if scheduled_at is None or scheduled_at <= datetime.utcnow():
                self._queue_notification(notification)
            else:
                notification.status = NotificationStatus.QUEUED
                self.scheduled_notifications[notification.notification_id] = notification

            logger.info(f"Queued notification {notification_id} for user {user_id} via {target_channel}")

            return notification

        except (NotificationError, TemplateError):
            raise
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            raise NotificationError(f"Notification failed: {e}")

    def send_batch(self, request: BatchNotificationRequest) -> List[str]:
        """
        Send notifications to multiple recipients.

        Args:
            request: Batch notification request

        Returns:
            List of notification IDs
        """
        try:
            notification_ids = []

            for i, user_id in enumerate(request.recipients):
                notification_id = f"{request.batch_id}_{i}"

                try:
                    notification = self.send_notification(
                        notification_id=notification_id,
                        user_id=user_id,
                        template_id=request.template_id,
                        variables=request.variables,
                        channel=request.channel,
                        priority=request.priority,
                        scheduled_at=request.scheduled_at
                    )
                    notification_ids.append(notification_id)

                except Exception as e:
                    logger.warning(f"Failed to send to user {user_id}: {e}")
                    continue

            logger.info(f"Batch {request.batch_id}: {len(notification_ids)}/{len(request.recipients)} queued")

            return notification_ids

        except Exception as e:
            logger.error(f"Batch send failed: {e}")
            raise NotificationError(f"Batch send failed: {e}")

    # ========================================================================
    # Delivery & Tracking
    # ========================================================================

    def _queue_notification(self, notification: Notification) -> None:
        """Add notification to priority queue."""
        self.queues[notification.priority].append(notification)
        notification.status = NotificationStatus.QUEUED

    def _enqueue_ready_scheduled_notifications(self) -> None:
        """Move scheduled notifications into active queues when they become due."""
        now = datetime.utcnow()
        ready_notification_ids = [
            notification_id
            for notification_id, notification in self.scheduled_notifications.items()
            if notification.scheduled_at is None or notification.scheduled_at <= now
        ]

        for notification_id in ready_notification_ids:
            notification = self.scheduled_notifications.pop(notification_id)
            self._queue_notification(notification)

    async def process_queue(self) -> int:
        """
        Process queued notifications.

        Returns:
            Number of notifications processed
        """
        processed = 0
        self._enqueue_ready_scheduled_notifications()

        # Process in priority order
        for priority in [
            NotificationPriority.URGENT,
            NotificationPriority.HIGH,
            NotificationPriority.NORMAL,
            NotificationPriority.LOW
        ]:
            queue = self.queues[priority]

            while queue and processed < self.batch_size:
                notification = queue.popleft()

                try:
                    await self._deliver_notification(notification)
                    processed += 1

                except DeliveryError as e:
                    logger.warning(f"Delivery failed for {notification.notification_id}: {e}")
                    self._handle_delivery_failure(notification, str(e))

        return processed

    async def _deliver_notification(self, notification: Notification) -> None:
        """Deliver a notification via the appropriate channel."""
        notification.status = NotificationStatus.SENDING

        try:
            if notification.channel == NotificationChannel.EMAIL:
                await self._send_email(notification)
            elif notification.channel == NotificationChannel.SMS:
                await self._send_sms(notification)
            elif notification.channel == NotificationChannel.PUSH:
                await self._send_push(notification)
            elif notification.channel == NotificationChannel.IN_APP:
                await self._send_in_app(notification)

            notification.status = NotificationStatus.SENT
            notification.sent_at = datetime.utcnow()

            # Record delivery receipt
            receipt = DeliveryReceipt(
                notification_id=notification.notification_id,
                channel=notification.channel,
                status=NotificationStatus.DELIVERED,
                timestamp=datetime.utcnow()
            )
            self.delivery_receipts[notification.notification_id].append(receipt)

            logger.info(f"Delivered notification {notification.notification_id}")

        except Exception as e:
            raise DeliveryError(f"Delivery failed: {e}")

    async def _send_email(self, notification: Notification) -> None:
        """Send email notification (stub implementation)."""
        if not self._email_enabled:
            logger.debug(f"Email stub: {notification.subject} to user {notification.user_id}")
            await asyncio.sleep(0.1)  # Simulate delivery
            return

        # Real implementation would use SMTP
        raise NotImplementedError("Email provider not configured")

    async def _send_sms(self, notification: Notification) -> None:
        """Send SMS notification (stub implementation)."""
        if not self._sms_enabled:
            logger.debug(f"SMS stub: {notification.body[:50]} to user {notification.user_id}")
            await asyncio.sleep(0.1)  # Simulate delivery
            return

        # Real implementation would use Twilio
        raise NotImplementedError("SMS provider not configured")

    async def _send_push(self, notification: Notification) -> None:
        """Send push notification (stub implementation)."""
        if not self._push_enabled:
            logger.debug(f"Push stub: {notification.subject} to user {notification.user_id}")
            await asyncio.sleep(0.1)  # Simulate delivery
            return

        # Real implementation would use Firebase
        raise NotImplementedError("Push provider not configured")

    async def _send_in_app(self, notification: Notification) -> None:
        """Send in-app notification (always available)."""
        # In-app notifications are just stored and displayed in UI
        logger.debug(f"In-app notification created for user {notification.user_id}")
        await asyncio.sleep(0.01)

    def _handle_delivery_failure(self, notification: Notification, error: str) -> None:
        """Handle failed notification delivery with retry logic."""
        notification.retry_count += 1
        notification.error_message = error

        if notification.retry_count < notification.max_retries:
            # Re-queue with delay
            notification.status = NotificationStatus.PENDING
            self._queue_notification(notification)
            logger.info(f"Retry {notification.retry_count}/{notification.max_retries} for {notification.notification_id}")
        else:
            # Max retries exceeded
            notification.status = NotificationStatus.FAILED
            logger.error(f"Notification {notification.notification_id} failed after {notification.retry_count} retries")

            # Record failure receipt
            receipt = DeliveryReceipt(
                notification_id=notification.notification_id,
                channel=notification.channel,
                status=NotificationStatus.FAILED,
                timestamp=datetime.utcnow(),
                error_details=error
            )
            self.delivery_receipts[notification.notification_id].append(receipt)

    # ========================================================================
    # Reporting & Analytics
    # ========================================================================

    def get_notification_status(self, notification_id: str) -> Optional[Notification]:
        """Get current status of a notification."""
        return self.notifications.get(notification_id)

    def get_delivery_receipts(self, notification_id: str) -> List[DeliveryReceipt]:
        """Get all delivery receipts for a notification."""
        return self.delivery_receipts.get(notification_id, [])

    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        notifications = [
            n for n in self.notifications.values()
            if n.user_id == user_id
        ]

        # Sort by creation time (newest first)
        notifications.sort(key=lambda n: n.created_at, reverse=True)

        return notifications[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get notification service statistics."""
        total = len(self.notifications)
        by_status = defaultdict(int)
        by_channel = defaultdict(int)

        for notification in self.notifications.values():
            by_status[notification.status.value] += 1
            by_channel[notification.channel.value] += 1

        return {
            "total_notifications": total,
            "by_status": dict(by_status),
            "by_channel": dict(by_channel),
            "queue_sizes": {
                priority.value: len(queue)
                for priority, queue in self.queues.items()
            },
            "scheduled_notifications": len(self.scheduled_notifications),
            "templates_count": len(self.templates),
            "users_with_preferences": len(self.preferences)
        }


# ============================================================================
# Singleton Instance
# ============================================================================

# Global singleton instance
notification_service = NotificationService()
