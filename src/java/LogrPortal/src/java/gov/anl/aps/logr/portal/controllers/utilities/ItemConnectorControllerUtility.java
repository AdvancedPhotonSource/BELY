/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.ItemConnectorFacade;
import gov.anl.aps.logr.portal.model.db.entities.Connector;
import gov.anl.aps.logr.portal.model.db.entities.ItemConnector;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;

/**
 *
 * @author darek
 */
public class ItemConnectorControllerUtility extends CdbEntityControllerUtility<ItemConnector, ItemConnectorFacade> {

    @Override
    protected ItemConnectorFacade getEntityDbFacade() {
        return ItemConnectorFacade.getInstance();
    }
    
    @Override
    public ItemConnector createEntityInstance(UserInfo sessionUser) {
        ItemConnector itemConnector = new ItemConnector();
        Connector connector = new Connector();
        itemConnector.setConnector(connector);
        itemConnector.setQuantity(1);

        return itemConnector;
    } 
    
    @Override
    public String getEntityTypeName() {
        return "itemConnector";
    }
       
}
