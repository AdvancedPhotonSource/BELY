/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.cdb.portal.model.db.beans.builder;

import gov.anl.aps.cdb.portal.controllers.settings.ItemSettings;
import java.util.Map;
import org.primefaces.model.SortOrder;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookQueryBuilder extends ItemQueryBuilder {
    
    public ItemDomainLogbookQueryBuilder(Integer domainId, Map filterMap, String sortField, SortOrder sortOrder, ItemSettings scopeSettings) {
        super(domainId, filterMap, sortField, sortOrder, scopeSettings);
    } 

    @Override
    protected void generateWhereString() {
        super.generateWhereString(); 
        
        if (filterMap == null || filterMap.isEmpty()) {
            appendRawWhere("i.itemElementMemberList IS EMPTY");
            appendRawWhere("i.entityTypeList IS EMPTY");
        }
    }
    
    
    
}
