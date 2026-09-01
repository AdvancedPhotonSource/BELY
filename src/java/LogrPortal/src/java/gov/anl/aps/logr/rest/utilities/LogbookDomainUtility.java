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
import java.util.List;

// Shared logbook domain lookups for the REST and MCP layers; copies before filtering so the domain's managed collection is never modified.
public final class LogbookDomainUtility {

    private LogbookDomainUtility() {
    }

    // There is only ever one logbook domain, so every caller resolves it the same way.
    public static Domain getLogbookDomain(DomainFacade domainFacade) {
        return domainFacade == null ? null : domainFacade.find(ItemDomainName.LOGBOOK_ID);
    }

    // Convenience overload so callers holding only the facade need no domain lookup of their own.
    public static List<EntityType> getLogbookTypes(DomainFacade domainFacade) {
        return getLogbookTypes(getLogbookDomain(domainFacade));
    }

    // Convenience overload so callers holding only the facade need no domain lookup of their own.
    public static List<ItemType> getLogbookSystems(DomainFacade domainFacade) {
        return getLogbookSystems(getLogbookDomain(domainFacade));
    }

    // Allowed logbook types minus the template type, as a new list; never returns the managed collection.
    public static List<EntityType> getLogbookTypes(Domain domain) {
        // Callers may hold no domain; return an empty, modifiable list rather than throwing.
        if (domain == null) {
            return new ArrayList<>();
        }

        List<EntityType> allowedEntityTypeList = domain.getAllowedEntityTypeList();
        // A domain with no configured allowed types is valid, not an error.
        if (allowedEntityTypeList == null) {
            return new ArrayList<>();
        }

        // Copy before filtering; never mutate the domain's managed collection.
        List<EntityType> logbookTypes = new ArrayList<>(allowedEntityTypeList);
        String templateName = EntityTypeName.template.getValue();
        // Null-tolerant exact-name match, preserving the original filtering semantics.
        logbookTypes.removeIf(t -> t != null && templateName.equals(t.getName()));

        return logbookTypes;
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
