"""Integration tests for MQTT message broker functionality."""

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from aiomqtt import Client, MqttError

from bely_mqtt.models import MQTTMessage, CoreEvent, LogEntryAddEvent
from bely_mqtt.plugin import MQTTHandler, PluginManager


# Get broker configuration from environment
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))


class TestHandler(MQTTHandler):
    """Test handler for integration tests."""

    def __init__(self):
        super().__init__()
        self.received_messages = []
        self.message_event = asyncio.Event()

    @property
    def topic_pattern(self) -> str:
        return "test/integration/#"

    async def handle(self, message: MQTTMessage) -> None:
        self.received_messages.append(message)
        self.message_event.set()


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def mqtt_client():
    """Create MQTT client for testing."""
    try:
        async with Client(MQTT_BROKER_HOST, MQTT_BROKER_PORT) as client:
            yield client
    except MqttError as e:
        pytest.skip(f"MQTT broker not available: {e}")


@pytest_asyncio.fixture
async def test_handler():
    """Create test handler instance."""
    return TestHandler()


@pytest.mark.asyncio
async def test_mqtt_connection(mqtt_client):
    """Test basic MQTT connection."""
    # If we get here, connection was successful
    assert mqtt_client is not None


@pytest.mark.asyncio
async def test_publish_and_subscribe(mqtt_client):
    """Test publishing and subscribing to topics."""
    test_topic = "test/integration/basic"
    test_payload = {"test": "data", "timestamp": datetime.now().isoformat()}
    
    # Subscribe to topic
    await mqtt_client.subscribe(test_topic)
    
    # Publish message
    await mqtt_client.publish(
        test_topic,
        payload=json.dumps(test_payload).encode(),
        qos=1
    )
    
    # Wait for message
    async with asyncio.timeout(5):
        async for message in mqtt_client.messages:
            if message.topic.matches(test_topic):
                received_payload = json.loads(message.payload.decode())
                assert received_payload == test_payload
                break


@pytest.mark.asyncio
async def test_handler_message_processing(mqtt_client, test_handler):
    """Test that handlers properly process MQTT messages."""
    manager = PluginManager()
    manager.register_handler(test_handler)
    
    test_topic = "test/integration/handler"
    test_payload = {
        "description": "Test event",
        "eventTimestamp": datetime.now().isoformat(),
        "entityName": "TestEntity",
        "entityId": 123,
        "eventTriggedByUsername": "test_user"
    }
    
    # Simulate receiving a message
    mqtt_message = MQTTMessage(topic=test_topic, payload=test_payload)
    await manager.handle_message(mqtt_message)
    
    # Check handler received the message
    assert len(test_handler.received_messages) == 1
    assert test_handler.received_messages[0].topic == test_topic
    assert test_handler.received_messages[0].payload == test_payload


@pytest.mark.asyncio
async def test_core_event_parsing_from_mqtt():
    """Test parsing CoreEvent from MQTT message."""
    payload = {
        "description": "Test action completed",
        "eventTimestamp": datetime.now().isoformat(),
        "entityName": "TestEntity",
        "entityId": 456,
        "eventTriggedByUsername": "mqtt_user"
    }
    
    message = MQTTMessage(topic="bely/events/core", payload=payload)
    event = CoreEvent(**message.payload)
    
    assert event.description == "Test action completed"
    assert event.entity_name == "TestEntity"
    assert event.entity_id == 456
    assert event.event_triggered_by_username == "mqtt_user"


@pytest.mark.asyncio
async def test_log_entry_event_parsing_from_mqtt():
    """Test parsing LogEntryAddEvent from MQTT message."""
    payload = {
        "description": "log entry was added",
        "eventTimestamp": datetime.now().isoformat(),
        "parentLogDocumentInfo": {
            "name": "[2025/11/21/2] Test Document",
            "id": 105,
            "lastModifiedOnDateTime": datetime.now().isoformat(),
            "createdByUsername": "test_user",
            "lastModifiedByUsername": "test_user",
            "enteredOnDateTime": datetime.now().isoformat(),
            "ownerUsername": "test_user",
            "ownerUserGroupName": "TEST_GROUP",
        },
        "logInfo": {
            "id": 267,
            "lastModifiedOnDateTime": datetime.now().isoformat(),
            "lastModifiedByUsername": "test_user",
            "enteredByUsername": "test_user",
            "enteredOnDateTime": datetime.now().isoformat(),
        },
        "logbookList": [
            {"name": "test-logbook", "id": 7, "displayName": "Test"}
        ],
        "textDiff": "New Test Entry",
        "entityName": "Log",
        "entityId": 267,
        "eventTriggedByUsername": "test_user",
    }
    
    message = MQTTMessage(topic="bely/events/log/add", payload=payload)
    event = LogEntryAddEvent(**message.payload)
    
    assert event.description == "log entry was added"
    assert event.log_info.id == 267
    assert event.parent_log_document_info.id == 105
    assert len(event.logbook_list) == 1
    assert event.logbook_list[0].display_name == "Test"


