/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.settings;

import gov.anl.aps.logr.portal.controllers.ItemGenericViewController;

/**
 *
 * @author djarosz
 */
public class ItemGenericViewSettings extends ItemSettings<ItemGenericViewController> {
    
    public ItemGenericViewSettings(ItemGenericViewController parentController) {
        super(parentController);
        displayNumberOfItemsPerPage = 25; 
    }
    
}
