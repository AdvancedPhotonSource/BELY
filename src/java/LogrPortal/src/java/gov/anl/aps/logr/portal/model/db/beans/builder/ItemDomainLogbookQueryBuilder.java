/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.beans.builder;

import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.controllers.settings.ItemSettings;
import java.util.Map;
import org.primefaces.model.SortOrder;

/**
 *
 * @author djarosz
 */
public class ItemDomainLogbookQueryBuilder extends ItemQueryBuilder {

    private final boolean allLogbookTypes;

    public ItemDomainLogbookQueryBuilder(Integer domainId, Map filterMap, String sortField, SortOrder sortOrder, ItemSettings scopeSettings) {
        this(domainId, filterMap, sortField, sortOrder, scopeSettings, false);
    }

    public ItemDomainLogbookQueryBuilder(Integer domainId, Map filterMap, String sortField, SortOrder sortOrder, ItemSettings scopeSettings, boolean allLogbookTypes) {
        super(domainId, filterMap, sortField, sortOrder, scopeSettings);
        this.allLogbookTypes = allLogbookTypes;
    }

    @Override
    protected void generateWhereString() {
        super.generateWhereString();

        if (allLogbookTypes) {
            // Show top level log documents of every logbook type. Templates are 
            // excluded since their only entity type is the template entity type. 
            appendRawWhere("i.itemElementMemberList IS EMPTY");
            appendRawWhere(ENTITY_TYPE_LIST_JOIN_NAME + ".name <> '" + EntityTypeName.template.getValue() + "'");
            include_etl = true;
            return;
        }

        if (filterMap == null || filterMap.isEmpty()) {
            appendRawWhere("i.itemElementMemberList IS EMPTY");
            appendRawWhere("i.entityTypeList IS EMPTY");
        }
    }

}
