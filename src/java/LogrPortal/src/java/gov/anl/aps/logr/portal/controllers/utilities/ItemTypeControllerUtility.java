/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.portal.model.db.beans.ItemCategoryFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemTypeFacade;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;

/**
 *
 * @author darek
 */
public class ItemTypeControllerUtility extends ItemTypeCategoryControllerUtility<ItemType, ItemTypeFacade> {
    
    ItemCategoryFacade itemCategoryFacade; 

    public ItemTypeControllerUtility() {
        itemCategoryFacade = ItemCategoryFacade.getInstance(); 
    }        

    @Override
    protected ItemTypeFacade getEntityDbFacade() {
        return ItemTypeFacade.getInstance(); 
    }

    @Override
    protected void clearCaches() {
        super.clearCaches(); 
        itemCategoryFacade.clearCache(); 
    }
    
    @Override
    protected ItemType createItemTypeCategoryEntity() {
        ItemType itemType = new ItemType();        
        return itemType;
    }
       
    @Override
    public String getEntityTypeName() {
        return "itemType";
    }
    
}
