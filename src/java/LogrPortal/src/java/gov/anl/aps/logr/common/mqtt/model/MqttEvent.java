/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import java.util.Date;

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
    Date eventTimestamp;

    public MqttEvent(Entity entity, String description) {
        this.entity = entity;
        this.description = description;
        this.eventTimestamp = new Date();
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
    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEventTimestamp() {
        return eventTimestamp;
    }

    public String toJson() throws JsonProcessingException {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.writeValueAsString(this);
    }
}
