/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.common.exceptions.AuthorizationError;
import gov.anl.aps.logr.common.exceptions.CdbException;
import gov.anl.aps.logr.common.exceptions.InvalidArgument;
import gov.anl.aps.logr.common.exceptions.ObjectNotFound;
import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.controllers.utilities.EntityInfoControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.LogControllerUtility;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.beans.ItemDomainLogbookFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityInfo;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.Item;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.ItemElement;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.model.db.utilities.EntityInfoUtility;
import gov.anl.aps.logr.rest.authentication.Secured;
import gov.anl.aps.logr.rest.entities.LogDocumentOptions;
import gov.anl.aps.logr.rest.entities.LogDocumentSection;
import gov.anl.aps.logr.rest.entities.LogEntry;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import javax.ejb.EJB;
import javax.ws.rs.GET;
import javax.ws.rs.PUT;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.core.MediaType;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * API route to provide logbook functionality.
 *
 * @author djarosz
 */
@Path("/Logbook")
@Tag(name = "Logbook")
public class LogbookRoute extends ItemBaseRoute {

    private static final Logger LOGGER = LogManager.getLogger(LogbookRoute.class.getName());

    @EJB
    DomainFacade domainFacade;        

    @EJB
    ItemDomainLogbookFacade itemDomainLogbookFacade;

    private Domain getLogbookDomain() {
        return domainFacade.find(ItemDomainName.LOGBOOK_ID);
    }

    @GET
    @Path("/LogbookTypes")
    @Produces(MediaType.APPLICATION_JSON)
    public List<EntityType> getLogbookTypes() {
        Domain domain = getLogbookDomain();
        List<EntityType> logbookTypes = domain.getAllowedEntityTypeList();
        // Remove template 
        for (EntityType logbookType : logbookTypes) {
            if (logbookType.getName().equals(EntityTypeName.template.getValue())) {
                logbookTypes.remove(logbookType);
                break;
            }
        }

        return logbookTypes;
    }

    @GET
    @Path("/LogbookSystems")
    @Produces(MediaType.APPLICATION_JSON)
    public List<ItemType> getLogbookSystems() {
        Domain domain = getLogbookDomain();

        return domain.getItemTypeList();
    }

    @GET
    @Path("/LogbookTemplates")
    @Produces(MediaType.APPLICATION_JSON)
    public List<ItemDomainLogbook> getLogbookTemplates() {
        String domainName = ItemDomainName.logbook.getValue();
        String entityTypeName = EntityTypeName.template.getValue();
        return itemDomainLogbookFacade.findByDomainAndEntityTypeAndTopLevel(domainName, entityTypeName);
    }
    
    @GET
    @Path("/LogDocuments/{logbookTypeId}/{limit}")
    @Operation(summary = "Fetch last modified log documents for specific logbook type.")
    @Produces(MediaType.APPLICATION_JSON)
    public List<ItemDomainLogbook> getLogDocuments(@PathParam("logbookTypeId") int logbookTypeId, @PathParam("limit") int rowLimit) throws InvalidArgument {
        List<EntityType> logbookTypes = getLogbookTypes();
        EntityType logbookType = null;
        
        for (EntityType type : logbookTypes) {
            if (type.getId() == logbookTypeId) {
                logbookType = type; 
                break;
            }
        }
        
        if (logbookType == null) {
            throw new InvalidArgument(String.format("%d is not a valid logbook type id.", logbookTypeId)); 
        }
              
        String domainName = ItemDomainName.logbook.getValue();
        String entityTypeName = logbookType.getName();
        return itemDomainLogbookFacade.findByDomainNameAndEntityTypeOrderByLastModifiedDate(domainName, entityTypeName, rowLimit); 
    }
}
