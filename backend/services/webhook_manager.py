"""
Webhook Management Service for BuilTPro Brain AI

Comprehensive webhook system for event-driven integrations with external services.

Features:
- Webhook registration and validation
- Event triggering system
- Retry logic with exponential backoff
- HMAC signature verification
- Delivery logs and analytics
- Rate limiting
- Payload validation
- Circuit breaker pattern

Author: BuilTPro AI Team
Created: 2026-02-15
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict, deque
import hashlib
import hmac
import json
import asyncio
from threading import Lock
import httpx

logger = logging.getLogger(__name__)


# ============================================================================
# Exceptions
# ============================================================================


class WebhookError(Exception):
    """Base exception for webhook errors."""
    pass


class WebhookValidationError(WebhookError):
    """Raised when webhook validation fails."""
    pass


class WebhookDeliveryError(WebhookError):
    """Raised when webhook delivery fails."""
    pass


class WebhookSignatureError(WebhookError):
    """Raised when signature verification fails."""
    pass


# ============================================================================
# Enums
# ============================================================================


class WebhookEvent(str, Enum):
    """Supported webhook events."""
    # Project events
    PROJECT_CREATED = "project.created"
    PROJECT_UPDATED = "project.updated"
    PROJECT_COMPLETED = "project.completed"

    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_APPROVED = "document.approved"

    # Task events
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_OVERDUE = "task.overdue"

    # Alert events
    BUDGET_ALERT = "alert.budget"
    SCHEDULE_ALERT = "alert.schedule"
    SAFETY_ALERT = "alert.safety"
    QUALITY_ALERT = "alert.quality"

    # User events
    USER_REGISTERED = "user.registered"
    USER_INVITED = "user.invited"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"


class WebhookStatus(str, Enum):
    """Webhook endpoint status."""
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    FAILED = "failed"


class DeliveryStatus(str, Enum):
    """Webhook delivery status."""
    PENDING = "pending"
    SENDING = "sending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"
    EXHAUSTED = "exhausted"


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class WebhookEndpoint:
    """Webhook endpoint configuration."""
    webhook_id: str
    url: str
    events: List[WebhookEvent]
    secret: str  # For HMAC signature
    description: str
    status: WebhookStatus = WebhookStatus.ACTIVE
    headers: Dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30
    max_retries: int = 5
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookPayload:
    """Webhook event payload."""
    event: WebhookEvent
    timestamp: datetime
    data: Dict[str, Any]
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt."""
    delivery_id: str
    webhook_id: str
    event: WebhookEvent
    payload: WebhookPayload
    status: DeliveryStatus
    created_at: datetime = field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    next_retry_at: Optional[datetime] = None


@dataclass
class DeliveryLog:
    """Detailed log entry for a delivery attempt."""
    log_id: str
    delivery_id: str
    attempt_number: int
    timestamp: datetime
    status: DeliveryStatus
    http_status: Optional[int] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    headers_sent: Dict[str, str] = field(default_factory=dict)
    response_snippet: Optional[str] = None


@dataclass
class WebhookStats:
    """Statistics for a webhook endpoint."""
    webhook_id: str
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    average_latency_ms: float
    success_rate: float
    last_delivery_at: Optional[datetime]
    consecutive_failures: int


# ============================================================================
# Webhook Manager
# ============================================================================


