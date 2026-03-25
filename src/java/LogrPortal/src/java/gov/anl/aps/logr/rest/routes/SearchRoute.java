/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.common.exceptions.InvalidArgument;
import gov.anl.aps.logr.common.exceptions.InvalidRequest;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookSearchOptions;
import gov.anl.aps.logr.portal.constants.EntityTypeName;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.controllers.utilities.ItemCategoryControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemElementControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemTypeControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyTypeCategoryControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyTypeControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.SearchControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.SourceControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.UserGroupControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.UserInfoControllerUtility;
import gov.anl.aps.logr.portal.model.db.beans.DomainFacade;
import gov.anl.aps.logr.portal.model.db.beans.UserInfoFacade;
import gov.anl.aps.logr.portal.model.db.entities.Domain;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.rest.entities.LogbookSearchResults;
import gov.anl.aps.logr.rest.entities.SearchEntitiesOptions;
import gov.anl.aps.logr.rest.entities.SearchEntitiesResults;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.ArrayList;
import java.util.Date;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import javax.ejb.EJB;
import javax.ws.rs.Consumes;
import javax.ws.rs.DefaultValue;
import javax.ws.rs.GET;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.PathParam;
import javax.ws.rs.Produces;
import javax.ws.rs.QueryParam;
import javax.ws.rs.core.MediaType;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 *
 * @author djarosz
 */
@Path("/Search")
@Tag(name = "Search")
public class SearchRoute {

    private static final Logger logger = LogManager.getLogger(SearchRoute.class.getName());

    @EJB
    DomainFacade domainFacade;

    @EJB
    UserInfoFacade userInfoFacade;

