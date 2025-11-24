/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.common.mqtt.model.entities.LogInfo;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookDocumentInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.LogReaction;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author djarosz
 */
public class LogReactionEvent extends MqttEvent<LogReaction> {

    boolean isDelete;

    LogInfo parentLogInfo;
    LogbookDocumentInfo parentLogDocumentInfo;

    public LogReactionEvent(LogReaction entity,
            Log parentLogEntry,
            ItemDomainLogbook parentLogDocument,
            UserInfo eventTriggedByUser,
            String description, boolean isDelete) {
        super(entity, eventTriggedByUser, description);

        this.isDelete = isDelete;

        if (parentLogEntry != null) {
            parentLogInfo = new LogInfo(parentLogEntry);
        }
        if (parentLogDocument != null) {
            parentLogDocumentInfo = new LogbookDocumentInfo(parentLogDocument);
        }
    }

    @Override
    public MqttTopic getTopic() {
        if (isDelete) {
            return MqttTopic.LOGREACTIONDELETE;
        }
        return MqttTopic.LOGREACTIONADD;
    }

    public LogReaction getLogReaction() {
        return entity;
    }

    public LogInfo getParentLogInfo() {
        return parentLogInfo;
    }

    public LogbookDocumentInfo getParentLogDocumentInfo() {
        return parentLogDocumentInfo;
    }

}
