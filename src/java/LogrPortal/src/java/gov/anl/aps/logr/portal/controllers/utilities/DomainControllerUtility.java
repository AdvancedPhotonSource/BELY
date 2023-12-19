/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class DomainControllerUtility extends CdbEntityControllerUtility<Domain, DomainFacade> {

    @Override
    protected DomainFacade getEntityDbFacade() {
        return DomainFacade.getInstance(); 
    }
        
    @Override
    public Domain createEntityInstance(UserInfo sessionUser) {
        return new Domain(); 
    }   
    
    @Override
    public String getEntityTypeName() {
        return "domain";
    }
    
}
