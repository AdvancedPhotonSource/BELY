/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;

/**
 *
 * @author djarosz
 */
public class ReplyLogEntryEvent extends LogEntryEvent {

    LogInfo parentlogInfo;

    public ReplyLogEntryEvent(ItemDomainLogbook parentLogbook, Log entity, String description, String textDiff) {
        super(parentLogbook, entity, description, textDiff);

        Log parentLogObject = getParentLogObject();

        if (parentLogObject != null) {
            parentlogInfo = new LogInfo(parentLogObject);
        }
    }

    @Override
    public MqttTopic getTopic() {
        return MqttTopic.LOGENTRYREPLY;
    }

    @JsonIgnore
    public Log getParentLogObject() {
        if (entity == null) {
            return null;
        }
        return entity.getParentLog();
    }

    public LogInfo getParentlogInfo() {
        return parentlogInfo;
    }

}
