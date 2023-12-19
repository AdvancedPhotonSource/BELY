/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans;

import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import javax.ejb.Stateless;

/**
 *
 * @author djarosz
 */
@Stateless
public class ItemDomainLogbookFacade extends ItemFacadeBase<ItemDomainLogbook> {   
    
    public ItemDomainLogbookFacade() {
        super(ItemDomainLogbook.class);
    }
    
    @Override
    public ItemDomainName getDomain() {
        return ItemDomainName.logbook;
    }   
    
    public static ItemDomainLogbookFacade getInstance() {
        return (ItemDomainLogbookFacade) SessionUtility.findFacade(ItemDomainLogbookFacade.class.getSimpleName()); 
    }
    
}
