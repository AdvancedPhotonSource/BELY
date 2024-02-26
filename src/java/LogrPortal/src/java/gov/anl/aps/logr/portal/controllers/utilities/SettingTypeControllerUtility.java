/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.SettingTypeFacade;
import gov.anl.aps.logr.portal.model.db.entities.SettingType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 * Enables administrators to modify the setting types. 
 * For example changing the global defaults. 
 *
 * @author darek
 */
public class SettingTypeControllerUtility extends CdbEntityControllerUtility<SettingType, SettingTypeFacade>{
    
    public SettingType findByName(String name) {
        return getEntityDbFacade().findByName(name);
    }

    @Override
    public String getEntityTypeName() {
        return "entityType"; 
    }

    @Override
    protected SettingTypeFacade getEntityDbFacade() {
        return SettingTypeFacade.getInstance(); 
    }

    @Override
    public SettingType createEntityInstance(UserInfo sessionUser) {
        throw new UnsupportedOperationException("Cannot be defined dynamically."); 
    }
    
}
