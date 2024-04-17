/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import java.util.ArrayList;
import java.util.List;

/**
 * API entity represents a log entry. Used for fetching, adding and updating a log entry. 
 * 
 * @author djarosz
 */
public class LogEntry {

    private int itemId;
    private Integer logId; 
    private String logEntry;
    
//    @JsonFormat(shape = JsonFormat.Shape.STRING)
//    private Date effectiveDate;

    public LogEntry() {
    }
    
    public LogEntry(int itemId, Log log) {
        this.itemId = itemId; 
        logId = log.getId(); 
        logEntry = log.getText();
        
        if (logEntry == null) {
            logEntry = ""; 
        }
    }

    public int getItemId() {
        return itemId;
    }

    public String getLogEntry() {
        return logEntry;
    }

    public Integer getLogId() {
        return logId;
    }
    
    public void updateLogPerLogEntryObject(Log log) {
        log.setText(logEntry);         
    }
    
    public static List<LogEntry> createLogEntryList(ItemDomainLogbook item) {
        List<LogEntry> logEntries = new ArrayList<>(); 
        
        List<Log> logList = item.getLogList();
        
        for (Log log : logList) {
            LogEntry entry = new LogEntry(item.getId(), log); 
            logEntries.add(entry); 
        }
        
        return logEntries;
    }
}
