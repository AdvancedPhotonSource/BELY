"""
Advanced logging handler that logs BELY events to files by topic.

This handler demonstrates how to create a handler that:
- Logs events to files organized by topic
- Automatically creates files for each subtopic
- Supports configurable logging directory
- Maintains separate loggers for each topic
- Accepts configuration from the framework

Environment Variables:
    BELY_LOG_DIR: Directory to store log files (default: current directory)

Configuration File:
    {
      "handlers": {
        "AdvancedLoggingHandler": {
          "logging_dir": "/var/log/bely"
        }
      }
    }

Usage:
    # With environment variable
    BELY_LOG_DIR=/var/log/bely bely-mqtt start --handlers-dir ./handlers
    
    # With configuration file
    bely-mqtt start --handlers-dir ./handlers --config config.json
    
    # With direct instantiation
    handler = AdvancedLoggingHandler(logging_dir="/var/log/bely")
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Optional

from bely_mqtt.models import MQTTMessage
from bely_mqtt.plugin import MQTTHandler


class AdvancedLoggingHandler(MQTTHandler):
    """
    Advanced handler that logs BELY events to files by topic.
    
    This handler subscribes to all BELY topics and logs each event to a
    separate file based on the topic. Files are automatically created in
    the specified logging directory.
    
    Example:
        handler = AdvancedLoggingHandler(logging_dir="/var/log/bely")
        
        Messages on "bely/logEntry/Add" are logged to:
        /var/log/bely/logEntry/Add.log
        
        Messages on "bely/logEntryReply/Update" are logged to:
        /var/log/bely/logEntryReply/Update.log
    """

    def __init__(
        self,
        logging_dir: Optional[str] = None,
        api_client: Optional[object] = None,
    ):
        """
        Initialize the advanced logging handler.
        
        Args:
            logging_dir: Directory to store log files. If None, uses BELY_LOG_DIR
                        environment variable or current directory.
                        Directory is created if it doesn't exist.
            api_client: Optional BELY API client (for compatibility with handler system).
        
        Examples:
            # Use environment variable
            BELY_LOG_DIR=/var/log/bely bely-mqtt start --handlers-dir ./handlers
            
            # Use direct instantiation
            handler = AdvancedLoggingHandler(logging_dir="/var/log/bely")
            
            # Use configuration file
            # config.json:
            # {
            #   "handlers": {
            #     "AdvancedLoggingHandler": {
            #       "logging_dir": "/var/log/bely"
            #     }
            #   }
            # }
            # bely-mqtt start --handlers-dir ./handlers --config config.json
            
            # Use default (current directory)
            handler = AdvancedLoggingHandler()
        """
        super().__init__(api_client=api_client)
        
        # Set up logging directory
        # Priority: parameter > environment variable > current directory
        if logging_dir is None:
            logging_dir = os.getenv("BELY_LOG_DIR", ".")
        
        self.logging_dir = Path(logging_dir)
        self.logging_dir.mkdir(parents=True, exist_ok=True)
        
        # Dictionary to store loggers for each topic
        self._topic_loggers: Dict[str, logging.Logger] = {}
        
        self.logger.info(f"AdvancedLoggingHandler initialized with directory: {self.logging_dir}")

    # Uses default topic_pattern "bely/#" - no need to override
    # This handler will receive all BELY events

    def _get_logger_for_topic(self, topic: str) -> logging.Logger:
        """
        Get or create a logger for the given topic.
        
        Creates a new logger if one doesn't exist for this topic.
        The logger writes to a file named after the topic path.
        
        Args:
            topic: The MQTT topic (e.g., "bely/logEntry/Add")
            
        Returns:
            A configured logger for the topic.
        """
        # Return cached logger if it exists
        if topic in self._topic_loggers:
            return self._topic_loggers[topic]
        
        # Create logger name from topic
        logger_name = f"bely_mqtt.topic.{topic.replace('/', '.')}"
        topic_logger = logging.getLogger(logger_name)
        
        # Set up file handler for this topic
        try:
            # Create subdirectories based on topic structure
            # e.g., "bely/logEntry/Add" -> "bely/logEntry/Add.log"
            topic_parts = topic.split("/")
            log_dir = self.logging_dir / Path(*topic_parts[:-1])
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"{topic_parts[-1]}.log"
            
            # Create file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            
            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            topic_logger.addHandler(file_handler)
            topic_logger.setLevel(logging.DEBUG)
            
            # Prevent propagation to root logger
            topic_logger.propagate = False
            
            self.logger.debug(f"Created logger for topic: {topic} -> {log_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to create logger for topic {topic}: {e}")
            raise
        
        # Cache the logger
        self._topic_loggers[topic] = topic_logger
        return topic_logger

    async def handle(self, message: MQTTMessage) -> None:
        """
        Log the incoming message to a file based on its topic.
        
        Args:
            message: The MQTT message to log.
        """
        try:
            # Get logger for this topic
            topic_logger = self._get_logger_for_topic(message.topic)
            
            # Log the event
            topic_logger.info(f"Event received on topic: {message.topic}")
            topic_logger.debug(f"Payload: {json.dumps(message.payload, indent=2)}")
            
            # Also log to main logger
            self.logger.debug(f"Logged event from {message.topic}")
            
        except Exception as e:
            self.logger.error(f"Error logging message from {message.topic}: {e}", exc_info=True)

    def get_log_file_for_topic(self, topic: str) -> Path:
        """
        Get the log file path for a given topic.
        
        Args:
            topic: The MQTT topic.
            
        Returns:
            Path to the log file for this topic.
        """
        topic_parts = topic.split("/")
        log_dir = self.logging_dir / Path(*topic_parts[:-1])
        return log_dir / f"{topic_parts[-1]}.log"

    def get_all_log_files(self) -> list[Path]:
        """
        Get all log files created by this handler.
        
        Returns:
            List of all log file paths.
        """
        return list(self.logging_dir.rglob("*.log"))
