/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.portal.model.db.entities;

import com.fasterxml.jackson.annotation.JsonIgnore;
import gov.anl.aps.logr.portal.constants.ItemDomainName;
import gov.anl.aps.logr.portal.controllers.utilities.ItemDomainLogbookControllerUtility;
import gov.anl.aps.logr.portal.model.db.utilities.LogUtility;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import javax.persistence.DiscriminatorValue;
import javax.persistence.Entity;

/**
 *
 * @author djarosz
 */
@Entity
@DiscriminatorValue(value = ItemDomainName.LOGBOOK_ID + "")
public class ItemDomainLogbook extends Item {

    public static final String LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME = "Logbook Document Settings";
    // System level settings. 
    public static final String DOC_LOCKOUT_SETTING_KEY = "docLockout";
    public static final String LOG_LOCKOUT_SETTING_KEY = "logLockout";

    private transient ItemDomainLogbook newLogbookSection = null;
    private transient List<ItemDomainLogbook> logbookSections;

    private transient PropertyValue logbookDocumentSettings;
    private transient Double documentLockoutHours;
    private transient Double logLockoutHours;

    private transient String opsPersonnel;
    private transient String opsShiftType = "Machine Studies";
    private transient LocalDateTime opsShiftStartTime;
    private transient LocalDateTime opsShiftEndTime;

    private transient List<Log> logListReversed = null;

    public ItemDomainLogbook() {
    }

    @Override
    public Item createInstance() {
        return new ItemDomainLogbook();
    }

    @Override
    public ItemDomainLogbookControllerUtility getItemControllerUtility() {
        return new ItemDomainLogbookControllerUtility();
    }

    @JsonIgnore
    public ItemDomainLogbook getNewLogbookSection() {
        return newLogbookSection;
    }

    public void setNewLogbookSection(ItemDomainLogbook newLogbookSection) {
        this.newLogbookSection = newLogbookSection;
    }

    @JsonIgnore
    public List<ItemDomainLogbook> getLogbookSections() {
        if (logbookSections == null) {
            logbookSections = new ArrayList<>();

            List<ItemElement> itemElementDisplayList = getItemElementDisplayList();

            if (!itemElementDisplayList.isEmpty()) {
                List<Log> logList = this.getLogList();
                if (logList != null && !logList.isEmpty()) {
                    // Add standard section only if it has log entries. 
                    logbookSections.add(this);
                }

                for (ItemElement element : getItemElementDisplayList()) {
                    ItemDomainLogbook containedItem = (ItemDomainLogbook) element.getContainedItem();
                    logbookSections.add(containedItem);
                }
            }
        }

        return logbookSections;
    }

    public Log addLogEntry(String logText, UserInfo userInfo) {
        List<Log> logList = getLogList();

        if (logList == null) {
            logList = new ArrayList<>();
            setLogList(logList);
        }

        Log newLog = LogUtility.createLogEntry(userInfo);
        newLog.setText(logText);

        logList.add(newLog);

        return newLog;
    }

    @JsonIgnore
    public PropertyValue getLogbookDocumentSettings() {
        if (logbookDocumentSettings == null) {
            List<PropertyValue> propertyValueList = this.getPropertyValueList();
            if (propertyValueList == null) {
                return null;
            }

            for (PropertyValue pv : propertyValueList) {
                PropertyType propertyType = pv.getPropertyType();
                String propertyTypeName = propertyType.getName();

                if (propertyTypeName.equals(LOGBOOK_SETTINGS_PROPERTY_TYPE_NAME)) {
                    logbookDocumentSettings = pv;
                    break;
                }
            }
        }

        return logbookDocumentSettings;
    }

    public void setLogbookDocumentSettings(PropertyValue logbookDocumentSettings) {
        this.logbookDocumentSettings = logbookDocumentSettings;
    }

    @JsonIgnore
    public String getOpsPersonnel() {
        return opsPersonnel;
    }

    public void setOpsPersonnel(String opsPersonnel) {
        this.opsPersonnel = opsPersonnel;
    }

    @JsonIgnore
    public String getOpsShiftType() {
        return opsShiftType;
    }

    public void setOpsShiftType(String opsShiftType) {
        this.opsShiftType = opsShiftType;
    }