    @GET
    @Path("/{searchText}")
    @Produces(MediaType.APPLICATION_JSON)
    @Operation(summary = "Search log documents and log entries.", responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    public LogbookSearchResults searchLogbook(
            @Parameter(description = "Search text with wildcard support (? for single char, * for multiple)", required = true)
            @PathParam("searchText") String searchText,
            @Parameter(description = "Use case insensitive matching")
            @QueryParam("caseInsensitive") @DefaultValue("true") boolean caseInsensitive,
            @Parameter(description = "Logbook type IDs to filter by, can specify multiple")
            @QueryParam("logbookTypeId") List<Integer> logbookTypeIdList,
            @Parameter(description = "System IDs to filter by, can specify multiple")
            @QueryParam("systemId") List<Integer> systemIdList,
            @Parameter(description = "User IDs to filter by, can specify multiple")
            @QueryParam("userId") List<Integer> userIdList,
            @Parameter(description = "Start of last modified date range filter")
            @QueryParam("startModifiedDate") Date startModifiedDate,
            @Parameter(description = "End of last modified date range filter")
            @QueryParam("endModifiedDate") Date endModifiedDate,
            @Parameter(description = "Start of creation date range filter")
            @QueryParam("startCreatedDate") Date startCreatedDate,
            @Parameter(description = "End of creation date range filter")
            @QueryParam("endCreatedDate") Date endCreatedDate
    ) throws InvalidRequest, InvalidArgument {

        // Resolve ID lists to entity lists
        List<EntityType> entityTypeList = resolveEntityTypeList(logbookTypeIdList);
        List<ItemType> itemTypeList = resolveItemTypeList(systemIdList);
        List<UserInfo> userList = resolveUserList(userIdList);

        Date startModifiedTime = startModifiedDate;
        Date endModifiedTime = endModifiedDate;
        Date startCreatedTime = startCreatedDate;
        Date endCreatedTime = endCreatedDate;

        // Adjust end times to include the full day
        endModifiedTime = ItemDomainLogbookControllerUtility.adjustEndTimeForSearch(endModifiedTime);
        endCreatedTime = ItemDomainLogbookControllerUtility.adjustEndTimeForSearch(endCreatedTime);

        ItemDomainLogbookControllerUtility utility = new ItemDomainLogbookControllerUtility();

        // Build search options map
        Map searchArgs = utility.createAdvancedSearchMap(
                entityTypeList, itemTypeList, userList,
                startModifiedTime, endModifiedTime,
                startCreatedTime, endCreatedTime);

        LogbookSearchResults results = new LogbookSearchResults();

        // Search log documents
        LinkedList<SearchResult> documentResults = utility.performEntitySearch(
                searchText, searchArgs, caseInsensitive);
        results.setDocumentResults(documentResults);

        // Search log entries
        LinkedList<SearchResult> logEntryResults = utility.searchLogEntries(
                searchText, caseInsensitive, searchArgs);
        results.setLogEntryResults(logEntryResults);

        // Publish MQTT search event
        LogbookSearchOptions searchOptions = new LogbookSearchOptions(
                entityTypeList, itemTypeList, userList,
                startModifiedTime, endModifiedTime,
                startCreatedTime, endCreatedTime, caseInsensitive);
        SearchControllerUtility.publishSearchMqttEvent(searchText, searchOptions, CallSource.API);

        return results;
    }

    @POST
    @Path("/GenericSearch")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    @Operation(responses = {@ApiResponse(responseCode = "200", description = "OK", useReturnTypeSchema = true)})
    public SearchEntitiesResults genericSearch(@RequestBody(required = true) SearchEntitiesOptions searchEntitiesOptions) throws InvalidRequest {
        SearchEntitiesResults results = new SearchEntitiesResults();
        String searchText = searchEntitiesOptions.getSearchText();

        if (searchText == null) {
            throw new InvalidRequest("Search text must be specified.");
        }

        if (searchEntitiesOptions.isIncludeItemElement()) {
            ItemElementControllerUtility itemElementControllerUtility = new ItemElementControllerUtility();
            LinkedList<SearchResult> itemElementResults = itemElementControllerUtility.performEntitySearch(searchText, true);
            results.setItemElementResults(itemElementResults);
        }
        if (searchEntitiesOptions.isIncludeItemType()) {
            ItemTypeControllerUtility itemTypeControllerUtility = new ItemTypeControllerUtility();
            LinkedList<SearchResult> itemTypeResults = itemTypeControllerUtility.performEntitySearch(searchText, true);
            results.setItemTypeResults(itemTypeResults);
        }
        if (searchEntitiesOptions.isIncludeItemCategoy()) {
            ItemCategoryControllerUtility itemCategoryControllerUtility = new ItemCategoryControllerUtility();
            LinkedList<SearchResult> itemCategoryResults = itemCategoryControllerUtility.performEntitySearch(searchText, true);
            results.setItemCategoryResults(itemCategoryResults);
        }
        if (searchEntitiesOptions.isIncludePropertyType()) {
            PropertyTypeControllerUtility propertyTypeControllerUtility = new PropertyTypeControllerUtility();
            LinkedList<SearchResult> propertyTypeResults = propertyTypeControllerUtility.performEntitySearch(searchText, true);
            results.setPropertyTypeResults(propertyTypeResults);
        }
        if (searchEntitiesOptions.isIncludePropertyTypeCategory()) {
            PropertyTypeCategoryControllerUtility propertyTypeCategoryControllerUtility = new PropertyTypeCategoryControllerUtility();
            LinkedList<SearchResult> propertyTypeCategoryResults = propertyTypeCategoryControllerUtility.performEntitySearch(searchText, true);
            results.setPropertyTypeCategoryResults(propertyTypeCategoryResults);
        }
        if (searchEntitiesOptions.isIncludeSource()) {
            SourceControllerUtility sourceControllerUtility = new SourceControllerUtility();
            LinkedList<SearchResult> sourceResults = sourceControllerUtility.performEntitySearch(searchText, true);
            results.setSourceResults(sourceResults);
        }
        if (searchEntitiesOptions.isIncludeUser()) {
            UserInfoControllerUtility userControllerUtility = new UserInfoControllerUtility();
            LinkedList<SearchResult> userResults = userControllerUtility.performEntitySearch(searchText, true);
            results.setUserResults(userResults);
        }
        if (searchEntitiesOptions.isIncludeUserGroup()) {
            UserGroupControllerUtility userGroupControllerUtility = new UserGroupControllerUtility();
            LinkedList<SearchResult> userGroupResults = userGroupControllerUtility.performEntitySearch(searchText, true);
            results.setUserGroupResults(userGroupResults);
        }

        return results;
    }

    private Domain getLogbookDomain() {
        return domainFacade.find(ItemDomainName.LOGBOOK_ID);
    }

    private List<EntityType> getLogbookTypes() {
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

    private List<ItemType> getLogbookSystems() {
        Domain domain = getLogbookDomain();

        return domain.getItemTypeList();
    }

    private List<EntityType> resolveEntityTypeList(List<Integer> idList) throws InvalidArgument {
        if (idList == null || idList.isEmpty()) {
            return null;
        }
        List<EntityType> result = new ArrayList<>();
        List<EntityType> validTypes = getLogbookTypes();
        for (Integer id : idList) {
            boolean found = false;
            for (EntityType type : validTypes) {
                if (type.getId() == id) {
                    result.add(type);
                    found = true;
                    break;
                }
            }
            if (!found) {
                throw new InvalidArgument("Invalid logbook type id: " + id);
            }
        }
        return result;
    }

    private List<ItemType> resolveItemTypeList(List<Integer> idList) throws InvalidArgument {
        if (idList == null || idList.isEmpty()) {
            return null;
        }
        List<ItemType> result = new ArrayList<>();
        List<ItemType> validSystems = getLogbookSystems();
        for (Integer id : idList) {
            boolean found = false;
            for (ItemType system : validSystems) {
                if (system.getId().equals(id)) {
                    result.add(system);
                    found = true;
                    break;
                }
            }
            if (!found) {
                throw new InvalidArgument("Invalid system id: " + id);
            }
        }
        return result;
    }

    private List<UserInfo> resolveUserList(List<Integer> idList) throws InvalidArgument {
        if (idList == null || idList.isEmpty()) {
            return null;
        }
        List<UserInfo> result = new ArrayList<>();
        for (Integer id : idList) {
            UserInfo user = userInfoFacade.find(id);
            if (user == null) {
                throw new InvalidArgument("Invalid user id: " + id);
            }
            result.add(user);
        }
        return result;
    }
}
