"""
Notification processor for Apprise Smart Notification Handler.
"""

from logging import Logger
from typing import Any, Dict, List, Optional

try:
    # Try relative imports first (when used as a package)
    from .email_threading import EmailThreadingStrategy, NotificationEventType
    from .apprise_email_wrapper import AppriseWithEmailHeaders, is_email_notification
except ImportError:
    # Fall back to absolute imports (when imported directly from tests)
    from email_threading import EmailThreadingStrategy, NotificationEventType  # type: ignore[no-redef]
    from apprise_email_wrapper import AppriseWithEmailHeaders, is_email_notification  # type: ignore[no-redef]


class NotificationProcessor:
    """Handles processing and sending of notifications."""

    def __init__(self, logger: Logger, domain: str = "notifications.bely.app"):
        """
        Initialize the notification processor.

        Args:
            logger: Logger instance for output
            domain: Domain for email threading IDs (default: notifications.bely.app)
        """

        self.logger = logger

        # Per-endpoint tracking: each entry is a dict with
        # {"apprise": AppriseWithEmailHeaders, "settings": Dict[str, bool], "has_email": bool}
        self.user_endpoint_configs: Dict[str, List[dict]] = {}

        # Initialize email threading strategy
        self.email_threading = EmailThreadingStrategy(domain=domain)

    def initialize_from_config(self, config: Dict[str, Any], config_loader: Any) -> None:
        """
        Initialize Apprise instances from configuration.

        Supports two config formats:
        - API format: user_config has "configs" list with per-endpoint dicts
        - YAML format: user_config has "apprise_urls" list with shared "notifications"

        Args:
            config: Configuration dictionary
            config_loader: ConfigLoader instance for URL processing
        """
        global_config = config.get("global", {})
        users_config = config.get("users", {})

        for username, user_config in users_config.items():
            try:
                if "configs" in user_config:
                    # API format: per-endpoint configs
                    for endpoint_config in user_config["configs"]:
                        self._add_endpoint(
                            username,
                            endpoint_config["apprise_url"],
                            endpoint_config.get("notifications", {}),
                            config_loader,
                            global_config,
                        )
                else:
                    # YAML format: shared notifications across all URLs
                    apprise_urls = user_config.get("apprise_urls", [])
                    if isinstance(apprise_urls, str):
                        apprise_urls = [apprise_urls]
                    notifications = user_config.get("notifications", {})

                    for url in apprise_urls:
                        self._add_endpoint(
                            username, url, notifications, config_loader, global_config
                        )

            except Exception as e:
                self.logger.error(f"Error initializing Apprise for user {username}: {e}")

    def _add_endpoint(
        self,
        username: str,
        url: str,
        notifications: Dict[str, bool],
        config_loader: Any,
        global_config: Dict[str, Any],
    ) -> None:
        """
        Add a single notification endpoint for a user.

        Args:
            username: Username this endpoint belongs to
            url: Apprise URL for the endpoint
            notifications: Notification preferences for this endpoint
            config_loader: ConfigLoader instance for URL processing
            global_config: Global configuration dictionary
        """
        apobj = AppriseWithEmailHeaders()
        processed_url = config_loader.process_apprise_url(url, global_config)

        if not apobj.add(processed_url):
            self.logger.warning(f"Failed to add Apprise URL for user {username}: {url}")
            return

        has_email = is_email_notification(processed_url)

        settings = {
            "entry_updates": notifications.get("entry_updates", True),
            "own_entry_edits": notifications.get("own_entry_edits", True),
            "entry_replies": notifications.get("entry_replies", True),
            "new_entries": notifications.get("new_entries", True),
            "reactions": notifications.get("reactions", True),
            "document_replies": notifications.get("document_replies", True),
        }

        if username not in self.user_endpoint_configs:
            self.user_endpoint_configs[username] = []

        self.user_endpoint_configs[username].append(
            {
                "apprise": apobj,
                "settings": settings,
                "has_email": has_email,
            }
        )

        self.logger.debug(f"Added endpoint for user: {username} (has_email: {has_email})")

    def should_notify(self, username: Optional[str], notification_type: str) -> bool:
        """
        Check if user should be notified for this type of event.

        Returns True if ANY endpoint for the user has this notification type enabled.

        Args:
            username: Username to check
            notification_type: Type of notification (entry_updates, own_entry_edits,
                             entry_replies, new_entries, reactions, document_replies)

        Returns:
            True if user should be notified, False otherwise
        """
        if not username:
            return False

        endpoints = self.user_endpoint_configs.get(username)
        if not endpoints:
            return False

        return any(ep["settings"].get(notification_type, True) for ep in endpoints)

    async def send_notification(
        self,
        username: Optional[str],
        title: str,
        body: str,
        headers: Optional[Dict[str, str]] = None,
        notification_type: Optional[str] = None,
    ) -> None:
        """
        Send notification to user via Apprise.

        When notification_type is provided, only sends to endpoints that have
        that type enabled. When None, sends to all endpoints.

        Args:
            username: Username to notify
            title: Notification title
            body: Notification body
            headers: Optional headers (used for email threading)
            notification_type: Optional notification type to filter endpoints
        """
        endpoints = self.user_endpoint_configs.get(username) if username else None
        if not endpoints:
            self.logger.debug(f"No notification endpoints for user: {username}")
            return

        for ep in endpoints:
            # Filter by notification type if specified
            if notification_type and not ep["settings"].get(notification_type, True):
                continue

            try:
                apobj = ep["apprise"]
                has_email = ep["has_email"]

                if headers and has_email:
                    result = apobj.notify(
                        body=body,
                        title=title,
                        headers=headers,
                    )
                    self.logger.debug(
                        f"Sent notification with email threading headers to {username}"
                    )
                else:
                    result = apobj.notify(
                        body=body,
                        title=title,
                    )

                if result:
                    self.logger.info(f"Notification sent to {username}: {title}")
                else:
                    self.logger.warning(f"Failed to send notification to {username}")

            except Exception as e:
                self.logger.error(f"Error sending notification to {username}: {e}", exc_info=True)

    async def send_notification_with_threading(
        self,
        username: Optional[str],
        title: str,
        body: str,
        event_type: NotificationEventType,
        document_id: str,
        document_name: str,
        entry_id: Optional[str] = None,
        parent_entry_id: Optional[str] = None,
        action_by: Optional[str] = None,
        notification_type: Optional[str] = None,
    ) -> None:
        """
        Send notification with email threading support.

        Args:
            username: Username to notify
            title: Notification title (will be overridden for threading)
            body: Notification body
            event_type: Type of notification event
            document_id: The document ID
            document_name: The document name
            entry_id: The log entry ID (if applicable)
            parent_entry_id: The parent entry ID (for replies)
            action_by: User who performed the action
            notification_type: Optional notification type to filter endpoints
        """
        endpoints = self.user_endpoint_configs.get(username) if username else None
        if not endpoints:
            self.logger.debug(f"No notification endpoints for user: {username}")
            return

        # Check if any endpoint for this user has email notifications
        has_email = any(ep["has_email"] for ep in endpoints)

        # Generate appropriate subject based on notification type
        action_desc = f"by {action_by}" if action_by else None
        threaded_subject = self.email_threading.generate_subject(
            event_type=event_type,
            document_title=document_name,
            action_description=action_desc,
            is_email=has_email,
        )

        # Generate email headers if any endpoint has email notifications
        headers = None
        if has_email:
            try:
                headers = self.email_threading.get_email_headers(
                    event_type=event_type,
                    document_id=document_id,
                    document_name=document_name,
                    entry_id=entry_id,
                    parent_entry_id=parent_entry_id,
                )
                self.logger.debug(f"Generated email threading headers for {username}: {headers}")
            except ValueError as e:
                self.logger.warning(f"Failed to generate email headers: {e}")

        # Send notification with threading support
        await self.send_notification(username, threaded_subject, body, headers, notification_type)

    async def process_notifications(
        self, event: Any, notification_configs: List[Dict[str, Any]]
    ) -> None:
        """
        Process and send notifications based on configuration.

        Args:
            event: The event to process
            notification_configs: List of dicts with:
                - username: User to notify
                - notification_type: Type of notification setting to check
                - title: Notification title
                - body: Notification body
                - context: Optional context for trigger description
                - event_type: Optional NotificationEventType for threading
                - entry_id: Optional entry ID for threading
                - parent_entry_id: Optional parent entry ID for threading
        """
        notifications_sent = []

        for config in notification_configs:
            username = config["username"]
            notification_type = config["notification_type"]

            # Skip if already notified or shouldn't notify
            if username in notifications_sent:
                continue
            if not self.should_notify(username, notification_type):
                continue
            if event.event_triggered_by_username == username:
                continue

            title = config["title"]
            body = config["body"]

            # Check if we have threading information
            if "event_type" in config and hasattr(event, "parent_log_document_info"):
                # Use threading-aware notification
                await self.send_notification_with_threading(
                    username=username,
                    title=title,
                    body=body,
                    event_type=config["event_type"],
                    document_id=event.parent_log_document_info.id,
                    document_name=event.parent_log_document_info.name,
                    entry_id=config.get("entry_id"),
                    parent_entry_id=config.get("parent_entry_id"),
                    action_by=event.event_triggered_by_username,
                    notification_type=notification_type,
                )
            else:
                # Fall back to simple notification
                await self.send_notification(
                    username, title, body, notification_type=notification_type
                )

            notifications_sent.append(username)
