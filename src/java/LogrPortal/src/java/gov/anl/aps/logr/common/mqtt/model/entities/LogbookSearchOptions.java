/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model.entities;

import com.fasterxml.jackson.annotation.JsonFormat;
import gov.anl.aps.logr.portal.model.db.entities.EntityType;
import gov.anl.aps.logr.portal.model.db.entities.ItemType;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Search options for logbook search MQTT events.
 *
 * @author djarosz
 */
public class LogbookSearchOptions {

    private final List<FilterItem> logbookTypes;
    private final List<FilterItem> systems;
    private final List<FilterItem> users;
    private final Date startModifiedDate;
    private final Date endModifiedDate;
    private final Date startCreatedDate;
    private final Date endCreatedDate;
    private final boolean caseInsensitive;

    public LogbookSearchOptions(
            List<EntityType> logbookTypes,
            List<ItemType> systems,
            List<UserInfo> users,
            Date startModifiedDate,
            Date endModifiedDate,
            Date startCreatedDate,
            Date endCreatedDate,
            boolean caseInsensitive) {

        this.logbookTypes = toFilterItems(logbookTypes, e -> new FilterItem(e.getId(), e.getName()));
        this.systems = toFilterItems(systems, s -> new FilterItem(s.getId(), s.getName()));
        this.users = toFilterItems(users, u -> new FilterItem(u.getId(), u.getUsername()));
        this.startModifiedDate = startModifiedDate;
        this.endModifiedDate = endModifiedDate;
        this.startCreatedDate = startCreatedDate;
        this.endCreatedDate = endCreatedDate;
        this.caseInsensitive = caseInsensitive;
    }

    private <T> List<FilterItem> toFilterItems(List<T> list, java.util.function.Function<T, FilterItem> mapper) {
        if (list == null) {
            return null;
        }
        return list.stream().map(mapper).collect(Collectors.toList());
    }

    public List<FilterItem> getLogbookTypes() {
        return logbookTypes;
    }

    public List<FilterItem> getSystems() {
        return systems;
    }

    public List<FilterItem> getUsers() {
        return users;
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getStartModifiedDate() {
        return startModifiedDate;
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEndModifiedDate() {
        return endModifiedDate;
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getStartCreatedDate() {
        return startCreatedDate;
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEndCreatedDate() {
        return endCreatedDate;
    }

    public boolean isCaseInsensitive() {
        return caseInsensitive;
    }

    public static class FilterItem {

        private int id;
        private String name;

        public FilterItem(int id, String name) {
            this.id = id;
            this.name = name;
        }

        public int getId() {
            return id;
        }

        public String getName() {
            return name;
        }
    }
}
