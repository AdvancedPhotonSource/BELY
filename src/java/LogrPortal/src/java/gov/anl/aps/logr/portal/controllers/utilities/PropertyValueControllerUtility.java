/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.PropertyValueFacade;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class PropertyValueControllerUtility extends CdbEntityControllerUtility<PropertyValue, PropertyValueFacade> {

    @Override
    protected PropertyValueFacade getEntityDbFacade() {
        return PropertyValueFacade.getInstance(); 
    }        

    @Override
    public String getEntityTypeName() {
        return "propertyValue";
    }

    @Override
    public PropertyValue createEntityInstance(UserInfo sessionUser) {
        return new PropertyValue(); 
    }
    
}
