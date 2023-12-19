/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.UserSettingFacade;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.model.db.entities.UserSetting;

/**
 *
 * @author darek
 */
public class UserSettingControllerUtility extends CdbEntityControllerUtility<UserSetting, UserSettingFacade> {

    @Override
    protected UserSettingFacade getEntityDbFacade() {
        return UserSettingFacade.getInstance();         
    }
    
    @Override
    public String getEntityTypeName() {
        return "userSetting";
    }

    @Override
    public UserSetting createEntityInstance(UserInfo sessionUser) {
        return new UserSetting(); 
    }
    
}
