/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.portal.constants.SystemLogLevel;
import gov.anl.aps.logr.portal.model.db.beans.EntityInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 * Controller utility provides create, edit, update and delete functionality for entity info records. 
 *  
 * @author darek
 */
public class EntityInfoControllerUtility extends CdbEntityControllerUtility<EntityInfo, EntityInfoFacade> {

    @Override
    protected EntityInfoFacade getEntityDbFacade() {
        return EntityInfoFacade.getInstance(); 
    }
        
    @Override
    public EntityInfo createEntityInstance(UserInfo sessionUser) {
        EntityInfo entityInfo = new EntityInfo(); 
        return entityInfo;
    }   
    
    @Override
    public String getEntityTypeName() {
        return "entityInfo";
    }

    @Override
    protected void addCdbEntitySystemLog(SystemLogLevel logLevel, String message, UserInfo sessionUser) throws CdbException {
        // No need to log 
        return;
    }
    
}
