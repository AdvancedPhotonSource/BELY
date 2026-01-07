/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.controllers.utilities;

import fish.payara.cloud.connectors.mqtt.api.MQTTConnection;
import fish.payara.cloud.connectors.mqtt.api.MQTTConnectionFactory;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.model.SearchEvent;
import gov.anl.aps.logr.common.mqtt.model.entities.SearchOptions;
import gov.anl.aps.logr.portal.utilities.SessionUtility;
import java.util.Map;
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
    public static void publishSearchMqttEvent(String searchText, SearchOptions searchOptions, CallSource searchSource) {
        try {
            SearchEvent searchEvent = new SearchEvent(searchText, searchOptions, searchSource);

            // Get MQTT connection factory
            MQTTConnectionFactory mqttFactory = SessionUtility.fetchMQTTConnectionFactory();
            if (mqttFactory == null) {
                logger.debug("MQTT not configured. Skipping search event publishing.");
                return;
            }

            // Publish the event
            MQTTConnection connection = mqttFactory.getConnection();
            try {
                String jsonMessage = searchEvent.toJson();
                connection.publish(searchEvent.getTopic().getValue(), jsonMessage.getBytes(), 0, false);
                logger.debug("Published anonymous search MQTT event from {}: {}", searchSource, jsonMessage);
                connection.close();
            } catch (Exception ex) {
                logger.error("Failed to publish search MQTT event from {}: {}", searchSource, ex.getMessage());
            }
        } catch (Exception ex) {
            logger.error("Error preparing search MQTT event from {}: {}", searchSource, ex.getMessage());
        }
    }
}
