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


class NotificationProcessor:
    """Handles processing and sending of notifications."""

    def __init__(self, logger: Logger):
        """
        Initialize the notification processor.

        Args:
            logger: Logger instance for output
        """

        self.logger = logger

        if not APPRISE_AVAILABLE:
            self.logger.warning("Apprise not installed. Install with: pip install apprise")
            raise ImportError("Apprise is required for this handler")

        self.user_apprise_instances: Dict[str, apprise.Apprise] = {}
        self.user_notification_settings: Dict[str, Dict[str, bool]] = {}

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

                for url in apprise_urls:
                    # Process mailto URLs to use global mail server settings if available
                    processed_url = config_loader.process_apprise_url(url, global_config)
                    if not apobj.add(processed_url):
                        self.logger.warning(f"Failed to add Apprise URL for user {username}: {url}")

                if apobj:
                    self.user_apprise_instances[username] = apobj
                    self.logger.debug(f"Initialized Apprise for user: {username}")
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
    ) -> None:
        """
        Send notification to user via Apprise.

        Args:
            username: Username to notify
            title: Notification title
            body: Notification body
        """
        if not username or username not in self.user_apprise_instances:
            self.logger.debug(f"No notification endpoints for user: {username}")
            return

        try:
            apobj = self.user_apprise_instances[username]

            # Send notification
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

            await self.send_notification(username, title, body)
            notifications_sent.append(username)
