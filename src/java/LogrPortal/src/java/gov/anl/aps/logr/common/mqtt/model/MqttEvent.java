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
public abstract class MqttEvent {

    Object entityId;
    String entityName;
    String description;

    public MqttEvent(CdbEntity entity, String description) {
        this.entityId = entity.getId();
        this.entityName = entity.getClass().getSimpleName();
        this.description = description;
    }

    @JsonIgnore
    public abstract MqttTopic getTopic();

    public Object getEntityId() {
        return entityId;
    }

    public void setEntityId(Object entityId) {
        this.entityId = entityId;
    }

    public String getEntityName() {
        return entityName;
    }

    public void setEntityName(String entityName) {
        this.entityName = entityName;
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