    @JsonIgnore
    public LocalDateTime getOpsShiftStartTime() {
        return opsShiftStartTime;
    }

    public void setOpsShiftStartTime(LocalDateTime opsShiftStartTime) {
        this.opsShiftStartTime = opsShiftStartTime;
    }

    @JsonIgnore
    public LocalDateTime getOpsShiftEndTime() {
        return opsShiftEndTime;
    }

    public void setOpsShiftEndTime(LocalDateTime opsShiftEndTime) {
        this.opsShiftEndTime = opsShiftEndTime;
    }

    public EntityInfo getMoreInfo() {
        return super.getEntityInfo();
    }

    @Override
    public EntityInfo getEntityInfo() {
        EntityInfo result = super.getEntityInfo();

        Boolean isItemTemplate = getIsItemTemplate();

        // Lockout timer is only enforced for non-templates. 
        if (!isItemTemplate) {
            Double documentLockoutHours = getDocumentLockoutHours();
            result.setLockoutTimeInHours(documentLockoutHours);
        }

        return result;
    }

    private Double getSettingValueAsDouble(String key) {
        PropertyValue settings = getLogbookDocumentSettings();
        if (settings != null) {
            String lockoutString = settings.getPropertyMetadataValueForKey(key);
            if (lockoutString != null) {
                return Double.valueOf(lockoutString);
            }
        }
        return null;

    }

    public Double getLogLockoutHours() {
        if (logLockoutHours == null) {
            logLockoutHours = getSettingValueAsDouble(LOG_LOCKOUT_SETTING_KEY);
        }
        return logLockoutHours;
    }

    public void setLogLockoutHours(Double logLockoutHours) {
        this.logLockoutHours = logLockoutHours;
    }

    @JsonIgnore
    public Double getDocumentLockoutHours() {
        if (documentLockoutHours == null) {
            documentLockoutHours = getSettingValueAsDouble(DOC_LOCKOUT_SETTING_KEY);
        }
        return documentLockoutHours;
    }

    public void setDocumentLockoutHours(Double documentLockoutHours) {
        this.documentLockoutHours = documentLockoutHours;
    }

    @JsonIgnore
    public boolean isDocumentWriteableByTimeout() {
        return getEntityInfo().isEntityWriteableByTimeout();
    }

    private transient ItemDomainLogbook nextDoc;
    private transient ItemDomainLogbook prevDoc;
    private transient boolean nextDocLoaded;
    private transient boolean prevDocLoaded;

    public void setNextDoc(ItemDomainLogbook nextDoc) {
        this.nextDoc = nextDoc;
    }

    public void setPrevDoc(ItemDomainLogbook prevDoc) {
        this.prevDoc = prevDoc;
    }

    @JsonIgnore
    public ItemDomainLogbook getNextDoc() {
        return this.nextDoc;
    }

    @JsonIgnore
    public ItemDomainLogbook getPrevDoc() {
        return this.prevDoc;
    }

    public void setNextDocLoaded(boolean nextDocLoaded) {
        this.nextDocLoaded = nextDocLoaded;
    }

    public void setPrevDocLoaded(boolean prevDocLoaded) {
        this.prevDocLoaded = prevDocLoaded;
    }

    @JsonIgnore
    public boolean getNextDocLoaded() {
        return this.nextDocLoaded;
    }

    @JsonIgnore
    public boolean getPrevDocLoaded() {
        return this.prevDocLoaded;
    }

    @JsonIgnore
    public ItemDomainLogbook getTopLevelLogDocument() {
        List<ItemElement> itemElementMemberList = getItemElementMemberList();
        if (itemElementMemberList != null && itemElementMemberList.size() == 1) {
            ItemElement itemElement = itemElementMemberList.get(0);
            Item item = itemElement.getParentItem();
            if (item instanceof ItemDomainLogbook) {
                return (ItemDomainLogbook) item;
            }
        }

        return this;
    }

    @JsonIgnore
    public List<Log> getLogListReversed() {
        if (logListReversed == null) {
            List<Log> logList = getLogList();
            logListReversed = new ArrayList<>(logList);
            Collections.reverse(logListReversed);
        }
        return logListReversed;
    }
}
