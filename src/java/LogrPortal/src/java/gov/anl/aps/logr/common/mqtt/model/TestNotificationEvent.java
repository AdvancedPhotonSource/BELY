/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import java.util.Map;

/**
 * MQTT event for test notification operations.
 *
 * @author djarosz
 */
@JsonInclude(JsonInclude.Include.NON_NULL)
public class TestNotificationEvent extends MqttEvent {

    private String notificationEndpoint;
    private String configurationName;
    private Integer configurationId;
    private Map<String, String> providerSettings;
    private String eventTriggedByUsername;

    public TestNotificationEvent(String notificationEndpoint, String configurationName,
            Integer configurationId, Map<String, String> providerSettings,
            String eventTriggedByUsername) {
        super();
        this.notificationEndpoint = notificationEndpoint;
        this.configurationName = configurationName;
        this.configurationId = configurationId;
        this.providerSettings = providerSettings;
        this.eventTriggedByUsername = eventTriggedByUsername;
    }

    @Override
    public MqttTopic getTopic() {
        return MqttTopic.NOTIFICATIONTEST;
    }

    public String getNotificationEndpoint() {
        return notificationEndpoint;
    }

    public String getConfigurationName() {
        return configurationName;
    }

    public Integer getConfigurationId() {
        return configurationId;
    }

    public Map<String, String> getProviderSettings() {
        return providerSettings;
    }

    public String getEventTriggedByUsername() {
        return eventTriggedByUsername;
    }
}
