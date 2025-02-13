/*
 * Copyright (c) UChicago Argonne, LLC. All rights reserved.
 * See LICENSE file.
 */
package gov.anl.aps.logr.rest.entities;

import com.fasterxml.jackson.annotation.JsonFormat;
import gov.anl.aps.logr.portal.model.db.entities.ItemDomainLogbook;
import gov.anl.aps.logr.portal.model.db.entities.Log;
import gov.anl.aps.logr.portal.model.db.entities.LogReaction;
import gov.anl.aps.logr.portal.model.db.entities.UserInfo;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;

/**
 * API entity represents a log entry. Used for fetching, adding and updating a
 * log entry.
 *
 * @author djarosz
 */
public class LogEntry {

    private int itemId;
    private Integer logId;
    private String logEntry;

    private Date enteredOnDateTime;
    private UserInfo enteredByUser;

    private Date lastModifiedOnDateTime;
    private UserInfo lastModifiedByUser;

    private List<LogEntry> logReplies;
    private List<LogReaction> logReactions;

    public LogEntry() {
    }

    public LogEntry(int itemId, Log log, boolean loadReplies, boolean loadReactions) {
        this.itemId = itemId;
        logId = log.getId();
        logEntry = log.getText();

        enteredOnDateTime = log.getEnteredOnDateTime();
        enteredByUser = log.getEnteredByUser();

        lastModifiedOnDateTime = log.getLastModifiedOnDateTime();
        lastModifiedByUser = log.getLastModifiedByUser();

        if (logEntry == null) {
            logEntry = "";
        }

        if (loadReplies) {
            logReplies = createLogEntryList(itemId, log.getChildLogList(), false, loadReactions);
        }

        if (loadReactions) {
            logReactions = log.getLogReactionList();
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

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getEnteredOnDateTime() {
        return enteredOnDateTime;
    }

    public UserInfo getEnteredByUser() {
        return enteredByUser;
    }

    @JsonFormat(shape = JsonFormat.Shape.STRING)
    public Date getLastModifiedOnDateTime() {
        return lastModifiedOnDateTime;
    }

    public UserInfo getLastModifiedByUser() {
        return lastModifiedByUser;
    }

    public List<LogEntry> getLogReplies() {
        return logReplies;
    }

    public List<LogReaction> getLogReactions() {
        return logReactions;
    }

    public void updateLogPerLogEntryObject(Log log) {
        log.setText(logEntry);
    }

    public static List<LogEntry> createLogEntryList(ItemDomainLogbook item, boolean loadReplies, boolean loadReactions) {
        List<Log> logList = item.getLogList();

        return createLogEntryList(item.getId(), logList, loadReplies, loadReactions);
    }

    private static List<LogEntry> createLogEntryList(Integer itemId, List<Log> logList, boolean loadReplies, boolean loadReactions) {
        List<LogEntry> logEntries = new ArrayList<>();

        for (Log log : logList) {
            LogEntry entry = new LogEntry(itemId, log, loadReplies, loadReactions);
            logEntries.add(entry);
        }

        return logEntries;
    }
}
