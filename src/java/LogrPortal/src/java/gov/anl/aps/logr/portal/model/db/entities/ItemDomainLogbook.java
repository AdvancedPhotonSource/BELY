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

    private transient ItemDomainLogbook newLogbookSection = null;
    private transient List<ItemDomainLogbook> logbookSections;
    
    private transient PropertyValue logbookDocumentSettings; 
    
    
    private transient String opsPersonnel; 
    private transient String opsShiftType = "Machine Studies"; 
    private transient LocalDateTime opsShiftStartTime; 
    private transient LocalDateTime opsShiftEndTime; 

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

    public LocalDateTime getOpsShiftStartTime() {
        return opsShiftStartTime;
    }

    public void setOpsShiftStartTime(LocalDateTime opsShiftStartTime) {
        this.opsShiftStartTime = opsShiftStartTime;
    }

    public LocalDateTime getOpsShiftEndTime() {
        return opsShiftEndTime;
    }

    public void setOpsShiftEndTime(LocalDateTime opsShiftEndTime) {
        this.opsShiftEndTime = opsShiftEndTime;
    }
}
