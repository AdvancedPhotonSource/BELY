/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.AllowedPropertyValueFacade;
import gov.anl.aps.logr.portal.model.db.entities.AllowedPropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class AllowedPropertyValueControllerUtility extends CdbEntityControllerUtility<AllowedPropertyValue, AllowedPropertyValueFacade>{

    @Override
    protected AllowedPropertyValueFacade getEntityDbFacade() {
        return AllowedPropertyValueFacade.getInstance(); 
    }
        
    @Override
    public AllowedPropertyValue createEntityInstance(UserInfo sessionUser) {
        AllowedPropertyValue allowedPropertyValue = new AllowedPropertyValue();
        return allowedPropertyValue;
    }   
    
    @Override
    public String getEntityTypeName() {
        return "allowedPropertyValue";
    }
    
}
