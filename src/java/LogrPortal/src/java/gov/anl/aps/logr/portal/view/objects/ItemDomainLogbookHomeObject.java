/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.view.objects;

import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook; 
import java.util.ArrayList;
import java.util.List;

/**
 * View object allows managing data that is displayed on the home page. 
 * 
 * @author djarosz
 */
public class ItemDomainLogbookHomeObject {
    
    EntityType logbookType;
    List<ItemDomainLogbook> logbookList; 
    
    List<ItemDomainLogbookHomeObject> homeChildren; 

    public ItemDomainLogbookHomeObject(EntityType logbookType, List<ItemDomainLogbook> logbookList) {
        this.logbookType = logbookType;
        this.logbookList = logbookList;
    }

    public ItemDomainLogbookHomeObject(EntityType logbookType) {
        this.logbookType = logbookType;
        
        if (logbookType.isHasChildren()) {
            homeChildren = new ArrayList<>(); 
            for (EntityType child : logbookType.getEntityTypeChildren()) {
                ItemDomainLogbookHomeObject childHome = new ItemDomainLogbookHomeObject(child);
                homeChildren.add(childHome); 
            }
        }
    }

    public EntityType getLogbookType() {
        return logbookType;
    }

    public List<ItemDomainLogbook> getLogbookList() {
        return logbookList;
    }

    public void setLogbookList(List<ItemDomainLogbook> logbookList) {
        this.logbookList = logbookList;
    }

    public List<ItemDomainLogbookHomeObject> getHomeChildren() {
        return homeChildren;
    }
    
}
