/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model.entities;

import gov.anl.aps.logr.portal.model.db.entities.EntityType;

/**
 *
 * @author djarosz
 */
public class LogbookInfo {

    EntityType logbook;

    public LogbookInfo(EntityType logbook) {
        this.logbook = logbook;
    }

    public Integer getId() {
        return this.logbook.getId();
    }

    public String getName() {
        return this.logbook.getName();
    }

    public String getDisplayName() {
        return this.logbook.getDisplayName();
    }

}
