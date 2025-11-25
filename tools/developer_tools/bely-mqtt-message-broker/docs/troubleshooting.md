# Troubleshooting Guide

## Common Issues

### MQTT Connection Issues

**Problem:** Cannot connect to MQTT broker

**Solutions:**
1. Check broker is running: `mosquitto_sub -t '#' -v`
2. Verify connection details:
   ```bash
   bely-mqtt start --mqtt-host localhost --mqtt-port 1883
   ```
3. Check firewall rules
4. Try without authentication first

### Handler Not Loading

**Problem:** Handler file exists but not being loaded

**Solutions:**
1. Check file naming: Must be `*.py` in handlers directory
2. Verify class inherits from `MQTTHandler`
3. Check for syntax errors: `python -m py_compile handlers/my_handler.py`
4. Enable debug logging: `--log-level DEBUG`

### Handler Not Receiving Messages

**Problem:** Handler loads but doesn't receive messages

**Solutions:**
1. Verify topic pattern matches:
   ```python
   # Check exact topic
   @property
   def topic_pattern(self) -> str:
       return "bely/logEntry/Add"  # Must match exactly
   ```
2. Test with wildcards:
   ```python
   return "bely/#"  # Receives all BELY messages
   ```
3. Check MQTT subscription: Look for "Subscribed to topic" in logs

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'bely_mqtt'`

**Solutions:**
1. Install the framework:
   ```bash
   pip install bely-mqtt-framework
   ```
2. Check virtual environment is activated
3. Verify installation:
   ```bash
   pip show bely-mqtt-framework
   ```

### Async Errors

**Problem:** `RuntimeWarning: coroutine 'handle' was never awaited`

**Solutions:**
1. Ensure handle method is async:
   ```python
   async def handle(self, message: MQTTMessage) -> None:
       # Your code here
   ```
2. Use `await` for async calls:
   ```python
   await some_async_function()
   ```

## Debug Mode

Enable debug logging to see detailed information:

```bash
bely-mqtt start --handlers-dir ./handlers --log-level DEBUG
```

This shows:
- Handler loading process
- MQTT connection details
- Message routing
- Error stack traces

## Getting Help

1. Check the [FAQ](faq.md)
2. Review [examples](examples.md)
3. Enable debug logging
4. Check GitHub issues
5. Ask in discussions

## Log Messages Explained

### INFO Messages

- `"Loading handlers from ..."` - Handler discovery started
- `"Loaded handler: ..."` - Handler successfully loaded
- `"Connected to MQTT broker"` - MQTT connection established
- `"Subscribed to topic: ..."` - Topic subscription successful

### WARNING Messages

- `"No handlers found"` - Check handlers directory
- `"Failed to load handler"` - Syntax error in handler file
- `"No handlers for topic"` - No matching topic patterns

### ERROR Messages

- `"Connection refused"` - MQTT broker not accessible
- `"Authentication failed"` - Check username/password
- `"Handler error"` - Exception in handle() method