/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model.entities;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import java.util.Date;

/**
 *
 * @author djarosz
 */
public class LogbookDocumentInfo {

    ItemDomainLogbook parentLogbook;

    public LogbookDocumentInfo(ItemDomainLogbook parentLogbook) {
        this.parentLogbook = parentLogbook;
    }

    public Integer getId() {
        return parentLogbook.getId();
    }

    public String getName() {
        return parentLogbook.getName();
    }

    @JsonIgnore
    public EntityInfo getEntityInfo() {
        return parentLogbook.getEntityInfo();
    }

    public String getCreatedByUsername() {
        return getEntityInfo().getCreatedByUsername();
    }

    public String getLastModifiedByUsername() {
        return getEntityInfo().getLastModifiedByUsername();
    }

    public String getOwnerUsername() {
        return getEntityInfo().getOwnerUsername();
    }

    public String getOwnerUserGroupName() {
        return getEntityInfo().getOwnerUserGroupName();
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEnteredOnDateTime() {
        return getEntityInfo().getCreatedOnDateTime();
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getLastModifiedOnDateTime() {
        return getEntityInfo().getLastModifiedOnDateTime();
    }
}
