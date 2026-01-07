/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.common.mqtt.constants.CallSource;
import gov.anl.aps.logr.common.mqtt.constants.MqttTopic;
import gov.anl.aps.logr.common.mqtt.model.entities.SearchOptions;

/**
 * MQTT event for search operations.
 *
 * @author djarosz
 */
public class SearchEvent extends MqttEvent {

    private String searchText;
    private SearchOptions searchOptions;
    private CallSource source; // "API" or "Portal"

    public SearchEvent(String searchText, SearchOptions searchOptions, CallSource searchSource) {
        super();
        this.searchText = searchText;
        this.searchOptions = searchOptions;
        this.source = searchSource;

    }

    @Override
    @JsonIgnore
    public MqttTopic getTopic() {
        return MqttTopic.SEARCH;
    }

    public String getSearchText() {
        return searchText;
    }

    public SearchOptions getSearchOptions() {
        return searchOptions;
    }

    public String getSource() {
        return source.getValue();
    }
}
