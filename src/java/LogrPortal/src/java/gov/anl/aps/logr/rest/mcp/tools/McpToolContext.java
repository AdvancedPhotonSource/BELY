/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.mcp.tools;

import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserGroupFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.rest.utilities.LogbookDomainUtility;
import java.util.List;

/** Facade bundle plus the resolved current user, built once per MCP request and passed to every {@link McpTool#call}. */
public class McpToolContext {

    private final DomainFacade domainFacade;
    private final ItemDomainLogbookFacade itemDomainLogbookFacade;
    private final ItemFacade itemFacade;
    private final UserInfoFacade userInfoFacade;
    private final UserGroupFacade userGroupFacade;
    private final UserInfo currentUser;

    public McpToolContext(
            DomainFacade domainFacade,
            ItemDomainLogbookFacade itemDomainLogbookFacade,
            ItemFacade itemFacade,
            UserInfoFacade userInfoFacade,
            UserGroupFacade userGroupFacade,
            UserInfo currentUser) {
        this.domainFacade = domainFacade;
        this.itemDomainLogbookFacade = itemDomainLogbookFacade;
        this.itemFacade = itemFacade;
        this.userInfoFacade = userInfoFacade;
        this.userGroupFacade = userGroupFacade;
        this.currentUser = currentUser;
    }

    public ItemDomainLogbookFacade getItemDomainLogbookFacade() {
        return itemDomainLogbookFacade;
    }

    public ItemFacade getItemFacade() {
        return itemFacade;
    }

    public UserInfoFacade getUserInfoFacade() {
        return userInfoFacade;
    }

    public UserGroupFacade getUserGroupFacade() {
        return userGroupFacade;
    }

    public UserInfo getCurrentUser() {
        return currentUser;
    }

    // Delegates to the shared helper so REST and MCP filter logbook types identically.
    public List<EntityType> getLogbookTypes() {
        return LogbookDomainUtility.getLogbookTypes(domainFacade);
    }

    // Delegates to the shared helper so REST and MCP resolve systems identically.
    public List<ItemType> getLogbookSystems() {
        return LogbookDomainUtility.getLogbookSystems(domainFacade);
    }
}