@pytest.mark.asyncio
async def test_wildcard_topic_matching(mqtt_client):
    """Test MQTT wildcard topic pattern matching."""
    topics_to_test = [
        ("test/integration/one", True),
        ("test/integration/two", True),
        ("test/integration/deep/nested", True),
        ("test/other/topic", False),
        ("other/integration/test", False),
    ]
    
    handler = TestHandler()
    
    for topic, should_match in topics_to_test:
        assert handler.topic_matches(topic) == should_match, \
            f"Topic {topic} match failed. Expected: {should_match}"


@pytest.mark.asyncio
async def test_multiple_handlers_integration(mqtt_client):
    """Test multiple handlers receiving the same message."""
    handler1 = TestHandler()
    handler2 = TestHandler()
    
    manager = PluginManager()
    manager.register_handler(handler1)
    manager.register_handler(handler2)
    
    test_message = MQTTMessage(
        topic="test/integration/multi",
        payload={"test": "multiple handlers"}
    )
    
    await manager.handle_message(test_message)
    
    assert len(handler1.received_messages) == 1
    assert len(handler2.received_messages) == 1
    assert handler1.received_messages[0].payload == test_message.payload
    assert handler2.received_messages[0].payload == test_message.payload


@pytest.mark.asyncio
async def test_error_handling_in_handler():
    """Test that errors in one handler don't affect others."""
    
    class ErrorHandler(MQTTHandler):
        @property
        def topic_pattern(self) -> str:
            return "test/integration/#"
        
        async def handle(self, message: MQTTMessage) -> None:
            raise ValueError("Test error")
    
    class SuccessHandler(MQTTHandler):
        def __init__(self):
            super().__init__()
            self.received = []
        
        @property
        def topic_pattern(self) -> str:
            return "test/integration/#"
        
        async def handle(self, message: MQTTMessage) -> None:
            self.received.append(message)
    
    error_handler = ErrorHandler()
    success_handler = SuccessHandler()
    
    manager = PluginManager()
    manager.register_handler(error_handler)
    manager.register_handler(success_handler)
    
    test_message = MQTTMessage(
        topic="test/integration/error",
        payload={"test": "error handling"}
    )
    
    # Should not raise even though ErrorHandler fails
    await manager.handle_message(test_message)
    
    # SuccessHandler should still receive the message
    assert len(success_handler.received) == 1


@pytest.mark.asyncio
async def test_qos_levels(mqtt_client):
    """Test different QoS levels for message delivery."""
    test_topic = "test/integration/qos"
    
    for qos in [0, 1, 2]:
        test_payload = {"qos": qos, "test": f"QoS {qos}"}
        
        await mqtt_client.subscribe(test_topic, qos=qos)
        
        await mqtt_client.publish(
            test_topic,
            payload=json.dumps(test_payload).encode(),
            qos=qos
        )
        
        # Wait for message with timeout
        async with asyncio.timeout(5):
            async for message in mqtt_client.messages:
                if message.topic.matches(test_topic):
                    received = json.loads(message.payload.decode())
                    assert received["qos"] == qos
                    break
        
        await mqtt_client.unsubscribe(test_topic)


@pytest.mark.asyncio
async def test_retained_messages(mqtt_client):
    """Test retained message functionality."""
    test_topic = "test/integration/retained"
    test_payload = {"retained": True, "data": "persistent"}
    
    # Publish retained message
    await mqtt_client.publish(
        test_topic,
        payload=json.dumps(test_payload).encode(),
        retain=True,
        qos=1
    )
    
    # Wait a bit for message to be stored
    await asyncio.sleep(0.5)
    
    # Subscribe and should immediately receive retained message
    await mqtt_client.subscribe(test_topic)
    
    async with asyncio.timeout(5):
        async for message in mqtt_client.messages:
            if message.topic.matches(test_topic):
                received = json.loads(message.payload.decode())
                assert received == test_payload
                assert message.retain == True
                break
    
    # Clean up retained message
    await mqtt_client.publish(test_topic, payload=b"", retain=True)