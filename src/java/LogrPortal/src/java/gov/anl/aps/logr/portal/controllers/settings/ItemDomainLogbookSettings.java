/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.settings;

import gov.anl.aps.logr.portal.controllers.ItemDomainLogbookController;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookSettings extends ItemSettings<ItemDomainLogbookController> {
    
    public ItemDomainLogbookSettings(ItemDomainLogbookController parentController) {
        super(parentController);
        displayNumberOfItemsPerPage = 10; 
    }
 
    @Override
    public Boolean getDisplayRowExpansion() {
        return true; 
    }
    
}
