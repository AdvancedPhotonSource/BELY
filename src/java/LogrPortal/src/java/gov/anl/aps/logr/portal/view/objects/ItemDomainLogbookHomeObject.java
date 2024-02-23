/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.view.objects;

import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook; 
import java.util.List;

/**
 * View object allows managing data that is displayed on the home page. 
 * 
 * @author djarosz
 */
public class ItemDomainLogbookHomeObject {
    
    EntityType logbookType;
    List<ItemDomainLogbook> logbookList; 

    public ItemDomainLogbookHomeObject(EntityType logbookType, List<ItemDomainLogbook> logbookList) {
        this.logbookType = logbookType;
        this.logbookList = logbookList;
    }

    public EntityType getLogbookType() {
        return logbookType;
    }

    public List<ItemDomainLogbook> getLogbookList() {
        return logbookList;
    }
    
}
