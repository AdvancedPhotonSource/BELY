---
globs: "**/*.py"
regex: class.*MQTTHandler
alwaysApply: false
---

When creating MQTTHandler subclasses, do not override the topic_pattern property unless there's a specific need to limit the topics. The default pattern "bely/#" allows the handler to receive all BELY events, and the framework automatically routes events to the appropriate handler methods. Only override topic_pattern for performance optimization or when you explicitly want to limit the handler to specific topics.