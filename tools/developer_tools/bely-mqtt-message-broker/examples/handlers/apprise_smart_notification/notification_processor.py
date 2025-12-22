"""
Notification processor for Apprise Smart Notification Handler.
"""

from logging import Logger
from typing import Any, Dict, List, Optional

try:
    import apprise

    APPRISE_AVAILABLE = True
except ImportError:
    APPRISE_AVAILABLE = False

try:
    # Try relative imports first (when used as a package)
    from .email_threading import EmailThreadingStrategy, NotificationEventType
except ImportError:
    # Fall back to absolute imports (when imported directly from tests)
    from email_threading import EmailThreadingStrategy, NotificationEventType  # type: ignore[no-redef]


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

        if not APPRISE_AVAILABLE:
            self.logger.warning("Apprise not installed. Install with: pip install apprise")
            raise ImportError("Apprise is required for this handler")

        self.user_apprise_instances: Dict[str, apprise.Apprise] = {}
        self.user_notification_settings: Dict[str, Dict[str, bool]] = {}
        self.user_has_email: Dict[str, bool] = {}  # Track which users have email notifications

        # Initialize email threading strategy
        self.email_threading = EmailThreadingStrategy(domain=domain)

    def initialize_from_config(self, config: Dict[str, Any], config_loader: Any) -> None:
        """
        Initialize Apprise instances from configuration.

        Args:
            config: Configuration dictionary
            config_loader: ConfigLoader instance for URL processing
        """
        if not APPRISE_AVAILABLE:
            raise ImportError("Apprise is required for notification processing")

        global_config = config.get("global", {})
        users_config = config.get("users", {})

        for username, user_config in users_config.items():
            try:
                # Create Apprise instance
                apobj = apprise.Apprise()

                # Add URLs from config
                apprise_urls = user_config.get("apprise_urls", [])
                if isinstance(apprise_urls, str):
                    apprise_urls = [apprise_urls]

                has_email = False
                for url in apprise_urls:
                    # Process mailto URLs to use global mail server settings if available
                    processed_url = config_loader.process_apprise_url(url, global_config)
                    if not apobj.add(processed_url):
                        self.logger.warning(f"Failed to add Apprise URL for user {username}: {url}")
                    else:
                        # Check if this is an email notification
                        if EmailThreadingStrategy.is_email_notification(processed_url):
                            has_email = True

                if apobj:
                    self.user_apprise_instances[username] = apobj
                    self.user_has_email[username] = has_email
                    self.logger.debug(
                        f"Initialized Apprise for user: {username} (has_email: {has_email})"
                    )
                else:
                    self.logger.warning(f"No valid Apprise URLs for user: {username}")

                # Store notification settings
                notifications = user_config.get("notifications", {})
                self.user_notification_settings[username] = {
                    "entry_updates": notifications.get("entry_updates", True),
                    "own_entry_edits": notifications.get("own_entry_edits", True),
                    "entry_replies": notifications.get("entry_replies", True),
                    "new_entries": notifications.get("new_entries", True),
                    "reactions": notifications.get("reactions", True),
                    "document_replies": notifications.get("document_replies", True),
                }

            except Exception as e:
                self.logger.error(f"Error initializing Apprise for user {username}: {e}")

    def should_notify(self, username: Optional[str], notification_type: str) -> bool:
        """
        Check if user should be notified for this type of event.

        Args:
            username: Username to check
            notification_type: Type of notification (entry_updates, own_entry_edits,
                             entry_replies, new_entries, reactions, document_replies)

        Returns:
            True if user should be notified, False otherwise
        """
        if not username:
            return False

        if username not in self.user_apprise_instances:
            return False

        settings = self.user_notification_settings.get(username, {})
        return settings.get(notification_type, True)

    async def send_notification(
        self,
        username: Optional[str],
        title: str,
        body: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Send notification to user via Apprise.

        Args:
            username: Username to notify
            title: Notification title
            body: Notification body
            headers: Optional headers (used for email threading)
        """
        if not username or username not in self.user_apprise_instances:
            self.logger.debug(f"No notification endpoints for user: {username}")
            return

        try:
            apobj = self.user_apprise_instances[username]

            # Only include headers if user has email notifications
            # Apprise will ignore headers for non-email notification types
            if headers and self.user_has_email.get(username, False):
                # Send notification with headers for email threading
                # Note: headers parameter might not be supported in all apprise versions
                # Using type: ignore to suppress mypy warning
                result = apobj.notify(
                    body=body,
                    title=title,
                    headers=headers,  # type: ignore[call-arg]
                )
                self.logger.debug(f"Sent notification with email threading headers to {username}")
            else:
                # Send notification without headers
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
        """
        if not username or username not in self.user_apprise_instances:
            self.logger.debug(f"No notification endpoints for user: {username}")
            return

        # Check if user has email notifications
        has_email = self.user_has_email.get(username, False)

        # Generate appropriate subject based on notification type
        action_desc = f"by {action_by}" if action_by else None
        threaded_subject = self.email_threading.generate_subject(
            event_type=event_type,
            document_title=document_name,
            action_description=action_desc,
            is_email=has_email,
        )

        # Generate email headers if user has email notifications
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
        await self.send_notification(username, threaded_subject, body, headers)

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
                )
            else:
                # Fall back to simple notification
                await self.send_notification(username, title, body)

            notifications_sent.append(username)
