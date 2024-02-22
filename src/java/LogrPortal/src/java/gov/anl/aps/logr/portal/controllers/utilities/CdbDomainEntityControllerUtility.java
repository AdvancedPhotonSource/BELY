/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.CdbEntityFacade;
import gov.anl.aps.logr.portal.model.db.entities.CdbDomainEntity;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.model.db.utilities.LogUtility;
import java.util.List;

/**
 *
 * @author darek
 */
public abstract class CdbDomainEntityControllerUtility<EntityType extends CdbDomainEntity, FacadeType extends CdbEntityFacade<EntityType>>
        extends CdbEntityControllerUtility<EntityType, FacadeType> {
    
    public Log prepareAddLog(EntityType cdbDomainEntity, UserInfo user) {
        Log logEntry = null;        
        logEntry = LogUtility.createLogEntry(user);        
        
        List<Log> cdbDomainEntityLogList = cdbDomainEntity.getLogList();
        cdbDomainEntityLogList.add(0, logEntry);
        return logEntry; 
    }

}
