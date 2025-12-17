/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.constants;

/**
 *
 * @author djarosz
 */
public enum ChangeType {

    ADD(1),
    UPDATE(2),
    DELETE(3);

    private final int value;

    ChangeType(int value) {
        this.value = value;
    }

    public int getValue() {
        return value;
    }

}
