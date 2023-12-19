/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.cdb.portal.model.db.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.cdb.portal.constants.ItemDomainName;
import gov.anl.aps.cdb.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import java.util.ArrayList;
import java.util.List;
import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;

/**
 *
 * @author djarosz
 */
@Entity
@DiscriminatorValue(value = ItemDomainName.LOGBOOK_ID + "")
public class ItemDomainLogbook extends Item {
    
    private transient ItemDomainLogbook newLogbookSection = null;
    private transient List<ItemDomainLogbook> logbookSections;     

    public ItemDomainLogbook() {
    }
    
    @Override
    public Item createInstance() {
        return new ItemDomainLogbook(); 
    } 
    
    @Override
    public ItemDomainLogbookControllerUtility getItemControllerUtility() {
        return new ItemDomainLogbookControllerUtility(); 
    }

    @JsonIgnore
    public ItemDomainLogbook getNewLogbookSection() {
        return newLogbookSection;
    }

    public void setNewLogbookSection(ItemDomainLogbook newLogbookSection) {
        this.newLogbookSection = newLogbookSection;
    }
    
    @JsonIgnore
    public List<ItemDomainLogbook> getLogbookSections() {
        if (logbookSections == null) {
            logbookSections = new ArrayList<>(); 
            
            logbookSections.add(this);
            
            for (ItemElement element : getItemElementDisplayList()) { 
                ItemDomainLogbook containedItem = (ItemDomainLogbook) element.getContainedItem();
                logbookSections.add(containedItem);
            }
           
        }
        
        return logbookSections; 
    }   
}
