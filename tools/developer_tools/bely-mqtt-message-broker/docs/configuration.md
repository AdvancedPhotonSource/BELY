# Configuration

The BELY MQTT Framework can be configured through command-line options, environment variables, or configuration files.

## Command-Line Options

```bash
bely-mqtt start [OPTIONS]
```

### MQTT Options

- `--mqtt-host TEXT` - MQTT broker hostname (default: localhost)
- `--mqtt-port INTEGER` - MQTT broker port (default: 1883)
- `--mqtt-username TEXT` - MQTT username for authentication
- `--mqtt-password TEXT` - MQTT password for authentication
- `--mqtt-topic TEXT` - MQTT topic pattern to subscribe (default: bely/#)

### Handler Options

- `--handlers-dir PATH` - Directory containing handler files (default: ./handlers)
- `--handler-config PATH` - JSON configuration file for handlers

### API Options

- `--api-url TEXT` - BELY API base URL
- `--api-key TEXT` - BELY API authentication key

### Logging Options

- `--log-level TEXT` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `--log-file PATH` - Log to file instead of console

## Environment Variables

All command-line options can be set via environment variables:

```bash
export MQTT_HOST=broker.example.com
export MQTT_PORT=1883
export MQTT_USERNAME=myuser
export MQTT_PASSWORD=mypass
export BELY_API_URL=https://api.bely.dev
export BELY_API_KEY=your-api-key
export LOG_LEVEL=DEBUG
```

## Configuration File

Create a `.env` file in your project root:

```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=bely/#

# BELY API Configuration
BELY_API_URL=https://api.bely.dev
BELY_API_KEY=your-api-key-here

# Logging
LOG_LEVEL=INFO

# Handler Configuration
HANDLERS_DIR=./handlers
```

## Handler Configuration

Handlers can be configured via JSON file:

```json
{
  "handlers": [
    {
      "module": "notification_handler",
      "class": "NotificationHandler",
      "config": {
        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK",
        "enabled": true
      }
    }
  ]
}
```

Use with: `--handler-config config.json`

## SSL/TLS Configuration

For secure MQTT connections:

```bash
bely-mqtt start \
    --mqtt-host broker.example.com \
    --mqtt-port 8883 \
    --mqtt-tls \
    --mqtt-ca-cert /path/to/ca.crt \
    --mqtt-client-cert /path/to/client.crt \
    --mqtt-client-key /path/to/client.key
```

## Logging Configuration

### Log Levels

- `DEBUG` - Detailed information for debugging
- `INFO` - General informational messages
- `WARNING` - Warning messages for potentially harmful situations
- `ERROR` - Error messages for serious problems

### Log Format

The default log format includes:
- Timestamp
- Log level
- Handler name
- Message

Example:
```
2024-01-01 12:00:00 INFO [LogHandler] New log entry added: ID=123
```

## Production Configuration

For production deployments:

1. Use environment variables for sensitive data
2. Enable appropriate log level (INFO or WARNING)
3. Configure log rotation
4. Use SSL/TLS for MQTT connections
5. Set up monitoring and alerting

Example production command:

```bash
bely-mqtt start \
    --handlers-dir /opt/bely-handlers \
    --log-level INFO \
    --log-file /var/log/bely-mqtt/app.log \
    --mqtt-tls \
    --mqtt-ca-cert /etc/ssl/mqtt/ca.crt
```