/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.utilities;

import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

// Shared logbook domain lookups for the REST and MCP layers; copies before filtering so the domain's managed collection is never modified.
public final class LogbookDomainUtility {

    private LogbookDomainUtility() {
    }

    // There is only ever one logbook domain, so every caller resolves it the same way.
    public static Domain getLogbookDomain(DomainFacade domainFacade) {
        return domainFacade == null ? null : domainFacade.find(ItemDomainName.LOGBOOK_ID);
    }

    public static List<EntityType> getLogbookTypes(DomainFacade domainFacade, boolean includeParents) {
        return getLogbookTypes(getLogbookDomain(domainFacade), includeParents);
    }

    public static List<EntityType> getLogbookTypeHierarchy(DomainFacade domainFacade) {
        return getLogbookTypeHierarchy(getLogbookDomain(domainFacade));
    }

    // Convenience overload so callers holding only the facade need no domain lookup of their own.
    public static List<ItemType> getLogbookSystems(DomainFacade domainFacade) {
        return getLogbookSystems(getLogbookDomain(domainFacade));
    }

    public static List<EntityType> getLogbookTypes(Domain domain, boolean includeParents) {
        List<EntityType> logbookTypes = getAllLogbookTypes(domain);
        if (!includeParents) {
            logbookTypes.removeIf(type -> type != null && type.isHasChildren());
        }
        return logbookTypes;
    }

    public static List<EntityType> getLogbookTypeHierarchy(Domain domain) {
        List<EntityType> roots = getAllLogbookTypes(domain);
        roots.removeIf(type -> type == null || type.getParentEntityType() != null);
        roots.sort(Comparator.comparing(EntityType::getSortOrder,
                Comparator.nullsLast(Comparator.naturalOrder())));
        for (EntityType root : roots) {
            initializeChildren(root);
        }
        return roots;
    }

    private static List<EntityType> getAllLogbookTypes(Domain domain) {
        if (domain == null || domain.getAllowedEntityTypeList() == null) {
            return new ArrayList<>();
        }

        List<EntityType> logbookTypes = new ArrayList<>(domain.getAllowedEntityTypeList());
        String templateName = EntityTypeName.template.getValue();
        logbookTypes.removeIf(type -> type != null && templateName.equals(type.getName()));
        return logbookTypes;
    }

    private static void initializeChildren(EntityType entityType) {
        List<EntityType> children = entityType.getEntityTypeChildren();
        if (children == null) {
            return;
        }
        children.size();
        for (EntityType child : children) {
            initializeChildren(child);
        }
    }

    // Systems configured for the logbook domain; unfiltered, empty when unavailable.
    public static List<ItemType> getLogbookSystems(Domain domain) {
        // Nothing filters this list, so the managed collection can be returned as-is.
        if (domain == null || domain.getItemTypeList() == null) {
            return Collections.emptyList();
        }

        return domain.getItemTypeList();
    }
}
