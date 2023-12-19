/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.constants;

public enum ListName {
    favorite("Favorites");

    private String value;

    private ListName(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }
};
