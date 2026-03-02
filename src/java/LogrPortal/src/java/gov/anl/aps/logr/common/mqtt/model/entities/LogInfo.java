/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model.entities;

import com.fasterxml.jackson.annotation.JsonFormat;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.util.Date;

/**
 *
 * @author djarosz
 */
public class LogInfo {

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
