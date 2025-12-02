"""
Smart Apprise Notification Handler for BELY MQTT Events.

This handler sends notifications for BELY events using Apprise, with configuration
from a YAML file. It supports:

1. Log Entry Updates - Notify when someone else updates a log entry
2. Log Entry Replies - Notify when someone else replies to a log entry
3. New Log Entries - Notify when someone else creates an entry in a document
4. Log Reactions - Notify when someone reacts to a log entry
5. Document Replies - Notify document owners when someone replies to any entry in their document
6. Own Entry Edits - Notify when someone else edits YOUR log entry (different from entry_updates)

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
          entry_updates: true       # Notify when any log entry is updated (typically for document owners)
          own_entry_edits: true     # Notify when YOUR log entries are edited by others
          entry_replies: true
          new_entries: true
          reactions: true
          document_replies: true  # Notify when anyone replies in owned documents

      jane_smith:
        apprise_urls:
          # Can mix different notification types
          - "mailto://jane@example.com"  # Uses global mail settings
          - "slack://token-a/token-b/token-c"
        notifications:
          entry_updates: true
          own_entry_edits: false   # Don't notify about edits to own entries
          entry_replies: false
          new_entries: true
          reactions: true
          document_replies: true

      # User with custom mail server (overrides global)
      custom_user:
        apprise_urls:
          # Full mailto URL with custom settings - ignores global
          - "mailto://custom_user:password@custom.server.com:465?to=user@example.com"
        notifications:
          entry_updates: true
          own_entry_edits: true
          entry_replies: true
          new_entries: true
          reactions: false
          document_replies: false  # Don't notify about replies in owned documents

Example usage:
    handler = ApprisSmartNotificationHandler(
        config_path="/path/to/config.yaml"
    )
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    LogEntryEventBase,
    LogReactionAddEvent,
    LogReactionDeleteEvent,
    LogReactionEventBase,
)
from bely_mqtt.config import GlobalConfig


class AppriseSmartNotificationHandler(MQTTHandler):
    """
    Smart notification handler using Apprise with YAML configuration.

    Sends notifications for:
    - Log entry updates by other users
    - Log entry replies by other users
    - New log entries in documents by other users
    - Reactions to log entries by other users
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
                    "own_entry_edits": notifications.get("own_entry_edits", True),
                    "entry_replies": notifications.get("entry_replies", True),
                    "new_entries": notifications.get("new_entries", True),
                    "reactions": notifications.get("reactions", True),
                    "document_replies": notifications.get("document_replies", True),
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
            await self._handle_add_event(event, is_reply=False)
        except Exception as e:
            self.logger.error(f"Error processing log entry add: {e}", exc_info=True)

    async def handle_log_entry_update(self, event: LogEntryUpdateEvent) -> None:
        """
        Handle log entry update events.

        Notify:
        1. The original creator if their entry is updated by someone else (own_entry_edits)
        2. Document owners about any updates

        Args:
            event: The log entry update event
        """
        try:
            await self._handle_update_event(event, is_reply=False)
        except Exception as e:
            self.logger.error(f"Error processing log entry update: {e}", exc_info=True)

    async def handle_log_entry_reply_add(self, event: LogEntryReplyAddEvent) -> None:
        """
        Handle log entry reply events.

        Notify:
        1. The original entry creator if someone else replies
        2. The document owner if someone replies to any entry in their document

        Args:
            event: The log entry reply add event
        """
        try:
            await self._handle_add_event(event, is_reply=True)
        except Exception as e:
            self.logger.error(f"Error processing log entry reply add: {e}", exc_info=True)

    async def handle_log_entry_reply_update(self, event: LogEntryReplyUpdateEvent) -> None:
        """
        Handle log entry reply update events.

        Notify:
        1. The original entry creator if someone else updates a reply on their entry (own_entry_edits)
        2. Document owners about any reply updates

        Args:
            event: The log entry reply update event
        """
        try:
            await self._handle_update_event(event, is_reply=True)
        except Exception as e:
            self.logger.error(f"Error processing log entry reply update: {e}", exc_info=True)

    async def _handle_add_event(
        self, event: Union[LogEntryAddEvent, LogEntryReplyAddEvent], is_reply: bool = False
    ) -> None:
        """
        Unified handler for add events (entry or reply adds).

        Args:
            event: The add event
            is_reply: Whether this is a reply add
        """
        notification_configs = []

        if is_reply:
            # Cast for type checking
            reply_event = event  # type: LogEntryReplyAddEvent

            # Notify the original entry creator
            creator_username = reply_event.parent_log_info.entered_by_username
            notification_configs.append(
                {
                    "username": creator_username,
                    "notification_type": "entry_replies",
                    "title": f"Reply to Your Log Entry in {reply_event.parent_log_document_info.name}",
                    "body": self._format_reply_added_body(reply_event),
                    "context": None,
                }
            )

            # Notify the document owner
            owner_username = reply_event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "document_replies",
                    "title": f"New Reply in Your Document: {reply_event.parent_log_document_info.name}",
                    "body": self._format_document_reply_body(reply_event),
                    "context": "document_owner",
                }
            )
        else:
            # Cast for type checking
            entry_event = event  # type: LogEntryAddEvent

            # Don't notify if the creator is also the document creator
            if (
                entry_event.event_triggered_by_username
                == entry_event.parent_log_document_info.created_by_username
            ):
                return

            # Notify document owner about new entry
            owner_username = entry_event.parent_log_document_info.owner_username
            notification_configs.append(
                {
                    "username": owner_username,
                    "notification_type": "new_entries",
                    "title": f"New Log Entry in {entry_event.parent_log_document_info.name}",
                    "body": self._format_entry_added_body(entry_event),
                    "context": None,
                }
            )

        await self._process_notifications(event, notification_configs)

    async def _handle_update_event(
        self, event: Union[LogEntryUpdateEvent, LogEntryReplyUpdateEvent], is_reply: bool = False
    ) -> None:
        """
        Unified handler for update events (entry or reply updates).

        Args:
            event: The update event
            is_reply: Whether this is a reply update
        """
        notification_configs = []

        if is_reply:
            # Cast for type checking
            reply_event = event  # type: LogEntryReplyUpdateEvent

            creator_username = reply_event.parent_log_info.entered_by_username
            own_edit_title = (
                f"Reply Updated on Your Log Entry in {reply_event.parent_log_document_info.name}"
            )
            own_edit_body = self._format_own_reply_updated_body(reply_event)
            owner_title = f"Reply Updated in {reply_event.parent_log_document_info.name}"
            owner_body = self._format_reply_updated_body(reply_event)
            owner_notification_type = "entry_replies"
        else:
            # Cast for type checking
            entry_event = event  # type: LogEntryUpdateEvent

            creator_username = entry_event.log_info.entered_by_username
            own_edit_title = (
                f"Your Log Entry Was Edited: {entry_event.parent_log_document_info.name}"
            )
            own_edit_body = self._format_own_entry_edited_body(entry_event)
            owner_title = f"Log Entry Updated: {entry_event.parent_log_document_info.name}"
            owner_body = self._format_entry_updated_body(entry_event)
            owner_notification_type = "entry_updates"

        # Config for notifying the original creator
        notification_configs.append(
            {
                "username": creator_username,
                "notification_type": "own_entry_edits",
                "title": own_edit_title,
                "body": own_edit_body,
                "context": "own_entry_edit" if not is_reply else "own_reply_update",
            }
        )

        # Config for notifying the document owner
        owner_username = event.parent_log_document_info.owner_username
        notification_configs.append(
            {
                "username": owner_username,
                "notification_type": owner_notification_type,
                "title": owner_title,
                "body": owner_body,
                "context": None,
            }
        )

        await self._process_notifications(event, notification_configs)

    async def _process_notifications(
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
            if not self._should_notify(username, notification_type):
                continue
            if event.event_triggered_by_username == username:
                continue

            title = config["title"]
            body = config["body"]

            await self._send_notification(username, title, body)
            notifications_sent.append(username)

    async def _handle_log_reaction_event(self, event: LogReactionEventBase) -> None:
        """
        Handle log reaction events (both add and delete).

        Notify the original entry creator if someone else reacts to or removes a reaction from their entry.

        Args:
            event: The log reaction event
        """
        try:
            # Don't notify the reactor (person who added/removed the reaction)
            if event.event_triggered_by_username == event.parent_log_info.entered_by_username:
                return

            # Check if we should notify about reactions
            creator_username = event.parent_log_info.entered_by_username
            if not self._should_notify(creator_username, "reactions"):
                return

            # Determine if this is an add or delete event
            is_delete = isinstance(event, LogReactionDeleteEvent)

            # Build notification
            if is_delete:
                title = (
                    f"Reaction Removed from Your Log Entry in {event.parent_log_document_info.name}"
                )
                body = self._format_reaction_deleted_body(event)
            else:
                title = f"Reaction to Your Log Entry in {event.parent_log_document_info.name}"
                body = self._format_reaction_added_body(event)

            # Send notification
            await self._send_notification(creator_username, title, body)

        except Exception as e:
            event_type = "delete" if isinstance(event, LogReactionDeleteEvent) else "add"
            self.logger.error(f"Error processing log reaction {event_type}: {e}", exc_info=True)

    async def handle_log_reaction_add(self, event: LogReactionAddEvent) -> None:
        """
        Handle log reaction add events.

        Notify the original entry creator if someone else reacts to their entry.

        Args:
            event: The log reaction add event
        """
        await self._handle_log_reaction_event(event)

    async def handle_log_reaction_delete(self, event: LogReactionDeleteEvent) -> None:
        """
        Handle log reaction delete events.

        Notify the original entry creator if someone removes a reaction from their entry.

        Args:
            event: The log reaction delete event
        """
        await self._handle_log_reaction_event(event)

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
            notification_type: Type of notification (entry_updates, own_entry_edits, entry_replies, new_entries, reactions, document_replies)

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

    def _generate_log_entry_link(self, document_id: int, log_id: int) -> str:
        """
        Generate a direct link to a log entry in BELY.

        Args:
            document_id: The document ID
            log_id: The log entry ID

        Returns:
            URL string to the log entry
        """
        if not self.bely_url:
            return ""

        # Remove trailing slash if present
        base_url = self.bely_url.rstrip("/")

        return f"{base_url}/views/item/view?id={document_id}&logId={log_id}"

    def _format_text_diff_pre(self, text_diff: str, max_height: str = "200px") -> str:
        """
        Format text diff in a styled pre box.

        Args:
            text_diff: The text difference to display
            max_height: Maximum height of the pre box (default: "200px")

        Returns:
            HTML formatted pre box with the text diff
        """
        return (
            f"<pre style='max-height: {max_height}; overflow-y: auto; "
            f"background-color: #f5f5f5; padding: 10px; border: 1px solid #ddd;'>"
            f"{text_diff}</pre>"
        )

    def _append_permalink_and_trigger(format_method):
        """Decorator to append permalink and trigger description to notification body."""

        def wrapper(self, event, notification_context=None):
            body = format_method(self, event)

            # Generate permalink if bely_url is available
            if self.bely_url:
                # Handle both LogEntryEventBase and LogReaction events
                if isinstance(event, LogEntryEventBase):
                    log_id = event.log_info.id
                    document_id = event.parent_log_document_info.id
                elif isinstance(event, LogReactionEventBase):
                    log_id = event.parent_log_info.id
                    document_id = event.parent_log_document_info.id
                else:
                    log_id = None
                    document_id = None

                if log_id and document_id:
                    link = self._generate_log_entry_link(document_id, log_id)
                    body += f"<br/><br/>View entry: {link}"

            # Add trigger description
            trigger_description = self._get_trigger_description(event, notification_context)
            body += f"<br/><br/><hr/><small><i>{trigger_description}</i></small>"

            return body

        return wrapper

    def _get_trigger_description(self, event, notification_context=None) -> str:
        """
        Get a description of why this notification was triggered.

        Args:
            event: The event that triggered the notification
            notification_context: Optional context about the notification type

        Returns:
            A human-readable description of the trigger
        """
        if isinstance(event, LogEntryAddEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"added a new log entry to the document '{event.parent_log_document_info.name}' "
                f"which you own. You have 'new_entries' notifications enabled."
            )
        elif isinstance(event, LogEntryUpdateEvent):
            # Check the notification context to determine the type
            if notification_context == "own_entry_edit":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"edited a log entry that you originally created in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'own_entry_edits' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a log entry in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'entry_updates' notifications enabled."
                )
        elif isinstance(event, LogEntryReplyAddEvent):
            # Check the notification context to determine the type
            if notification_context == "document_owner":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"added a reply to an entry in your document '{event.parent_log_document_info.name}'. "
                    f"You have 'document_replies' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"replied to your log entry in the document '{event.parent_log_document_info.name}'. "
                    f"You have 'entry_replies' notifications enabled."
                )
        elif isinstance(event, LogEntryReplyUpdateEvent):
            # Check the notification context to determine the type
            if notification_context == "own_reply_update":
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a reply on your log entry in the document "
                    f"'{event.parent_log_document_info.name}'. You have 'own_entry_edits' notifications enabled."
                )
            else:
                return (
                    f"This notification was sent because {event.event_triggered_by_username} "
                    f"updated a reply in the document '{event.parent_log_document_info.name}' "
                    f"which you own. You have 'entry_replies' notifications enabled."
                )
        elif isinstance(event, LogReactionAddEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"added a reaction to your log entry in the document "
                f"'{event.parent_log_document_info.name}'. You have 'reactions' notifications enabled."
            )
        elif isinstance(event, LogReactionDeleteEvent):
            return (
                f"This notification was sent because {event.event_triggered_by_username} "
                f"removed a reaction from your log entry in the document "
                f"'{event.parent_log_document_info.name}'. You have 'reactions' notifications enabled."
            )
        else:
            return "This notification was sent due to activity on your BELY content."

    @_append_permalink_and_trigger
    def _format_entry_added_body(self, event: LogEntryAddEvent) -> str:
        """Format notification body for new log entry."""
        return (
            f"New entry added to {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown: {self._format_text_diff_pre(event.text_diff)}"
        )

    @_append_permalink_and_trigger
    def _format_entry_updated_body(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for updated log entry (document owner notification)."""
        return (
            f"Entry updated in {event.parent_log_document_info.name}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"Original author: {event.log_info.entered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )

    def _format_own_entry_edited_body(self, event: LogEntryUpdateEvent) -> str:
        """Format notification body for when user's own entry is edited by someone else."""
        body = (
            f"Your entry was edited in {event.parent_log_document_info.name}<br/>"
            f"Edited by: {event.event_triggered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"Description: {event.description}<br/>"
            f"<br/>Entry markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )

        # Manually add permalink and trigger with context
        if self.bely_url:
            link = self._generate_log_entry_link(
                event.parent_log_document_info.id, event.log_info.id
            )
            body += f"<br/><br/>View entry: {link}"

        # Add trigger description with own_entry_edit context
        trigger_description = self._get_trigger_description(event, "own_entry_edit")
        body += f"<br/><br/><hr/><small><i>{trigger_description}</i></small>"

        return body

    @_append_permalink_and_trigger
    def _format_reply_added_body(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for new reply."""
        return (
            f"New reply to your entry in {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"<br/>Reply markdown: {self._format_text_diff_pre(event.text_diff)}"
        )

    @_append_permalink_and_trigger
    def _format_reply_updated_body(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for updated reply (document owner notification)."""
        return (
            f"Reply updated in {event.parent_log_document_info.name}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"On entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"<br/>Reply markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )

    def _format_own_reply_updated_body(self, event: LogEntryReplyUpdateEvent) -> str:
        """Format notification body for when a reply on user's own entry is updated by someone else."""
        body = (
            f"A reply on your entry was updated in {event.parent_log_document_info.name}<br/>"
            f"Updated by: {event.event_triggered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"<br/>Reply markdown changes: {self._format_text_diff_pre(event.text_diff)}"
        )

        # Manually add permalink and trigger with context
        if self.bely_url:
            link = self._generate_log_entry_link(
                event.parent_log_document_info.id, event.parent_log_info.id
            )
            body += f"<br/><br/>View entry: {link}"

        # Add trigger description with own_reply_update context
        trigger_description = self._get_trigger_description(event, "own_reply_update")
        body += f"<br/><br/><hr/><small><i>{trigger_description}</i></small>"

        return body

    def _format_document_reply_body(self, event: LogEntryReplyAddEvent) -> str:
        """Format notification body for document owner about new reply."""
        body = (
            f"New reply added in your document {event.parent_log_document_info.name}<br/>"
            f"Reply by: {event.event_triggered_by_username}<br/>"
            f"To entry by: {event.parent_log_info.entered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"<br/>Reply markdown: {self._format_text_diff_pre(event.text_diff)}"
        )

        # Manually add permalink and trigger with context
        if self.bely_url:
            link = self._generate_log_entry_link(
                event.parent_log_document_info.id, event.parent_log_info.id
            )
            body += f"<br/><br/>View entry: {link}"

        # Add trigger description with document owner context
        trigger_description = self._get_trigger_description(event, "document_owner")
        body += f"<br/><br/><hr/><small><i>{trigger_description}</i></small>"

        return body

    def _format_reaction_body(self, event: LogReactionEventBase, is_removed: bool) -> str:
        """Format notification body for reaction events."""
        reaction_info = event.log_reaction.reaction
        title = "Reaction removed from" if is_removed else "New reaction added to"

        return (
            f"{title} your entry in {event.parent_log_document_info.name}<br/>"
            f"By: {event.event_triggered_by_username}<br/>"
            f"Time: {event.event_timestamp}<br/>"
            f"Reaction: {reaction_info.emoji} {reaction_info.name}<br/>"
            f"Description: {event.description}"
        )

    @_append_permalink_and_trigger
    def _format_reaction_added_body(self, event: LogReactionAddEvent) -> str:
        """Format notification body for added reaction."""
        return self._format_reaction_body(event, is_removed=False)

    @_append_permalink_and_trigger
    def _format_reaction_deleted_body(self, event: LogReactionDeleteEvent) -> str:
        """Format notification body for deleted reaction."""
        return self._format_reaction_body(event, is_removed=True)
