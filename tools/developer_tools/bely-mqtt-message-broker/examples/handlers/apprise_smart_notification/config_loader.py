"""
Configuration loader for Apprise Smart Notification Handler.
"""

from logging import Logger
from pathlib import Path
from typing import Any, Dict

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class ConfigLoader:
    """Handles loading and processing of YAML configuration files."""

    def __init__(self, logger: Logger):
        """
        Initialize the config loader.

        Args:
            logger: Logger instance for output
        """
        self.logger = logger

        if not YAML_AVAILABLE:
            self.logger.warning("PyYAML not installed. Install with: pip install pyyaml")
            raise ImportError("PyYAML is required for this handler")

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If config file not found
            ValueError: If config is invalid
        """
        if not YAML_AVAILABLE:
            raise ImportError("PyYAML is required for configuration loading")

        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f) or {}

            self.logger.info(f"Loaded configuration from {config_path}")

            # Validate config structure
            if "users" not in config:
                self.logger.warning("No users configured in config file")
                config["users"] = {}

            # Log global configuration status
            self._log_global_config_status(config)

            return config

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config file: {e}")

    def _log_global_config_status(self, config: Dict[str, Any]) -> None:
        """
        Log the status of global configuration.

        Args:
            config: The loaded configuration dictionary
        """
        if "global" in config:
            global_config = config["global"]
            if "mail_server" in global_config:
                # Check if this is an authenticated or non-authenticated server
                has_auth = "mail_username" in global_config and "mail_password" in global_config
                auth_type = "authenticated" if has_auth else "non-authenticated"
                port = global_config.get("mail_port", 25 if not has_auth else 587)

                self.logger.info(
                    f"Global mail server configured ({auth_type}): "
                    f"{global_config.get('mail_server')}:{port}"
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

    def load_config_from_api(self, api_factory) -> Dict[str, Any]:
        """
        Load notification configurations from the BELY REST API.

        Args:
            api_factory: BelyApiFactory instance for accessing the BELY API

        Returns:
            Dictionary containing user configurations keyed by username,
            with per-endpoint structure

        Raises:
            Exception: If API call fails
        """
        nc_api = api_factory.getNotificationConfigurationApi()

        configs = nc_api.get_all()

        users: Dict[str, Any] = {}
        for config in configs:
            username = config.username
            if not username:
                continue

            if username not in users:
                users[username] = {"configs": []}

            # handler_preferences_by_name is already {str: bool} from the API
            notifications = config.handler_preferences_by_name or {}

            users[username]["configs"].append(
                {
                    "apprise_url": config.notification_endpoint,
                    "notifications": notifications,
                }
            )

        self.logger.info(
            f"Loaded {len(configs)} notification configurations " f"for {len(users)} users from API"
        )
        return {"users": users}

    def process_apprise_url(self, url: str, global_config: Dict[str, Any]) -> str:
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
