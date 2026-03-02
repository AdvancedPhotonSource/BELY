/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.portal.model.db.entities.CdbEntity;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author djarosz
 */
public class AddEvent extends MqttEntityEvent {

    public AddEvent(CdbEntity entity, UserInfo eventTriggedByUser, String description) {
        super(entity, eventTriggedByUser, description);
    }

    @Override
    public MqttTopic getTopic() {
        return MqttTopic.ADD;
    }

}
