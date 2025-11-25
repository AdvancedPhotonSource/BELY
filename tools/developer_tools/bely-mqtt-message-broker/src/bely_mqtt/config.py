"""
Configuration system for BELY MQTT handlers.

This module provides a configuration system that allows handlers to receive
configuration parameters when they are instantiated.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


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
    """

    def __init__(self):
        """Initialize the configuration manager."""
        self.configs: Dict[str, HandlerConfig] = {}
        self.logger = logging.getLogger(__name__)

    def load_from_file(self, config_file: Path) -> None:
        """
        Load configuration from a JSON file.
        
        File format:
            {
              "handlers": {
                "AdvancedLoggingHandler": {
                  "logging_dir": "/var/log/bely"
                },
                "MyHandler": {
                  "param1": "value1",
                  "param2": "value2"
                }
              }
            }
        
        Args:
            config_file: Path to the configuration file.
        
        Raises:
            FileNotFoundError: If the configuration file doesn't exist.
            json.JSONDecodeError: If the file is not valid JSON.
        """
        config_file = Path(config_file)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        try:
            with open(config_file) as f:
                data = json.load(f)
            
            handlers_config = data.get("handlers", {})
            for handler_name, config in handlers_config.items():
                self.set_config(handler_name, config)
            
            self.logger.info(f"Loaded configuration from {config_file}")
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in configuration file: {e}")
            raise

    def load_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """
        Load configuration from a dictionary.
        
        Args:
            config_dict: Dictionary with "handlers" key containing handler configs.
        """
        handlers_config = config_dict.get("handlers", {})
        for handler_name, config in handlers_config.items():
            self.set_config(handler_name, config)

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
        return f"ConfigManager({self.configs})"
