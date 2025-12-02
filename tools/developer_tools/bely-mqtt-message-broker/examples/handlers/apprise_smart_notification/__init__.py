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

Example usage:
    handler = AppriseSmartNotificationHandler(
        config_path="/path/to/config.yaml"
    )
"""

from .handler import AppriseSmartNotificationHandler

__all__ = ["AppriseSmartNotificationHandler"]
