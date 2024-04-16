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
    
    @GET
    @Path("/LogEntries/{logDocumentId}")
    @Operation(summary = "Fetch log entry for log document id or section id.")
    @Produces(MediaType.APPLICATION_JSON)
    public List<LogEntry> getLogEntries(@PathParam("logDocumentId") int logDocumentId) throws ObjectNotFound, InvalidArgument {
        ItemDomainLogbook logDocument = getLogDocumentById(logDocumentId);                 
        
        return LogEntry.createLogEntryList(logDocument); 
    }        
    
    @GET
    @Path("/LogbookSections/{logDocumentId}")
    @Produces(MediaType.APPLICATION_JSON)
    public List<LogDocumentSection> getLogbookSections(@PathParam("logDocumentId") int logDocumentId) throws ObjectNotFound, InvalidArgument {
        ItemDomainLogbook logDocument = getLogDocumentById(logDocumentId); 
        
        List<ItemElement> itemElementDisplayList = logDocument.getItemElementDisplayList();
        List<LogDocumentSection> sections = new ArrayList<>(); 
        for (ItemElement ie : itemElementDisplayList)  {
            Item containedItem = ie.getContainedItem();
            
            Integer id = containedItem.getId();
            String name = containedItem.getName();
            
            LogDocumentSection section = new LogDocumentSection(id, name);
            
            sections.add(section); 
        }
        
        return sections; 
    }
    
    @GET
    @Path("/LogEntryTemplate/{logDocumentId}")
    @Operation(summary = "Fetch new log entry template for log document id or section id.")
    @Produces(MediaType.APPLICATION_JSON)
    @SecurityRequirement(name = "belyAuth")
    @Secured
    public LogEntry getLogEntryTemplate(@PathParam("logDocumentId") int logDocumentId) throws ObjectNotFound, InvalidArgument, AuthorizationError {
        ItemDomainLogbook logDocument = getLogDocumentById(logDocumentId);                
        verifyCurrentUserPermissionForItem(logDocument); 
        
        UserInfo user = getCurrentRequestUserInfo();
        
        ItemDomainLogbookControllerUtility utility = new ItemDomainLogbookControllerUtility();
        Log prepareAddLog = utility.prepareAddLog(logDocument, user);
        
        return new LogEntry(logDocumentId, prepareAddLog); 
    }
    
    @PUT
    @Path("/AddUpdateLogEntry")
    @Produces(MediaType.APPLICATION_JSON)
    @Operation(summary = "Add/Update a log entry to a log document or section")
    @SecurityRequirement(name = "belyAuth")
    @Secured
    public LogEntry addUpdateLogEntry(@RequestBody(required = true) LogEntry logEntry) throws CdbException {
        int itemId = logEntry.getItemId();
        
        ItemDomainLogbook logDocument = getLogDocumentById(itemId);                
        verifyCurrentUserPermissionForItem(logDocument); 
        
        UserInfo user = getCurrentRequestUserInfo();
        Integer logId = logEntry.getLogId();
        Log logEntity = null; 
        ItemDomainLogbookControllerUtility utility = new ItemDomainLogbookControllerUtility();        
        
        if (logId == null) {            
            logEntity = utility.prepareAddLog(logDocument, user);            
        } else {
            List<Log> logList = logDocument.getLogList();
            
            for (Log log : logList) {
                if (Objects.equals(log.getId(), logId)) {
                    logEntity = log; 
                    break; 
                }
            }
            
            if (logEntity == null) {
                throw new ObjectNotFound(
                        String.format(
                                "Log id %d does not exist for log document %d.", 
                                logId, 
                                itemId
                        )
                ); 
            }
            utility.verifySaveLogLockoutsForItem(logDocument, logEntity, user);
        }
        
        logEntry.updateLogPerLogEntryObject(logEntity);        
        logEntity = saveLog(logEntity, user); 
        
        // Update modified date. 
        updateModifiedDateForLogDocument(logDocument, user);
        
        return new LogEntry(itemId, logEntity); 
    }
    @PUT
    @Path("/CreateLogDocumentSection/{logDocumentId}/{sectionName}")
    @Produces(MediaType.APPLICATION_JSON)
    @Operation(summary = "Create logbook document.")
    @SecurityRequirement(name = "belyAuth")
    @Secured
    public ItemDomainLogbook createLogDocumentSection(@PathParam("logDocumentId") int logDocumentId, @PathParam("sectionName") String sectionName) throws CdbException {        
        UserInfo user = getCurrentRequestUserInfo();
        
        ItemDomainLogbook logbook = itemDomainLogbookFacade.find(logDocumentId);        
        verifyCurrentUserPermissionForItem(logbook); 
        
        ItemDomainLogbookControllerUtility utility = new ItemDomainLogbookControllerUtility(); 
        ItemDomainLogbook newSection = utility.createLogbookSectionItem(user);
        newSection.setName(sectionName); 
        
        utility.addLogbookSection(logbook, newSection, user);
        
        logbook = utility.update(logbook, user); 
        
        return logbook;         
    }

    @Override
    protected void verifyUserPermissionForItem(UserInfo user, Item item) throws AuthorizationError {
        // Permission verification should be done at the top level document only. 
        if (item instanceof ItemDomainLogbook) {
            item = ((ItemDomainLogbook)item).getTopLevelLogDocument(); 
        }
        
        super.verifyUserPermissionForItem(user, item); 
    }

}
