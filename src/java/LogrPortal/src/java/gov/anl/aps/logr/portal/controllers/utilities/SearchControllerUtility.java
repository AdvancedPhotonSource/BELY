/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.SearchEvent;
import gov.anl.aps.logr.common.mqtt.model.entities.LogbookSearchOptions;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

/**
 * Utility class for search-related operations.
 *
 * @author djarosz
 */
public class SearchControllerUtility {

    private static final Logger logger = LogManager.getLogger(SearchControllerUtility.class.getName());

    /**
     * Publishes an anonymous MQTT event when a search is performed.
     *
     * @param searchText The search text
     * @param searchOptions Map of search options/settings
     * @param searchSource The source of the search (e.g., "Portal", "API")
     */
    public static void publishSearchMqttEvent(String searchText, LogbookSearchOptions searchOptions, CallSource searchSource) {
        SearchEvent searchEvent = new SearchEvent(searchText, searchOptions, searchSource);
        try {
            SessionUtility.publishMqttEvent(searchEvent);
        } catch (Exception ex) {
            logger.error("Failed to publish search MQTT event from {}: {}", searchSource, ex.getMessage());
        }
    }
}
