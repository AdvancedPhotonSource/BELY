/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.utilities.ObjectUtility;
import gov.anl.aps.logr.portal.controllers.ItemController;
import gov.anl.aps.logr.portal.model.db.beans.ItemElementFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.model.db.utilities.EntityInfoUtility;
import gov.anl.aps.logr.portal.model.db.utilities.ItemElementUtility;
import gov.anl.aps.logr.portal.view.objects.ItemElementConstraintInformation;
import java.util.List;

/**
 *
 * @author darek
 */
public class ItemElementControllerUtility extends CdbDomainEntityControllerUtility<ItemElement, ItemElementFacade> {
    
    @Override
    protected void prepareEntityDestroy(ItemElement itemElement, UserInfo userInfo) throws CdbException {
        super.prepareEntityDestroy(itemElement, userInfo);
        // Verify that item domain allows destroy of item element.   

        Item parentItem = itemElement.getParentItem();        
    }

    @Override
    public void prepareEntityUpdateOnRemoval(ItemElement designElement) {
        EntityInfo entityInfo = designElement.getEntityInfo();
        EntityInfoUtility.updateEntityInfo(entityInfo);
    }   
    
    public ItemElementConstraintInformation getFreshItemElementConstraintInformation(ItemElement itemElement) {
        itemElement = findById(itemElement.getId());
        return getItemElementConstraintInformation(itemElement);
    }        
    
    @Override
    protected void prepareEntityUpdate(ItemElement itemElement, UserInfo userInfo) throws CdbException {
        super.prepareEntityUpdate(itemElement, userInfo);
        
        EntityInfo entityInfo = itemElement.getEntityInfo();
                
        EntityInfoUtility.updateEntityInfo(entityInfo, userInfo);        
        
        ItemElement originalItemElement = null; 
        if (itemElement.getId() != null) {
            originalItemElement = findById(itemElement.getId());
        }
        
        // Check if history needs to be added
        ItemElementUtility.prepareItemElementHistory(originalItemElement, itemElement, entityInfo);        

        // Basic checks for updating an element must be verified with domain of item element. 
        Item parentItem = itemElement.getParentItem();
        ItemControllerUtility itemController = parentItem.getItemControllerUtility();
        //ItemController itemController = ItemController.findDomainControllerForItem(parentItem);
        itemController.checkItemElement(itemElement);

        if (itemElement.getId() != null) {
            ItemElement freshDbItemElement = findById(itemElement.getId());

            // Verify if contained item changed
            Item originalContainedItem = freshDbItemElement.getContainedItem();
            if (ObjectUtility.equals(originalContainedItem, itemElement.getContainedItem()) == false) {
                // Contained item has been updated.
                ItemElementConstraintInformation ieci = getItemElementConstraintInformation(freshDbItemElement);
                if (ieci.isSafeToUpdateContainedItem() == false) {
                    itemElement.setContainedItem(originalContainedItem);
                    throw new CdbException("Cannot update item element " + itemElement + " due to constraints not met. Please reload the item details page and try again.");
                }
            }

            //Verify if isRequred changed
            Boolean originalIsRequired = freshDbItemElement.getIsRequired();
            if (ObjectUtility.equals(originalIsRequired, itemElement.getIsRequired()) == false) {                
                itemController.finalizeItemElementRequiredStatusChanged(itemElement, userInfo);                
            }
        }
    }
    
    public ItemElementConstraintInformation getItemElementConstraintInformation(ItemElement itemElement) {
        ItemElementConstraintInformation itemElementConstraintInformation = null;
        if (itemElement != null) {
            itemElementConstraintInformation = itemElement.getConstraintInformation();
            if (itemElementConstraintInformation == null) {
                Item parentItem = itemElement.getParentItem();
                if (parentItem != null) {
                    ItemController itemDomainController = ItemController.findDomainControllerForItem(parentItem);
                    itemElementConstraintInformation = itemDomainController.loadItemElementConstraintInformation(itemElement);
                    itemElement.setConstraintInformation(itemElementConstraintInformation);
                }
            }
        }
        return itemElementConstraintInformation;
    }
    
    @Override
    protected ItemElementFacade getEntityDbFacade() {
        return ItemElementFacade.getInstance(); 
    }
    
    @Override
    public ItemElement createEntityInstance(UserInfo sessionUser) {
        ItemElement designElement = new ItemElement();
        EntityInfo entityInfo = EntityInfoUtility.createEntityInfo();
        designElement.setEntityInfo(entityInfo);

        // clear selection lists
        return designElement;
    }

    @Override
    public String getEntityInstanceName(ItemElement entity) {
        if (entity != null) {
            return entity.getName();
        }
        return "";
    }
        
    @Override
    public String getEntityTypeName() {
        return "itemElement";
    }
    
}
