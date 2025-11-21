/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.constants;

/**
 *
 * @author djarosz
 */
public enum MqttTopic {
    UPDATE("bely/update"),
    ADD("bely/add"),
    DELETE("bely/delete"),
    LOGENTRYADD("bely/logEntry/Add"),
    LOGENTRYUPDATE("bely/logEntry/Update"),
    LOGENTRYREPLYADD("bely/logEntryReply/Add"),
    LOGENTRYREPLYUPDATE("bely/logEntryReply/Update");

    private final String value;

    MqttTopic(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    @Override
    public String toString() {
        return super.toString() + "(" + value + ")";
    }
}
