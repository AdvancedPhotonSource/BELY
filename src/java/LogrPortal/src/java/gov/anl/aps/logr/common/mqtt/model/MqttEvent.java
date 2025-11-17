/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;

/**
 *
 * @author djarosz
 */
public abstract class MqttEvent<Entity extends CdbEntity> {

    Entity entity;
    String description;

    public MqttEvent(Entity entity, String description) {
        this.entity = entity;
        this.description = description;
    }

    @JsonIgnore
    public abstract MqttTopic getTopic();

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

    public void setDescription(String description) {
        this.description = description;
    }

    public String toJson() throws JsonProcessingException {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.writeValueAsString(this);
    }
}
