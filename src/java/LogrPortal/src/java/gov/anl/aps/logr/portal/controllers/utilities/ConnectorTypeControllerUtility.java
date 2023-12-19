/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.ConnectorTypeFacade;
import gov.anl.aps.logr.portal.model.db.entities.ConnectorType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class ConnectorTypeControllerUtility extends CdbEntityControllerUtility<ConnectorType, ConnectorTypeFacade>{

    @Override
    protected ConnectorTypeFacade getEntityDbFacade() {
        return ConnectorTypeFacade.getInstance(); 
    }
    
    @Override
    public ConnectorType createEntityInstance(UserInfo sessionUser) {
        return new ConnectorType(); 
    }
    
    @Override
    public String getEntityTypeName() {
        return "connectorType"; 
    }
    
}
