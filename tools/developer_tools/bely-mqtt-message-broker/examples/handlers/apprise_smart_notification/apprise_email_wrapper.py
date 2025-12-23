"""
Custom Apprise wrapper to support email headers for threading.

This module provides a custom implementation that allows passing email headers
to email notifications without modifying the Apprise library.
"""

from typing import Dict, Optional
from urllib.parse import urlparse

import apprise


class EmailNotificationWrapper:
    """
    Wrapper for email notifications that supports custom headers.

    This class provides a way to send email notifications with custom headers
    (like Message-ID and References for threading) without modifying Apprise.
    """

    def __init__(self, apprise_url: str):
        """
        Initialize the email wrapper with an Apprise URL.

        Args:
            apprise_url: The Apprise email URL (mailto:// or mailtos://)
        """
        self.apprise_url = apprise_url
        self._parse_email_config()

    def _parse_email_config(self) -> None:
        """Parse the email configuration from the Apprise URL."""
        # Parse the URL to extract components
        parsed = urlparse(self.apprise_url)

        # Check if this is an email notification
        if parsed.scheme not in ("mailto", "mailtos"):
            raise ValueError(f"Not an email URL: {self.apprise_url}")

        # Store the parsed components for later use
        self.scheme = parsed.scheme
        self.netloc = parsed.netloc
        self.path = parsed.path
        self.query = parsed.query
        self.parsed_url = parsed

    def send_with_headers(
        self, title: str, body: str, headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send an email notification with custom headers.

        Args:
            title: Email subject
            body: Email body
            headers: Optional dictionary of email headers

        Returns:
            True if notification was sent successfully, False otherwise
        """
        try:
            # Create a NotifyEmail instance directly
            email_instance = apprise.Apprise.instantiate(self.apprise_url)

            # Check if this is an email notification instance
            # We check for the class name since we can't import NotifyEmail directly
            if not (email_instance and email_instance.__class__.__name__ == "NotifyEmail"):
                # Fall back to regular Apprise if not an email notification
                apobj = apprise.Apprise()
                apobj.add(self.apprise_url)
                result = apobj.notify(body=body, title=title)
                return bool(result)

            # If we have headers, inject them into the email instance
            if headers:
                # Ensure the email instance has a headers attribute
                if not hasattr(email_instance, "headers"):
                    setattr(email_instance, "headers", {})  # type: ignore[attr-defined]
                # Clear any existing headers and set our custom ones
                getattr(email_instance, "headers").clear()  # type: ignore[attr-defined]
                getattr(email_instance, "headers").update(headers)  # type: ignore[attr-defined]
            else:
                # Ensure headers is at least an empty dict
                if not hasattr(email_instance, "headers"):
                    setattr(email_instance, "headers", {})  # type: ignore[attr-defined]

            # Send the notification using the email instance
            result = email_instance.send(body=body, title=title)
            return bool(result)

        except Exception as e:
            print(f"Error sending email with headers: {e}")
            return False


class AppriseWithEmailHeaders:
    """
    Extended Apprise wrapper that supports email headers for threading.

    This class wraps around Apprise to provide email header support while
    maintaining compatibility with other notification types.
    """

    def __init__(self):
        """Initialize the wrapper."""
        self.apprise = apprise.Apprise()
        self.email_wrappers = {}
        self.non_email_urls = []

    def add(self, url: str) -> bool:
        """
        Add a notification URL.

        Args:
            url: The Apprise notification URL

        Returns:
            True if URL was added successfully
        """
        # Check if this is an email URL
        if self._is_email_url(url):
            # Create an email wrapper for this URL
            try:
                wrapper = EmailNotificationWrapper(url)
                # Use URL as key for now (could be improved)
                self.email_wrappers[url] = wrapper
                return True
            except Exception:
                # If wrapper creation fails, fall back to regular Apprise
                result = self.apprise.add(url)
                return bool(result)
        else:
            # For non-email URLs, use regular Apprise
            self.non_email_urls.append(url)
            result = self.apprise.add(url)
            return bool(result)

    def _is_email_url(self, url: str) -> bool:
        """Check if a URL is an email notification URL."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("mailto", "mailtos")
        except Exception:
            return False

    def notify(self, body: str, title: str = "", headers: Optional[Dict[str, str]] = None) -> bool:
        """
        Send notifications with optional email headers support.

        Args:
            body: Notification body
            title: Notification title
            headers: Optional email headers (only used for email notifications)

        Returns:
            True if all notifications were sent successfully
        """
        success = True

        # Send to email endpoints with headers
        for url, wrapper in self.email_wrappers.items():
            result = wrapper.send_with_headers(title, body, headers)
            success = success and result

        # Send to non-email endpoints (without headers)
        if self.non_email_urls:
            result = self.apprise.notify(body=body, title=title)
            success = success and bool(result)

        return success

    def __bool__(self) -> bool:
        """Check if any notification endpoints are configured."""
        return bool(self.email_wrappers) or bool(self.non_email_urls)


def is_email_notification(url: str) -> bool:
    """
    Check if an Apprise URL is for email notifications.

    Args:
        url: The Apprise URL to check

    Returns:
        True if the URL is for email notifications
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("mailto", "mailtos")
    except Exception:
        return False
