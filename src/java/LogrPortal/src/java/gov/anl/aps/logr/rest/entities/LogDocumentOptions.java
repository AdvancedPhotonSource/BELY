/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import java.util.List;

/**
 * API entity represents options to create a new log document. 
 * 
 * @author djarosz
 */
public class LogDocumentOptions {
    
    private String name; 
    
    private List<Integer> systemIdList = null; 
    private Integer logbookTypeId = null; 
    private Integer templateId = null;       
    private boolean skipDefaultLogbookTypeTemplate = false; 
    
    private List<ItemType> systemList = null; 
    private EntityType logbookType = null; 
    private ItemDomainLogbook templateItem = null;     

    public LogDocumentOptions() {       
    }

    public String getName() {
        return name;
    }

    public List<Integer> getSystemIdList() {
        return systemIdList;
    }

    public Integer getLogbookTypeId() {
        return logbookTypeId;
    }

    public Integer getTemplateId() {
        return templateId;
    }

    public boolean isSkipDefaultLogbookTypeTemplate() {
        return skipDefaultLogbookTypeTemplate;
    }

    public void setSkipDefaultLogbookTypeTemplate(boolean skipDefaultLogbookTypeTemplate) {
        this.skipDefaultLogbookTypeTemplate = skipDefaultLogbookTypeTemplate;
    }

    @JsonIgnore
    public List<ItemType> getSystemList() {
        return systemList;
    }

    public void setSystemList(List<ItemType> systemList) {
        this.systemList = systemList;
    }

    @JsonIgnore
    public EntityType getLogbookType() {
        return logbookType;
    }

    public void setLogbookType(EntityType logbookType) {
        this.logbookType = logbookType;
    }

    @JsonIgnore
    public ItemDomainLogbook getTemplateItem() {
        return templateItem;
    }

    public void setTemplateItem(ItemDomainLogbook templateItem) {
        this.templateItem = templateItem;
    }
    
    
    
}
