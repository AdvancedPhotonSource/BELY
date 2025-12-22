"""
Email threading support for Apprise Smart Notification Handler.

This module provides email threading headers to ensure related notifications
are grouped together in email clients.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from urllib.parse import urlparse
import hashlib


class NotificationEventType(Enum):
    """Types of notification events for email threading"""

    DOCUMENT_CREATE = "document_create"
    DOCUMENT_UPDATE = "document_update"
    DOCUMENT_DELETE = "document_delete"
    ENTRY_ADD = "entry_add"
    ENTRY_UPDATE = "entry_update"
    ENTRY_DELETE = "entry_delete"
    ENTRY_REPLY = "entry_reply"
    REPLY_UPDATE = "reply_update"
    REPLY_DELETE = "reply_delete"
    REACTION_ADD = "reaction_add"
    REACTION_DELETE = "reaction_delete"

    @property
    def is_document_event(self) -> bool:
        """Check if this is a document-level event"""
        return self in {self.DOCUMENT_CREATE, self.DOCUMENT_UPDATE, self.DOCUMENT_DELETE}

    @property
    def is_entry_event(self) -> bool:
        """Check if this is an entry-level event (not a reply)"""
        return self in {self.ENTRY_ADD, self.ENTRY_UPDATE, self.ENTRY_DELETE}

    @property
    def is_reply_event(self) -> bool:
        """Check if this is a reply event"""
        return self in {self.ENTRY_REPLY, self.REPLY_UPDATE, self.REPLY_DELETE}

    @property
    def is_reaction_event(self) -> bool:
        """Check if this is a reaction event"""
        return self in {self.REACTION_ADD, self.REACTION_DELETE}


class EmailThreadingStrategy:
    """
    Email threading strategy that works with Apprise's custom headers.
    Only applies to email-type notifications.
    """

    # Email notification schemes in Apprise
    EMAIL_SCHEMES = {
        "mailto",
        "mailtos",  # Generic email
    }

    def __init__(self, domain: str = "notifications.bely.app"):
        """
        Initialize the email threading strategy.

        Args:
            domain: Domain to use in message IDs
        """
        self.domain = domain

    @staticmethod
    def is_email_notification(apprise_url: str) -> bool:
        """
        Check if an Apprise URL is for email notifications.

        Args:
            apprise_url: The Apprise notification URL

        Returns:
            True if this is an email notification URL
        """
        try:
            # Handle special case for mailto URLs that might not have ://
            if apprise_url.startswith("mailto:"):
                return True

            parsed = urlparse(apprise_url)
            scheme = parsed.scheme.lower()

            # Check if it's an email scheme
            return scheme in EmailThreadingStrategy.EMAIL_SCHEMES
        except Exception:
            return False

    def _generate_stable_id(self, identifier: str) -> str:
        """
        Generate a stable ID for threading purposes.
        Uses a hash to ensure consistency across notifications.

        Args:
            identifier: The identifier to hash

        Returns:
            A stable message ID
        """
        # Create a stable hash from the identifier
        hash_obj = hashlib.sha256(identifier.encode())
        short_hash = hash_obj.hexdigest()[:12]
        return f"<{identifier}.{short_hash}@{self.domain}>"

    def generate_document_thread_id(self, document_id: str) -> str:
        """
        Generate the root thread ID for a document.

        Args:
            document_id: The document ID

        Returns:
            Thread ID for the document
        """
        return self._generate_stable_id(f"doc.{document_id}")

    def generate_entry_thread_id(self, entry_id: str) -> str:
        """
        Generate a stable thread ID for an entry.

        Args:
            entry_id: The entry ID

        Returns:
            Thread ID for the entry
        """
        return self._generate_stable_id(f"entry.{entry_id}")

    def get_email_headers(
        self,
        event_type: NotificationEventType,
        document_id: str,
        document_name: str,
        entry_id: Optional[str] = None,
        parent_entry_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generate email-specific threading headers.

        Args:
            event_type: Type of notification event
            document_id: The document ID
            document_name: The document name (for Thread-Topic)
            entry_id: The log entry ID (if applicable)
            parent_entry_id: The parent entry ID (for replies)

        Returns:
            Dictionary of email threading headers
        """
        headers = {}

        # Thread-Topic helps some email clients group messages
        # Use document name for better readability
        safe_name = document_name.replace("\n", " ").replace("\r", " ")[:100]
        headers["Thread-Topic"] = f"Log: {safe_name}"

        # X-Thread-Id is a custom header for additional threading hint
        headers["X-Thread-Id"] = self.generate_document_thread_id(document_id)
        headers["X-Document-Id"] = document_id

        if event_type.is_document_event:
            # Document events start the thread
            # We'll use References to establish the thread root
            headers["References"] = self.generate_document_thread_id(document_id)

        elif event_type.is_entry_event:
            # Entry events reference the document
            if not entry_id:
                raise ValueError(f"entry_id required for {event_type.value}")

            headers["In-Reply-To"] = self.generate_document_thread_id(document_id)
            headers["References"] = self.generate_document_thread_id(document_id)
            headers["X-Entry-Id"] = entry_id

        elif event_type.is_reply_event:
            # Reply events reference both document and parent entry
            if not entry_id:
                raise ValueError(f"entry_id required for {event_type.value}")
            if not parent_entry_id:
                raise ValueError(f"parent_entry_id required for {event_type.value}")

            parent_ref = self.generate_entry_thread_id(parent_entry_id)
            doc_ref = self.generate_document_thread_id(document_id)

            headers["In-Reply-To"] = parent_ref
            headers["References"] = f"{doc_ref} {parent_ref}"
            headers["X-Entry-Id"] = entry_id
            headers["X-Parent-Entry-Id"] = parent_entry_id

        elif event_type.is_reaction_event:
            # Reaction events reference the entry they're reacting to
            if not entry_id:
                raise ValueError(f"entry_id required for {event_type.value}")

            entry_ref = self.generate_entry_thread_id(entry_id)
            doc_ref = self.generate_document_thread_id(document_id)

            headers["In-Reply-To"] = entry_ref
            headers["References"] = f"{doc_ref} {entry_ref}"
            headers["X-Entry-Id"] = entry_id

        # Add metadata for debugging
        headers["X-Notification-Time"] = datetime.now(timezone.utc).isoformat()
        headers["X-Event-Type"] = event_type.value

        return headers

    def generate_subject(
        self,
        event_type: NotificationEventType,
        document_title: str,
        action_description: Optional[str] = None,
        is_email: bool = True,
    ) -> str:
        """
        Generate subject lines - consistent for emails, descriptive for others.

        Args:
            event_type: Type of notification event
            document_title: Title of the document
            action_description: Optional description of the action
            is_email: Whether this is for an email notification

        Returns:
            Subject line for the notification
        """
        # Sanitize document title
        safe_title = document_title.replace("\n", " ").replace("\r", " ")

        if is_email:
            # Email subjects need consistency for threading
            base_subject = f"Log: {safe_title}"

            # Document creation starts a new thread without "Re:"
            if event_type == NotificationEventType.DOCUMENT_CREATE:
                return f"New {base_subject}"

            # All other events use "Re:" for threading
            prefix = "Re: "

            # Add event-specific indicators
            if event_type == NotificationEventType.DOCUMENT_UPDATE:
                suffix = " [Document Updated]"
            elif event_type == NotificationEventType.DOCUMENT_DELETE:
                suffix = " [Document Deleted]"
            elif event_type == NotificationEventType.ENTRY_UPDATE:
                suffix = " [Entry Updated]"
            elif event_type == NotificationEventType.ENTRY_DELETE:
                suffix = " [Entry Deleted]"
            elif event_type == NotificationEventType.REPLY_UPDATE:
                suffix = " [Reply Updated]"
            elif event_type == NotificationEventType.REPLY_DELETE:
                suffix = " [Reply Deleted]"
            elif event_type == NotificationEventType.REACTION_ADD:
                if action_description:
                    suffix = f" [{action_description}]"
                else:
                    suffix = " [Reaction Added]"
            elif event_type == NotificationEventType.REACTION_DELETE:
                if action_description:
                    suffix = f" [{action_description}]"
                else:
                    suffix = " [Reaction Removed]"
            elif action_description:
                suffix = f" - {action_description}"
            else:
                suffix = ""

            return f"{prefix}{base_subject}{suffix}"

        else:
            # Non-email notifications can have more descriptive subjects
            if event_type == NotificationEventType.DOCUMENT_CREATE:
                return f"📄 New Document: {safe_title}"
            elif event_type == NotificationEventType.DOCUMENT_UPDATE:
                return f"📝 Document Updated: {safe_title}"
            elif event_type == NotificationEventType.DOCUMENT_DELETE:
                return f"🗑️ Document Deleted: {safe_title}"
            elif event_type == NotificationEventType.ENTRY_ADD:
                desc = f" - {action_description}" if action_description else ""
                return f"➕ New Entry in {safe_title}{desc}"
            elif event_type == NotificationEventType.ENTRY_UPDATE:
                desc = f" - {action_description}" if action_description else ""
                return f"✏️ Entry Updated in {safe_title}{desc}"
            elif event_type == NotificationEventType.ENTRY_DELETE:
                desc = f" - {action_description}" if action_description else ""
                return f"🗑️ Entry Deleted in {safe_title}{desc}"
            elif event_type == NotificationEventType.ENTRY_REPLY:
                desc = f" - {action_description}" if action_description else ""
                return f"💬 Reply in {safe_title}{desc}"
            elif event_type == NotificationEventType.REPLY_UPDATE:
                desc = f" - {action_description}" if action_description else ""
                return f"✏️ Reply Updated in {safe_title}{desc}"
            elif event_type == NotificationEventType.REPLY_DELETE:
                desc = f" - {action_description}" if action_description else ""
                return f"🗑️ Reply Deleted in {safe_title}{desc}"
            elif event_type == NotificationEventType.REACTION_ADD:
                desc = f" - {action_description}" if action_description else ""
                return f"👍 Reaction in {safe_title}{desc}"
            elif event_type == NotificationEventType.REACTION_DELETE:
                desc = f" - {action_description}" if action_description else ""
                return f"👎 Reaction Removed in {safe_title}{desc}"

            return safe_title


def detect_event_type(
    event: Any,
    is_reply: bool = False,
    is_update: bool = False,
    is_delete: bool = False,
    is_reaction: bool = False,
    is_reaction_delete: bool = False,
) -> NotificationEventType:
    """
    Detect the notification event type from the event and context.

    Args:
        event: The event object
        is_reply: Whether this is a reply event
        is_update: Whether this is an update event
        is_delete: Whether this is a delete event
        is_reaction: Whether this is a reaction event
        is_reaction_delete: Whether this is a reaction delete event

    Returns:
        The appropriate NotificationEventType
    """
    if is_reaction:
        if is_reaction_delete:
            return NotificationEventType.REACTION_DELETE
        return NotificationEventType.REACTION_ADD

    if is_reply:
        if is_delete:
            return NotificationEventType.REPLY_DELETE
        elif is_update:
            return NotificationEventType.REPLY_UPDATE
        else:
            return NotificationEventType.ENTRY_REPLY

    # Regular entry events
    if is_delete:
        return NotificationEventType.ENTRY_DELETE
    elif is_update:
        return NotificationEventType.ENTRY_UPDATE
    else:
        return NotificationEventType.ENTRY_ADD
