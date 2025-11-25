"""
Smart Apprise Notification Handler for BELY MQTT Events.

This handler sends notifications for BELY events using Apprise, with configuration
from a YAML file. It supports:

1. Log Entry Updates - Notify when someone else updates a log entry
2. Log Entry Replies - Notify when someone else replies to a log entry
3. New Log Entries - Notify when someone else creates an entry in a document

Configuration is loaded from a YAML file with the following structure:

    global:
      mail_server: "smtp.gmail.com"
      mail_port: 587
      mail_username: "your-email@gmail.com"
      mail_password: "your-app-password"
      mail_from: "your-email@gmail.com"
      mail_from_name: "BELY Notifications"

    users:
      john_doe:
        apprise_urls:
          - "mailto://john@example.com"
          - "discord://webhook-id/webhook-token"
        notifications:
          entry_updates: true
          entry_replies: true
          new_entries: true
      
      jane_smith:
        apprise_urls:
          - "slack://token-a/token-b/token-c"
        notifications:
          entry_updates: true
          entry_replies: false
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
    ):
        """
        Initialize the handler.
        
        Args:
            config_path: Path to YAML configuration file
            api_client: Optional BELY API client
        
        Raises:
            ImportError: If apprise or yaml not installed
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        super().__init__(api_client=api_client)
        
        if not APPRISE_AVAILABLE:
            self.logger.warning(
                "Apprise not installed. Install with: pip install apprise"
            )
            raise ImportError("Apprise is required for this handler")
        
        if not YAML_AVAILABLE:
            self.logger.warning(
                "PyYAML not installed. Install with: pip install pyyaml"
            )
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
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f) or {}
            
            self.logger.info(f"Loaded configuration from {config_path}")
            
            # Validate config structure
            if 'users' not in self.config:
                self.logger.warning("No users configured in config file")
                self.config['users'] = {}
        
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    def _initialize_apprise_instances(self) -> None:
        """Initialize Apprise instances for each user."""
        global_config = self.config.get('global', {})
        users_config = self.config.get('users', {})
        
        for username, user_config in users_config.items():
            try:
                # Create Apprise instance
                apobj = apprise.Apprise()
                
                # Add URLs from config
                apprise_urls = user_config.get('apprise_urls', [])
                if isinstance(apprise_urls, str):
                    apprise_urls = [apprise_urls]
                
                for url in apprise_urls:
                    if not apobj.add(url):
                        self.logger.warning(
                            f"Failed to add Apprise URL for user {username}: {url}"
                        )
                
                if apobj:
                    self.user_apprise_instances[username] = apobj
                    self.logger.debug(f"Initialized Apprise for user: {username}")
                else:
                    self.logger.warning(f"No valid Apprise URLs for user: {username}")
                
                # Store notification settings
                notifications = user_config.get('notifications', {})
                self.user_notification_settings[username] = {
                    'entry_updates': notifications.get('entry_updates', True),
                    'entry_replies': notifications.get('entry_replies', True),
                    'new_entries': notifications.get('new_entries', True),
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
            if event.event_triggered_by_username == event.parent_log_document_info.created_by_username:
                return
            
            # Check if we should notify about new entries
            owner_username = event.parent_log_document_info.owner_username
            if not self._should_notify(owner_username, 'new_entries'):
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
            if not self._should_notify(creator_username, 'entry_updates'):
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
            if not self._should_notify(creator_username, 'entry_replies'):
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
            if not self._should_notify(creator_username, 'entry_replies'):
                return
            
            # Build notification
            title = f"Reply Updated on Your Log Entry in {event.parent_log_document_info.name}"
            body = self._format_reply_updated_body(event)
            
            # Send notification
            await self._send_notification(creator_username, title, body)
        
        except Exception as e:
            self.logger.error(f"Error processing log entry reply update: {e}", exc_info=True)

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
