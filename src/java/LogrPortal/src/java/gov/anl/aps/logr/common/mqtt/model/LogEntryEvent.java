/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.util.ArrayList;
import java.util.Date;
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

    public LogEntryEvent(ItemDomainLogbook parentLogbook, Log entity, String description, String textDiff) {
        super(entity, description);
        this.logInfo = new LogInfo(entity);
        this.textDiff = textDiff;

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
    public MqttTopic getTopic() {
        return MqttTopic.LOGENTRY;
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

    protected class LogInfo {

        Log log;

        public LogInfo(Log log) {
            this.log = log;
        }

        public Integer getId() {
            return log.getId();
        }

        public String getEnteredByUsername() {
            return log.getEnteredByUsername();
        }

        public String getLastModifiedByUsername() {
            return log.getLastModifiedByUsername();
        }

        @JsonFormat(shape = JsonFormat.Shape.STRING)
        public Date getEnteredOnDateTime() {
            return log.getEnteredOnDateTime();
        }

        @JsonFormat(shape = JsonFormat.Shape.STRING)
        public Date getLastModifiedOnDateTime() {
            return log.getLastModifiedOnDateTime();
        }
    }

    private class LogbookDocumentInfo {

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

    private class LogbookInfo {

        EntityType logbook;

        public LogbookInfo(EntityType logbook) {
            this.logbook = logbook;
        }

        public Integer getId() {
            return this.logbook.getId();
        }

        public String getName() {
            return this.logbook.getName();
        }

        public String getDisplayName() {
            return this.logbook.getDisplayName();
        }
    }

}
