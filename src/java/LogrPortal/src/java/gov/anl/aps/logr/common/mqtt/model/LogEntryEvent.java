/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;

/**
 *
 * @author djarosz
 */
public class LogEntryEvent extends MqttEvent {

    public LogEntryEvent(CdbEntity entity, String description) {
        super(entity, description);
    }

    @Override
    public MqttTopic getTopic() {
        return MqttTopic.LOGENTRY;
    }

}
