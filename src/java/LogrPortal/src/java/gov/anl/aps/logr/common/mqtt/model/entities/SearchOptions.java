/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.common.mqtt.model.entities;

/**
 *
 * @author djarosz
 */
public class SearchOptions {

    private boolean includeItemElement;
    private boolean includeItemType;
    private boolean includeItemCategory;
    private boolean includePropertyType;
    private boolean includePropertyTypeCategory;
    private boolean includeSource;
    private boolean includeUser;
    private boolean includeUserGroup;

    public SearchOptions(boolean includeItemElement, boolean includeItemType, boolean includeItemCategory, boolean includePropertyType, boolean includePropertyTypeCategory, boolean includeSource, boolean includeUser, boolean includeUserGroup) {
        this.includeItemElement = includeItemElement;
        this.includeItemType = includeItemType;
        this.includeItemCategory = includeItemCategory;
        this.includePropertyType = includePropertyType;
        this.includePropertyTypeCategory = includePropertyTypeCategory;
        this.includeSource = includeSource;
        this.includeUser = includeUser;
        this.includeUserGroup = includeUserGroup;
    }

    public boolean isIncludeItemElement() {
        return includeItemElement;
    }

    public boolean isIncludeItemType() {
        return includeItemType;
    }

    public boolean isIncludeItemCategory() {
        return includeItemCategory;
    }

    public boolean isIncludePropertyType() {
        return includePropertyType;
    }

    public boolean isIncludePropertyTypeCategory() {
        return includePropertyTypeCategory;
    }

    public boolean isIncludeSource() {
        return includeSource;
    }

    public boolean isIncludeUser() {
        return includeUser;
    }

    public boolean isIncludeUserGroup() {
        return includeUserGroup;
    }

}
