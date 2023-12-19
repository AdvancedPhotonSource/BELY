package gov.anl.aps.logr.portal.controllers;

/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */

import gov.anl.aps.logr.portal.model.db.entities.PropertyType;
import gov.anl.aps.logr.portal.model.db.entities.PropertyValue;

/**
 *
 * @author darek
 */
public interface IItemStatusController {
    
    void prepareEditInventoryStatus();
    
    boolean getRenderedHistoryButton();    
    PropertyValue getCurrentStatusPropertyValue();
    PropertyType getInventoryStatusPropertyType();
    
}


