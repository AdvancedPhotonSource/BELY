/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.util.Date;

/**
 *
 * @author djarosz
 */
public class LogEntryEvent extends MqttEvent<Log> {

    LogbookInfo parentLogbookInfo;
    LogInfo logInfo;

    public LogEntryEvent(ItemDomainLogbook parentLogbook, Log entity, String description) {
        super(entity, description);
        this.logInfo = new LogInfo(entity);

        if (parentLogbook != null) {
            parentLogbookInfo = new LogbookInfo(parentLogbook);
        }
    }

    @Override
    public MqttTopic getTopic() {
        return MqttTopic.LOGENTRY;
    }

    public LogInfo getLogInfo() {
        return logInfo;
    }

    public LogbookInfo getParentLogbookInfo() {
        return parentLogbookInfo;
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

    private class LogbookInfo {

        ItemDomainLogbook parentLogbook;

        public LogbookInfo(ItemDomainLogbook parentLogbook) {
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

}
