/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model;

import gov.anl.aps.logr.portal.controllers.settings.ItemSettings;
import gov.anl.aps.logr.portal.model.db.beans.ItemFacadeBase;
import gov.anl.aps.logr.portal.model.db.beans.builder.ItemGenericQueryBuilder;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import java.util.Map;
import org.primefaces.model.SortOrder;

/**
 *
 * @author darek
 */
public class ItemGenericLazyDataModel extends ItemLazyDataModel<ItemFacadeBase, ItemGenericQueryBuilder> {

    public ItemGenericLazyDataModel(ItemFacadeBase facade, Domain itemDomain, ItemSettings settings) {
        super(facade, itemDomain, settings);
    }

    @Override
    protected ItemGenericQueryBuilder getQueryBuilder(Map filterMap, String sortField, SortOrder sortOrder) {
        return new ItemGenericQueryBuilder(itemDomain.getId(), filterMap, sortField, sortOrder, settings);  
    }

    
}
