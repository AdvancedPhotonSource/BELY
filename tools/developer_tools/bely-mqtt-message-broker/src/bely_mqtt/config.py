"""
Configuration system for BELY MQTT handlers.

This module provides a configuration system that allows handlers to receive
configuration parameters when they are instantiated.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class GlobalConfig:
    """
    Global configuration shared across all handlers.

    Stores configuration parameters that will be available to all handlers.

    URL configuration fields:
        bely_url: The public-facing URL that end-users access in their browser.
                  Used to generate clickable links in notifications (log entry
                  permalinks, unsubscribe URLs). Must be reachable by notification
                  recipients.
        api_url:  The internal URL used by the broker for server-to-server API
                  calls to the BELY server. Defaults to bely_url if not set.
                  Set this to localhost or an internal hostname when the broker
                  runs on the same machine as BELY, so API calls bypass the
                  public network. Never used in user-facing notification content.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize global configuration.

        Args:
            config: Dictionary of global configuration parameters.
        """
        self.config = config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self.config.get(key, default)

    @property
    def bely_url(self) -> Optional[str]:
        """
        Get the public-facing BELY URL from configuration.

        This URL is used to generate user-facing links in notifications,
        such as log entry permalinks and unsubscribe URLs. It must be
        accessible by the end-users who receive those notifications.

        Returns:
            Public BELY URL if configured, None otherwise.
        """
        return self.config.get("bely_url")

    @property
    def api_url(self) -> Optional[str]:
        """
        Get the BELY API URL for internal server-to-server API calls.

        Used by BelyApiFactory for making API requests to the BELY server.
        Defaults to bely_url if not explicitly configured, which is correct
        when the broker accesses BELY through the same public URL.

        Set api_url explicitly when the broker runs on the same host as BELY
        and should use localhost or an internal hostname for API calls, while
        bely_url remains the public URL for notification links.

        Returns:
            API URL if configured, otherwise falls back to bely_url.
            Returns None if neither is configured.
        """
        return self.config.get("api_url") or self.bely_url

    def __repr__(self) -> str:
        """Return string representation."""
        return f"GlobalConfig({self.config})"


class HandlerConfig:
    """
    Configuration for a handler.

    Stores configuration parameters that will be passed to handler constructors.
    """

    def __init__(self, handler_name: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize handler configuration.

        Args:
            handler_name: Name of the handler class.
            config: Dictionary of configuration parameters.
        """
        self.handler_name = handler_name
        self.config = config or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key.
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        return self.config.get(key, default)

    def __repr__(self) -> str:
        """Return string representation."""
        return f"HandlerConfig({self.handler_name}, {self.config})"


class ConfigManager:
    """
    Manages configuration for handlers.

    Loads configuration from files or dictionaries and provides it to handlers.
    Supports both global configuration (shared across all handlers) and
    handler-specific configuration.
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.global_config: Optional[GlobalConfig] = None
        self.configs: Dict[str, HandlerConfig] = {}
        self.logger = logging.getLogger(__name__)

    def load_from_file(self, config_file: Path) -> None:
        """
        Load configuration from a YAML file.

        File format:
            global:
              shared_param: value
              another_param: value
              bely_url: https://bely.example.com  # public URL for notification links
              api_url: http://localhost:8080       # optional; internal API URL, defaults to bely_url

            handlers:
              AdvancedLoggingHandler:
                logging_dir: /var/log/bely
              MyHandler:
                param1: value1
                param2: value2
              AppriseSmartNotificationHandler:
                config_path: /path/to/apprise_config.yaml

        Args:
            config_file: Path to the YAML configuration file.

        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            yaml.YAMLError: If the file is not valid YAML.
        """
        config_file = Path(config_file)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_file) as f:
                data = yaml.safe_load(f)

            # Load global configuration if present
            if "global" in data:
                self.set_global_config(data["global"])
                self.logger.info(f"Loaded global configuration: {data['global']}")

            # Load handler-specific configurations
            handlers_config = data.get("handlers", {})
            for handler_name, config in handlers_config.items():
                self.set_config(handler_name, config)

            self.logger.info(f"Loaded configuration from {config_file}")
        except yaml.YAMLError as e:
            self.logger.error(f"Invalid YAML in configuration file: {e}")
            raise

    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Load configuration from a dictionary.

        Args:
            config_dict: Dictionary with optional "global" and "handlers" keys.
        """
        # Load global configuration if present
        if "global" in config_dict:
            self.set_global_config(config_dict["global"])

        # Load handler-specific configurations
        handlers_config = config_dict.get("handlers", {})
        for handler_name, config in handlers_config.items():
            self.set_config(handler_name, config)

    def set_global_config(self, config: Dict[str, Any]) -> None:
        """
        Set global configuration.

        Args:
            config: Global configuration dictionary.
        """
        self.global_config = GlobalConfig(config)
        self.logger.debug(f"Set global configuration: {config}")

    def get_global_config(self) -> Optional[GlobalConfig]:
        """
        Get global configuration.

        Returns:
            GlobalConfig if set, None otherwise.
        """
        return self.global_config

    def set_config(self, handler_name: str, config: Dict[str, Any]) -> None:
        """
        Set configuration for a handler.

        Args:
            handler_name: Name of the handler class.
            config: Configuration dictionary.
        """
        self.configs[handler_name] = HandlerConfig(handler_name, config)
        self.logger.debug(f"Set configuration for {handler_name}: {config}")

    def get_config(self, handler_name: str) -> Optional[HandlerConfig]:
        """
        Get configuration for a handler.

        Args:
            handler_name: Name of the handler class.

        Returns:
            HandlerConfig if found, None otherwise.
        """
        return self.configs.get(handler_name)

    def has_config(self, handler_name: str) -> bool:
        """
        Check if configuration exists for a handler.

        Args:
            handler_name: Name of the handler class.

        Returns:
            True if configuration exists.
        """
        return handler_name in self.configs

    def __repr__(self) -> str:
        """Return string representation."""
        return f"ConfigManager(global={self.global_config}, handlers={self.configs})"
