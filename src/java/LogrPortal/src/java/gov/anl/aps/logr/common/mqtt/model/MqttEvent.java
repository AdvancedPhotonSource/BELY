/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import java.util.Date;

/**
 *
 * @author djarosz
 */
public abstract class MqttEvent {

    Date eventTimestamp;

    @JsonIgnore
    public abstract MqttTopic getTopic();

    public MqttEvent() {
        this.eventTimestamp = new Date();
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEventTimestamp() {
        return eventTimestamp;
    }

    public String toJson() throws JsonProcessingException {
        ObjectMapper mapper = new ObjectMapper();
        return mapper.writeValueAsString(this);
    }

}
