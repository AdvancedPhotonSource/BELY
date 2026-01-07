/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author djarosz
 */
public abstract class MqttEntityEvent<Entity extends CdbEntity> extends MqttEvent {

    Entity entity;
    String description;
    UserInfo eventTriggedByUser;

    public MqttEntityEvent(Entity entity, UserInfo eventTriggedByUser, String description) {
        super();
        this.entity = entity;
        this.description = description;
        this.eventTriggedByUser = eventTriggedByUser;
    }

    @JsonIgnore
    public CdbEntity getEntity() {
        return entity;
    }

    public Object getEntityId() {
        return entity.getId();
    }

    public String getEntityName() {
        return entity.getClass().getSimpleName();
    }

    public String getDescription() {
        return description;
    }

    public String getEventTriggedByUsername() {
        if (eventTriggedByUser == null) {
            return null;
        }

        return eventTriggedByUser.getUsername();
    }
}
