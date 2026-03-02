/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.exceptions;

/**
 * Exception thrown when MQTT is not configured on the server.
 */
public class MqttNotConfiguredException extends ConfigurationError {

    public MqttNotConfiguredException() {
        super();
    }

    public MqttNotConfiguredException(String message) {
        super(message);
    }
}
