/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model;

import gov.anl.aps.logr.portal.controllers.settings.ItemSettings;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.beans.builder.ItemDomainLogbookQueryBuilder;
import gov.anl.aps.logr.portal.model.db.beans.builder.ItemQueryBuilder;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import java.util.HashMap;
import java.util.Map;
import org.primefaces.model.FilterMeta;
import org.primefaces.model.SortMeta;
import org.primefaces.model.SortOrder;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookLazyDataModel extends ItemLazyDataModel<ItemDomainLogbookFacade, ItemDomainLogbookQueryBuilder> {

    private boolean allLogbookTypes = false;

    public ItemDomainLogbookLazyDataModel(ItemDomainLogbookFacade facade, Domain itemDomain, ItemSettings settings) {
        super(facade, itemDomain, settings);
        
        addDefaultSortOrder();
    }
    
    private void addDefaultSortOrder() {
        Map sortBy = new HashMap();
        String idKey = ItemQueryBuilder.QueryTranslator.id.getValue();        
        SortMeta sortMeta = new SortMeta(); 
        sortMeta.setOrder(SortOrder.DESCENDING);
        sortBy.put(idKey, sortMeta); 
        
        setDefaultSortOrderMap(sortBy); 
    }

    @Override
    protected ItemDomainLogbookQueryBuilder getQueryBuilder(Map filterMap, String sortField, SortOrder sortOrder) {
        return new ItemDomainLogbookQueryBuilder(itemDomain.getId(), filterMap, sortField, sortOrder, settings, allLogbookTypes);
    }

    /**
     * Show log documents of every logbook type instead of a single type.
     */
    public void setAllLogbookTypes() {
        allLogbookTypes = true;
        setCurrentEntityType(null);
    }

    public boolean isAllLogbookTypes() {
        return allLogbookTypes;
    }
    
    public void setCurrentEntityType(String entityType) {
        if (entityType != null) {
            allLogbookTypes = false;
        }

        if (entityType == null) {
            setDefaultFilterBy(null);
        } else {
            Map filterBy = new HashMap();
            
            String entityTypeKey = ItemQueryBuilder.QueryTranslator.entityTypeName.getValue();      
            FilterMeta filter = new FilterMeta();            
            filter.setFilterValue(entityType);            
            filterBy.put(entityTypeKey, filter);
            
            setDefaultFilterBy(filterBy);            
        }
        
    }
    
}
