/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.common.mqtt.model.entities.LogInfo;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookDocumentInfo;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.ArrayList;
import java.util.List;

/**
 *
 * @author djarosz
 */
public class LogEntryEvent extends MqttEvent<Log> {

    LogbookDocumentInfo parentLogDocumentInfo;
    LogInfo logInfo;
    List<LogbookInfo> logbookList;
    String textDiff;
    protected boolean isNew;

    public LogEntryEvent(ItemDomainLogbook parentLogbook, Log entity, UserInfo eventTriggedByUser, String description, String textDiff, boolean isNew) {
        super(entity, eventTriggedByUser, description);
        this.logInfo = new LogInfo(entity);
        this.textDiff = textDiff;
        this.isNew = isNew;

        if (parentLogbook != null) {
            parentLogDocumentInfo = new LogbookDocumentInfo(parentLogbook);
        }

        List<EntityType> entityTypeList = parentLogbook.getEntityTypeList();
        logbookList = new ArrayList<>();
        for (EntityType entityType : entityTypeList) {
            LogbookInfo info = new LogbookInfo(entityType);
            logbookList.add(info);
        }
    }

    @Override
    public final MqttTopic getTopic() {
        if (isNew) {
            return getAddEventTopic();
        }
        return getUpdateEventTopic();
    }

    protected MqttTopic getAddEventTopic() {
        return MqttTopic.LOGENTRYADD;
    }

    protected MqttTopic getUpdateEventTopic() {
        return MqttTopic.LOGENTRYUPDATE;
    }

    public LogInfo getLogInfo() {
        return logInfo;
    }

    public LogbookDocumentInfo getParentLogDocumentInfo() {
        return parentLogDocumentInfo;
    }

    public List<LogbookInfo> getLogbookList() {
        return logbookList;
    }

    public String getTextDiff() {
        return textDiff;
    }

}
