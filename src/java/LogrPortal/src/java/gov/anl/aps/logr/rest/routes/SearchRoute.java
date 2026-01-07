/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.routes;

import gov.anl.aps.logr.common.exceptions.InvalidRequest;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.entities.SearchOptions;
import gov.anl.aps.logr.portal.controllers.utilities.ItemCategoryControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemElementControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.ItemTypeControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyTypeCategoryControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.PropertyTypeControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.SearchControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.SourceControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.UserGroupControllerUtility;
import gov.anl.aps.logr.portal.controllers.utilities.UserInfoControllerUtility;
import gov.anl.aps.logr.portal.utilities.SearchResult;
import gov.anl.aps.logr.rest.entities.SearchEntitiesOptions;
import gov.anl.aps.logr.rest.entities.SearchEntitiesResults;
import io.swagger.v3.oas.annotations.parameters.RequestBody;
import io.swagger.v3.oas.annotations.tags.Tag;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import javax.ws.rs.Consumes;
import javax.ws.rs.POST;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
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

    @POST
    @Path("/Entities")
    @Produces(MediaType.APPLICATION_JSON)
    @Consumes(MediaType.APPLICATION_JSON)
    public SearchEntitiesResults searchEntities(@RequestBody(required = true) SearchEntitiesOptions searchEntitiesOptions) throws InvalidRequest {
        SearchEntitiesResults results = new SearchEntitiesResults();
        String searchText = searchEntitiesOptions.getSearchText();

        if (searchText == null) {
            throw new InvalidRequest("Search text must be specified.");
        }

        // Publish anonymous MQTT event for API search
        SearchOptions searchOptions = new SearchOptions(
                searchEntitiesOptions.isIncludeItemElement(),
                searchEntitiesOptions.isIncludeItemType(),
                searchEntitiesOptions.isIncludeItemCategoy(),
                searchEntitiesOptions.isIncludePropertyType(),
                searchEntitiesOptions.isIncludePropertyTypeCategory(),
                searchEntitiesOptions.isIncludeSource(),
                searchEntitiesOptions.isIncludeUser(),
                searchEntitiesOptions.isIncludeUserGroup()
        );
        SearchControllerUtility.publishSearchMqttEvent(searchText, searchOptions, CallSource.API);

        if (searchEntitiesOptions.isIncludeItemElement()) {
            ItemElementControllerUtility itemElementControllerUtility = new ItemElementControllerUtility();
            LinkedList<SearchResult> itemElementResults = itemElementControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(itemElementResults);
        }
        if (searchEntitiesOptions.isIncludeItemType()) {
            ItemTypeControllerUtility itemTypeControllerUtility = new ItemTypeControllerUtility();
            LinkedList<SearchResult> itemTypeResults = itemTypeControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(itemTypeResults);
        }
        if (searchEntitiesOptions.isIncludeItemCategoy()) {
            ItemCategoryControllerUtility itemCategoryControllerUtility = new ItemCategoryControllerUtility();
            LinkedList<SearchResult> itemCategoryResults = itemCategoryControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(itemCategoryResults);
        }
        if (searchEntitiesOptions.isIncludePropertyType()) {
            PropertyTypeControllerUtility propertyTypeControllerUtility = new PropertyTypeControllerUtility();
            LinkedList<SearchResult> propertyTypeResults = propertyTypeControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(propertyTypeResults);
        }
        if (searchEntitiesOptions.isIncludePropertyTypeCategory()) {
            PropertyTypeCategoryControllerUtility propertyTypeCategoryControllerUtility = new PropertyTypeCategoryControllerUtility();
            LinkedList<SearchResult> propertyTypeCategoryResults = propertyTypeCategoryControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(propertyTypeCategoryResults);
        }
        if (searchEntitiesOptions.isIncludeSource()) {
            SourceControllerUtility sourceControllerUtility = new SourceControllerUtility();
            LinkedList<SearchResult> sourceResults = sourceControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(sourceResults);
        }
        if (searchEntitiesOptions.isIncludeUser()) {
            UserInfoControllerUtility userControllerUtility = new UserInfoControllerUtility();
            LinkedList<SearchResult> userResults = userControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(userResults);
        }
        if (searchEntitiesOptions.isIncludeUserGroup()) {
            UserGroupControllerUtility userGroupControllerUtility = new UserGroupControllerUtility();
            LinkedList<SearchResult> userGroupResults = userGroupControllerUtility.performEntitySearch(searchText, true);
            results.setItemDomainCatalogResults(userGroupResults);
        }

        return results;
    }
}
