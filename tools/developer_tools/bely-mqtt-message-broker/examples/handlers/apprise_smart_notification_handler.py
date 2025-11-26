"""
Smart Apprise Notification Handler for BELY MQTT Events.

This handler sends notifications for BELY events using Apprise, with configuration
from a YAML file. It supports:

1. Log Entry Updates - Notify when someone else updates a log entry
2. Log Entry Replies - Notify when someone else replies to a log entry
3. New Log Entries - Notify when someone else creates an entry in a document

Configuration is loaded from a YAML file with the following structure:

    global:
      # Global mail server settings - automatically applied to simple mailto:// URLs

      # Example 1: Authenticated mail server (Gmail, Office365, etc.)
      mail_server: "smtp.gmail.com"
      mail_port: 587
      mail_username: "your-email@gmail.com"  # Optional - only for authenticated servers
      mail_password: "your-app-password"     # Optional - only for authenticated servers
      mail_from: "your-email@gmail.com"
      mail_from_name: "BELY Notifications"

      # Example 2: Non-authenticated mail server (internal/relay servers)
      # mail_server: "mail.com"
      # mail_port: 25                        # Often port 25 for non-authenticated
      # mail_from: "bely@aps.anl.gov"
      # mail_from_name: "BELY Notifications"
      # No username/password needed for non-authenticated servers

    users:
      john_doe:
        apprise_urls:
          # Simple mailto URL - will use global mail settings if available
          - "mailto://john@example.com"
          # Other notification services
          - "discord://webhook-id/webhook-token"
        notifications:
          entry_updates: true
          entry_replies: true
          new_entries: true

      jane_smith:
        apprise_urls:
          # Can mix different notification types
          - "mailto://jane@example.com"  # Uses global mail settings
          - "slack://token-a/token-b/token-c"
        notifications:
          entry_updates: true
          entry_replies: false
          new_entries: true

      # User with custom mail server (overrides global)
      custom_user:
        apprise_urls:
          # Full mailto URL with custom settings - ignores global
          - "mailto://custom_user:password@custom.server.com:465?to=user@example.com"
        notifications:
          entry_updates: true
          entry_replies: true
          new_entries: true

Example usage:
    handler = ApprisSmartNotificationHandler(
        config_path="/path/to/config.yaml"
    )
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import apprise

    APPRISE_AVAILABLE = True
except ImportError:
    APPRISE_AVAILABLE = False

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from bely_mqtt import (
    MQTTHandler,
    LogEntryAddEvent,
    LogEntryUpdateEvent,
    LogEntryReplyAddEvent,
    LogEntryReplyUpdateEvent,
)
from bely_mqtt.config import GlobalConfig


class AppriseSmartNotificationHandler(MQTTHandler):
    """
    Smart notification handler using Apprise with YAML configuration.

    Sends notifications for:
    - Log entry updates by other users
    - Log entry replies by other users
    - New log entries in documents by other users
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        api_client: Optional[Any] = None,
        global_config: Optional[GlobalConfig] = None,
    ):
        """
        Initialize the handler.

        Args:
            config_path: Path to YAML configuration file
            api_client: Optional BELY API client
            global_config: Optional global configuration containing bely_url and other settings

        Raises:
            ImportError: If apprise or yaml not installed
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        super().__init__(api_client=api_client)
        self.bely_url = global_config.bely_url

        if not APPRISE_AVAILABLE:
            self.logger.warning("Apprise not installed. Install with: pip install apprise")
            raise ImportError("Apprise is required for this handler")

        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not installed. Install with: pip install pyyaml")
            raise ImportError("PyYAML is required for this handler")

        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.user_apprise_instances: Dict[str, apprise.Apprise] = {}
        self.user_notification_settings: Dict[str, Dict[str, bool]] = {}

        if config_path:
            self._load_config(config_path)
            self._initialize_apprise_instances()
        else:
            self.logger.warning("No config path provided. Handler will not send notifications.")

    def _load_config(self, config_path: str) -> None:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_file, "r") as f:
                self.config = yaml.safe_load(f) or {}

            self.logger.info(f"Loaded configuration from {config_path}")

            # Validate config structure
            if "users" not in self.config:
                self.logger.warning("No users configured in config file")
                self.config["users"] = {}

            # Log global configuration status
            if "global" in self.config:
                global_config = self.config["global"]
                if "mail_server" in global_config:
                    # Check if this is an authenticated or non-authenticated server
                    has_auth = "mail_username" in global_config and "mail_password" in global_config
                    auth_type = "authenticated" if has_auth else "non-authenticated"
                    self.logger.info(
                        f"Global mail server configured ({auth_type}): "
                        f"{global_config.get('mail_server')}:{global_config.get('mail_port', 25 if not has_auth else 587)}"
                    )

                    # Warn if partial authentication (only username or only password)
                    if ("mail_username" in global_config) != ("mail_password" in global_config):
                        self.logger.warning(
                            "Partial authentication detected. Both mail_username and mail_password "
                            "are required for authenticated servers."
                        )
                else:
                    self.logger.info(
                        "No global mail server configured. Simple mailto:// URLs will need full configuration."
                    )
            else:
                self.logger.info(
                    "No global configuration found. Simple mailto:// URLs will need full configuration."
                )

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    def _initialize_apprise_instances(self) -> None:
        """Initialize Apprise instances for each user."""
        global_config = self.config.get("global", {})
        users_config = self.config.get("users", {})

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
                    processed_url = self._process_apprise_url(url, global_config)
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
                    "entry_replies": notifications.get("entry_replies", True),
                    "new_entries": notifications.get("new_entries", True),
                }

            except Exception as e:
                self.logger.error(f"Error initializing Apprise for user {username}: {e}")

    async def handle_log_entry_add(self, event: LogEntryAddEvent) -> None:
        """
        Handle new log entry events.

        Notify document owner/creators if entry is created by someone else.

        Args:
            event: The log entry add event
        """
        try:
            # Don't notify the creator
            if (
                event.event_triggered_by_username
                == event.parent_log_document_info.created_by_username
            ):
                return

            # Check if we should notify about new entries
            owner_username = event.parent_log_document_info.owner_username
            if not self._should_notify(owner_username, "new_entries"):
                return

            # Build notification
            title = f"New Log Entry in {event.parent_log_document_info.name}"
            body = self._format_entry_added_body(event)

            # Send notification
            await self._send_notification(owner_username, title, body)

        except Exception as e:
            self.logger.error(f"Error processing log entry add: {e}", exc_info=True)

    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        """
        Handle log entry update events.

        Notify the original creator if entry is updated by someone else.

        Args:
            event: The log entry update event
        """
        try:
            # Don't notify the updater
            if event.event_triggered_by_username == event.log_info.entered_by_username:
                return

            # Check if we should notify about updates
            creator_username = event.log_info.entered_by_username
            if not self._should_notify(creator_username, "entry_updates"):
                return

            # Build notification
            title = f"Log Entry Updated: {event.parent_log_document_info.name}"
            body = self._format_entry_updated_body(event)

            # Send notification
            await self._send_notification(creator_username, title, body)

        except Exception as e:
            self.logger.error(f"Error processing log entry update: {e}", exc_info=True)

    async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        """
        Handle log entry reply events.

        Notify the original entry creator if someone else replies.

        Args:
            event: The log entry reply add event
        """
        try:
            # Don't notify the replier
            if event.event_triggered_by_username == event.parent_log_info.entered_by_username:
                return

            # Check if we should notify about replies
            creator_username = event.parent_log_info.entered_by_username
            if not self._should_notify(creator_username, "entry_replies"):
                return

            # Build notification
            title = f"Reply to Your Log Entry in {event.parent_log_document_info.name}"
            body = self._format_reply_added_body(event)

            # Send notification
            await self._send_notification(creator_username, title, body)

        except Exception as e:
            self.logger.error(f"Error processing log entry reply add: {e}", exc_info=True)

    async def handle_log_entry_reply_update(self, event: LogEntryReplyUpdateEvent) -> None:
        """
        Handle log entry reply update events.

        Notify the original entry creator if someone else updates a reply.

        Args:
            event: The log entry reply update event
        """
        try:
            # Don't notify the updater
            if event.event_triggered_by_username == event.parent_log_info.entered_by_username:
                return

            # Check if we should notify about replies
            creator_username = event.parent_log_info.entered_by_username
            if not self._should_notify(creator_username, "entry_replies"):
                return

            # Build notification
            title = f"Reply Updated on Your Log Entry in {event.parent_log_document_info.name}"
            body = self._format_reply_updated_body(event)

            # Send notification
            await self._send_notification(creator_username, title, body)

        except Exception as e:
            self.logger.error(f"Error processing log entry reply update: {e}", exc_info=True)

    def _process_apprise_url(self, url: str, global_config: Dict[str, Any]) -> str:
        """
        Process Apprise URL to incorporate global settings.

        For mailto:// URLs, this will use global mail server settings if available.
        Supports both authenticated and non-authenticated mail servers.

        Args:
            url: Original Apprise URL
            global_config: Global configuration dictionary

        Returns:
            Processed URL with global settings applied
        """
        # Check if this is a simple mailto URL that needs global settings
        if url.startswith("mailto://") and global_config and "mail_server" in global_config:
            # Extract the email address from the simple mailto URL
            email_part = url.replace("mailto://", "")

            # Get mail server settings
            mail_server = global_config.get("mail_server")
            mail_from = global_config.get("mail_from", "noreply@localhost")
            mail_from_name = global_config.get("mail_from_name", "BELY Notifications")

            # Check if this is an authenticated or non-authenticated server
            has_auth = "mail_username" in global_config and "mail_password" in global_config

            if has_auth:
                # Authenticated mail server (Gmail, Office365, etc.)
                mail_port = global_config.get("mail_port", 587)
                mail_username = global_config.get("mail_username")
                mail_password = global_config.get("mail_password")

                # If mail_from not specified, use username
                if "mail_from" not in global_config:
                    mail_from = mail_username

                # Construct the full Apprise mailto URL with authentication
                # Format: mailto://username:password@server:port?to=recipient&from=sender&name=sender_name
                processed_url = (
                    f"mailto://{mail_username}:{mail_password}@{mail_server}:{mail_port}"
                    f"?to={email_part}&from={mail_from}&name={mail_from_name}"
                )

                self.logger.debug(f"Processed mailto URL with authentication for: {email_part}")
            else:
                # Non-authenticated mail server (internal relay servers)
                mail_port = global_config.get("mail_port", 25)  # Default to port 25 for non-auth

                # Construct the Apprise mailto URL without authentication
                # Format: mailto://server:port?to=recipient&from=sender&name=sender_name
                processed_url = (
                    f"mailto://{mail_server}:{mail_port}"
                    f"?to={email_part}&from={mail_from}&name={mail_from_name}"
                )

                self.logger.debug(f"Processed mailto URL without authentication for: {email_part}")

            return processed_url

        # Return original URL if not a mailto or no global config
        return url

    def _should_notify(self, username: Optional[str], notification_type: str) -> bool:
        """
        Check if user should be notified for this type of event.

        Args:
            username: Username to check
            notification_type: Type of notification (entry_updates, entry_replies, new_entries)

        Returns:
            True if user should be notified, False otherwise
        """
        if not username:
            return False

        if username not in self.user_apprise_instances:
            return False

        settings = self.user_notification_settings.get(username, {})
        return settings.get(notification_type, True)

    async def _send_notification(
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

    def _format_entry_added_body(self, event: LogEntryAddEvent) -> str:
        """Format notification body for new log entry."""
        return (
            f"New entry added to {event.parent_log_document_info.name}\n"
            f"By: {event.event_triggered_by_username}\n"
            f"Time: {event.event_timestamp}\n"
            f"Description: {event.description}"
        )

    def _format_entry_updated_body(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for updated log entry."""
        return (
            f"Entry updated in {event.parent_log_document_info.name}\n"
            f"Updated by: {event.event_triggered_by_username}\n"
            f"Time: {event.event_timestamp}\n"
            f"Description: {event.description}"
        )

    def _format_reply_added_body(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for new reply."""
        return (
            f"New reply to your entry in {event.parent_log_document_info.name}\n"
            f"By: {event.event_triggered_by_username}\n"
            f"Time: {event.event_timestamp}\n"
            f"Reply: {event.text_diff[:100]}..."
        )

    def _format_reply_updated_body(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for updated reply."""
        return (
            f"Reply updated on your entry in {event.parent_log_document_info.name}\n"
            f"Updated by: {event.event_triggered_by_username}\n"
            f"Time: {event.event_timestamp}\n"
            f"Reply: {event.text_diff[:100]}..."
        )
