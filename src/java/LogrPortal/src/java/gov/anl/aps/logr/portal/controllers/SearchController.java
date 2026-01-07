/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers;

import gov.anl.aps.logr.common.constants.CdbProperty;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.entities.SearchOptions;
import gov.anl.aps.logr.portal.controllers.settings.SearchSettings;
import gov.anl.aps.logr.portal.controllers.utilities.SearchControllerUtility;
import gov.anl.aps.logr.portal.utilities.ConfigurationUtility;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.io.IOException;
import java.io.Serializable;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import javax.annotation.PostConstruct;
import javax.enterprise.context.SessionScoped;
import javax.faces.context.FacesContext;
import javax.inject.Named;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Search controller.
 */
@Named(SearchController.controllerNamed)
@SessionScoped
public class SearchController implements Serializable {

    public static final String controllerNamed = "searchController";

    private static final Logger logger = LogManager.getLogger(SearchController.class.getName());

    private static final String SEARCH_TEXT_URL_KEY = "searchString";

    private String searchString = null;

    private String searchOpts = null;

    private Boolean performSearch = false;
    private Boolean performExternallyInitializedSearch = false;

    private SearchSettings searchSettings;

    private final Set<CdbEntityController> searchableControllers;

    protected String contextRootPermanentUrl;

    /**
     * Constructor.
     */
    public SearchController() {
        searchableControllers = new HashSet<>();
        contextRootPermanentUrl = ConfigurationUtility.getPortalProperty(CdbProperty.PERMANENT_CONTEXT_ROOT_URL_PROPERTY_NAME);
    }

    @PostConstruct
    public void initialize() {
        searchSettings = new SearchSettings(this);
        searchSettings.updateSettings();
    }

    public static SearchController getInstance() {
        return (SearchController) SessionUtility.findBean(controllerNamed);
    }

    public void registerSearchableController(CdbEntityController entityController) {
        searchableControllers.add(entityController);
    }

    public String performInputBoxSearchAdvamced() {
        getSearchSettings().setAdvancedSearch(true);
        return performInputBoxSearch(false);
    }

    public String getSearchPath() {
        return "/views/search/search";
    }

    public String performInputBoxSearch() {
        return performInputBoxSearch(true);
    }

    private String performInputBoxSearch(boolean requireSearchString) {
        if (searchString == null || searchString.isEmpty()) {
            if (requireSearchString) {
                SessionUtility.addWarningMessage("Warning", "Please specify a search entry.");
                return null;
            }
        } else {
            performExternallyInitializedSearch = true;
        }

        return String.format("%s.xhtml?faces-redirect=true", getSearchPath());
    }

    public String getInputBoxSearchString() {
        return "";
    }

    public void setInputBoxSearchString(String searchString) {
        setSearchString(searchString);
    }

    public void prepareSearch() {
        if (searchString != null && !searchString.isEmpty()) {
            performSearch = true;
            performExternallyInitializedSearch = false;
        }
    }

    public void search() {
        if (performSearch) {
            // Publish anonymous MQTT event for search
            SearchOptions searchOptions = new SearchOptions(
                    searchSettings.getDisplayItemElements(),
                    searchSettings.getDisplayItemTypes(),
                    searchSettings.getDisplayItemCategories(),
                    searchSettings.getDisplayPropertyTypes(),
                    searchSettings.getDisplayPropertyTypeCategories(),
                    searchSettings.getDisplaySources(),
                    searchSettings.getDisplayUsers(),
                    searchSettings.getDisplayUserGroups()
            );
            SearchControllerUtility.publishSearchMqttEvent(searchString, searchOptions, CallSource.Portal);

            for (CdbEntityController controller : searchableControllers) {
                // Check if controller needs to be skipped.                               
                if (controller instanceof ItemTypeController) {
                    if (!searchSettings.getDisplayItemTypes()) {
                        continue;
                    }
                } else if (controller instanceof ItemCategoryController) {
                    if (!searchSettings.getDisplayItemCategories()) {
                        continue;
                    }
                } else if (controller instanceof PropertyTypeController) {
                    if (!searchSettings.getDisplayPropertyTypes()) {
                        continue;
                    }
                } else if (controller instanceof PropertyTypeCategoryController) {
                    if (!searchSettings.getDisplayPropertyTypeCategories()) {
                        continue;
                    }
                } else if (controller instanceof SourceController) {
                    if (!searchSettings.getDisplaySources()) {
                        continue;
                    }
                } else if (controller instanceof UserGroupController) {
                    if (!searchSettings.getDisplayUserGroups()) {
                        continue;
                    }
                } else if (controller instanceof UserInfoController) {
                    if (!searchSettings.getDisplayUsers()) {
                        continue;
                    }
                } else if (controller instanceof ItemElementController) {
                    if (!searchSettings.getDisplayItemElements()) {
                        continue;
                    }
                }

                controller.performEntitySearch(searchString, searchSettings.getCaseInsensitive());
            }
        }
    }

    public void completeSearch() {
        if (searchString == null || searchString.isEmpty()) {
            SessionUtility.addWarningMessage("Warning", "Search string is empty.");
        } else {
            performSearch = false;
            try {
                FacesContext.getCurrentInstance().getExternalContext().redirect("search");
            } catch (IOException ex) {
                logger.debug(ex);
            }
        }
    }

    public boolean isDisplayResults() {
        return (searchString != null && !searchString.isEmpty()) && !performSearch;
    }

    public boolean isDisplayLoadingScreen() {
        return performSearch;
    }

    public boolean isPerformSearch() {
        return performSearch;
    }

    public boolean isPerformExternallyInitializedSearch() {
        return performExternallyInitializedSearch;
    }

    public String getCurrentViewId() {
        return SessionUtility.getCurrentViewId();
    }

    // Common customize function when settings are changed.
    public String customizeListDisplay() {
        return customizeSearch();
    }

    public String customizeSearch() {
        String returnPage = SessionUtility.getCurrentViewId() + "?faces-redirect=true";
        logger.debug("Returning to page: " + returnPage);
        return returnPage;
    }

    public String getSearchString() {
        return searchString;
    }

    public void setSearchString(String searchString) {
        this.searchString = searchString;
        searchOpts = null;
    }

    public SearchSettings getSearchSettings() {
        return searchSettings;
    }

    public void processPreRender() {
        searchSettings.updateSettings();
    }

    public void processSearchRequestParams() {
        // User friendly search string in URL. 
        String text = SessionUtility.getRequestParameterValue(SEARCH_TEXT_URL_KEY);
        if (text != null && !text.isEmpty()) {
            searchString = text;
            performExternallyInitializedSearch = true;
            return;
        }
    }

    public String getSearchOpts() {
        if (searchOpts == null) {
            searchOpts = URLEncoder.encode(searchString, StandardCharsets.UTF_8);
            searchOpts = String.format("%s=%s", SEARCH_TEXT_URL_KEY, searchOpts);
        }
        return searchOpts;
    }

    public String getSearchPermaLink() {
        return String.format("%s%s?%s", contextRootPermanentUrl, getSearchPath(), getSearchOpts());
    }
}
