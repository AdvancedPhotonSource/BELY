/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.ArrayList;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookControllerUtility extends ItemControllerUtility<ItemDomainLogbook, ItemDomainLogbookFacade> {

    @Override
    protected ItemDomainLogbookFacade getItemFacadeInstance() {
        return ItemDomainLogbookFacade.getInstance();
    }

    @Override
    protected ItemDomainLogbook instenciateNewItemDomainEntity() {
        return new ItemDomainLogbook(); 
    }

    @Override
    public boolean isEntityHasQrId() {
        return false;
    }

    @Override
    public boolean isEntityHasName() {
        return true;
    }

    @Override
    public boolean isEntityHasProject() {
        return false; 
    }

    @Override
    public String getDefaultDomainName() {
        return ItemDomainName.logbook.getValue(); 
    }

    @Override
    public String getDerivedFromItemTitle() {
        throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
    }

    @Override
    public String getEntityTypeName() {
        return "logbook";
    }
    
    @Override
    public boolean isEntityHasItemIdentifier2() {
        return false;
    }

    @Override
    public Log prepareAddLog(ItemDomainLogbook cdbDomainEntity, UserInfo user) {
        Log log = super.prepareAddLog(cdbDomainEntity, user); 
        
        log.setItemElementList(new ArrayList<>());
        ItemElement selfElement = cdbDomainEntity.getSelfElement();
        
        log.getItemElementList().add(selfElement);         
        
        return log; 
    }

    
}
