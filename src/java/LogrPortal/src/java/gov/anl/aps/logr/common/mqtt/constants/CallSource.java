/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.constants;

/**
 *
 * @author djarosz
 */
public enum CallSource {

    API("API"),
    Portal("Portal"),
    MCP("MCP");

    private final String value;

    CallSource(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

}
