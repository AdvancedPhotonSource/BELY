/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.constants;

public enum ItemDomainName {        
    logbook("Logbook", ItemDomainName.LOGBOOK_ID);
        
    public final static int LOGBOOK_ID = 1;

    private String value;
    private Integer id;

    private ItemDomainName(String value, Integer id) {
        this.value = value;
        this.id = id;
    }

    public final String getValue() {
        return value;
    }

    public final Integer getId() {
        return id;
    }
};