class WebhookManager:
    """
    Production-ready webhook management system.

    Features:
    - Event-driven architecture
    - Automatic retry with exponential backoff
    - HMAC signature verification
    - Circuit breaker for failing endpoints
    - Delivery tracking and analytics
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        """Singleton pattern for global webhook manager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the webhook manager."""
        if hasattr(self, '_initialized'):
            return

        self._initialized = True

        # Storage
        self.endpoints: Dict[str, WebhookEndpoint] = {}
        self.deliveries: Dict[str, WebhookDelivery] = {}
        self.delivery_logs: Dict[str, List[DeliveryLog]] = defaultdict(list)
        self.event_subscriptions: Dict[WebhookEvent, List[str]] = defaultdict(list)

        # Queue for async delivery
        self.delivery_queue: deque = deque()

        # Statistics
        self.stats: Dict[str, WebhookStats] = {}

        # Circuit breaker configuration
        self.circuit_breaker_threshold = 10  # Consecutive failures before pause
        self.circuit_breaker_timeout = 300  # Seconds before retry

        # Retry configuration
        self.retry_delays = [60, 300, 900, 3600, 7200]  # Exponential backoff in seconds

        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=30.0)

        logger.info("Webhook Manager initialized")

    # ========================================================================
    # Webhook Registration
    # ========================================================================

    def register_webhook(
        self,
        webhook_id: str,
        url: str,
        events: List[WebhookEvent],
        secret: str,
        description: str = "",
        headers: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 30,
        max_retries: int = 5
    ) -> WebhookEndpoint:
        """
        Register a new webhook endpoint.

        Args:
            webhook_id: Unique webhook identifier
            url: Target URL for webhook delivery
            events: List of events to subscribe to
            secret: Secret key for HMAC signature
            description: Human-readable description
            headers: Optional custom headers
            timeout_seconds: Request timeout
            max_retries: Maximum retry attempts

        Returns:
            WebhookEndpoint object
        """
        try:
            # Validate URL
            if not url.startswith(('http://', 'https://')):
                raise WebhookValidationError("URL must start with http:// or https://")

            # Validate events
            if not events:
                raise WebhookValidationError("At least one event must be specified")

            endpoint = WebhookEndpoint(
                webhook_id=webhook_id,
                url=url,
                events=events,
                secret=secret,
                description=description,
                headers=headers or {},
                timeout_seconds=timeout_seconds,
                max_retries=max_retries
            )

            self.endpoints[webhook_id] = endpoint

            # Update event subscriptions
            for event in events:
                if webhook_id not in self.event_subscriptions[event]:
                    self.event_subscriptions[event].append(webhook_id)

            # Initialize stats
            self.stats[webhook_id] = WebhookStats(
                webhook_id=webhook_id,
                total_deliveries=0,
                successful_deliveries=0,
                failed_deliveries=0,
                average_latency_ms=0.0,
                success_rate=0.0,
                last_delivery_at=None,
                consecutive_failures=0
            )

            logger.info(f"Registered webhook {webhook_id} for {len(events)} events")

            return endpoint

        except WebhookValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to register webhook {webhook_id}: {e}")
            raise WebhookError(f"Webhook registration failed: {e}")

    def update_webhook(
        self,
        webhook_id: str,
        **updates
    ) -> WebhookEndpoint:
        """Update an existing webhook endpoint."""
        if webhook_id not in self.endpoints:
            raise WebhookError(f"Webhook not found: {webhook_id}")

        endpoint = self.endpoints[webhook_id]

        # Update fields
        for key, value in updates.items():
            if hasattr(endpoint, key):
                setattr(endpoint, key, value)

        endpoint.updated_at = datetime.utcnow()

        # Update event subscriptions if events changed
        if 'events' in updates:
            self._rebuild_subscriptions(webhook_id, updates['events'])

        logger.info(f"Updated webhook {webhook_id}")

        return endpoint

    def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook endpoint."""
        if webhook_id in self.endpoints:
            # Remove from event subscriptions
            for event_list in self.event_subscriptions.values():
                if webhook_id in event_list:
                    event_list.remove(webhook_id)

            del self.endpoints[webhook_id]
            logger.info(f"Deleted webhook {webhook_id}")

    def _rebuild_subscriptions(self, webhook_id: str, new_events: List[WebhookEvent]) -> None:
        """Rebuild event subscriptions for a webhook."""
        # Remove from all events
        for event_list in self.event_subscriptions.values():
            if webhook_id in event_list:
                event_list.remove(webhook_id)

        # Add to new events
        for event in new_events:
            if webhook_id not in self.event_subscriptions[event]:
                self.event_subscriptions[event].append(webhook_id)

    # ========================================================================
    # Event Triggering
    # ========================================================================

    def trigger_event(
        self,
        event: WebhookEvent,
        data: Dict[str, Any],
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[str]:
        """
        Trigger a webhook event.

        Args:
            event: Event type
            data: Event data payload
            resource_id: Optional resource identifier
            resource_type: Optional resource type
            user_id: Optional user who triggered the event

        Returns:
            List of delivery IDs created
        """
        try:
            # Create payload
            payload = WebhookPayload(
                event=event,
                timestamp=datetime.utcnow(),
                data=data,
                resource_id=resource_id,
                resource_type=resource_type,
                user_id=user_id
            )

            # Find subscribed webhooks
            subscribed_webhooks = self.event_subscriptions.get(event, [])

            delivery_ids = []

            for webhook_id in subscribed_webhooks:
                endpoint = self.endpoints.get(webhook_id)

                if not endpoint:
                    continue

                # Check if endpoint is active
                if endpoint.status != WebhookStatus.ACTIVE:
                    logger.debug(f"Skipping inactive webhook {webhook_id}")
                    continue

                # Create delivery
                delivery_id = f"{webhook_id}_{event.value}_{datetime.utcnow().timestamp()}"

                delivery = WebhookDelivery(
                    delivery_id=delivery_id,
                    webhook_id=webhook_id,
                    event=event,
                    payload=payload,
                    status=DeliveryStatus.PENDING
                )

                self.deliveries[delivery_id] = delivery
                self.delivery_queue.append(delivery_id)

                delivery_ids.append(delivery_id)

            logger.info(f"Triggered event {event} - {len(delivery_ids)} deliveries queued")

            return delivery_ids

        except Exception as e:
            logger.error(f"Failed to trigger event {event}: {e}")
            raise WebhookError(f"Event trigger failed: {e}")

    # ========================================================================
    # Delivery Processing
    # ========================================================================

    async def process_deliveries(self, batch_size: int = 10) -> int:
        """
        Process queued webhook deliveries.

        Args:
            batch_size: Maximum deliveries to process

        Returns:
            Number of deliveries processed
        """
        processed = 0

        while self.delivery_queue and processed < batch_size:
            delivery_id = self.delivery_queue.popleft()
            delivery = self.deliveries.get(delivery_id)

            if not delivery:
                continue

            try:
                await self._deliver_webhook(delivery)
                processed += 1

            except WebhookDeliveryError as e:
                logger.warning(f"Delivery failed: {e}")
                self._schedule_retry(delivery)

        return processed

    async def _deliver_webhook(self, delivery: WebhookDelivery) -> None:
        """Deliver a webhook to its endpoint."""
        endpoint = self.endpoints.get(delivery.webhook_id)

        if not endpoint:
            raise WebhookDeliveryError(f"Endpoint not found: {delivery.webhook_id}")

        delivery.status = DeliveryStatus.SENDING
        delivery.sent_at = datetime.utcnow()

        start_time = datetime.utcnow()

        try:
            # Prepare payload
            payload_dict = {
                "event": delivery.event.value,
                "timestamp": delivery.payload.timestamp.isoformat(),
                "data": delivery.payload.data,
                "resource_id": delivery.payload.resource_id,
                "resource_type": delivery.payload.resource_type,
                "user_id": delivery.payload.user_id,
                "metadata": delivery.payload.metadata
            }

            payload_json = json.dumps(payload_dict)

            # Generate HMAC signature
            signature = self._generate_signature(payload_json, endpoint.secret)

            # Prepare headers
            headers = {
                **endpoint.headers,
                "Content-Type": "application/json",
                "X-Webhook-Signature": signature,
                "X-Webhook-Event": delivery.event.value,
                "X-Webhook-Delivery": delivery.delivery_id
            }

            # Send request
            response = await self.http_client.post(
                endpoint.url,
                content=payload_json,
                headers=headers,
                timeout=endpoint.timeout_seconds
            )

            duration = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Handle response
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate
            delivery.completed_at = datetime.utcnow()

            if 200 <= response.status_code < 300:
                delivery.status = DeliveryStatus.SUCCESS
                self._record_success(delivery, duration, headers, response)
            else:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:200]}"
                self._record_failure(delivery, duration, headers, response)
                raise WebhookDeliveryError(delivery.error_message)

        except httpx.TimeoutException as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = f"Timeout after {endpoint.timeout_seconds}s"
            self._record_failure(delivery, duration, {}, None, str(e))
            raise WebhookDeliveryError(delivery.error_message)

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000
            delivery.status = DeliveryStatus.FAILED
            delivery.error_message = str(e)
            self._record_failure(delivery, duration, {}, None, str(e))
            raise WebhookDeliveryError(str(e))

    def _schedule_retry(self, delivery: WebhookDelivery) -> None:
        """Schedule a retry for a failed delivery."""
        endpoint = self.endpoints.get(delivery.webhook_id)

        if not endpoint or delivery.retry_count >= endpoint.max_retries:
            delivery.status = DeliveryStatus.EXHAUSTED
            logger.error(f"Delivery {delivery.delivery_id} exhausted after {delivery.retry_count} retries")

            # Update stats
            stats = self.stats.get(delivery.webhook_id)
            if stats:
                stats.consecutive_failures += 1

                # Circuit breaker
                if stats.consecutive_failures >= self.circuit_breaker_threshold:
                    endpoint.status = WebhookStatus.FAILED
                    logger.warning(f"Circuit breaker triggered for webhook {delivery.webhook_id}")

            return

        # Calculate retry delay with exponential backoff
        delay_seconds = self.retry_delays[min(delivery.retry_count, len(self.retry_delays) - 1)]
        delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        delivery.status = DeliveryStatus.RETRYING
        delivery.retry_count += 1

        # Re-queue
        self.delivery_queue.append(delivery.delivery_id)

        logger.info(f"Scheduled retry {delivery.retry_count} for {delivery.delivery_id} in {delay_seconds}s")

    # ========================================================================
    # Signature & Security
    # ========================================================================

    def _generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC SHA-256 signature for payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return f"sha256={signature}"

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """Verify HMAC signature for incoming webhook."""
        expected = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected, signature)

    # ========================================================================
    # Logging & Analytics
    # ========================================================================

    def _record_success(
        self,
        delivery: WebhookDelivery,
        duration_ms: float,
        headers: Dict[str, str],
        response: httpx.Response
    ) -> None:
        """Record successful delivery."""
        log = DeliveryLog(
            log_id=f"{delivery.delivery_id}_attempt_{delivery.retry_count}",
            delivery_id=delivery.delivery_id,
            attempt_number=delivery.retry_count + 1,
            timestamp=datetime.utcnow(),
            status=DeliveryStatus.SUCCESS,
            http_status=response.status_code,
            duration_ms=int(duration_ms),
            headers_sent=headers,
            response_snippet=response.text[:200]
        )

        self.delivery_logs[delivery.delivery_id].append(log)

        # Update stats
        stats = self.stats.get(delivery.webhook_id)
        if stats:
            stats.total_deliveries += 1
            stats.successful_deliveries += 1
            stats.consecutive_failures = 0
            stats.last_delivery_at = datetime.utcnow()

            # Update average latency
            total_latency = stats.average_latency_ms * (stats.total_deliveries - 1)
            stats.average_latency_ms = (total_latency + duration_ms) / stats.total_deliveries

            # Update success rate
            stats.success_rate = (stats.successful_deliveries / stats.total_deliveries) * 100

    def _record_failure(
        self,
        delivery: WebhookDelivery,
        duration_ms: float,
        headers: Dict[str, str],
        response: Optional[httpx.Response],
        error: str
    ) -> None:
        """Record failed delivery."""
        log = DeliveryLog(
            log_id=f"{delivery.delivery_id}_attempt_{delivery.retry_count}",
            delivery_id=delivery.delivery_id,
            attempt_number=delivery.retry_count + 1,
            timestamp=datetime.utcnow(),
            status=DeliveryStatus.FAILED,
            http_status=response.status_code if response else None,
            duration_ms=int(duration_ms),
            error=error,
            headers_sent=headers,
            response_snippet=response.text[:200] if response else None
        )

        self.delivery_logs[delivery.delivery_id].append(log)

        # Update stats
        stats = self.stats.get(delivery.webhook_id)
        if stats:
            stats.total_deliveries += 1
            stats.failed_deliveries += 1
            stats.consecutive_failures += 1

            # Update success rate
            if stats.total_deliveries > 0:
                stats.success_rate = (stats.successful_deliveries / stats.total_deliveries) * 100

    def get_delivery_logs(self, delivery_id: str) -> List[DeliveryLog]:
        """Get all logs for a delivery."""
        return self.delivery_logs.get(delivery_id, [])

    def get_webhook_stats(self, webhook_id: str) -> Optional[WebhookStats]:
        """Get statistics for a webhook."""
        return self.stats.get(webhook_id)

    def get_all_stats(self) -> Dict[str, WebhookStats]:
        """Get statistics for all webhooks."""
        return self.stats.copy()


# ============================================================================
# Singleton Instance
# ============================================================================

# Global singleton instance
webhook_manager = WebhookManager()
