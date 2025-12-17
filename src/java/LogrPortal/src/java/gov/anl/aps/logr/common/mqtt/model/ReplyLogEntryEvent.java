/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.common.mqtt.constants.ChangeType;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.common.mqtt.model.entities.LogInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author djarosz
 */
public class ReplyLogEntryEvent extends LogEntryEvent {

    LogInfo parentLogInfo;

    public ReplyLogEntryEvent(ItemDomainLogbook parentLogbook, Log entity, UserInfo eventTriggedByUser, String description, String textDiff, ChangeType changeType) {
        super(parentLogbook, entity, eventTriggedByUser, description, textDiff, changeType);

        Log parentLogObject = getParentLogObject();

        if (parentLogObject != null) {
            parentLogInfo = new LogInfo(parentLogObject);
        }
    }

    @Override
    protected MqttTopic getAddEventTopic() {
        return MqttTopic.LOGENTRYREPLYADD;
    }

    @Override
    protected MqttTopic getUpdateEventTopic() {
        return MqttTopic.LOGENTRYREPLYUPDATE;
    }

    @Override
    protected MqttTopic getDeletedEventTopic() {
        return MqttTopic.LOGENTRYREPLYDELETE;
    }

    @JsonIgnore
    public final Log getParentLogObject() {
        if (entity == null) {
            return null;
        }
        return entity.getParentLog();
    }

    public LogInfo getParentLogInfo() {
        return parentLogInfo;
    }

}
