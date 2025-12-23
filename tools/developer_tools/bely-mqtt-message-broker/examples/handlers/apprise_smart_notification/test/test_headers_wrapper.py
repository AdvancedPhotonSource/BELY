#!/usr/bin/env python3
"""
Comprehensive test suite for email headers wrapper functionality.

This module tests that email headers (Message-ID, References, In-Reply-To)
are properly passed through the wrapper to enable email threading.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import pytest

# Add parent directory to path for imports
handler_path = Path(__file__).parent.parent
if handler_path.exists():
    sys.path.insert(0, str(handler_path))

# Mock apprise at module level before importing apprise_email_wrapper
sys.modules['apprise'] = MagicMock()
sys.modules['apprise.plugins.email.base'] = MagicMock()

# Now we can safely import the module
import apprise_email_wrapper
apprise_email_wrapper.APPRISE_AVAILABLE = True


class TestEmailNotificationWrapper:
    """Test suite for EmailNotificationWrapper class."""

    @pytest.fixture
    def mock_apprise(self):
        """Create mock apprise module."""
        mock_apprise = MagicMock()
        mock_apprise.Apprise = MagicMock()

        # Create a mock NotifyEmail instance
        mock_email_instance = MagicMock()
        mock_email_instance.__class__.__name__ = "NotifyEmail"
        mock_email_instance.send = MagicMock(return_value=True)
        mock_email_instance.headers = {}

        mock_apprise.Apprise.instantiate = MagicMock(return_value=mock_email_instance)

        return mock_apprise, mock_email_instance

    def test_wrapper_initialization(self):
        """Test EmailNotificationWrapper initialization with various URLs."""
        # Test valid email URLs
        wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://user:pass@gmail.com")
        assert wrapper.scheme == "mailto"

        wrapper_secure = apprise_email_wrapper.EmailNotificationWrapper(
            "mailtos://user:pass@gmail.com"
        )
        assert wrapper_secure.scheme == "mailtos"

        # Test invalid URL
        with pytest.raises(ValueError, match="Not an email URL"):
            apprise_email_wrapper.EmailNotificationWrapper("slack://token")

    def test_send_with_headers(self, mock_apprise):
        """Test sending email with custom headers."""
        mock_apprise_module, mock_email_instance = mock_apprise

        # Patch the apprise module that's already imported
        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise_module):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Define custom headers for email threading
            headers = {
                "Message-ID": "<unique123@notifications.example.com>",
                "References": "<parent456@notifications.example.com>",
                "In-Reply-To": "<parent456@notifications.example.com>",
                "X-Thread-Topic": "Test Document",
            }

            # Send notification with headers
            result = wrapper.send_with_headers(
                title="Test Subject", body="Test Body", headers=headers
            )

            # Verify the email instance was created
            mock_apprise_module.Apprise.instantiate.assert_called_once_with(
                "mailto://test@example.com"
            )

            # Verify headers were set on the email instance
            assert mock_email_instance.headers == headers

            # Verify send was called with correct parameters
            mock_email_instance.send.assert_called_once_with(body="Test Body", title="Test Subject")

            assert result is True

    def test_send_without_headers(self, mock_apprise):
        """Test sending email without custom headers."""
        mock_apprise_module, mock_email_instance = mock_apprise

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise_module):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Send notification without headers
            result = wrapper.send_with_headers(title="Test Subject", body="Test Body", headers=None)

            # Verify headers attribute exists but is empty
            assert hasattr(mock_email_instance, "headers")
            assert mock_email_instance.headers == {}

            # Verify send was called
            mock_email_instance.send.assert_called_once()
            assert result is True

    def test_headers_override_existing(self, mock_apprise):
        """Test that new headers override any existing headers."""
        mock_apprise_module, mock_email_instance = mock_apprise

        # Pre-populate headers with existing values
        mock_email_instance.headers = {"Old-Header": "old-value"}

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise_module):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Send with new headers
            new_headers = {"Message-ID": "<new123@example.com>", "New-Header": "new-value"}

            wrapper.send_with_headers(title="Test", body="Test", headers=new_headers)

            # Verify old headers were cleared and new ones set
            assert mock_email_instance.headers == new_headers
            assert "Old-Header" not in mock_email_instance.headers

    def test_fallback_for_non_email(self, mock_apprise):
        """Test fallback to regular Apprise for non-email notifications."""
        mock_apprise_module, _ = mock_apprise

        # Make instantiate return None to simulate non-email URL
        mock_apprise_module.Apprise.instantiate.return_value = None

        # Create a mock Apprise instance for fallback
        mock_apprise_instance = MagicMock()
        mock_apprise_instance.add = MagicMock(return_value=True)
        mock_apprise_instance.notify = MagicMock(return_value=True)
        mock_apprise_module.Apprise.return_value = mock_apprise_instance

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise_module):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Send notification (should fall back to regular Apprise)
            result = wrapper.send_with_headers(
                title="Test", body="Test Body", headers={"Message-ID": "<test@example.com>"}
            )

            # Verify fallback was used
            mock_apprise_instance.add.assert_called_once_with("mailto://test@example.com")
            mock_apprise_instance.notify.assert_called_once_with(body="Test Body", title="Test")
            assert result is True

    def test_error_handling(self, mock_apprise):
        """Test error handling in send_with_headers."""
        mock_apprise_module, mock_email_instance = mock_apprise

        # Make send raise an exception
        mock_email_instance.send.side_effect = Exception("Network error")

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise_module):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Should return False on error
            with patch("builtins.print") as mock_print:
                result = wrapper.send_with_headers(
                    title="Test", body="Test", headers={"Message-ID": "<test@example.com>"}
                )

                assert result is False
                mock_print.assert_called_once()
                assert "Error sending email with headers" in str(mock_print.call_args)


class TestAppriseWithEmailHeaders:
    """Test suite for AppriseWithEmailHeaders class."""

    @pytest.fixture
    def mock_setup(self):
        """Setup mocks for testing."""
        mock_apprise = MagicMock()
        mock_apprise.Apprise = MagicMock()

        mock_apprise_instance = MagicMock()
        mock_apprise_instance.add = MagicMock(return_value=True)
        mock_apprise_instance.notify = MagicMock(return_value=True)
        mock_apprise.Apprise.return_value = mock_apprise_instance

        return mock_apprise, mock_apprise_instance

    def test_add_email_url(self, mock_setup):
        """Test adding email URLs creates wrapper instances."""
        mock_apprise, mock_apprise_instance = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()

            # Mock EmailNotificationWrapper
            with patch.object(
                apprise_email_wrapper, "EmailNotificationWrapper"
            ) as mock_wrapper_class:
                mock_email_wrapper = MagicMock()
                mock_wrapper_class.return_value = mock_email_wrapper

                # Add email URLs
                assert wrapper.add("mailto://user1@example.com")
                assert wrapper.add("mailtos://user2@example.com")

                # Verify wrappers were created
                assert mock_wrapper_class.call_count == 2
                mock_wrapper_class.assert_any_call("mailto://user1@example.com")
                mock_wrapper_class.assert_any_call("mailtos://user2@example.com")

                # Verify wrappers are stored
                assert len(wrapper.email_wrappers) == 2

    def test_add_non_email_url(self, mock_setup):
        """Test adding non-email URLs uses regular Apprise."""
        mock_apprise, mock_apprise_instance = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()
            wrapper.apprise = mock_apprise_instance

            # Add non-email URLs
            assert wrapper.add("slack://token")
            assert wrapper.add("discord://webhook")

            # Verify regular Apprise was used
            assert mock_apprise_instance.add.call_count == 2
            mock_apprise_instance.add.assert_any_call("slack://token")
            mock_apprise_instance.add.assert_any_call("discord://webhook")

            # Verify URLs are tracked
            assert len(wrapper.non_email_urls) == 2

    def test_notify_with_mixed_urls(self, mock_setup):
        """Test notify with both email and non-email URLs."""
        mock_apprise, mock_apprise_instance = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()
            wrapper.apprise = mock_apprise_instance

            # Create mock email wrappers
            mock_email_wrapper1 = MagicMock()
            mock_email_wrapper1.send_with_headers = MagicMock(return_value=True)

            mock_email_wrapper2 = MagicMock()
            mock_email_wrapper2.send_with_headers = MagicMock(return_value=True)

            # Manually add to simulate successful adds
            wrapper.email_wrappers = {
                "mailto://user1@example.com": mock_email_wrapper1,
                "mailto://user2@example.com": mock_email_wrapper2,
            }
            wrapper.non_email_urls = ["slack://token"]

            # Define headers for email threading
            headers = {
                "Message-ID": "<msg123@example.com>",
                "References": "<parent456@example.com>",
            }

            # Send notification
            result = wrapper.notify(body="Test notification", title="Test Title", headers=headers)

            # Verify email wrappers were called with headers
            mock_email_wrapper1.send_with_headers.assert_called_once_with(
                "Test Title", "Test notification", headers
            )
            mock_email_wrapper2.send_with_headers.assert_called_once_with(
                "Test Title", "Test notification", headers
            )

            # Verify regular Apprise was called for non-email
            mock_apprise_instance.notify.assert_called_once_with(
                body="Test notification", title="Test Title"
            )

            assert result is True

    def test_notify_without_headers(self, mock_setup):
        """Test notify without headers still works."""
        mock_apprise, mock_apprise_instance = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()

            # Create mock email wrapper
            mock_email_wrapper = MagicMock()
            mock_email_wrapper.send_with_headers = MagicMock(return_value=True)

            wrapper.email_wrappers = {"mailto://user@example.com": mock_email_wrapper}

            # Send notification without headers
            result = wrapper.notify(body="Test", title="Title")

            # Verify wrapper was called with None for headers
            mock_email_wrapper.send_with_headers.assert_called_once_with("Title", "Test", None)

            assert result is True

    def test_bool_operator(self, mock_setup):
        """Test __bool__ operator returns correct values."""
        mock_apprise, _ = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()

            # Empty wrapper should be False
            assert not wrapper

            # Add email wrapper
            wrapper.email_wrappers["mailto://test@example.com"] = MagicMock()
            assert wrapper

            # Clear and add non-email URL
            wrapper.email_wrappers.clear()
            wrapper.non_email_urls.append("slack://token")
            assert wrapper

    def test_partial_failure_handling(self, mock_setup):
        """Test handling when some notifications fail."""
        mock_apprise, mock_apprise_instance = mock_setup

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()

            # Create mock email wrappers with different results
            mock_email_wrapper1 = MagicMock()
            mock_email_wrapper1.send_with_headers = MagicMock(return_value=True)

            mock_email_wrapper2 = MagicMock()
            mock_email_wrapper2.send_with_headers = MagicMock(return_value=False)  # This one fails

            wrapper.email_wrappers = {
                "mailto://user1@example.com": mock_email_wrapper1,
                "mailto://user2@example.com": mock_email_wrapper2,
            }

            # Send notification
            result = wrapper.notify(
                body="Test", title="Title", headers={"Message-ID": "<test@example.com>"}
            )

            # Should return False if any notification fails
            assert result is False


class TestUtilityFunctions:
    """Test utility functions in the module."""

    def test_is_email_notification(self):
        """Test is_email_notification function."""
        # Test email URLs
        assert apprise_email_wrapper.is_email_notification("mailto://user@example.com")
        assert apprise_email_wrapper.is_email_notification("mailtos://secure@example.com")
        assert apprise_email_wrapper.is_email_notification(
            "mailto://user:pass@smtp.gmail.com:587"
        )

        # Test non-email URLs
        assert not apprise_email_wrapper.is_email_notification("slack://token")
        assert not apprise_email_wrapper.is_email_notification("discord://webhook/token")
        assert not apprise_email_wrapper.is_email_notification("https://example.com")
        assert not apprise_email_wrapper.is_email_notification("telegram://bot_token/chat_id")

        # Test invalid URLs
        assert not apprise_email_wrapper.is_email_notification("")
        assert not apprise_email_wrapper.is_email_notification("not a url")


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_email_threading_scenario(self):
        """Test a complete email threading scenario."""
        mock_apprise = MagicMock()

        # Create a mock email instance that tracks headers
        class MockEmailInstance:
            def __init__(self):
                self.headers = {}
                self.__class__.__name__ = "NotifyEmail"
                self.sent_messages = []

            def send(self, body, title):
                self.sent_messages.append(
                    {"title": title, "body": body, "headers": self.headers.copy()}
                )
                return True

        mock_email = MockEmailInstance()
        mock_apprise.Apprise.instantiate = MagicMock(return_value=mock_email)

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            # Create wrapper for email notification
            wrapper = apprise_email_wrapper.EmailNotificationWrapper(
                "mailto://notifications@example.com"
            )

            # Simulate a thread of messages

            # 1. Initial message
            initial_headers = {
                "Message-ID": "<doc123@notifications.example.com>",
                "X-Thread-Topic": "Project Status Report",
            }

            wrapper.send_with_headers(
                title="Project Status Report",
                body="Initial project status",
                headers=initial_headers,
            )

            # 2. First reply
            reply1_headers = {
                "Message-ID": "<doc123.reply1@notifications.example.com>",
                "References": "<doc123@notifications.example.com>",
                "In-Reply-To": "<doc123@notifications.example.com>",
                "X-Thread-Topic": "Project Status Report",
            }

            wrapper.send_with_headers(
                title="Re: Project Status Report",
                body="Update on task completion",
                headers=reply1_headers,
            )

            # 3. Second reply in thread
            reply2_headers = {
                "Message-ID": "<doc123.reply2@notifications.example.com>",
                "References": "<doc123@notifications.example.com> <doc123.reply1@notifications.example.com>",
                "In-Reply-To": "<doc123.reply1@notifications.example.com>",
                "X-Thread-Topic": "Project Status Report",
            }

            wrapper.send_with_headers(
                title="Re: Project Status Report",
                body="Additional comments",
                headers=reply2_headers,
            )

            # Verify all messages were sent with correct headers
            assert len(mock_email.sent_messages) == 3

            # Check first message
            assert (
                mock_email.sent_messages[0]["headers"]["Message-ID"]
                == "<doc123@notifications.example.com>"
            )
            assert "References" not in mock_email.sent_messages[0]["headers"]

            # Check first reply
            assert (
                mock_email.sent_messages[1]["headers"]["Message-ID"]
                == "<doc123.reply1@notifications.example.com>"
            )
            assert (
                mock_email.sent_messages[1]["headers"]["In-Reply-To"]
                == "<doc123@notifications.example.com>"
            )

            # Check second reply
            assert (
                mock_email.sent_messages[2]["headers"]["Message-ID"]
                == "<doc123.reply2@notifications.example.com>"
            )
            assert (
                mock_email.sent_messages[2]["headers"]["In-Reply-To"]
                == "<doc123.reply1@notifications.example.com>"
            )
            assert (
                "<doc123@notifications.example.com>"
                in mock_email.sent_messages[2]["headers"]["References"]
            )

    def test_multiple_recipients_with_headers(self):
        """Test sending to multiple email recipients with same headers."""
        mock_apprise = MagicMock()
        mock_apprise.Apprise = MagicMock()

        # Track all email instances created
        email_instances = []

        def create_email_instance(url):
            instance = MagicMock()
            instance.__class__.__name__ = "NotifyEmail"
            instance.headers = {}
            instance.send = MagicMock(return_value=True)
            instance.url = url  # Track which URL this is for
            email_instances.append(instance)
            return instance

        mock_apprise.Apprise.instantiate = create_email_instance

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            # Create wrapper with multiple email endpoints
            wrapper = apprise_email_wrapper.AppriseWithEmailHeaders()

            # Mock EmailNotificationWrapper to track calls
            with patch.object(
                apprise_email_wrapper, "EmailNotificationWrapper"
            ) as mock_wrapper_class:
                # Create individual mock wrappers
                mock_wrappers = []
                for i in range(3):
                    mock_wrapper = MagicMock()
                    mock_wrapper.send_with_headers = MagicMock(return_value=True)
                    mock_wrappers.append(mock_wrapper)

                # Configure mock to return different wrapper for each call
                mock_wrapper_class.side_effect = mock_wrappers

                # Add multiple email recipients
                wrapper.add("mailto://alice@example.com")
                wrapper.add("mailto://bob@example.com")
                wrapper.add("mailto://charlie@example.com")

                # Send notification with threading headers
                headers = {
                    "Message-ID": "<notification123@system.example.com>",
                    "X-Priority": "High",
                    "X-Thread-Topic": "System Alert",
                }

                result = wrapper.notify(
                    title="System Alert", body="Critical system update required", headers=headers
                )

                # Verify all wrappers were called with the same headers
                for mock_wrapper in mock_wrappers:
                    mock_wrapper.send_with_headers.assert_called_once_with(
                        "System Alert", "Critical system update required", headers
                    )

                assert result is True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_special_characters_in_headers(self):
        """Test headers with special characters."""
        mock_apprise = MagicMock()
        mock_email = MagicMock()
        mock_email.__class__.__name__ = "NotifyEmail"
        mock_email.headers = {}
        mock_email.send = MagicMock(return_value=True)
        mock_apprise.Apprise.instantiate = MagicMock(return_value=mock_email)

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Headers with special characters
            headers = {
                "Message-ID": "<msg-with-special-chars!@#$%@example.com>",
                "X-Custom-Header": "Value with spaces and 特殊文字",
                "References": "<ref1@example.com> <ref2@example.com> <ref3@example.com>",
            }

            result = wrapper.send_with_headers(title="Test", body="Test", headers=headers)

            # Headers should be set exactly as provided
            assert mock_email.headers == headers
            assert result is True

    def test_very_long_header_values(self):
        """Test headers with very long values."""
        mock_apprise = MagicMock()
        mock_email = MagicMock()
        mock_email.__class__.__name__ = "NotifyEmail"
        mock_email.headers = {}
        mock_email.send = MagicMock(return_value=True)
        mock_apprise.Apprise.instantiate = MagicMock(return_value=mock_email)

        with patch.object(apprise_email_wrapper, 'apprise', mock_apprise):
            wrapper = apprise_email_wrapper.EmailNotificationWrapper("mailto://test@example.com")

            # Create a very long References header (common in long email threads)
            long_references = " ".join([f"<msg{i}@example.com>" for i in range(50)])

            headers = {
                "Message-ID": "<current@example.com>",
                "References": long_references,
                "X-Long-Value": "A" * 1000,  # Very long header value
            }

            result = wrapper.send_with_headers(title="Test", body="Test", headers=headers)

            # Headers should be set regardless of length
            assert mock_email.headers == headers
            assert len(mock_email.headers["References"]) > 500
            assert len(mock_email.headers["X-Long-Value"]) == 1000
            assert result is True


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
