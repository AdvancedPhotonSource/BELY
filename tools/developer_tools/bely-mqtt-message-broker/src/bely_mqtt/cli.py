"""
Command-line interface for BELY MQTT framework.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from bely_mqtt.config import ConfigManager
from bely_mqtt.mqtt_client import BelyMQTTClient
from bely_mqtt.plugin import BelyAPIClient, PluginManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option()
def cli() -> None:
    """BELY MQTT Framework - Pluggable MQTT handler for BELY events."""
    pass


@cli.command()
@click.option(
    "--broker-host",
    default="localhost",
    envvar="MQTT_BROKER_HOST",
    help="MQTT broker hostname or IP address.",
)
@click.option(
    "--broker-port",
    default=1883,
    type=int,
    envvar="MQTT_BROKER_PORT",
    help="MQTT broker port.",
)
@click.option(
    "--client-id",
    default="bely-mqtt-client",
    envvar="MQTT_CLIENT_ID",
    help="MQTT client ID.",
)
@click.option(
    "--username",
    default=None,
    envvar="MQTT_USERNAME",
    help="MQTT broker username.",
)
@click.option(
    "--password",
    default=None,
    envvar="MQTT_PASSWORD",
    help="MQTT broker password.",
)
@click.option(
    "--topic",
    "-t",
    multiple=True,
    default=["bely/#"],
    help="MQTT topic(s) to subscribe to. Can be specified multiple times.",
)
@click.option(
    "--handlers-dir",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    envvar="BELY_HANDLERS_DIR",
    help="Directory containing handler plugins.",
)
@click.option(
    "--api-url",
    default=None,
    envvar="BELY_API_URL",
    help="BELY API base URL for querying additional information.",
)
@click.option(
    "--api-key",
    default=None,
    envvar="BELY_API_KEY",
    help="BELY API key for authentication.",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    default="INFO",
    envvar="LOG_LEVEL",
    help="Logging level.",
)
@click.option(
    "--env-file",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    help="Path to .env file for environment variables.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    default=None,
    envvar="BELY_CONFIG",
    help="Path to configuration file for handlers (JSON format).",
)
def start(
    broker_host: str,
    broker_port: int,
    client_id: str,
    username: Optional[str],
    password: Optional[str],
    topic: tuple[str, ...],
    handlers_dir: Optional[Path],
    api_url: Optional[str],
    api_key: Optional[str],
    log_level: str,
    env_file: Optional[Path],
    config: Optional[Path],
) -> None:
    """Start the BELY MQTT client with registered handlers."""
    # Load environment variables from file if provided
    if env_file:
        load_dotenv(env_file)

    # Set logging level
    logging.getLogger().setLevel(log_level)

    logger.info("Starting BELY MQTT Framework")
    logger.info(f"Broker: {broker_host}:{broker_port}")
    logger.info(f"Topics: {', '.join(topic)}")

    # Initialize API client if URL is provided
    api_client = None
    if api_url:
        api_client = BelyAPIClient(base_url=api_url, api_key=api_key)
        logger.info(f"BELY API client initialized: {api_url}")

    # Initialize configuration manager
    config_manager = None
    if config:
        config_manager = ConfigManager()
        try:
            config_manager.load_from_file(config)
            logger.info(f"Loaded handler configuration from: {config}")
        except Exception as e:
            logger.error(f"Failed to load configuration file: {e}")
            sys.exit(1)

    # Initialize plugin manager
    plugin_manager = PluginManager(api_client=api_client, config_manager=config_manager)

    # Load handlers from directory if provided
    if handlers_dir:
        logger.info(f"Loading handlers from: {handlers_dir}")
        plugin_manager.load_handlers_from_directory(handlers_dir)

    if not plugin_manager.handlers:
        logger.warning("No handlers registered. Messages will be received but not processed.")

    # Initialize MQTT client
    mqtt_client = BelyMQTTClient(
        broker_host=broker_host,
        broker_port=broker_port,
        client_id=client_id,
        username=username,
        password=password,
        plugin_manager=plugin_manager,
    )

    # Subscribe to topics
    for t in topic:
        mqtt_client.subscribe(t)

    # Start the client
    try:
        mqtt_client.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--handlers-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
    help="Directory containing handler plugins.",
)
def list_handlers(handlers_dir: Path) -> None:
    """List all available handlers in a directory."""
    plugin_manager = PluginManager()
    plugin_manager.load_handlers_from_directory(handlers_dir)

    if not plugin_manager.handlers:
        click.echo("No handlers found.")
        return

    click.echo(f"Found {len(plugin_manager.handlers)} handler(s):\n")
    for handler in plugin_manager.handlers:
        click.echo(f"  {handler.__class__.__name__}")
        click.echo(f"    Topic Pattern: {handler.topic_pattern}")
        if handler.__doc__:
            click.echo(f"    Description: {handler.__doc__.strip()}")
        click.echo()


@cli.command()
def validate_config() -> None:
    """Validate the current configuration."""
    click.echo("Configuration validation not yet implemented.")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
